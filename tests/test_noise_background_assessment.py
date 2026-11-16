"""Check the prospective grid endpoint, paired uncertainty and fixed inventory."""

import copy
import json
import math

import mpmath as mp
import pytest
from test_noise_pilot_assessment import core, identity, inputs, package
from test_structure_proof import T, op, q

from ringdown_sr import noise_background_assessment as assessment
from ringdown_sr import noise_pilot_assessment as pilot


def assess(*, arm="estimated_1024", tree=None, status="success", arrays=None):
    arrays = inputs() if arrays is None else arrays
    return assessment.assess_package(
        package(arrays, tree=tree, status=status),
        None if status == "not_run" else arrays,
        amplitude=1.0,
        source_identity=identity(status, arm=arm),
    )


def records():
    template = assess()
    result = []
    offsets = {
        "ordinary": 0.0,
        "known_covariance": 0.02,
        "estimated_64": 0.03,
        "estimated_256": 0.01,
        "estimated_1024": -0.01,
    }
    for model, planned in assessment.PLANNED_BLOCKS.items():
        for block in range(1, planned + 1):
            for arm in assessment.ARMS:
                current = copy.deepcopy(template)
                current["source_identity"] = identity(model=model, block=block, arm=arm)
                current["background_training_windows"] = assessment.training_windows(
                    arm
                )
                current["primary"]["value"] = 0.5 + offsets[arm] * block
                result.append(current)
    return result


def replace_failure(
    values, *, model="ar1", block=1, arm="estimated_256", status="not_run"
):
    failed = assess(arm=arm, status=status)
    failed["source_identity"] = identity(status, model=model, block=block, arm=arm)
    index = next(
        i
        for i, record in enumerate(values)
        if all(
            record["source_identity"][key] == expected
            for key, expected in (("model", model), ("block", block), ("arm", arm))
        )
    )
    values[index] = failed


@pytest.mark.parametrize("arm", assessment.ARMS)
def test_primary_is_new_grid_without_mutating_selection_historical_diagnostics_or_globals(
    arm,
):
    data = inputs()
    original = package(data, tree=op("+", core(), q(0.125)))
    original["selected_candidate"]["prediction"] = data["signal"].tolist()
    before = copy.deepcopy(original)
    old_constants = pilot.FORMAT, pilot.ARMS, pilot.CONTRASTS
    selected_identity = identity(arm=arm)
    record = assessment.assess_package(
        original, data, amplitude=2.0, source_identity=selected_identity
    )
    assert record["primary"]["value"] == pytest.approx(0.0625)
    assert record["amplitude_errors"]["training"]["rms_over_amplitude"] == 0.0
    assert record["format"] == assessment.FORMAT != pilot.FORMAT
    assert record["primary_endpoint"] == assessment.PRIMARY_ENDPOINT
    assert record["source_identity"] == selected_identity
    assert record["background_training_windows"] == assessment.training_windows(arm)
    assert record["original_candidate"] == before["selected_candidate"]
    assert original == before
    assert (pilot.FORMAT, pilot.ARMS, pilot.CONTRASTS) == old_constants
    assert record["supplemental"]["new_parameter_match"] == {"status": "not_assessed"}
    json.dumps(record, allow_nan=False)


def test_continuous_family_failure_does_not_filter_a_finite_grid_endpoint():
    data = inputs()
    hole = float(data["diagnostic_time_s"][0])
    record = assess(arrays=data, tree=op("/", q(1), op("-", T, q(hole))))
    assert record["primary"]["status"] == "available"
    assert record["primary"]["value"] > 0
    assert record["supplemental"]["original_family"]["status"] == "proven_nonmember"
    assert record["supplemental"]["curve"]["status"] == "not_assessable"


