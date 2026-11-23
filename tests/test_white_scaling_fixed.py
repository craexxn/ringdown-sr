"""Check retained fixed-worker failures and original formula records."""

import json

import pytest

from ringdown_sr import white_scaling_fixed as fixed
from ringdown_sr.pilot import _write_json


def test_later_fixed_failure_preserves_finished_start(tmp_path, monkeypatch):
    record = {"tree": {"kind": "constant", "value_hex": (1.0).hex()}, "elapsed": 0.25}

    def fail_after_one(directory):
        _write_json(directory / "fixed-start-01.json", record)
        _write_json(
            directory / "fixed_status.json",
            {"format": fixed.FORMAT, "status": "running", "current_start": 2},
        )
        raise ValueError("injected second-start failure")

    monkeypatch.setattr(fixed, "_run", fail_after_one)
    with pytest.raises(ValueError, match="injected second-start failure"):
        fixed.run(tmp_path)
    assert json.loads((tmp_path / "fixed-start-01.json").read_text()) == record
    status = json.loads((tmp_path / "fixed_status.json").read_text())
    assert status["status"] == "failed"
    assert status["current_start"] == 2
    assert status["completed_starts"] == 1
    assert status["worker_body_seconds"] >= 0
    assert "injected second-start failure" in status["error"]
    assert not (tmp_path / "fixed_result.json").exists()
    with pytest.raises(ValueError, match="fresh prepared directory"):
        fixed.run(tmp_path)


def test_fixed_interruption_is_recorded_without_claiming_completion(
    tmp_path, monkeypatch
):
    def interrupt(directory):
        raise KeyboardInterrupt

    monkeypatch.setattr(fixed, "_run", interrupt)
    with pytest.raises(KeyboardInterrupt):
        fixed.run(tmp_path)
    status = json.loads((tmp_path / "fixed_status.json").read_text())
    assert status["status"] == "failed"
    assert status["completed_starts"] == 0
    assert status["error"].startswith("KeyboardInterrupt:")
