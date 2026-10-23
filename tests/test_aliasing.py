"""Independent rational references for bounded frequency/phase reduction."""

import json
import math
import sys
from dataclasses import FrozenInstanceError
from fractions import Fraction

import pytest
from test_alias_references import REFERENCES

from ringdown_sr.aliasing import (
    Phase,
    _atan_interval,
    _float_field,
    _Interval,
    _pi_interval,
    angular_frequency_fields,
    rational_field,
    reduce_alias,
)


def ratio(record):
    return Fraction(int(record["numerator"]), int(record["denominator"]))


def test_machin_identity_has_an_independent_exact_tangent_witness():
    # tan(2 atan(1/5))=5/12; tan(4 atan(1/5))=120/119.
    twice = 2 * Fraction(1, 5) / (1 - Fraction(1, 5) ** 2)
    four = 2 * twice / (1 - twice**2)
    assert twice == Fraction(5, 12) and four == Fraction(120, 119)
    assert (four - Fraction(1, 239)) / (1 + four / 239) == 1
    # 0 < 4 atan(1/5)-atan(1/239) < 4/5 < pi/2 selects pi/4.
    assert 4 * Fraction(74, 375) - Fraction(1, 239) > 0


def test_alternating_bounds_and_pi_enclosures():
    first = _atan_interval(Fraction(1, 5), 1)
    second = _atan_interval(Fraction(1, 5), 2)
    assert (first.low, first.high) == (Fraction(74, 375), Fraction(1, 5))
    assert (second.low, second.high) == (
        Fraction(74, 375),
        Fraction(74, 375) + Fraction(1, 15625),
    )
    # Independent 100-digit decimal enclosure, much narrower than 64 terms.
    decimal_low = Fraction(
        "3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679"
    )
    decimal_high = decimal_low + Fraction(1, 10**100)
    previous = _Interval(Fraction(3), Fraction(4))
    for terms in (1, 2, 3, 16, 32, 64):
        current = _pi_interval(terms)
        assert previous.low <= current.low < decimal_low
        assert decimal_high < current.high <= previous.high
        previous = current
    assert previous.high - previous.low < Fraction(1, 10**90)


@pytest.mark.parametrize("terms", [0, 65, True, 16.0])
def test_pi_budget_is_bounded(terms):
    with pytest.raises(ValueError):
        _pi_interval(terms)


@pytest.mark.parametrize(
    "value",
    [
        0,
        1,
        -1,
        Fraction(1, 3),
        Fraction.from_float(5e-324),
        Fraction.from_float(sys.float_info.max),
    ],
)
def test_rational_float_fields_are_finite_and_round_trip(value):
    field = rational_field(value)
    assert field == {"value": float(value), "status": "available", "reason": None}
    json.dumps(field, allow_nan=False)


@pytest.mark.parametrize("sign", [-1, 1])
def test_rounding_ties_underflow_and_overflow_are_explicit(sign):
    halfway = sign * (Fraction(1) + Fraction(1, 2**53))
    assert rational_field(halfway)["reason"] == "rounding_boundary"
    assert rational_field(sign * Fraction(1, 2**1075))["reason"] == "rounded_to_zero"
    assert rational_field(sign * Fraction(10**400))["reason"] == "outside_float64_range"
    # Either side of a tie is uniquely representable within one rounding cell.
    assert rational_field(halfway - sign * Fraction(1, 2**100))["value"] == sign
    assert rational_field(halfway + sign * Fraction(1, 2**100))[
        "value"
    ] == sign * math.nextafter(1.0, math.inf)


def test_the_entire_enclosure_must_fit_a_single_rounding_cell():
    spanning = _Interval(Fraction(1), Fraction(1) + Fraction(3, 2**53))
    assert _float_field(spanning)["reason"] == "rounding_boundary"
    inside = _Interval(
        Fraction(1) - Fraction(1, 2**100), Fraction(1) + Fraction(1, 2**100)
    )
    assert _float_field(inside)["value"] == 1


