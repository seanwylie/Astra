"""
Astra Evolution: Generate a code change proposal from a goal and file content.

Given Astra's goal (e.g. "add a timeout to the ping script") and the content
of an allowlisted file, asks LLM to produce proposed new content and rationale.
Submits to proposals store as pending.
"""

import os
from typing import Optional, Tuple

from app.core.evolution.readable_code import read_file
from app.core.evolution.proposals import add_proposal


def generate_and_submit_proposal(
    file_path: str,
    goal: str,
) -> Optional[Tuple[int, str]]:
    """
    Read allowlisted file, ask LLM for proposed change and rationale, store as pending.
    Returns (proposal_index, message) or None on failure.
    """
    content = read_file(file_path)
    if content is None:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        return None

    prompt = (
        f"File path: {file_path}\n\n"
        f"Current content:\n```\n{content[:4000]}\n```\n\n"
        f"Astra's goal: {goal}\n\n"
        "Respond with exactly two blocks separated by ---:\n"
        "BLOCK1: One short rationale (why this change).\n"
        "BLOCK2: The full new file content (complete replacement). No markdown, no backticks."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = (resp.choices[0].message.content or "").strip()
    except Exception:
        return None

    parts = text.split("---", 1)
    rationale = (parts[0].strip() if parts else "")[:500]
    proposed = (parts[1].strip() if len(parts) > 1 else "").strip()
    if not proposed:
        return None
    # Strip markdown code fence if present
    if proposed.startswith("```"):
        lines = proposed.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        proposed = "\n".join(lines)

    proposal = add_proposal(
        file_path=file_path,
        current_content_snippet=content[:1500],
        proposed_content=proposed,
        rationale=rationale,
        status="pending",
    )
    from app.core.evolution.proposals import load_proposals
    proposals = load_proposals()
    index = next(i for i, p in enumerate(proposals) if p.get("proposed_at") == proposal.get("proposed_at"))
    return (index, f"Proposal #{index} for {file_path} (pending approval).")


def list_readable_for_astra() -> str:
    """Return a short listing of readable paths for Astra to choose from."""
    from app.core.evolution.readable_code import list_readable
    items = list_readable()
    lines = [f"- {path} {'(dir)' if is_dir else ''}" for path, is_dir in items if not is_dir]
    return "\n".join(lines[:50]) if lines else "No readable files."
