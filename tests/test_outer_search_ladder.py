"""Independent budget design, distinct curve/support counts and exact guards."""

import copy
import itertools
import subprocess
from collections import Counter

import pytest
import test_search_duration as duration_tests
from test_local_optimizer import option_fixture
from test_noiseless_control import BACKEND_SEEDS
from test_noiseless_control import DRIVER as OLD

from ringdown_sr import local_optimizer as prior
from ringdown_sr import outer_search_ladder as control
from ringdown_sr.constant_diagnostic import backend_seed
from ringdown_sr.pilot import _sha256
from ringdown_sr.symbolic import SearchBudget

NATIVE_SEEDS = {
    20261201: 251545258,
    20261202: 1693883930,
    20261203: 1061961791,
    20261204: 1660936152,
    20261205: 1337693906,
}


@pytest.fixture(scope="module")
def diagnoses():
    return duration_tests.diagnoses.__wrapped__()


@pytest.fixture(autouse=True)
def seed_mapping(monkeypatch):
    for seed, native in NATIVE_SEEDS.items():
        monkeypatch.setitem(BACKEND_SEEDS, seed, native)


def test_bound_plan_order_and_fixed_local_profile():
    assert control.SEEDS == tuple(range(20261201, 20261206))
    assert set(control.SEEDS).isdisjoint(prior.SEEDS)
    assert {s: backend_seed(s) for s in control.SEEDS} == NATIVE_SEEDS
    assert (control.LIMIT_SECONDS, control.WORKER_LIMIT_SECONDS) == (14400, 1800)
    cells = control.planned_cells()
    labels = [c["budget"]["niterations"] for c in cells]
    assert labels == [
        200,
        500,
        5000,
        2000,
        500,
        2000,
        200,
        5000,
        2000,
        5000,
        500,
        200,
        5000,
        200,
        2000,
        500,
        200,
        500,
        5000,
        2000,
    ]
    assert Counter(labels) == {200: 5, 500: 5, 2000: 5, 5000: 5}
    assert all(set(labels[p:16:4]) == {200, 500, 2000, 5000} for p in range(4))
    assert len({(labels[i], labels[i + 1]) for i in range(16) if i % 4 != 3}) == 12
    common = None
    for c in cells:
        assert c["condition"] == c["arm"] == "local_300_5"
        assert c["grammar"] == "unrestricted"
        budget = SearchBudget(**c["budget"])
        actual = control.profile_parameters(budget, c["condition"])
        assert actual == prior.profile_parameters(budget, "local_300_5")
        assert (
            actual["optimizer_iterations"] == 300 and actual["optimizer_nrestarts"] == 5
        )
        value = control.common_parameters(actual)
        assert common is None or common == value
        common = value
    assert "optimizer_iterations" in common and "optimizer_nrestarts" in common
    assert len(control.search_profiles()) == 20
    contents = (control.ROOT / control.PLAN).read_bytes()
    assert _sha256(contents) == control.PLAN_SHA256
    assert (
        subprocess.check_output(
            ["git", "show", f"{control.PLAN_COMMIT}:{control.PLAN}"], cwd=control.ROOT
        )
        == contents
    )


@pytest.mark.parametrize("seed", tuple(NATIVE_SEEDS))
def test_native_300_5_fields_seeds_and_source_preserved(seed):
    record = option_fixture(seed, "local_300_5")
    original = copy.deepcopy(record)
    assert (
        control.verify_options(record, seed, "local_300_5", OLD, OLD.load_support())[
            "status"
        ]
        == "passed"
    )
    control.common_options(record, OLD.load_support())
    assert record == original


@pytest.mark.parametrize(
    "fault", ["iterations", "restarts", "seed", "simplify", "plugin", "profile"]
)
def test_wrong_native_profile_is_rejected_before_normalization(fault):
    record = option_fixture(20261201, "local_300_5")
    fields = {f["name"]: f for f in record["backend_options"]}
    if fault == "iterations":
        fields["optimizer_options"]["value"] = "Options(iterations = 100,)"
    elif fault == "restarts":
        fields["optimizer_nrestarts"]["value"] = "2"
    elif fault == "seed":
        record["backend_seed"] += 1
    elif fault == "simplify":
        fields["should_simplify"]["value"] = "true"
    elif fault == "plugin":
        record["plugins"] = []
    else:
        record = option_fixture(20261201, "local_100_2")
    with pytest.raises(ValueError):
        control.verify_options(record, 20261201, "local_300_5", OLD, OLD.load_support())


