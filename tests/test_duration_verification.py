"""Independent loss, exact-form and phase counterexamples for duration format 2."""

import copy
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from test_structure import constant as c
from test_structure import operator as op
from test_structure import time_node as t

from ringdown_sr import symbolic
from ringdown_sr.aliasing import Phase, phase_field, reduce_alias
from ringdown_sr.duration_replay import candidate_evidence, verify_loss_replay
from ringdown_sr.losses import mean_squared_error
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.parameters import analyze_tree
from ringdown_sr.representation_control import diagnose_candidate
from ringdown_sr.structure import (
    InvalidTreeError,
    recognize_ringdown,
    recognize_ringdown_extended,
)

FIXTURE = Path(__file__).parent / "fixtures/duration_replay_cases.json"
FIXTURE_DATA = json.loads(FIXTURE.read_bytes())
CASES = FIXTURE_DATA["cases"]
PI = Decimal(
    "3.141592653589793238462643383279502884197169399375105820974944592307816406286"
)


def replay(y, native, python, **changes):
    y, native, python = (np.asarray(v, dtype=float) for v in (y, native, python))
    native_loss = mean_squared_error(y - native)
    args = {
        "observed": y,
        "native_prediction": native,
        "python_prediction": python,
        "raw_loss": native_loss,
        "replay_loss": native_loss,
        "table_loss": native_loss,
        "python_loss": mean_squared_error(y - python),
        "loss_object": None,
    }
    args.update(changes)
    return verify_loss_replay(**args)


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("exponent", [-100, 0, 100])
def test_observed_roundoff_passes_without_changing_raw_losses_or_vectors(
    case, exponent
):
    arrays = {
        key: np.asarray(values, dtype=float)
        for key, values in FIXTURE_DATA["training_inputs"].items()
    }
    scale = 2.0**exponent
    y = arrays["observed"] * scale
    native = np.array(case["native_prediction"]) * scale
    python = np.array(case["python_prediction"]) * scale
    raw = case["native_loss"] * scale**2
    before = (y.copy(), native.copy(), python.copy())
    with pytest.raises(AssertionError):
        symbolic._verify_loss_replay(
            y, native, python, raw, raw, raw, mean_squared_error(y - python), None
        )
    record = replay(y, native, python, raw_loss=raw, replay_loss=raw, table_loss=raw)
    assert record["status"] == "passed"
    assert record["table_loss"] == raw
    assert record["absolute_loss_difference"] <= record["loss_difference_bound"]
    assert record["prediction_replay"]["max_normalized_difference"] < 3e-16
    for saved, current in zip(before, (y, native, python), strict=True):
        np.testing.assert_array_equal(saved.view(np.uint64), current.view(np.uint64))


def test_exact_zero_and_simple_hand_computed_reduction():
    assert replay([1, 2, 3], [1, 2, 3], [1, 2, 3])["loss_difference_bound"] == 0
    assert (
        replay([1, 2, 3], [0.5, 1.5, 2.5], [0.5, 1.5, 2.5])["native_residual_mse"]
        == 0.25
    )
    with pytest.raises(ValueError, match="own residual"):
        replay([1], [1], [1], raw_loss=1e-30, replay_loss=1e-30, table_loss=1e-30)


@pytest.mark.parametrize("which", ["native", "python", "replay"])
def test_internally_consistent_but_wrong_loss_is_not_hidden_by_prediction_agreement(
    which,
):
    changes = {
        "native": {
            "raw_loss": 0.25 * (1 + 1e-11),
            "replay_loss": 0.25 * (1 + 1e-11),
            "table_loss": 0.25 * (1 + 1e-11),
        },
        "python": {"python_loss": 0.25 * (1 + 1e-11)},
        "replay": {"replay_loss": 0.25 * (1 + 1e-11)},
    }[which]
    with pytest.raises(ValueError, match="own residual"):
        replay([1, 2, 3], [0.5, 1.5, 2.5], [0.5, 1.5, 2.5], **changes)


