"""Fit one known damped sinusoid by separable bounded least squares."""

import math
from dataclasses import dataclass
from numbers import Integral

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import least_squares

from ringdown_sr.losses import CovarianceLoss, mean_squared_error


@dataclass(frozen=True)
class FitAttempt:
    """Record each supplied start, including failed or exhausted searches."""

    initial_frequency_hz: float
    initial_decay_time_s: float
    converged: bool
    usable: bool
    status: int | None
    nfev: int | None
    scaled_mse: float | None
    message: str


@dataclass(frozen=True)
class ReferenceFit:
    """Return canonical parameters, predictions, losses, and solver diagnostics."""

    amplitude: float
    frequency_hz: float
    decay_time_s: float
    phase_rad: float
    prediction: NDArray[np.float64]
    residual: NDArray[np.float64]
    ordinary_mse: float
    covariance_mean_squared: float | None
    selected_start_index: int
    active_mask: tuple[int, int]
    nonlinear_jacobian_rank: int
    attempts: tuple[FitAttempt, ...]


class ReferenceFitError(RuntimeError):
    """Retain diagnostics when no supplied start yields a usable convergence."""

    def __init__(self, attempts: tuple[FitAttempt, ...]) -> None:
        super().__init__("No starting point produced a usable converged reference fit.")
        self.attempts = attempts


def _array(values: ArrayLike, name: str) -> NDArray[np.float64]:
    try:
        array = np.asarray(values)
        if not np.issubdtype(array.dtype, np.number) or np.iscomplexobj(array):
            raise ValueError
        with np.errstate(over="raise", invalid="raise"):
            array = array.astype(np.float64, copy=False)
    except (ValueError, TypeError, OverflowError, FloatingPointError) as error:
        raise ValueError(f"{name} must contain finite real numbers.") from error
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain finite real numbers.")
    return array


def _bounds(values: ArrayLike, name: str) -> NDArray[np.float64]:
    bounds = _array(values, name)
    if bounds.shape != (2,) or not 0 < bounds[0] < bounds[1]:
        raise ValueError(f"{name} must contain two increasing positive bounds.")
    return bounds


