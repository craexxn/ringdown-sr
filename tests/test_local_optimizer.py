"""Independent factorial contrasts, absolute budget fields and immutable policies."""

import copy
import itertools
import subprocess
from collections import Counter

import pytest
import test_search_duration as duration_tests
from test_noiseless_control import BACKEND_SEEDS
from test_noiseless_control import DRIVER as OLD
from test_search_duration import option_fixture as duration_options

from ringdown_sr import local_optimizer as control
from ringdown_sr import search_duration as duration
from ringdown_sr.constant_diagnostic import backend_seed
from ringdown_sr.pilot import _sha256
from ringdown_sr.symbolic import SearchBudget

NATIVE_SEEDS = {
    20261120: 2125027390,
    20261121: 645605771,
    20261122: 749285051,
    20261123: 1762788718,
    20261124: 1362583845,
}


@pytest.fixture(scope="module")
def diagnoses():
    return duration_tests.diagnoses.__wrapped__()


@pytest.fixture(autouse=True)
def seed_mapping(monkeypatch):
    for seed, native in NATIVE_SEEDS.items():
        monkeypatch.setitem(BACKEND_SEEDS, seed, native)


def option_fixture(seed, condition):
    iterations, restarts = {
        "local_100_2": (100, 2),
        "local_300_2": (300, 2),
        "local_100_5": (100, 5),
        "local_300_5": (300, 5),
    }[condition]
    record = duration_options(seed, "unrestricted")
    record["condition"] = condition
    record["optimizer_settings"]["iterations"] = str(iterations)
    for field in record["backend_options"]:
        if field["name"] == "optimizer_options":
            field["value"] = field["value"].replace(
                "iterations = 100,", f"iterations = {iterations},"
            )
        elif field["name"] == "optimizer_nrestarts":
            field["value"] = str(restarts)
        elif field["name"] == "loss_function":
            field.update(
                type="typeof(Main.LocalOptimizerBudget.objective)",
                value="Main.LocalOptimizerBudget.objective",
            )
    return record


def test_bound_design_seeds_and_only_two_profile_factors():
    cells = control.planned_cells()
    assert control.SEEDS == tuple(range(20261120, 20261125))
    assert set(control.SEEDS).isdisjoint(duration.SEEDS)
    assert {seed: backend_seed(seed) for seed in control.SEEDS} == NATIVE_SEEDS
    labels = [c["condition"] for c in cells]
    b, i, r, x = "local_100_2", "local_300_2", "local_100_5", "local_300_5"
    assert labels == [b, i, x, r, i, r, b, x, r, x, i, b, x, b, r, i, b, i, x, r]
    assert Counter(labels) == {b: 5, i: 5, r: 5, x: 5}
    assert all(set(labels[p:16:4]) == {b, i, r, x} for p in range(4))
    assert len({(labels[p], labels[p + 1]) for p in range(16) if p % 4 != 3}) == 12
    assert (control.WORKER_LIMIT_SECONDS, control.LIMIT_SECONDS) == (600, 7200)
    contents = (control.ROOT / control.PLAN).read_bytes()
    assert _sha256(contents) == control.PLAN_SHA256
    assert (
        subprocess.check_output(
            ["git", "show", f"{control.PLAN_COMMIT}:{control.PLAN}"], cwd=control.ROOT
        )
        == contents
    )
    assert all(control.source_hashes()[p] for p in control.RUNTIME.values())
    for cell in cells:
        budget = SearchBudget(**cell["budget"])
        assert cell["grammar"] == "unrestricted" and budget.niterations == 200
        old = duration.profile_parameters(budget, "unrestricted")
        actual = control.profile_parameters(budget, cell["condition"])
        assert actual == {
            **old,
            "loss_function": control.OBJECTIVE,
            "optimizer_iterations": int(cell["condition"].split("_")[1]),
            "optimizer_nrestarts": int(cell["condition"].split("_")[2]),
        }
        assert old["optimizer_iterations"] == 100 and old["optimizer_nrestarts"] == 2
        assert (
            actual["should_simplify"] is False and actual["nested_constraints"] is None
        )


