"""Independently derived endpoints, fixed denominators and original-domain cases."""

import copy
import json
import math
from fractions import Fraction

import gmpy2
import mpmath as mp
import numpy as np
import pytest
from test_structure_proof import T, op, q

from ringdown_sr import main_study_assessment as assessment


def arrays():
    training = np.arange(103, dtype=np.float64) / 4096
    fractions = (np.arange(1024, dtype=np.float64) + 0.371) / 1024
    main = fractions * 0.025
    support = fractions * (102 / 4096)
    return {
        "time_s": training,
        "signal": np.ones(103),
        "observed": np.ones(103),
        "covariance_true": np.eye(103) * 4,
        "main_time_s": main,
        "main_truth": np.ones(1024),
        "support_time_s": support,
        "support_truth": np.ones(1024),
        "endpoint_time_s": np.array([0.0, 0.025]),
        "endpoint_truth": np.ones(2),
    }


def identity(
    condition="estimated_4096s",
    *,
    signal_id=assessment.SIGNALS[0],
    model="ar1",
    block=1,
    status="success",
):
    return {
        "signal_id": signal_id,
        "case_id": f"{signal_id}-{model}-{block:02d}",
        "model": model,
        "block": block,
        "condition": condition,
        "grid": "uniform",
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
            "tree": q(1.125) if tree is None else tree,
            "prediction": (np.full(103, 1.5) if native is None else native).tolist(),
            "display_equation": "1.12500000000000000",
            "complexity": 1,
            "loss": 0.25,
        }
        if status == "success"
        else None,
    }


def assess(
    condition="estimated_4096s",
    *,
    status="success",
    tree=None,
    signal_id=assessment.SIGNALS[0],
):
    data = arrays()
    return assessment.assess_package(
        package(data, status=status, tree=tree),
        None if status == "not_run" else data,
        amplitude=2.0,
        source_identity=identity(condition, status=status, signal_id=signal_id),
    )


def records(signal_id=None):
    template = assess()
    offsets = {
        "ordinary": 0.0,
        "known_covariance": -0.001,
        "estimated_64s": 0.004,
        "estimated_4096s": 0.002,
    }
    output = []
    for signal in assessment.SIGNALS if signal_id is None else (signal_id,):
        for model, count in assessment.PLANNED_BLOCKS.items():
            for block in range(1, count + 1):
                for condition in assessment.ARMS:
                    record = copy.deepcopy(template)
                    record["source_identity"] = identity(
                        condition, signal_id=signal, model=model, block=block
                    )
                    record["background_duration_seconds"] = {
                        "estimated_64s": 64,
                        "estimated_4096s": 4096,
                    }.get(condition)
                    value = 0.2 + offsets[condition] * block
                    record["primary"]["value"] = record["errors"]["main"][
                        "relative_l2"
                    ] = value
                    output.append(record)
    return output


def test_native_training_and_original_offgrid_selection_remain_separate():
    data = arrays()
    original = package(data)
    before = copy.deepcopy(original)
    record = assessment.assess_package(
        original, data, amplitude=-2.0, source_identity=identity()
    )
    assert record["primary"]["value"] == 0.125
    assert record["errors"]["training"]["relative_l2"] == 0.5
    assert record["errors"]["training"]["rms_over_amplitude"] == 0.25
    assert record["errors"]["main"]["rms_over_amplitude"] == 0.0625
    assert record["diagnostics"]["ordinary_mse"]["value"] == 0.25
    assert record["diagnostics"]["q_true_per_sample"]["value"] == 0.0625
    assert record["original_candidate"] == before["selected_candidate"]
    assert original == before
    assert record["amplitude"] == 2.0
    assert record["supplemental"]["new_parameter_match"] == {"status": "not_assessed"}
    assert record["supplemental"]["physical_identification"] == {
        "status": "not_assessed"
    }
    assert json.loads(json.dumps(record, allow_nan=False)) == record


