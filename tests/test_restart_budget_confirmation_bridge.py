"""Bind new signals to unchanged native search and failure contracts."""

import copy
from types import SimpleNamespace

import numpy as np
import pytest
import test_global_restarts
import test_restart_budget_bridge

from ringdown_sr import assessment_sources as sources
from ringdown_sr import restart_budget_confirmation_profile as profile
from ringdown_sr.pilot import _write_json
from ringdown_sr.search_duration import SearchInvocationGuard
from ringdown_sr.symbolic import SearchBudget

historical_failed_worker = test_global_restarts.failed_worker
failed_worker = test_restart_budget_bridge.failed_worker


@pytest.fixture
def bridge():
    return profile.native.load_module(
        profile.ROOT / profile.BRIDGE, "budget_confirmation_test_bridge"
    )


@pytest.fixture
def request_fixture(bridge, monkeypatch, tmp_path):
    commit = "a" * 40
    provenance = {
        "git": {"available": True, "changes": [], "commit": commit, "dirty": False}
    }
    monkeypatch.setattr(bridge, "_provenance", lambda: provenance)
    monkeypatch.setattr(bridge.os, "sched_getaffinity", lambda _: {3})
    inputs = tmp_path / "anchor.npz"
    arrays, _ = profile.inputs("fixture_a", True)
    np.savez(inputs, **arrays)
    plan = next(p for p in profile.plans("fixture_a", True) if p["arm"] == "L")
    request = profile.request_for(plan, inputs, commit, True)
    path = tmp_path / "request.json"
    _write_json(path, request)
    return path, inputs, request, arrays, provenance


def read_request(bridge, fixture, action="verify"):
    path, inputs, *_ = fixture
    return bridge.checked_request(
        path, inputs, action, None, SimpleNamespace(read_json=sources.read_json)
    )


@pytest.mark.parametrize("action", ["prepare", "run", "verify"])
def test_all_worker_phases_bind_exact_readonly_physical_inputs(
    bridge, request_fixture, action
):
    _, _, expected, arrays, _ = request_fixture
    actual, loaded = read_request(bridge, request_fixture, action)
    assert actual == expected
    assert actual["coordinate"] == {"name": "t", "scale_hex": (1.0).hex(), "unit": "s"}
    assert all(loaded[key].tobytes() == arrays[key].tobytes() for key in arrays)
    assert all(not value.flags.writeable for value in loaded.values())


@pytest.mark.parametrize(
    "fault",
    ["seed", "scope", "iterations", "member", "coordinate", "adapter", "protocol"],
)
def test_request_changes_cannot_reassign_a_frozen_search(
    bridge, request_fixture, fault
):
    path, _, request, _, _ = request_fixture
    if fault == "seed":
        request["seed"] += 1
    elif fault == "scope":
        request["scope"] = "scientific"
    elif fault == "iterations":
        request["niterations"] = request["cell"]["niterations"] = 1
    elif fault == "member":
        request["cell"]["member"] = 2
    elif fault == "coordinate":
        request["coordinate"]["scale_hex"] = (32.0).hex()
    elif fault == "adapter":
        request["adapter_sha256"] = "0" * 64
    else:
        request["protocol_commit"] = "f" * 40
    _write_json(path, request)
    with pytest.raises(ValueError):
        read_request(bridge, request_fixture)


@pytest.mark.parametrize(
    "fault", ["missing", "extra", "scaled", "truth_bit", "other_signal"]
)
def test_physical_input_roles_bits_and_signal_are_fixed(bridge, request_fixture, fault):
    _, path, _, arrays, _ = request_fixture
    changed = {key: value.copy() for key, value in arrays.items()}
    if fault == "missing":
        changed.pop("diagnostic_truth")
    elif fault == "extra":
        changed["irregular_truth"] = changed["observed"]
    elif fault == "scaled":
        changed["time_s"] *= 32
    elif fault == "truth_bit":
        changed["observed"][0] = np.nextafter(changed["observed"][0], np.inf)
    else:
        changed, _ = profile.inputs("fixture_b", True)
    np.savez(path, **changed)
    with pytest.raises(ValueError, match="input roles or Float64"):
        read_request(bridge, request_fixture)


@pytest.mark.parametrize("fault", ["dirty", "changes", "commit", "available"])
def test_read_verification_requires_original_clean_sources(
    bridge, request_fixture, fault
):
    provenance = request_fixture[-1]
    provenance["git"][fault] = {
        "dirty": True,
        "changes": [profile.BRIDGE],
        "commit": "b" * 40,
        "available": False,
    }[fault]
    with pytest.raises(ValueError, match="exact clean"):
        read_request(bridge, request_fixture)


