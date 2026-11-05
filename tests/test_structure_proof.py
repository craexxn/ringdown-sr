"""Manufactured mathematical identities, strict original domains and proof limits."""

import copy
import json
import math
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import gmpy2
import pytest
import sympy as sp

from ringdown_sr.structure import InvalidTreeError
from ringdown_sr.structure_algebra import (
    LIMITS,
    ONE,
    PI,
    TIME,
    ZERO,
    Algebra,
    Unresolved,
)
from ringdown_sr.structure_assessment import bound_interval, interval_binding
from ringdown_sr.structure_proof import assess_structure

CASES = json.loads(
    (
        Path(__file__).parent / "fixtures/assessment/preparation_structure_cases.json"
    ).read_text()
)["cases"]
BY_ID = {c["id"]: c for c in CASES}
FIELDS = ("algebraic_identity", "domain", "original_family", "continuous_extension")


def q(value):
    return {"kind": "constant", "value_hex": float(value).hex()}


T = {"kind": "variable", "index": 1}


def op(name, *children):
    names = ("exp", "sin", "cos") if len(children) == 1 else ("+", "-", "*", "/")
    return {
        "kind": "operator",
        "operator": name,
        "arity": len(children),
        "operator_index": names.index(name) + 1,
        "children": list(children),
    }


def sym_exact(record):
    if record["kind"] == "rational":
        return sp.Rational(
            int(record["numerator_hex"], 16), int(record["denominator_hex"], 16)
        )
    args = [sym_exact(a) for a in record["children"]]
    return {
        "add": lambda: sp.Add(*args),
        "mul": lambda: sp.Mul(*args),
        "inv": lambda: 1 / args[0],
        "exp": lambda: sp.exp(args[0]),
        "sin": lambda: sp.sin(args[0]),
        "cos": lambda: sp.cos(args[0]),
        "pi": lambda: sp.pi,
        "t": lambda: sp.Symbol("t", real=True),
    }[record["kind"]]()


def original_exact(tree):
    if tree["kind"] == "constant":
        return sp.Rational(Fraction.from_float(float.fromhex(tree["value_hex"])))
    if tree["kind"] == "variable":
        return sp.Symbol("t", real=True)
    children = [original_exact(c) for c in tree["children"]]
    name = tree["operator"]
    if len(children) == 1:
        return {"exp": sp.exp, "sin": sp.sin, "cos": sp.cos}[name](*children)
    a, b = children
    return {
        "+": lambda: a + b,
        "-": lambda: a - b,
        "*": lambda: a * b,
        "/": lambda: a / b,
    }[name]()


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_preparation_domains_and_independent_symbolic_identity(case):
    tree = copy.deepcopy(case["original_tree"])
    result = assess_structure(tree, (Fraction(0), Fraction(1)))
    assert tree == case["original_tree"]
    json.dumps(result, allow_nan=False)
    allowed = case["implementation_expectation"]["conservative_unresolved_allowed"]
    for field in FIELDS:
        expected = case["mathematical_expectation"][field]
        actual = result[field]["status"]
        assert actual == expected or (allowed and actual == "unresolved"), (
            field,
            result,
        )
    if result["algebraic_identity"]["status"] == "proven_on_original_domain":
        coefficients = {
            name: sym_exact(value)
            for name, value in result["coefficients_exact"].items()
        }
        t = sp.Symbol("t", real=True)
        expression = sp.exp(-coefficients["gamma"] * t) * (
            coefficients["a"] * sp.cos(coefficients["omega"] * t)
            + coefficients["b"] * sp.sin(coefficients["omega"] * t)
        )
        # CAS is an independent oracle for these manufactured fixed identities,
        # never a production decision source or a domain oracle.
        assert sp.simplify(sp.expand_trig(original_exact(tree) - expression)) == 0
        assert result["proof_trace"]
    assert result["new_parameter_match"]["status"] == "not_assessed"
    assert result["remainder"]["status"] == "not_assessed"


@pytest.mark.parametrize(
    "endpoint,position,direction",
    [(0, "left_endpoint", "right"), (1, "right_endpoint", "left")],
)
def test_endpoint_holes_require_one_sided_extensions(endpoint, position, direction):
    tree = op(
        "*",
        op("/", op("-", T, q(endpoint)), op("-", T, q(endpoint))),
        op("*", op("exp", op("*", q(-1), T)), op("cos", T)),
    )
    result = assess_structure(tree, (0, 1))
    assert result["original_family"]["status"] == "proven_nonmember"
    assert result["continuous_extension"]["status"] == "proven_member"
    assert result["domain"]["exclusions"][0]["position"] == position
    assert result["domain"]["exclusions"][0]["proof"]["direction"] == direction


def test_known_hole_does_not_hide_an_unresolved_second_denominator():
    unknown = op("+", op("sin", op("*", T, T)), q(0.1))
    tree = op("/", op("/", T, T), unknown)
    result = assess_structure(tree, (-1, 1))
    assert result["domain"]["status"] == "unresolved"
    assert result["domain"]["exclusions"]
    assert result["continuous_extension"]["status"] == "unresolved"
    assert result["algebraic_identity"]["status"] == "unresolved"


