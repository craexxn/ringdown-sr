"""Certified, bounded diagnoses of every rule-derived ringdown component."""

from dataclasses import asdict
from fractions import Fraction

import gmpy2
import numpy as np

from .structure import _validated_tree
from .structure_algebra import (
    LIMITS,
    ONE,
    TIME,
    ZERO,
    Algebra,
    NowhereDefined,
    Unresolved,
    constant,
    rational_record,
)
from .structure_domain import Domain, normalize_original
from .structure_proof import expanded_terms

FORMAT = "ringdown-sr-remainder-proof-1"
MAX_DEPTH, MAX_LEAVES = 8, 256
RESOURCE_FAILURES = {
    "analysis_step_limit",
    "analysis_node_limit",
    "normalized_term_limit",
    "rational_bit_limit",
}


def _term_mode(term, algebra):
    coefficient, rate, omega = ONE, ZERO, ZERO
    a, b, trig_count = ONE, ZERO, 0
    signs = []
    for factor in term.args if term.op == "mul" else (term,):
        if constant(factor):
            coefficient = algebra.mul(coefficient, factor)
        elif factor.op == "exp":
            slope, intercept = algebra.affine(factor.args[0])
            rate = algebra.add(rate, slope)
            coefficient = algebra.mul(coefficient, algebra.unary("exp", intercept))
        elif factor.op in ("sin", "cos"):
            trig_count += 1
            if trig_count > 1:
                raise Unresolved("trigonometric_product_not_supported")
            slope, phase = algebra.affine(factor.args[0])
            sign, proof = algebra.sign(slope)
            signs.append(proof)
            if sign == 0:
                coefficient = algebra.mul(coefficient, algebra.unary(factor.op, phase))
                continue
            omega = slope if sign > 0 else algebra.neg(slope)
            cosine, sine = algebra.unary("cos", phase), algebra.unary("sin", phase)
            a, b = (
                (cosine, algebra.mul(algebra.q(-sign), sine))
                if factor.op == "cos"
                else (sine, algebra.mul(algebra.q(sign), cosine))
            )
        else:
            raise Unresolved("unsupported_normalized_factor")
    return rate, omega, algebra.mul(coefficient, a), algebra.mul(coefficient, b), signs


def _mode_expression(rate, omega, a, b, algebra):
    phase = algebra.mul(omega, TIME)
    return algebra.mul(
        algebra.unary("exp", algebra.mul(rate, TIME)),
        algebra.add(
            algebra.mul(a, algebra.unary("cos", phase)),
            algebra.mul(b, algebra.unary("sin", phase)),
        ),
    )


def components(normalized, algebra, trace):
    """Enumerate all certified groups; unsupported terms stay in each remainder."""
    modes, unmatched = {}, []
    for term in expanded_terms(normalized, algebra):
        try:
            rate, omega, a, b, signs = _term_mode(term, algebra)
        except Unresolved as error:
            if str(error) in RESOURCE_FAILURES:
                raise
            unmatched.append(term)
            trace.append(
                {
                    "rule_id": "retained_unmatched_term",
                    "term": term.record(),
                    "reason": str(error),
                }
            )
            continue
        old_a, old_b = modes.get((rate, omega), (ZERO, ZERO))
        modes[rate, omega] = algebra.add(old_a, a), algebra.add(old_b, b)
        trace.append(
            {
                "rule_id": "exact_affine_mode_decomposition",
                "before": term.record(),
                "after": {
                    k: v.record()
                    for k, v in zip(
                        ("rate", "omega", "a", "b"), (rate, omega, a, b), strict=True
                    )
                },
                "sign_proofs": signs,
                "preconditions": "complete original domain retained; exact affine addition identities",
            }
        )
    groups = []
    for (rate, omega), (a, b) in sorted(modes.items(), key=lambda item: repr(item[0])):
        expression = _mode_expression(rate, omega, a, b, algebra)
        eligible, signs, reason = False, [], "nondecaying_nonoscillatory_or_zero_group"
        try:
            rate_sign, rate_proof = algebra.sign(rate)
            omega_sign, omega_proof = algebra.sign(omega)
            signs.extend((rate_proof, omega_proof))
            nonzero = False
            for coefficient in (a, b):
                try:
                    sign, proof = algebra.sign(coefficient)
                    signs.append(proof)
                    nonzero |= sign != 0
                except Unresolved as error:
                    if str(error) in RESOURCE_FAILURES:
                        raise
            eligible = rate_sign < 0 and omega_sign > 0 and nonzero
        except Unresolved as error:
            if str(error) in RESOURCE_FAILURES:
                raise
            reason = str(error)
        groups.append((expression, eligible, (rate, omega, a, b), signs, reason))
    candidates = []
    for index, (core, eligible, values, signs, reason) in enumerate(groups):
        if not eligible:
            trace.append(
                {
                    "rule_id": "retained_other_mode",
                    "term": core.record(),
                    "reason": reason,
                }
            )
            continue
        rate, omega, a, b = values
        residual = algebra.add(
            *unmatched, *(g[0] for j, g in enumerate(groups) if j != index)
        )
        candidates.append(
            (
                core,
                residual,
                {
                    "component_index": len(candidates),
                    "coefficients_exact": {
                        k: v.record()
                        for k, v in zip(
                            ("gamma", "omega", "a", "b"),
                            (algebra.neg(rate), omega, a, b),
                            strict=True,
                        )
                    },
                    "coefficient_sign_proofs": signs,
                    "core_expression": core.record(),
                    "remainder_expression": residual.record(),
                    "decomposition": "proven_on_original_domain",
                    "bound": {"status": "unresolved"},
                },
            )
        )
    return candidates


