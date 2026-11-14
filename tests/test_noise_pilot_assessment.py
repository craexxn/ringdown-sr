"""Independent error norms, original proofs and complete paired denominators."""

import copy
import json
import math

import numpy as np
import pytest
from test_structure_proof import T, op, q

from ringdown_sr import noise_pilot_assessment as assessment
from ringdown_sr.structure import InvalidTreeError
from ringdown_sr.symbolic import evaluate_tree


def core():
    return op("*", op("exp", op("*", q(-4), T)), op("cos", op("*", q(64), T)))


def inputs():
    times = np.arange(9, dtype=np.float64) / 4096
    diagnostic = (np.arange(8, dtype=np.float64) + 0.5) / 4096
    irregular = (np.arange(7, dtype=np.float64) + 0.3) / 4096

    def truth(values):
        return np.exp(-4 * values) * np.cos(64 * values)

    signal = truth(times)
    return {
        "time_s": times,
        "signal": signal,
        "observed": signal + np.linspace(-0.05, 0.05, len(times)),
        "diagnostic_time_s": diagnostic,
        "diagnostic_truth": truth(diagnostic),
        "irregular_time_s": irregular,
        "irregular_truth": truth(irregular),
        "covariance_true": np.eye(len(times), dtype=np.float64) * 0.25,
    }


def identity(status="success", *, model="white", block=1, arm="ordinary"):
    return {
        "model": model,
        "block": block,
        "arm": arm,
        "package_sha256": "a" * 64 if status != "not_run" else None,
        "input_sha256": "b" * 64 if status != "not_run" else None,
        "selected_member_path": "ordinary/member-02/result.json"
        if status == "success"
        else None,
    }


def package(arrays, *, tree=None, status="success"):
    tree = core() if tree is None else tree
    selected = (
        None
        if status != "success"
        else {
            "tree": tree,
            "prediction": evaluate_tree(tree, arrays["time_s"]).tolist(),
            "loss": 0.125,
            "complexity": 9,
            "display_equation": "unaltered native export",
        }
    )
    return {
        "package_status": status,
        "selected_candidate": selected,
        "costs": {
            "fit_wall_seconds": None if status != "success" else 3.0,
            "callback_calls_during_fit": None if status != "success" else 123,
        },
        "search_calls": 0 if status == "not_run" else 4,
    }


def assess(arrays=None, *, tree=None, status="success"):
    arrays = inputs() if arrays is None else arrays
    return assessment.assess_package(
        package(arrays, tree=tree, status=status),
        arrays,
        amplitude=1.0,
        source_identity=identity(status),
    )


def test_original_family_and_three_grids_keep_clean_truth_separate_from_observed():
    arrays = inputs()
    report = package(arrays)
    before = copy.deepcopy(report)
    record = assessment.assess_package(
        report, arrays, amplitude=1.0, source_identity=identity()
    )
    assert report == before
    assert record["original_candidate"] == report["selected_candidate"]
    assert record["primary"]["value"] == 0.0
    assert record["diagnostics"]["ordinary_mse"]["value"] == pytest.approx(
        np.mean((arrays["observed"] - arrays["signal"]) ** 2)
    )
    assert record["diagnostics"]["q_true_per_sample"]["value"] == pytest.approx(
        4 * record["diagnostics"]["ordinary_mse"]["value"]
    )
    assert record["supplemental"]["curve"]["grade"] == "A"
    assert record["supplemental"]["original_family"]["status"] == "proven_member"
    assert record["supplemental"]["domain"]["status"] == "defined_everywhere"
    assert record["supplemental"]["new_parameter_match"] == {"status": "not_assessed"}
    assert record["supplemental"]["remainder"]["status"] == "bound_proven"
    assert set(record["supplemental"]["remainder"]["reference_binding"]) == {
        "training",
        "diagnostic",
    }
    assert all(
        record["amplitude_errors"][r]["rms_over_amplitude"] == 0.0
        for r in assessment.ROLES
    )
    record["original_candidate"]["tree"]["children"][0] = q(1)
    assert report == before
    json.dumps(record, allow_nan=False)


