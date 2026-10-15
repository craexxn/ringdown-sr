"""Check sampling conventions and independently derived signal values."""

import math

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from ringdown_sr.signals import ringdown_signal, sample_times


def test_sample_times_have_exact_binary_spacing_and_exclude_window_end():
    # Five samples at 8 Hz occupy [0, 5/8); the last sample is at 4/8.
    actual = sample_times(n_samples=5, sample_rate_hz=8.0)
    assert_array_equal(actual, [0.0, 0.125, 0.25, 0.375, 0.5])
    assert actual.dtype == np.float64


def test_sample_count_is_explicit_for_the_provisional_sampling_rate():
    # 25 ms * 4096 Hz = 102.4, so this API asks for an integer count.
    actual = sample_times(n_samples=102, sample_rate_hz=4096.0)
    assert actual.size == 102
    assert actual[-1] == 101 / 4096
    assert_array_equal(np.diff(actual), np.full(101, 1 / 4096))


def test_single_sample_starts_at_zero():
    assert_array_equal(sample_times(1, 4096.0), [0.0])


@pytest.mark.parametrize(
    ("n_samples", "error"),
    [
        (0, ValueError),
        (-1, ValueError),
        (1.5, TypeError),
        (True, TypeError),
        (np.bool_(True), TypeError),
    ],
)
def test_invalid_sample_counts_are_rejected(n_samples, error):
    with pytest.raises(error, match="n_samples"):
        sample_times(n_samples, 4096.0)


@pytest.mark.parametrize(
    ("sample_rate", "error"),
    [
        (0.0, ValueError),
        (-1.0, ValueError),
        (math.nan, ValueError),
        (math.inf, ValueError),
        (True, TypeError),
    ],
)
def test_invalid_sample_rates_are_rejected(sample_rate, error):
    with pytest.raises(error, match="sample_rate_hz"):
        sample_times(5, sample_rate)


def test_ringdown_matches_hand_calculated_oscillation_and_decay():
    # tau = 1/ln(2) gives an envelope A * 2**(-t).
    # For f = 1 Hz the cosine is [1, 0, -1, 0, 1] at these times.
    actual = ringdown_signal(
        [0.0, 0.25, 0.5, 0.75, 1.0],
        amplitude=2.0,
        frequency_hz=1.0,
        decay_time_s=1 / math.log(2),
    )
    assert_allclose(actual, [2.0, 0.0, -math.sqrt(2), 0.0, 1.0], rtol=1e-14, atol=1e-15)


def test_zero_frequency_matches_hand_calculated_halving():
    actual = ringdown_signal(
        [0.0, 1.0, 2.0, 3.0],
        amplitude=2.0,
        frequency_hz=0.0,
        decay_time_s=1 / math.log(2),
    )
    assert_allclose(actual, [2.0, 1.0, 0.5, 0.25], rtol=1e-14, atol=0.0)


def test_phase_is_an_additive_angle_in_radians():
    # At t = 0, a phase of pi flips the amplitude's sign.
    actual = ringdown_signal(
        [0.0], amplitude=3.0, frequency_hz=1.0, decay_time_s=1.0, phase_rad=math.pi
    )
    assert_allclose(actual, [-3.0], rtol=1e-14, atol=0.0)


def test_phase_changes_quarter_period_values():
    # cos(2*pi*t + pi/2) is [0, -1, 0, 1] at quarter periods.
    actual = ringdown_signal(
        [0.0, 0.25, 0.5, 0.75],
        amplitude=1.0,
        frequency_hz=1.0,
        decay_time_s=1 / math.log(2),
        phase_rad=math.pi / 2,
    )
    assert_allclose(actual, [0.0, -(2**-0.25), 0.0, 2**-0.75], rtol=1e-14, atol=1e-15)


def test_tiny_amplitude_is_not_hidden_by_absolute_tolerance():
    actual = ringdown_signal(
        [0.0, 1.0, 2.0],
        amplitude=1e-21,
        frequency_hz=0.0,
        decay_time_s=1 / math.log(2),
    )
    assert_allclose(actual, [1e-21, 5e-22, 2.5e-22], rtol=1e-14, atol=0.0)


def test_negative_amplitude_is_preserved():
    actual = ringdown_signal(
        [0.0, 1.0],
        amplitude=-2.0,
        frequency_hz=0.0,
        decay_time_s=1 / math.log(2),
    )
    assert_allclose(actual, [-2.0, -1.0], rtol=1e-14, atol=0.0)


def test_zero_amplitude_produces_zero_signal():
    actual = ringdown_signal(
        [0.0, 0.5, 1.0], amplitude=0.0, frequency_hz=1.0, decay_time_s=1.0
    )
    assert_array_equal(actual, [0.0, 0.0, 0.0])


@pytest.mark.parametrize(
    "times",
    [[], [0.0, -0.1], [math.nan], [math.inf], 0.0, [[0.0]], [1j], ["0"], [True]],
)
def test_invalid_time_arrays_are_rejected(times):
    with pytest.raises(ValueError, match="time_s"):
        ringdown_signal(times, amplitude=1.0, frequency_hz=1.0, decay_time_s=1.0)


@pytest.mark.parametrize(
    ("name", "value", "error"),
    [
        ("amplitude", math.nan, ValueError),
        ("amplitude", math.inf, ValueError),
        ("frequency_hz", -1.0, ValueError),
        ("frequency_hz", math.nan, ValueError),
        ("decay_time_s", 0.0, ValueError),
        ("decay_time_s", -1.0, ValueError),
        ("decay_time_s", math.inf, ValueError),
        ("phase_rad", math.nan, ValueError),
        ("phase_rad", True, TypeError),
    ],
)
def test_invalid_signal_parameters_are_rejected(name, value, error):
    parameters = {"amplitude": 1.0, "frequency_hz": 1.0, "decay_time_s": 1.0}
    parameters[name] = value
    with pytest.raises(error, match=name):
        ringdown_signal([0.0, 0.5], **parameters)


def test_numerical_overflow_is_reported_instead_of_returning_nan():
    with pytest.raises(ValueError, match="numerical range"):
        ringdown_signal(
            [1.0],
            amplitude=1.0,
            frequency_hz=np.finfo(np.float64).max,
            decay_time_s=1.0,
        )
