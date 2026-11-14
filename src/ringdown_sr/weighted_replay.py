"""Read-only backward-error certificates for the confirmed weighted profile.

The original covariance, both Cholesky factors, and both whitening vectors are
bound separately. This certifies small *backward* errors, not forward accuracy
of Q for an arbitrarily ill-conditioned covariance. No fit, regularization,
truth-based tolerance, or comparison of tiny native/Python losses is involved.
"""

import copy
import hashlib
from collections import OrderedDict
from fractions import Fraction

import numpy as np

from . import duration_replay, prediction_reference
from .losses import CovarianceLoss, _real_array, mean_squared_error
from .symbolic import evaluate_tree

FORMAT = "ringdown-sr-weighted-loss-replay-2"
ORDINARY_FORMAT = "ringdown-sr-confirmed-ordinary-loss-replay-1"
_U = Fraction(1, 2**53)
_MAX_FINITE = Fraction.from_float(float(np.finfo(np.float64).max))
_HALF_MIN_SUBNORMAL = Fraction(1, 2**1075)
# Rechecking a front must not repeat dense matrix multiplication per candidate.
# Cache keys consume all covariance/factor bits; returned evidence is copied.
_FACTOR_CACHE = OrderedDict()


def _fingerprint(values):
    encoded = np.ascontiguousarray(values, dtype="<f8")
    return {
        "shape": list(encoded.shape),
        "dtype": "<f8",
        "sha256": hashlib.sha256(encoded.tobytes()).hexdigest(),
    }


def _gamma(operations):
    product = operations * _U
    if product >= 1:
        raise ValueError("Weighted replay exceeds its rounding-bound domain.")
    return product / (1 - product)


def _fraction_record(value):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def _reduction_bounds(samples):
    """Bound the complete sum-of-squares/sqrt/divide/square reference model.

    The sum of rounded squares has relative error at most gamma_N. Taking its
    square root and later squaring contributes two numerator rounding factors;
    dividing and later squaring contributes two more; the final square adds
    one. The rounded sqrt(N) contributes two denominator factors. This model
    is checked against each actual scalar, not presumed for arbitrary BLAS.
    """
    gamma = _gamma(samples)
    if gamma >= 1:
        raise ValueError("Loss reduction exceeds its rounding-bound domain.")
    lower = (1 - gamma) * (1 - _U) ** 5 / (1 + _U) ** 2
    upper = (1 + gamma) * (1 + _U) ** 5 / (1 - _U) ** 2
    return lower, upper


def _reduction_record(samples):
    lower, upper = _reduction_bounds(samples)
    return {
        "model": "sum_squares_sqrt_divide_sqrt_N_then_square",
        "meaning": "checked_scalar_error_not_a_universal_BLAS_guarantee",
        "sum_squares_gamma": _fraction_record(_gamma(samples)),
        "unit_roundoff": _fraction_record(_U),
        "numerator_rounding_factors": 5,
        "denominator_rounding_factors": 2,
        "relative_lower": _fraction_record(lower),
        "relative_upper": _fraction_record(upper),
    }


def _reduction(loss, reference, samples):
    value = duration_replay._loss(loss)
    duration_replay._normal_or_zero(value)
    lower, upper = _reduction_bounds(samples)
    if reference * samples * (1 + _gamma(samples)) > _MAX_FINITE:
        raise ValueError("Loss reduction sum is outside the finite Float64 domain.")
    if not lower * reference <= value <= upper * reference:
        raise ValueError("Loss disagrees with its own residual reduction bound.")


