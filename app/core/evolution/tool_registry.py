"""
Astra Evolution: Tool registry and pending-tools approval flow.

Registry: JSON file listing active tools (name, path, description, allowlist).
Pending: tools awaiting co-parent approval; stored in JSON file or S3.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Evolution dir: app/core/evolution/
_EVOLUTION_DIR = Path(__file__).resolve().parent
DEFAULT_REGISTRY_PATH = _EVOLUTION_DIR / "tool_registry.json"
DEFAULT_PENDING_PATH = _EVOLUTION_DIR / "pending_tools.json"


def _ensure_evolution_dir() -> None:
    _EVOLUTION_DIR.mkdir(parents=True, exist_ok=True)


def load_registry(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load active tool registry. Keys: active (list of tool dicts), version."""
    path = path or DEFAULT_REGISTRY_PATH
    if not path.exists():
        return {"version": 1, "active": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {"version": 1, "active": []}
    except Exception:
        return {"version": 1, "active": []}


def save_registry(data: Dict[str, Any], path: Optional[Path] = None) -> None:
    _ensure_evolution_dir()
    path = path or DEFAULT_REGISTRY_PATH
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_active_tools() -> List[Dict[str, Any]]:
    """List of active (approved) tools."""
    reg = load_registry()
    return reg.get("active") or []


def get_tool_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get active tool by name."""
    for t in get_active_tools():
        if (t.get("name") or "").strip().lower() == name.strip().lower():
            return t
    return None


def register_active_tool(name: str, script_path: str, description: str = "", allowed_ops: Optional[List[str]] = None) -> None:
    """Add a tool to the active registry."""
    reg = load_registry()
    active = reg.get("active") or []
    name = name.strip()
    # Remove existing with same name
    active = [t for t in active if (t.get("name") or "").strip().lower() != name.lower()]
    active.append({
        "name": name,
        "script_path": script_path,
        "description": description.strip(),
        "allowed_ops": allowed_ops or [],
    })
    reg["active"] = active
    save_registry(reg)


# --- Pending tools (approval flow) ---

def load_pending_tools(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load list of pending tools (awaiting approval)."""
    path = path or DEFAULT_PENDING_PATH
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_pending_tools(pending: List[Dict[str, Any]], path: Optional[Path] = None) -> None:
    _ensure_evolution_dir()
    path = path or DEFAULT_PENDING_PATH
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pending, f, indent=2)


def add_pending_tool(name: str, script_path: str, description: str = "", proposed_by: str = "astra") -> None:
    """Add a tool to the pending list."""
    pending = load_pending_tools()
    name = name.strip()
    pending = [p for p in pending if (p.get("name") or "").strip().lower() != name.lower()]
    pending.append({
        "name": name,
        "script_path": script_path,
        "description": description.strip(),
        "proposed_by": proposed_by,
        "status": "pending",
    })
    save_pending_tools(pending)


def approve_pending_tool(name: str) -> Optional[str]:
    """
    Move a pending tool to active registry. Returns script_path on success, None if not found.
    """
    pending = load_pending_tools()
    name_lower = name.strip().lower()
    found = None
    new_pending = []
    for p in pending:
        if (p.get("name") or "").strip().lower() == name_lower:
            found = p
        else:
            new_pending.append(p)
    if not found:
        return None
    save_pending_tools(new_pending)
    script_path = found.get("script_path", "")
    description = found.get("description", "")
    register_active_tool(found.get("name", name), script_path, description)
    return script_path


def reject_pending_tool(name: str) -> bool:
    """Remove a pending tool. Returns True if it was found."""
    pending = load_pending_tools()
    name_lower = name.strip().lower()
    new_pending = [p for p in pending if (p.get("name") or "").strip().lower() != name_lower]
    if len(new_pending) == len(pending):
        return False
    save_pending_tools(new_pending)
    return True
