"""Raw-parameter and original-tree replay checks with independent references."""

import copy
import json
import math
import subprocess
import sys
from fractions import Fraction

import numpy as np
import pytest
from test_structure import constant, model, operator, time_node

from ringdown_sr import parameters
from ringdown_sr.parameters import analyze_tree
from ringdown_sr.signals import sample_times
from ringdown_sr.structure import InvalidTreeError
from ringdown_sr.symbolic import evaluate_tree


def test_basic_reference_raw_parameters_and_both_replays():
    report = analyze_tree(model(), sample_times(128, 4096), sample_rate_hz=4096)
    raw = report["raw_parameters"]
    for key, value in {
        "amplitude": 2,
        "exponential_rate_per_s": -125,
        "angular_frequency_per_s": 512,
        "phase_rad": 0.25,
        "decay_time_s": 0.008,
    }.items():
        assert raw[key] == {"value": value, "status": "available", "reason": None}
    assert raw["frequency_raw_signed_hz"]["value"] == 256 / math.pi
    assert raw["frequency_raw_hz"]["value"] == 256 / math.pi
    assert (
        report["raw_replay"]["status"] == report["alias_replay"]["status"] == "passed"
    )
    assert report["alias"]["status"] == "available"
    assert report["structure"]["raw_coefficients"]["d"] == {
        "numerator": "1",
        "denominator": "4",
    }
    assert report["identifiability"] == {
        "physical_identification": "not_assessed",
        "zero_amplitude": False,
        "amplitude_phase_degeneracy": "none",
    }
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize("amplitude", [-2, 0, 1e-21])
@pytest.mark.parametrize(
    "rate,status,reason",
    [
        (-125, "available", None),
        (0, "not_applicable", "undamped"),
        (1, "not_applicable", "growing"),
    ],
)
def test_signed_tiny_and_exact_zero_amplitudes_do_not_change_the_decay_rule(
    amplitude, rate, status, reason
):
    tree = model(
        amplitude=amplitude, exponential=operator("*", constant(rate), time_node())
    )
    report = analyze_tree(tree, sample_times(64, 4096), sample_rate_hz=4096)
    raw = report["raw_parameters"]
    assert raw["amplitude"]["value"] == amplitude
    assert raw["decay_time_s"]["status"] == status
    assert raw["decay_time_s"]["reason"] == reason
    assert report["identifiability"]["zero_amplitude"] is (amplitude == 0)
    assert (
        report["raw_replay"]["status"] == report["alias_replay"]["status"] == "passed"
    )
    if amplitude == 0:
        assert report["raw_replay"]["amplitude_scale"] == 0


@pytest.mark.parametrize("frequency,expected_alias", [(0, "dc"), (512, "none")])
def test_degeneracy_is_explicit_and_not_physical_identification(
    frequency, expected_alias
):
    tree = model(
        oscillation=operator(
            "+", operator("*", constant(frequency), time_node()), constant(0.25)
        )
    )
    report = analyze_tree(tree, sample_times(8, 4096), sample_rate_hz=4096)
    assert report["identifiability"]["amplitude_phase_degeneracy"] == expected_alias
    assert report["identifiability"]["physical_identification"] == "not_assessed"


@pytest.mark.parametrize("angular", [-512, 2 * math.pi * 4346, 2 * math.pi * 3846])
def test_raw_signed_frequency_and_sample_alias_are_separate(angular):
    tree = model(
        oscillation=operator(
            "+", operator("*", constant(angular), time_node()), constant(0.25)
        )
    )
    report = analyze_tree(tree, sample_times(16, 4096), sample_rate_hz=4096)
    raw = report["raw_parameters"]
    assert raw["frequency_raw_signed_hz"]["value"] == pytest.approx(
        angular / (2 * math.pi), rel=1e-15
    )
    assert raw["frequency_raw_hz"]["value"] >= 0
    assert report["alias"]["frequency_alias_hz"]["value"] < 2048
    assert (
        report["raw_replay"]["status"] == report["alias_replay"]["status"] == "passed"
    )


