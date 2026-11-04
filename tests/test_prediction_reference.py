"""Independent arithmetic, range and membership counterexamples for duration 4."""

import copy
import json
import math
import sys
from fractions import Fraction as F
from pathlib import Path

import gmpy2
import numpy as np
import pytest
from test_structure import constant as c
from test_structure import operator as op
from test_structure import time_node as t

from ringdown_sr import prediction_reference as ref
from ringdown_sr import symbolic
from ringdown_sr.duration_replay import candidate_evidence, verify_loss_replay
from ringdown_sr.losses import mean_squared_error
from ringdown_sr.parameters import _prediction_replay

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures/duration_prediction_cases.json").read_bytes()
)


def interval(tree, times=(0.0,)):
    result = ref.reference(tree, times)
    assert result["status"] == "bounded", result
    return [[float.fromhex(v) for v in p] for p in result["intervals_hex"]]


@pytest.mark.parametrize("precision", ref.PRECISIONS)
@pytest.mark.parametrize(
    "a,b,expected",
    [
        (1.0, 2.0**-53, 1.0),
        (1.0 + 2.0**-52, 2.0**-53, 1.0 + 2.0**-51),
        (2.0 - 2.0**-52, 2.0**-53, 2.0),
        (0.0, 0.0, 0.0),
        (2.0**-1074, 2.0**-1074, 2.0**-1073),
        (2.0**1023, -(2.0**1023), 0.0),
    ],
)
def test_nearest_even_boundaries_with_exact_halfway_inputs(precision, a, b, expected):
    assert ref._intervals(
        ref._validated_tree(op("+", c(a), c(b))), [0.0], precision
    ) == [(F(expected), F(expected))]


@pytest.mark.parametrize("sign", [-1, 1])
def test_gradual_underflow_ties_and_binade_crossing(sign):
    smallest = sign * 2.0**-1074
    assert interval(op("/", c(smallest), c(2))) == [[0.0, 0.0]]
    assert interval(op("/", c(3 * smallest), c(2))) == [[2 * smallest, 2 * smallest]]
    assert interval(
        op("-", c(sys.float_info.min), c(smallest if sign == 1 else -smallest))
    ) == [[math.nextafter(sys.float_info.min, 0.0)] * 2]


def test_original_node_order_is_not_an_unrounded_or_fused_function():
    tree = op("+", op("-", op("-", t(), c(1e16)), c(-1e16)), c(1))
    assert interval(tree, [0.0, 0.125, 0.875]) == [[1.0, 1.0]] * 3
    # (1+2^-27)*(1-2^-27)-1 rounds its product to 1 before subtraction.
    tree = op("-", op("*", c(1 + 2.0**-27), c(1 - 2.0**-27)), c(1))
    assert interval(tree) == [[0.0, 0.0]]
    with pytest.raises(ref.PredictionVerificationError):
        ref.verify_prediction(tree, [0.0], [-(2.0**-54)], [-(2.0**-54)])


@pytest.mark.parametrize("operator,center", [("exp", 1.0), ("sin", 0.0), ("cos", 1.0)])
def test_one_neighbor_and_codomain_are_exact_at_zero(operator, center):
    expected = [math.nextafter(center, -math.inf), math.nextafter(center, math.inf)]
    if operator == "cos":
        expected[1] = 1.0
    assert ref._intervals(ref._validated_tree(op(operator, c(0))), [0.0], 128) == [
        tuple(map(F, expected))
    ]


def test_known_historical_exp_rounding_binade_and_amplification():
    x = float.fromhex("-0x1.9e8846667be65p-11")
    correct = float.fromhex("0x1.ff98686aa5743p-1")
    assert interval(op("exp", c(x))) == [
        [math.nextafter(correct, -math.inf), math.nextafter(correct, math.inf)]
    ]
    record = ref.verify_prediction(
        op("exp", c(x)), [0.0], [math.nextafter(correct, 0.0)], [correct]
    )
    assert record["status"] == "passed"
    with pytest.raises(ref.PredictionVerificationError):
        ref.verify_prediction(
            op("exp", c(x)),
            [0.0],
            [math.nextafter(math.nextafter(correct, 0.0), 0.0)],
            [correct],
        )


