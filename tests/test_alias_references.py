"""Independent sample-alias references for a future expression interpreter.

These are explicit reference pairs, not an implementation of tree recognition
or a general frequency/phase reduction algorithm.
"""

import math
from dataclasses import dataclass
from fractions import Fraction

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from ringdown_sr.signals import ringdown_signal, sample_times

FS = 4096
TAU = 0.008


@dataclass(frozen=True)
class AliasReference:
    raw_hz: float
    raw_phase_pi: Fraction
    alias_hz: float
    alias_phase_pi: Fraction
    orientation: int


# Phases are rational multiples of pi; signed frequencies are explicit.
REFERENCES = [
    pytest.param(
        AliasReference(250, Fraction(1, 5), 250, Fraction(1, 5), 1), id="base"
    ),
    pytest.param(
        AliasReference(4346, Fraction(1, 5), 250, Fraction(1, 5), 1), id="plus-fs"
    ),
    pytest.param(
        AliasReference(3846, Fraction(1, 5), 250, Fraction(-1, 5), -1), id="reflection"
    ),
    pytest.param(
        AliasReference(-250, Fraction(1, 5), 250, Fraction(-1, 5), -1), id="negative"
    ),
    pytest.param(
        AliasReference(-4346, Fraction(1, 5), 250, Fraction(-1, 5), -1),
        id="negative-plus-fs",
    ),
    pytest.param(
        AliasReference(-3846, Fraction(1, 5), 250, Fraction(1, 5), 1),
        id="negative-reflection",
    ),
    pytest.param(
        AliasReference(4346, Fraction(9, 4), 250, Fraction(1, 4), 1), id="phase-wrap"
    ),
    pytest.param(
        AliasReference(3846, Fraction(9, 4), 250, Fraction(-1, 4), -1),
        id="phase-wrap-reflection",
    ),
    pytest.param(
        AliasReference(250, Fraction(1), 250, Fraction(-1), 1), id="phase-plus-pi"
    ),
    pytest.param(AliasReference(0, Fraction(1, 5), 0, Fraction(1, 5), 1), id="dc"),
    pytest.param(
        AliasReference(4096, Fraction(1, 5), 0, Fraction(1, 5), 1), id="dc-alias"
    ),
    pytest.param(
        AliasReference(2048, Fraction(1, 5), 2048, Fraction(-1, 5), -1), id="nyquist"
    ),
    pytest.param(
        AliasReference(-2048, Fraction(1, 5), 2048, Fraction(-1, 5), -1),
        id="negative-nyquist",
    ),
    pytest.param(
        AliasReference(6144, Fraction(1, 5), 2048, Fraction(-1, 5), -1),
        id="nyquist-alias",
    ),
    pytest.param(
        AliasReference(
            math.nextafter(2048.0, 0.0),
            Fraction(1, 5),
            math.nextafter(2048.0, 0.0),
            Fraction(1, 5),
            1,
        ),
        id="below-nyquist-one-ulp",
    ),
    pytest.param(
        AliasReference(
            math.nextafter(2048.0, math.inf),
            Fraction(1, 5),
            2047.9999999999995,
            Fraction(-1, 5),
            -1,
        ),
        id="above-nyquist-one-ulp",
    ),
]


def signed_expression(times, frequency, phase, amplitude):
    """Evaluate the declared signed expression without the generator's f >= 0 contract."""
    return (
        amplitude
        * np.exp(-times / TAU)
        * np.cos(2 * math.pi * frequency * times + phase)
    )


def sample_error_budget(times, raw_hz, raw_phase, alias_hz, alias_phase):
    """Budget moderate-argument Float64 evaluation; exact identities are checked separately."""
    max_argument = max(
        np.max(np.abs(2 * math.pi * raw_hz * times + raw_phase)),
        np.max(np.abs(2 * math.pi * alias_hz * times + alias_phase)),
        np.max(times / TAU),
    )
    return 16 * np.finfo(np.float64).eps * (1 + max_argument)