@pytest.mark.parametrize("reference", REFERENCES)
def test_existing_hz_references_use_the_original_exact_pi_multiple(reference):
    report = reduce_alias(
        sample_rate_hz=4096,
        frequency_hz=Fraction.from_float(float(reference.raw_hz)),
        phase=Phase("pi_multiple", reference.raw_phase_pi),
    )
    assert report["status"] == "available"
    assert report["frequency_alias_hz"]["value"] == reference.alias_hz
    assert report["orientation"] == reference.orientation
    exact = report["phase_alias_exact"]
    assert ratio(exact["radian_part"]) == 0
    assert ratio(exact["pi_multiple"]) == reference.alias_phase_pi
    assert (
        report["phase_alias_rad"]["value"] == float(reference.alias_phase_pi) * math.pi
    )
    raw = Fraction.from_float(float(reference.raw_hz))
    assert raw - int(
        report["frequency_turns"]
    ) * 4096 == reference.orientation * Fraction.from_float(float(reference.alias_hz))
    expected = (
        "dc"
        if reference.alias_hz == 0
        else "nyquist"
        if reference.alias_hz == 2048
        else "none"
    )
    assert report["degeneracy"] == expected
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize("sign", [-1, 1])
@pytest.mark.parametrize("orientation", [-1, 1])
@pytest.mark.parametrize("neighbor", [-1, 0, 1])
def test_binary_radian_pi_neighbors_have_independent_integer_quotients(
    sign, orientation, neighbor
):
    positive = (
        math.pi
        if neighbor == 0
        else math.nextafter(math.pi, 0 if neighbor < 0 else math.inf)
    )
    phase = Fraction.from_float(sign * positive)
    report = reduce_alias(
        sample_rate_hz=4096,
        frequency_hz=orientation * 250,
        phase=Phase("radian_rational", phase),
    )
    expected_turns = sign * orientation if neighbor == 1 else 0
    assert int(report["phase_turns"]) == expected_turns
    assert report["status"] == "available"
    exact = report["phase_alias_exact"]
    assert ratio(exact["radian_part"]) == orientation * phase
    assert ratio(exact["pi_multiple"]) == -2 * expected_turns
    assert report["phase_input"]["kind"] == "radian_rational"


@pytest.mark.parametrize(
    "phase,orientation,turns,coefficient",
    [(1, 1, 1, -1), (1, -1, 0, -1), (-1, 1, 0, -1), (-1, -1, 1, -1)],
)
def test_exact_pi_endpoints_remain_distinct_from_binary_radians(
    phase, orientation, turns, coefficient
):
    report = reduce_alias(
        sample_rate_hz=4096,
        frequency_hz=orientation * 250,
        phase=Phase("pi_multiple", phase),
    )
    assert report["status"] == "available"
    assert report["phase_turns"] == str(turns)
    assert ratio(report["phase_alias_exact"]["pi_multiple"]) == coefficient
    assert report["phase_alias_rad"]["value"] == -math.pi


@pytest.mark.parametrize("sign", [-1, 1])
@pytest.mark.parametrize("neighbor", [-1, 0, 1])
def test_angular_nyquist_is_not_a_hz_declaration(sign, neighbor):
    center = 2 * math.pi * 2048
    c = (
        center
        if neighbor == 0
        else math.nextafter(center, 0 if neighbor < 0 else math.inf)
    )
    report = reduce_alias(
        sample_rate_hz=4096,
        angular_frequency_per_s=Fraction.from_float(sign * c),
        phase=Phase("radian_rational", 0),
    )
    assert report["degeneracy"] == "none"
    assert report["orientation"] == (sign if neighbor <= 0 else -sign)
    assert report["frequency_turns"] == ("0" if neighbor <= 0 else str(sign))
    if neighbor == 0:
        assert (
            angular_frequency_fields(Fraction.from_float(sign * c))["absolute"]["value"]
            == 2048
        )
        assert report["status"] == "numerical_unresolved"
        assert report["frequency_alias_hz"] == {
            "value": None,
            "status": "numerical_unresolved",
            "reason": "boundary_rounding",
        }
    else:
        assert report["status"] == "available"
        assert 0 < report["frequency_alias_hz"]["value"] < 2048


