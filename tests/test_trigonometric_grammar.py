"""Counterexamples for the single grammar intervention and its decision gates."""

import copy
import importlib.util

import pytest
from test_free_optimizer_budget import option_fixture as budget_options
from test_noiseless_control import DRIVER as OLD
from test_noiseless_control import candidate, reference_tree
from test_structure import constant

from ringdown_sr import symbolic
from ringdown_sr import trigonometric_grammar as control
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _sha256
from ringdown_sr.representation_control import diagnose_candidate

SPEC = importlib.util.spec_from_file_location(
    "grammar_driver", control.ROOT / "scripts/run_trigonometric_grammar.py"
)
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)
NESTING = {
    "type": "Vector{Tuple{Int64, Int64, Vector{Tuple{Int64, Int64, Int64}}}}",
    "value": "[(1, 2, [(1, 2, 0), (1, 3, 0)]), (1, 3, [(1, 2, 0), (1, 3, 0)])]",
}


def option_fixture(seed, condition):
    record = budget_options(seed, 100)
    record.pop("iterations")
    record["condition"] = condition
    for field in record["backend_options"]:
        if field["name"] == "loss_function":
            field.update(type=f"typeof({control.OBJECTIVE})", value=control.OBJECTIVE)
        elif field["name"] == "nested_constraints" and condition == "no_nested_trig":
            field.update(NESTING)
    return record