def test_binary_angular_nyquist_never_claims_an_exact_nyquist_degeneracy():
    tree = model(oscillation=operator("*", constant(2 * math.pi * 2048), time_node()))
    report = analyze_tree(tree, sample_times(16, 4096), sample_rate_hz=4096)
    assert report["raw_parameters"]["frequency_raw_hz"]["value"] == 2048
    assert report["alias"]["frequency_alias_hz"]["reason"] == "boundary_rounding"
    assert report["alias"]["degeneracy"] == "none"
    assert report["raw_replay"]["status"] == "passed"
    assert report["alias_replay"] == {
        "status": "not_attempted",
        "reason": "alias_unavailable",
    }


def test_underflow_is_not_an_exact_zero_amplitude():
    tree = model(amplitude=operator("*", constant(1e-300), constant(1e-300)))
    times = sample_times(8, 4096)
    assert np.array_equal(evaluate_tree(tree, times), np.zeros(8))
    report = analyze_tree(tree, times, sample_rate_hz=4096)
    assert report["raw_parameters"]["amplitude"] == {
        "value": None,
        "status": "numerical_unresolved",
        "reason": "rounded_to_zero",
    }
    assert report["identifiability"]["zero_amplitude"] is False
    assert report["raw_replay"]["reason"] == "unavailable_raw_coefficient"


def test_nonassociative_original_tree_cannot_be_confirmed_by_exact_algebra():
    left = operator("+", operator("+", constant(1e16), constant(-1e16)), constant(1))
    right = operator("+", constant(1e16), operator("+", constant(-1e16), constant(1)))
    times = sample_times(32, 4096)
    reports = [
        analyze_tree(
            model(exponential=operator("*", rate, time_node())),
            times,
            sample_rate_hz=4096,
        )
        for rate in (left, right)
    ]
    assert (
        reports[0]["structure"]["raw_coefficients"]
        == reports[1]["structure"]["raw_coefficients"]
    )
    assert reports[0]["raw_parameters"]["exponential_rate_per_s"]["value"] == 1
    assert reports[0]["raw_replay"]["status"] == "passed"
    assert (
        reports[1]["raw_replay"]["status"]
        == reports[1]["alias_replay"]["status"]
        == "failed"
    )
    assert reports[1]["raw_replay"]["reason"] == "prediction_mismatch"


@pytest.mark.parametrize("amplitude", [1, 1e-21])
def test_equal_quadratics_cannot_hide_an_opposite_original_prediction(
    monkeypatch, amplitude
):
    tree = model(amplitude=amplitude)
    times = sample_times(16, 4096)
    original = evaluate_tree(tree, times)
    assert np.dot(original, original) == np.dot(-original, -original)
    monkeypatch.setattr(parameters, "evaluate_tree", lambda *_: -original)
    report = analyze_tree(tree, times, sample_rate_hz=4096)
    for replay in (report["raw_replay"], report["alias_replay"]):
        assert (
            replay["status"] == "failed" and replay["reason"] == "prediction_mismatch"
        )
        assert replay["max_normalized_difference"] == pytest.approx(2)
        assert replay["amplitude_scale"] < 2 * amplitude


@pytest.mark.parametrize("offset", [True, False])
def test_foreign_time_axes_keep_raw_replay_but_no_zero_origin_alias(offset):
    times = sample_times(16, 4096)
    if offset:
        times += 1 / 4096
    else:
        times[5] = np.nextafter(times[5], math.inf)
    report = analyze_tree(model(), times, sample_rate_hz=4096)
    assert report["raw_replay"]["status"] == "passed"
    assert report["alias"] == {
        "status": "not_attempted",
        "reason": "time_axis_not_zero_origin_uniform",
    }
    assert report["alias_replay"]["status"] == "not_attempted"


def test_nonfinite_canonical_form_is_not_confirmed_by_a_finite_original():
    rate = operator("+", constant(1e16), operator("+", constant(-1e16), constant(1)))
    report = analyze_tree(
        model(exponential=operator("*", rate, time_node())), [0, 1000], sample_rate_hz=1
    )
    assert report["raw_replay"] == {
        "status": "failed",
        "reason": "nonfinite_replay_prediction",
    }
    assert report["alias_replay"]["status"] == "not_attempted"
    json.dumps(report, allow_nan=False)


