"""Independent coordinate, replay, missing-value and per-seed references."""

import copy
import json
import math
from pathlib import Path

import numpy as np
import pytest
from test_structure import constant, operator, time_node

from ringdown_sr import representation_control as control
from ringdown_sr.noiseless_control import frozen_data, parameter_match
from ringdown_sr.parameters import analyze_tree
from ringdown_sr.pilot import _sha256
from ringdown_sr.symbolic import evaluate_tree


def reference(frequency=250, scale=1, amplitude=1, phase=0):
    oscillation = operator("*", constant(2 * math.pi * frequency / scale), time_node())
    if phase:
        oscillation = operator("+", oscillation, constant(phase))
    return operator(
        "*",
        constant(amplitude),
        operator(
            "*",
            operator("exp", operator("*", constant(-125 / scale), time_node())),
            operator("cos", oscillation),
        ),
    )


def candidate(tree, arrays, condition):
    coordinate = control.search_coordinates(arrays, condition)
    prediction = evaluate_tree(tree, coordinate["time_s"])
    return {
        "tree": tree,
        "complexity": 11,
        "loss": float(np.mean((arrays["observed"] - prediction) ** 2)),
        "display_equation": "fixed reference",
    }


def completed_cells():
    arrays = frozen_data()
    cells = control.planned_cells()
    for cell in cells:
        condition = cell["condition"]
        item = candidate(
            reference(scale=cell["settings"]["time_scale"]), arrays, condition
        )
        diagnosis = control.diagnose_candidate(item, 0, 0, arrays, condition)
        cell.update(
            status="completed",
            diagnostics={
                "selected_index": 0,
                "candidates": [diagnosis],
                "timing_seconds": {"fixture": 1},
                "callback_calls_during_fit": 3,
            },
        )
    return cells


def test_fixed_plan_membership_order_budget_and_hash():
    cells = control.planned_cells()
    assert [(cell["budget"]["seed"], cell["condition"]) for cell in cells] == [
        (20261020, "baseline"),
        (20261020, "time_stretch"),
        (20261020, "complexity_frequency"),
        (20261021, "time_stretch"),
        (20261021, "complexity_frequency"),
        (20261021, "baseline"),
        (20261022, "complexity_frequency"),
        (20261022, "baseline"),
        (20261022, "time_stretch"),
    ]
    assert all(cell["budget"]["niterations"] == 200 for cell in cells)
    assert all(
        cell["budget"]["populations"] == 2
        and cell["budget"]["population_size"] == 32
        and cell["budget"]["ncycles_per_iteration"] == 50
        for cell in cells
    )
    plan = Path(__file__).resolve().parents[1] / "docs/search_representation_plan.md"
    assert _sha256(plan.read_bytes()) == control.PLAN_SHA256


def test_coordinate_stretch_uses_window_and_preserves_observation_bits():
    arrays = frozen_data()
    original = {key: value.copy() for key, value in arrays.items()}
    mapped = control.search_coordinates(arrays, "time_stretch")
    np.testing.assert_array_equal(mapped["time_s"], np.arange(128) / 128)
    np.testing.assert_array_equal(
        mapped["diagnostic_time_s"],
        np.array([(j + k / 8) / 128 for j in range(127) for k in range(1, 8)]),
    )
    np.testing.assert_array_equal(
        mapped["observed"].view(np.uint64), arrays["observed"].view(np.uint64)
    )
    assert all(not value.flags.writeable for value in mapped.values())
    for key, value in original.items():
        np.testing.assert_array_equal(arrays[key], value)
    assert control.condition_settings("complexity_frequency")["use_frequency"] is True
    assert control.condition_settings("time_stretch")["use_frequency"] is False
    with pytest.raises(ValueError):
        control.condition_settings("combined")


