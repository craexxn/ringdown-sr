"""Exercise the new package binding through the inherited worker contracts."""

import copy
import math
from types import SimpleNamespace

import numpy as np
import pytest
import test_global_restarts
from test_local_optimizer import option_fixture as local_options
from test_noiseless_control import BACKEND_SEEDS
from test_structure import constant, operator, time_node

from ringdown_sr import assessment_sources as sources
from ringdown_sr import restart_budget_profile as profile
from ringdown_sr.pilot import _write_json
from ringdown_sr.search_duration import SearchInvocationGuard
from ringdown_sr.symbolic import SearchBudget

historical_failed_worker = test_global_restarts.failed_worker


@pytest.fixture
def bridge():
    return profile.native.load_module(
        profile.ROOT / profile.BRIDGE, "restart_budget_test_bridge"
    )


@pytest.fixture
def bound_request(bridge, monkeypatch, tmp_path):
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
    return (
        path,
        inputs,
        request,
        arrays,
        SimpleNamespace(read_json=sources.read_json),
        provenance,
    )


@pytest.mark.parametrize("action", ["prepare", "run", "verify"])
def test_every_worker_phase_uses_exact_readonly_physical_inputs(
    bridge, bound_request, action
):
    path, inputs, expected, arrays, reader, _ = bound_request
    actual, saved = bridge.checked_request(path, inputs, action, None, reader)
    assert actual == expected
    assert actual["coordinate"] == {"name": "t", "scale_hex": (1.0).hex(), "unit": "s"}
    assert all(saved[key].tobytes() == arrays[key].tobytes() for key in arrays)
    assert all(not value.flags.writeable for value in saved.values())


@pytest.mark.parametrize("fault", ["missing", "extra", "scaled", "one_bit", "signal"])
def test_input_binding_rejects_changed_roles_scale_truth_or_signal(
    bridge, bound_request, fault
):
    path, inputs, _, arrays, reader, _ = bound_request
    changed = {key: value.copy() for key, value in arrays.items()}
    if fault == "missing":
        changed.pop("diagnostic_time_s")
    elif fault == "extra":
        changed["irregular_time_s"] = changed["time_s"]
    elif fault == "scaled":
        changed["time_s"] *= 32
    elif fault == "one_bit":
        changed["observed"][0] = np.nextafter(changed["observed"][0], np.inf)
    else:
        changed, _ = profile.inputs("fixture_b", True)
    np.savez(inputs, **changed)
    with pytest.raises(ValueError, match="input roles or Float64"):
        bridge.checked_request(path, inputs, "verify", None, reader)


@pytest.mark.parametrize(
    "fault",
    [
        "scope",
        "seed",
        "adapter",
        "protocol",
        "coordinate",
        "iterations",
        "extra_long_member",
    ],
)
def test_request_cannot_change_frozen_members_or_bindings(bridge, bound_request, fault):
    path, inputs, request, _, reader, _ = bound_request
    if fault == "scope":
        request["scope"] = "scientific"
    elif fault == "seed":
        request["seed"] += 1
    elif fault == "adapter":
        request["adapter_sha256"] = "0" * 64
    elif fault == "protocol":
        request["protocol_commit"] = "f" * 40
    elif fault == "coordinate":
        request["coordinate"]["scale_hex"] = (32.0).hex()
    elif fault == "iterations":
        request["niterations"] = request["cell"]["niterations"] = 1
    else:
        request["cell"]["member"] = 2
        request["seed"] = request["cell"]["seed"] = profile.plans("fixture_a", True)[2][
            "seed"
        ]
    _write_json(path, request)
    with pytest.raises(ValueError):
        bridge.checked_request(path, inputs, "verify", None, reader)


@pytest.mark.parametrize("fault", ["dirty", "changes", "commit", "unavailable"])
def test_read_verification_requires_exact_clean_execution_sources(
    bridge, bound_request, fault
):
    path, inputs, _, _, reader, provenance = bound_request
    key, value = {
        "dirty": ("dirty", True),
        "changes": ("changes", [profile.BRIDGE]),
        "commit": ("commit", "b" * 40),
        "unavailable": ("available", False),
    }[fault]
    provenance["git"][key] = value
    with pytest.raises(ValueError, match="exact clean"):
        bridge.checked_request(path, inputs, "verify", None, reader)


