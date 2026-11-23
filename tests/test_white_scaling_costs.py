"""Reject fabricated completion or incomplete measurements before publication."""

import json
import math
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

from ringdown_sr import white_scaling as pilot


def _completed_record(kind):
    record = {
        "status": "completed",
        "started_at": "2026-11-23T10:00:00+00:00",
        "finished_at": "2026-11-23T10:00:02+00:00",
        "wall_seconds": 2.0,
        "cpu_user_seconds": 1.25,
        "cpu_system_seconds": 0.125,
        "cpu_measurement_complete": True,
    }
    if kind == "series":
        record.update(
            format=pilot.FORMAT,
            completed_fixed=18,
            completed_search=21,
            stage="search",
            current_cell=pilot.cells()[-1]["id"],
            wall_scope=pilot.SERIES_WALL_SCOPE,
            cpu_scope=pilot.SERIES_CPU_SCOPE,
        )
    else:
        record.update(
            format=pilot.FORMAT + "-fixed-call-1",
            returncode=0,
            wall_scope=pilot.FIXED_WALL_SCOPE,
            cpu_scope=pilot.FIXED_CPU_SCOPE,
        )
    return record


def _validate(kind, record):
    return (pilot._series_costs if kind == "series" else pilot._fixed_costs)(record)


@pytest.mark.parametrize("kind", ["series", "fixed"])
def test_completed_measured_costs_preserve_values_and_declared_scope(kind):
    record = _completed_record(kind)
    checked = _validate(kind, record)
    assert checked == {
        key: record[key]
        for key in (
            "wall_seconds",
            "cpu_user_seconds",
            "cpu_system_seconds",
            "wall_scope",
            "cpu_scope",
            "cpu_measurement_complete",
        )
    }
    # A measured zero is valid; CPU completeness is checked independently.
    for key in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        record[key] = 0
    _validate(kind, record)


@pytest.mark.parametrize("kind", ["series", "fixed"])
@pytest.mark.parametrize(
    "field", ["wall_seconds", "cpu_user_seconds", "cpu_system_seconds"]
)
@pytest.mark.parametrize("invalid", [-0.001, math.nan, math.inf, -math.inf, True, None])
def test_invalid_measured_cost_cannot_release_completed_record(kind, field, invalid):
    record = _completed_record(kind)
    record[field] = invalid
    with pytest.raises(ValueError, match="finite nonnegative"):
        _validate(kind, record)


@pytest.mark.parametrize("kind", ["series", "fixed"])
@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("status", "aborted"),
        ("cpu_measurement_complete", False),
        ("cpu_measurement_complete", 1),
        ("wall_scope", "fit_only"),
        ("cpu_scope", "self_only"),
        ("finished_at", "2026-11-23T10:00:02"),
        ("started_at", "2026-11-23T10:00:00"),
        ("finished_at", "2026-11-23T09:59:59+00:00"),
        ("finished_at", "not-a-timestamp"),
        ("finished_at", None),
    ],
)
def test_incomplete_or_contradictory_completion_is_rejected(kind, field, invalid):
    record = _completed_record(kind)
    record[field] = invalid
    with pytest.raises(ValueError):
        _validate(kind, record)


@pytest.mark.parametrize("kind", ["series", "fixed"])
@pytest.mark.parametrize("missing", ["wall_scope", "cpu_scope", "finished_at"])
def test_missing_completion_evidence_is_rejected(kind, missing):
    record = _completed_record(kind)
    del record[missing]
    with pytest.raises(ValueError, match="terminal record"):
        _validate(kind, record)


@pytest.mark.parametrize("kind", ["series", "fixed"])
def test_error_field_cannot_coexist_with_positive_completion(kind):
    record = _completed_record(kind)
    record["error"] = "InterruptedError: interrupted after worker completion"
    with pytest.raises(ValueError):
        _validate(kind, record)


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("completed_fixed", 17),
        ("completed_search", 20),
        ("completed_fixed", 18.0),
        ("completed_search", 21.0),
        ("stage", "fixed"),
        ("current_cell", "not-the-final-cell"),
    ],
)
def test_series_requires_exact_terminal_cell_and_worker_counts(field, invalid):
    record = _completed_record("series")
    record[field] = invalid
    with pytest.raises(ValueError, match="terminal record"):
        pilot._series_costs(record)