@pytest.mark.parametrize("condition", control.CONDITIONS)
@pytest.mark.parametrize(
    "frequency,within", [(250, True), (4346, False), (33018, True)]
)
def test_coordinate_alias_references_preserve_full_tree_and_physical_parameters(
    condition, frequency, within
):
    arrays = frozen_data()
    scale = control.condition_settings(condition)["time_scale"]
    tree = reference(frequency, scale)
    item = candidate(tree, arrays, condition)
    before = copy.deepcopy(item)
    result = control.diagnose_candidate(item, 0, 0, arrays, condition)
    assert item == before
    assert (result["curve_marker"] == "within_tolerance") is within
    assert result["physical_identification"] == "not_assessed"
    assert result["parameter_match"]["status"] == "matched"
    physical = result["physical_analysis"]
    assert physical["alias"]["frequency_alias_hz"]["value"] == pytest.approx(250)
    assert physical["raw_parameters"]["decay_time_s"]["value"] == pytest.approx(0.008)
    assert (
        physical["raw_replay"]["status"]
        == physical["alias_replay"]["status"]
        == "passed"
    )
    assert result["search_analysis"]["raw_parameters"]["decay_time_s"][
        "value"
    ] == pytest.approx(scale * 0.008)
    np.testing.assert_array_equal(
        evaluate_tree(reference(frequency), arrays["time_s"]),
        evaluate_tree(tree, scale * arrays["time_s"]),
    )


def test_negative_amplitude_phase_equivalence_survives_physical_conversion():
    arrays = frozen_data()
    tree = reference(scale=32, amplitude=-1, phase=math.pi)
    result = control.diagnose_candidate(
        candidate(tree, arrays, "time_stretch"), 0, 0, arrays, "time_stretch"
    )
    assert result["curve_marker"] == "within_tolerance"
    assert result["parameter_match"]["status"] == "matched"


def test_unsupported_constant_remains_unassessed():
    arrays = frozen_data()
    result = control.diagnose_candidate(
        candidate(constant(0), arrays, "time_stretch"), 0, 0, arrays, "time_stretch"
    )
    assert result["search_analysis"]["structure"]["structure_status"] == "not_supported"
    assert result["parameter_match"]["status"] == "not_assessed"


def test_eighth_grid_blindspot_still_differs_at_an_off_grid_physical_time():
    times = np.array([1 / (16 * 4096)])
    original = evaluate_tree(reference(), times)
    blind = evaluate_tree(reference(frequency=33018, scale=32), 32 * times)
    np.testing.assert_allclose(blind, -original, atol=1e-14, rtol=1e-12)


def test_a_good_unsupported_curve_is_kept_separate_from_parameter_status():
    arrays = frozen_data()
    tree = operator(
        "*",
        operator("exp", operator("*", constant(-125 / 32), time_node())),
        operator(
            "sin",
            operator(
                "+",
                operator("*", constant(2 * math.pi * 250 / 32), time_node()),
                constant(math.pi / 2),
            ),
        ),
    )
    result = control.diagnose_candidate(
        candidate(tree, arrays, "time_stretch"), 0, 0, arrays, "time_stretch"
    )
    assert result["curve_marker"] == "within_tolerance"
    assert result["parameter_match"]["status"] == "not_assessed"


@pytest.mark.parametrize("gate", ["raw_replay", "alias_replay"])
def test_failed_search_replay_cannot_be_repaired_by_coordinate_conversion(gate):
    arrays = frozen_data()
    tree = reference(scale=32)
    source = analyze_tree(tree, 32 * arrays["time_s"], sample_rate_hz=128)
    source[gate] = {"status": "failed", "reason": "injected mismatch"}
    before = copy.deepcopy(source)
    physical = control.physical_analysis(source, tree, arrays["time_s"], 32)
    assert parameter_match(physical)["status"] == "not_assessed"
    assert source == before


