"""
Astra Evolution: Read own code (allowlisted paths only).

Astra can read only paths that are in the allowlist. Used for "read own code
and propose modifications" (Mom, can I get a tattoo?).
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple

# Project root: parent of app/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Paths Astra is allowed to read (relative to project root). No full repo access.
DEFAULT_READABLE_PATHS: List[str] = [
    "app/core/evolution/sandbox",
    "app/core/evolution/tool_registry.json",
    "app/core/evolution/pending_tools.json",
    "config/schedule_config.json",
]


def get_readable_paths() -> List[str]:
    """Return the list of allowlisted paths (relative to project root)."""
    try:
        from app.config.loader import load_config
        cfg = load_config("general_config") or {}
        paths = cfg.get("evolution_readable_paths")
        if isinstance(paths, list) and paths:
            return [p.strip() for p in paths if p and isinstance(p, str)]
    except Exception:
        pass
    return list(DEFAULT_READABLE_PATHS)


def _resolve_path(relative_path: str) -> Optional[Path]:
    """Resolve relative_path to absolute Path if it is under an allowlisted base. Returns None if not allowed."""
    relative_path = relative_path.strip().strip("/")
    if not relative_path or ".." in relative_path:
        return None
    allowed = get_readable_paths()
    for base in allowed:
        base = base.strip().strip("/")
        if not base:
            continue
        # base can be a file or directory
        if relative_path == base or relative_path.startswith(base + "/"):
            full = _PROJECT_ROOT / relative_path
            try:
                full.resolve().relative_to(_PROJECT_ROOT.resolve())
            except ValueError:
                return None
            return full
        # If we're asking for a path and base is a dir, allow listing and reading under it
        if base.endswith("/") or not os.path.splitext(base)[1]:
            if relative_path.startswith(base.rstrip("/") + "/") or relative_path == base.rstrip("/"):
                full = _PROJECT_ROOT / relative_path
                try:
                    full.resolve().relative_to(_PROJECT_ROOT.resolve())
                except ValueError:
                    return None
                return full
    return None


def list_readable() -> List[Tuple[str, bool]]:
    """
    List all readable paths: (relative_path, is_directory).
    Expands directories to their contents (one level for dirs).
    """
    result: List[Tuple[str, bool]] = []
    for base in get_readable_paths():
        base = base.strip().strip("/")
        full = _PROJECT_ROOT / base
        if not full.exists():
            continue
        try:
            rel = str(full.relative_to(_PROJECT_ROOT))
        except ValueError:
            rel = base
        if full.is_file():
            result.append((rel.replace("\\", "/"), False))
        else:
            result.append((rel.replace("\\", "/"), True))
            try:
                for child in sorted(full.iterdir()):
                    if child.name.startswith("."):
                        continue
                    child_rel = str(child.relative_to(_PROJECT_ROOT)).replace("\\", "/")
                    result.append((child_rel, child.is_dir()))
            except PermissionError:
                pass
    return result


def read_file(relative_path: str) -> Optional[str]:
    """
    Read content of an allowlisted file. Returns None if path not allowed or not a file.
    """
    path = _resolve_path(relative_path)
    if path is None or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None