def test_relocation_is_only_permitted_for_read_verification(
    bridge, bound_request, monkeypatch, tmp_path
):
    path, inputs, _, _, reader, _ = bound_request
    moved = tmp_path / "moved.npz"
    moved.write_bytes(inputs.read_bytes())
    bridge.checked_request(path, moved, "verify", None, reader)
    with pytest.raises(ValueError, match="input path"):
        bridge.checked_request(path, moved, "run", None, reader)
    monkeypatch.setattr(bridge.os, "sched_getaffinity", lambda _: {2, 3})
    with pytest.raises(ValueError, match="single-CPU"):
        bridge.checked_request(path, inputs, "prepare", None, reader)
    bridge.checked_request(path, moved, "verify", None, reader)


def test_shared_seeds_use_separate_fresh_workers_with_the_same_local_profile(
    bridge, tmp_path
):
    plans = profile.plans("anchor")
    chosen = [
        next(
            p for p in plans if p["block"] == 1 and p["arm"] == arm and p["member"] == 0
        )
        for arm in ("R", "L")
    ]
    assert chosen[0]["seed"] == chosen[1]["seed"]
    drivers = []
    parameters = []
    for plan in chosen:
        legacy = SimpleNamespace()
        request = profile.request_for(plan, tmp_path / "anchor.npz", "a" * 40)
        native, driver, _, _ = bridge.context(request, legacy)
        cell = legacy.cell_for(request)
        assert cell["signal"] == "anchor" and cell["condition"] == "iterations"
        assert cell["budget"]["seed"] == plan["seed"]
        assert cell["budget"]["niterations"] == plan["niterations"]
        actual = native.profile_parameters(SearchBudget(**cell["budget"]), "iterations")
        assert actual["warm_start"] is False and actual["guesses"] is None
        assert actual["optimizer_iterations"] == 300
        assert actual["optimizer_nrestarts"] == 5
        assert actual["use_frequency"] and actual["use_frequency_in_tournament"]
        assert actual["should_simplify"] is False
        assert actual["timeout_in_seconds"] is None
        assert actual["warmup_maxsize_by"] == 0.0
        parameters.append(actual)
        drivers.append(driver)
    assert drivers[0] is not drivers[1]
    assert parameters[0]["niterations"] == 1000
    assert parameters[1]["niterations"] == 2000
    assert {k: v for k, v in parameters[0].items() if k != "niterations"} == {
        k: v for k, v in parameters[1].items() if k != "niterations"
    }


@pytest.mark.parametrize("arm", ["R", "L"])
def test_diagnosis_uses_physical_seconds_and_preserves_the_original_candidate(
    bridge, monkeypatch, tmp_path, arm
):
    plan = next(p for p in profile.plans("anchor") if p["arm"] == arm)
    request = profile.request_for(plan, tmp_path / "inputs.npz", "a" * 40)
    driver = SimpleNamespace()
    legacy = SimpleNamespace(cell_for=lambda r: {"budget": r["cell"], "signal": "old"})
    context = (None, driver, None, None)
    monkeypatch.setattr(bridge, "base_context", lambda *args: context)
    assert bridge.context(request, legacy) is context
    assert driver.FS == 4096
    assert legacy.cell_for(request) == {"budget": plan, "signal": "anchor"}
    candidate = {
        "tree": operator(
            "*",
            operator("exp", operator("*", constant(-125), time_node())),
            operator("cos", operator("*", constant(500 * math.pi), time_node())),
        ),
        "complexity": 9,
        "loss": 1e-30,
        "display_equation": "q(t)",
    }
    original = copy.deepcopy(candidate)
    arrays, _ = profile.inputs("anchor")
    actual = driver.diagnose_cell_candidate(candidate, 2, 2, arrays, {})
    assert candidate == original
    assert actual["source_candidate_sha256"] == sources.sha256(
        sources.json_bytes(candidate)
    )
    assert actual["curve_marker"] == "within_tolerance" and actual["is_selected"]
    assert actual["physical_analysis"]["raw_parameters"]["decay_time_s"][
        "value"
    ] == pytest.approx(0.008)
    assert actual["parameter_match"]["status"] == "not_assessed"
    changed = {key: value.copy() for key, value in arrays.items()}
    changed["time_s"] *= 32
    with pytest.raises(ValueError, match="different|physical"):
        driver.diagnose_cell_candidate(candidate, 2, 2, changed, {})


