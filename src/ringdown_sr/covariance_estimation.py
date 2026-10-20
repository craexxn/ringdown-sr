"""Estimate a fixed covariance from independent zero-mean background windows."""

import math
from dataclasses import dataclass, replace
from numbers import Real

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import LinAlgError, cholesky, norm, solve_triangular
from scipy.linalg.blas import dsyrk


@dataclass(frozen=True)
class CovarianceCandidate:
    """Record one alpha, including rejection before or during scoring.

    Eigenvalues have covariance units. None means a diagnostic was not
    available or not attempted. Scores average over validation windows,
    without dividing the quadratic by the covariance dimension.
    """

    alpha: float
    reason: str | None = None
    eigenvalues: tuple[float, ...] | None = None
    condition_number: float | None = None
    cholesky_success: bool | None = None
    log_determinant: float | None = None
    validation_quadratic_mean: float | None = None
    score: float | None = None

    @property
    def eligible(self) -> bool:
        """Return whether this candidate has a finite usable score."""
        return self.reason is None and self.score is not None


@dataclass(frozen=True, eq=False)
class CovarianceEstimate:
    """Keep the raw and selected matrices and all sorted candidate diagnostics."""

    raw_covariance: NDArray[np.float64]
    covariance: NDArray[np.float64]
    mu: float
    alpha_selected: float
    candidates: tuple[CovarianceCandidate, ...]
    n_train: int
    n_validation: int
    kappa_max: float
    mean_mode: str
    method: str = "empirical_identity_shrinkage_holdout_v1"


class CovarianceEstimationError(ValueError):
    """Keep available diagnostics when covariance estimation cannot succeed."""

    def __init__(
        self,
        message: str,
        *,
        candidates: tuple[CovarianceCandidate, ...] = (),
        raw_covariance: NDArray[np.float64] | None = None,
        mu: float | None = None,
    ) -> None:
        super().__init__(message)
        self.candidates = candidates
        self.raw_covariance = raw_covariance
        self.mu = mu


def _real_array(values: ArrayLike, name: str) -> NDArray[np.float64]:
    try:
        array = np.asarray(values)
        if array.dtype.kind not in "iuf":
            raise ValueError
        with np.errstate(over="raise", invalid="raise"):
            array = array.astype(np.float64, copy=False)
    except (TypeError, ValueError, OverflowError, FloatingPointError) as error:
        raise ValueError(f"{name} must contain finite real numbers.") from error
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain finite real numbers.")
    return array


def _windows(values: ArrayLike, name: str) -> NDArray[np.float64]:
    array = _real_array(values, name)
    if array.ndim != 2 or 0 in array.shape:
        raise ValueError(f"{name} must have nonempty shape (n_windows, n_samples).")
    return array


def _mean_mode(value: str) -> None:
    if not isinstance(value, str) or value != "known_zero":
        raise ValueError('mean_mode must explicitly be "known_zero".')


def _freeze(array: NDArray[np.float64]) -> NDArray[np.float64]:
    # Immutable bytes also prevent callers from re-enabling the WRITEABLE flag.
    return np.frombuffer(array.tobytes(), dtype=np.float64).reshape(array.shape)


def _empirical(windows: NDArray[np.float64]) -> NDArray[np.float64]:
    # Per-column scaling protects squares and preserves covariance units.
    scales = np.max(np.abs(windows), axis=0)
    with np.errstate(under="ignore"):
        normalized = np.divide(
            windows, scales, out=np.zeros_like(windows), where=scales != 0
        )
    triangle = dsyrk(1.0 / windows.shape[0], normalized, trans=1, lower=0)
    rows, columns = np.triu_indices(windows.shape[1])
    try:
        with np.errstate(over="raise", invalid="raise", under="ignore"):
            entries = triangle[rows, columns] * np.maximum(
                scales[rows], scales[columns]
            )
            entries *= np.minimum(scales[rows], scales[columns])
    except FloatingPointError as error:
        raise CovarianceEstimationError(
            "The empirical covariance exceeds the finite float64 range."
        ) from error
    matrix = np.empty((windows.shape[1], windows.shape[1]), dtype=np.float64)
    matrix[rows, columns] = entries
    matrix[columns, rows] = entries
    if not np.all(np.isfinite(matrix)) or np.any(
        (scales > 0) & (matrix.diagonal() == 0)
    ):
        raise CovarianceEstimationError(
            "The empirical variances are not representable in float64."
        )
    return matrix