@pytest.mark.parametrize("precision", ref.PRECISIONS)
@pytest.mark.parametrize(
    "operator,bounds,expected",
    [
        ("sin", (1.0, 2.0), 1.0),
        ("sin", (4.0, 5.0), -1.0),
        ("cos", (-1.0, 1.0), 1.0),
        ("cos", (3.0, 4.0), -1.0),
    ],
)
def test_internal_extrema_with_independent_integer_brackets(
    precision, operator, bounds, expected
):
    pi = tuple(
        ref._directed("pi", None, precision, r)
        for r in (gmpy2.RoundDown, gmpy2.RoundUp)
    )
    lo, hi = ref._transcendental(operator, tuple(map(F, bounds)), precision, pi)
    assert (hi if expected > 0 else lo) == expected


@pytest.mark.parametrize("operator", ["sin", "cos"])
@pytest.mark.parametrize(
    "bounds",
    [
        (-10.0, 10.0),
        (1e100, math.nextafter(1e100, math.inf)),
        (-1e300, -math.nextafter(1e300, 0.0)),
    ],
)
def test_many_periods_and_uncertain_huge_phase_include_both_extrema(operator, bounds):
    pi = tuple(
        ref._directed("pi", None, 128, r) for r in (gmpy2.RoundDown, gmpy2.RoundUp)
    )
    assert ref._transcendental(operator, tuple(map(F, bounds)), 128, pi) == (
        F(-1),
        F(1),
    )


@pytest.mark.parametrize("x", [-1076.0, -1e60, -sys.float_info.max])
def test_proven_extreme_exp_underflow_does_not_underflow_mpfr(x):
    assert ref._intervals(ref._validated_tree(op("exp", c(x))), [0.0], 128) == [
        (F(0), F(2.0**-1074))
    ]
    assert ref.reference(op("exp", c(x)), [0.0])["status"] == "indeterminate"
    # A finite amplitude elsewhere supplies a reference scale, no unit floor.
    assert (
        ref.verify_prediction(op("exp", t()), [x, 0.0], [0.0, 1.0], [0.0, 1.0])[
            "status"
        ]
        == "passed"
    )


@pytest.mark.parametrize(
    "tree,reason",
    [
        (op("/", c(1), c(0)), "possible_zero_denominator"),
        (op("/", c(1), op("sin", c(0))), "possible_zero_denominator"),
        (op("exp", c(1024)), "possible_binary64_overflow"),
        (op("exp", c(1e60)), "possible_binary64_overflow"),
        (op("*", c(sys.float_info.max), c(2)), "possible_binary64_overflow"),
        (op("-", op("exp", c(1)), op("exp", c(1))), "reference_width_exceeds_bound"),
    ],
)
def test_undefined_overflow_or_broad_even_when_both_predictions_agree(tree, reason):
    r = ref.reference(tree, [0.0])
    assert r["status"] == "indeterminate" and r["reason"] == reason
    assert [a["precision_bits"] for a in r["attempts"]] == list(ref.PRECISIONS)
    assert ref.membership(r, [0.0], [0.0])["status"] == "indeterminate"


@pytest.mark.parametrize("exponent", [-1000, 0, 1000])
def test_exact_width_boundary_without_float_square_overflow_or_underflow(exponent):
    scale = F(2) ** exponent
    # w <= 2^-26.5*S. Compare rational integers immediately on both sides.
    k = math.isqrt(2**147)
    inside = F(k, 2**100) * scale
    outside = F(k + 1, 2**100) * scale
    assert ref.width_check([(scale - inside, scale)])[0]
    assert not ref.width_check([(scale - outside, scale)])[0]
    assert ref.width_check([(F(0), F(0))]) == (True, F(0), F(0))


def test_precision_selection_and_scale_never_consume_predictions(monkeypatch):
    original = ref._intervals
    seen = []

    def wide_first(node, times, precision):
        seen.append(precision)
        return [(F(-1), F(1))] if precision == 128 else original(node, times, precision)

    monkeypatch.setattr(ref, "_intervals", wide_first)
    r = ref.reference(c(2), [0.0])
    assert seen == [128, 256] and r["precision_bits"] == 256
    good = ref.membership(r, [2.0], [2.0])
    bad = ref.membership(r, [3.0], [3.0])
    assert good["status"] == "passed" and bad["status"] == "failed"
    for key in ("intervals_hex", "scale", "precision_bits", "attempts"):
        assert good[key] == bad[key]