def fit_ringdown(
    time_s: ArrayLike,
    observed: ArrayLike,
    *,
    frequency_bounds_hz: tuple[float, float],
    decay_time_bounds_s: tuple[float, float],
    initial_points: ArrayLike,
    covariance: ArrayLike | None = None,
    max_nfev: int = 1000,
) -> ReferenceFit:
    """Fit exp(-t/tau) * (a*cos(2*pi*f*t) + b*sin(2*pi*f*t)).

    Times must start at zero and contain at least five uniformly spaced
    samples. Frequency bounds must lie strictly between zero and Nyquist;
    decay-time bounds must be positive. Every explicit (f, tau) start must
    be strictly inside both bounds. No true parameters or hidden starts
    are used. The covariance, when supplied, is fixed and positive definite.

    Linear coefficients are solved at each nonlinear trial. Both data and
    basis columns are whitened for a covariance-weighted fit. Constant data
    scaling protects tiny amplitudes without changing the minimizer.
    Multiple local searches do not guarantee a global minimum or identifiable
    physical parameters; inspect bounds, Jacobian rank, and all attempts.
    """
    times = _array(time_s, "time_s")
    values = _array(observed, "observed")
    if times.ndim != 1 or times.size < 5:
        raise ValueError(
            "time_s must be a one-dimensional array with at least 5 samples."
        )
    if values.shape != times.shape:
        raise ValueError("observed must have the same one-dimensional shape as time_s.")
    if times[0] != 0 or np.any(np.diff(times) <= 0):
        raise ValueError("time_s must start at zero and be strictly increasing.")
    spacing = times[1]
    expected = np.arange(times.size) * spacing
    if not np.allclose(times, expected, rtol=64 * np.finfo(float).eps, atol=0):
        raise ValueError("time_s must be uniformly spaced.")
    frequency_bounds = _bounds(frequency_bounds_hz, "frequency_bounds_hz")
    decay_bounds = _bounds(decay_time_bounds_s, "decay_time_bounds_s")
    if frequency_bounds[1] * spacing >= 0.5:
        raise ValueError("frequency_bounds_hz must lie strictly below Nyquist.")
    starts = _array(initial_points, "initial_points")
    if starts.ndim != 2 or starts.shape[1] != 2 or starts.shape[0] == 0:
        raise ValueError(
            "initial_points must have shape (n_starts, 2), with n_starts > 0."
        )
    lower_physical = np.array([frequency_bounds[0], decay_bounds[0]])
    upper_physical = np.array([frequency_bounds[1], decay_bounds[1]])
    if np.any(starts <= lower_physical) or np.any(starts >= upper_physical):
        raise ValueError("initial_points must be strictly inside the supplied bounds.")
    if isinstance(max_nfev, (bool, np.bool_)) or not isinstance(max_nfev, Integral):
        raise TypeError("max_nfev must be a positive integer.")
    if max_nfev < 1:
        raise ValueError("max_nfev must be a positive integer.")
    data_scale = float(np.max(np.abs(values)))
    if data_scale == 0:
        raise ValueError(
            "observed must be nonzero; a zero signal has no identifiable f or tau."
        )
    weight = None if covariance is None else CovarianceLoss(covariance)
    if weight is not None and weight.n_samples != times.size:
        raise ValueError("covariance dimension must match the sample count.")

    def whiten(vector: NDArray[np.float64]) -> NDArray[np.float64]:
        return vector if weight is None else weight.whiten(vector)

    weighted_data = whiten(values / data_scale)
    weight_scale = float(np.max(np.abs(weighted_data)))
    if weight_scale == 0:
        raise ValueError("Whitened data underflowed the float64 range.")
    target = weighted_data / weight_scale
    span = float(times[-1])
    log_span = math.log(span)
    scaled_time = times / span

    def coordinates(points: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.stack(
            (points[..., 0] * span, np.log(points[..., 1]) - log_span), axis=-1
        )

    lower, upper = coordinates(np.stack((lower_physical, upper_physical)))
    transformed_starts = coordinates(starts)
    if (
        not np.all(np.isfinite([lower, upper]))
        or np.any(lower >= upper)
        or np.any(transformed_starts <= lower)
        or np.any(transformed_starts >= upper)
    ):
        raise ValueError(
            "Bounds or initial_points lose separation in float64 coordinates."
        )

    def project(parameters: NDArray[np.float64]):
        tau = math.exp(float(parameters[1]) + log_span)
        with np.errstate(
            over="ignore", under="ignore", invalid="raise", divide="raise"
        ):
            envelope = np.exp(-times / tau)
            angle = 2 * np.pi * parameters[0] * scaled_time
            basis = envelope[:, None] * np.column_stack((np.cos(angle), np.sin(angle)))
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            design = (
                np.column_stack([whiten(column) for column in basis.T]) / weight_scale
            )
        if not np.all(np.isfinite(design)):
            raise ValueError("The weighted basis exceeds the float64 range.")
        coefficients, _, rank, _ = np.linalg.lstsq(design, target, rcond=None)
        if rank != 2:
            raise ValueError(
                "The sampled sine/cosine basis is numerically rank deficient."
            )
        return design @ coefficients - target, basis, coefficients

    attempts: list[FitAttempt] = []
    best = None
    best_score = math.inf
    for index, (initial, transformed) in enumerate(
        zip(starts, transformed_starts, strict=True)
    ):
        solution = None
        score = None
        try:
            solution = least_squares(
                lambda parameters: project(parameters)[0],
                transformed,
                bounds=(lower, upper),
                method="trf",
                jac="3-point",
                x_scale="jac",
                loss="linear",
                ftol=1e-10,
                xtol=1e-10,
                gtol=1e-10,
                max_nfev=int(max_nfev),
            )
            score = mean_squared_error(solution.fun)
            if not solution.success:
                attempts.append(
                    FitAttempt(
                        *map(float, initial),
                        False,
                        False,
                        int(solution.status),
                        int(solution.nfev),
                        score,
                        str(solution.message),
                    )
                )
                continue
            _, basis, coefficients = project(solution.x)
            with np.errstate(over="raise", invalid="raise"):
                prediction = (basis @ coefficients) * data_scale
                residual = values - prediction
            ordinary_mse = mean_squared_error(residual)
            weighted_mse = None if weight is None else weight.mean_squared(residual)
            amplitude = math.hypot(*coefficients) * data_scale
            if not math.isfinite(amplitude):
                raise ValueError("The fitted amplitude exceeds the float64 range.")
            phase = (math.atan2(-coefficients[1], coefficients[0]) + math.pi) % (
                2 * math.pi
            ) - math.pi
            rank = int(np.linalg.matrix_rank(solution.jac))
            attempts.append(
                FitAttempt(
                    *map(float, initial),
                    True,
                    True,
                    int(solution.status),
                    int(solution.nfev),
                    score,
                    str(solution.message),
                )
            )
            if score < best_score:
                best_score = score
                best = (
                    amplitude,
                    float(solution.x[0] / span),
                    math.exp(float(solution.x[1]) + log_span),
                    phase,
                    prediction,
                    residual,
                    ordinary_mse,
                    weighted_mse,
                    index,
                    tuple(map(int, solution.active_mask)),
                    rank,
                )
        except (
            ValueError,
            FloatingPointError,
            OverflowError,
            np.linalg.LinAlgError,
        ) as error:
            attempts.append(
                FitAttempt(
                    *map(float, initial),
                    False if solution is None else bool(solution.success),
                    False,
                    None if solution is None else int(solution.status),
                    None if solution is None else int(solution.nfev),
                    score,
                    str(error),
                )
            )
    if best is None:
        raise ReferenceFitError(tuple(attempts))
    best[4].setflags(write=False)
    best[5].setflags(write=False)
    return ReferenceFit(*best, tuple(attempts))
