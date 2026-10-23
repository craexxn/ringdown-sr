"""Bounded alias diagnostics using rational enclosures of mathematical pi."""

import math
from dataclasses import dataclass
from fractions import Fraction
from functools import cache

PI_TERM_BUDGETS = (16, 32, 64)


def _rational(value, name="value") -> Fraction:
    if type(value) not in (int, Fraction):
        raise TypeError(
            f"{name} must be an int or Fraction; encode Float64 bits explicitly."
        )
    return Fraction(value)


def _ratio(value: Fraction) -> dict:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


@dataclass(frozen=True)
class Phase:
    """Declare either exact rational radians or an exact rational multiple of pi."""

    kind: str
    value: Fraction

    def __post_init__(self):
        if self.kind not in ("radian_rational", "pi_multiple"):
            raise ValueError("Unknown phase kind.")
        object.__setattr__(self, "value", _rational(self.value, "phase value"))

    def to_dict(self) -> dict:
        return {"kind": self.kind, "value": _ratio(self.value)}


@dataclass(frozen=True)
class _Interval:
    low: Fraction
    high: Fraction

    def __post_init__(self):
        if self.low > self.high:
            raise ValueError("Reversed interval.")

    @classmethod
    def point(cls, value):
        return cls(Fraction(value), Fraction(value))

    def add(self, other):
        return _Interval(self.low + other.low, self.high + other.high)

    def scale(self, factor):
        endpoints = self.low * factor, self.high * factor
        return _Interval(min(endpoints), max(endpoints))

    def divide(self, other):
        if other.low <= 0 <= other.high:
            raise ZeroDivisionError("Interval denominator includes zero.")
        endpoints = [
            a / b for a in (self.low, self.high) for b in (other.low, other.high)
        ]
        return _Interval(min(endpoints), max(endpoints))

    def absolute(self):
        if self.low >= 0:
            return self
        if self.high <= 0:
            return self.scale(-1)
        return _Interval(Fraction(0), max(-self.low, self.high))


def _atan_interval(x: Fraction, terms: int) -> _Interval:
    partial = sum(
        ((-1) ** j * x ** (2 * j + 1) / (2 * j + 1) for j in range(terms)), Fraction(0)
    )
    following = partial + (-1) ** terms * x ** (2 * terms + 1) / (2 * terms + 1)
    return _Interval(min(partial, following), max(partial, following))


@cache
def _pi_interval(terms: int) -> _Interval:
    if type(terms) is not int or not 1 <= terms <= PI_TERM_BUDGETS[-1]:
        raise ValueError("Pi series budget must be between 1 and 64 terms.")
    first = _atan_interval(Fraction(1, 5), terms).scale(16)
    second = _atan_interval(Fraction(1, 239), terms).scale(-4)
    return first.add(second)


def _unresolved(reason):
    return {"value": None, "status": "numerical_unresolved", "reason": reason}


def _float_field(interval: _Interval) -> dict:
    """Certify a unique finite Float64 rounding cell, conservatively excluding ties."""
    if interval.low == interval.high == 0:
        return {"value": 0.0, "status": "available", "reason": None}
    try:
        value = float((interval.low + interval.high) / 2)
    except OverflowError:
        return _unresolved("outside_float64_range")
    if not math.isfinite(value):
        return _unresolved("outside_float64_range")
    if value == 0:
        return _unresolved("rounded_to_zero")
    exact = Fraction.from_float(value)
    previous = math.nextafter(value, -math.inf)
    following = math.nextafter(value, math.inf)
    lower = (
        (Fraction.from_float(previous) + exact) / 2
        if math.isfinite(previous)
        else exact - (Fraction.from_float(following) - exact) / 2
    )
    upper = (
        (exact + Fraction.from_float(following)) / 2
        if math.isfinite(following)
        else exact + (exact - Fraction.from_float(previous)) / 2
    )
    if not lower < interval.low or not interval.high < upper:
        return _unresolved("rounding_boundary")
    return {"value": value, "status": "available", "reason": None}


def rational_field(value: Fraction) -> dict:
    """Convert an exact rational, without calling a rounded zero an exact zero."""
    return _float_field(_Interval.point(_rational(value)))


def angular_frequency_fields(value: Fraction) -> dict:
    """Derive signed/absolute Hz fields using mathematical pi, not float(pi)."""
    value = _rational(value)
    for terms in PI_TERM_BUDGETS:
        frequency = _Interval.point(value).divide(_pi_interval(terms).scale(2))
        fields = {
            "signed": _float_field(frequency),
            "absolute": _float_field(frequency.absolute()),
            "pi_terms": terms,
        }
        if all(fields[k]["status"] == "available" for k in ("signed", "absolute")):
            break
    return fields


def _unique_floor(interval):
    lower, upper = math.floor(interval.low), math.floor(interval.high)
    return lower if lower == upper else None