def bound_remainder(expr, interval, algebra):
    """Certify a complete left-first dyadic cover, sharing the caller's budget."""
    leaves, pending = [], [(interval, 0)]
    slots, failed_attempts = 1, 0
    result = {"status": "unresolved", "upper": None, "leaves": leaves}
    try:
        while pending:
            current, depth = pending.pop()
            last = "interval_unresolved"
            for precision in algebra.limits.precisions:
                try:
                    low, high = algebra.interval(expr, precision, current)
                except Unresolved as error:
                    if str(error) in RESOURCE_FAILURES:
                        raise
                    failed_attempts += 1
                    last = str(error)
                    continue
                leaves.append(
                    {
                        "interval": [rational_record(x) for x in current],
                        "depth": depth,
                        "precision_bits": precision,
                        "lower": rational_record(low),
                        "upper": rational_record(high),
                        "absolute_upper": rational_record(max(abs(low), abs(high))),
                    }
                )
                break
            else:
                result["last_interval_failure"] = last
                result["unresolved_interval"] = [rational_record(x) for x in current]
                if depth >= MAX_DEPTH:
                    raise Unresolved("subdivision_depth_limit")
                if slots >= MAX_LEAVES:
                    raise Unresolved("subdivision_leaf_limit")
                middle = algebra.check_fraction(sum(current) / 2)
                slots += 1
                pending.extend(
                    (
                        ((middle, current[1]), depth + 1),
                        ((current[0], middle), depth + 1),
                    )
                )
        upper = max(_fraction(leaf["absolute_upper"]) for leaf in leaves)
        result.update(status="bound_proven", upper=rational_record(upper))
        result.pop("unresolved_interval", None)
        result.pop("last_interval_failure", None)
    except Unresolved as error:
        result["reason"] = str(error)
    result.update(failed_interval_attempts=failed_attempts, partition_slots=slots)
    return result


def _fraction(record):
    return Fraction(
        int(record["numerator_hex"], 16), int(record["denominator_hex"], 16)
    )


def reference_scales(reference, interval, algebra):
    """Use exact saved vector bits; invalid scales never erase an absolute bound."""
    if not isinstance(reference, dict) or set(reference) != {"time_s", "truth"}:
        raise Unresolved("missing_reference_grid")
    time, truth = (np.asarray(reference[k]) for k in ("time_s", "truth"))
    if (
        time.dtype != np.dtype("float64")
        or truth.dtype != np.dtype("float64")
        or time.ndim != 1
        or truth.shape != time.shape
        or not time.size
        or not np.all(np.isfinite(time))
        or not np.all(np.isfinite(truth))
    ):
        raise Unresolved("invalid_reference_grid")
    total, maximum = Fraction(0), Fraction(0)
    for t, y in zip(time, truth, strict=True):
        algebra.tick()
        if not interval[0] <= Fraction.from_float(float(t)) <= interval[1]:
            raise Unresolved("reference_outside_bound_interval")
        value = Fraction.from_float(float(y))
        total = algebra.check_fraction(total + value * value)
        maximum = max(maximum, abs(value))
    if maximum == 0:
        raise Unresolved("zero_reference_scale")
    square = algebra.check_fraction(total / len(truth))
    # MPFR first encloses the exact rational square, then monotone sqrt.
    for precision in algebra.limits.precisions:
        algebra.tick()
        try:
            endpoints = []
            for rounding in (gmpy2.RoundDown, gmpy2.RoundUp):
                with gmpy2.context(
                    precision=precision,
                    round=rounding,
                    emin=-algebra.limits.rational_bits,
                    emax=algebra.limits.rational_bits,
                    trap_underflow=True,
                    trap_overflow=True,
                    trap_invalid=True,
                    trap_erange=True,
                    trap_divzero=True,
                    trap_inexact=False,
                    subnormalize=False,
                    allow_complex=False,
                ):
                    value = gmpy2.sqrt(
                        gmpy2.mpfr(gmpy2.mpq(square.numerator, square.denominator))
                    )
                    if not gmpy2.is_finite(value):
                        raise Unresolved("nonfinite_reference_scale")
                    n, d = value.as_integer_ratio()
                    endpoints.append(algebra.check_fraction(Fraction(int(n), int(d))))
        except (ArithmeticError, ValueError):
            continue
        if endpoints[0] > 0:
            return {
                "status": "assessed",
                "sample_count": len(truth),
                "rms_squared_exact": rational_record(square),
                "maximum_exact": rational_record(maximum),
                "rms_lower": rational_record(endpoints[0]),
                "rms_upper": rational_record(endpoints[1]),
                "precision_bits": precision,
            }
    raise Unresolved("positive_reference_scale_unresolved")