def runtime():
    return {
        "cpu_name": "fixture",
        "cpu_models": ["fixture CPU"],
        "cpu_threads": 4,
        "word_size": 64,
        "julia_threads": 1,
        "interactive_threads": 0,
        "gc_threads": 1,
        "blas_threads": 1,
        "affinity": [3],
        "thread_environment": dict(profile.native.JULIA_THREADS),
    }


@pytest.fixture
def preflight(bridge, monkeypatch, tmp_path):
    plan = next(p for p in profile.plans("variant_high") if p["arm"] == "L")
    request = profile.request_for(plan, tmp_path / "anchor.npz", "a" * 40)
    legacy = SimpleNamespace()
    control, driver, support, probe = bridge.context(request, legacy)
    # Snapshot replay has its own tests; keep the actual options/reference verifier.
    monkeypatch.setattr(driver, "verify_snapshots", lambda *args: None)
    seed = plan["seed"]
    monkeypatch.setitem(
        BACKEND_SEEDS, seed, int(np.random.RandomState(seed).randint(0, 2**31 - 1))
    )
    options = local_options(seed, "local_300_5")
    options["condition"] = "iterations"
    for field in options["backend_options"]:
        if field["name"] == "loss_function":
            field.update(type=f"typeof({control.OBJECTIVE})", value=control.OBJECTIVE)
    options["backend_options"].append(
        {"name": "warmup_maxsize_by", "type": "Float64", "value": "0.0"}
    )
    common = {
        "format": control.FORMAT,
        "status": "verified",
        "source_sha256": {"source": "sha"},
        "reviewed_backend_sources": control.configuration()["reviewed_backend_sources"],
        "budget_runtime": runtime(),
    }
    documents = {
        "options": {
            **copy.deepcopy(common),
            "mode": "options",
            "callback_calls": 0,
            "profiles": [options],
        },
        "references": {
            **copy.deepcopy(common),
            "mode": "references",
            "cases": [
                {"condition": "iterations", "frequency_hz": f}
                for f in (250, 4346, 33018)
            ],
            "grammar_cases": [
                {**case, "condition": "iterations"}
                for case in control.prior.expected_grammar_cases()
            ],
        },
    }

    def verify():
        return legacy.verify_preflight(
            documents["options"],
            documents["references"],
            {},
            {"source": "sha"},
            control,
            driver,
            support,
            probe,
            seed,
        )

    verify()
    return documents, verify


@pytest.mark.parametrize(
    "fault",
    [
        "time_profile",
        "timeout",
        "local_restarts",
        "reference_source",
        "backend_source",
        "signal_reference",
        "runtime_affinity",
    ],
)
def test_actual_preflight_keeps_fixed_profile_references_and_runtime(preflight, fault):
    documents, verify = preflight
    options = documents["options"]["profiles"][0]
    fields = {field["name"]: field for field in options["backend_options"]}
    references = documents["references"]
    if fault == "time_profile":
        options["condition"] = "time"
    elif fault == "timeout":
        fields["timeout_in_seconds"].update(type="Float64", value="400.0")
    elif fault == "local_restarts":
        fields["optimizer_nrestarts"]["value"] = "2"
    elif fault == "reference_source":
        references["source_sha256"] = {}
    elif fault == "backend_source":
        references["reviewed_backend_sources"] = {}
    elif fault == "signal_reference":
        references["cases"][0]["frequency_hz"] = 320
    else:
        references["budget_runtime"]["affinity"] = [4]
        profile.native.validate_runtime(references["budget_runtime"])
    with pytest.raises(ValueError):
        verify()


