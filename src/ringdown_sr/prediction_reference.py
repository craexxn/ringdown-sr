"""Bound the original binary64 tree, independently of either actual prediction.

Basic operations use exact rationals and one nearest-even binary64 rounding.
Transcendentals use directed MPFR ranges followed by the frozen one-neighbor
contract. MPFR contexts are local; no hardware rounding mode or search state
is touched. There is deliberately no cache and no observation input.
"""

import math
from fractions import Fraction

import gmpy2

from .losses import _real_array
from .parameter_export import _fingerprint
from .pilot import _json_bytes, _sha256
from .structure import _validated_tree
from .symbolic import ROOT

FORMAT = "ringdown-sr-prediction-reference-1"
PLAN = "docs/search_duration_prediction_plan.md"
PLAN_COMMIT = "9bff8a29030026dcdc2de52640556a73a57fe2a4"
PLAN_SHA256 = "2a215b6f178c085cad6611070124e09e929f35917eba66723f4522c1fe81393c"
PRECISIONS = (128, 256, 512, 1024)
UNIT_ROUNDOFF = Fraction(1, 2**53)
SOURCES = (
    PLAN,
    "src/ringdown_sr/prediction_reference.py",
    "src/ringdown_sr/structure.py",
    "src/ringdown_sr/parameter_export.py",
    "src/ringdown_sr/pilot.py",
    "src/ringdown_sr/losses.py",
    "src/ringdown_sr/symbolic.py",
    "pyproject.toml",
    "uv.lock",
)


class UnresolvedReference(ValueError):
    """The finite interval model cannot certify this evaluation."""


class PredictionVerificationError(ValueError):
    def __init__(self, evidence):
        self.evidence = evidence
        super().__init__(
            f"Prediction reference {evidence['status']}: {evidence['reason']}"
        )


def binding():
    hashes = {name: _sha256((ROOT / name).read_bytes()) for name in SOURCES}
    if hashes[PLAN] != PLAN_SHA256:
        raise ValueError("The frozen prediction reference plan changed.")
    return {
        "plan": PLAN,
        "plan_commit": PLAN_COMMIT,
        "plan_sha256": PLAN_SHA256,
        "source_sha256": hashes,
        "library": {
            "gmpy2": gmpy2.version(),
            "mpfr": gmpy2.mpfr_version(),
            "gmp": gmpy2.mp_version(),
        },
    }


def _rational(value):
    return Fraction(*value.as_integer_ratio())


def _round(value):
    # CPython Fraction.__float__ implements nearest-even including subnormals.
    try:
        rounded = float(value)
    except OverflowError as error:
        raise UnresolvedReference("possible_binary64_overflow") from error
    if not math.isfinite(rounded):
        raise UnresolvedReference("possible_binary64_overflow")
    return Fraction.from_float(rounded)


def _binary(operator, a, b):
    if operator == "+":
        bounds = a[0] + b[0], a[1] + b[1]
    elif operator == "-":
        bounds = a[0] - b[1], a[1] - b[0]
    elif operator == "*":
        products = [x * y for x in a for y in b]
        bounds = min(products), max(products)
    else:
        if b[0] <= 0 <= b[1]:
            raise UnresolvedReference("possible_zero_denominator")
        quotients = [x / y for x in a for y in b]
        bounds = min(quotients), max(quotients)
    return tuple(map(_round, bounds))


def _directed(function, value, precision, rounding):
    # Explicitly set the exponent range and traps, independent of caller state.
    with gmpy2.context(
        precision=precision,
        round=rounding,
        emin=-1073741823,
        emax=1073741823,
        subnormalize=False,
        trap_underflow=True,
        trap_overflow=True,
        trap_invalid=True,
        trap_divzero=True,
        trap_erange=True,
        trap_inexact=False,
        allow_complex=False,
    ):
        if value is None:
            result = gmpy2.const_pi()
        else:
            # Every node endpoint is binary64 and is exact at all four precisions.
            argument = gmpy2.mpfr(gmpy2.mpq(value.numerator, value.denominator))
            result = getattr(gmpy2, function)(argument)
        if not gmpy2.is_finite(result):
            raise UnresolvedReference("nonfinite_mpfr_reference")
        return _rational(result)


