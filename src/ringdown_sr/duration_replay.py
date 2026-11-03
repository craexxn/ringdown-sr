"""Versioned ordinary-MSE evidence for the duration study, without fitting."""

import math
import sys
from fractions import Fraction

import numpy as np

from .losses import _real_array, mean_squared_error
from .symbolic import _check_prediction_replay, evaluate_tree

FORMAT = "ringdown-sr-duration-loss-replay-1"
_UNIT_ROUNDOFF = Fraction(1, 2**53)
_MIN_NORMAL = Fraction.from_float(sys.float_info.min)
_MAX_FINITE = Fraction.from_float(sys.float_info.max)


def candidate_evidence(candidate, times, observed):
    """Recompute evidence independently in the parent from consumed artifacts."""
    record = candidate.get("loss_replay")
    if not isinstance(record, dict) or "table_loss" not in record:
        raise ValueError("Missing duration candidate loss evidence.")
    return verify_loss_replay(
        observed,
        candidate["prediction"],
        evaluate_tree(candidate["tree"], times),
        candidate["loss"],
        candidate["julia_reimport_loss"],
        record["table_loss"],
        candidate["python_loss"],
        None,
    )


def _loss(value):
    if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
        raise ValueError("Replay losses must be finite nonnegative scalars.")
    return Fraction(value)


def _normal_or_zero(value):
    if value and not _MIN_NORMAL <= value <= _MAX_FINITE:
        raise ValueError("MSE reduction is outside the normal Float64 domain.")


def _reference(residual):
    values = [Fraction.from_float(float(value)) for value in residual]
    squares = [value * value for value in values]
    for square in squares:
        _normal_or_zero(square)
    total = sum(squares, Fraction(0))
    _normal_or_zero(total)
    mean = total / len(values)
    _normal_or_zero(mean)
    return values, mean


def _reduction(loss, reference, gamma):
    difference = abs(_loss(loss) - reference)
    if difference > gamma * reference:
        raise ValueError("Loss disagrees with its own residual reduction bound.")


def verify_loss_replay(
    observed,
    native_prediction,
    python_prediction,
    raw_loss,
    replay_loss,
    table_loss,
    python_loss,
    loss_object,
):
    """Check each loss against its own residuals before comparing the replays.

    All decisions involving reduction bounds use exact rational arithmetic.
    The normal-domain check deliberately fails closed on under/overflow.
    No truth, candidate selection, fitting or covariance model is accepted.
    """
    if loss_object is not None:
        raise ValueError("Duration replay is defined only for ordinary MSE.")
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
        raise ValueError("Replay needs equal nonempty vectors.")
    for loss in (raw_loss, replay_loss, table_loss, python_loss):
        _loss(loss)
    prediction_check = _check_prediction_replay(python, native)
    np.testing.assert_allclose([replay_loss, table_loss], raw_loss, rtol=1e-10, atol=0)
    k = observed.size + 2
    ku = k * _UNIT_ROUNDOFF
    if ku >= 1:
        raise ValueError("MSE reduction exceeds its rounding bound domain.")
    gamma = ku / (1 - ku)
    with np.errstate(over="raise", invalid="raise"):
        native_residual = observed - native
        python_residual = observed - python
    rn, qn = _reference(native_residual)
    rp, qp = _reference(python_residual)
    for loss in (raw_loss, replay_loss, table_loss):
        _reduction(loss, qn, gamma)
    _reduction(python_loss, qp, gamma)
    native_mse = mean_squared_error(native_residual)
    independent_mse = mean_squared_error(python_residual)
    _reduction(native_mse, qn, gamma)
    _reduction(independent_mse, qp, gamma)
    if float(python_loss).hex() != independent_mse.hex():
        raise ValueError("Recorded Python loss differs from its actual replay.")
    difference_bound = (
        sum(
            (
                2 * abs(a) * abs(b - a) + (b - a) ** 2
                for a, b in zip(rn, rp, strict=True)
            ),
            Fraction(0),
        )
        / observed.size
    )
    bound = difference_bound + gamma * (qn + qp)
    difference = abs(_loss(python_loss) - _loss(raw_loss))
    if difference > bound:
        raise ValueError("Independent MSE difference exceeds its residual bound.")
    return {
        "format": FORMAT,
        "status": "passed",
        "metric": "ordinary_mse",
        "samples": int(observed.size),
        "table_loss": float(table_loss),
        "native_residual_mse": native_mse,
        "independent_residual_mse": independent_mse,
        "prediction_replay": prediction_check,
        "reduction_gamma": float(gamma),
        "residual_difference_bound": float(difference_bound),
        "loss_difference_bound": float(bound),
        "absolute_loss_difference": float(difference),
        "decision_arithmetic": "exact_rational",
        "domain": "normal_float64_or_exact_zero",
    }