@pytest.mark.parametrize("which", ["python", "native", "both"])
@pytest.mark.parametrize(
    "value",
    [math.nan, math.inf, math.nextafter(1.0, 0.0), math.nextafter(1.0, math.inf)],
)
def test_membership_checks_each_actual_vector_without_added_tolerance(which, value):
    r = ref.reference(c(1), [0.0])
    a = [value] if which in ("python", "both") else [1.0]
    b = [value] if which in ("native", "both") else [1.0]
    assert ref.membership(r, a, b)["status"] == "failed"


def test_context_restored_on_success_and_exception():
    with gmpy2.context(precision=71, round=gmpy2.RoundUp, trap_inexact=True):
        before = str(gmpy2.get_context())
        interval(op("exp", c(1)))
        assert str(gmpy2.get_context()) == before
        with pytest.raises(AttributeError):
            ref._directed("not_an_operation", F(1), 128, gmpy2.RoundDown)
        assert str(gmpy2.get_context()) == before


@pytest.mark.parametrize(
    "mutation", ["operator", "constant", "arity", "hidden_child", "time"]
)
def test_invalid_metadata_is_checked_before_any_shortcut(mutation):
    tree = op("*", c(0), op("exp", t()))
    times = [0.0]
    if mutation == "operator":
        tree["children"][1]["operator"] = "cos"
    if mutation == "constant":
        tree["children"][0]["value_hex"] = "nan"
    if mutation == "arity":
        tree["arity"] = True
    if mutation == "hidden_child":
        tree["children"].append(c(1))
    if mutation == "time":
        times = [math.inf]
    with pytest.raises(ValueError):
        ref.reference(tree, times)


def test_same_numerical_value_does_not_hide_bit_or_order_binding():
    a = ref.reference(c(0), [0.0])
    b = ref.reference(c(-0.0), [-0.0])
    assert a["tree_sha256"] != b["tree_sha256"] and a["times"] != b["times"]
    assert a["intervals_hex"] == b["intervals_hex"]
    first = op("+", t(), c(0))
    second = op("+", c(0), t())
    assert (
        ref.reference(first, [0.0])["tree_sha256"]
        != ref.reference(second, [0.0])["tree_sha256"]
    )


@pytest.mark.parametrize(
    "case", FIXTURE["cases"], ids=lambda c: f"cell-{c['cell']}-index-{c['index']}"
)
def test_all_original_and_csv_003_cases_against_actual_saved_native_predictions(case):
    times = np.asarray(FIXTURE["training_inputs"]["time_s"])
    observed = np.asarray(FIXTURE["training_inputs"]["observed"])
    candidate = copy.deepcopy(case["candidate"])
    before = copy.deepcopy(candidate)
    python = symbolic.evaluate_tree(candidate["tree"], times)
    evidence = ref.verify_prediction(
        candidate["tree"], times, python, candidate["prediction"]
    )
    assert evidence["precision_bits"] == 128
    # Original stored native/table losses remain unchanged. CSV reconstructions
    # have no original Pandas table value and are explicitly not original exports.
    candidate["python_loss"] = mean_squared_error(observed - python)
    candidate.setdefault("loss_replay", {"table_loss": candidate["loss"]})
    assert (
        candidate_evidence(candidate, times, observed, prediction_check=evidence)[
            "status"
        ]
        == "passed"
    )
    assert case["candidate"] == before
    if case["cell"] == 5 and case["index"] in (5, 6, 7, 9):
        with pytest.raises(AssertionError):
            symbolic._check_prediction_replay(
                case["fixed_python_replay"], candidate["prediction"]
            )
        assert (
            _prediction_replay(
                np.asarray(candidate["prediction"]),
                np.asarray(case["fixed_python_replay"]),
            )["status"]
            == "failed"
        )


def test_002_stale_native_loss_remains_rejected_after_valid_reference():
    stale = json.loads(
        (Path(__file__).parent / "fixtures/duration_stale_loss_case.json").read_bytes()
    )
    times = np.asarray(FIXTURE["training_inputs"]["time_s"])
    observed = np.asarray(FIXTURE["training_inputs"]["observed"])
    python = symbolic.evaluate_tree(stale["tree"], times)
    evidence = ref.verify_prediction(stale["tree"], times, python, python)
    actual = mean_squared_error(observed - python)
    with pytest.raises(AssertionError):
        verify_loss_replay(
            observed,
            python,
            python,
            stale["loss"],
            actual,
            stale["loss"],
            actual,
            None,
            prediction_check=evidence,
        )
