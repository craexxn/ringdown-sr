"""Independent identities and interval counterexamples for remainder diagnosis."""

import copy
import math
from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest
import sympy as sp
from test_structure_proof import T, op, q, sym_exact, unresolved_pole_tree

from ringdown_sr.remainder_proof import (
    _fraction,
    assess_remainder,
    bound_remainder,
)
from ringdown_sr.structure_algebra import LIMITS, ONE, TIME, Algebra


def core(rate=-1, omega=2, trig="cos"):
    return op("*", op("exp", op("*", q(rate), T)), op(trig, op("*", q(omega), T)))


def references():
    return {
        "training": {"time_s": np.array([0.0, 1.0]), "truth": np.array([0.0, 2.0])},
        "diagnostic": {"time_s": np.array([0.25, 0.75]), "truth": np.array([3.0, 3.0])},
    }


def diagnose(tree, refs=None, interval=(0, 1), **kwargs):
    return assess_remainder(
        tree, interval, references() if refs is None else refs, **kwargs
    )


def test_constant_remainder_has_exact_bound_and_correct_distinct_norms():
    result = diagnose(op("+", core(), q(0.5)))
    assert result["status"] == "bound_proven"
    assert len(result["components"]) == 1
    c = result["components"][0]
    assert _fraction(c["bound"]["upper"]) == Fraction(1, 2)
    training = c["relative_contribution_bounds"]["training"]
    rms = _fraction(training["relative_rms_upper"])
    assert Fraction(1, 8) <= rms * rms < Fraction(1, 8) + Fraction(1, 2**120)
    assert _fraction(training["relative_max_upper"]) == Fraction(1, 4)
    diagnostic = c["relative_contribution_bounds"]["diagnostic"]
    assert _fraction(diagnostic["relative_rms_upper"]) == Fraction(1, 6)
    assert _fraction(diagnostic["relative_max_upper"]) == Fraction(1, 6)
    assert "grade" not in result and "negligible" not in result


def test_undamped_small_term_is_retained_exactly():
    epsilon = 2**-40
    tree = op(
        "*",
        op("+", op("exp", op("*", q(-1), T)), q(epsilon)),
        op("sin", op("*", q(2), T)),
    )
    c = diagnose(tree)["components"][0]
    assert _fraction(c["bound"]["upper"]) == Fraction.from_float(epsilon)
    t = sp.Symbol("t", real=True)
    assert (
        sp.simplify(
            sym_exact(c["remainder_expression"]) - sp.Rational(1, 2**40) * sp.sin(2 * t)
        )
        == 0
    )


def test_all_distinct_modes_are_reported_without_truth_based_choice():
    tree = op("+", core(), core(-2, 3, "sin"))
    original = copy.deepcopy(tree)
    result = diagnose(tree)
    assert len(result["components"]) == 2
    t = sp.Symbol("t", real=True)
    expected = sp.exp(-t) * sp.cos(2 * t) + sp.exp(-2 * t) * sp.sin(3 * t)
    for c in result["components"]:
        assert (
            sp.simplify(
                sym_exact(c["core_expression"])
                + sym_exact(c["remainder_expression"])
                - expected
            )
            == 0
        )
    different = references()
    different["training"]["truth"] *= 1e90
    other = diagnose(tree, different)
    for left, right in zip(result["components"], other["components"], strict=True):
        for name in (
            "coefficients_exact",
            "core_expression",
            "remainder_expression",
            "bound",
        ):
            assert left[name] == right[name]
    assert tree == original


def test_equal_modes_combine_and_do_not_create_a_false_nonzero_remainder():
    result = diagnose(op("+", core(), core()))
    assert len(result["components"]) == 1
    c = result["components"][0]
    assert _fraction(c["bound"]["upper"]) == 0
    assert sym_exact(c["coefficients_exact"]["a"]) == 2


def test_exact_cancellation_does_not_manufacture_a_component():
    result = diagnose(op("-", core(), core()))
    assert result["status"] == "unresolved" and not result["components"]


