import pytest

from zavero import actionlog


@pytest.fixture(autouse=True)
def _private_action_log(tmp_path, monkeypatch):
    """Tests must never write fake events into the real logs/actions.jsonl."""
    monkeypatch.setattr(actionlog, "_PATH", tmp_path / "actions.jsonl")
    monkeypatch.setattr(actionlog, "FEEDBACK", tmp_path / "feedback.jsonl")
