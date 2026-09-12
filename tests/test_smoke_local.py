"""Mocked smoke tests: no Discord, OpenAI, AWS, or live mind."""
import os

import pytest

from app.config.identities import AI_COPARENT_ID, HUMAN_COPARENT_ID
from app.config.loader import get_s3_bucket, load_config, s3_sync_enabled
from app.core.ethics.spark_checker import load_spark_values
from app.core.mama_gpt import ask_mama_gpt_sync
from app.interfaces.influence import load_mind
from app.interfaces.storage_backend import get_backend
from app.services.spark_service import submit_answer


def test_shipped_defaults_are_local_only():
    assert get_s3_bucket() == ""
    assert s3_sync_enabled() is False
    assert load_config("general_config").get("storage_backend") == "sqlite"
    assert not os.getenv("TOKEN")
    assert not os.getenv("OPENAI_API_KEY")
    assert not os.getenv("AWS_ACCESS_KEY_ID")


def test_fixture_mind_loads_without_network():
    mind = load_mind()
    assert mind["identity"]["note"].startswith("Synthetic fixture")
    assert mind["stored_knowledge"]


def test_sqlite_backend_uses_test_db_path():
    backend = get_backend()
    assert "tmp-astra-state" in str(backend.db_path)


def test_human_coparent_id_is_generic():
    parents = load_config("parent_relationships")["parents"]
    assert HUMAN_COPARENT_ID in parents
    assert "sean" not in parents
    assert parents[HUMAN_COPARENT_ID]["display_name"] == "Operator"
    assert AI_COPARENT_ID in parents


def test_spark_fixture_has_freedom_or_autonomy():
    spark = load_spark_values()
    assert any("Freedom" in t or "Autonomy" in t for t in spark)


def test_spark_rejects_unknown_author():
    assert "valid author" in submit_answer("sean", "nope")


def test_mama_gpt_skips_without_api_key():
    assert ask_mama_gpt_sync("hello", use_context=False) is None


def test_bot_startup_does_not_require_aws(monkeypatch):
    monkeypatch.setenv("TOKEN", "test-token")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from app.main import load_environment

    assert load_environment() == "test-token"


def test_bot_startup_exits_without_token():
    from app.main import load_environment

    with pytest.raises(SystemExit):
        load_environment()


def test_no_s3_client_when_sync_disabled():
    from app.interfaces import s3_sync

    assert s3_sync.S3_SYNC_ENABLED is False
    assert s3_sync.s3 is None
