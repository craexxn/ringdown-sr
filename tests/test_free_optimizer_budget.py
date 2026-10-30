"""Counterexamples for free-budget profiles, count comparisons and replay gates."""

import copy
import importlib.util

import pytest
from test_noiseless_control import BACKEND_SEEDS, candidate, reference_tree
from test_noiseless_control import DRIVER as OLD
from test_representation_profiles import PLUGINS, fields, plugin_fixture
from test_structure import constant

from ringdown_sr import free_optimizer_budget as control
from ringdown_sr import symbolic
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _sha256
from ringdown_sr.representation_control import diagnose_candidate

SPEC = importlib.util.spec_from_file_location(
    "free_budget_driver", control.ROOT / "scripts/run_free_optimizer_budget.py"
)
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)


def option_fixture(seed, iterations):
    backend = fields("complexity_frequency", seed)
    for field in backend:
        if field["name"] == "loss_function":
            field.update(type=f"typeof({control.OBJECTIVE})", value=control.OBJECTIVE)
        elif field["name"] == "optimizer_options":
            field["value"] = field["value"].replace(
                "iterations = 20,", f"iterations = {iterations},", 1
            )
    return {
        "iterations": iterations,
        "python_seed": seed,
        "backend_seed": BACKEND_SEEDS[seed],
        "backend_options": backend,
        "plugins_field": copy.deepcopy(PLUGINS["complexity_frequency"]),
        "plugins": plugin_fixture("complexity_frequency"),
        "optimizer_settings": {
            "iterations": str(iterations),
            "callback": "nothing",
            "f_reltol": "0.0",
        },
    }


def test_frozen_design_exact_order_budget_and_plan_hash():
    cells = control.planned_cells()
    assert [(c["budget"]["seed"], c["iterations"]) for c in cells] == [
        (20261020, 20),
        (20261020, 100),
        (20261021, 100),
        (20261021, 20),
        (20261022, 20),
        (20261022, 100),
    ]
    assert all(
        c["budget"]
        == {
            "seed": c["budget"]["seed"],
            "niterations": 200,
            "populations": 2,
            "population_size": 32,
            "ncycles_per_iteration": 50,
        }
        for c in cells
    )
    assert control.LIMIT_SECONDS == 3600
    assert _sha256((control.ROOT / control.PLAN).read_bytes()) == control.PLAN_SHA256
    assert all(control.source_hashes()[src] for src in control.RUNTIME.values())


@pytest.mark.parametrize("iterations", [20, 100])
def test_only_declared_profile_changes_and_no_general_default_mutation(iterations):
    budget = symbolic.SearchBudget(seed=20261020, niterations=200)
    original = symbolic.search_parameters(budget)
    result = control.profile_parameters(budget, iterations)
    changes = {k for k in original if result[k] != original[k]}
    assert changes == {
        "loss_function",
        "use_frequency",
        "use_frequency_in_tournament",
    } | ({"optimizer_iterations"} if iterations == 100 else set())
    assert result["optimizer_nrestarts"] == 2
    assert result["guesses"] is None and result["warm_start"] is False
    assert symbolic.search_parameters(budget) == original


@pytest.mark.parametrize(
    "document",
    [
        {},
        {"format": control.PROFILE_FORMAT, "iterations": 200},
        {"format": control.PROFILE_FORMAT, "iterations": 20.0},
        {"format": control.PROFILE_FORMAT, "iterations": True},
        {"format": control.PROFILE_FORMAT, "iterations": 20, "guesses": ["truth"]},
        {"format": control.PROFILE_FORMAT, "iterations": 20, "use_frequency": False},
    ],
)
def test_profile_rejects_overrides_truth_and_unapproved_budgets(document):
    with pytest.raises(ValueError):
        control.checked_profile(document)


@pytest.mark.parametrize("seed", control.SEEDS)
@pytest.mark.parametrize("iterations", control.ITERATIONS)
def test_absolute_options_include_first_seed_and_preserve_plugin_field(
    seed, iterations
):
    value = option_fixture(seed, iterations)
    original = copy.deepcopy(value)
    assert (
        control.verify_options(value, seed, iterations, OLD, OLD.load_support())[
            "status"
        ]
        == "passed"
    )
    assert value == original
    assert "plugins" in control.common_options(value, OLD.load_support())["fields"]


def complete_cells(low, high):
    arrays = frozen_data()
    cells = control.planned_cells()
    for cell in cells:
        index = control.SEEDS.index(cell["budget"]["seed"])
        success = (low if cell["iterations"] == 20 else high)[index]
        trees = [reference_tree() if success else constant(0), reference_tree()]
        records = [
            diagnose_candidate(
                candidate(tree, arrays), i, 0, arrays, "complexity_frequency"
            )
            for i, tree in enumerate(trees)
        ]
        cell.update(
            status="completed", diagnostics={"selected_index": 0, "candidates": records}
        )
    return cells


@pytest.mark.parametrize(
    "low,high,outcome,counts",
    [
        ([1, 1, 1], [1, 0, 0], "fewer_successes", (3, 1)),
        ([1, 1, 1], [1, 1, 1], "equal_successes", (3, 3)),
        ([0, 0, 0], [0, 0, 0], "no_successes", (0, 0)),
        ([1, 0, 0], [0, 1, 1], "more_successes", (1, 2)),
        ([1, 0, 0], [0, 1, 0], "equal_successes", (1, 1)),
    ],
)
def test_review_counterexamples_compare_counts_before_structure(
    low, high, outcome, counts
):
    cells = complete_cells(low, high)
    for cell in cells:
        if cell["iterations"] == 100:
            cell["diagnostics"]["candidates"][0]["parameter_match"]["status"] = (
                "not_assessed"
            )
    result = control.comparison(cells, final_verified=True)
    assert result["comparison"]["outcome"] == outcome
    assert (result["comparison"]["C20"], result["comparison"]["C100"]) == counts
    assert result["summaries"]["100"]["supported_reconstructions"] == 0
    transitions = result["comparison"]["transitions"]
    assert (
        transitions.get("0->1", 0) - transitions.get("1->0", 0) == counts[1] - counts[0]
    )
    assert sum(transitions.values()) == 3
    for pair in result["pair_differences"]:
        parameters = [
            v for name, v in pair["metrics"].items() if name.startswith("parameter/")
        ]
        assert parameters and all(v["difference"] is None for v in parameters)


@pytest.mark.parametrize(
    "fault", ["final", "missing", "failed", "other_tree", "replay"]
)
def test_incomplete_or_unselected_or_unreplayed_trees_cannot_lift_results(fault):
    cells = complete_cells([0, 0, 0], [0, 0, 0])
    verified = True
    if fault == "final":
        verified = False
    elif fault == "missing":
        cells.pop()
    elif fault == "failed":
        cells[-1]["status"] = "failed"
    elif fault == "replay":
        selected = cells[0]["diagnostics"]["candidates"][1]
        selected["physical_analysis"]["raw_replay"]["status"] = "failed"
        assert not control.supported_reconstruction(selected)
    result = control.comparison(cells, final_verified=verified)
    if fault in {"final", "missing", "failed"}:
        assert all(value is None for value in result.values())
    else:
        assert result["comparison"]["C100"] == result["comparison"]["C20"] == 0
        assert result["summaries"]["100"]["unselected_curve_successes"] == 3
        assert result["summaries"]["100"]["supported_reconstructions"] == 0