@pytest.mark.parametrize("fault", ["unavailable", "overflow", "subnormal"])
def test_unavailable_or_out_of_range_conversion_blocks_positive_replay(fault):
    arrays = frozen_data()
    tree = reference(scale=32)
    source = analyze_tree(tree, 32 * arrays["time_s"], sample_rate_hz=128)
    field = source["raw_parameters"]["angular_frequency_per_s"]
    if fault == "unavailable":
        field.update(status="numerical_unresolved", value=None, reason="fixture")
    else:
        field["value"] = (
            np.finfo(float).max
            if fault == "overflow"
            else float.fromhex("0x0.0000000000001p-1022")
        )
    physical = control.physical_analysis(source, tree, arrays["time_s"], 32)
    assert physical["raw_parameters"]["angular_frequency_per_s"]["value"] is None
    assert physical["raw_replay"]["status"] != "passed"
    assert parameter_match(physical)["status"] == "not_assessed"


def test_seed_differences_have_signed_values_and_preserve_missing_errors():
    cells = completed_cells()
    cells[0]["diagnostics"]["candidates"][0]["training_loss"] = 0.3
    cells[1]["diagnostics"]["candidates"][0]["training_loss"] = 0.1
    cells[1]["diagnostics"]["candidates"][0]["parameter_match"]["errors"][
        "frequency"
    ] = None
    before = copy.deepcopy(cells)
    result = control.seed_differences(cells)
    pair = result[0]
    assert pair["seed"] == 20261020 and pair["condition"] == "time_stretch"
    assert pair["metrics"]["training_mse"]["difference"] == pytest.approx(-0.2)
    assert pair["metrics"]["training_mse"]["baseline"] == 0.3
    assert pair["baseline_cell"] == 1 and pair["variant_cell"] == 2
    assert pair["baseline_markers"]["parameters"] == "matched"
    assert pair["metrics"]["parameter/frequency"]["difference"] is None
    assert pair["metrics"]["parameter/frequency"]["status"] == "not_assessed"
    assert cells == before
    json.dumps(result, allow_nan=False)


def test_missing_pairs_and_final_verification_failure_suppress_differences():
    cells = completed_cells()
    cells[0]["status"] = "planned"
    assert all(
        item["status"] == "not_assessed" for item in control.seed_differences(cells)[:2]
    )
    assert all(
        item["metrics"] is None
        for item in control.seed_differences(cells, final_verified=False)
    )
    assert all(
        item["statistics"] is None
        for item in control.condition_summaries(cells, final_verified=False).values()
    )
    with pytest.raises(ValueError, match="Duplicate"):
        control.seed_differences([*cells, cells[0]])


def test_summaries_keep_finite_denominators_and_large_finite_median():
    cells = completed_cells()
    baseline = [cell for cell in cells if cell["condition"] == "baseline"]
    for index, cell in enumerate(baseline):
        cell["diagnostics"]["candidates"][0]["curve_errors"]["diagnostic"][
            "relative_rms"
        ] = None if index == 2 else 1.6e308
    summary = control.condition_summaries(cells)["baseline"]
    values = summary["statistics"]["diagnostic/relative_rms"]
    assert values["finite_count"] == 2 and values["planned_count"] == 3
    assert values["median"] == 1.6e308
    json.dumps(summary, allow_nan=False)


def test_finite_but_unresolved_metrics_keep_source_status_and_block_differences():
    cells = completed_cells()
    selected = cells[1]["diagnostics"]["candidates"][0]
    selected["parameter_match"].update(
        status="not_assessed", reason="raw_replay_not_passed"
    )
    selected["curve_errors"]["diagnostic"].update(
        status="numerical_unresolved", reason="fixture_range"
    )
    result = control.seed_differences(cells)[0]
    for name in ("parameter/frequency", "diagnostic/relative_rms"):
        metric = result["metrics"][name]
        assert metric["baseline"] is not None and metric["variant"] is not None
        assert metric["baseline_availability"]["status"] == "available"
        assert metric["variant_availability"]["status"] == "not_assessed"
        assert metric["difference"] is None
    summary = control.condition_summaries(cells)["time_stretch"]
    assert summary["statistics"]["parameter/frequency"]["finite_count"] == 2
    assert summary["statistics"]["diagnostic/relative_rms"]["finite_count"] == 2