@pytest.mark.parametrize("reference", REFERENCES)
def test_reference_pairs_differ_by_exact_integer_turns(reference):
    # cos(a) = cos(s*a) for s in {-1, 1}; integer turns preserve cosine.
    raw = Fraction.from_float(float(reference.raw_hz))
    alias = Fraction.from_float(float(reference.alias_hz))
    assert 0 <= alias <= FS / 2
    assert -1 <= reference.alias_phase_pi < 1
    assert -FS / 2 <= reference.orientation * alias < FS / 2
    for j in range(128):
        raw_turns = raw * j / FS + reference.raw_phase_pi / 2
        alias_turns = alias * j / FS + reference.alias_phase_pi / 2
        assert (raw_turns - reference.orientation * alias_turns).denominator == 1


@pytest.mark.parametrize("reference", REFERENCES)
@pytest.mark.parametrize("amplitude", [1.0, -2.0, 1e-21])
def test_reference_pairs_match_actual_ringdown_samples(reference, amplitude):
    times = sample_times(128, FS)
    raw_phase = float(reference.raw_phase_pi) * math.pi
    alias_phase = float(reference.alias_phase_pi) * math.pi
    raw = signed_expression(times, reference.raw_hz, raw_phase, amplitude)
    alias = ringdown_signal(
        times,
        amplitude=amplitude,
        frequency_hz=reference.alias_hz,
        decay_time_s=TAU,
        phase_rad=alias_phase,
    )
    # Normalize before comparing so tiny amplitudes cannot hide a wrong phase.
    budget = sample_error_budget(
        times, reference.raw_hz, raw_phase, reference.alias_hz, alias_phase
    )
    assert_allclose(raw / abs(amplitude), alias / abs(amplitude), rtol=0, atol=budget)


@pytest.mark.parametrize("amplitude", [1.0, 1e-21])
def test_reflection_without_phase_reversal_is_a_counterexample(amplitude):
    times = sample_times(128, FS)
    raw = signed_expression(times, 3846, math.pi / 5, amplitude)
    wrong = signed_expression(times, 250, math.pi / 5, amplitude)
    assert np.max(np.abs(raw / amplitude - wrong / amplitude)) > 0.5


@pytest.mark.parametrize("amplitude", [1.0, 1e-21])
def test_sample_equivalent_expressions_can_disagree_between_samples(amplitude):
    times = np.array([1 / (2 * FS)])
    raw = signed_expression(times, 4346, math.pi / 5, amplitude) / amplitude
    alias = signed_expression(times, 250, math.pi / 5, amplitude) / amplitude
    # A single added fs gives pi at the midpoint, hence the opposite sign.
    assert_allclose(raw, -alias, rtol=0, atol=16 * np.finfo(float).eps)
    assert abs(float(raw[0] - alias[0])) > 1


def test_nonzero_time_origin_needs_an_additional_phase_shift():
    times = 1 / (4 * FS) + sample_times(128, FS)
    raw = signed_expression(times, 4346, math.pi / 5, 1)
    wrong = signed_expression(times, 250, math.pi / 5, 1)
    corrected_phase = math.pi / 5 + math.pi / 2
    corrected = signed_expression(times, 250, corrected_phase, 1)
    assert np.max(np.abs(raw - wrong)) > 0.5
    budget = sample_error_budget(times, 4346, math.pi / 5, 250, corrected_phase)
    assert_allclose(raw, corrected, rtol=0, atol=budget)


@pytest.mark.parametrize("frequency", [0.0, FS / 2])
def test_dc_and_nyquist_do_not_identify_amplitude_and_phase_separately(frequency):
    times = sample_times(128, FS)
    # 2*cos(pi/3) = 1*cos(0) = 1 exactly; the envelope is unchanged.
    first = ringdown_signal(
        times,
        amplitude=2,
        frequency_hz=frequency,
        decay_time_s=TAU,
        phase_rad=math.pi / 3,
    )
    second = ringdown_signal(
        times, amplitude=1, frequency_hz=frequency, decay_time_s=TAU, phase_rad=0
    )
    budget = 2 * sample_error_budget(times, frequency, math.pi / 3, frequency, 0)
    assert_allclose(first, second, rtol=0, atol=budget)


def test_zero_amplitude_does_not_identify_frequency_decay_or_phase():
    times = sample_times(128, FS)
    first = ringdown_signal(
        times, amplitude=0, frequency_hz=250, decay_time_s=0.008, phase_rad=0.1
    )
    second = ringdown_signal(
        times, amplitude=0, frequency_hz=4346, decay_time_s=0.02, phase_rad=-0.7
    )
    assert_array_equal(first, np.zeros(128))
    assert_array_equal(second, np.zeros(128))