def test_pinned_pandas_csv_conversion_is_distinct_from_native_reduction():
    # Observed in the K3 eight-point technical control, not a new scientific fit.
    encoded = "0.008261169598036541"
    parsed = float(pd.read_csv(StringIO("Loss\n" + encoded + "\n"))["Loss"][0])
    raw = float(encoded)
    assert parsed == 0.0082611695980365 and parsed != raw
    times = np.arange(8, dtype=float) / 8
    prediction = np.exp(times * 0.8401887737401458)
    record = replay(
        1 + times,
        prediction,
        prediction,
        raw_loss=raw,
        replay_loss=raw,
        table_loss=parsed,
    )
    assert record["table_loss"] == parsed
    assert (
        record["table_loss_role"] == "pysr_pandas_csv_value; relative_comparison_only"
    )


def test_wrong_table_value_still_fails_its_unchanged_relative_contract():
    with pytest.raises(AssertionError):
        replay(
            [1, 2, 3], [0.5, 1.5, 2.5], [0.5, 1.5, 2.5], table_loss=0.25 * (1 + 1e-6)
        )


@pytest.mark.parametrize("value", [1e-160, 1e-200, 1e155])
def test_non_normal_squares_fail_closed_even_if_the_reported_loss_is_zero(value):
    with pytest.raises(ValueError, match="normal Float64"):
        verify_loss_replay(
            np.array([value]), np.zeros(1), np.zeros(1), 0.0, 0.0, 0.0, 0.0, None
        )


def test_prediction_and_metric_gates_are_required_separately():
    with pytest.raises(AssertionError):
        replay([1], [1], [1 + 1e-6])
    with pytest.raises(ValueError, match="ordinary"):
        replay([1], [1], [1], loss_object=object())
    with pytest.raises(ValueError, match="equal nonempty"):
        verify_loss_replay([1], [1, 2], [1], 0.0, 0.0, 0.0, 0.0, None)


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf"), True])
def test_invalid_loss_is_rejected(bad):
    with pytest.raises(ValueError):
        replay([1], [1], [1], raw_loss=bad)


@pytest.mark.parametrize("case", CASES)
def test_csv_case_diagnosis_has_matching_parameters_without_replacing_original_tree(
    case,
):
    arrays = frozen_data()
    tree = copy.deepcopy(case["tree"])
    candidate = {**case, "loss": case["native_loss"]}
    legacy = diagnose_candidate(candidate, 0, 0, arrays, "complexity_frequency")
    new = diagnose_candidate(
        candidate, 0, 0, arrays, "complexity_frequency", extended_structure=True
    )
    assert legacy["search_analysis"]["structure"]["structure_status"] == "not_supported"
    assert new["search_analysis"]["structure"]["structure_status"] == "recognized"
    assert new["parameter_match"]["status"] == "matched"
    assert new["physical_analysis"]["raw_replay"]["status"] == "passed"
    assert new["physical_analysis"]["alias_replay"]["status"] == "passed"
    assert new["physical_identification"] == "not_assessed"
    assert new["curve_errors"] == legacy["curve_errors"]
    assert new["source_candidate_sha256"] == legacy["source_candidate_sha256"]
    assert case["tree"] == tree
    raw = recognize_ringdown_extended(tree).coefficients
    with localcontext() as context:
        context.prec = 80
        expected_phase = (
            Decimal(raw.phase_rad.numerator) / Decimal(raw.phase_rad.denominator)
            - PI / 2
        )
        assert new["search_analysis"]["raw_parameters"]["phase_rad"]["value"] == float(
            expected_phase
        )