@pytest.mark.parametrize(
    ("prediction", "truth", "amplitude"),
    (
        ([1e308, -1e308], [-1e308, 1e308], 1.0),
        ([2e-300, -2e-300], [1e-300, -1e-300], 1.0),
        ([1.0, 2.0, 4.0], [3.0, 1.0, -2.0], 2.0),
        ([0.0, 0.0], [1e308, 1e308], 1.0),
    ),
)
def test_relative_l2_matches_independent_256_bit_norm_reference(
    prediction, truth, amplitude
):
    with gmpy2.context(precision=256):
        numerator = sum(
            (gmpy2.mpfr(p) - gmpy2.mpfr(t)) ** 2
            for p, t in zip(prediction, truth, strict=True)
        )
        denominator = sum(gmpy2.mpfr(t) ** 2 for t in truth)
        reference = float(gmpy2.sqrt(numerator / denominator))
    result = assessment.curve_metrics(np.array(prediction), np.array(truth), amplitude)
    assert result["relative_l2"] == pytest.approx(reference, rel=5e-16, abs=0)
    assert result["relative_l2_reason"] is None
    json.dumps(result, allow_nan=False)


def test_relative_l2_can_remain_finite_when_amplitude_error_overflows():
    result = assessment.curve_metrics(np.array([1e308]), np.array([-1e308]), 1.0)
    assert result["relative_l2"] == 2.0
    assert result["rms_over_amplitude"] is None
    assert result["max_over_amplitude"] is None
    assert result["status"] == "numerical_unresolved"


def test_unrepresentable_relative_error_and_zero_reference_are_not_finite_successes():
    result = assessment.curve_metrics(np.array([1e308]), np.array([1e-308]), 1.0)
    assert result["relative_l2"] is None
    assert result["relative_l2_reason"] == "relative_l2_out_of_range"
    with pytest.raises(ValueError, match="positive norm"):
        assessment.curve_metrics(np.ones(2), np.zeros(2), 1.0)


def test_exact_l2_rmse_identity_uses_reference_rms_instead_of_amplitude_only():
    p = np.array([3.0, 6.0, 9.0])
    truth = np.array([1.0, 2.0, 3.0])
    result = assessment.curve_metrics(p, truth, 7.0)
    assert result["relative_l2"] == pytest.approx(2.0)
    assert result["relative_l2"] == pytest.approx(
        result["rms_over_amplitude"] / (math.sqrt(14 / 3) / 7)
    )


def test_pole_between_last_training_point_and_nominal_endpoint_is_assessed():
    pole = 0.02495
    assert 102 / 4096 < pole < 0.025
    record = assess(tree=op("/", q(1), op("-", T, q(pole))))
    assert record["supplemental"]["domain"]["status"] == "nonremovable_singularities"
    assert record["supplemental"]["original_family"]["status"] == "proven_nonmember"
    assert record["primary"]["status"] == "available"
    interval = record["supplemental"]["domain"]["interval"]["endpoints"]
    decoded = [
        Fraction(int(v["numerator_hex"], 16), int(v["denominator_hex"], 16))
        for v in interval
    ]
    assert decoded == [Fraction(0), Fraction(1, 40)]


def test_one_nonfinite_grid_point_invalidates_full_endpoint_without_changing_native_training():
    hole = float(arrays()["main_time_s"][3])
    record = assess(tree=op("/", q(1), op("-", T, q(hole))))
    assert record["primary"] == {
        "status": "not_available",
        "reason": "nonfinite_original_tree_prediction",
        "value": None,
    }
    assert record["errors"]["training"]["relative_l2"] == 0.5
    assert record["errors"]["support"]["relative_l2"] is not None
    json.dumps(record, allow_nan=False)


def test_membership_is_separate_from_matching_truth_or_physical_parameters():
    record = assess(
        tree=op("*", op("exp", op("*", q(-250), T)), op("cos", op("*", q(1200), T)))
    )
    assert record["supplemental"]["original_family"]["status"] == "proven_member"
    assert record["supplemental"]["new_parameter_match"]["status"] == "not_assessed"
    assert record["supplemental"]["remainder"]["status"] == "not_assessed"
    assert record["primary"]["value"] > 0


def test_syntax_descriptor_erases_only_constants_without_commutative_reordering():
    first = op("+", T, q(1))
    second = op("+", T, q(7))
    swapped = op("+", q(1), T)
    assert assessment.topology_descriptor(first) == assessment.topology_descriptor(
        second
    )
    assert assessment.topology_descriptor(first) != assessment.topology_descriptor(
        swapped
    )
    assert first["children"][1]["value_hex"] == float(1).hex()