def _ordinary_evidence(
    observed, native, python, raw_loss, replay_loss, table_loss, python_loss, proof
):
    """Use the new scalar contract without changing the frozen duration worker."""
    observed, native, python = (
        _real_array(values, name)
        for values, name in (
            (observed, "observed"),
            (native, "native_prediction"),
            (python, "python_prediction"),
        )
    )
    if (
        observed.ndim != 1
        or not observed.size
        or not (observed.shape == native.shape == python.shape)
    ):
        raise ValueError("Replay needs equal nonempty vectors.")
    for loss in (raw_loss, replay_loss, table_loss, python_loss):
        duration_replay._loss(loss)
    np.testing.assert_allclose([replay_loss, table_loss], raw_loss, rtol=1e-10, atol=0)
    with np.errstate(over="raise", invalid="raise"):
        native_residual, python_residual = observed - native, observed - python
    rn, qn = duration_replay._reference(native_residual)
    rp, qp = duration_replay._reference(python_residual)
    for loss in (raw_loss, replay_loss):
        _reduction(loss, qn, observed.size)
    _reduction(python_loss, qp, observed.size)
    native_mse = mean_squared_error(native_residual)
    python_mse = mean_squared_error(python_residual)
    _reduction(native_mse, qn, observed.size)
    _reduction(python_mse, qp, observed.size)
    if float(python_loss).hex() != python_mse.hex():
        raise ValueError("Recorded Python loss differs from its actual replay.")
    residual_bound = (
        sum(
            (
                2 * abs(a) * abs(b - a) + (b - a) ** 2
                for a, b in zip(rn, rp, strict=True)
            ),
            Fraction(0),
        )
        / observed.size
    )
    lower, upper = _reduction_bounds(observed.size)
    gamma = max(1 - lower, upper - 1)
    bound = residual_bound + gamma * (qn + qp)
    difference = abs(Fraction(python_loss) - Fraction(raw_loss))
    if difference > bound:
        raise ValueError("Independent MSE difference exceeds its residual bound.")
    return {
        "format": ORDINARY_FORMAT,
        "status": "passed",
        "metric": "ordinary_mse",
        "samples": int(observed.size),
        "table_loss": float(table_loss),
        "table_loss_role": "pysr_pandas_csv_value; relative_comparison_only",
        "prediction_replay": proof,
        "native_residual_mse": native_mse,
        "independent_residual_mse": python_mse,
        "reduction_rounding": _reduction_record(observed.size),
        "reduction_gamma": _fraction_record(gamma),
        "residual_difference_bound": float(residual_bound),
        "loss_difference_bound": float(bound),
        "absolute_loss_difference": float(difference),
        "decision_arithmetic": "exact_rational",
        "domain": "normal_float64_or_exact_zero",
    }


def _directed_fraction(value, upwards):
    result = float(value)
    represented = Fraction.from_float(result)
    if (upwards and represented < value) or (not upwards and represented > value):
        result = float(np.nextafter(result, np.inf if upwards else -np.inf))
    return result


def _rounded_nonnegative(value, upwards, exact_zero):
    if not np.isfinite(value).all() or np.any(value < 0):
        raise ValueError("Weighted replay bounds exceed the finite Float64 domain.")
    result = np.where(
        exact_zero, 0.0, np.nextafter(value, np.inf if upwards else -np.inf)
    )
    # Downward rounding of a positive exact result rounded to zero stays zero.
    result = np.maximum(result, 0.0)
    if not np.isfinite(result).all():
        raise ValueError("Weighted replay bounds exceed the finite Float64 domain.")
    return result


def _multiply(a, b, upwards):
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        return _rounded_nonnegative(
            np.multiply(a, b), upwards, (np.asarray(a) == 0) | (np.asarray(b) == 0)
        )


def _divide(a, b, upwards):
    if np.any(np.asarray(b) <= 0):
        raise ValueError("Weighted replay bound has a nonpositive divisor.")
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        return _rounded_nonnegative(np.divide(a, b), upwards, np.asarray(a) == 0)


def _add(a, b, upwards=True):
    with np.errstate(over="ignore", invalid="ignore"):
        return _rounded_nonnegative(
            np.add(a, b), upwards, (np.asarray(a) == 0) & (np.asarray(b) == 0)
        )


def _product_domain(a, b, terms):
    """Exclude overflow of nonzero products and positive partial sums."""
    positive_a = np.abs(a[a != 0])
    positive_b = np.abs(b[b != 0])
    if not positive_a.size or not positive_b.size:
        return
    largest_sum = (
        terms * Fraction(float(positive_a.max())) * Fraction(float(positive_b.max()))
    )
    if largest_sum > _MAX_FINITE:
        raise ValueError("Weighted products are outside the finite Float64 domain.")