def test_adjacent_binary64_frequencies_are_not_combined():
    tree = op("+", core(), core(omega=math.nextafter(2.0, math.inf)))
    result = diagnose(tree)
    assert len(result["components"]) == 2
    assert (
        result["components"][0]["coefficients_exact"]["omega"]
        != result["components"][1]["coefficients_exact"]["omega"]
    )


def test_tiny_coefficient_on_growing_exponential_is_not_a_tiny_bound():
    tree = op("+", core(), op("*", q(2**-40), op("exp", op("*", q(1000), T))))
    bound = diagnose(tree)["components"][0]["bound"]
    assert bound["status"] == "bound_proven"
    assert _fraction(bound["upper"]) > 2**1000


@pytest.mark.parametrize("root", [0, 0.5, 1])
def test_actual_poles_never_receive_a_finite_global_bound(root):
    tree = op("+", core(), op("/", q(2**-40), op("-", T, q(root))))
    c = diagnose(tree)["components"][0]
    assert c["bound"]["status"] == "unresolved"
    assert c["bound"]["upper"] is None
    assert c["relative_contribution_bounds"]["training"]["status"] == "not_assessable"


@pytest.mark.parametrize("root", [0, 0.001, 127 / 4096])
def test_incomplete_original_domain_blocks_even_a_plausible_normal_form(root):
    result = diagnose(unresolved_pole_tree(root), interval=(0, Fraction(127, 4096)))
    assert result["status"] == "unresolved"
    assert result["reason"] == "original_domain_completeness_unresolved"
    assert result["components"] == []


def test_removable_hole_is_kept_separate_from_the_bound_of_the_extension():
    tree = op("/", q(1), op("/", op("exp", T), op("cos", op("*", q(2), T))))
    result = diagnose(tree)
    assert result["domain_witness"]["status"] == "removable_holes"
    c = result["components"][0]
    assert _fraction(c["bound"]["upper"]) == 0
    assert c["bound"]["continuous_extension_included"] is True


def test_adaptive_cover_proves_a_bound_when_one_interval_cannot():
    a = Algebra()
    expr = a.div(ONE, a.add(ONE, a.mul(TIME, TIME)))
    result = bound_remainder(expr, (Fraction(-2), Fraction(2)), a)
    assert result["status"] == "bound_proven"
    assert _fraction(result["upper"]) == 1
    assert len(result["leaves"]) == 2
    ranges = [[_fraction(x) for x in leaf["interval"]] for leaf in result["leaves"]]
    assert ranges == [[-2, 0], [0, 2]]
    assert result["failed_interval_attempts"] == 4


def test_finite_whole_interval_bound_is_not_optimized_further():
    a = Algebra()
    expr = a.unary("sin", TIME)
    result = bound_remainder(expr, (Fraction(0), Fraction(4)), a)
    assert result["status"] == "bound_proven" and len(result["leaves"]) == 1
    assert result["leaves"][0]["depth"] == 0


def test_shared_step_budget_does_not_restart_for_other_components():
    tree = op("+", core(), core(-2, 3, "sin"))
    result = diagnose(tree, limits=replace(LIMITS, steps=2))
    assert (
        result["status"] == "unresolved" and result["reason"] == "analysis_step_limit"
    )
    assert result["work"]["analysis_steps"] == 3


@pytest.mark.parametrize(
    "bad", [None, np.zeros(2), np.array([np.nan, 1.0]), np.array([True, False])]
)
def test_invalid_reference_never_replaces_an_absolute_bound_with_zero(bad):
    refs = references()
    refs["training"] = (
        None if bad is None else {"time_s": np.array([0.0, 1.0]), "truth": bad}
    )
    c = diagnose(op("+", core(), q(1)), refs)["components"][0]
    assert _fraction(c["bound"]["upper"]) == 1
    assert c["relative_contribution_bounds"]["training"]["status"] == "not_assessable"


def test_reference_outside_interval_has_no_relative_contribution_certificate():
    refs = references()
    refs["diagnostic"]["time_s"][1] = 2.0
    c = diagnose(op("+", core(), q(1)), refs)["components"][0]
    assert (
        c["relative_contribution_bounds"]["diagnostic"]["reason"]
        == "reference_outside_bound_interval"
    )
