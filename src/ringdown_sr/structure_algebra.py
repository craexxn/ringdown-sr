"""Bounded exact expressions and directed real intervals for structure proofs.

This is separate from the historical binary64 prediction contract. No CAS,
floating-point tolerance, reference signal or fitted parameter enters this module.
"""

import math
from dataclasses import dataclass, field
from fractions import Fraction

import gmpy2


class Unresolved(ValueError):
    """The declared finite proof system cannot decide this obligation."""


class NowhereDefined(ValueError):
    """An original denominator is identically zero on its possible domain."""


@dataclass(frozen=True)
class Limits:
    nodes: int = 4096
    terms: int = 256
    roots: int = 4096
    steps: int = 10000
    rational_bits: int = 16384
    precisions: tuple[int, ...] = (128, 256, 512, 1024)


LIMITS = Limits()


def rational_record(value):
    """Hexadecimal integers avoid decimal conversion limits and precision loss."""
    return {
        "numerator_hex": hex(value.numerator),
        "denominator_hex": hex(value.denominator),
    }


@dataclass(frozen=True)
class Expr:
    op: str
    args: tuple["Expr", ...] = ()
    value: Fraction = Fraction(0)
    size: int = field(default=1, compare=False)

    def record(self):
        if self.op == "q":
            return {"kind": "rational", **rational_record(self.value)}
        return {"kind": self.op, "children": [a.record() for a in self.args]}


ZERO, ONE = Expr("q"), Expr("q", value=Fraction(1))
TIME, PI = Expr("t"), Expr("pi")