def _check_gradual_underflow():
    # A flush-to-zero product implementation does not satisfy this certificate.
    tiny = np.finfo(np.float64).tiny
    a = np.diag([tiny, tiny])
    b = np.diag([0.5, 0.5])
    expected = np.diag([float.fromhex("0x0.8000000000000p-1022")] * 2)
    subnormal = float.fromhex("0x0.0000000000001p-1022")
    subnormal_matrix = np.diag([subnormal, subnormal])
    if (
        not np.array_equal(a @ b, expected)
        or tiny * 0.5 != expected[0, 0]
        or not np.array_equal(subnormal_matrix @ np.eye(2), subnormal_matrix)
    ):
        raise ValueError("Weighted replay requires IEEE gradual underflow.")


def _product_certificate(a, b, target):
    """Enclose a product residual, including every verifier rounding operation.

    For k-term dot products, |fl(AB)-AB| <= gamma_k |A||B| + alpha_k, with
    alpha_k = k * 2^-1075 / (1-k*u). This includes IEEE gradual underflow of
    products; addition of binary64 values is exact when its result is subnormal.
    The absolute product is enclosed by (P_hat +/- alpha_k)/(1 +/- gamma_k).
    The accepted residual is at most gamma_(2k+2) |A||B| + 2*alpha_k, allowing
    original and verifier roundoff. This is a measured backward-error contract,
    not an assertion of exact Cholesky bits or a forward error bound for Q.
    """
    # Julia exports matrices in Fortran order, while archive readers commonly
    # copy them in C order. BLAS can use different reduction paths for those
    # layouts; canonical operands make the serialized proof reproducible.
    a = np.ascontiguousarray(a, dtype=np.float64)
    b = np.ascontiguousarray(b, dtype=np.float64)
    target = np.ascontiguousarray(target, dtype=np.float64)
    terms = a.shape[1]
    _check_gradual_underflow()
    _product_domain(a, b, terms)
    gamma = _gamma(terms)
    limit = _gamma(2 * terms + 2)
    underflow = terms * _HALF_MIN_SUBNORMAL / (1 - terms * _U)
    underflow_upper = _directed_fraction(underflow, True)
    gamma_upper = _directed_fraction(gamma, True)
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        product = a @ b
        absolute_product = np.abs(a) @ np.abs(b)
        difference = np.abs(product - target)
    if not np.isfinite(product).all() or not np.isfinite(absolute_product).all():
        raise ValueError("Weighted product replay is nonfinite.")
    # Evaluate tiny bounds in units of the smallest normal number. Power-of-two
    # scaling is exact here and avoids losing an entire subnormal ULP in each
    # verifier operation. alpha_k / 2^-1022 equals gamma_k exactly.
    scaled = (absolute_product < 2.0**-512) & (difference < 2.0**-512)
    exponents = np.where(scaled, 1022, 0)
    absolute_product = np.ldexp(absolute_product, exponents)
    difference = np.ldexp(difference, exponents)
    underflow_upper = np.where(scaled, gamma_upper, underflow_upper)
    underflow_limit_lower = np.where(
        scaled,
        _directed_fraction(2 * gamma, False),
        _directed_fraction(2 * underflow, False),
    )
    lower_numerator = _rounded_nonnegative(
        np.maximum(absolute_product - underflow_upper, 0),
        False,
        absolute_product <= underflow_upper,
    )
    lower = _divide(lower_numerator, _directed_fraction(1 + gamma, True), False)
    upper = _divide(
        _add(absolute_product, underflow_upper),
        _directed_fraction(1 - gamma, False),
        True,
    )
    # A final subtraction also rounds; one directed step encloses its exact
    # absolute value. Equality of the two floating operands is exactly zero.
    difference_upper = _rounded_nonnegative(difference, True, product == target)
    residual_upper = _add(
        _add(difference_upper, _multiply(gamma_upper, upper, True)), underflow_upper
    )
    permitted_lower = _add(
        _multiply(_directed_fraction(limit, False), lower, False),
        underflow_limit_lower,
        False,
    )
    if np.any(residual_upper > permitted_lower):
        raise ValueError(
            "Weighted factor or whitening violates its backward-error bound."
        )
    positive = lower > 0
    ratio = (
        float(np.max(_divide(residual_upper[positive], lower[positive], True)))
        if np.any(positive)
        else 0.0
    )
    with np.errstate(under="ignore"):
        absolute_bound = np.ldexp(residual_upper, -exponents)
    absolute_bound = _rounded_nonnegative(absolute_bound, True, residual_upper == 0)
    return {
        "status": "passed",
        "dot_product_terms": terms,
        "product_rounding_gamma": _fraction_record(gamma),
        "backward_error_gamma": _fraction_record(limit),
        "product_underflow_bound": _fraction_record(underflow),
        "backward_error_underflow_bound": _fraction_record(2 * underflow),
        "max_relative_residual_upper_on_positive_product_lower_bounds": ratio,
        "entries_without_positive_product_lower_bound": int(
            np.count_nonzero(~positive)
        ),
        "max_absolute_residual_upper": float(np.max(absolute_bound)),
    }


