"""Bind the structure policy and the verified original training interval."""

from dataclasses import asdict
from fractions import Fraction
from pathlib import Path

import gmpy2
import numpy as np

from .structure_algebra import LIMITS, rational_record
from .structure_proof import FORMAT, assess_structure

ROOT = Path(__file__).resolve().parents[2]
FILES = ("data/structure_assessment_v1.json", "docs/supplemental_structure.md")
POLICY = {
    "format": FORMAT,
    "stage": 2,
    "interval": "closed_verified_training_span_in_physical_seconds",
    "constants": "exact_binary64_rationals_and_symbolic_real_expressions",
    "family": "exp(-gamma*t)*(a*cos(omega*t)+b*sin(omega*t)); gamma>0; omega>0; a*a+b*b>0",
    "limits": {**asdict(LIMITS), "precisions": list(LIMITS.precisions)},
    "rules": [
        "exact_ring_and_exponential_identities",
        "affine_exponential_and_trigonometric_addition",
        "original_denominators_before_cancellation",
        "complete_affine_and_trigonometric_zero_sets",
        "directed_mpfr_sign",
        "continuous_normal_form_on_dense_original_domain",
        "nonzero_numerator_over_simple_zero",
        "single_mode_uniqueness",
    ],
    "unresolved_is_nonmember": False,
    "remainder": "not_assessed",
    "new_parameter_match": "not_assessed",
}


def check_policy(raw):
    from .assessment_sources import _same, read_json

    _same(read_json(raw), POLICY, "Unsupported structure proof policy.")


def runtime():
    return {
        "gmpy2": gmpy2.version(),
        "mpfr": gmpy2.mpfr_version(),
        "gmp": gmpy2.mp_version(),
    }


def training_interval(time):
    values = np.asarray(time)
    if (
        values.dtype != np.dtype("float64")
        or values.ndim != 1
        or len(values) < 2
        or not np.all(np.isfinite(values))
        or not np.all(values[1:] > values[:-1])
    ):
        raise ValueError(
            "Structure assessment requires finite strictly increasing Float64 training times."
        )
    return tuple(Fraction.from_float(float(x)) for x in (values[0], values[-1]))


def interval_binding(time):
    return {
        "unit": "seconds",
        "closed": [True, True],
        "endpoints": [rational_record(x) for x in training_interval(time)],
    }


def bound_interval(binding):
    if (
        set(binding) != {"unit", "closed", "endpoints"}
        or binding["unit"] != "seconds"
        or binding["closed"] != [True, True]
        or len(binding["endpoints"]) != 2
    ):
        raise ValueError("Invalid structure interval binding.")
    values = []
    for endpoint in binding["endpoints"]:
        if set(endpoint) != {"numerator_hex", "denominator_hex"}:
            raise ValueError("Invalid exact endpoint.")
        value = Fraction(
            int(endpoint["numerator_hex"], 16), int(endpoint["denominator_hex"], 16)
        )
        if rational_record(value) != endpoint:
            raise ValueError("Noncanonical exact endpoint.")
        values.append(value)
    if values[0] >= values[1]:
        raise ValueError("Empty structure interval.")
    return tuple(values)


def supplement(record, binding):
    proof = assess_structure(
        record["original_candidate"]["tree"], bound_interval(binding)
    )
    proof["structure_proof_format"] = proof.pop("format")
    record["supplemental"].update(proof)


def status_counts(records):
    from collections import Counter

    return {
        name + "_status_counts": dict(
            Counter(r["supplemental"][name]["status"] for r in records)
        )
        for name in (
            "algebraic_identity",
            "domain",
            "original_family",
            "continuous_extension",
        )
    }
