"""
Astra Evolution: Apply an approved code proposal.

Writes the proposed content to the file (path must be allowlisted).
Optionally run tests/lint after apply; audit log.
"""

from pathlib import Path
from typing import Optional, Tuple

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def resolve_allowlisted_path(relative_path: str) -> Optional[Path]:
    """Resolve relative path to absolute if it is in the evolution readable allowlist."""
    from app.core.evolution.readable_code import get_readable_paths
    relative_path = relative_path.strip().strip("/").replace("\\", "/")
    if not relative_path or ".." in relative_path:
        return None
    for base in get_readable_paths():
        base = base.strip().strip("/")
        if relative_path == base or relative_path.startswith(base + "/"):
            full = _PROJECT_ROOT / relative_path
            try:
                full.resolve().relative_to(_PROJECT_ROOT.resolve())
            except ValueError:
                return None
            return full
    return None


def apply_proposal(proposal: dict) -> Tuple[bool, str]:
    """
    Write proposal's proposed_content to proposal's file_path (if allowlisted).
    Returns (success, message).
    """
    file_path = (proposal.get("file_path") or "").strip()
    if not file_path:
        return False, "No file_path in proposal."
    path = resolve_allowlisted_path(file_path)
    if path is None:
        return False, f"Path not allowlisted: {file_path}"
    if path.is_dir():
        return False, f"Path is a directory: {file_path}"
    content = (proposal.get("proposed_content") or "").strip()
    if not content:
        return False, "No proposed_content."
    try:
        path.write_text(content, encoding="utf-8")
    except Exception as e:
        return False, str(e)
    _audit_log(proposal, "applied")
    return True, f"Applied to {file_path}."


def _audit_log(proposal: dict, action: str) -> None:
    """Append to audit log (optional)."""
    try:
        log_path = Path(__file__).resolve().parent / "proposal_audit.log"
        line = f"{action}\t{proposal.get('file_path', '')}\t{proposal.get('proposed_at', '')}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
