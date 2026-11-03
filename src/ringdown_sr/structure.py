"""Recognize a limited real-valued ringdown structure in exported Float64 trees.

Exact rational extraction does not preserve floating-point evaluation order.
This module performs no numerical replay, fitting, alias reduction or inference.
"""

import math
from dataclasses import dataclass
from fractions import Fraction

# This is the pinned exported-tree contract, checked against the search grammar.
_BINARY = ("+", "-", "*", "/")
_UNARY = ("exp", "sin", "cos")
MAX_TREE_NODES = 20


class InvalidTreeError(ValueError):
    """The input does not satisfy the bounded exported-tree contract."""


class _Unsupported(Exception):
    """A valid tree is outside the deliberately limited recognition pattern."""


@dataclass(frozen=True)
class _Node:
    kind: str
    value: Fraction = Fraction(0)
    operator: str = ""
    children: tuple["_Node", ...] = ()


@dataclass(frozen=True)
class RawCoefficients:
    """Exact real coefficients in A * exp(b*t) * cos(c*t+d)."""

    amplitude: Fraction
    exponential_rate_per_s: Fraction
    angular_frequency_per_s: Fraction
    phase_rad: Fraction
    phase_pi_multiple: Fraction = Fraction(0)

    def to_dict(self) -> dict:
        """Encode rational values without Float64 conversion or JSON number loss."""
        result = {
            name: {
                "numerator": str(value.numerator),
                "denominator": str(value.denominator),
            }
            for name, value in zip(
                ("A", "b", "c", "d"),
                (
                    self.amplitude,
                    self.exponential_rate_per_s,
                    self.angular_frequency_per_s,
                    self.phase_rad,
                ),
                strict=True,
            )
        }
        if self.phase_pi_multiple:
            result["d_pi"] = {
                "numerator": str(self.phase_pi_multiple.numerator),
                "denominator": str(self.phase_pi_multiple.denominator),
            }
        return result


@dataclass(frozen=True)
class StructureRecognition:
    """A structural diagnosis, with later interpretation stages left unattempted."""

    coefficients: RawCoefficients | None
    reason: str | None = None
    version: int = 1

    @property
    def structure_status(self) -> str:
        return "recognized" if self.coefficients is not None else "not_supported"

    def to_dict(self) -> dict:
        coefficients = self.coefficients
        rate = None if coefficients is None else coefficients.exponential_rate_per_s
        return {
            "format": f"ringdown-sr-structure-recognition-{self.version}",
            "structure_status": self.structure_status,
            "reason": self.reason,
            "raw_coefficients": None
            if coefficients is None
            else coefficients.to_dict(),
            "exponential_status": None
            if rate is None
            else "decaying"
            if rate < 0
            else "growing"
            if rate > 0
            else "undamped",
            "amplitude_status": None
            if coefficients is None
            else "zero"
            if coefficients.amplitude == 0
            else "nonzero",
            "phase_kind": None
            if coefficients is None
            else "radian_plus_pi"
            if coefficients.phase_pi_multiple
            else "radian_rational",
            "replay_status": "not_attempted",
            "parameter_interpretation": "not_attempted",
            "alias_status": "not_attempted",
            "physical_identification": "not_assessed",
        }


def _validated_tree(tree: dict) -> _Node:
    count = 0

    def visit(node):
        nonlocal count
        count += 1
        if count > MAX_TREE_NODES:
            raise InvalidTreeError("Tree exceeds the 20-node exported search contract.")
        if type(node) is not dict:
            raise InvalidTreeError("Every tree node must be a dictionary.")
        kind = node.get("kind")
        if kind == "constant":
            if set(node) != {"kind", "value_hex"} or type(node["value_hex"]) is not str:
                raise InvalidTreeError("Invalid constant node fields.")
            try:
                value = float.fromhex(node["value_hex"])
            except (ValueError, OverflowError) as error:
                raise InvalidTreeError("Invalid Float64 constant.") from error
            if not math.isfinite(value) or value.hex() != node["value_hex"]:
                raise InvalidTreeError(
                    "Constants must use canonical finite Float64 hex."
                )
            return _Node(kind, value=Fraction.from_float(value))
        if kind == "variable":
            if (
                set(node) != {"kind", "index"}
                or type(node["index"]) is not int
                or node["index"] != 1
            ):
                raise InvalidTreeError(
                    "Only the time variable with integer index 1 is valid."
                )
            return _Node(kind)
        if kind != "operator" or set(node) != {
            "kind",
            "operator",
            "arity",
            "operator_index",
            "children",
        }:
            raise InvalidTreeError("Invalid operator node fields or node kind.")
        arity, index = node["arity"], node["operator_index"]
        if type(arity) is not int or arity not in (1, 2):
            raise InvalidTreeError("Operator arity must be integer 1 or 2.")
        names = _UNARY if arity == 1 else _BINARY
        if (
            type(index) is not int
            or not 1 <= index <= len(names)
            or type(node["operator"]) is not str
            or node["operator"] != names[index - 1]
        ):
            raise InvalidTreeError(
                "Operator name and index must match the exported grammar."
            )
        if type(node["children"]) is not list or len(node["children"]) != arity:
            raise InvalidTreeError("Operator child count does not match its arity.")
        return _Node(
            kind,
            operator=node["operator"],
            children=tuple(visit(child) for child in node["children"]),
        )

    return visit(tree)