@pytest.mark.parametrize("returncode", [1, -15, None, False, 0.0])
def test_fixed_completion_requires_successful_integer_exit_code(returncode):
    record = _completed_record("fixed")
    record["returncode"] = returncode
    with pytest.raises(ValueError, match="terminal record"):
        pilot._fixed_costs(record)


@pytest.mark.parametrize("failure", [KeyboardInterrupt, TimeoutError])
def test_interrupted_fixed_worker_is_stopped_and_keeps_partial_cpu_costs(
    tmp_path, monkeypatch, failure
):
    stopped = []

    class InterruptedProcess:
        returncode = None

        def wait(self, *, timeout):
            assert timeout > 0
            raise failure("test interruption")

    process = InterruptedProcess()
    monkeypatch.setattr(pilot.subprocess, "Popen", lambda *a, **k: process)
    monkeypatch.setattr(pilot.symbolic, "_stop_worker", stopped.append)
    usage = iter(
        [
            SimpleNamespace(ru_utime=3.0, ru_stime=0.25),
            SimpleNamespace(ru_utime=4.5, ru_stime=0.375),
        ]
    )
    monkeypatch.setattr(pilot.resource, "getrusage", lambda *a: next(usage))
    with pytest.raises(failure, match="test interruption"):
        pilot._fixed(tmp_path, deadline=pilot.time.monotonic() + 10)
    assert stopped == [process]
    outcome = json.loads((tmp_path / "call.json").read_text())
    assert outcome["status"] == "aborted"
    assert outcome["cpu_measurement_complete"] is False
    assert outcome["cpu_user_seconds"] == 1.5
    assert outcome["cpu_system_seconds"] == 0.125
    assert outcome["error"].startswith(failure.__name__ + ":")
    assert math.isfinite(outcome["wall_seconds"]) and outcome["wall_seconds"] >= 0
    assert outcome["started_at"] and outcome["finished_at"]
    with pytest.raises(ValueError):
        pilot._fixed_costs(outcome)


@pytest.mark.parametrize("returncode", [0, 3])
def test_fixed_worker_records_real_exit_and_measured_child_costs(
    tmp_path, monkeypatch, returncode
):
    process = SimpleNamespace(wait=lambda **kwargs: returncode)
    monkeypatch.setattr(pilot.subprocess, "Popen", lambda *a, **k: process)
    usage = iter(
        [
            SimpleNamespace(ru_utime=3.0, ru_stime=0.25),
            SimpleNamespace(ru_utime=4.5, ru_stime=0.375),
        ]
    )
    monkeypatch.setattr(pilot.resource, "getrusage", lambda *a: next(usage))
    if returncode:
        with pytest.raises(RuntimeError, match="worker failed"):
            pilot._fixed(tmp_path, deadline=pilot.time.monotonic() + 10)
    else:
        pilot._fixed(tmp_path, deadline=pilot.time.monotonic() + 10)
    outcome = json.loads((tmp_path / "call.json").read_text())
    assert outcome["returncode"] == returncode
    if returncode:
        assert outcome["status"] == "aborted"
        assert outcome["cpu_measurement_complete"] is False
        assert outcome["cpu_user_seconds"] == 1.5
        assert outcome["cpu_system_seconds"] == 0.125
        with pytest.raises(ValueError):
            pilot._fixed_costs(outcome)
    else:
        checked = pilot._fixed_costs(outcome)
        assert checked["cpu_user_seconds"] == 1.5
        assert checked["cpu_system_seconds"] == 0.125


def test_aborted_series_preserves_known_cpu_partial_counts(tmp_path, monkeypatch):
    root = tmp_path / "series"

    def prepare(path):
        path.mkdir()
        return {"sources": {}, "provenance": {}}

    def fail(*args):
        raise KeyboardInterrupt("injected series interrupt")

    measurements = iter([(3.0, 0.25), (4.5, 0.375)])
    monkeypatch.setattr(pilot, "prepare", prepare)
    monkeypatch.setattr(pilot, "_sources", dict)
    monkeypatch.setattr(pilot, "_provenance", dict)
    monkeypatch.setattr(pilot, "_cpu_snapshot", lambda: next(measurements))
    monkeypatch.setattr(pilot, "_fixed", fail)
    with pytest.raises(KeyboardInterrupt, match="series interrupt"):
        pilot.run(root)
    outcome = pilot._read(root / "status.json")
    assert outcome["status"] == "aborted"
    assert outcome["cpu_measurement_complete"] is False
    assert outcome["cpu_user_seconds"] == 1.5
    assert outcome["cpu_system_seconds"] == 0.125