def test_nonfinite_original_is_an_explicit_failed_replay():
    tree = model(exponential=operator("*", constant(1e308), time_node()))
    report = analyze_tree(tree, [0, 1], sample_rate_hz=1)
    assert report["structure"]["structure_status"] == "recognized"
    assert report["raw_replay"] == {
        "status": "failed",
        "reason": "nonfinite_original_prediction",
    }
    json.dumps(report, allow_nan=False)


def test_huge_angles_keep_raw_fields_and_a_failed_or_unresolved_diagnosis():
    tree = model(
        oscillation=operator(
            "+", operator("*", constant(1e300), time_node()), constant(1e300)
        )
    )
    report = analyze_tree(tree, sample_times(8, 4096), sample_rate_hz=4096)
    assert report["raw_parameters"]["angular_frequency_per_s"]["value"] == 1e300
    assert report["alias"]["status"] == "numerical_unresolved"
    assert report["alias"]["pi_terms"] == 64
    json.dumps(report, allow_nan=False)


def test_input_objects_and_original_tree_are_read_only():
    tree = model()
    before = copy.deepcopy(tree)
    times = sample_times(16, 4096)
    expected_times = times.copy()
    times.flags.writeable = False
    first = analyze_tree(tree, times, sample_rate_hz=4096)
    assert first == analyze_tree(
        copy.deepcopy(tree), expected_times.copy(), sample_rate_hz=4096
    )
    assert tree == before and np.array_equal(times, expected_times)


def test_unsupported_valid_tree_is_recorded_but_invalid_tree_raises():
    report = analyze_tree(operator("sin", time_node()), [0, 1], sample_rate_hz=1)
    assert report["structure"]["structure_status"] == "not_supported"
    assert report["raw_parameters"] is None
    assert (
        report["raw_replay"]["status"] == report["alias"]["status"] == "not_attempted"
    )
    with pytest.raises(InvalidTreeError):
        analyze_tree({"kind": "variable", "index": 2}, [0], sample_rate_hz=1)


@pytest.mark.parametrize(
    "times", [[], [[0, 1]], [0, math.nan], [0, math.inf], [True], ["0"], [1j]]
)
def test_invalid_time_inputs_are_rejected(times):
    with pytest.raises(ValueError):
        analyze_tree(model(), times, sample_rate_hz=4096)


@pytest.mark.parametrize(
    "sample_rate,error",
    [
        (0, ValueError),
        (-1, ValueError),
        (True, TypeError),
        (np.bool_(True), TypeError),
        (math.inf, ValueError),
        (math.nan, ValueError),
        ("4096", TypeError),
        (1j, TypeError),
        (10**400, ValueError),
    ],
)
def test_invalid_sample_rates_are_rejected(sample_rate, error):
    with pytest.raises(error):
        analyze_tree(model(), [0, 1], sample_rate_hz=sample_rate)


def test_parameter_module_does_not_initialize_julia_or_pysr():
    code = "import sys; from ringdown_sr.parameters import analyze_tree; assert not {'juliacall', 'pysr'} & sys.modules.keys()"
    subprocess.run([sys.executable, "-c", code], check=True)


def test_exact_rational_tau_can_be_unrepresentable_without_becoming_zero():
    # The exact extracted b is a ratio, not the rounded result of this division.
    rate = operator("/", constant(-1e-300), constant(1e300))
    report = analyze_tree(
        model(exponential=operator("*", rate, time_node())), [0], sample_rate_hz=4096
    )
    assert (
        Fraction(
            int(report["structure"]["raw_coefficients"]["b"]["numerator"]),
            int(report["structure"]["raw_coefficients"]["b"]["denominator"]),
        )
        < 0
    )
    assert report["raw_parameters"]["decay_time_s"]["reason"] == "outside_float64_range"
    assert (
        report["raw_parameters"]["exponential_rate_per_s"]["reason"]
        == "rounded_to_zero"
    )