def _affine(node: _Node) -> tuple[Fraction, Fraction]:
    """Read exact slope/intercept; do not cancel nonlinear or singular subtrees."""
    if node.kind == "constant":
        return Fraction(0), node.value
    if node.kind == "variable":
        return Fraction(1), Fraction(0)
    if node.operator not in _BINARY:
        raise _Unsupported("unsupported_affine_operator")
    a, b = _affine(node.children[0])
    c, d = _affine(node.children[1])
    if node.operator == "+":
        return a + c, b + d
    if node.operator == "-":
        return a - c, b - d
    if node.operator == "*":
        if a != 0 and c != 0:
            raise _Unsupported("non_affine_product")
        return a * d + b * c, b * d
    if c != 0:
        raise _Unsupported("time_dependent_denominator")
    if d == 0:
        raise _Unsupported("zero_denominator")
    return a / d, b / d


def _scalar(node: _Node) -> Fraction:
    """Require a syntactically time-free rational outer factor."""
    if node.kind == "constant":
        return node.value
    if node.kind != "operator" or node.operator not in _BINARY:
        raise _Unsupported("non_scalar_outer_factor")
    left, right = (_scalar(child) for child in node.children)
    if node.operator == "+":
        return left + right
    if node.operator == "-":
        return left - right
    if node.operator == "*":
        return left * right
    if right == 0:
        raise _Unsupported("zero_denominator")
    return left / right


def _factors(node: _Node) -> list[_Node]:
    if node.kind == "operator" and node.operator == "*":
        return _factors(node.children[0]) + _factors(node.children[1])
    return [node]


def recognize_ringdown(tree: dict) -> StructureRecognition:
    """Recognize one exp(b*t) and one cos(c*t+d) with rational scalar factors.

    All nodes are validated before pattern matching, including unsupported
    branches and factors multiplied by zero. Malformed inputs raise
    InvalidTreeError; valid unsupported expressions return a reason code.
    The input is not modified. No samples, truth, losses or seeds are used.
    """
    root = _validated_tree(tree)
    factors = _factors(root)
    exponentials = [node for node in factors if node.operator == "exp"]
    cosines = [node for node in factors if node.operator == "cos"]
    try:
        if len(exponentials) != 1:
            raise _Unsupported("exponential_factor_count")
        if len(cosines) != 1:
            raise _Unsupported("cosine_factor_count")
        amplitude = Fraction(1)
        for node in factors:
            if node.operator not in ("exp", "cos"):
                amplitude *= _scalar(node)
        rate, intercept = _affine(exponentials[0].children[0])
        if intercept != 0:
            raise _Unsupported("nonzero_exponential_intercept")
        frequency, phase = _affine(cosines[0].children[0])
    except _Unsupported as error:
        return StructureRecognition(coefficients=None, reason=str(error))
    return StructureRecognition(RawCoefficients(amplitude, rate, frequency, phase))


def recognize_ringdown_extended(tree: dict) -> StructureRecognition:
    """Recognize one numerator sin/cos and one exp in products/quotients.

    Denominator singularities are never cancelled. Pi remains an exact
    symbolic phase component; the original evaluation tree is untouched.
    This opt-in contract does not change the legacy recognizer.
    """
    root = _validated_tree(tree)
    exponentials, oscillations, scalars = [], [], []

    def collect(node, orientation=1, inside_denominator=False):
        if node.operator == "*":
            for child in node.children:
                collect(child, orientation, inside_denominator)
        elif node.operator == "/":
            collect(node.children[0], orientation, inside_denominator)
            collect(node.children[1], -orientation, True)
        elif node.operator == "exp":
            exponentials.append((node, orientation))
        elif node.operator in ("sin", "cos"):
            if inside_denominator:
                raise _Unsupported("trigonometric_denominator")
            oscillations.append(node)
        else:
            value = _scalar(node)
            if inside_denominator and value == 0:
                raise _Unsupported("zero_denominator")
            scalars.append(value if orientation == 1 else 1 / value)

    try:
        collect(root)
        if len(exponentials) != 1:
            raise _Unsupported("exponential_factor_count")
        if len(oscillations) != 1:
            raise _Unsupported("trigonometric_factor_count")
        amplitude = math.prod(scalars, start=Fraction(1))
        exponential, orientation = exponentials[0]
        rate, intercept = _affine(exponential.children[0])
        if intercept != 0:
            raise _Unsupported("nonzero_exponential_intercept")
        oscillation = oscillations[0]
        frequency, phase = _affine(oscillation.children[0])
        pi_part = Fraction(-1, 2) if oscillation.operator == "sin" else Fraction(0)
    except _Unsupported as error:
        return StructureRecognition(None, str(error), version=2)
    return StructureRecognition(
        RawCoefficients(amplitude, orientation * rate, frequency, phase, pi_part),
        version=2,
    )