def test_primary_amplitude_norm_is_not_the_historical_r1_truth_norm():
    arrays = inputs()
    record = assessment.assess_package(
        package(arrays, tree=q(0)), arrays, amplitude=2.0, source_identity=identity()
    )
    expected = (
        math.sqrt(sum(float(y) ** 2 for y in arrays["signal"]) / len(arrays["signal"]))
        / 2
    )
    assert record["primary"]["value"] == pytest.approx(expected)
    assert record["curve_errors"]["training"]["relative_rms"] == 1.0
    assert record["curve_errors"]["training"]["relative_max"] == 1.0
    assert record["supplemental"]["curve"]["grade"] == "D"


def test_verified_native_prediction_controls_training_only_without_reselection():
    arrays = inputs()
    report = package(arrays)
    report["selected_candidate"]["prediction"] = (arrays["signal"] + 0.125).tolist()
    report["unselected_truth_candidate"] = package(arrays)["selected_candidate"]
    record = assessment.assess_package(
        report, arrays, amplitude=1.0, source_identity=identity()
    )
    assert record["primary"]["value"] == pytest.approx(0.125)
    assert record["original_candidate"] == report["selected_candidate"]
    assert record["amplitude_errors"]["diagnostic"]["rms_over_amplitude"] == 0.0
    assert record["amplitude_errors"]["irregular"]["rms_over_amplitude"] == 0.0


def test_original_domain_hole_is_preserved_and_unavailable_grid_is_not_grade_d():
    arrays = inputs()
    hole = float(arrays["diagnostic_time_s"][0])
    tree = op("/", q(1), op("-", T, q(hole)))
    record = assess(arrays, tree=tree)
    assert record["status"] == "success"
    assert record["primary"]["status"] == "available"
    assert record["amplitude_errors"]["diagnostic"]["status"] == "not_available"
    assert record["supplemental"]["curve"]["status"] == "not_assessable"
    assert record["supplemental"]["domain"]["exclusions"]
    assert record["supplemental"]["original_family"]["status"] == "proven_nonmember"


def test_invalid_tree_and_unknown_evaluation_error_are_not_numerical_failures(
    monkeypatch,
):
    arrays = inputs()
    report = package(arrays)
    report["selected_candidate"]["tree"] = {"kind": "variable", "index": True}
    with pytest.raises(InvalidTreeError):
        assessment.assess_package(
            report, arrays, amplitude=1.0, source_identity=identity()
        )

    def broken(*args):
        raise ValueError("source integrity changed")

    monkeypatch.setattr(assessment, "evaluate_tree", broken)
    with pytest.raises(ValueError, match="source integrity changed"):
        assess(arrays)


@pytest.mark.parametrize("status", ["failed", "not_run"])
def test_failed_and_not_run_outputs_keep_unknown_costs_and_no_invented_prediction(
    status,
):
    arrays = inputs()
    report = package(arrays, status=status)
    record = assessment.assess_package(
        report,
        None if status == "not_run" else arrays,
        amplitude=1.0,
        source_identity=identity(status),
    )
    assert record["status"] == status
    assert record["primary"]["value"] is None
    assert record["original_candidate"] is None
    assert record["planned_members"] == 4
    assert record["costs"]["fit_wall_seconds"] is None
    assert record["supplemental"]["new_parameter_match"] == {"status": "not_assessed"}
    assert record["supplemental"]["curve"]["grade"] is None
    assert record["search_calls"] == (0 if status == "not_run" else 4)
    json.dumps(record, allow_nan=False)