def test_overwide_denominator_interval_is_not_a_zero_certificate():
    # 1+(t*t) is positive, but interval multiplication on [-1,1] includes zero.
    result = assess_structure(op("/", q(1), op("+", q(1), op("*", T, T))), (-1, 1))
    assert result["domain"]["status"] == "unresolved"
    assert result["domain"]["exclusions"] == []
    assert result["original_family"]["status"] == "unresolved"


def test_mixed_hole_and_pole_remain_separate():
    tree = op("*", op("/", T, T), op("/", q(1), op("-", T, q(0.5))))
    result = assess_structure(tree, (0, 1))
    assert result["domain"]["status"] == "mixed"
    assert {r["kind"] for r in result["domain"]["exclusions"]} == {
        "removable",
        "nonremovable",
    }
    assert result["continuous_extension"]["status"] == "proven_nonmember"


@pytest.mark.parametrize("name", ["S016", "S017", "S030"])
def test_zero_and_nowhere_defined_are_not_positive(name):
    result = assess_structure(BY_ID[name]["original_tree"], (0, 1))
    assert result["algebraic_identity"]["status"] != "proven_on_original_domain"
    assert result["continuous_extension"]["status"] != "proven_member"


@pytest.mark.parametrize("name", ["S018", "S019", "S020", "S021", "S034"])
def test_unsupported_forms_are_not_negative_pattern_matches(name):
    result = assess_structure(BY_ID[name]["original_tree"], (0, 1))
    assert result["algebraic_identity"]["status"] == "unresolved"
    assert result["original_family"]["status"] == "unresolved"


@pytest.mark.parametrize(
    "field,value",
    [("steps", 1), ("nodes", 2), ("terms", 1), ("roots", 1), ("rational_bits", 8)],
)
def test_declared_resource_exhaustion_never_creates_a_positive_result(field, value):
    tree = BY_ID["S022"]["original_tree"]
    if field == "terms":
        tree = BY_ID["S011"]["original_tree"]
    result = assess_structure(tree, (0, 10), limits=replace(LIMITS, **{field: value}))
    assert result["original_family"]["status"] != "proven_member"
    assert result["continuous_extension"]["status"] != "proven_member"


def test_constant_sign_enclosure_including_zero_stays_unknown():
    algebra = Algebra()
    # The exact identity sin(1)-sin(1) is intentionally not normalized here.
    value = algebra.node(
        "add",
        algebra.node("sin", ONE),
        algebra.node("mul", algebra.q(-1), algebra.node("sin", ONE)),
    )
    with pytest.raises(Unresolved):
        algebra.sign(value)


@pytest.mark.parametrize("exponent", [1000000, -1000000])
def test_mpfr_range_exhaustion_is_unresolved(exponent):
    tree = op("*", op("exp", q(exponent)), BY_ID["S001"]["original_tree"])
    result = assess_structure(tree, (0, 1))
    assert result["original_family"]["status"] == "unresolved"
    assert result["algebraic_identity"]["status"] == "unresolved"


@pytest.mark.parametrize("precision", LIMITS.precisions)
def test_directed_constant_enclosures_against_independent_high_precision_oracle(
    precision,
):
    algebra = Algebra()
    for expression, oracle in [
        (
            algebra.unary("sin", algebra.q(Fraction.from_float(math.pi))),
            lambda: gmpy2.sin(gmpy2.mpfr(math.pi)),
        ),
        (algebra.unary("cos", ONE), lambda: gmpy2.cos(gmpy2.mpfr(1))),
        (
            algebra.unary("exp", algebra.q(Fraction(-1, 3))),
            lambda: gmpy2.exp(-gmpy2.mpfr(1) / 3),
        ),
    ]:
        low, high = algebra.interval(expression, precision)
        with gmpy2.context(precision=2048):
            reference = oracle()
            assert (
                gmpy2.mpq(low.numerator, low.denominator)
                <= reference
                <= gmpy2.mpq(high.numerator, high.denominator)
            )
    # A binary64 pi constant is not the exact derived pi symbol.
    assert (
        algebra.sign(algebra.unary("sin", algebra.q(Fraction.from_float(math.pi))))[0]
        == 1
    )
    assert algebra.unary("sin", PI) == ZERO


def test_interval_extrema_and_mpfr_context_are_preserved():
    original = gmpy2.get_context().copy()
    with gmpy2.context(precision=53, round=gmpy2.RoundToZero, emax=200):
        algebra = Algebra()
        assert algebra.interval(
            algebra.unary("sin", TIME), 128, (Fraction(-2), Fraction(2))
        ) == (-1, 1)
        assert gmpy2.get_context().precision == 53
        assert gmpy2.get_context().round == gmpy2.RoundToZero
        assert gmpy2.get_context().emax == 200
    assert gmpy2.get_context().precision == original.precision


def test_invalid_hidden_node_is_rejected_before_zero_reduction():
    with pytest.raises(InvalidTreeError):
        assess_structure(op("*", q(0), {"kind": "variable", "index": True}), (0, 1))


def test_closed_training_span_uses_exact_original_samples():
    import numpy as np

    time = np.arange(128, dtype=np.float64) / 4096
    binding = interval_binding(time)
    assert bound_interval(binding) == (0, Fraction(127, 4096))
    assert bound_interval(binding)[1] != Fraction(128, 4096)
    for invalid in (
        time[::-1],
        np.array([0, 1]),
        np.array([0.0, float("nan")]),
        np.array([1.0, 1.0]),
    ):
        with pytest.raises(ValueError):
            interval_binding(invalid)