def _factor_certificate(covariance, factor):
    if (
        factor.shape != covariance.shape
        or np.any(np.diag(factor) <= 0)
        or np.any(np.triu(factor, 1) != 0)
    ):
        raise ValueError("Weighted replay requires a positive-diagonal lower factor.")
    covariance_binding = _fingerprint(covariance)
    factor_binding = _fingerprint(factor)
    key = (covariance_binding["sha256"], factor_binding["sha256"], factor.shape)
    if key in _FACTOR_CACHE:
        _FACTOR_CACHE.move_to_end(key)
        return copy.deepcopy(_FACTOR_CACHE[key])
    result = _product_certificate(factor, factor.T, covariance)
    result.update(covariance=covariance_binding, factor=factor_binding)
    if (
        _fingerprint(covariance) != covariance_binding
        or _fingerprint(factor) != factor_binding
    ):
        raise ValueError("Weighted factor inputs changed during verification.")
    _FACTOR_CACHE[key] = copy.deepcopy(result)
    while len(_FACTOR_CACHE) > 2:
        _FACTOR_CACHE.popitem(last=False)
    return result


def verify_loss_replay(
    observed,
    native_prediction,
    python_prediction,
    raw_loss,
    replay_loss,
    table_loss,
    python_loss,
    loss_object,
    *,
    prediction_check=None,
    covariance=None,
    native_factor=None,
    native_whitened=None,
):
    """Check losses using MPFR-bound predictions and each actual whitening.

    The worker supplies a fresh prediction proof; the reading parent must
    recompute it (``candidate_evidence`` does so). This scalar routine does not
    authenticate a caller-supplied prediction certificate. Native factor and
    whitening evidence must come from the objective actually used by the worker.
    """
    if (
        not isinstance(prediction_check, dict)
        or prediction_check.get("format") != prediction_reference.FORMAT
        or prediction_check.get("status") != "passed"
    ):
        raise ValueError("Missing bounded prediction evidence.")
    if loss_object is None:
        if any(
            value is not None for value in (covariance, native_factor, native_whitened)
        ):
            raise ValueError("Unweighted replay must not carry covariance evidence.")
        return _ordinary_evidence(
            observed,
            native_prediction,
            python_prediction,
            raw_loss,
            replay_loss,
            table_loss,
            python_loss,
            prediction_check,
        )
    if not isinstance(loss_object, CovarianceLoss):
        raise TypeError("Weighted replay requires its actual CovarianceLoss object.")
    observed, native, python = (
        _real_array(value, name)
        for value, name in (
            (observed, "observed"),
            (native_prediction, "native_prediction"),
            (python_prediction, "python_prediction"),
        )
    )
    if (
        observed.ndim != 1
        or not observed.size
        or not (observed.shape == native.shape == python.shape)
    ):
        raise ValueError("Weighted replay needs equal nonempty vectors.")
    covariance = _real_array(covariance, "covariance")
    native_factor = _real_array(native_factor, "native_factor")
    native_whitened = _real_array(native_whitened, "native_whitened")
    python_factor = _real_array(loss_object._factor, "python_factor")
    if (
        covariance.shape != (observed.size, observed.size)
        or not np.array_equal(covariance, covariance.T)
        or native_whitened.shape != observed.shape
    ):
        raise ValueError(
            "Weighted replay covariance or whitening has an invalid shape."
        )
    for loss in (raw_loss, replay_loss, table_loss, python_loss):
        duration_replay._loss(loss)
    np.testing.assert_allclose([replay_loss, table_loss], raw_loss, rtol=1e-10, atol=0)
    factor_checks = {
        "native": _factor_certificate(covariance, native_factor),
        "python": _factor_certificate(covariance, python_factor),
    }
    with np.errstate(over="raise", invalid="raise"):
        native_residual = observed - native
        python_residual = observed - python
    python_whitened = loss_object.whiten(python_residual)
    whitening_checks = {
        "native": _product_certificate(native_factor, native_whitened, native_residual),
        "python": _product_certificate(python_factor, python_whitened, python_residual),
    }
    lower, upper = _reduction_bounds(observed.size)
    gamma = max(1 - lower, upper - 1)
    _, native_reference = duration_replay._reference(native_whitened)
    _, python_reference = duration_replay._reference(python_whitened)
    for loss in (raw_loss, replay_loss):
        _reduction(loss, native_reference, observed.size)
    _reduction(python_loss, python_reference, observed.size)
    native_reduction = mean_squared_error(native_whitened)
    python_reduction = loss_object.mean_squared(python_residual)
    _reduction(native_reduction, native_reference, observed.size)
    _reduction(python_reduction, python_reference, observed.size)
    if float(python_loss).hex() != python_reduction.hex():
        raise ValueError("Recorded Python loss differs from its actual replay.")
    return {
        "format": FORMAT,
        "status": "passed",
        "metric": "covariance_q_over_n",
        "samples": int(observed.size),
        "table_loss": float(table_loss),
        "table_loss_role": "pysr_pandas_csv_value; relative_comparison_only",
        "prediction_replay": prediction_check,
        "factor_checks": factor_checks,
        "whitening_checks": whitening_checks,
        "native_whitened_residual": _fingerprint(native_whitened),
        "python_whitened_residual": _fingerprint(python_whitened),
        "native_residual": _fingerprint(native_residual),
        "python_residual": _fingerprint(python_residual),
        "reduction_gamma": _fraction_record(gamma),
        "reduction_rounding": _reduction_record(observed.size),
        "native_reduction_reference": _fraction_record(native_reference),
        "python_reduction_reference": _fraction_record(python_reference),
        "native_reduction": native_reduction,
        "python_reduction": python_reduction,
        "absolute_loss_difference": float(
            abs(Fraction(raw_loss) - Fraction(python_loss))
        ),
        "loss_difference_role": "diagnostic_only; each_own_whitening_is_checked",
        "claim": "backward_error_only; no_forward_Q_accuracy_or_conditioning_claim",
        "decision_arithmetic": "directed_binary64_enclosures_and_exact_rational_reduction",
        "domain": "IEEE_gradual_underflow_products; normal_squares; finite_bounds; no_regularization",
    }


def candidate_evidence(
    candidate, times, observed, covariance=None, *, native_factor=None, loss_object=None
):
    """Recompute MPFR membership and scalar evidence from consumed originals."""
    record = candidate.get("loss_replay")
    if not isinstance(record, dict) or "table_loss" not in record:
        raise ValueError("Missing weighted-profile candidate loss evidence.")
    prediction = evaluate_tree(candidate["tree"], times)
    proof = prediction_reference.verify_prediction(
        candidate["tree"], times, prediction, candidate["prediction"]
    )
    if covariance is None and loss_object is not None:
        raise ValueError("Unweighted replay must not carry a covariance loss object.")
    if covariance is not None and loss_object is None:
        loss_object = CovarianceLoss(covariance)
    return verify_loss_replay(
        observed,
        candidate["prediction"],
        prediction,
        candidate["loss"],
        candidate["julia_reimport_loss"],
        record["table_loss"],
        candidate["python_loss"],
        loss_object,
        prediction_check=proof,
        covariance=covariance,
        native_factor=native_factor,
        native_whitened=candidate.get("native_whitened_residual"),
    )