@pytest.mark.parametrize("seed", tuple(NATIVE_SEEDS))
@pytest.mark.parametrize(
    "condition", ("local_100_2", "local_300_2", "local_100_5", "local_300_5")
)
def test_absolute_native_profiles_and_normalization_preserve_source(seed, condition):
    record = option_fixture(seed, condition)
    original = copy.deepcopy(record)
    assert (
        control.verify_options(record, seed, condition, OLD, OLD.load_support())[
            "status"
        ]
        == "passed"
    )
    baseline = option_fixture(20261120, "local_100_2")
    assert control.common_options(record, OLD.load_support()) == control.common_options(
        baseline, OLD.load_support()
    )
    assert original == record


@pytest.mark.parametrize(
    "fault",
    [
        "iterations",
        "iterations_missing",
        "restarts",
        "restarts_type",
        "restarts_missing",
        "snapshot",
        "condition",
        "objective",
        "simplify",
        "nested",
        "seed",
        "plugin",
    ],
)
def test_wrong_fields_fail_before_normalization(fault):
    record = option_fixture(20261120, "local_300_5")
    fields = {f["name"]: f for f in record["backend_options"]}
    if fault.startswith("iterations"):
        fields["optimizer_options"]["value"] = (
            "Options(other_iterations = 300,)"
            if fault.endswith("missing")
            else "Options(iterations = 100,)"
        )
    elif fault.startswith("restarts"):
        if fault.endswith("missing"):
            record["backend_options"].remove(fields["optimizer_nrestarts"])
        elif fault.endswith("type"):
            fields["optimizer_nrestarts"]["type"] = "Bool"
        else:
            fields["optimizer_nrestarts"]["value"] = "2"
    elif fault == "snapshot":
        record["optimizer_settings"]["iterations"] = "100"
    elif fault == "condition":
        record["condition"] = "local_100_5"
    elif fault == "objective":
        fields["loss_function"]["value"] = "Main.TrigonometricGrammar.objective"
    elif fault == "simplify":
        fields["should_simplify"]["value"] = "true"
    elif fault == "nested":
        fields["nested_constraints"]["value"] = "[]"
    elif fault == "seed":
        record["backend_seed"] += 1
    else:
        record["plugins"] = []
    with pytest.raises(ValueError):
        control.verify_options(record, 20261120, "local_300_5", OLD, OLD.load_support())


def completed(diagnoses, success):
    cells = control.planned_cells()
    for cell in cells:
        chosen = copy.deepcopy(diagnoses[int(success(cell))])
        unselected = copy.deepcopy(diagnoses[1])
        unselected.update(source_index=1, is_selected=False)
        cell.update(
            status="completed",
            diagnostics={"selected_index": 0, "candidates": [chosen, unselected]},
        )
    return cells


def test_all_block_patterns_keep_simple_effects_baseline_and_interaction(diagnoses):
    names = ("local_100_2", "local_300_2", "local_100_5", "local_300_5")
    contrasts = ((0, 1), (2, 3), (0, 2), (1, 3), (0, 3))
    for pattern in itertools.product((False, True), repeat=4):
        # Rotate all four combinations across seeds to exercise asymmetric pairs.
        for rotate in (False, True):

            def success(cell, rotate=rotate, pattern=pattern):
                offset = (cell["budget"]["seed"] - 20261120) if rotate else 0
                return pattern[(names.index(cell["condition"]) + offset) % 4]

            cells = completed(diagnoses, success)
            result = control.comparison(cells, final_verified=True)
            counts = [
                sum(success(c) for c in cells if c["condition"] == name)
                for name in names
            ]
            assert [
                result["summaries"][name]["curve_successes"] for name in names
            ] == counts
            assert len(result["pair_differences"]) == 25
            assert (
                result["comparison"]["count_interaction"]
                == counts[3] - counts[2] - counts[1] + counts[0]
            )
            for value, (left, right) in zip(
                result["comparison"]["contrasts"].values(), contrasts, strict=True
            ):
                assert value["difference"] == counts[right] - counts[left]
                assert sum(value["transitions"].values()) == 5
                assert value["development_signal"] == (
                    "supported_structure_gain"
                    if counts[right] > counts[left]
                    else "hypothesis_not_supported"
                )


