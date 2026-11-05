"""Independent, bounded real-family/domain proof for one original selection."""

from dataclasses import asdict
from fractions import Fraction

from .structure import _validated_tree
from .structure_algebra import (
    LIMITS,
    ONE,
    ZERO,
    Algebra,
    NowhereDefined,
    Unresolved,
    constant,
    rational_record,
)
from .structure_domain import Domain, normalize_original

FORMAT = "ringdown-sr-structure-proof-1"


def expanded_terms(expr, algebra):
    """Bound distributivity before constructing any Cartesian product."""
    algebra.tick()
    if expr.op == "add":
        result = []
        for arg in expr.args:
            more = expanded_terms(arg, algebra)
            if len(result) + len(more) > algebra.limits.terms:
                raise Unresolved("normalized_term_limit")
            result.extend(more)
        return result
    if expr.op == "mul":
        result = [ONE]
        for arg in expr.args:
            more = expanded_terms(arg, algebra)
            if len(result) * len(more) > algebra.limits.terms:
                raise Unresolved("normalized_term_limit")
            result = [algebra.mul(a, b) for a in result for b in more]
        return result
    return [expr]


def family(expr, algebra, trace):
    """Normalize finite affine exponential/sinusoidal terms, without fitting."""
    modes = {}
    signs = []
    for term in expanded_terms(expr, algebra):
        coefficient, rate, omega = ONE, ZERO, ZERO
        a, b, trig_count = ONE, ZERO, 0
        factors = term.args if term.op == "mul" else (term,)
        for factor in factors:
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
                    coefficient = algebra.mul(
                        coefficient, algebra.unary(factor.op, phase)
                    )
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
        a, b = algebra.mul(coefficient, a), algebra.mul(coefficient, b)
        previous = modes.get((rate, omega), (ZERO, ZERO))
        modes[rate, omega] = algebra.add(previous[0], a), algebra.add(previous[1], b)
        trace.append(
            {
                "rule_id": "affine_exponential_and_trigonometric_addition",
                "rule_version": 1,
                "original_node_path": "root",
                "before": term.record(),
                "after": {
                    "rate": rate.record(),
                    "omega": omega.record(),
                    "a": a.record(),
                    "b": b.record(),
                },
                "preconditions": "exact affine arguments; signed frequency certificate; original domain retained",
            }
        )
    modes = {key: value for key, value in modes.items() if value != (ZERO, ZERO)}
    if not modes:
        return "proven_nonmember", "identically_zero_amplitude", None, signs
    if len(modes) != 1:
        raise Unresolved("multiple_modes_without_nonmembership_proof")
    (rate, omega), (a, b) = next(iter(modes.items()))
    nonzero = False
    for coefficient in (a, b):
        try:
            sign, proof = algebra.sign(coefficient)
            signs.append(proof)
            nonzero |= sign != 0
        except Unresolved:
            pass
    if not nonzero:
        raise Unresolved("nonzero_combined_amplitude_unresolved")
    rate_sign, rate_proof = algebra.sign(rate)
    omega_sign, omega_proof = algebra.sign(omega)
    signs += [rate_proof, omega_proof]
    coefficients = {
        "gamma": algebra.neg(rate).record(),
        "omega": omega.record(),
        "a": a.record(),
        "b": b.record(),
    }
    if rate_sign >= 0 or omega_sign == 0:
        return (
            "proven_nonmember",
            "single_mode_uniqueness_excludes_nondecaying_or_nonoscillatory_form",
            coefficients,
            signs,
        )
    if omega_sign < 0:
        raise Unresolved("frequency_sign_invariant")
    return (
        "proven_on_original_domain",
        "single_decaying_nonzero_mode",
        coefficients,
        signs,
    )


