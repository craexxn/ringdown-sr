"""Exercise coordinate boundaries and the inherited native failure verifier."""

import copy
import math
from types import SimpleNamespace

import numpy as np
import pytest
import test_global_restarts
from test_structure import constant, operator, time_node

from ringdown_sr import assessment_sources as sources
from ringdown_sr import time_coordinate_profile as profile
from ringdown_sr.pilot import _write_json
from ringdown_sr.search_duration import SearchInvocationGuard

historical_failed_worker = test_global_restarts.failed_worker


@pytest.fixture
def bridge():
    return profile.native.load_module(
        profile.ROOT / profile.BRIDGE, "coordinate_test_bridge"
    )


@pytest.fixture
def bound_request(bridge, monkeypatch, tmp_path):
    commit = "a" * 40
    provenance = {
        "git": {"available": True, "changes": [], "commit": commit, "dirty": False}
    }
    monkeypatch.setattr(bridge, "_provenance", lambda: provenance)
    monkeypatch.setattr(bridge.os, "sched_getaffinity", lambda _: {3})
    inputs = tmp_path / "search-U.npz"
    arrays = profile.search_inputs("fixture_a", "U", True)
    np.savez(inputs, **arrays)
    plan = profile.plans("fixture_a", True)[1]
    request = profile.request_for(plan, inputs, commit, True)
    path = tmp_path / "request.json"
    _write_json(path, request)
    reader = SimpleNamespace(read_json=sources.read_json)
    return path, inputs, request, arrays, reader, provenance


@pytest.mark.parametrize("action", ["prepare", "run", "verify"])
def test_all_worker_phases_require_the_same_bound_readonly_inputs(
    bridge, bound_request, action
):
    path, inputs, expected, arrays, reader, _ = bound_request
    actual, saved = bridge.checked_request(path, inputs, action, None, reader)
    assert actual == expected
    assert all(saved[k].tobytes() == arrays[k].tobytes() for k in arrays)
    assert all(not a.flags.writeable for a in saved.values())


@pytest.mark.parametrize(
    "fault", ["missing", "extra", "physical", "double_scale", "one_bit", "signal"]
)
def test_reader_rejects_changed_coordinates_roles_truth_or_signal(
    bridge, bound_request, fault
):
    path, inputs, _, arrays, reader, _ = bound_request
    changed = {k: v.copy() for k, v in arrays.items()}
    if fault == "missing":
        changed.pop("diagnostic_time_s")
    elif fault == "extra":
        changed["irregular_time_s"] = changed["time_s"]
    elif fault == "physical":
        changed, _ = profile.inputs("fixture_a", True)
    elif fault == "double_scale":
        changed["time_s"] *= 32
    elif fault == "one_bit":
        changed["observed"][0] = np.nextafter(changed["observed"][0], np.inf)
    else:
        changed = profile.search_inputs("fixture_b", "U", True)
    np.savez(inputs, **changed)
    with pytest.raises(ValueError, match="signal, scale, input roles or Float64"):
        bridge.checked_request(path, inputs, "verify", None, reader)


@pytest.mark.parametrize(
    "field,value",
    [
        ("seed", 74),
        ("scope", "scientific"),
        ("scope", "unknown"),
        ("adapter_sha256", "0" * 64),
        ("protocol_commit", "f" * 40),
        ("coordinate", {"arm": "U", "scale_hex": (1024.0).hex(), "unit": "s"}),
        ("coordinate", {"arm": "U", "scale_hex": (32.0).hex(), "unit": "1"}),
    ],
)
def test_request_cannot_change_scope_seed_adapter_or_scale(
    bridge, bound_request, field, value
):
    path, inputs, request, _, reader, _ = bound_request
    _write_json(path, {**request, field: value})
    with pytest.raises(ValueError):
        bridge.checked_request(path, inputs, "verify", None, reader)


@pytest.mark.parametrize("action", ["prepare", "run", "verify"])
@pytest.mark.parametrize("fault", ["dirty", "changes", "commit", "unavailable"])
def test_every_phase_requires_exact_clean_execution_sources(
    bridge, bound_request, action, fault
):
    path, inputs, _, _, reader, provenance = bound_request
    field, value = {
        "dirty": ("dirty", True),
        "changes": ("changes", ["scripts/time_coordinate_bridge.py"]),
        "commit": ("commit", "b" * 40),
        "unavailable": ("available", False),
    }[fault]
    provenance["git"][field] = value
    with pytest.raises(ValueError, match="exact clean"):
        bridge.checked_request(path, inputs, action, None, reader)


