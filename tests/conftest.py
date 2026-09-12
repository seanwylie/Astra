"""
Pytest configuration and fixtures for Astra.
Ensures project root on path, config dir set, and logging in test mode.
"""
import os
import sys
from pathlib import Path

import pytest

# Project root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Point config at project config/ so tests find JSON files
os.environ.setdefault("ASTRA_CONFIG_DIR", str(ROOT / "config"))
# Isolate state from any operator database sitting under data/
os.environ.setdefault("ASTRA_DB_PATH", str(ROOT / "tests" / ".tmp-astra-state.db"))
os.environ.setdefault("ASTRA_MIND_FILE", str(ROOT / "fixtures" / "example_mind.json"))
# Host env must not leak a personal bucket or live keys into the suite.
# Set empty strings so later dotenv.load_dotenv() cannot refill them.
os.environ.pop("S3_BUCKET_NAME", None)
os.environ.pop("ASTRA_S3_BUCKET", None)
os.environ["TOKEN"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["AWS_ACCESS_KEY_ID"] = ""
os.environ["AWS_SECRET_ACCESS_KEY"] = ""

# Optional: reduce noise during tests (set LOG_LEVEL=DEBUG to see logs)
os.environ.setdefault("LOG_LEVEL", "WARNING")


@pytest.fixture
def minimal_mind_dict():
    """Minimal mind data structure for tests that need a mind dict without S3."""
    return {
        "self_reflections": [],
        "self_questions": [],
        "stored_knowledge": [],
    }


def pytest_configure(config):
    """Set up logging in test mode (no console spam). Register markers (also in pyproject.toml)."""
    import logging
    config.addinivalue_line(
        "markers", "integration: marks tests as integration (external services; run with -m 'not integration' for unit-only)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit (no external services)"
    )
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "WARNING")),
        format="%(name)s - %(levelname)s - %(message)s",
    )