def test_nonfinite_grid_prediction_has_no_invented_error_and_preserves_native_training():
    data = inputs()
    hole = float(data["irregular_time_s"][0])
    record = assess(arrays=data, tree=op("/", q(1), op("-", T, q(hole))))
    assert record["primary"]["value"] is None
    assert record["primary"]["reason"]
    assert record["amplitude_errors"]["training"]["rms_over_amplitude"] is not None
    assert record["status"] == "success"
    json.dumps(record, allow_nan=False)


@pytest.mark.parametrize("status", ["failed", "not_run"])
def test_unavailable_package_retains_costs_denominator_and_exact_source_identity(
    status,
):
    record = assess(status=status)
    assert record["planned_members"] == 4
    assert record["search_calls"] == (0 if status == "not_run" else 4)
    assert record["original_candidate"] is None
    assert record["primary"]["value"] is None
    assert record["costs"]["fit_wall_seconds"] is None
    assert record["source_identity"] == identity(status, arm="estimated_1024")


def test_exact_inventory_model_denominators_and_independent_paired_student_t_intervals():
    result = assessment.summary(records())
    assert result["planned_packages"] == 130
    assert result["planned_search_calls"] == 520
    assert result["planned_blocks_per_model"] == {"ar1": 20, "white": 6}
    assert result["primary_contrast"] == "estimated_1024_minus_ordinary"
    assert result["secondary_contrast"] == "estimated_1024_minus_estimated_64"
    assert result["primary_model"] == "ar1"
    assert result["pooled"] is result["automatic_arm_selection"] is False
    for model, n in assessment.PLANNED_BLOCKS.items():
        group = result["models"][model]
        assert len(group["contrasts"]) == 8
        assert all(arm["failure_denominator"] == n for arm in group["arms"].values())
        assert all(
            arm["planned_search_calls"] == 4 * n for arm in group["arms"].values()
        )
        stats = group["contrasts"][assessment.PRIMARY_CONTRAST]
        values = [-block / 100 for block in range(1, n + 1)]
        mean = sum(values) / n
        deviation = math.sqrt(sum((value - mean) ** 2 for value in values) / (n - 1))
        mcse = deviation / math.sqrt(n)
        # Independent high-precision inverse Student-t CDF via incomplete beta.
        with mp.workdps(50):
            degrees = mp.mpf(n - 1)
            cdf = lambda x, degrees=degrees: (
                1
                - mp.betainc(
                    degrees / 2,
                    mp.mpf("0.5"),
                    0,
                    degrees / (degrees + x * x),
                    regularized=True,
                )
                / 2
            )
            critical = float(
                mp.findroot(lambda x, cdf=cdf: cdf(x) - mp.mpf("0.975"), (2, 3))
            )
        interval = stats["interval_95"]
        assert stats["mean"] == pytest.approx(mean)
        assert stats["sample_sd"] == pytest.approx(deviation)
        assert stats["mcse"] == pytest.approx(mcse)
        assert [entry["value"] for entry in stats["values"]] == pytest.approx(values)
        assert interval["critical_value"] == pytest.approx(critical, rel=1e-11)
        assert interval["lower"] == pytest.approx(mean - critical * mcse)
        assert interval["upper"] == pytest.approx(mean + critical * mcse)
        assert interval["status"] == "available"
        assert interval["simultaneous"] is interval["decision_rule"] is False
    json.dumps(result, allow_nan=False)


def test_third_arm_failure_does_not_remove_primary_pair_or_count_as_zero():
    values = records()
    replace_failure(values)
    model = assessment.summary(values)["models"]["ar1"]
    primary = model["contrasts"][assessment.PRIMARY_CONTRAST]
    assert (
        primary["available"] == 20 and primary["interval_95"]["status"] == "available"
    )
    incomplete = model["contrasts"]["estimated_256_minus_ordinary"]
    assert incomplete["available"] == 19 and incomplete["planned"] == 20
    assert incomplete["mcse"] is None and incomplete["interval_95"]["lower"] is None
    assert incomplete["values"][0]["value"] is None
    arm = model["arms"]["estimated_256"]
    assert arm["failed_or_not_run"] == 1 and arm["failure_denominator"] == 20
    assert arm["search_calls"] == 76 and arm["planned_search_calls"] == 80