@pytest.mark.parametrize("status", ("failed", "not_run"))
def test_missing_outputs_keep_status_costs_and_no_formula_type(status):
    record = assess(status=status)
    assert record["planned_members"] == 4
    assert record["search_calls"] == (0 if status == "not_run" else 4)
    assert record["costs"]["worker_wall_seconds"] is None
    assert record["topology_descriptor"] is None
    assert record["supplemental"]["domain"]["status"] == "not_assessed"


@pytest.mark.parametrize("signal_id", (None, *assessment.SIGNALS))
def test_complete_inventory_has_exact_primary_family_and_no_restart_pseudoreplication(
    signal_id,
):
    result = assessment.summary(records(signal_id), signal_id=signal_id)
    expected_signals = 2 if signal_id is None else 1
    assert result["planned_packages"] == 160 * expected_signals
    assert (
        result["planned_new_search_calls"]
        == result["new_search_calls"]
        == 640 * expected_signals
    )
    assert (
        result["new_package_costs"]["worker_wall_seconds"]["total"]
        == 1600 * expected_signals
    )
    assert len(result["primary_contrasts"]) == expected_signals
    assert result["primary_family_size"] == 2
    assert result["pooled"] is result["automatic_arm_selection"] is False
    primary_count = 0
    for signal in result["signals"].values():
        for model, n in assessment.PLANNED_BLOCKS.items():
            group = signal["models"][model]
            assert group["conditions"]["ordinary"]["primary"]["planned"] == n
            for contrast in group["contrasts"].values():
                primary_count += int(contrast["is_primary"])
    assert primary_count == expected_signals
    json.dumps(result, allow_nan=False)


def test_paired_moments_and_bonferroni_intervals_have_analytic_references():
    result = assessment.summary(
        records(assessment.SIGNALS[0]), signal_id=assessment.SIGNALS[0]
    )
    for model, n in assessment.PLANNED_BLOCKS.items():
        pair = result["signals"][assessment.SIGNALS[0]]["models"][model]["contrasts"][
            assessment.PRIMARY_CONTRAST
        ]
        mean = -0.002 * (n + 1) / 2
        sd = 0.002 * math.sqrt(n * (n + 1) / 12)
        mcse = 0.002 * math.sqrt((n + 1) / 12)
        assert pair["mean"] == pytest.approx(mean)
        assert pair["sample_sd"] == pytest.approx(sd)
        assert pair["mcse"] == pytest.approx(mcse)
        interval = pair["interval"]
        # Independent 50-digit inverse Student CDF through the incomplete beta.
        with mp.workdps(50):
            degrees = mp.mpf(n - 1)
            probability = mp.mpf("0.9875" if model == "ar1" else "0.975")
            k = float(
                mp.findroot(
                    lambda x, degrees=degrees, probability=probability: (
                        1
                        - mp.betainc(
                            degrees / 2,
                            mp.mpf("0.5"),
                            0,
                            degrees / (degrees + x * x),
                            regularized=True,
                        )
                        / 2
                        - probability
                    ),
                    (2, 3),
                )
            )
        assert interval["critical_value"] == pytest.approx(k, rel=2e-10)
        assert interval["lower"] == pytest.approx(mean - k * mcse)
        assert interval["upper"] == pytest.approx(mean + k * mcse)
        assert interval["confidence"] == (0.975 if model == "ar1" else 0.95)


def test_missing_pair_retains_conditional_description_and_no_complete_comparison_interval():
    signal = assessment.SIGNALS[0]
    values = records(signal)
    index = next(i for i, v in enumerate(values) if v["source_identity"] == identity())
    values[index] = assess(status="failed")
    result = assessment.summary(values, signal_id=signal)
    model = result["signals"][signal]["models"]["ar1"]
    pair = model["contrasts"][assessment.PRIMARY_CONTRAST]
    assert (pair["planned"], pair["available"], pair["unavailable"]) == (30, 29, 1)
    assert pair["mcse"] is None
    assert pair["interval"]["status"] == "not_available"
    assert pair["pair_availability"] == {
        "both_available": 29,
        "only_left_available": 0,
        "only_right_available": 1,
        "both_unavailable": 0,
    }
    assert pair["denominator_scope"] == "available_pairs_conditional_on_both_endpoints"
    group = model["conditions"]["estimated_4096s"]
    assert group["structure"]["original_family"]["counts"]["not_assessed"] == 1
    assert (
        group["structure"]["topology"]["most_frequent_fraction_of_planned"] == 29 / 30
    )
    assert group["structure"]["topology"]["distinct_descriptors"] == 1
    assert result["new_package_costs"]["worker_wall_seconds"]["total"] is None
    assert result["new_package_costs"]["worker_wall_seconds"]["known_subtotal"] == 1590