def test_verification_allows_relocation_but_execution_keeps_path_and_affinity(
    bridge, bound_request, monkeypatch, tmp_path
):
    path, inputs, _, _, reader, _ = bound_request
    relocated = tmp_path / "relocated.npz"
    relocated.write_bytes(inputs.read_bytes())
    bridge.checked_request(path, relocated, "verify", None, reader)
    with pytest.raises(ValueError, match="input path"):
        bridge.checked_request(path, relocated, "run", None, reader)
    monkeypatch.setattr(bridge.os, "sched_getaffinity", lambda _: {2, 3})
    with pytest.raises(ValueError, match="single-CPU"):
        bridge.checked_request(path, inputs, "prepare", None, reader)
    bridge.checked_request(path, inputs, "verify", None, reader)


@pytest.mark.parametrize("arm,scale", [("T", 1), ("U", 32)])
@pytest.mark.parametrize("technical", [False, True])
def test_coordinate_context_preserves_native_cell_and_uses_actual_spacing(
    bridge, monkeypatch, tmp_path, arm, scale, technical
):
    name = "fixture_b" if technical else "anchor"
    plan = next(p for p in profile.plans(name, technical) if p["arm"] == arm)
    request = profile.request_for(plan, tmp_path / "inputs.npz", "a" * 40, technical)
    driver = SimpleNamespace()
    legacy = SimpleNamespace(
        cell_for=lambda r: {"budget": r["cell"], "signal": "anchor"}
    )
    ctx = (None, driver, None, None)
    monkeypatch.setattr(bridge, "base_context", lambda *args: ctx)
    assert bridge.context(request, legacy) is ctx
    assert driver.FS == (8 if technical else 4096) / scale
    assert legacy.cell_for(request) == {"budget": plan, "signal": name}
    arrays = profile.search_inputs(name, arm, technical)
    changed = {key: value.copy() for key, value in arrays.items()}
    changed["time_s"][1] = np.nextafter(changed["time_s"][1], np.inf)
    with pytest.raises(ValueError, match="different search coordinates"):
        driver.diagnose_cell_candidate({}, 0, 0, changed, {})


@pytest.mark.parametrize("arm,scale", [("T", 1), ("U", 32)])
def test_native_diagnosis_replays_in_physical_seconds_without_parameter_decision(
    bridge, monkeypatch, tmp_path, arm, scale
):
    plan = next(p for p in profile.plans("anchor") if p["arm"] == arm)
    request = profile.request_for(plan, tmp_path / "inputs.npz", "a" * 40)
    driver = SimpleNamespace()
    legacy = SimpleNamespace(cell_for=lambda r: {})
    monkeypatch.setattr(
        bridge, "base_context", lambda *args: (None, driver, None, None)
    )
    bridge.context(request, legacy)
    tree = operator(
        "*",
        operator("exp", operator("*", constant(-125 / scale), time_node())),
        operator("cos", operator("*", constant(500 * math.pi / scale), time_node())),
    )
    candidate = {
        "tree": tree,
        "complexity": 9,
        "loss": 1e-30,
        "display_equation": "q(t)",
    }
    original = copy.deepcopy(candidate)
    arrays = profile.search_inputs("anchor", arm)
    actual = driver.diagnose_cell_candidate(candidate, 2, 2, arrays, {})
    assert candidate == original
    assert actual["source_candidate_sha256"] == sources.sha256(
        sources.json_bytes(candidate)
    )
    assert actual["curve_marker"] == "within_tolerance" and actual["is_selected"]
    assert actual["physical_analysis"]["raw_parameters"]["decay_time_s"][
        "value"
    ] == pytest.approx(0.008)
    assert actual["parameter_match"] == {
        "status": "not_assessed",
        "reason": "no_coordinate_development_parameter_rule",
    }
    assert actual["coordinate"] == request["coordinate"]


@pytest.mark.parametrize("arm", ["T", "U"])
@pytest.mark.parametrize("finished", [True, False])
def test_coordinate_arms_require_regular_iteration_completion(
    bridge, tmp_path, arm, finished
):
    count = 4000 if finished else 7
    record = {
        "format": profile.native.FORMAT,
        "populations": 2,
        "processed_population_cycles": count,
        "checks": count,
        "requested_iterations": 2000,
        "completed_outer_rounds": count // 2,
        "residual_population_cycles": count % 2,
        "iteration_limit_reached": finished,
        "technical_counter_stop": False,
        "affinity": [3],
        "native_start_unix_seconds": 1000.0,
        "loop_entry_unix_seconds": 1000.0,
        "monotonic_to_last_check_seconds": 20.0,
        "elapsed_at_last_check_seconds": 20.0,
        "main_loop_call_wall_seconds": 21.0,
        "clock_difference_seconds": 0.0,
        "timeout_reached": False,
    }
    (tmp_path / "worker").mkdir()
    _write_json(tmp_path / "worker/time_budget_clock.json", record)
    request = {"cell": {"condition": "iterations", "arm": arm, "niterations": 2000}}
    reader = SimpleNamespace(read_json=sources.read_json)
    if finished:
        assert (
            bridge.clock_evidence(tmp_path, request, reader)["reason"]
            == "iteration_limit"
        )
    else:
        with pytest.raises(ValueError, match="without its allowed stopping rule"):
            bridge.clock_evidence(tmp_path, request, reader)