def _normalize_bounds(result, references, interval, algebra):
    references = references if isinstance(references, dict) else {}
    scales = {}
    for grid in ("training", "diagnostic"):
        try:
            scales[grid] = reference_scales(
                (references or {}).get(grid), interval, algebra
            )
        except Unresolved as error:
            scales[grid] = {"status": "not_assessable", "reason": str(error)}
    result["reference_scales"] = scales
    for candidate in result["components"]:
        candidate["relative_contribution_bounds"] = {}
        for grid, scale in scales.items():
            value = {"status": "not_assessable", "reason": "absolute_bound_unresolved"}
            if scale["status"] != "assessed":
                value = dict(scale)
            elif candidate["bound"]["status"] == "bound_proven":
                try:
                    algebra.tick()
                    upper = _fraction(candidate["bound"]["upper"])
                    rms = algebra.check_fraction(upper / _fraction(scale["rms_lower"]))
                    maximum = algebra.check_fraction(
                        upper / _fraction(scale["maximum_exact"])
                    )
                    value = {
                        "status": "bound_proven",
                        "relative_rms_upper": rational_record(rms),
                        "relative_max_upper": rational_record(maximum),
                    }
                except Unresolved as error:
                    value = {"status": "not_assessable", "reason": str(error)}
            candidate["relative_contribution_bounds"][grid] = value


def assess_remainder(tree, interval, references=None, *, limits=LIMITS):
    """Assess exact components before touching any reference or signal metadata."""
    node = _validated_tree(tree)
    if (
        len(interval) != 2
        or any(type(x) not in (int, Fraction) for x in interval)
        or interval[0] >= interval[1]
    ):
        raise ValueError(
            "A closed exact rational interval of positive length is required."
        )
    for name in ("nodes", "terms", "roots", "steps", "rational_bits"):
        value = getattr(limits, name)
        if type(value) is not int or not 0 < value <= getattr(LIMITS, name):
            raise ValueError("Invalid remainder resource limit: " + name)
    if (
        not limits.precisions
        or any(
            type(p) is not int or p not in LIMITS.precisions for p in limits.precisions
        )
        or tuple(sorted(set(limits.precisions))) != limits.precisions
    ):
        raise ValueError("Invalid precision schedule.")
    interval = tuple(map(Fraction, interval))
    algebra, trace, constraints = Algebra(limits), [], []
    result = {
        "format": FORMAT,
        "status": "unresolved",
        "limits": asdict(limits),
        "interval": [rational_record(x) for x in interval],
        "component_selection": "all_certified_mode_groups_without_ranking",
        "components": [],
        "proof_trace": trace,
    }
    try:
        for value in interval:
            algebra.check_fraction(value)
        normalized = normalize_original(node, algebra, trace, constraints)
        result["original_denominator_conditions"] = [
            {"original_node_path": p, "expression": e.record()} for e, p in constraints
        ]
        domain = Domain(algebra, interval).assess(constraints, normalized)
        result["domain_witness"] = domain
        if not domain["nonempty_dense_original_domain_proven"]:
            raise Unresolved("original_domain_completeness_unresolved")
        candidates = components(normalized, algebra, trace)
        if not candidates:
            raise Unresolved("no_certified_rule_based_component")
        for _, residual, candidate in candidates:
            candidate["bound"] = bound_remainder(residual, interval, algebra)
            candidate["bound"]["scope"] = "original_domain_within_closed_interval"
            candidate["bound"]["continuous_extension_included"] = (
                domain["status"] == "removable_holes"
            )
            result["components"].append(candidate)
        result["status"] = (
            "bound_proven"
            if all(c["bound"]["status"] == "bound_proven" for c in result["components"])
            else "unresolved"
        )
        _normalize_bounds(result, references, interval, algebra)
    except (Unresolved, NowhereDefined) as error:
        result["reason"] = str(error)
    result["work"] = {
        "analysis_steps": algebra.steps,
        "root_candidates": algebra.root_count,
    }
    return result