@pytest.mark.parametrize("kind", ["fixed", "series"])
def test_terminal_cost_write_failure_preserves_worker_exception_and_known_costs(
    tmp_path, monkeypatch, kind
):
    root = tmp_path / kind
    original = RuntimeError("original worker failure")

    def fail(*args, **kwargs):
        raise original

    original_writer = pilot._write_json

    def write(path, value):
        if value.get("status") == "aborted":
            raise OSError("injected terminal write failure")
        original_writer(path, value)

    monkeypatch.setattr(pilot, "_write_json", write)
    if kind == "fixed":
        root.mkdir()
        process = SimpleNamespace(wait=fail, returncode=-15)
        monkeypatch.setattr(pilot.subprocess, "Popen", lambda *args, **kwargs: process)
        monkeypatch.setattr(pilot.symbolic, "_stop_worker", lambda process: None)
        usage = iter(
            [
                SimpleNamespace(ru_utime=3.0, ru_stime=0.25),
                SimpleNamespace(ru_utime=4.5, ru_stime=0.375),
            ]
        )
        monkeypatch.setattr(pilot.resource, "getrusage", lambda *args: next(usage))
        operation = lambda: pilot._fixed(root, pilot.time.monotonic() + 10)
        evidence = root / "call-write-failure.json"
    else:

        def prepare(path):
            path.mkdir()
            return {"sources": {}, "provenance": {}}

        usage = iter([(3.0, 0.25), (4.5, 0.375)])
        monkeypatch.setattr(pilot, "prepare", prepare)
        monkeypatch.setattr(pilot, "_sources", dict)
        monkeypatch.setattr(pilot, "_provenance", dict)
        monkeypatch.setattr(pilot, "_cpu_snapshot", lambda: next(usage))
        monkeypatch.setattr(pilot, "_fixed", fail)
        operation = lambda: pilot.run(root)
        evidence = root / "status-write-failure.json"
    with pytest.raises(RuntimeError, match="original worker failure") as raised:
        operation()
    assert raised.value is original
    assert original.__notes__ == [
        "Secondary cost-record write failure: OSError: injected terminal write failure"
    ]
    record = pilot._read(evidence)
    assert record["error"] == "RuntimeError: original worker failure"
    assert record["secondary_error"] == "OSError: injected terminal write failure"
    assert record["cost_record"]["cpu_measurement_complete"] is False
    assert record["cost_record"]["cpu_user_seconds"] == 1.5
    assert record["cost_record"]["cpu_system_seconds"] == 0.125