@pytest.fixture
def failed_worker(historical_failed_worker):
    root, arrays, prepared, ctx, documents = historical_failed_worker
    documents["profile.json"]["condition"] = "iterations"
    _write_json(root / "worker/profile.json", documents["profile.json"])
    return root, arrays, prepared, ctx, documents


@pytest.mark.parametrize(
    "failure", ["guard", "interrupt", "unknown", "timeout_masks_interrupt"]
)
def test_coordinate_read_verification_cannot_accept_integrity_or_interrupt_failures(
    bridge, failed_worker, failure
):
    root, arrays, prepared, ctx, documents = failed_worker
    if failure == "guard":
        with pytest.raises(ValueError) as caught:
            SearchInvocationGuard(None, 2)._jl_call_nogil(niterations=3)
        error = "ValueError: " + str(caught.value)
    else:
        error = (
            "RuntimeError: unexplained"
            if failure == "unknown"
            else "KeyboardInterrupt: "
        )
    documents["metadata.json"]["error"] = error
    _write_json(root / "worker/metadata.json", documents["metadata.json"])
    kind = "fit_error"
    if failure == "timeout_masks_interrupt":
        kind = "worker_timeout"
        _write_json(
            root / "worker/status.json",
            {"status": "failed", "error": "TimeoutExpired: budget"},
        )
    _write_json(
        root / "outcome.json", {"status": "worker_failed", "failure_kind": kind}
    )
    with pytest.raises(ValueError, match="failure"):
        bridge.bridge.verify_result(
            root, {"cell": {"condition": "iterations"}}, arrays, prepared, None, ctx
        )


@pytest.mark.parametrize("field", ["worker_provenance", "worker_adapter_source_sha256"])
@pytest.mark.parametrize("phase", ["before_worker_start", "fit", "replay"])
@pytest.mark.parametrize("mutation", ["missing", "changed"])
def test_coordinate_read_verification_keeps_phase_specific_worker_origin(
    bridge, failed_worker, field, phase, mutation
):
    root, arrays, prepared, ctx, documents = failed_worker
    metadata = documents["metadata.json"]
    metadata.update(phase=phase)
    metadata.pop("error")
    metadata.pop("failed_during")
    if mutation == "missing":
        metadata.pop(field)
    else:
        metadata[field] = {"wrong": "source"}
    _write_json(root / "worker/metadata.json", metadata)
    _write_json(
        root / "worker/status.json",
        {"status": "failed", "error": "TimeoutExpired: budget"},
    )
    resources = {
        "scope": "worker_launcher_and_waited_descendants",
        "process_wall_seconds": 1.0,
        "cpu_user_seconds": 0.2,
        "cpu_system_seconds": 0.1,
    }
    _write_json(root / "worker_resources.json", resources)
    outcome = {
        "status": "worker_failed",
        "failure_kind": "worker_timeout",
        "resources": resources,
    }
    _write_json(root / "outcome.json", outcome)
    request = {"cell": {"condition": "iterations"}}
    if phase == "before_worker_start" and mutation == "missing":
        assert (
            bridge.bridge.verify_result(root, request, arrays, prepared, None, ctx)
            == outcome
        )
    else:
        with pytest.raises(ValueError, match="provenance"):
            bridge.bridge.verify_result(root, request, arrays, prepared, None, ctx)


def test_ordinary_numerical_failure_remains_an_allowed_recorded_failure(
    bridge, failed_worker
):
    root, arrays, prepared, ctx, documents = failed_worker
    error = RuntimeError("Historical worker failed; inspect worker/worker.log.")
    assert (
        bridge.bridge.FAILURES.failure_kind(error, documents["metadata.json"])
        == "fit_error"
    )
    bridge.bridge.FAILURES.verify_failed_worker(
        root, arrays, prepared, ctx, "fit_error", condition="iterations"
    )
