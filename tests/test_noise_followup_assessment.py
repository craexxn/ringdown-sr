"""Check paired follow-up endpoints and shared-control accounting analytically."""

import copy
import json
import math

import numpy as np
import pytest
from test_structure_proof import T, op, q

from ringdown_sr import noise_followup_assessment as assessment


def arrays(*, jitter=False):
    times = np.linspace(0, 1, 9)
    if jitter:
        times[1:-1] += np.array([0.01, -0.02, 0.015, -0.01, 0.02, -0.015, 0.01])
    return {
        "time_s": times,
        "signal": np.zeros(9),
        "observed": np.zeros(9),
        "covariance_true": np.eye(9) * 4,
        "diagnostic_time_s": np.linspace(0.05, 0.95, 8),
        "diagnostic_truth": np.zeros(8),
        "irregular_time_s": np.array([0.03, 0.17, 0.28, 0.49, 0.61, 0.83, 0.97]),
        "irregular_truth": np.zeros(7),
    }


def identity(condition="estimated_4096s", *, model="ar1", block=1, status="success"):
    return {
        "model": model,
        "block": block,
        "condition": condition,
        "grid": "jitter" if condition.startswith("jitter_") else "uniform",
        "package_sha256": None if status == "not_run" else "1" * 64,
        "input_sha256": "2" * 64,
        "selected_member_path": f"symbolic/{condition}/member-01/result.json"
        if status == "success"
        else None,
    }


def package(data, *, status="success", tree=None, native=None):
    return {
        "package_status": status,
        "search_calls": 0 if status == "not_run" else 4,
        "costs": {
            "worker_wall_seconds": 10.0 if status == "success" else None,
            "fit_wall_seconds": 8.0 if status == "success" else None,
            "callback_calls_during_fit": 100 if status == "success" else None,
        },
        "selected_candidate": {
            "tree": q(0.125) if tree is None else tree,
            "prediction": (
                np.full_like(data["time_s"], 0.5) if native is None else native
            ).tolist(),
            "display_equation": "0.12500000000000000",
            "complexity": 1,
            "loss": 0.25,
        }
        if status == "success"
        else None,
    }


def assess(condition="estimated_4096s", *, status="success", tree=None):
    data = arrays(jitter=condition.startswith("jitter_"))
    return assessment.assess_package(
        package(data, status=status, tree=tree),
        None if status == "not_run" else data,
        amplitude=2.0,
        source_identity=identity(condition, status=status),
    )


def records(block="all"):
    template = assess()
    offsets = {
        "ordinary": 0.0,
        "known_covariance": -0.001,
        "estimated_64s": 0.004,
        "estimated_4096s": 0.002,
        "jitter_ordinary": -0.002,
        "jitter_known_covariance": -0.003,
    }
    result = []
    for model, count in assessment.PLANNED_BLOCKS.items():
        for index in range(1, count + 1):
            for condition in assessment.conditions(block):
                record = copy.deepcopy(template)
                record["source_identity"] = identity(
                    condition, model=model, block=index
                )
                record["background_duration_seconds"] = {
                    "estimated_64s": 64,
                    "estimated_4096s": 4096,
                }.get(condition)
                record["primary"]["value"] = 0.2 + offsets[condition] * index
                result.append(record)
    return result


@pytest.mark.parametrize("condition", assessment.ARMS)
def test_original_selection_native_training_and_grid_specific_bindings_are_retained(
    condition,
):
    data = arrays(jitter=condition.startswith("jitter_"))
    original = package(data)
    before = copy.deepcopy(original)
    selected_identity = identity(condition)
    record = assessment.assess_package(
        original, data, amplitude=-2.0, source_identity=selected_identity
    )
    assert record["primary"]["value"] == 0.0625
    assert record["amplitude_errors"]["training"]["rms_over_amplitude"] == 0.25
    assert record["amplitude_errors"]["training"]["max_over_amplitude"] == 0.25
    assert record["diagnostics"]["ordinary_mse"]["value"] == 0.25
    assert record["diagnostics"]["q_true_per_sample"]["value"] == 0.0625
    assert record["source_identity"] == selected_identity
    assert record["original_candidate"] == before["selected_candidate"]
    assert (
        record["prediction_evaluation"]["training"]
        == "verified_native_selected_prediction"
    )
    assert record["reference_binding"]["training"]["time_s"]
    assert all(
        value == {"status": "not_assessed"} for value in record["supplemental"].values()
    )
    assert original == before
    assert record["amplitude"] == 2.0
    json.dumps(record, allow_nan=False)


def test_nonfinite_heldout_prediction_retains_native_training_and_no_partial_rmse():
    hole = arrays()["irregular_time_s"][3]
    record = assess(tree=op("/", q(1), op("-", T, q(float(hole)))))
    assert record["status"] == "success"
    assert record["primary"]["status"] == "not_available"
    assert record["primary"]["value"] is None
    assert record["primary"]["reason"] == "nonfinite_original_tree_prediction"
    assert record["amplitude_errors"]["training"]["rms_over_amplitude"] == 0.25
    assert record["amplitude_errors"]["diagnostic"]["rms_over_amplitude"] is not None
    json.dumps(record, allow_nan=False)


@pytest.mark.parametrize("status", ("failed", "not_run"))
def test_unavailable_packages_preserve_calls_unknown_costs_and_reason(status):
    record = assess(status=status)
    assert record["planned_members"] == 4
    assert record["search_calls"] == (0 if status == "not_run" else 4)
    assert record["primary"] == {
        "status": "not_available",
        "reason": "package_" + status,
        "value": None,
    }
    assert record["original_candidate"] is None
    assert record["costs"]["worker_wall_seconds"] is None


