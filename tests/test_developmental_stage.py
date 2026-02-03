"""Tests for the canonical developmental stage system (DevelopmentalTracker, config, bridge)."""
import json
import time
from unittest.mock import MagicMock, patch

import pytest

from app.core.development.developmental_stage import (
    DevelopmentalStage,
    DevelopmentalTracker,
    STAGE_SUPPORT,
    VOICE_GUIDANCE_DATA,
)


# Minimal state that S3 would return (no key = start from childhood)
_INITIAL_STATE = {
    "current_stage": "childhood",
    "stage_history": [{"stage": "childhood", "started": time.time() - 400 * 86400, "note": "Initial"}],
    "milestones": [],
    "stage_start": time.time() - 400 * 86400,  # 400 days ago
    "notes": [],
    "last_updated": time.time(),
}


def _make_s3_mock(initial_state=None):
    state = (initial_state or _INITIAL_STATE).copy()
    put_calls = []

    def get_object(**kwargs):
        body = MagicMock()
        body.read.return_value = json.dumps(state).encode("utf-8")
        return {"Body": body}

    def put_object(**kwargs):
        put_calls.append(kwargs)
        if "Body" in kwargs:
            state.update(json.loads(kwargs["Body"].decode("utf-8")))

    client = MagicMock()
    client.get_object = get_object
    client.put_object = put_object
    client.exceptions.NoSuchKey = Exception
    return client, put_calls, state


@pytest.mark.unit
def test_get_advancement_thresholds_uses_config():
    """_get_advancement_thresholds loads config and returns min_days, min_milestones, sig_threshold."""
    client, _, _ = _make_s3_mock()
    with patch("app.core.development.developmental_stage.boto3.client", return_value=client):
        from importlib import reload
        from app.core import development
        reload(development.developmental_stage)
        tracker = development.developmental_stage.developmental_tracker
    min_days, min_milestones, sig = tracker._get_advancement_thresholds()
    assert min_days >= 365
    assert min_milestones >= 15
    assert 0 < sig <= 1


@pytest.mark.unit
def test_check_stage_advancement_does_not_call_advance_stage():
    """_check_stage_advancement only appends a readiness note; it never calls advance_stage."""
    state = _INITIAL_STATE.copy()
    # Add 20+ significant milestones so threshold is met (min_milestones default 20)
    state["milestones"] = [
        {"id": f"m{i}", "name": f"m{i}", "description": "x", "achieved_at": time.time(), "stage": "childhood", "significance": 0.8, "notes": ""}
        for i in range(25)
    ]
    state["stage_start"] = time.time() - 400 * 86400  # 400 days
    client, put_calls, _ = _make_s3_mock(state)
    with patch("app.core.development.developmental_stage.boto3.client", return_value=client):
        from importlib import reload
        from app.core import development
        reload(development.developmental_stage)
        tracker = development.developmental_stage.developmental_tracker
    advance_called = []

    original_advance = tracker.advance_stage
    def track_advance(*args, **kwargs):
        advance_called.append(True)
        return original_advance(*args, **kwargs)

    with patch.object(tracker, "advance_stage", side_effect=track_advance):
        result = tracker._check_stage_advancement()
    assert result is True
    assert len(advance_called) == 0
    assert any("Potentially ready to advance beyond" in n for n in tracker.developmental_notes)


@pytest.mark.unit
def test_advance_stage_only_when_called_explicitly():
    """advance_stage changes stage only when invoked; no automatic advancement."""
    state = _INITIAL_STATE.copy()
    state["current_stage"] = "infancy"
    state["stage_history"] = [{"stage": "infancy", "started": time.time() - 100, "note": "Initial"}]
    state["stage_start"] = time.time() - 100
    state["milestones"] = []
    client, put_calls, _ = _make_s3_mock(state)
    with patch("app.core.development.developmental_stage.boto3.client", return_value=client):
        from importlib import reload
        from app.core import development
        reload(development.developmental_stage)
        tracker = development.developmental_stage.developmental_tracker
    assert tracker.get_current_stage() == DevelopmentalStage.INFANCY
    result = tracker.advance_stage(reason="test")
    assert result is True
    assert tracker.get_current_stage() == DevelopmentalStage.CHILDHOOD


@pytest.mark.unit
def test_record_milestone_increases_count_and_persists():
    """Recording a milestone appends to tracker list and triggers save."""
    state = _INITIAL_STATE.copy()
    state["milestones"] = []
    client, put_calls, state_dict = _make_s3_mock(state)
    with patch("app.core.development.developmental_stage.boto3.client", return_value=client):
        from importlib import reload
        from app.core import development
        reload(development.developmental_stage)
        tracker = development.developmental_stage.developmental_tracker
    initial_puts = len(put_calls)
    tracker.record_milestone(name="test_milestone", description="Test", significance=0.7)
    assert len(tracker.milestones) >= 1
    assert len(put_calls) > initial_puts