def empirical_covariance(
    background_train: ArrayLike, *, mean_mode: str
) -> NDArray[np.float64]:
    """Return B.T @ B / M without centering, using the known population mean zero.

    Rows must be independent copies of a background window; correlated
    columns are allowed. Independence and the population mean are caller
    assumptions, not inferred from a finite matrix. A zero matrix is a
    valid second moment here, but cannot be used by estimate_covariance.
    The returned matrix is exactly symmetric, immutable, and in squared
    input units. Unrepresentable positive variances raise an error.
    """
    _mean_mode(mean_mode)
    return _freeze(_empirical(_windows(background_train, "background_train")))


def _alphas(values: ArrayLike) -> tuple[float, ...]:
    array = _real_array(values, "alpha_candidates")
    if array.ndim != 1 or array.size == 0:
        raise ValueError("alpha_candidates must be a nonempty one-dimensional grid.")
    if np.any((array < 0) | (array > 1)):
        raise ValueError("alpha_candidates must lie in [0, 1].")
    if np.unique(array).size != array.size:
        raise ValueError("alpha_candidates must be unique.")
    return tuple(0.0 if alpha == 0 else float(alpha) for alpha in np.sort(array))


def _candidate(
    raw: NDArray[np.float64],
    mu: float,
    alpha: float,
    validation: NDArray[np.float64],
    kappa_max: float,
    *,
    n_train: int,
) -> tuple[CovarianceCandidate, NDArray[np.float64] | None]:
    diagnostic = CovarianceCandidate(alpha)
    if alpha == 0 and n_train < raw.shape[0]:
        # rank(B.T @ B) <= n_train; rounded eigenvalues cannot restore rank.
        return replace(diagnostic, reason="structurally_singular"), None
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
            matrix = (1 - alpha) * raw
            if alpha != 0:
                # Sum nonnegative terms to retain tiny explicit alpha*mu values.
                diagonal = matrix.diagonal() + alpha * mu
                # Equal diagonal and target entries are mathematically unchanged.
                np.fill_diagonal(matrix, np.where(raw.diagonal() == mu, mu, diagonal))
            relative_eigenvalues = np.linalg.eigvalsh(matrix / mu)
            eigenvalues = relative_eigenvalues * mu
        if not np.all(np.isfinite(eigenvalues)) or np.any(
            (relative_eigenvalues > 0) & (eigenvalues == 0)
        ):
            return replace(diagnostic, reason="eigenvalues_out_of_range"), None
    except (FloatingPointError, np.linalg.LinAlgError):
        return replace(diagnostic, reason="matrix_diagnostic_failed"), None
    diagnostic = replace(diagnostic, eigenvalues=tuple(float(v) for v in eigenvalues))
    if relative_eigenvalues[0] <= 0:
        return replace(diagnostic, reason="not_positive_definite"), None
    condition = float(relative_eigenvalues[-1]) / float(relative_eigenvalues[0])
    if not math.isfinite(condition):
        return replace(diagnostic, reason="condition_not_finite"), None
    diagnostic = replace(diagnostic, condition_number=condition)
    if condition > kappa_max:
        return replace(diagnostic, reason="condition_limit_exceeded"), None
    try:
        factor = cholesky(matrix, lower=True, check_finite=False)
    except LinAlgError:
        return replace(
            diagnostic, reason="cholesky_failed", cholesky_success=False
        ), None
    if not np.all(np.isfinite(factor)):
        return replace(
            diagnostic, reason="cholesky_nonfinite", cholesky_success=False
        ), None
    diagnostic = replace(diagnostic, cholesky_success=True)
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
            logdet = 2 * float(np.log(factor.diagonal()).sum())
            if not math.isfinite(logdet):
                raise FloatingPointError
            diagnostic = replace(diagnostic, log_determinant=logdet)
            transformed = solve_triangular(
                factor, validation.T, lower=True, check_finite=False
            )
            if not np.all(np.isfinite(transformed)):
                raise FloatingPointError
            scaled_norm = float(
                norm(
                    (transformed / math.sqrt(validation.shape[0])).ravel(),
                    check_finite=False,
                )
            )
            quadratic = scaled_norm * scaled_norm
            if not math.isfinite(quadratic):
                raise FloatingPointError
            diagnostic = replace(diagnostic, validation_quadratic_mean=quadratic)
            score = logdet + quadratic
        if not math.isfinite(score):
            raise FloatingPointError
    except (FloatingPointError, LinAlgError, OverflowError):
        return replace(diagnostic, reason="validation_score_out_of_range"), None
    return replace(diagnostic, score=score), matrix


