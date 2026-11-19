"""Check observational progress accounting, including stale and damaged states."""

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def watch():
    spec = importlib.util.spec_from_file_location(
        "watch_noise_followup", ROOT / "scripts/watch_noise_followup.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def test_missing_root_does_not_create_files(watch, tmp_path):
    root = tmp_path / "not-started"
    value = watch.snapshot(root)
    assert not root.exists()
    assert value["blocks"]["duration"]["finished_processes"] == 0
    assert value["blocks"]["duration"]["planned_processes"] == 416
    assert value["blocks"]["sampling"]["planned_processes"] == 208
    assert "keine neuen Worker" in watch.render(value)
    assert "Laufordner noch nicht vorhanden" in watch.render(value)


def test_invocation_costs_remain_separate_and_incomplete_cpu_is_labelled(
    watch, tmp_path
):
    root = tmp_path / "run"
    for index, complete in enumerate((True, False), 1):
        write(
            root / f"duration/calls/{index:04d}.json",
            {
                "wall_seconds": 3600.0,
                "cpu_user_seconds": 3400.0,
                "cpu_system_seconds": 100.0,
                "cpu_measurement_complete": complete,
            },
        )
    value = watch.snapshot(root)
    costs = value["blocks"]["duration"]["invocation_costs"]
    assert costs == {
        "saved_calls": 2,
        "wall_seconds": 7200.0,
        "cpu_seconds": 7000.0,
        "cpu_measurement_complete": False,
    }
    assert value["blocks"]["duration"]["measured_worker_seconds"] == 0
    rendered = watch.render(value)
    assert "2.00 h" in rendered
    assert "unvollständig" in rendered
    assert "nicht addieren" in rendered


def test_process_outcomes_are_separate_from_scientific_success(watch, tmp_path):
    root = tmp_path / "run"
    package = root / "duration/cases/ar1-01/symbolic/ordinary"
    write(
        root / "duration/run_state.json",
        {
            "status": "aborted",
            "cases": [{"id": "ar1-01", "status": "running"}],
            "error": "clock changed",
        },
    )
    write(
        package / "run_state.json",
        {
            "status": "running",
            "members": ["completed", "finished", "running", "planned"],
        },
    )
    write(
        package / "member-01/outcome.json",
        {"status": "completed", "worker_wall_seconds": 123.0},
    )
    write(
        package / "member-02/outcome.json",
        {"status": "fit_error", "worker_wall_seconds": 7.0},
    )
    write(
        package / "member-02/metadata.json",
        {
            "phase": "failed",
            "failed_during": "fit",
            "error": "ArithmeticError: fixture",
        },
    )
    write(
        package / "member-03/metadata.json",
        {"phase": "fit", "worker_started_at": "2026-11-19T10:00:00+00:00"},
    )
    original = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    value = watch.snapshot(root, now=datetime(2026, 11, 19, 10, 5, tzinfo=UTC))
    block = value["blocks"]["duration"]
    assert block["finished_processes"] == 2
    assert block["recorded_failures"] == 1
    assert block["measured_worker_seconds"] == 130.0
    assert block["finished_cases"] == 0
    active = block["cases"][0]["conditions"][0]["workers"][2]
    assert active["seconds"] == 300.0
    assert active["timing_kind"] == "seit Start*"
    assert not active["process_finished"]
    text = watch.render(value)
    assert "clock changed" in text
    assert "ArithmeticError" in text
    assert "kein wissenschaftlicher Erfolgsnachweis" in text
    assert {path: path.read_bytes() for path in original} == original


def test_malformed_json_and_unknown_paths_never_count_as_success(watch, tmp_path):
    root = tmp_path / "run"
    state = root / "duration/run_state.json"
    write(
        state,
        {
            "status": "running",
            "cases": [
                {"id": "../../outside", "status": "completed"},
                {"id": "ar1-01", "status": "running"},
            ],
        },
    )
    bad = root / "duration/cases/ar1-01/symbolic/ordinary/member-01/outcome.json"
    bad.parent.mkdir(parents=True)
    bad.write_text('{"status":')
    value = watch.snapshot(root)
    assert value["blocks"]["duration"]["finished_cases"] == 0
    assert value["blocks"]["duration"]["finished_processes"] == 0
    assert len(value["warnings"]) >= 2


def test_symlinked_status_is_not_followed(watch, tmp_path):
    root = tmp_path / "run"
    state = root / "duration/run_state.json"
    state.parent.mkdir(parents=True)
    target = tmp_path / "outside.json"
    target.write_text('{"status":"completed"}')
    state.symlink_to(target)
    value = watch.snapshot(root)
    assert value["blocks"]["duration"]["finished_cases"] == 0
    assert any("Link" in item for item in value["warnings"])


def test_invalid_and_boolean_costs_are_not_measured(watch, tmp_path):
    write(
        tmp_path / "outcome.json", {"status": "completed", "worker_wall_seconds": True}
    )
    value = watch.worker_state(tmp_path, "planned", datetime.now(UTC), [])
    assert value["seconds"] is None
    assert value["timing_kind"] == "—"


@pytest.mark.parametrize("interval", ["0", "-1", "61", "nan", "inf"])
def test_invalid_refresh_intervals_are_rejected(watch, tmp_path, interval):
    with pytest.raises(SystemExit):
        watch.main(["--root", str(tmp_path), "--once", "--interval", interval])


def test_terminal_control_characters_are_not_rendered(watch):
    assert "\x1b" not in watch.clean_text("bad\x1b[2Jstatus\nnext")
