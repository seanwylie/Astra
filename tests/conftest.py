"""
Pytest configuration and fixtures for Astra.
Ensures project root on path, config dir set, and logging in test mode.
"""
import os
import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Point config at project config/ so tests find JSON files
os.environ.setdefault("ASTRA_CONFIG_DIR", str(ROOT / "config"))

# Optional: reduce noise during tests (set LOG_LEVEL=DEBUG to see logs)
os.environ.setdefault("LOG_LEVEL", "WARNING")


def pytest_configure(config):
    """Set up logging in test mode (no console spam)."""
    import logging
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "WARNING")),
        format="%(name)s - %(levelname)s - %(message)s",
    )