def test_new_paired_seeds_are_separate_fresh_searches_with_the_fixed_local_profile(
    bridge, tmp_path
):
    plans = profile.plans("confirm_high")
    chosen = [
        next(
            p for p in plans if p["block"] == 1 and p["arm"] == arm and p["member"] == 0
        )
        for arm in ("R", "L")
    ]
    drivers, parameters = [], []
    for plan in chosen:
        legacy = SimpleNamespace()
        request = profile.request_for(plan, tmp_path / "inputs.npz", "a" * 40)
        native, driver, _, _ = bridge.context(request, legacy)
        cell = legacy.cell_for(request)
        actual = native.profile_parameters(SearchBudget(**cell["budget"]), "iterations")
        assert cell["signal"] == "confirm_high"
        assert cell["budget"]["seed"] == plan["seed"]
        assert driver.FS == 4096
        assert actual["warm_start"] is False and actual["guesses"] is None
        assert actual["optimizer_iterations"] == 300
        assert actual["optimizer_nrestarts"] == 5
        assert actual["use_frequency"] and actual["use_frequency_in_tournament"]
        assert actual["should_simplify"] is False
        assert actual["timeout_in_seconds"] is None
        assert actual["warmup_maxsize_by"] == 0.0
        drivers.append(driver)
        parameters.append(actual)
    assert drivers[0] is not drivers[1]
    assert chosen[0]["seed"] == chosen[1]["seed"]
    assert [p["niterations"] for p in parameters] == [1000, 2000]
    assert {k: v for k, v in parameters[0].items() if k != "niterations"} == {
        k: v for k, v in parameters[1].items() if k != "niterations"
    }


def verify_failed(bridge, fixture):
    root, arrays, prepared, context, _ = fixture
    return bridge.bridge.verify_result(
        root, {"cell": {"condition": "iterations"}}, arrays, prepared, None, context
    )


def test_ordinary_numerical_failure_keeps_native_cost_and_source_contracts(
    bridge, failed_worker
):
    outcome = verify_failed(bridge, failed_worker)
    assert outcome["failure_kind"] == "fit_error"
    assert outcome["resources"]["process_wall_seconds"] == 1.0


@pytest.mark.parametrize(
    "fault", ["guard", "interrupt", "unknown", "timeout_masks_interrupt"]
)
def test_real_failure_verification_rejects_integrity_errors_and_interrupts(
    bridge, failed_worker, fault
):
    root, _, _, _, documents = failed_worker
    metadata = copy.deepcopy(documents["metadata.json"])
    if fault == "guard":
        with pytest.raises(ValueError) as caught:
            SearchInvocationGuard(None, 2)._jl_call_nogil(niterations=3)
        metadata["error"] = "ValueError: " + str(caught.value)
    elif fault == "unknown":
        metadata["error"] = "RuntimeError: unknown search failure"
    else:
        metadata["error"] = "KeyboardInterrupt: "
    if fault == "timeout_masks_interrupt":
        _write_json(
            root / "worker/status.json",
            {"status": "failed", "error": "TimeoutExpired: budget"},
        )
        outcome = sources.read_json((root / "outcome.json").read_bytes())
        outcome["failure_kind"] = "worker_timeout"
        _write_json(root / "outcome.json", outcome)
    _write_json(root / "worker/metadata.json", metadata)
    with pytest.raises(ValueError):
        verify_failed(bridge, failed_worker)


@pytest.mark.parametrize("field", ["worker_provenance", "worker_adapter_source_sha256"])
@pytest.mark.parametrize("mutation", ["missing", "contradictory"])
def test_actual_failed_worker_origin_is_required_after_fit(
    bridge, failed_worker, field, mutation
):
    root, _, _, _, documents = failed_worker
    metadata = copy.deepcopy(documents["metadata.json"])
    if mutation == "missing":
        metadata.pop(field)
    else:
        metadata[field] = {"wrong": "worker"}
    _write_json(root / "worker/metadata.json", metadata)
    with pytest.raises(ValueError, match="provenance"):
        verify_failed(bridge, failed_worker)


@pytest.mark.parametrize("phase", ["before_worker_start", "fit"])
@pytest.mark.parametrize("contradiction", [False, True])
def test_early_timeout_may_lack_evidence_but_present_conflicts_always_fail(
    bridge, failed_worker, phase, contradiction
):
    root, _, _, _, documents = failed_worker
    metadata = copy.deepcopy(documents["metadata.json"])
    metadata.update(phase=phase)
    for key in (
        "error",
        "failed_during",
        "worker_provenance",
        "worker_adapter_source_sha256",
    ):
        metadata.pop(key)
    if contradiction:
        metadata["worker_provenance"] = {"wrong": "worker"}
    _write_json(root / "worker/metadata.json", metadata)
    _write_json(
        root / "worker/status.json",
        {"status": "failed", "error": "TimeoutExpired: budget"},
    )
    outcome = sources.read_json((root / "outcome.json").read_bytes())
    outcome["failure_kind"] = "worker_timeout"
    _write_json(root / "outcome.json", outcome)
    (root / "worker/time_budget_runtime.json").unlink()
    if phase == "before_worker_start" and not contradiction:
        assert verify_failed(bridge, failed_worker) == outcome
    else:
        with pytest.raises((ValueError, FileNotFoundError)):
            verify_failed(bridge, failed_worker)