def _nested_cost_fixture(
    root,
    monkeypatch,
    *,
    series_wall=100.0,
    fixed_wall=2.0,
    optimization=0.01,
    search_wall=1.0,
    fit_wall=0.5,
):
    """Write a complete series envelope, stubbing native proofs rather than verify."""
    root.mkdir()
    arrays = pilot.data()
    np.savez(root / "inputs.npz", **arrays)
    cells = pilot.cells()
    by_id = {cell["id"]: cell for cell in cells}

    def completed(wall):
        start = datetime(2026, 11, 23, 10, tzinfo=UTC)
        return {
            "status": "completed",
            "started_at": start.isoformat(),
            "finished_at": (start + timedelta(seconds=wall)).isoformat(),
            "cpu_measurement_complete": True,
            "cpu_user_seconds": 12.0,
            "cpu_system_seconds": 0.25,
            "wall_seconds": wall,
        }

    pilot._write_json(
        root / "manifest.json",
        {
            "format": pilot.FORMAT,
            "sources": {},
            "cells": cells,
            "input_sha256": pilot._sha256((root / "inputs.npz").read_bytes()),
        },
    )
    pilot._write_json(
        root / "status.json",
        {
            **completed(series_wall),
            "format": pilot.FORMAT,
            "completed_fixed": 18,
            "completed_search": 21,
            "stage": "search",
            "current_cell": cells[-1]["id"],
            "wall_scope": pilot.SERIES_WALL_SCOPE,
            "cpu_scope": pilot.SERIES_CPU_SCOPE,
            # Parallel CPU counters can legitimately exceed elapsed wall time.
            "cpu_user_seconds": 500.0,
            "cpu_system_seconds": 10.0,
        },
    )
    for cell in cells:
        if not cell["repeat"]:
            directory = root / "fixed" / cell["id"]
            directory.mkdir(parents=True)
            pilot._write_json(
                directory / "call.json",
                {
                    **completed(fixed_wall),
                    "format": pilot.FORMAT + "-fixed-call-1",
                    "returncode": 0,
                    "wall_scope": pilot.FIXED_WALL_SCOPE,
                    "cpu_scope": pilot.FIXED_CPU_SCOPE,
                },
            )
        directory = root / "search" / cell["id"]
        directory.mkdir(parents=True)
        pilot._write_json(
            directory / "result.json",
            {
                "candidates": [
                    {
                        "tree": {"kind": "constant", "value_hex": (0.0).hex()},
                        "complexity": 1,
                        "loss": 0.0,
                        "display_equation": "0.0",
                    }
                ],
                "selected_index": 0,
                "baseline_loss": 1.0,
                "cost_normalization": 1.0,
                "callback_calls_during_fit": 1,
            },
        )

    def prepared(directory):
        cell = by_id[directory.name]
        return (
            {
                "arm": cell["arm"],
                "budget": {"seed": cell["seed"]},
                "sigma_hex": pilot.SIGMA.hex(),
                "technical": False,
            },
            {
                "time_s": arrays["time_s"],
                "observed": arrays[f"observed_{cell['case']}"],
            },
            {},
        )

    def fixed_result(directory):
        records = [
            {
                "start": {"name": f"start-{i + 1}"},
                "initial_parameters": [],
                "parameters": [],
                "loss": 0.0,
                "residual": [(0.0).hex()] * 128,
                "fit_callback_count": 1,
                "local_steps": [],
                "optimization_seconds": optimization,
                "display_equation": "0.0",
                "rng_before": [],
                "rng_after": [],
                "restart_draws": [],
                "restart_parameters": [],
                "states": [],
            }
            for i in range(4)
        ]
        return {"request": prepared(directory)[0], "records": records}

    def search_result(directory):
        return {
            "costs": {
                "status": "completed",
                "returncode": 0,
                "cpu_measurement_complete": True,
                "worker_wall_seconds": search_wall,
                "fit_wall_seconds": fit_wall,
                "cpu_user_seconds": 6.0,
                "cpu_system_seconds": 0.25,
            }
        }

    monkeypatch.setattr(pilot, "_sources", dict)
    monkeypatch.setattr(pilot.fixed, "verify_fixed", fixed_result)
    monkeypatch.setattr(pilot.worker, "verify_prepared", prepared)
    monkeypatch.setattr(pilot.worker, "verify_member", search_result)


@pytest.mark.parametrize(
    ("overrides", "error"),
    [
        pytest.param({}, None, id="coherent-wall-scopes-with-cpu-above-wall"),
        pytest.param(
            {"optimization": 0.75},
            "Local optimization sum exceeds",
            id="local-sum-exceeds-fixed-worker",
        ),
        pytest.param(
            {"series_wall": 30.0},
            "Sequential worker time sum exceeds",
            id="fixed-worker-sum-exceeds-series",
        ),
        pytest.param(
            {"fixed_wall": 0.1, "search_wall": 10.0},
            "Sequential worker time sum exceeds",
            id="search-worker-sum-exceeds-series",
        ),
        pytest.param(
            {"fit_wall": 2.0},
            "Search fit exceeds",
            id="fit-exceeds-search-worker",
        ),
    ],
)
def test_full_series_verifier_checks_nested_wall_scopes(
    tmp_path, monkeypatch, overrides, error
):
    root = tmp_path / "source"
    _nested_cost_fixture(root, monkeypatch, **overrides)
    before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    if error:
        with pytest.raises(ValueError, match=error):
            pilot.verify(root)
    else:
        report = pilot.verify(root)
        assert report["status"] == "verified"
        assert len(report["fixed_worker_costs"]) == 18
        assert len(report["search_worker_costs"]) == 21
        assert report["sequential_worker_wall_sum_seconds"] == 57.0
        assert report["series_costs"]["cpu_user_seconds"] > report["wall_seconds"]
        assert all(
            costs["cpu_user_seconds"] > costs["wall_seconds"]
            for costs in report["fixed_worker_costs"].values()
        )
        assert all(
            costs["cpu_user_seconds"] > costs["worker_wall_seconds"]
            for costs in report["search_worker_costs"].values()
        )
    assert {
        path: path.read_bytes() for path in root.rglob("*") if path.is_file()
    } == before
