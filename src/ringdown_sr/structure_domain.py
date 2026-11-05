"""Original denominator obligations and certified finite exclusion sets."""

import math
from fractions import Fraction

from .structure_algebra import (
    ONE,
    PI,
    TIME,
    ZERO,
    NowhereDefined,
    Unresolved,
    constant,
    rational_record,
)


def normalize_original(node, algebra, trace, constraints, path="root"):
    """Validate separately first; retain each original denominator before cancellation."""
    algebra.tick()
    if node.kind == "constant":
        return algebra.q(node.value)
    if node.kind == "variable":
        return TIME
    children = [
        normalize_original(c, algebra, trace, constraints, f"{path}/{i}")
        for i, c in enumerate(node.children)
    ]
    op = node.operator
    if op == "/":
        constraints.append((children[1], f"{path}/1"))
    before = {"operator": op, "children": [c.record() for c in children]}
    if op == "+":
        value = algebra.add(*children)
    elif op == "-":
        value = algebra.add(children[0], algebra.neg(children[1]))
    elif op == "*":
        value = algebra.mul(*children)
    elif op == "/":
        value = algebra.div(*children)
    else:
        value = algebra.unary(op, children[0])
    trace.append(
        {
            "rule_id": "exact_ring_and_exponential_identities"
            if op in ("+", "-", "*", "/")
            else "elementary_composition",
            "rule_version": 1,
            "original_node_path": path,
            "before": before,
            "after": value.record(),
            "preconditions": "all original children defined; every original denominator nonzero",
            "domain_conditions": [p for _, p in constraints],
        }
    )
    return value


def substitute(expr, value, algebra):
    algebra.tick()
    if expr == TIME:
        return value
    if not expr.args:
        return expr
    args = [substitute(a, value, algebra) for a in expr.args]
    if expr.op == "add":
        return algebra.add(*args)
    if expr.op == "mul":
        return algebra.mul(*args)
    if expr.op == "inv":
        return algebra.div(ONE, args[0])
    return algebra.unary(expr.op, args[0])


