"""Exercise crossover evidence, ordering and failure closure without scientific fits."""

import copy
import io
import os
import signal
import subprocess
import tarfile
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from ringdown_sr import seed_driver_crosscheck as cross
from ringdown_sr.pilot import _json_bytes, _sha256, _write_json
from ringdown_sr.search_duration import load_module

BRIDGE = load_module(cross.ROOT / cross.BRIDGE, "test_crosscheck_bridge")
CLOCK = load_module(
    cross.ROOT / "scripts/run_trigonometric_grammar.py", "test_crosscheck_clock"
)


def environment():
    return {
        "python_version": "3.12.14",
        "platform": "reference-host",
        "packages": {"numpy": "2.5.3"},
        "numerical_libraries": {
            "snapshot": "before_fit",
            "numpy_build": {},
            "scipy_build": {},
            "threadpools": {
                "details": [
                    {
                        "filepath": "/old/lib.so",
                        "version": "1",
                        "architecture": "Haswell",
                        "num_threads": 1,
                    }
                ]
            },
        },
    }


def evidence():
    return {
        "signature": {
            "front": [
                {
                    "tree": {"value_hex": "0x1p0"},
                    "complexity": 1,
                    "loss_hex": "0x0p0",
                    "prediction": "abc",
                    "residual": "def",
                }
            ],
            "selected_index": 0,
            "rng": {"python_seed": 1, "backend_seed": 2},
        },
        "parameters": {"niterations": 500},
        "backend_options": {"seed": 2},
        "callback_calls_during_fit": 100,
        "markers": {
            "curve": "within_tolerance",
            "structure": "supported",
            "parameters": "match",
        },
        "worker_wall_seconds": 10,
        "environment": environment(),
        "environment_after_search": environment(),
    }


def tar_bytes(files, extra=()):
    archive = io.BytesIO()
    values = {
        **files,
        "checksums.json": _json_bytes({n: _sha256(v) for n, v in files.items()}),
    }
    with tarfile.open(fileobj=archive, mode="w:gz") as stream:
        for name, contents in values.items():
            info = tarfile.TarInfo("reference/" + name)
            info.size = len(contents)
            stream.addfile(info, io.BytesIO(contents))
        for info, contents in extra:
            stream.addfile(info, io.BytesIO(contents))
    return archive.getvalue()