def _transcendental(operator, interval, precision, pi):
    low, high = interval
    if operator == "exp" and high >= 1024:
        raise UnresolvedReference("possible_binary64_overflow")

    def endpoint(value, direction):
        if operator == "exp" and value <= -1076:
            return Fraction(0) if direction == gmpy2.RoundDown else Fraction(1, 2**1076)
        return _directed(operator, value, precision, direction)

    lower = min(endpoint(v, gmpy2.RoundDown) for v in interval)
    upper = max(endpoint(v, gmpy2.RoundUp) for v in interval)
    if operator != "exp" and low != high:
        # Extrema occur at pi*(k+offset). Exact division by outward pi bounds
        # conservatively covers possible integer k, even for huge arguments.
        offset = Fraction(1, 2) if operator == "sin" else Fraction(0)
        ratios = [v / p - offset for v in interval for p in pi]
        first, last = math.ceil(min(ratios)), math.floor(max(ratios))
        if first <= last:
            if first % 2 == 0 or first < last:
                upper = Fraction(1)
            if first % 2 == 1 or first < last:
                lower = Fraction(-1)
    low64, high64 = float(_round(lower)), float(_round(upper))
    padded = math.nextafter(low64, -math.inf), math.nextafter(high64, math.inf)
    if not all(map(math.isfinite, padded)):
        raise UnresolvedReference("neighbor_binary64_overflow")
    lower, upper = map(Fraction.from_float, padded)
    if operator == "exp":
        lower = max(Fraction(0), lower)
    else:
        lower, upper = max(Fraction(-1), lower), min(Fraction(1), upper)
    return lower, upper


def _intervals(node, times, precision):
    pi = tuple(
        _directed("pi", None, precision, r) for r in (gmpy2.RoundDown, gmpy2.RoundUp)
    )

    def visit(node, time):
        if node.kind == "constant":
            return node.value, node.value
        if node.kind == "variable":
            return time, time
        # Validate and evaluate both children, even under multiplication by zero.
        children = [visit(child, time) for child in node.children]
        if len(children) == 2:
            return _binary(node.operator, *children)
        return _transcendental(node.operator, children[0], precision, pi)

    return [visit(node, Fraction.from_float(float(t))) for t in times]


def width_check(intervals):
    scale = max(abs(v) for interval in intervals for v in interval)
    width = max(high - low for low, high in intervals)
    return width * width <= UNIT_ROUNDOFF * scale * scale, scale, width


def _fraction_record(value):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def reference(tree, times):
    """Select the first sufficiently narrow enclosure without actual predictions."""
    node = _validated_tree(tree)
    times = _real_array(times, "reference times")
    if times.ndim != 1 or not times.size:
        raise ValueError("Reference times must be a nonempty finite vector.")
    anchor = binding()
    result = {
        "format": FORMAT,
        "binding": anchor,
        "tree_sha256": _sha256(_json_bytes(tree)),
        "times": _fingerprint(times),
        "neighbor_steps": 1,
        "precisions": list(PRECISIONS),
        "unit_roundoff": _fraction_record(UNIT_ROUNDOFF),
        "attempts": [],
    }
    for precision in PRECISIONS:
        try:
            intervals = _intervals(node, times, precision)
            narrow, scale, width = width_check(intervals)
            reason = None if narrow else "reference_width_exceeds_bound"
            result.update(
                precision_bits=precision,
                intervals_hex=[
                    [float(v).hex() for v in interval] for interval in intervals
                ],
                scale=_fraction_record(scale),
                max_width=_fraction_record(width),
                decision_arithmetic="exact_rational",
            )
        except UnresolvedReference as error:
            reason = str(error)
            narrow = False
        result["attempts"].append({"precision_bits": precision, "reason": reason})
        if narrow:
            result.update(
                status="bounded",
                reason=None,
                precision_bits=precision,
                intervals_hex=[
                    [float(v).hex() for v in interval] for interval in intervals
                ],
                scale=_fraction_record(scale),
                max_width=_fraction_record(width),
                width_status="passed",
                decision_arithmetic="exact_rational",
            )
            break
    else:
        result.update(status="indeterminate", reason=reason, width_status="not_passed")
    if binding() != anchor:
        raise ValueError("Reference sources changed during consumption.")
    if (
        _sha256(_json_bytes(tree)) != result["tree_sha256"]
        or _fingerprint(times) != result["times"]
    ):
        raise ValueError("Reference input bits changed during consumption.")
    return result


def membership(record, python_prediction, native_prediction):
    """Check both vectors only after the reference precision has been selected."""
    result = dict(record)
    if result["status"] != "bounded":
        result["membership"] = {"status": "not_attempted"}
        return result
    intervals = [[float.fromhex(v) for v in pair] for pair in record["intervals_hex"]]
    failures = {}
    for name, values in (("python", python_prediction), ("native", native_prediction)):
        try:
            values = _real_array(values, name)
            if values.shape != (len(intervals),):
                raise ValueError("Invalid prediction shape.")
        except ValueError:
            failures[name] = "invalid_or_nonfinite_vector"
            continue
        outside = [
            i
            for i, (v, (lo, hi)) in enumerate(zip(values, intervals, strict=True))
            if not lo <= v <= hi
        ]
        if outside:
            failures[name] = outside
    result.update(
        status="failed" if failures else "passed",
        reason="prediction_outside_reference" if failures else None,
        meaning="compatible_with_bounded_rounding_model",
        membership={"status": "failed" if failures else "passed", "failures": failures},
    )
    return result


def verify_prediction(tree, times, python_prediction, native_prediction):
    evidence = membership(reference(tree, times), python_prediction, native_prediction)
    if evidence["status"] != "passed":
        raise PredictionVerificationError(evidence)
    return evidence