def reduce_alias(
    *, sample_rate_hz, phase: Phase, frequency_hz=None, angular_frequency_per_s=None
) -> dict:
    """Reduce a declared exact frequency and phase for t[j]=j/fs, within a fixed budget.

    Exactly one frequency representation is required. Integer/Fraction values
    are accepted; callers must explicitly encode floating-point input bits.
    Availability certifies conversion, not numerical replay or identifiability.
    """
    fs = _rational(sample_rate_hz, "sample_rate_hz")
    if fs <= 0:
        raise ValueError("sample_rate_hz must be positive.")
    if type(phase) is not Phase:
        raise TypeError("An explicit Phase is required.")
    if (frequency_hz is None) == (angular_frequency_per_s is None):
        raise ValueError("Exactly one frequency representation is required.")
    hz_input = frequency_hz is not None
    value = _rational(
        frequency_hz if hz_input else angular_frequency_per_s, "frequency"
    )
    result = {
        "format": "ringdown-sr-alias-reduction-1",
        "frequency_input": {
            "kind": "hz_rational" if hz_input else "angular_rational",
            "value": _ratio(value),
        },
        "phase_input": phase.to_dict(),
        "sample_rate_hz_exact": _ratio(fs),
        "convention": "t[j]=j/fs; q in [-fs/2,fs/2); phase in [-pi,pi)",
        "status": "numerical_unresolved",
        "reason": "frequency_folding_unresolved",
        "frequency_alias_hz": _unresolved("frequency_folding_unresolved"),
        "phase_alias_rad": _unresolved("phase_reduction_unresolved"),
        "frequency_turns": None,
        "orientation": None,
        "phase_turns": None,
        "phase_alias_exact": None,
        "degeneracy": "undetermined",
    }
    for terms in PI_TERM_BUDGETS:
        pi = _pi_interval(terms)
        result["pi_terms"] = terms
        frequency = (
            _Interval.point(value)
            if hz_input
            else _Interval.point(value).divide(pi.scale(2))
        )
        turns = _unique_floor(
            frequency.scale(1 / fs).add(_Interval.point(Fraction(1, 2)))
        )
        if turns is None:
            continue
        result["frequency_turns"] = str(turns)
        remainder = frequency.add(_Interval.point(-turns * fs))
        if remainder.high < 0:
            orientation = -1
        elif remainder.low >= 0:
            orientation = 1
        else:
            result["reason"] = "frequency_orientation_unresolved"
            continue
        result["orientation"] = orientation
        absolute = remainder.absolute()
        if absolute.low == absolute.high == 0:
            degeneracy = "dc"
        elif absolute.low == absolute.high == fs / 2:
            degeneracy = "nyquist"
        elif 0 < absolute.low and absolute.high < fs / 2:
            degeneracy = "none"
        else:
            degeneracy = "undetermined"
        result["degeneracy"] = degeneracy
        frequency_field = _float_field(absolute)
        if degeneracy == "none" and frequency_field["reason"] == "rounded_to_zero":
            frequency_field = _unresolved("boundary_rounding")
        if (
            frequency_field["status"] == "available"
            and degeneracy == "none"
            and Fraction.from_float(frequency_field["value"]) in (0, fs / 2)
        ):
            frequency_field = _unresolved("boundary_rounding")
        result["frequency_alias_hz"] = frequency_field
        signed_phase = orientation * phase.value
        if phase.kind == "pi_multiple":
            phase_turns = math.floor(signed_phase / 2 + Fraction(1, 2))
            radian_part, pi_part = Fraction(0), signed_phase - 2 * phase_turns
        else:
            phase_turns = _unique_floor(
                _Interval.point(signed_phase)
                .divide(pi.scale(2))
                .add(_Interval.point(Fraction(1, 2)))
            )
            if phase_turns is None:
                result["reason"] = "phase_reduction_unresolved"
                continue
            radian_part, pi_part = signed_phase, Fraction(-2 * phase_turns)
        result["phase_turns"] = str(phase_turns)
        result["phase_alias_exact"] = {
            "radian_part": _ratio(radian_part),
            "pi_multiple": _ratio(pi_part),
        }
        normalized_phase = _Interval.point(radian_part).add(pi.scale(pi_part))
        phase_field = _float_field(normalized_phase)
        if phase_field["status"] == "available":
            rounded_phase = Fraction.from_float(phase_field["value"])
            if not -pi.low <= rounded_phase < pi.low:
                phase_field = _unresolved("boundary_rounding")
        result["phase_alias_rad"] = phase_field
        if frequency_field["status"] != "available":
            result["reason"] = frequency_field["reason"]
        elif phase_field["status"] != "available":
            result["reason"] = phase_field["reason"]
        elif degeneracy == "undetermined":
            result["reason"] = "frequency_boundary_unresolved"
        else:
            result.update(status="available", reason=None)
            return result
    return result
