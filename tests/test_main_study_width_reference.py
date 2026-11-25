"""Regress the original N103 width failure independently of any search or noise."""

import math
from fractions import Fraction

import numpy as np
import pytest

from ringdown_sr import confirmed_profile, prediction_reference
from ringdown_sr.symbolic import evaluate_tree

# Manjaro 001 / signal_200_4ms-ar1-16 / estimated_64s / member-04.
# Exact native CSV rows 11 and 5 in the diagnosis archive
# b0d733dcdc95d22559a0322bc3311b25d152f7a13591b7b8c5d3c3ccce9bc066.
SENSITIVE = (
    "cos((-1493.0512231398136 + exp(0.26964692692527875 * exp(t * "
    "212.92052381852446))) * (t * -0.8387893432849028)) / exp(247.5514599633466 * t)"
)
STABLE = "cos(1251.905122634334 * t) / exp(253.40272372087964 * t)"
TIMES = np.arange(103, dtype=np.float64) / 4096


def test_sensitive_front_member_remains_indeterminate_with_identical_predictions():
    tree = confirmed_profile.equation_tree(SENSITIVE)
    values = evaluate_tree(tree, TIMES)
    with pytest.raises(prediction_reference.PredictionVerificationError) as caught:
        prediction_reference.verify_prediction(tree, TIMES, values, values)
    evidence = caught.value.evidence
    assert evidence["status"] == "indeterminate"
    assert evidence["reason"] == "reference_width_exceeds_bound"
    assert evidence["membership"]["status"] == "not_attempted"

    # Independently evaluated by changing only the inner exp result at t=96/4096
    # from nearest-even to its lower binary64 neighbor (all other nodes nearest).
    # These are model-permitted witnesses, not historical Python/Julia values.
    witness_low = float.fromhex("-0x1.1301dae9453d4p-9")
    witness_high = float.fromhex("0x1.83b2382ec4880p-9")
    lower, upper = map(float.fromhex, evidence["intervals_hex"][96])
    assert lower <= witness_low < witness_high <= upper
    # |cos| <= 1 and the denominator is at least prevfloat(1) at every sample.
    scale_bound = Fraction.from_float(math.nextafter(1.0, math.inf))
    witness_width = Fraction(witness_high) - Fraction(witness_low)
    assert witness_width**2 > Fraction(1, 2**53) * scale_bound**2


def test_stable_front_member_passes_but_outside_native_prediction_is_a_mismatch():
    tree = confirmed_profile.equation_tree(STABLE)
    scalar = [
        math.cos(1251.905122634334 * t) / math.exp(253.40272372087964 * t)
        for t in TIMES
    ]
    assert (
        prediction_reference.verify_prediction(tree, TIMES, scalar, scalar)["status"]
        == "passed"
    )
    wrong = scalar.copy()
    # At t=0, even a valid one-neighbor variation in exp(0) bounds the
    # quotient by nextfloat(1). Step beyond that absolute maximum.
    wrong[0] = math.nextafter(math.nextafter(1.0, math.inf), math.inf)
    with pytest.raises(prediction_reference.PredictionVerificationError) as caught:
        prediction_reference.verify_prediction(tree, TIMES, scalar, wrong)
    assert caught.value.evidence["status"] == "failed"
    assert caught.value.evidence["reason"] == "prediction_outside_reference"
    assert caught.value.evidence["membership"]["failures"] == {"native": [0]}