def estimate_covariance(
    background_train: ArrayLike,
    background_validation: ArrayLike,
    *,
    alpha_candidates: ArrayLike,
    kappa_max: float,
    mean_mode: str,
) -> CovarianceEstimate:
    """Select (1-alpha)*S + alpha*trace(S)/N*I using held-out Gaussian scores.

    Both matrices contain independent zero-mean windows with the same
    distribution, sampling and sample order. Train and validation roles
    must be independent; these assumptions cannot be checked from arrays.
    S is estimated only from training. The score is logdet(C) plus the
    mean validation quadratic; it is not Q/N. Candidates are sorted and
    exact score ties prefer smaller alpha. Condition <= kappa_max is
    allowed. Alpha zero is rejected structurally when n_train < n_samples.
    There is no refit, matrix repair, hidden alpha or fallback.
    No RNG, signal truth or analytic covariance is accessed.
    """
    _mean_mode(mean_mode)
    train = _windows(background_train, "background_train")
    validation = _windows(background_validation, "background_validation")
    if train.shape[1] != validation.shape[1]:
        raise ValueError(
            "background_train and background_validation dimensions must match."
        )
    alphas = _alphas(alpha_candidates)
    if isinstance(kappa_max, (bool, np.bool_)) or not isinstance(kappa_max, Real):
        raise TypeError("kappa_max must be a finite real number greater than one.")
    try:
        kappa_max = float(kappa_max)
    except OverflowError as error:
        raise ValueError("kappa_max must be finite in float64.") from error
    if not math.isfinite(kappa_max) or kappa_max <= 1:
        raise ValueError("kappa_max must be a finite real number greater than one.")
    raw = _freeze(_empirical(train))
    diagonal = raw.diagonal()
    largest = float(diagonal.max())
    with np.errstate(under="ignore"):
        mu = largest * float(np.mean(diagonal / largest)) if largest > 0 else 0.0
    if not math.isfinite(mu) or mu <= 0:
        raise CovarianceEstimationError(
            "The training mean variance must be finite and strictly positive.",
            raw_covariance=raw,
            mu=mu,
        )
    candidates = []
    selected = None
    covariance = None
    for alpha in alphas:
        candidate, matrix = _candidate(
            raw, mu, alpha, validation, kappa_max, n_train=train.shape[0]
        )
        candidates.append(candidate)
        if candidate.eligible and (
            selected is None or candidate.score < selected.score
        ):
            selected, covariance = candidate, matrix
    if selected is None:
        raise CovarianceEstimationError(
            "No alpha candidate produced a usable covariance and validation score.",
            candidates=tuple(candidates),
            raw_covariance=raw,
            mu=mu,
        )
    return CovarianceEstimate(
        raw_covariance=raw,
        covariance=_freeze(covariance),
        mu=mu,
        alpha_selected=selected.alpha,
        candidates=tuple(candidates),
        n_train=train.shape[0],
        n_validation=validation.shape[0],
        kappa_max=kappa_max,
        mean_mode=mean_mode,
    )
