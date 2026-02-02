"""
Astra Evolution: Code change proposals ("Mom, can I get a tattoo?").

Schema: file_path, current_content_snippet, proposed_diff_or_content, rationale, proposed_at, status.
Stored in JSON file (or S3). Co-parent can list, approve, reject, or approve-with-edits.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_EVOLUTION_DIR = Path(__file__).resolve().parent
DEFAULT_PROPOSALS_PATH = _EVOLUTION_DIR / "code_proposals.json"


def load_proposals(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load all proposals (any status)."""
    path = path or DEFAULT_PROPOSALS_PATH
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_proposals(proposals: List[Dict[str, Any]], path: Optional[Path] = None) -> None:
    path = path or DEFAULT_PROPOSALS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(proposals, f, indent=2)


def add_proposal(
    file_path: str,
    current_content_snippet: str,
    proposed_content: str,
    rationale: str,
    status: str = "pending",
) -> Dict[str, Any]:
    """Add a new proposal. Returns the created proposal dict."""
    import time
    proposal = {
        "file_path": file_path.strip(),
        "current_content_snippet": (current_content_snippet or "")[:2000],
        "proposed_content": (proposed_content or "").strip(),
        "rationale": (rationale or "").strip(),
        "proposed_at": time.time(),
        "status": status,
    }
    proposals = load_proposals()
    proposals.append(proposal)
    save_proposals(proposals)
    return proposal


def get_pending_proposals() -> List[Dict[str, Any]]:
    """Proposals with status 'pending'."""
    return [p for p in load_proposals() if (p.get("status") or "").lower() == "pending"]


def set_proposal_status(proposal_index: int, status: str) -> bool:
    """Set status by index in full list. Returns True if updated."""
    proposals = load_proposals()
    if proposal_index < 0 or proposal_index >= len(proposals):
        return False
    proposals[proposal_index]["status"] = status
    save_proposals(proposals)
    return True


def get_proposal_by_index(index: int) -> Optional[Dict[str, Any]]:
    """Get proposal by index (in full list)."""
    proposals = load_proposals()
    if index < 0 or index >= len(proposals):
        return None
    return proposals[index]