@pytest.mark.parametrize(
    ("block", "packages", "new_packages", "referenced", "calls"),
    (
        ("duration", 104, 104, 0, 416),
        ("sampling", 104, 52, 52, 208),
        ("all", 156, 156, 0, 624),
    ),
)
def test_exact_block_inventory_and_no_double_counting_of_shared_controls(
    block, packages, new_packages, referenced, calls
):
    result = assessment.summary(records(block), block=block)
    assert result["planned_packages"] == packages
    assert result["planned_new_packages"] == new_packages
    assert result["referenced_packages"] == referenced
    assert result["planned_new_search_calls"] == result["new_search_calls"] == calls
    assert (
        result["planned_reference_search_calls"]
        == result["referenced_search_calls"]
        == 4 * referenced
    )
    assert (
        result["new_package_costs"]["worker_wall_seconds"]["total"] == 10 * new_packages
    )
    if referenced:
        assert (
            result["referenced_package_costs"]["worker_wall_seconds"]["total"]
            == 10 * referenced
        )
        assert (
            result["models"]["ar1"]["conditions"]["ordinary"]["new_search_calls"] == 0
        )
        assert (
            result["models"]["ar1"]["conditions"]["ordinary"]["referenced_search_calls"]
            == 80
        )
    else:
        assert result["referenced_package_costs"] == {}
    assert result["pooled"] is result["automatic_arm_selection"] is False
    assert result["shared_controls_independent_between_blocks"] is False
    assert (
        len(result["models"]["ar1"]["contrasts"])
        == {
            "duration": 6,
            "sampling": 4,
            "all": 9,
        }[block]
    )
    json.dumps(result, allow_nan=False)


def test_paired_differences_and_marginal_student_intervals_have_independent_references():
    result = assessment.summary(records())
    critical = {20: 2.093024054408263, 6: 2.570581835636314}
    for model, count in assessment.PLANNED_BLOCKS.items():
        for name in assessment.PRIMARY_CONTRASTS.values():
            pair = result["models"][model]["contrasts"][name]
            # The fixture differences are -0.002*i; use closed-form moments.
            mean = -0.002 * (count + 1) / 2
            deviation = 0.002 * math.sqrt(count * (count + 1) / 12)
            mcse = 0.002 * math.sqrt((count + 1) / 12)
            assert pair["mean"] == pytest.approx(mean)
            assert pair["sample_sd"] == pytest.approx(deviation)
            assert pair["mcse"] == pytest.approx(mcse)
            interval = pair["interval_95"]
            assert interval["status"] == "available"
            assert interval["lower"] == pytest.approx(mean - critical[count] * mcse)
            assert interval["upper"] == pytest.approx(mean + critical[count] * mcse)
            assert interval["simultaneous"] is interval["decision_rule"] is False


def test_failed_pair_keeps_planned_denominator_and_disables_complete_case_interval():
    values = records("duration")
    index = next(
        i
        for i, value in enumerate(values)
        if value["source_identity"] == identity("estimated_4096s")
    )
    values[index] = assess(status="failed")
    result = assessment.summary(values, block="duration")
    pair = result["models"]["ar1"]["contrasts"][
        assessment.PRIMARY_CONTRASTS["duration"]
    ]
    assert pair["planned"] == 20
    assert pair["available"] == 19
    assert pair["unavailable"] == 1
    assert pair["interval_95"]["status"] == "not_available"
    assert pair["mcse"] is None
    assert pair["denominator_scope"] == "available_pairs_conditional_on_both_endpoints"
    assert result["new_package_costs"]["worker_wall_seconds"]["total"] is None
    assert result["new_package_costs"]["worker_wall_seconds"]["known_subtotal"] == 1030
    assert (
        result["models"]["ar1"]["conditions"]["estimated_4096s"]["failure_fraction"]
        == 0.05
    )


def test_duplicated_controls_cannot_inflate_all_block_sample_count():
    with pytest.raises(ValueError, match="Duplicate"):
        assessment.summary(records("duration") + records("sampling"))
    with pytest.raises(ValueError, match="inventory"):
        assessment.summary(records("duration"))
    with pytest.raises(ValueError, match="inventory"):
        assessment.summary(records("all"), block="sampling")


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("grid", "jitter"),
        ("block", True),
        ("block", 21),
        ("condition", "estimated_64"),
        ("selected_member_path", "../escape.json"),
        ("package_sha256", "abc"),
    ),
)
def test_identity_mismatches_are_integrity_errors(name, value):
    selected_identity = identity()
    selected_identity[name] = value
    with pytest.raises(ValueError):
        assessment.assess_package(
            package(arrays()),
            arrays(),
            amplitude=1.0,
            source_identity=selected_identity,
        )


@pytest.mark.parametrize("amplitude", (0, float("nan"), float("inf"), True))
def test_invalid_amplitudes_are_not_silently_assessed(amplitude):
    with pytest.raises(ValueError):
        assessment.assess_package(
            package(arrays()), arrays(), amplitude=amplitude, source_identity=identity()
        )


def test_invalid_tree_and_original_native_dimension_are_integrity_errors():
    data = arrays()
    invalid = package(data, tree={"kind": "invalid"})
    with pytest.raises(ValueError):
        assessment.assess_package(
            invalid, data, amplitude=1.0, source_identity=identity()
        )
    invalid = package(data, native=np.zeros(8))
    with pytest.raises(ValueError):
        assessment.assess_package(
            invalid, data, amplitude=1.0, source_identity=identity()
        )


@pytest.mark.parametrize("block", (None, "background", 1, True))
def test_unknown_block_is_rejected(block):
    with pytest.raises(ValueError):
        assessment.summary([], block=block)