def test_white_missing_primary_pair_preserves_independent_ar1_uncertainty():
    values = records()
    replace_failure(values, model="white", arm="ordinary", status="failed")
    summary = assessment.summary(values)
    assert (
        summary["models"]["white"]["contrasts"][assessment.PRIMARY_CONTRAST]["mcse"]
        is None
    )
    assert (
        summary["models"]["ar1"]["contrasts"][assessment.PRIMARY_CONTRAST]["mcse"]
        is not None
    )


def test_all_failed_outputs_keep_planned_denominators_and_unavailable_uncertainty():
    values = records()
    for model, planned in assessment.PLANNED_BLOCKS.items():
        for block in range(1, planned + 1):
            for arm in assessment.ARMS:
                replace_failure(
                    values, model=model, block=block, arm=arm, status="failed"
                )
    result = assessment.summary(values)
    for model, planned in assessment.PLANNED_BLOCKS.items():
        for arm in result["models"][model]["arms"].values():
            assert arm["failure_denominator"] == planned
            assert arm["failure_fraction"] == 1
            assert arm["primary"]["mean"] is None
        for contrast in result["models"][model]["contrasts"].values():
            assert contrast["available"] == 0
            assert contrast["mcse"] is contrast["interval_95"]["lower"] is None


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "extra_white_block",
        "wrong_arm",
        "wrong_size",
        "legacy_format",
        "nonfinite",
        "negative",
        "false_available",
        "wrong_calls",
        "wrong_primary",
    ],
)
def test_invalid_inventory_and_endpoint_claims_are_rejected(change):
    values = records()
    if change == "missing":
        values.pop()
    elif change == "duplicate":
        values.append(copy.deepcopy(values[0]))
    elif change == "extra_white_block":
        values[-1]["source_identity"]["block"] = 7
    elif change == "wrong_arm":
        values[0]["source_identity"]["arm"] = "estimated_covariance"
    elif change == "wrong_size":
        values[0]["background_training_windows"] = 64
    elif change == "legacy_format":
        values[0]["format"] = pilot.FORMAT
    elif change == "nonfinite":
        values[0]["primary"]["value"] = float("inf")
    elif change == "negative":
        values[0]["primary"]["value"] = -1
    elif change == "false_available":
        values[0]["primary"]["status"] = "not_available"
    elif change == "wrong_calls":
        values[0]["search_calls"] = True
    else:
        values[0]["primary_endpoint"] = "training"
    with pytest.raises(ValueError):
        assessment.summary(values)


def test_large_finite_statistics_never_emit_infinity_or_drop_extreme_blocks():
    values = records()
    for record in values:
        record["primary"]["value"] = (
            1e308 if record["source_identity"]["arm"] == "estimated_1024" else 0.0
        )
    summary = assessment.summary(values)
    primary = summary["models"]["ar1"]["contrasts"][assessment.PRIMARY_CONTRAST]
    assert primary["available"] == 20 and primary["mean"] == 1e308
    assert primary["interval_95"]["lower"] == 1e308
    json.dumps(summary, allow_nan=False)


def test_out_of_range_interval_stays_explicit_without_losing_finite_differences():
    values = records()
    for record in values:
        block = record["source_identity"]["block"]
        arm = record["source_identity"]["arm"]
        record["primary"]["value"] = (
            1.7e308 if arm == "estimated_1024" and block != 1 else 0.0
        )
    summary = assessment.summary(values)
    primary = summary["models"]["white"]["contrasts"][assessment.PRIMARY_CONTRAST]
    assert primary["available"] == 6
    assert primary["interval_95"]["status"] == "not_available"
    assert primary["interval_95"]["reason"] == "interval_out_of_range"
    json.dumps(summary, allow_nan=False)