@pytest.mark.parametrize(
    "change", ["covariance", "truth_shape", "float32", "nonfinite", "outside_interval"]
)
def test_invalid_bound_inputs_are_integrity_errors(change):
    arrays = inputs()
    report = package(arrays)
    if change == "covariance":
        arrays["covariance_true"][0, 0] = -1
    elif change == "truth_shape":
        arrays["signal"] = arrays["signal"][:-1]
    elif change == "float32":
        arrays["diagnostic_truth"] = arrays["diagnostic_truth"].astype(np.float32)
    elif change == "nonfinite":
        arrays["observed"][0] = np.nan
    else:
        arrays["irregular_time_s"][-1] = 1.0
    with pytest.raises(ValueError):
        assessment.assess_package(
            report, arrays, amplitude=1.0, source_identity=identity()
        )


@pytest.mark.parametrize("amplitude", [True, 0, float("nan"), float("inf"), "1"])
def test_invalid_amplitude_is_not_a_numerical_output(amplitude):
    arrays = inputs()
    with pytest.raises(ValueError, match="amplitude"):
        assessment.assess_package(
            package(arrays), arrays, amplitude=amplitude, source_identity=identity()
        )


def records():
    record = assess()
    result = []
    for model in assessment.MODELS:
        for block in range(1, 7):
            for arm in assessment.ARMS:
                current = copy.deepcopy(record)
                current["source_identity"] = identity(model=model, block=block, arm=arm)
                value = (
                    0.5
                    if arm == "ordinary"
                    else 0.6
                    if arm == "known_covariance"
                    else 0.5 + block / 100
                )
                if model == "ar1":
                    value *= 2
                current["primary"]["value"] = value
                result.append(current)
    return result


def test_summary_has_all_six_values_and_independent_model_specific_paired_mcse():
    result = assessment.summary(records())
    contrast = result["models"]["white"]["contrasts"]["estimated_minus_ordinary"]
    expected = np.arange(1, 7) / 100
    assert [v["value"] for v in contrast["values"]] == pytest.approx(expected)
    assert contrast["mean"] == pytest.approx(0.035)
    assert contrast["median"] == pytest.approx(0.035)
    independent_sd = math.sqrt(sum((float(v) - 0.035) ** 2 for v in expected) / 5)
    assert contrast["sample_sd"] == pytest.approx(independent_sd)
    assert contrast["mcse"] == pytest.approx(independent_sd / math.sqrt(6))
    assert result["models"]["ar1"]["contrasts"]["estimated_minus_ordinary"][
        "mean"
    ] == pytest.approx(0.07)
    assert result["pooled"] is False
    assert result["automatic_arm_selection"] is False
    assert result["planned_packages"] == 36
    json.dumps(result, allow_nan=False)


def replace_with_failure(
    values, *, model="white", block=1, arm="known_covariance", status="failed"
):
    failed = assess(status=status)
    failed["source_identity"] = identity(status, model=model, block=block, arm=arm)
    index = next(
        i
        for i, value in enumerate(values)
        if all(
            value["source_identity"][key] == expected
            for key, expected in (("model", model), ("block", block), ("arm", arm))
        )
    )
    values[index] = failed


def test_third_arm_failure_preserves_complete_primary_pairs_and_failure_denominator():
    values = records()
    replace_with_failure(values)
    model = assessment.summary(values)["models"]["white"]
    primary = model["contrasts"]["estimated_minus_ordinary"]
    assert primary["available"] == 6 and primary["mcse"] is not None
    incomplete = model["contrasts"]["known_minus_ordinary"]
    assert incomplete["available"] == 5 and incomplete["mcse"] is None
    assert incomplete["planned"] == 6
    assert incomplete["values"][0]["value"] is None
    arm = model["arms"]["known_covariance"]
    assert arm["failure_denominator"] == 6
    assert arm["failed_or_not_run"] == 1
    assert arm["primary"]["available"] == 5


def test_not_run_still_counts_in_planned_denominator_and_partial_pairs_never_get_mcse():
    values = records()
    replace_with_failure(values, arm="estimated_covariance", status="not_run")
    model = assessment.summary(values)["models"]["white"]
    assert model["arms"]["estimated_covariance"]["package_status_counts"] == {
        "not_run": 1,
        "success": 5,
    }
    assert model["contrasts"]["estimated_minus_ordinary"]["mcse"] is None
    assert model["contrasts"]["known_minus_ordinary"]["mcse"] is not None