@pytest.mark.parametrize(
    "fault", ["parameters", "structure", "raw_replay", "alias_replay"]
)
def test_new_support_must_belong_to_same_newly_successful_original_selection(
    diagnoses, fault
):
    cells = completed(
        diagnoses,
        lambda c: c["condition"] != "local_100_2" or c["budget"]["seed"] == 20261120,
    )
    for cell in cells:
        if cell["budget"]["seed"] == 20261120:
            continue  # Retain an old supported success, which cannot certify new gains.
        chosen = control.selected(cell)
        if fault == "parameters":
            chosen["parameter_match"]["status"] = "not_assessed"
        elif fault == "structure":
            chosen["search_analysis"]["structure"]["structure_status"] = "not_supported"
        else:
            chosen["physical_analysis"][fault]["status"] = "failed"
    result = control.comparison(cells, final_verified=True)
    for key in result["comparison"]["baseline_contrasts"]:
        assert (
            result["comparison"]["contrasts"][key]["development_signal"]
            == "approximation_gain_only"
        )


def test_unselected_good_candidates_and_unavailable_metrics_never_create_success(
    diagnoses,
):
    cells = completed(diagnoses, lambda _: False)
    control.selected(cells[0])["curve_errors"]["diagnostic"].update(
        status="not_available", relative_rms=None, relative_max=None
    )
    result = control.comparison(cells, final_verified=True)
    assert all(
        s["curve_successes"] == 0 and s["unselected_curve_successes"] == 5
        for s in result["summaries"].values()
    )
    assert (
        result["summaries"]["local_100_2"]["statistics"]["diagnostic/relative_rms"][
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


@pytest.mark.parametrize(
    "fault", ["pending", "missing", "failed", "order", "outer_budget", "grammar"]
)
def test_incomplete_or_changed_design_never_releases_aggregates(diagnoses, fault):
    cells = completed(diagnoses, lambda _: False)
    if fault == "missing":
        cells.pop()
    elif fault == "failed":
        cells[-1]["status"] = "failed"
    elif fault == "order":
        cells.reverse()
    elif fault == "outer_budget":
        cells[0]["budget"]["niterations"] = 2000
    elif fault == "grammar":
        cells[0]["grammar"] = "no_nested_trig"
    if fault in {"order", "outer_budget", "grammar"}:
        with pytest.raises(ValueError):
            control.comparison(cells, final_verified=True)
    else:
        assert all(
            v is None
            for v in control.comparison(
                cells, final_verified=fault != "pending"
            ).values()
        )


def test_each_pair_carries_its_own_original_costs_and_explicit_wall_scope(diagnoses):
    cells = completed(diagnoses, lambda _: False)
    for cell in cells:
        cell["diagnostics"].update(
            worker_wall_seconds=float(cell["number"]),
            timing_seconds={"fit_including_jit_and_python_exports": cell["number"] / 2},
            callback_calls_during_fit=10 * cell["number"],
            backend_evaluation_counter={"status": "unavailable"},
        )
    result = control.comparison(cells, final_verified=True)
    for pair in result["pair_differences"]:
        for side in ("first", "second"):
            number = pair[side + "_cell"]
            costs = pair["costs"][side]
            assert costs["worker_wall_seconds"] == number
            assert costs["callback_calls_during_fit"] == 10 * number
            assert (
                costs["timing_seconds"]["fit_including_jit_and_python_exports"]
                == number / 2
            )
            assert costs["backend_evaluation_counter"] == {"status": "unavailable"}
            assert (
                costs["worker_wall_seconds_scope"]
                == "worker_launch_and_parent_verification"
            )


def test_invalid_profile_and_changed_bound_plan_fail(monkeypatch, tmp_path):
    for condition in (None, True, [], "unrestricted", "local_500_2"):
        with pytest.raises(ValueError):
            control.checked_profile(
                {"format": control.PROFILE_FORMAT, "condition": condition}
            )
    path = tmp_path / "changed.md"
    path.write_text("changed plan\n")
    monkeypatch.setattr(control, "PLAN", str(path))
    with pytest.raises(ValueError):
        control.source_hashes()