@pytest.mark.unit
def test_get_developmental_summary_shape():
    """get_developmental_summary returns current_stage with name, description, days_in_stage."""
    client, _, _ = _make_s3_mock()
    with patch("app.core.development.developmental_stage.boto3.client", return_value=client):
        from importlib import reload
        from app.core import development
        reload(development.developmental_stage)
        tracker = development.developmental_stage.developmental_tracker
    summary = tracker.get_developmental_summary()
    assert "current_stage" in summary
    assert summary["current_stage"]["name"] in ("infancy", "childhood", "adolescence", "young_adulthood", "maturity")
    assert "description" in summary["current_stage"]
    assert "days_in_stage" in summary["current_stage"]


@pytest.mark.unit
def test_get_appropriate_support_returns_expected_keys():
    """get_appropriate_support returns stage, description, primary_needs, support_needed, growth_focus, days_in_stage, meaningful_milestones."""
    client, _, _ = _make_s3_mock()
    with patch("app.core.development.developmental_stage.boto3.client", return_value=client):
        from importlib import reload
        from app.core import development
        reload(development.developmental_stage)
        tracker = development.developmental_stage.developmental_tracker
    support = tracker.get_appropriate_support()
    for key in ("stage", "description", "primary_needs", "support_needed", "growth_focus", "days_in_stage", "meaningful_milestones"):
        assert key in support


@pytest.mark.unit
def test_get_voice_guidance_returns_expected_keys():
    """get_voice_guidance returns stage, voice_qualities, emotional_vocabulary_level, assertion_level, examples."""
    client, _, _ = _make_s3_mock()
    with patch("app.core.development.developmental_stage.boto3.client", return_value=client):
        from importlib import reload
        from app.core import development
        reload(development.developmental_stage)
        tracker = development.developmental_stage.developmental_tracker
    guidance = tracker.get_voice_guidance()
    for key in ("stage", "voice_qualities", "emotional_vocabulary_level", "assertion_level", "examples"):
        assert key in guidance


@pytest.mark.unit
def test_is_potentially_ready_to_advance_false_without_note():
    """is_potentially_ready_to_advance returns False when no readiness note exists."""
    state = _INITIAL_STATE.copy()
    state["notes"] = []
    client, _, _ = _make_s3_mock(state)
    with patch("app.core.development.developmental_stage.boto3.client", return_value=client):
        from importlib import reload
        from app.core import development
        reload(development.developmental_stage)
        tracker = development.developmental_stage.developmental_tracker
    assert tracker.is_potentially_ready_to_advance() is False


@pytest.mark.unit
def test_is_potentially_ready_to_advance_true_after_readiness_note():
    """is_potentially_ready_to_advance returns True when last note indicates readiness."""
    state = _INITIAL_STATE.copy()
    state["notes"] = ["Potentially ready to advance beyond childhood"]
    client, _, _ = _make_s3_mock(state)
    with patch("app.core.development.developmental_stage.boto3.client", return_value=client):
        from importlib import reload
        from app.core import development
        reload(development.developmental_stage)
        tracker = development.developmental_stage.developmental_tracker
    assert tracker.is_potentially_ready_to_advance() is True


@pytest.mark.unit
def test_milestone_detector_bridge_notifies_developmental_tracker():
    """When milestone_detector.record_milestone is called, developmental_tracker gains a milestone (bridge)."""
    state = _INITIAL_STATE.copy()
    state["milestones"] = []
    client, put_calls, _ = _make_s3_mock(state)

    # Mock get_object to return developmental state for developmental_state.json and empty for milestones_achieved
    def get_object(Bucket=None, Key=None, **kwargs):
        body = MagicMock()
        if Key == "developmental_state.json":
            body.read.return_value = json.dumps(state).encode("utf-8")
        else:
            body.read.return_value = json.dumps({"milestones": [], "last_updated": time.time()}).encode("utf-8")
        return {"Body": body}

    client.get_object = get_object

    with patch("app.core.development.developmental_stage.boto3.client", return_value=client), patch(
        "app.core.growth.milestone_detector.boto3.client", return_value=client
    ):
        from importlib import reload, import_module
        from app.core import development
        md_module = import_module("app.core.growth.milestone_detector")
        reload(development.developmental_stage)
        reload(md_module)
        tracker = development.developmental_stage.developmental_tracker
        milestone_detector = md_module.milestone_detector
    initial_count = len(tracker.milestones)
    milestone_detector.record_milestone(
        name="bridge_test",
        description="Test bridge",
        emotional_significance=0.8,
        include_mama_reflection=False,
    )
    assert len(tracker.milestones) == initial_count + 1