def test_frozen_order_budget_and_plan_binding():
    cells = control.planned_cells()
    assert [(c["budget"]["seed"], c["condition"]) for c in cells] == [
        (20261020, "unrestricted"),
        (20261020, "no_nested_trig"),
        (20261021, "no_nested_trig"),
        (20261021, "unrestricted"),
        (20261022, "unrestricted"),
        (20261022, "no_nested_trig"),
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
    assert all(control.source_hashes()[p] for p in control.RUNTIME.values())


def test_exactly_one_between_arm_factor_and_no_general_default_mutation():
    budget = symbolic.SearchBudget(seed=20261020, niterations=200)
    ordinary = symbolic.search_parameters(budget)
    left, right = [control.profile_parameters(budget, c) for c in control.CONDITIONS]
    assert {k for k in left if left[k] != right[k]} == {"nested_constraints"}
    assert right["nested_constraints"] == {
        "sin": {"sin": 0, "cos": 0},
        "cos": {"sin": 0, "cos": 0},
    }
    assert left["nested_constraints"] is None
    assert right["optimizer_iterations"] == 100
    assert right["optimizer_nrestarts"] == 2
    assert right["guesses"] is None and right["warm_start"] is False
    assert right["use_frequency"] and right["use_frequency_in_tournament"]
    right["nested_constraints"]["sin"]["sin"] = 5
    assert (
        control.profile_parameters(budget, "no_nested_trig")["nested_constraints"][
            "sin"
        ]["sin"]
        == 0
    )
    assert symbolic.search_parameters(budget) == ordinary


@pytest.mark.parametrize(
    "document",
    [
        {},
        {"format": control.PROFILE_FORMAT, "condition": True},
        {"format": control.PROFILE_FORMAT, "condition": "other"},
        {
            "format": control.PROFILE_FORMAT,
            "condition": "no_nested_trig",
            "guesses": ["truth"],
        },
        {
            "format": control.PROFILE_FORMAT,
            "condition": "unrestricted",
            "optimizer_iterations": 200,
        },
    ],
)
def test_profile_rejects_overrides(document):
    with pytest.raises(ValueError):
        control.checked_profile(document)


@pytest.mark.parametrize("seed", control.SEEDS)
@pytest.mark.parametrize("condition", control.CONDITIONS)
def test_absolute_options_and_complete_common_optimizer_policy(seed, condition):
    record = option_fixture(seed, condition)
    original = copy.deepcopy(record)
    assert (
        control.verify_options(record, seed, condition, OLD, OLD.load_support())[
            "status"
        ]
        == "passed"
    )
    assert record == original
    common = control.common_options(record, OLD.load_support())
    assert "optimizer_options" in common["fields"] and "plugins" in common["fields"]
    assert common["optimizer_settings"]["iterations"] == "100"


@pytest.mark.parametrize(
    "value",
    [
        "nothing",
        "[]",
        "[(1, 2, [(1, 2, 0), (1, 3, 0)])]",
        NESTING["value"].replace("(1, 3, 0)", "(1, 3, 1)", 1),
        NESTING["value"].replace("(1, 2, 0)", "(1, 2, -1)", 1),
        NESTING["value"].replace("(1, 2, 0)", "(1, 1, 0)", 1),
        NESTING["value"].replace("(1, 2, 0)", "(1, 2, False)", 1),
        NESTING["value"].replace("(1, 3, 0)", "(1, 2, 0)", 1),
        "__import__('os').getcwd()",
    ],
)
def test_partial_weakened_extra_or_executable_native_rules_fail(value):
    with pytest.raises(ValueError):
        control.verify_nesting_field({**NESTING, "value": value}, "no_nested_trig")


def node(operator, *children):
    return {"kind": "operator", "operator": operator, "children": list(children)}


@pytest.mark.parametrize("outer", ["sin", "cos"])
@pytest.mark.parametrize("inner", ["sin", "cos"])
@pytest.mark.parametrize("distant", [False, True])
def test_all_direct_and_distant_trig_pairs_fail_only_in_intervention(
    outer, inner, distant
):
    inside = node(inner, constant(0.2))
    if distant:
        inside = node("+", constant(0.1), node("*", constant(2.0), inside))
    tree = node(outer, inside)
    control.verify_tree_grammar(tree, "unrestricted")
    with pytest.raises(ValueError, match="descendant"):
        control.verify_tree_grammar(tree, "no_nested_trig")


def test_target_and_unrelated_forms_remain_allowed():
    for tree in (
        reference_tree(),
        node("exp", node("cos", constant(1))),
        node("cos", node("exp", constant(1))),
        node("*", node("sin", constant(1)), node("cos", constant(2))),
    ):
        control.verify_tree_grammar(tree, "no_nested_trig")


def complete_cells(low, high):
    arrays = frozen_data()
    cells = control.planned_cells()
    for cell in cells:
        index = control.SEEDS.index(cell["budget"]["seed"])
        success = (low if cell["condition"] == "unrestricted" else high)[index]
        trees = [reference_tree() if success else constant(0), reference_tree()]
        cell.update(
            status="completed",
            diagnostics={
                "selected_index": 0,
                "candidates": [
                    diagnose_candidate(
                        candidate(tree, arrays), i, 0, arrays, "complexity_frequency"
                    )
                    for i, tree in enumerate(trees)
                ],
            },
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
def test_count_comparison_requires_gain_and_same_selected_structure(
    low, high, outcome, counts
):
    cells = complete_cells(low, high)
    result = control.comparison(cells, final_verified=True)
    assert result["comparison"]["outcome"] == outcome
    assert (result["comparison"]["C_K"], result["comparison"]["C_A"]) == counts
    assert result["comparison"]["development_signal"] == (
        "supported_structure_gain"
        if counts[1] > counts[0]
        else "hypothesis_not_supported"
    )
    for cell in cells:
        if cell["condition"] == "no_nested_trig":
            cell["diagnostics"]["candidates"][0]["parameter_match"]["status"] = (
                "not_assessed"
            )
    result = control.comparison(cells, final_verified=True)
    assert result["comparison"]["development_signal"] == (
        "approximation_gain_only"
        if counts[1] > counts[0]
        else "hypothesis_not_supported"
    )
    assert result["summaries"]["no_nested_trig"]["supported_reconstructions"] == 0


@pytest.mark.parametrize(
    "fault", ["final", "missing", "failed", "other_tree", "replay"]
)
def test_incomplete_or_unselected_or_unreplayed_trees_cannot_lift_results(fault):
    cells = complete_cells([0, 0, 0], [0, 0, 0])
    if fault == "missing":
        cells.pop()
    elif fault == "failed":
        cells[-1]["status"] = "failed"
    elif fault == "replay":
        selected = cells[0]["diagnostics"]["candidates"][1]
        selected["physical_analysis"]["raw_replay"]["status"] = "failed"
        assert not control.supported_reconstruction(selected)
    result = control.comparison(cells, final_verified=fault != "final")
    if fault in {"final", "missing", "failed"}:
        assert all(v is None for v in result.values())
    else:
        assert result["comparison"]["C_A"] == result["comparison"]["C_K"] == 0
        assert result["summaries"]["no_nested_trig"]["unselected_curve_successes"] == 3
