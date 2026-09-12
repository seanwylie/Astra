"""
Astra Evolution: LLM-generated tool proposals.

When a concept implies an action (e.g. ping, time), asks the LLM to generate
a single Python script. Script is written to the sandbox and added as a
*pending* tool for co-parent approval. No execution until approved.
"""

import os
import re
from pathlib import Path
from typing import Optional, Tuple

from app.core.evolution.tool_registry import (
    add_pending_tool,
    get_active_tools,
    load_pending_tools,
    get_tool_by_name,
)

_SANDBOX_DIR = Path(__file__).resolve().parent / "sandbox"

# Concepts that may trigger an automatic tool proposal (lowercase).
CONCEPT_ACTION_TRIGGERS = {"ping", "time", "date", "echo"}


def _sanitize_name(concept: str) -> str:
    """Turn a concept into a valid script name (no spaces, alphanumeric + underscore)."""
    name = re.sub(r"[^\w]", "_", concept.strip().lower())
    return name.strip("_") or "tool"


def _already_has_tool(name: str) -> bool:
    """True if name is already active or pending."""
    if get_tool_by_name(name):
        return True
    name_lower = name.lower()
    for p in load_pending_tools():
        if (p.get("name") or "").strip().lower() == name_lower:
            return True
    return False


def propose_tool_for_concept(concept: str, definition: str = "") -> Optional[Tuple[str, str]]:
    """
    Ask LLM to generate a single Python script for the concept; write to sandbox and add as pending.
    Returns (tool_name, script_path) if successful, None otherwise.
    """
    name = _sanitize_name(concept)
    if _already_has_tool(name):
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        return None

    active_names = [t.get("name", "") for t in get_active_tools()] + [p.get("name", "") for p in load_pending_tools()]
    safety = (
        "Rules: (1) Only use Python stdlib or very simple code. "
        "(2) No os.system(), no eval/exec of user input. "
        "(3) For 'ping', you may use subprocess.run(['ping', '-c', '1', host]) with a single host from sys.argv. "
        "(4) For 'time' or 'date', use datetime and print current time. "
        "(5) Script must read args from sys.argv[1:] and print a single result to stdout. "
        "(6) Keep the script under 80 lines."
    )
    prompt = (
        f"Concept: {concept}\nDefinition: {definition[:500] if definition else 'None'}\n\n"
        f"Existing tool names (do not reuse): {', '.join(active_names) or 'none'}\n\n"
        f"{safety}\n\n"
        "Respond with exactly two lines:\n"
        "LINE1: Tool short description (one line)\n"
        "LINE2: The full Python script (no markdown, no backticks). Start the script from the first line of code (e.g. import sys)."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = (resp.choices[0].message.content or "").strip()
    except Exception:
        return None

    lines = content.split("\n")
    if len(lines) < 2:
        return None
    description = lines[0].strip().strip('"\'')
    # Rest is the script; skip any leading markdown or empty lines
    script_lines = []
    for i in range(1, len(lines)):
        if lines[i].strip().startswith("```"):
            continue
        script_lines.append(lines[i])
    script_body = "\n".join(script_lines)
    if not script_body.strip():
        return None

    # Ensure we have a valid Python script (starts with import or def or #)
    script_body = script_body.strip()
    if not (script_body.startswith("import ") or script_body.startswith("#") or script_body.startswith("from ")):
        script_body = "import sys\n" + script_body

    script_path = _SANDBOX_DIR / f"{name}.py"
    try:
        script_path.write_text(script_body, encoding="utf-8")
    except Exception:
        return None

    add_pending_tool(name, str(script_path.name), description=description, proposed_by="astra")
    return (name, str(script_path))