@pytest.mark.parametrize("tiny", [Fraction(1, 2**1075), -Fraction(1, 2**1075)])
def test_inner_alias_cannot_become_an_exact_dc(tiny):
    report = reduce_alias(
        sample_rate_hz=4096, frequency_hz=tiny, phase=Phase("pi_multiple", 0)
    )
    assert report["status"] == "numerical_unresolved"
    assert report["frequency_alias_hz"]["value"] is None
    assert report["frequency_alias_hz"]["reason"] == "boundary_rounding"
    assert report["degeneracy"] == "none"


def test_extreme_angles_exhaust_the_budget_without_a_modulo_fallback():
    frequency = reduce_alias(
        sample_rate_hz=4096,
        angular_frequency_per_s=10**300,
        phase=Phase("radian_rational", 0),
    )
    phase = reduce_alias(
        sample_rate_hz=4096, frequency_hz=250, phase=Phase("radian_rational", 10**300)
    )
    for report in (frequency, phase):
        assert report["status"] == "numerical_unresolved" and report["pi_terms"] == 64
        json.dumps(report, allow_nan=False)
    assert frequency["frequency_turns"] is None
    assert phase["frequency_alias_hz"]["value"] == 250
    assert phase["phase_turns"] is None
    # Explicit pi multiples cancel symbolically even with a huge exact quotient.
    declared = reduce_alias(
        sample_rate_hz=4096,
        frequency_hz=250,
        phase=Phase("pi_multiple", 2 * 10**300 + Fraction(1, 4)),
    )
    assert declared["status"] == "available"
    assert declared["phase_turns"] == str(10**300)
    assert ratio(declared["phase_alias_exact"]["pi_multiple"]) == Fraction(1, 4)


def test_refinement_recovers_small_remainders_and_tighter_rounding_cells():
    # A rational 31-digit approximation to pi is deliberately near its boundary.
    phase = Fraction("3.141592653589793238462643383279")
    report = reduce_alias(
        sample_rate_hz=4096, frequency_hz=250, phase=Phase("radian_rational", phase)
    )
    assert report["phase_turns"] == "0" and report["pi_terms"] >= 32
    angular = angular_frequency_fields(Fraction(1, 3))
    assert angular["signed"]["value"] == pytest.approx(1 / (6 * math.pi), rel=1e-15)


def test_declared_input_contracts_and_phase_immutability():
    phase = Phase("radian_rational", Fraction(1, 4))
    with pytest.raises(FrozenInstanceError):
        phase.value = Fraction(1)
    for invalid in (0.25, True, "1/4"):
        with pytest.raises(TypeError):
            Phase("radian_rational", invalid)
        with pytest.raises(TypeError):
            rational_field(invalid)
    with pytest.raises(ValueError):
        Phase("guess_pi", 1)
    base = {"sample_rate_hz": 4096, "phase": phase}
    for frequencies in ({}, {"frequency_hz": 1, "angular_frequency_per_s": 1}):
        with pytest.raises(ValueError):
            reduce_alias(**base, **frequencies)
    for invalid in (4096.0, True):
        with pytest.raises(TypeError):
            reduce_alias(sample_rate_hz=invalid, phase=phase, frequency_hz=1)
    with pytest.raises(ValueError):
        reduce_alias(sample_rate_hz=0, phase=phase, frequency_hz=1)
    with pytest.raises(TypeError):
        reduce_alias(
            sample_rate_hz=4096,
            phase={"kind": "pi_multiple", "value": 1},
            frequency_hz=1,
        )