def completed(diagnoses, state):
    cells = control.planned_cells()
    for c in cells:
        value = state(c)
        chosen = copy.deepcopy(diagnoses[int(value > 0)])
        if value == 1:
            chosen["parameter_match"]["status"] = "not_assessed"
        unselected = copy.deepcopy(diagnoses[1])
        unselected.update(source_index=1, is_selected=False)
        c.update(
            status="completed",
            diagnostics={"selected_index": 0, "candidates": [chosen, unselected]},
        )
    return cells


def test_all_curve_support_states_and_asymmetric_seed_pairs(diagnoses):
    levels = (200, 500, 2000, 5000)
    contrasts = ((0, 1), (1, 2), (2, 3), (0, 2), (0, 3))
    for pattern in itertools.product(range(3), repeat=4):
        for rotate in (False, True):

            def state(c, pattern=pattern, rotate=rotate):
                return pattern[
                    (
                        levels.index(c["budget"]["niterations"])
                        + (c["budget"]["seed"] - 20261201 if rotate else 0)
                    )
                    % 4
                ]

            cells = completed(diagnoses, state)
            result = control.comparison(cells, final_verified=True)
            counts = [
                (
                    sum(state(c) > 0 for c in cells if c["budget"]["niterations"] == n),
                    sum(
                        state(c) == 2 for c in cells if c["budget"]["niterations"] == n
                    ),
                )
                for n in levels
            ]
            assert [
                (s["curve_successes"], s["supported_reconstructions"])
                for s in result["summaries"].values()
            ] == counts
            assert len(result["pair_differences"]) == 25
            for value, (left, right) in zip(
                result["comparison"]["contrasts"].values(), contrasts, strict=True
            ):
                dc, ds = (counts[right][i] - counts[left][i] for i in (0, 1))
                assert (value["curve_difference"], value["supported_difference"]) == (
                    dc,
                    ds,
                )
                for name, predicate in [
                    ("curve_transitions", lambda v: v > 0),
                    ("supported_transitions", lambda v: v == 2),
                ]:
                    pairs = [
                        (
                            state(
                                next(
                                    c
                                    for c in cells
                                    if c["budget"]["seed"] == seed
                                    and c["budget"]["niterations"] == levels[i]
                                )
                            )
                        )
                        for seed in control.SEEDS
                        for i in (left, right)
                    ]
                    expected = {
                        f"{a}->{b}": sum(
                            predicate(pairs[j]) == bool(a)
                            and predicate(pairs[j + 1]) == bool(b)
                            for j in range(0, 10, 2)
                        )
                        for a in (0, 1)
                        for b in (0, 1)
                    }
                    assert value[name] == expected
                expected = (
                    "curve_and_supported_count_gain"
                    if dc > 0 and ds > 0
                    else "supported_count_gain_only"
                    if ds > 0
                    else "curve_count_gain_only"
                    if dc > 0
                    else "no_count_gain"
                )
                assert value["count_outcome"] == expected


def test_new_supported_seed_with_lost_support_does_not_raise_support_count(diagnoses):
    def state(c):
        seed, n = c["budget"]["seed"], c["budget"]["niterations"]
        return (
            (2 if seed == 20261201 else 0)
            if n == 200
            else (2 if seed == 20261202 else 1 if seed == 20261201 else 0)
        )

    result = control.comparison(completed(diagnoses, state), final_verified=True)
    for name in result["comparison"]["baseline_contrasts"]:
        value = result["comparison"]["contrasts"][name]
        assert (value["curve_difference"], value["supported_difference"]) == (1, 0)
        assert (
            value["supported_transitions"]["0->1"]
            == value["supported_transitions"]["1->0"]
            == 1
        )
        assert value["count_outcome"] == "curve_count_gain_only"