@pytest.mark.parametrize("contents", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'])
def test_ambiguous_json_is_rejected(contents):
    with pytest.raises(ValueError):
        cross.read_json(contents)


@pytest.mark.parametrize(
    "name",
    [
        "/absolute",
        "../escape",
        "reference/../escape",
        "reference//file",
        "./reference/file",
    ],
)
def test_archive_paths_cannot_escape_or_alias(name):
    info = tarfile.TarInfo(name)
    info.size = 1
    with pytest.raises(ValueError):
        cross.archive_files(
            tar_bytes({"file": b"original"}, [(info, b"x")]), "reference"
        )


@pytest.mark.parametrize("kind", [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE])
def test_archive_links_and_special_members_are_rejected(kind):
    info = tarfile.TarInfo("reference/link")
    info.type, info.linkname = kind, "file"
    with pytest.raises(ValueError):
        cross.archive_files(
            tar_bytes({"file": b"original"}, [(info, b"")]), "reference"
        )


def test_archive_duplicate_or_unlisted_members_fail():
    for name in ("file", "extra"):
        info = tarfile.TarInfo("reference/" + name)
        info.size = 1
        with pytest.raises(ValueError):
            cross.archive_files(
                tar_bytes({"file": b"original"}, [(info, b"x")]), "reference"
            )
    assert (
        cross.archive_files(tar_bytes({"file": b"original"}), "reference")["file"]
        == b"original"
    )


def test_wrong_original_archive_stops_before_extraction(tmp_path, monkeypatch):
    path = tmp_path / "archive"
    path.write_bytes(b"different")
    monkeypatch.setattr(
        cross, "archive_files", lambda *a: pytest.fail("must not extract")
    )
    with pytest.raises(ValueError, match="original reference"):
        cross.read_reference(path, "outer")


def test_frozen_anchor_bits_match_the_historical_bridge_contract():
    from ringdown_sr.noiseless_control import fingerprint

    for name, values in cross.anchor_arrays().items():
        shape, digest = BRIDGE.ANCHOR[name]
        assert fingerprint(values) == {"shape": shape, "dtype": "<f8", "sha256": digest}
    assert cross.source_hashes()[cross.PLAN] == cross.PLAN_SHA256


def test_reference_arrays_require_all_roles_and_exact_bits():
    arrays = cross.anchor_arrays()

    def files():
        result = {}
        for filename, keys in (
            ("training.npz", ("time_s", "observed")),
            ("diagnostic.npz", ("diagnostic_time_s", "diagnostic_truth")),
        ):
            stream = io.BytesIO()
            np.savez(stream, **{k: arrays[k] for k in keys})
            result[filename] = stream.getvalue()
        return result

    assert set(cross.reference_arrays(files(), "outer")) == set(arrays)
    arrays["observed"] = arrays["observed"].copy()
    arrays["observed"][3] = np.nextafter(arrays["observed"][3], np.inf)
    with pytest.raises(ValueError, match="bits"):
        cross.reference_arrays(files(), "outer")


@pytest.mark.parametrize(
    "field", ["signature", "parameters", "backend_options", "callback_calls_during_fit"]
)
def test_matching_success_markers_do_not_hide_search_mismatches(field):
    old, new = evidence(), evidence()
    new[field] = "different"
    result = cross.comparison(old, new)
    assert result["markers_equal"] and not result["all_search_features_equal"]
    assert result["matches"][field] is False


@pytest.mark.parametrize(
    "field", ["tree", "complexity", "loss_hex", "prediction", "residual"]
)
def test_entire_front_including_unselected_entries_is_compared(field):
    old, new = evidence(), evidence()
    old["signature"]["front"].append(copy.deepcopy(old["signature"]["front"][0]))
    new["signature"] = copy.deepcopy(old["signature"])
    new["signature"]["front"][1][field] = "changed"
    assert not cross.comparison(old, new)["matches"]["signature"]


def test_environment_ignores_only_paths_snapshot_and_pool_order():
    old, new = environment(), environment()
    new["numerical_libraries"]["snapshot"] = "options"
    new["numerical_libraries"]["threadpools"]["details"][0]["filepath"] = "/new/lib.so"
    assert cross.environment_key(old) == cross.environment_key(new)
    for key, value in (("version", "2"), ("architecture", "other"), ("num_threads", 2)):
        changed = copy.deepcopy(new)
        changed["numerical_libraries"]["threadpools"]["details"][0][key] = value
        assert cross.environment_key(old) != cross.environment_key(changed)
    new["packages"]["numpy"] = "other"
    assert cross.environment_key(old) != cross.environment_key(new)


@pytest.fixture
def orchestrator(tmp_path, monkeypatch):
    anchor = cross.anchor_arrays()
    monkeypatch.setattr(cross, "anchor_arrays", lambda: anchor)
    root = tmp_path / "repo"
    root.mkdir()
    pins = (
        "uv.lock",
        "pyproject.toml",
        ".python-version",
        "julia/Project.toml",
        "julia/Manifest.toml",
        "src/ringdown_sr/juliapkg.json",
    )
    for name in pins:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text("pin")
    monkeypatch.setattr(cross, "ROOT", root)
    monkeypatch.setattr(cross, "scientific_platform", lambda: None)
    monkeypatch.setattr(cross, "source_hashes", lambda: {cross.BRIDGE: "bridge"})
    monkeypatch.setattr(cross, "_provenance", lambda: {"git": {"dirty": False}})
    monkeypatch.setattr(cross, "load_module", lambda *a: CLOCK)
    monkeypatch.setattr(
        cross,
        "read_reference",
        lambda *a: (b"original archive", {"reference.txt": b"proof"}),
    )
    events = []

    def git(*args):
        events.append(args[:2])
        if args[1] == "add":
            target = Path(args[3])
            for name in pins:
                (target / name).parent.mkdir(parents=True, exist_ok=True)
                (target / name).write_bytes((root / name).read_bytes())
        elif args[1] == "remove":
            import shutil

            shutil.rmtree(args[2])

    monkeypatch.setattr(cross, "git", git)
    state = SimpleNamespace(
        events=events, hook=lambda *a: None, output=tmp_path / "result"
    )

    def bridge(checkout, action, kind, output, request, clock):
        state.events.append((action, kind))
        state.hook(action, kind, output)
        if action == "verify":
            _write_json(output, evidence())
        elif action == "prepare":
            output.mkdir()
            _write_json(
                output / "options.json", {"initial": {"environment": environment()}}
            )
        else:
            _write_json(output / "verified.json", evidence())

    monkeypatch.setattr(cross, "call_bridge", bridge)
    state.bridge = bridge
    state.run = lambda: cross.run("outer.tar.gz", "transfer.tar.gz", state.output)
    return state


def test_both_preflights_precede_exactly_two_crossovers_and_final_manifest(
    orchestrator,
):
    state = orchestrator
    report = state.run()
    assert report["outcome"] == "both_crossovers_reproduced"
    operations = [e for e in state.events if e[0] != "worktree"]
    assert operations == [
        ("verify", "outer"),
        ("verify", "transfer"),
        ("prepare", "transfer"),
        ("prepare", "outer"),
        ("run", "transfer"),
        ("run", "outer"),
    ]
    expected = cross.read_json(
        (state.output / "crosscheck_checksums.json").read_bytes()
    )
    assert expected == {
        p.relative_to(state.output).as_posix(): _sha256(p.read_bytes())
        for p in state.output.rglob("*")
        if p.is_file() and p.name != "crosscheck_checksums.json"
    }


@pytest.mark.parametrize(
    "fault",
    [
        "first_prepare",
        "second_prepare",
        "second_run",
        "timeout",
        "signal",
        "consumed_bytes",
        "environment",
    ],
)
def test_failed_runs_retain_evidence_and_never_publish_a_positive_outcome(
    orchestrator, monkeypatch, fault
):
    state = orchestrator

    def bridge(*args):
        action, kind, output = args[1:4]
        if (
            (fault == "first_prepare" and (action, kind) == ("prepare", "transfer"))
            or (fault == "second_prepare" and (action, kind) == ("prepare", "outer"))
            or (fault == "second_run" and (action, kind) == ("run", "outer"))
        ):
            raise ValueError("injected")
        if action == "run" and fault == "timeout":
            raise TimeoutError("injected")
        if action == "run" and fault == "signal":
            os.kill(os.getpid(), signal.SIGTERM)
        if action == "run" and fault == "consumed_bytes":
            (state.output / "inputs/anchor.npz").write_bytes(b"mutated")
        state.bridge(*args)
        if action == "prepare" and kind == "outer" and fault == "environment":
            changed = environment()
            changed["packages"]["numpy"] = "wrong"
            _write_json(output / "options.json", {"initial": {"environment": changed}})

    monkeypatch.setattr(cross, "call_bridge", bridge)
    with pytest.raises((ValueError, TimeoutError, InterruptedError)):
        state.run()
    report = cross.read_json((state.output / "crosscheck_report.json").read_bytes())
    assert report["status"] == "failed" and report["outcome"] == "not_assessed"
    assert not (state.output / "crosscheck_checksums.json").exists()
    assert (state.output / "inputs/anchor.npz").exists()
    if fault in ("first_prepare", "second_prepare", "environment"):
        assert not any(e[0] == "run" for e in state.events)


def test_finalization_failure_revokes_success(orchestrator, monkeypatch):
    original = cross._write_json
    published = []

    def write(path, value):
        original(path, value)
        if path.name == "crosscheck_checksums.json":
            published.append(path)
            raise OSError("publication failure")

    monkeypatch.setattr(cross, "_write_json", write)
    with pytest.raises(OSError):
        orchestrator.run()
    assert len(published) == 1
    assert (
        cross.read_json((orchestrator.output / "crosscheck_report.json").read_bytes())[
            "outcome"
        ]
        == "not_assessed"
    )
    assert not (orchestrator.output / "crosscheck_checksums.json").exists()


@pytest.mark.parametrize(
    "filename", ["crosscheck_summary.md", "crosscheck_checksums.json"]
)
def test_late_final_document_changes_revoke_success(
    orchestrator, monkeypatch, filename
):
    write_bytes = Path.write_bytes
    changed = []

    def change_after_pending_report(path, contents):
        result = write_bytes(path, contents)
        if (
            path == orchestrator.output / "crosscheck_report.json.tmp"
            and cross.read_json(contents)["status"] == "completed"
        ):
            changed.append(filename)
            write_bytes(orchestrator.output / filename, b"changed after verification\n")
        return result

    monkeypatch.setattr(Path, "write_bytes", change_after_pending_report)
    with pytest.raises(ValueError, match="Final crossover documents changed"):
        orchestrator.run()
    assert changed == [filename]
    report = cross.read_json(
        (orchestrator.output / "crosscheck_report.json").read_bytes()
    )
    assert report["status"] == "failed" and report["outcome"] == "not_assessed"
    assert len(report["comparisons"]) == 2
    assert not (orchestrator.output / "crosscheck_checksums.json").exists()
    assert "not_assessed" in (orchestrator.output / "crosscheck_summary.md").read_text()


def test_valid_search_difference_is_reported_without_rerunning(
    orchestrator, monkeypatch
):
    state = orchestrator

    def bridge(*args):
        state.bridge(*args)
        if args[1:3] == ("run", "outer"):
            result = evidence()
            result["callback_calls_during_fit"] += 1
            _write_json(args[3] / "verified.json", result)

    monkeypatch.setattr(cross, "call_bridge", bridge)
    report = state.run()
    assert (
        report["status"] == "completed"
        and report["outcome"] == "valid_crossovers_differ"
    )
    assert sum(e[0] == "run" for e in state.events) == 2


def test_existing_destinations_are_preserved(orchestrator):
    state = orchestrator
    state.output.mkdir()
    (state.output / "existing").write_bytes(b"keep")
    with pytest.raises(ValueError, match="new crossover output"):
        state.run()
    assert (state.output / "existing").read_bytes() == b"keep"
    assert state.events == []


def test_parent_deadline_interrupts_blocked_preparation(orchestrator, monkeypatch):
    monkeypatch.setattr(cross, "LIMIT_SECONDS", 0.15)
    orchestrator.hook = lambda *a: time.sleep(1)
    with pytest.raises(TimeoutError):
        orchestrator.run()
    assert not any(e[0] == "run" for e in orchestrator.events)


def test_failure_after_positive_report_replace_revokes_every_success_artifact(
    orchestrator, monkeypatch
):
    replace = Path.replace

    def fail_after_publish(path, target):
        result = replace(path, target)
        if path.name == "crosscheck_report.json.tmp":
            report = cross.read_json(Path(target).read_bytes())
            if report["status"] == "completed":
                raise OSError("failure after positive report publication")
        return result

    monkeypatch.setattr(Path, "replace", fail_after_publish)
    with pytest.raises(OSError, match="positive report"):
        orchestrator.run()
    report = cross.read_json(
        (orchestrator.output / "crosscheck_report.json").read_bytes()
    )
    assert report["outcome"] == "not_assessed" and report["status"] == "failed"
    assert not (orchestrator.output / "crosscheck_checksums.json").exists()


@pytest.mark.parametrize(
    "mutation",
    [
        "options_seed",
        "options_count",
        "callbacks",
        "source",
        "references_missing",
        "grammar_missing",
    ],
)
def test_single_seed_preflight_requires_fixed_reference_coverage(mutation):
    control = SimpleNamespace(
        FORMAT="format",
        expected_grammar_cases=lambda: ["case"],
        verify_options=lambda *a: None,
    )
    driver = SimpleNamespace(BASE=None, verify_snapshots=lambda *a: None)
    options = {
        "format": "format",
        "mode": "options",
        "status": "verified",
        "source_sha256": {"source": "sha"},
        "callback_calls": 0,
        "profiles": [{"condition": "local_300_5", "python_seed": 73}],
    }
    references = {
        "format": "format",
        "mode": "references",
        "status": "verified",
        "source_sha256": {"source": "sha"},
        "grammar_cases": ["case"],
        "cases": [
            {"condition": "local_300_5", "frequency_hz": f} for f in (250, 4346, 33018)
        ],
    }

    def verify():
        BRIDGE.verify_preflight(
            options, references, {}, {"source": "sha"}, control, driver, None, None, 73
        )

    verify()
    if mutation == "options_seed":
        options["profiles"][0]["python_seed"] = 74
    elif mutation == "options_count":
        options["profiles"] *= 2
    elif mutation == "callbacks":
        options["callback_calls"] = 1
    elif mutation == "source":
        options["source_sha256"] = {}
    elif mutation == "references_missing":
        references["cases"].pop()
    else:
        references["grammar_cases"] = []
    with pytest.raises(ValueError):
        verify()


@pytest.mark.parametrize(
    "field,value",
    [
        ("seed", 74),
        ("niterations", 500),
        ("scope", "invalid"),
        ("commit", "wrong"),
        ("bridge_sha256", "wrong"),
    ],
)
def test_technical_bridge_rejects_unplanned_requests(
    tmp_path, monkeypatch, field, value
):
    commit = BRIDGE.HISTORIES["outer"][0]
    monkeypatch.setattr(
        BRIDGE,
        "_provenance",
        lambda: {
            "git": {"available": True, "changes": [], "commit": commit, "dirty": False}
        },
    )
    inputs = tmp_path / "input.npz"
    np.savez(inputs, **BRIDGE.technical_arrays())
    request = {
        "scope": "technical",
        "kind": "outer",
        "commit": commit,
        "seed": 73,
        "niterations": 2,
        "inputs": str(inputs),
        "bridge_sha256": _sha256(Path(BRIDGE.__file__).read_bytes()),
    }
    path = tmp_path / "request.json"
    _write_json(path, request)
    support = SimpleNamespace(read_json=cross.read_json)
    BRIDGE.checked_request(path, "outer", "prepare", support)
    request[field] = value
    _write_json(path, request)
    with pytest.raises(ValueError):
        BRIDGE.checked_request(path, "outer", "prepare", support)


def test_scientific_runner_refuses_non_manjaro(monkeypatch):
    monkeypatch.setattr(cross.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        cross.platform, "freedesktop_os_release", lambda: {"ID": "ubuntu"}
    )
    with pytest.raises(ValueError, match="Manjaro"):
        cross.scientific_platform()


def test_secondary_cleanup_failures_and_signals_cannot_preserve_success(
    tmp_path, monkeypatch
):
    report = {
        "status": "completed",
        "comparisons": [cross.comparison(evidence(), evidence())] * 2,
    }
    cross.save_report(tmp_path, report)
    (tmp_path / "crosscheck_checksums.json").write_bytes(b"old manifest")
    unlink = Path.unlink
    attempts = []

    def fail_once(path, *args, **kwargs):
        if path.name == "crosscheck_checksums.json":
            attempts.append(path)
            if len(attempts) == 1:
                os.kill(os.getpid(), signal.SIGTERM)
                raise OSError("injected unlink failure")
        return unlink(path, *args, **kwargs)

    def fail_summary(*args):
        raise OSError("injected summary failure")

    monkeypatch.setattr(Path, "unlink", fail_once)
    monkeypatch.setattr(cross, "save_report", fail_summary)
    cross.retain_failure(
        tmp_path, report, TimeoutError("expired"), CLOCK.WallTimeLimit(10)
    )
    saved = cross.read_json((tmp_path / "crosscheck_report.json").read_bytes())
    assert saved["status"] == "failed" and saved["outcome"] == "not_assessed"
    assert saved["abort_signals"] == [signal.SIGTERM]
    assert len(saved["abort_cleanup_errors"]) == 2 and len(attempts) == 2
    assert not (tmp_path / "crosscheck_checksums.json").exists()
    assert not (tmp_path / "crosscheck_summary.md").exists()


def test_bridge_cancellation_stops_its_separate_worker_session(tmp_path, monkeypatch):
    checkout = tmp_path / "checkout"
    (checkout / "scripts").mkdir(parents=True)
    (checkout / "scripts/run_python.py").write_text(
        "import os\nfrom pathlib import Path\nROOT=Path(__file__).parent.parent\n"
        "def prepare_runtime(root): return os.environ.copy()\n"
    )
    marker = tmp_path / "worker.pid"
    bridge = tmp_path / "bridge.py"
    bridge.write_text(
        "import os, signal, subprocess, sys, time\n"
        "from pathlib import Path\n"
        "child=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)\n"
        "def stop(signum, frame):\n"
        "    os.killpg(child.pid, signal.SIGTERM)\n"
        "    child.wait()\n"
        "    raise SystemExit(143)\n"
        "signal.signal(signal.SIGTERM, stop)\n"
        f"Path({str(marker)!r}).write_text(str(child.pid))\n"
        "time.sleep(60)\n"
    )
    monkeypatch.setattr(cross, "ROOT", tmp_path)
    monkeypatch.setattr(cross, "BRIDGE", "bridge.py")
    clock = CLOCK.WallTimeLimit(1)
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            cross.call_bridge(
                checkout, "run", "outer", tmp_path / "out", tmp_path / "request", clock
            )
        assert marker.exists(), "The test must reach the separate worker session."
        pid = int(marker.read_text())
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)
    finally:
        if marker.exists():
            try:
                os.killpg(int(marker.read_text()), signal.SIGKILL)
            except ProcessLookupError:
                pass