@pytest.mark.parametrize(
    "change",
    ["missing", "duplicate", "extra_block", "nonfinite", "false_available", "negative"],
)
def test_summary_rejects_inventory_and_endpoint_integrity_errors(change):
    values = records()
    if change == "missing":
        values.pop()
    elif change == "duplicate":
        values.append(copy.deepcopy(values[0]))
    elif change == "extra_block":
        values[0]["source_identity"]["block"] = 7
    elif change == "nonfinite":
        values[0]["primary"]["value"] = float("inf")
    elif change == "negative":
        values[0]["primary"]["value"] = -1
    else:
        values[0]["primary"]["status"] = "not_available"
    with pytest.raises(ValueError):
        assessment.summary(values)


def test_large_finite_values_never_emit_infinite_summary_statistics():
    values = records()
    for record in values:
        record["primary"]["value"] = (
            1e308 if record["source_identity"]["arm"] == "estimated_covariance" else 0.0
        )
    result = assessment.summary(values)
    contrast = result["models"]["white"]["contrasts"]["estimated_minus_ordinary"]
    assert contrast["mean"] == contrast["median"] == 1e308
    json.dumps(result, allow_nan=False)


def test_loss_overflow_is_explicit_while_finite_primary_remains_available():
    record = assess(tree=q(1e308))
    assert record["status"] == "success"
    assert record["primary"]["status"] == "available"
    assert record["primary"]["value"] == pytest.approx(1e308)
    for metric in record["diagnostics"].values():
        assert metric["value"] is None
        assert metric["status"] == "numerical_unresolved"
        assert metric["reason"]
    json.dumps(record, allow_nan=False)


def test_unknown_loss_value_error_is_an_integrity_error(monkeypatch):
    def changed_loss(*args):
        raise ValueError("unexpected changed objective")

    monkeypatch.setattr(assessment, "mean_squared_error", changed_loss)
    with pytest.raises(ValueError, match="unexpected changed objective"):
        assess()


def test_all_failed_packages_retain_all_denominators_and_no_invented_zero_error():
    template = assess(status="failed")
    values = []
    for model in assessment.MODELS:
        for block in range(1, 7):
            for arm in assessment.ARMS:
                current = copy.deepcopy(template)
                current["source_identity"] = identity(
                    "failed", model=model, block=block, arm=arm
                )
                values.append(current)
    result = assessment.summary(values)
    for model in result["models"].values():
        for arm in model["arms"].values():
            assert arm["primary"]["available"] == 0
            assert arm["primary"]["planned"] == 6
            assert arm["primary"]["mean"] is None
            assert arm["failure_denominator"] == 6
            assert arm["failure_fraction"] == 1.0
        for contrast in model["contrasts"].values():
            assert contrast["available"] == 0
            assert contrast["mean"] is None
            assert contrast["mcse"] is None
    json.dumps(result, allow_nan=False)


def test_complete_smaller_fixture_does_not_get_a_six_block_mcse():
    values = [record for record in records() if record["source_identity"]["block"] == 1]
    result = assessment.summary(values, planned_blocks=1)
    contrast = result["models"]["white"]["contrasts"]["estimated_minus_ordinary"]
    assert contrast["available"] == 1 and contrast["planned"] == 1
    assert contrast["sample_sd"] is None and contrast["mcse"] is None


@pytest.mark.parametrize("change", ["cost", "digest", "status", "calls"])
def test_invalid_source_and_accounting_are_not_accepted_as_failures(change):
    arrays = inputs()
    report, source = package(arrays), identity()
    if change == "cost":
        report["costs"]["fit_wall_seconds"] = True
    elif change == "digest":
        source["package_sha256"] = "A" * 64
    elif change == "status":
        report["package_status"] = "running"
    else:
        report["search_calls"] = 3
    with pytest.raises(ValueError):
        assessment.assess_package(report, arrays, amplitude=1.0, source_identity=source)