def assess_structure(tree, interval, *, limits=LIMITS):
    """Prove on an explicit exact interval; the caller binds it to original data."""
    node = _validated_tree(tree)
    if (
        len(interval) != 2
        or any(type(x) not in (int, Fraction) for x in interval)
        or interval[0] >= interval[1]
    ):
        raise ValueError(
            "A closed exact rational interval of positive length is required."
        )
    # Reduced limits are useful for counterexamples; silently increasing the
    # agreed proof budget is not an alternate production mode.
    for name in ("nodes", "terms", "roots", "steps", "rational_bits"):
        value = getattr(limits, name)
        if type(value) is not int or not 0 < value <= getattr(LIMITS, name):
            raise ValueError("Invalid proof resource limit: " + name)
    if (
        not limits.precisions
        or any(
            type(p) is not int or p not in LIMITS.precisions for p in limits.precisions
        )
        or tuple(sorted(set(limits.precisions))) != limits.precisions
    ):
        raise ValueError("Invalid precision schedule.")
    interval = tuple(map(Fraction, interval))
    algebra = Algebra(limits)
    trace, constraints = [], []
    result = {
        "format": FORMAT,
        "limits": asdict(limits),
        "algebraic_identity": {"status": "unresolved"},
        "domain": {
            "status": "unresolved",
            "interval": {
                "unit": "seconds",
                "closed": [True, True],
                "endpoints": [rational_record(v) for v in interval],
            },
            "exclusions": [],
        },
        "original_family": {"status": "unresolved"},
        "continuous_extension": {"status": "unresolved"},
        "coefficients_exact": None,
        "coefficient_sign_proofs": [],
        "proof_trace": trace,
        "remainder": {"status": "not_assessed"},
        "new_parameter_match": {"status": "not_assessed"},
    }
    try:
        for value in interval:
            algebra.check_fraction(value)
        normalized = normalize_original(node, algebra, trace, constraints)
        result["normalized_expression"] = normalized.record()
        result["original_denominator_conditions"] = [
            {"original_node_path": path, "nonzero_expression": expr.record()}
            for expr, path in constraints
        ]
        domain = Domain(algebra, interval).assess(constraints, normalized)
        result["domain"].update(domain)
        if domain["exclusions"]:
            result["original_family"] = {
                "status": "proven_nonmember",
                "reason": "original_domain_gap",
            }
        status, reason, coefficients, signs = (
            "unresolved",
            "original_domain_nonempty_not_proven",
            None,
            [],
        )
        if domain["nonempty_dense_original_domain_proven"]:
            try:
                status, reason, coefficients, signs = family(normalized, algebra, trace)
            except Unresolved as error:
                reason = str(error)
            if any(hole["kind"] == "nonremovable" for hole in domain["exclusions"]):
                status, reason = (
                    "proven_nonmember",
                    "unbounded_simple_pole_excludes_continuous_family",
                )
        result["algebraic_identity"] = {"status": status, "reason": reason}
        result["coefficients_exact"] = coefficients
        result["coefficient_sign_proofs"] = signs
        if domain["status"] == "defined_everywhere":
            result["original_family"] = {
                "status": "proven_member"
                if status == "proven_on_original_domain"
                else status,
                "reason": reason,
            }
            result["continuous_extension"] = {"status": "not_applicable"}
        elif domain["status"] == "removable_holes":
            result["continuous_extension"] = {
                "status": "proven_member"
                if status == "proven_on_original_domain"
                else status,
                "reason": reason,
            }
        elif any(hole["kind"] == "nonremovable" for hole in domain["exclusions"]):
            result["continuous_extension"] = {
                "status": "proven_nonmember",
                "reason": "nonremovable_singularity",
            }
        if algebra.steps > limits.steps:
            raise Unresolved("analysis_step_limit")
    except NowhereDefined as error:
        result["domain"].update(status="nowhere_defined", reason=str(error))
        result["original_family"] = {
            "status": "proven_nonmember",
            "reason": "empty_original_domain",
        }
        result["algebraic_identity"] = {
            "status": "unresolved",
            "reason": "empty_original_domain",
        }
        result["continuous_extension"] = {
            "status": "unresolved",
            "reason": "no_unique_extension_from_empty_domain",
        }
    except Unresolved as error:
        # Preserve traces but revoke all global conclusions after a resource failure.
        for name in ("algebraic_identity", "original_family", "continuous_extension"):
            result[name] = {"status": "unresolved", "reason": str(error)}
        result["domain"].update(status="unresolved", reason=str(error))
    result["work"] = {
        "analysis_steps": algebra.steps,
        "root_candidates": algebra.root_count,
    }
    return result
