"""Hermetic checks for the open-source local-first defaults."""
from pathlib import Path

from app.config.loader import get_s3_bucket, load_config, s3_sync_enabled
from app.interfaces.influence import load_mind


def test_default_bucket_is_empty():
    assert get_s3_bucket() == ""
    assert s3_sync_enabled() is False


def test_s3_sync_is_off_in_shipped_config():
    config = load_config("general_config")
    assert not config.get("s3_sync_enabled")
    assert not config.get("s3_bucket")


def test_example_mind_loads_without_network():
    mind = load_mind()
    assert mind["identity"]["note"].startswith("Synthetic fixture")
    assert mind["stored_knowledge"]
    assert any("Spark" in item for item in mind["stored_knowledge"])


def test_example_mind_file_is_tracked():
    root = Path(__file__).resolve().parent.parent
    path = root / "fixtures" / "example_mind.json"
    assert path.is_file()
    assert path.stat().st_size < 8_000