class Algebra:
    """A finite rational-ring normalizer with explicit elementary identities."""

    def __init__(self, limits=LIMITS):
        self.limits = limits
        self.steps = 0
        self.root_count = 0

    def tick(self, count=1):
        self.steps += count
        if self.steps > self.limits.steps:
            raise Unresolved("analysis_step_limit")

    def check_fraction(self, value):
        if (
            max(value.numerator.bit_length(), value.denominator.bit_length())
            > self.limits.rational_bits
        ):
            raise Unresolved("rational_bit_limit")
        return value

    def q(self, value):
        return Expr("q", value=self.check_fraction(Fraction(value)))

    def node(self, op, *args):
        self.tick()
        size = 1 + sum(a.size for a in args)
        if size > self.limits.nodes:
            raise Unresolved("analysis_node_limit")
        return Expr(op, args, size=size)

    def neg(self, value):
        return self.mul(self.q(-1), value)

    def add(self, *values):
        self.tick()
        items = [a for v in values for a in (v.args if v.op == "add" else (v,))]
        if len(items) > self.limits.terms:
            raise Unresolved("normalized_term_limit")
        grouped = {}
        for item in items:
            coefficient, basis = Fraction(1), item
            if item.op == "q":
                coefficient, basis = item.value, ONE
            elif item.op == "mul" and item.args[0].op == "q":
                coefficient = item.args[0].value
                rest = item.args[1:]
                basis = rest[0] if len(rest) == 1 else self.node("mul", *rest)
            grouped[basis] = self.check_fraction(
                grouped.get(basis, Fraction(0)) + coefficient
            )
        terms = [self.mul(self.q(c), b) for b, c in grouped.items() if c]
        if not terms:
            return ZERO
        terms.sort(key=repr)
        return terms[0] if len(terms) == 1 else self.node("add", *terms)

    def mul(self, *values):
        self.tick()
        coefficient = Fraction(1)
        powers = {}
        exponents = []

        def collect(value, power=1):
            nonlocal coefficient
            self.tick()
            if value.op == "mul":
                for arg in value.args:
                    collect(arg, power)
            elif value.op == "inv":
                collect(value.args[0], -power)
            elif value.op == "q":
                if not value.value and power < 0:
                    raise NowhereDefined("identically_zero_denominator")
                # Multiplication/division can at most double the current bit bound.
                coefficient = self.check_fraction(
                    coefficient * (value.value if power == 1 else 1 / value.value)
                )
            elif value.op == "exp":
                exponents.append(
                    value.args[0] if power == 1 else self.neg(value.args[0])
                )
            else:
                powers[value] = powers.get(value, 0) + power

        for value in values:
            collect(value)
        # Children and denominators were visited before this zero reduction.
        if not coefficient:
            return ZERO
        factors = []
        for value, power in sorted(powers.items(), key=lambda item: repr(item[0])):
            if len(factors) + abs(power) > self.limits.nodes:
                raise Unresolved("analysis_node_limit")
            factors.extend(
                [value if power > 0 else self.node("inv", value)] * abs(power)
            )
        if exponents:
            exponent = self.add(*exponents)
            if exponent != ZERO:
                factors.append(self.node("exp", exponent))
        factors.sort(key=repr)
        if coefficient != 1 or not factors:
            factors.insert(0, self.q(coefficient))
        return factors[0] if len(factors) == 1 else self.node("mul", *factors)

    def div(self, numerator, denominator):
        if denominator == ZERO:
            raise NowhereDefined("identically_zero_denominator")
        return self.mul(numerator, self.node("inv", denominator))

    def unary(self, op, arg):
        if arg == ZERO:
            return ZERO if op == "sin" else ONE
        # Exact pi occurs only in derived root expressions, never by float snapping.
        multiple = Fraction(1) if arg == PI else None
        if (
            arg.op == "mul"
            and len(arg.args) == 2
            and arg.args[0].op == "q"
            and arg.args[1] == PI
        ):
            multiple = arg.args[0].value
        if (
            op in ("sin", "cos")
            and multiple is not None
            and (2 * multiple).denominator == 1
        ):
            quadrant = int(2 * multiple) % 4
            return self.q(((0, 1, 0, -1) if op == "sin" else (1, 0, -1, 0))[quadrant])
        return self.node(op, arg)

    def affine(self, value):
        """Return exact slope/intercept, refusing nonlinear products."""
        self.tick()
        if value == TIME:
            return ONE, ZERO
        if constant(value):
            return ZERO, value
        if value.op == "add":
            pairs = [self.affine(a) for a in value.args]
            return self.add(*(p[0] for p in pairs)), self.add(*(p[1] for p in pairs))
        if value.op == "mul":
            slope, intercept = ZERO, ONE
            for arg in value.args:
                a, b = self.affine(arg)
                if slope != ZERO and a != ZERO:
                    raise Unresolved("nonaffine_argument")
                slope, intercept = (
                    self.add(self.mul(slope, b), self.mul(intercept, a)),
                    self.mul(intercept, b),
                )
            return slope, intercept
        raise Unresolved("nonaffine_argument")

    def interval(self, expr, precision, time=None):
        """Outward MPFR bounds; every transcendental endpoint is exact binary."""
        self.tick()

        def directed(value, rounding, function=None):
            with gmpy2.context(
                precision=precision,
                round=rounding,
                emin=-self.limits.rational_bits,
                emax=self.limits.rational_bits,
                subnormalize=False,
                trap_underflow=True,
                trap_overflow=True,
                trap_invalid=True,
                trap_divzero=True,
                trap_erange=True,
                trap_inexact=False,
                allow_complex=False,
            ):
                if function == "pi":
                    number = gmpy2.const_pi()
                else:
                    number = gmpy2.mpfr(gmpy2.mpq(value.numerator, value.denominator))
                    if function:
                        number = getattr(gmpy2, function)(number)
                if not gmpy2.is_finite(number):
                    raise Unresolved("nonfinite_interval")
                numerator, denominator = number.as_integer_ratio()
                return self.check_fraction(Fraction(int(numerator), int(denominator)))

        def outward(low, high):
            return directed(low, gmpy2.RoundDown), directed(high, gmpy2.RoundUp)

        try:
            if expr.op == "q":
                return outward(expr.value, expr.value)
            if expr.op == "pi":
                return tuple(
                    directed(None, r, "pi") for r in (gmpy2.RoundDown, gmpy2.RoundUp)
                )
            if expr.op == "t":
                if time is None:
                    raise Unresolved("nonconstant_coefficient")
                return outward(*time)
            args = [self.interval(a, precision, time) for a in expr.args]
            if expr.op == "add":
                return outward(sum(a[0] for a in args), sum(a[1] for a in args))
            if expr.op == "mul":
                result = (Fraction(1), Fraction(1))
                for arg in args:
                    products = [a * b for a in result for b in arg]
                    result = outward(min(products), max(products))
                return result
            if expr.op == "inv":
                low, high = args[0]
                if low <= 0 <= high:
                    raise Unresolved("interval_contains_zero_denominator")
                return outward(1 / high, 1 / low)
            low, high = args[0]
            if expr.op == "exp":
                return directed(low, gmpy2.RoundDown, "exp"), directed(
                    high, gmpy2.RoundUp, "exp"
                )
            if expr.op not in ("sin", "cos"):
                raise Unresolved("unsupported_interval_operator")
            lower = min(directed(x, gmpy2.RoundDown, expr.op) for x in (low, high))
            upper = max(directed(x, gmpy2.RoundUp, expr.op) for x in (low, high))
            pi = self.interval(PI, precision)
            offset = Fraction(1, 2) if expr.op == "sin" else Fraction(0)
            ratios = [x / p - offset for x in (low, high) for p in pi]
            first, last = math.ceil(min(ratios)), math.floor(max(ratios))
            if first <= last:
                if first % 2 == 0 or first < last:
                    upper = Fraction(1)
                if first % 2 or first < last:
                    lower = Fraction(-1)
            return lower, upper
        except (OverflowError, ValueError, ZeroDivisionError) as error:
            if isinstance(error, Unresolved):
                raise
            raise Unresolved("interval_arithmetic_limit") from error

    def sign(self, expr):
        """Return a certificate, never treating an interval containing zero as zero."""
        if expr.op == "q":
            return (expr.value > 0) - (expr.value < 0), {
                "rule_id": "exact_rational_sign",
                "expression": expr.record(),
            }
        last = "sign_unresolved"
        for precision in self.limits.precisions:
            try:
                low, high = self.interval(expr, precision)
            except Unresolved as error:
                last = str(error)
                continue
            if low > 0 or high < 0:
                return (1 if low > 0 else -1), {
                    "rule_id": "directed_mpfr_sign",
                    "precision_bits": precision,
                    "expression": expr.record(),
                    "lower": rational_record(low),
                    "upper": rational_record(high),
                }
        raise Unresolved(last)


def constant(expr):
    return expr.op != "t" and all(constant(a) for a in expr.args)
