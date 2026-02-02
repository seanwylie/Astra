"""
Astra Evolution: Sandbox for running Astra-grown tools.

Runs a script inside the evolution sandbox directory with restricted environment.
No filesystem access outside sandbox; network only if allowlisted for the tool.
"""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.evolution.tool_registry import get_tool_by_name, get_active_tools

# Sandbox dir: app/core/evolution/sandbox/
_SANDBOX_DIR = Path(__file__).resolve().parent / "sandbox"
DEFAULT_TIMEOUT = 30


def get_sandbox_dir() -> Path:
    return _SANDBOX_DIR


def run_script_in_sandbox(
    script_path: str | Path,
    args: Optional[List[str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    allow_network: bool = False,
    env_override: Optional[Dict[str, str]] = None,
) -> tuple[int, str, str]:
    """
    Run a Python script inside the sandbox. Script path must be under _SANDBOX_DIR.

    Returns (returncode, stdout, stderr).
    """
    script_path = Path(script_path).resolve()
    try:
        script_path.resolve().relative_to(_SANDBOX_DIR.resolve())
    except ValueError:
        return -1, "", "Script path is outside evolution sandbox."

    args = args or []
    env = os.environ.copy()
    # Project root = parent of app/ (sandbox is app/core/evolution/sandbox)
    _project_root = _SANDBOX_DIR.parent.parent.parent.parent
    env["PYTHONPATH"] = os.pathsep.join(
        [str(env.get("PYTHONPATH", "")), str(_project_root)]
    ).lstrip(os.pathsep)
    if not allow_network:
        env["ASTRA_SANDBOX_NO_NETWORK"] = "1"
    if env_override:
        env.update(env_override)

    try:
        result = subprocess.run(
            ["python3", str(script_path)] + args,
            cwd=str(_SANDBOX_DIR),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return -2, "", "Script timed out."
    except Exception as e:
        return -3, "", str(e)


def run_tool_by_name(name: str, args: Optional[List[str]] = None) -> tuple[bool, str]:
    """
    Look up an active tool by name and run it in the sandbox.
    Returns (success, output_message).
    """
    tool = get_tool_by_name(name)
    if not tool:
        return False, f"No active tool named '{name}'."
    script_path = tool.get("script_path")
    if not script_path:
        return False, f"Tool '{name}' has no script_path."
    path = Path(script_path)
    if not path.is_absolute():
        path = _SANDBOX_DIR / path
    if not path.exists():
        return False, f"Script not found: {path}"
    allowed_ops = tool.get("allowed_ops") or []
    allow_network = "network" in allowed_ops or "ping" in allowed_ops
    code, out, err = run_script_in_sandbox(path, args=args, allow_network=allow_network)
    if code == 0:
        return True, (out or "").strip() or "(no output)"
    msg = err or out or f"Exit code {code}"
    return False, msg
