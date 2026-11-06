"""Counterexamples for the separately frozen iteration/time comparison."""

import copy
from types import SimpleNamespace

import pytest

from ringdown_sr import assessment_sources as sources
from ringdown_sr import time_budget_profile as profile
from ringdown_sr.pilot import _write_json
from ringdown_sr.symbolic import ROOT, SearchBudget

bridge = profile.load_module(
    ROOT / "scripts/time_budget_bridge.py", "tested_time_bridge"
)


def test_frozen_paired_schedules_never_mix_reused_and_fresh_controls():
    fresh, reuse = bridge.cells("fresh_all"), bridge.cells("reuse_pr76")
    assert len(fresh) == 8 and len(reuse) == 4
    assert [cell["arm"] for cell in fresh] == list("IZZ IIZZI".replace(" ", ""))
    assert [cell["seed"] for cell in reuse] == [20261201, 20261210, 20261211, 20261212]
    assert all(cell["arm"] == "Z" and cell["niterations"] == 1000000 for cell in reuse)
    assert [cell["seed"] for cell in fresh if cell["arm"] == "I"] == [
        cell["seed"] for cell in reuse
    ]
    assert all(cell["niterations"] == 2000 for cell in fresh if cell["arm"] == "I")
    with pytest.raises(ValueError, match="explicit"):
        bridge.cells("automatic")


def test_new_profile_only_changes_the_declared_stopping_fields_and_wrapper():
    budget = SearchBudget(seed=20261210, niterations=1000000)
    old = profile.prior.profile_parameters(budget, "local_300_5")
    new = profile.profile_parameters(budget, "time")
    assert new["optimizer_iterations"] == 300 and new["optimizer_nrestarts"] == 5
    assert new["use_frequency"] and new["use_frequency_in_tournament"]
    assert new["should_simplify"] is False
    assert new["timeout_in_seconds"] == 400 and new["warmup_maxsize_by"] == 0
    assert {
        k: v
        for k, v in new.items()
        if k not in {"loss_function", "timeout_in_seconds", "warmup_maxsize_by"}
    } == {
        k: v for k, v in old.items() if k not in {"loss_function", "timeout_in_seconds"}
    }
    assert profile.configuration()["worker_seconds"] == 1800
    assert profile.configuration()["total_seconds"] == 7200


def clock_fixture(tmp_path, condition="time", count=7, elapsed=400.25):
    (tmp_path / "worker").mkdir(exist_ok=True)
    iterations = 2000 if condition == "iterations" else 1000000
    record = {
        "format": profile.FORMAT,
        "populations": 2,
        "processed_population_cycles": count,
        "checks": count,
        "requested_iterations": iterations,
        "completed_outer_rounds": count // 2,
        "residual_population_cycles": count % 2,
        "iteration_limit_reached": count == 2 * iterations,
        "technical_counter_stop": False,
        "affinity": [3],
        "native_start_unix_seconds": 1.0,
        "elapsed_at_last_check_seconds": elapsed,
        "main_loop_call_wall_seconds": elapsed + 1,
        "clock_difference_seconds": 0.0,
        "timeout_reached": condition != "iterations" and elapsed > 400,
    }
    request = {
        "cell": {
            "condition": condition,
            "arm": "I" if condition == "iterations" else "Z",
            "niterations": iterations,
        }
    }
    return request, record


@pytest.mark.parametrize(
    ("condition", "count", "elapsed", "reason"),
    [
        ("time", 7, 400.25, "regular_timeout"),
        ("time", 2000000, 3.0, "iteration_reserve"),
        ("time", 2000000, 401.0, "iteration_reserve"),
        ("iterations", 4000, 300.0, "iteration_limit"),
    ],
)
def test_regular_time_and_reserve_have_distinct_reasons(
    tmp_path, condition, count, elapsed, reason
):
    request, record = clock_fixture(tmp_path, condition, count, elapsed)
    _write_json(tmp_path / "worker/time_budget_clock.json", record)
    actual = bridge.clock_evidence(
        tmp_path, request, SimpleNamespace(read_json=sources.read_json)
    )
    assert actual["reason"] == reason
    assert actual["clock"]["completed_outer_rounds"] == count // 2
    assert actual["overshoot_seconds"] == (
        max(0, elapsed - 400) if condition == "time" else None
    )


@pytest.mark.parametrize(
    "mutation",
    [
        {"checks": 8},
        {"completed_outer_rounds": 4},
        {"iteration_limit_reached": True},
        {"technical_counter_stop": True},
        {"affinity": [1, 2]},
        {"timeout_reached": False},
        {"clock_difference_seconds": 2},
        {"elapsed_at_last_check_seconds": float("nan")},
    ],
)
def test_inconsistent_or_technical_native_stop_cannot_be_scientific_completion(
    tmp_path, mutation
):
    request, record = clock_fixture(tmp_path)
    record.update(copy.deepcopy(mutation))
    # The test parser permits NaN solely to exercise the numeric fail-closed gate.
    import json

    (tmp_path / "worker/time_budget_clock.json").write_text(json.dumps(record))
    with pytest.raises(ValueError):
        bridge.clock_evidence(tmp_path, request, SimpleNamespace(read_json=json.loads))


def test_early_return_without_a_timer_or_iteration_limit_is_not_success(tmp_path):
    request, record = clock_fixture(tmp_path, "iterations", 7, 4.0)
    _write_json(tmp_path / "worker/time_budget_clock.json", record)
    with pytest.raises(ValueError, match="without its allowed"):
        bridge.clock_evidence(
            tmp_path, request, SimpleNamespace(read_json=sources.read_json)
        )