def test_all_four_pair_availability_states_are_reported_without_imputation():
    signal = assessment.SIGNALS[0]
    values = records(signal)
    for record in values:
        identity_ = record["source_identity"]
        if identity_["model"] == "ar1" and (
            (identity_["block"] in (1, 3) and identity_["condition"] == "estimated_64s")
            or (
                identity_["block"] in (2, 3)
                and identity_["condition"] == "estimated_4096s"
            )
        ):
            record["primary"] = {
                "status": "not_available",
                "reason": "nonfinite_original_tree_prediction",
                "value": None,
            }
            record["errors"]["main"] = assessment.curve_metrics(
                None, np.ones(1024), 2.0, reason="nonfinite_original_tree_prediction"
            )
    pair = assessment.summary(values, signal_id=signal)["signals"][signal]["models"][
        "ar1"
    ]["contrasts"][assessment.PRIMARY_CONTRAST]
    assert pair["pair_availability"] == {
        "both_available": 27,
        "only_left_available": 1,
        "only_right_available": 1,
        "both_unavailable": 1,
    }


def test_duplicates_omissions_and_wrong_signal_sections_are_integrity_errors():
    values = records(assessment.SIGNALS[0])
    for bad in (values[:-1], values + [values[0]]):
        with pytest.raises(ValueError, match="inventory|Duplicate"):
            assessment.summary(bad, signal_id=assessment.SIGNALS[0])
    with pytest.raises(ValueError, match="inventory"):
        assessment.summary(values)
    with pytest.raises(ValueError, match="Unknown"):
        assessment.summary([], signal_id="different")


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("block", True),
        ("block", 31),
        ("grid", "jitter"),
        ("signal_id", "other"),
        ("case_id", "ar1-01"),
        ("package_sha256", "bad"),
        ("selected_member_path", "../escape"),
    ),
)
def test_malformed_identity_is_rejected(key, value):
    binding = identity()
    binding[key] = value
    with pytest.raises(ValueError):
        assessment.assess_package(
            package(arrays()), arrays(), amplitude=1.0, source_identity=binding
        )


@pytest.mark.parametrize(
    "key", ("main_time_s", "support_time_s", "endpoint_time_s", "time_s")
)
def test_wrong_axes_are_rejected_before_assessment(key):
    data = arrays()
    data[key] = data[key].copy()
    data[key][0] = -0.01
    with pytest.raises(ValueError):
        assessment.assess_package(
            package(data), data, amplitude=1.0, source_identity=identity()
        )


def test_forged_primary_or_formula_descriptor_is_rejected_in_summary():
    for field in ("primary", "topology_descriptor"):
        values = records(assessment.SIGNALS[0])
        if field == "primary":
            values[0][field]["value"] = 12.0
        else:
            values[0][field] = {"kind": "variable", "index": 1}
        with pytest.raises(ValueError, match="Primary|Topology"):
            assessment.summary(values, signal_id=assessment.SIGNALS[0])


def test_unresolved_family_and_mixed_domain_keep_distinct_summary_categories():
    signal = assessment.SIGNALS[0]
    values = records(signal)
    ringdown = op("*", op("exp", op("*", q(-250), T)), op("cos", op("*", q(1200), T)))
    unresolved = assess("ordinary", tree=op("+", ringdown, T))
    assert unresolved["supplemental"]["original_family"]["status"] == "unresolved"
    mixed = assess(
        "known_covariance",
        tree=op(
            "*", op("/", q(1), T), op("/", op("-", T, q(0.01)), op("-", T, q(0.01)))
        ),
    )
    assert mixed["supplemental"]["domain"]["status"] == "mixed"
    for replacement in (unresolved, mixed):
        index = next(
            i
            for i, item in enumerate(values)
            if item["source_identity"] == replacement["source_identity"]
        )
        values[index] = replacement
    groups = assessment.summary(values, signal_id=signal)["signals"][signal]["models"][
        "ar1"
    ]["conditions"]
    assert (
        groups["ordinary"]["structure"]["original_family"]["counts"]["unresolved"] == 1
    )
    assert groups["known_covariance"]["structure"]["domain"]["counts"]["mixed"] == 1
    assert groups["known_covariance"]["primary"]["planned"] == 30