@pytest.mark.parametrize(
    "fault", ["structure", "parameters", "raw_replay", "alias_replay"]
)
def test_support_gates_require_same_selected_candidate(diagnoses, fault):
    cells = completed(diagnoses, lambda c: 2)
    for c in cells:
        d = control.selected(c)
        if fault == "structure":
            d["search_analysis"]["structure"]["structure_status"] = "not_supported"
        elif fault == "parameters":
            d["parameter_match"]["status"] = "not_assessed"
        else:
            d["physical_analysis"][fault]["status"] = "failed"
    result = control.comparison(cells, final_verified=True)
    assert all(
        s["curve_successes"] == 5 and s["supported_reconstructions"] == 0
        for s in result["summaries"].values()
    )


def test_unselected_candidates_missing_metrics_and_costs(diagnoses):
    cells = completed(diagnoses, lambda c: 0)
    control.selected(cells[0])["curve_errors"]["diagnostic"].update(
        status="not_available", relative_rms=None, relative_max=None
    )
    for c in cells:
        c["diagnostics"].update(
            worker_wall_seconds=float(c["number"]),
            timing_seconds={"fit_including_jit_and_python_exports": c["number"] / 2},
            callback_calls_during_fit=10 * c["number"],
        )
    result = control.comparison(cells, final_verified=True)
    assert all(
        s["curve_successes"] == s["supported_reconstructions"] == 0
        and s["unselected_curve_successes"] == 5
        for s in result["summaries"].values()
    )
    assert (
        result["summaries"]["200"]["statistics"]["diagnostic/relative_rms"][
            "finite_count"
        ]
        == 4
    )
    assert (
        result["pair_differences"][0]["metrics"]["diagnostic/relative_rms"][
            "difference"
        ]
        is None
    )
    for p in result["pair_differences"]:
        a, b = p["first_cell"], p["second_cell"]
        delta = p["cost_changes"]["worker_wall_seconds"]
        assert (
            delta["first"],
            delta["second"],
            delta["difference"],
            delta["ratio"],
        ) == (float(a), float(b), b - a, b / a)
        assert (
            p["costs"]["first"]["worker_wall_seconds_scope"]
            == "worker_launch_and_parent_verification"
        )
    assert control._cost_change(None, 1)["difference"] is None
    assert control._cost_change(0, 1)["ratio"] is None
    assert control._cost_change(1e-308, 1e308)["ratio"] is None


@pytest.mark.parametrize(
    "fault", ["pending", "missing", "failed", "order", "budget", "grammar"]
)
def test_incomplete_or_changed_design_never_releases_aggregates(diagnoses, fault):
    cells = completed(diagnoses, lambda c: 2)
    if fault == "missing":
        cells.pop()
    elif fault == "failed":
        cells[-1]["status"] = "failed"
    elif fault == "order":
        cells.reverse()
    elif fault == "budget":
        cells[0]["budget"]["niterations"] = 500
    elif fault == "grammar":
        cells[0]["grammar"] = "no_nested_trig"
    if fault in ("order", "budget", "grammar"):
        with pytest.raises(ValueError):
            control.comparison(cells, final_verified=True)
    else:
        assert all(
            v is None
            for v in control.comparison(
                cells, final_verified=fault != "pending"
            ).values()
        )


@pytest.mark.parametrize("iterations", [200, 500, 2000, 5000])
def test_guard_delegates_exact_requested_budget_once(iterations):
    class Search:
        def __init__(self):
            self.calls = []

        def _jl_call_nogil(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            return object()

    class Backend:
        pass

    backend = Backend()
    backend.equation_search = Search()
    guard = control.SearchInvocationGuard(backend, iterations)
    kwargs = {
        "niterations": iterations,
        "parallelism": "serial",
        "return_state": True,
        "saved_state": None,
        "guesses": None,
        "weights": None,
    }
    args = (object(), object())
    guard._jl_call_nogil(*args, **kwargs)
    assert backend.equation_search.calls == [(args, kwargs)]
    assert guard.record() == control.invocation_record(iterations)
    with pytest.raises(ValueError):
        guard._jl_call_nogil(*args, **kwargs)
    for mutation in (
        {"niterations": iterations + 1},
        {"saved_state": object()},
        {"guesses": object()},
    ):
        fresh = control.SearchInvocationGuard(backend, iterations)
        with pytest.raises(ValueError):
            fresh._jl_call_nogil(*args, **(kwargs | mutation))
    assert len(backend.equation_search.calls) == 1