@pytest.mark.parametrize(
    "mutation",
    [
        "commit",
        "dirty",
        "completion",
        "seed",
        "iterations",
        "profile",
        "curve",
        "source",
        "frozen",
    ],
)
def test_reference_requires_original_provenance_and_consumption_anchors(
    tmp_path, monkeypatch, mutation
):
    spec = copy.deepcopy(cross.HISTORIES["outer"])
    provenance = {
        "git": {
            "available": True,
            "changes": [],
            "commit": spec["commit"],
            "dirty": False,
        }
    }
    cell = {
        "number": 2,
        "directory": "cell-02",
        "budget": {"seed": 20261201, "niterations": 500},
        "condition": "local_300_5",
        "grammar": "unrestricted",
        "status": "completed",
        "diagnostics": {
            "selected_index": 0,
            "candidates": [{"curve_marker": "within_tolerance"}],
        },
    }
    report = {
        "format": spec["format"],
        "status": "completed",
        "final_verification": "passed",
        "control_initial": {"provenance": provenance},
        "control_final": {"provenance": copy.deepcopy(provenance)},
        "cells": [{}, cell, *[{} for _ in range(18)]],
        "source_sha256": {"code.py": _sha256(b"code")},
        "frozen_file_sha256": {"proof": _sha256(b"original")},
    }
    if mutation in ("commit", "dirty"):
        provenance["git"][mutation] = "wrong" if mutation == "commit" else True
    elif mutation == "completion":
        report["final_verification"] = "failed"
    elif mutation in ("seed", "iterations"):
        cell["budget"]["seed" if mutation == "seed" else "niterations"] += 1
    elif mutation == "profile":
        cell["condition"] = "local_100_2"
    elif mutation == "curve":
        cell["diagnostics"]["candidates"][0]["curve_marker"] = "outside_tolerance"
    elif mutation == "source":
        report["source_sha256"]["code.py"] = "wrong"
    elif mutation == "frozen":
        report["frozen_file_sha256"]["proof"] = "wrong"
    contents = tar_bytes({"report.json": _json_bytes(report), "proof": b"original"})
    spec.update(prefix="reference", archive_sha256=_sha256(contents))
    monkeypatch.setitem(cross.HISTORIES, "outer", spec)
    monkeypatch.setattr(cross, "git", lambda *a: b"code")
    monkeypatch.setattr(
        cross,
        "reference_arrays",
        lambda *a: pytest.fail("Invalid provenance must stop before data consumption."),
    )
    path = tmp_path / "original.tar.gz"
    path.write_bytes(contents)
    with pytest.raises(ValueError):
        cross.read_reference(path, "outer")