@pytest.mark.parametrize("trig", ["sin", "cos"])
@pytest.mark.parametrize("quotient", [False, True])
@pytest.mark.parametrize("frequency", [-512, 512])
@pytest.mark.parametrize("amplitude", [-2, 2])
def test_exact_form_coefficients_cover_signs_and_equivalent_products(
    trig, quotient, frequency, amplitude
):
    exponential = op("exp", op("*", c(125 if quotient else -125), t()))
    oscillation = op(trig, op("+", op("*", c(frequency), t()), c(0.25)))
    tree = op("*", c(amplitude), op("/" if quotient else "*", oscillation, exponential))
    result = recognize_ringdown_extended(tree)
    raw = result.coefficients
    assert result.structure_status == "recognized"
    assert (
        raw.amplitude,
        raw.exponential_rate_per_s,
        raw.angular_frequency_per_s,
        raw.phase_rad,
        raw.phase_pi_multiple,
    ) == (
        amplitude,
        -125,
        frequency,
        Fraction(1, 4),
        Fraction(-1, 2) if trig == "sin" else 0,
    )
    if quotient or trig == "sin":
        assert recognize_ringdown(tree).structure_status == "not_supported"
    analysis = analyze_tree(
        tree, np.arange(16) / 4096, sample_rate_hz=4096, extended_structure=True
    )
    assert (
        analysis["raw_replay"]["status"]
        == analysis["alias_replay"]["status"]
        == "passed"
    )


def quotient_model():
    return op("/", op("sin", op("*", c(512), t())), op("exp", op("*", c(125), t())))


@pytest.mark.parametrize(
    "make",
    [
        lambda: op("+", quotient_model(), c(1)),
        lambda: op("*", quotient_model(), t()),
        lambda: op("*", quotient_model(), op("cos", t())),
        lambda: op("*", quotient_model(), op("exp", t())),
        lambda: op("/", c(1), quotient_model()),
        lambda: op("/", c(1), op("/", c(1), quotient_model())),
        lambda: op("/", quotient_model(), c(0)),
        lambda: op("/", quotient_model(), op("/", c(0), c(1))),
        lambda: op("/", quotient_model(), op("/", c(1), c(0))),
        lambda: op("/", op("sin", op("*", t(), t())), op("exp", t())),
        lambda: op("/", op("sin", t()), op("exp", op("+", t(), c(1)))),
    ],
)
def test_singular_extra_nonlinear_and_additive_forms_stay_unsupported(make):
    assert recognize_ringdown_extended(make()).structure_status == "not_supported"


def test_all_nodes_are_validated_even_when_multiplied_by_zero():
    tree = op("*", c(0), quotient_model())
    tree["children"][1]["children"][0]["operator_index"] = True
    with pytest.raises(InvalidTreeError):
        recognize_ringdown_extended(tree)


def test_recognition_does_not_override_failed_numerical_replay():
    argument = op("*", t(), op("+", c(1e16), op("+", c(-1e16), c(1))))
    tree = op("/", op("sin", argument), op("exp", op("*", c(1), t())))
    report = analyze_tree(
        tree, np.arange(8) / 8, sample_rate_hz=8, extended_structure=True
    )
    assert report["structure"]["structure_status"] == "recognized"
    assert report["raw_replay"]["status"] == "failed"


@pytest.mark.parametrize("orientation", [-1, 1])
def test_mixed_phase_alias_orientation_is_derived_with_exact_pi(orientation):
    phase = Phase("radian_plus_pi", Fraction(1, 4), Fraction(-1, 2))
    result = reduce_alias(
        sample_rate_hz=4096, frequency_hz=orientation * 250, phase=phase
    )
    assert result["status"] == "available"
    assert result["frequency_alias_hz"]["value"] == 250
    with localcontext() as context:
        context.prec = 80
        expected = orientation * (Decimal(1) / 4 - PI / 2)
        assert result["phase_alias_rad"]["value"] == float(expected)
        assert phase_field(phase)["value"] == float(Decimal(1) / 4 - PI / 2)


def test_parent_requires_replay_evidence_even_for_perfect_predictions():
    with pytest.raises(ValueError, match="Missing"):
        candidate_evidence({}, np.arange(8), np.ones(8))
