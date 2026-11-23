"""Protect main-study dispatch, immutable archives and observational progress."""

import hashlib
import importlib.util
import json
import sys
import tarfile
import types
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ringdown_sr.main_study_archiving import archive

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.mark.parametrize("action", ["run", "verify"])
@pytest.mark.parametrize(
    "signal,previous", [("signal_250_6ms", False), ("signal_200_4ms", True)]
)
def test_wrong_section_dependencies_rejected_before_import(action, signal, previous):
    command = load("run_main_study")
    arguments = [
        action,
        "--inputs",
        "i",
        "--technical",
        "t",
        "--output",
        "o",
        "--signal",
        signal,
    ]
    if previous:
        arguments += ["--previous", "p"]
    if action == "verify":
        arguments += ["--export", "v"]
    with pytest.raises(SystemExit) as error:
        command.main(arguments)
    assert error.value.code == 2


def test_verify_requires_separate_costed_export():
    with pytest.raises(SystemExit):
        load("run_main_study").parser().parse_args(
            [
                "verify",
                "--inputs",
                "i",
                "--technical",
                "t",
                "--output",
                "o",
                "--signal",
                "signal_200_4ms",
            ]
        )


def test_verification_dispatch_cannot_start_searches(monkeypatch):
    import ringdown_sr

    calls = []
    module = types.ModuleType("main_study")
    module.verify = lambda *args, **kwargs: calls.append((args, kwargs))
    module.run = lambda *args, **kwargs: pytest.fail("Verification launched a search")
    monkeypatch.setitem(sys.modules, "ringdown_sr.main_study", module)
    monkeypatch.setattr(ringdown_sr, "main_study", module, raising=False)
    assert (
        load("run_main_study").main(
            [
                "verify",
                "--inputs",
                "i",
                "--technical",
                "t",
                "--output",
                "o",
                "--signal",
                "signal_250_6ms",
                "--previous",
                "p",
                "--export",
                "v",
            ]
        )
        == 0
    )
    assert calls == [
        (
            (Path("i"), Path("t"), Path("o")),
            {
                "signal_id": "signal_250_6ms",
                "previous": Path("p"),
                "export": Path("v"),
            },
        )
    ]


def test_archive_preserves_failed_partial_bytes_and_refuses_overwrite(tmp_path):
    root = tmp_path / "run"
    write(root / "signal_200_4ms/run_state.json", {"status": "aborted"})
    write(root / "signal_200_4ms-call.json", {"status": "aborted", "wall_seconds": 8})
    write(root / "workflow_state.json", {"status": "aborted"})
    original = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    output = archive(root, "partial")
    with tarfile.open(output) as packed:
        for name, raw in original.items():
            assert packed.extractfile("run/" + name).read() == raw
        receipt = json.load(packed.extractfile("run/ARCHIVE-partial.json"))
        assert receipt["files_sha256"] == {
            name: hashlib.sha256(raw).hexdigest() for name, raw in original.items()
        }
        assert "scientific verification is a separate step" in receipt["scope"]
    assert (
        output.with_name(output.name + ".sha256").read_text()
        == f"{hashlib.sha256(output.read_bytes()).hexdigest()}  {output.name}\n"
    )
    with pytest.raises(ValueError, match="already exists"):
        archive(root, "partial")
    assert {name: (root / name).read_bytes() for name in original} == original


def test_archive_requires_predecessors_and_rejects_symlinks(tmp_path):
    root = tmp_path / "run"
    root.mkdir()
    with pytest.raises(ValueError, match="predecessor"):
        archive(root, "signal_200_4ms")
    outside = tmp_path / "outside"
    outside.write_text("original")
    (root / "linked").symlink_to(outside)
    with pytest.raises(ValueError, match="regular"):
        archive(root, "partial")
    assert outside.read_text() == "original"


def test_missing_progress_is_read_only_and_counts_all_planned_workers(tmp_path):
    watch = load("watch_main_study")
    root = tmp_path / "not-started"
    result = watch.snapshot(root)
    assert not root.exists()
    assert (
        sum(block["planned_processes"] for block in result["blocks"].values()) == 1280
    )
    assert all(block["finished_processes"] == 0 for block in result["blocks"].values())
    assert "kein wissenschaftlicher Erfolgsnachweis" in watch.render(result)


def test_stale_running_progress_and_partial_costs_never_imply_completion(tmp_path):
    watch = load("watch_main_study")
    signal = "signal_200_4ms"
    case = signal + "-ar1-01"
    root = tmp_path / "run"
    package = root / signal / "cases" / case / "symbolic/ordinary"
    write(
        root / signal / "run_state.json",
        {"status": "aborted", "cases": [{"id": case, "status": "running"}]},
    )
    write(
        package / "run_state.json",
        {"members": ["finished", "running", "planned", "planned"]},
    )
    write(
        package / "member-01/outcome.json",
        {"status": "fit_error", "worker_wall_seconds": 9.0},
    )
    write(
        package / "member-02/metadata.json",
        {"worker_started_at": "2026-11-23T10:00:00+00:00", "phase": "fit"},
    )
    write(
        root / (signal + "-call.json"),
        {
            "wall_seconds": 300.0,
            "cpu_user_seconds": 200.0,
            "cpu_system_seconds": 2.0,
            "cpu_measurement_complete": False,
        },
    )
    original = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    result = watch.snapshot(root, now=datetime(2026, 11, 23, 10, 5, tzinfo=UTC))
    block = result["blocks"][signal]
    assert block["finished_cases"] == 0
    assert block["finished_processes"] == block["recorded_failures"] == 1
    assert block["measured_worker_seconds"] == 9.0
    assert block["invocation_costs"]["wall_seconds"] == 300.0
    assert not block["invocation_costs"]["cpu_measurement_complete"]
    assert block["cases"][0]["conditions"][0]["workers"][1]["seconds"] == 300.0
    assert {path: path.read_bytes() for path in original} == original