class Domain:
    """Prove denominator nonzeros or a complete finite set of exact roots."""

    def __init__(self, algebra, interval):
        self.a = algebra
        self.interval = interval
        self.proofs = []

    def locate(self, root):
        signs, proofs = [], []
        for bound in self.interval:
            sign, proof = self.a.sign(self.a.add(root, self.a.q(-bound)))
            signs.append(sign)
            proofs.append(proof)
        if signs[0] < 0 or signs[1] > 0:
            return None
        return {
            "point": root.record(),
            "position": "left_endpoint"
            if signs[0] == 0
            else "right_endpoint"
            if signs[1] == 0
            else "interior",
            "membership_proofs": proofs,
        }

    def roots(self, expr):
        self.a.tick()
        if constant(expr):
            sign, proof = self.a.sign(expr)
            self.proofs.append(proof)
            if sign == 0:
                raise NowhereDefined("identically_zero_denominator")
            return []
        if expr.op in ("exp", "inv"):
            self.proofs.append(
                {
                    "rule_id": "exponential_or_reciprocal_nonzero_on_child_domain",
                    "expression": expr.record(),
                }
            )
            return []
        if expr.op == "mul":
            return [root for arg in expr.args for root in self.roots(arg)]
        try:
            slope, intercept = self.a.affine(expr)
        except Unresolved:
            slope = None
        if slope is not None:
            sign, proof = self.a.sign(slope)
            self.proofs.append(proof)
            if sign == 0:
                return self.roots(intercept)
            root = self.a.div(self.a.neg(intercept), slope)
            self.a.root_count += 1
            if self.a.root_count > self.a.limits.roots:
                raise Unresolved("root_candidate_limit")
            location = self.locate(root)
            self.proofs.append(
                {
                    "rule_id": "complete_affine_zero_set",
                    "expression": expr.record(),
                    "root": root.record(),
                    "inside_interval": location is not None,
                }
            )
            return [(root, location)] if location is not None else []
        if expr.op in ("sin", "cos"):
            slope, intercept = self.a.affine(expr.args[0])
            sign, proof = self.a.sign(slope)
            self.proofs.append(proof)
            if sign == 0:
                return self.roots(self.a.unary(expr.op, intercept))
            offset = Fraction(0) if expr.op == "sin" else Fraction(1, 2)
            # A coarse outward enclosure is sufficient: each candidate is then
            # individually compared with both exact closed endpoints.
            precision = self.a.limits.precisions[0]
            bounds = [
                self.a.interval(
                    self.a.add(self.a.mul(slope, self.a.q(t)), intercept), precision
                )
                for t in self.interval
            ]
            pi = self.a.interval(PI, precision)
            ratios = [x / p - offset for pair in bounds for x in pair for p in pi]
            first, last = math.ceil(min(ratios)), math.floor(max(ratios))
            self.a.root_count += max(0, last - first + 1)
            if self.a.root_count > self.a.limits.roots:
                raise Unresolved("root_candidate_limit")
            roots = []
            for k in range(first, last + 1):
                root = self.a.div(
                    self.a.add(
                        self.a.mul(self.a.q(k + offset), PI), self.a.neg(intercept)
                    ),
                    slope,
                )
                location = self.locate(root)
                if location is not None:
                    roots.append((root, location))
            self.proofs.append(
                {
                    "rule_id": "complete_affine_trigonometric_zero_set",
                    "expression": expr.record(),
                    "slope_sign": proof,
                    "precision_bits": precision,
                    "phase_endpoint_enclosures": [
                        [rational_record(x) for x in pair] for pair in bounds
                    ],
                    "pi_enclosure": [rational_record(x) for x in pi],
                    "candidate_k_range": [first, last],
                    "zero_equation": "argument=k*pi"
                    if expr.op == "sin"
                    else "argument=(k+1/2)*pi",
                    "included_points": [r.record() for r, _ in roots],
                }
            )
            return roots
        # A broad enclosure containing zero proves neither a root nor a gap.
        for precision in self.a.limits.precisions:
            try:
                low, high = self.a.interval(expr, precision, self.interval)
            except Unresolved:
                continue
            if low > 0 or high < 0:
                self.proofs.append(
                    {
                        "rule_id": "interval_nonzero_on_closed_interval",
                        "expression": expr.record(),
                        "precision_bits": precision,
                        "sign": 1 if low > 0 else -1,
                        "lower": rational_record(low),
                        "upper": rational_record(high),
                    }
                )
                return []
        raise Unresolved("denominator_zero_set_unresolved")

    def continuous_at(self, expr, root):
        """Elementary continuity with certified nonzero denominators at the point."""
        self.a.tick()
        for arg in expr.args:
            self.continuous_at(arg, root)
        if expr.op == "inv":
            value = substitute(expr.args[0], root, self.a)
            sign, proof = self.a.sign(value)
            self.proofs.append(proof)
            if not sign:
                raise Unresolved("normalized_denominator_zero_at_exclusion")
        return substitute(expr, root, self.a)

    def simple_pole(self, expr, root):
        """A single reciprocal affine/trig factor with a nonzero continuous numerator."""
        factors = list(expr.args) if expr.op == "mul" else [expr]
        inverse = [f for f in factors if f.op == "inv"]
        if len(inverse) != 1:
            raise Unresolved("singularity_type_unresolved")
        denominator = inverse[0].args[0]
        # Exact substitution (including exact half-pi identities) establishes
        # that this exclusion is a zero of the remaining denominator.
        value = substitute(denominator, root, self.a)
        if value != ZERO:
            raise Unresolved("pole_location_unresolved")
        argument = (
            denominator.args[0] if denominator.op in ("sin", "cos") else denominator
        )
        slope, _ = self.a.affine(argument)
        slope_sign, slope_proof = self.a.sign(slope)
        if not slope_sign:
            raise Unresolved("simple_zero_not_proven")
        numerator = self.a.mul(*(f for f in factors if f is not inverse[0]))
        limit = self.continuous_at(numerator, root)
        numerator_sign, numerator_proof = self.a.sign(limit)
        if not numerator_sign:
            raise Unresolved("nonzero_pole_numerator_not_proven")
        return {
            "rule_id": "nonzero_numerator_over_simple_zero",
            "denominator": denominator.record(),
            "slope_proof": slope_proof,
            "numerator_proof": numerator_proof,
            "one_sided_unbounded_at_endpoint": True,
        }

    def assess(self, constraints, normalized):
        exclusions = {}
        unresolved = []
        for denominator, path in constraints:
            try:
                found = self.roots(denominator)
            except Unresolved as error:
                unresolved.append({"original_node_path": path, "reason": str(error)})
                continue
            for root, location in found:
                if root not in exclusions:
                    exclusions[root] = {**location, "original_node_paths": []}
                exclusions[root]["original_node_paths"].append(path)
        for root, record in exclusions.items():
            try:
                limit = self.continuous_at(normalized, root)
                record.update(
                    kind="removable",
                    limit=limit.record(),
                    proof={
                        "rule_id": "continuous_normal_form_on_dense_original_domain",
                        "direction": "right"
                        if record["position"] == "left_endpoint"
                        else "left"
                        if record["position"] == "right_endpoint"
                        else "two_sided",
                    },
                )
            except (Unresolved, NowhereDefined):
                try:
                    proof = self.simple_pole(normalized, root)
                    record.update(kind="nonremovable", proof=proof)
                except (Unresolved, NowhereDefined) as error:
                    record.update(kind="unresolved", reason=str(error))
        kinds = {r["kind"] for r in exclusions.values()}
        complete = not unresolved
        status = "unresolved"
        if complete and "unresolved" not in kinds:
            status = (
                "defined_everywhere"
                if not kinds
                else "removable_holes"
                if kinds == {"removable"}
                else "nonremovable_singularities"
                if kinds == {"nonremovable"}
                else "mixed"
            )
        # A local smooth expression alone does not prove a unique extension
        # when other original domain obligations remain unresolved.
        if not complete:
            for record in exclusions.values():
                if record["kind"] == "removable":
                    record.update(
                        kind="unresolved",
                        reason="original_domain_completeness_unresolved",
                    )
        return {
            "status": status,
            "exclusions": list(exclusions.values()),
            "unresolved_obligations": unresolved,
            "nonempty_dense_original_domain_proven": complete,
            "proofs": self.proofs,
        }