@pytest.mark.parametrize("arm,iterations", [("R", 1000), ("L", 2000)])
@pytest.mark.parametrize("finished", [True, False])
def test_both_packages_require_each_members_own_iteration_limit(
    bridge, tmp_path, arm, iterations, finished
):
    count = 2 * iterations if finished else 7
    record = {
        "format": profile.native.FORMAT,
        "populations": 2,
        "processed_population_cycles": count,
        "checks": count,
        "requested_iterations": iterations,
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
    request = {
        "cell": {"condition": "iterations", "arm": arm, "niterations": iterations}
    }
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
    root, arrays, prepared, context, documents = historical_failed_worker
    documents["profile.json"]["condition"] = "iterations"
    _write_json(root / "worker/profile.json", documents["profile.json"])
    resources = {
        "scope": "worker_launcher_and_waited_descendants",
        "process_wall_seconds": 1.0,
        "cpu_user_seconds": 0.2,
        "cpu_system_seconds": 0.1,
    }
    _write_json(root / "worker_resources.json", resources)
    _write_json(root / "worker/time_budget_runtime.json", runtime())
    _write_json(root / "options.json", {"budget_runtime": runtime()})
    _write_json(
        root / "outcome.json",
        {
            "status": "worker_failed",
            "failure_kind": "fit_error",
            "resources": resources,
        },
    )
    return root, arrays, prepared, context, documents


def verify_failed(bridge, fixture):
    root, arrays, prepared, context, _ = fixture
    return bridge.bridge.verify_result(
        root, {"cell": {"condition": "iterations"}}, arrays, prepared, None, context
    )


def test_ordinary_numerical_failure_is_retained_with_all_source_and_cost_checks(
    bridge, failed_worker
):
    result = verify_failed(bridge, failed_worker)
    assert result["failure_kind"] == "fit_error"
    assert result["resources"]["process_wall_seconds"] == 1.0


@pytest.mark.parametrize(
    "fault",
    ["guard", "interrupt", "timeout_masks_interrupt", "adapter", "profile", "runtime"],
)
def test_failed_member_cannot_bypass_integrity_contracts(bridge, failed_worker, fault):
    root, _, _, _, documents = failed_worker
    metadata = documents["metadata.json"]
    if fault == "guard":
        with pytest.raises(ValueError) as caught:
            SearchInvocationGuard(None, 2)._jl_call_nogil(niterations=3)
        metadata["error"] = "ValueError: " + str(caught.value)
    elif fault in {"interrupt", "timeout_masks_interrupt"}:
        metadata["error"] = "KeyboardInterrupt: "
        if fault == "timeout_masks_interrupt":
            _write_json(
                root / "worker/status.json",
                {"status": "failed", "error": "TimeoutExpired: budget"},
            )
            outcome = sources.read_json((root / "outcome.json").read_bytes())
            outcome["failure_kind"] = "worker_timeout"
            _write_json(root / "outcome.json", outcome)
    elif fault == "adapter":
        metadata["worker_adapter_source_sha256"] = {"adapter": "different"}
    elif fault == "profile":
        _write_json(
            root / "worker/profile.json", {"format": "profile", "condition": "time"}
        )
    else:
        _write_json(
            root / "worker/time_budget_runtime.json", {**runtime(), "affinity": [4]}
        )
    _write_json(root / "worker/metadata.json", metadata)
    with pytest.raises(ValueError):
        verify_failed(bridge, failed_worker)


@pytest.mark.parametrize("phase", ["before_worker_start", "fit", "replay"])
@pytest.mark.parametrize("runtime_present", [False, True])
def test_timeout_requires_phase_specific_runtime_and_rejects_present_conflicts(
    bridge, failed_worker, phase, runtime_present
):
    root, _, _, _, documents = failed_worker
    metadata = documents["metadata.json"]
    metadata.update(phase=phase)
    metadata.pop("error")
    metadata.pop("failed_during")
    if phase == "before_worker_start":
        metadata.pop("worker_provenance")
        metadata.pop("worker_adapter_source_sha256")
    _write_json(root / "worker/metadata.json", metadata)
    _write_json(
        root / "worker/status.json",
        {"status": "failed", "error": "TimeoutExpired: budget"},
    )
    outcome = sources.read_json((root / "outcome.json").read_bytes())
    outcome["failure_kind"] = "worker_timeout"
    _write_json(root / "outcome.json", outcome)
    runtime_path = root / "worker/time_budget_runtime.json"
    if runtime_present:
        _write_json(runtime_path, {**runtime(), "affinity": [4]})
    else:
        runtime_path.unlink()
    if phase == "before_worker_start" and not runtime_present:
        assert verify_failed(bridge, failed_worker) == outcome
    else:
        with pytest.raises((ValueError, FileNotFoundError)):
            verify_failed(bridge, failed_worker)
