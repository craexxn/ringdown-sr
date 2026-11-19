"""Bounded-memory covariance estimates for the prospective duration comparison."""

import math
from dataclasses import dataclass
from numbers import Real

import numpy as np
from scipy.linalg import toeplitz
from scipy.linalg.blas import dsyrk
from scipy.signal import periodogram, windows

from .covariance_estimation import (
    CovarianceEstimate,
    CovarianceEstimationError,
    _alphas,
    _candidate,
    _freeze,
    _windows,
)

METHOD = "continuous_blocks_identity_shrinkage_holdout_v1"
WELCH_METHOD = "welch_toeplitz_identity_shrinkage_holdout_v1"
CHUNK_SAMPLES = 65536


@dataclass(frozen=True)
class WelchCovariance:
    """Retain exact diagnostic curves and the finite-lag Toeplitz matrix."""

    raw_covariance: np.ndarray
    frequencies_hz: np.ndarray
    psd: np.ndarray
    acf: np.ndarray
    segments: int
    n_train_samples: int
    method: str = WELCH_METHOD


def empirical_from_series(series, *, n_samples=128, chunk_samples=CHUNK_SAMPLES):
    """Return the zero-mean second moment of consecutive, nonoverlapping blocks.

    A stationary trajectory supplies dependent rows; no independent-row
    statistical interpretation is attached. The summation order is fixed by
    ``chunk_samples`` and never copies the complete trajectory into memory.
    """
    if type(n_samples) is not int or n_samples <= 0:
        raise ValueError("n_samples must be a positive integer.")
    if (
        type(chunk_samples) is not int
        or chunk_samples < n_samples
        or chunk_samples % n_samples
    ):
        raise ValueError("Chunks must contain a positive whole number of windows.")
    if (
        not isinstance(series, np.ndarray)
        or series.ndim != 1
        or series.dtype != np.dtype("float64")
        or series.size == 0
        or series.size % n_samples
    ):
        raise ValueError("Expected a Float64 series with complete nonempty windows.")
    count = series.size // n_samples
    triangle = np.zeros((n_samples, n_samples), dtype=np.float64)
    try:
        with np.errstate(over="raise", invalid="raise", under="ignore"):
            for start in range(0, series.size, chunk_samples):
                chunk = series[start : start + chunk_samples]
                if not np.isfinite(chunk).all():
                    raise ValueError("Training data must be finite.")
                windows = chunk.reshape(-1, n_samples)
                triangle += dsyrk(1.0 / count, windows, trans=1, lower=0)
    except FloatingPointError as error:
        raise CovarianceEstimationError(
            "The training second moment is not representable."
        ) from error
    rows, columns = np.triu_indices(n_samples)
    matrix = np.empty((n_samples, n_samples), dtype=np.float64)
    matrix[rows, columns] = triangle[rows, columns]
    matrix[columns, rows] = triangle[rows, columns]
    if not np.isfinite(matrix).all():
        raise CovarianceEstimationError("The training second moment is nonfinite.")
    return _freeze(matrix)


def estimate_from_raw(
    raw_covariance,
    background_validation,
    *,
    n_train,
    alpha_candidates,
    kappa_max=1e8,
    mean_mode="known_zero",
    structural_rank_bound=None,
    method=METHOD,
):
    """Apply the existing alpha rule to an explicitly dependent-row estimate.

    The validation windows must be independent of training and of one another.
    This function makes no independence claim about the training blocks. The
    numerical candidate evaluator and tie rule are shared with the old method.
    """
    if mean_mode != "known_zero":
        raise ValueError("The population mean must explicitly be known_zero.")
    if type(n_train) is not int or n_train <= 0:
        raise ValueError("n_train must be a positive integer.")
    if structural_rank_bound is not None and (
        type(structural_rank_bound) is not int or structural_rank_bound <= 0
    ):
        raise ValueError("A supplied structural rank bound must be positive.")
    if method not in {METHOD, WELCH_METHOD}:
        raise ValueError("Unknown covariance construction.")
    raw = np.asarray(raw_covariance)
    if (
        raw.dtype != np.dtype("float64")
        or raw.ndim != 2
        or raw.shape[0] == 0
        or raw.shape[0] != raw.shape[1]
        or not np.isfinite(raw).all()
        or not np.array_equal(raw, raw.T)
    ):
        raise ValueError("Expected a finite symmetric Float64 second-moment matrix.")
    raw = _freeze(raw)
    validation = _windows(background_validation, "background_validation")
    if validation.shape[1] != raw.shape[0]:
        raise ValueError("Training and validation dimensions differ.")
    if (
        isinstance(kappa_max, (bool, np.bool_))
        or not isinstance(kappa_max, Real)
        or not math.isfinite(float(kappa_max))
        or kappa_max <= 1
    ):
        raise ValueError("kappa_max must be finite and greater than one.")
    diagonal = raw.diagonal()
    largest = float(diagonal.max())
    mu = largest * float(np.mean(diagonal / largest)) if largest > 0 else 0.0
    if not math.isfinite(mu) or mu <= 0:
        raise CovarianceEstimationError(
            "The training mean variance must be finite and strictly positive.",
            raw_covariance=raw,
            mu=mu,
        )
    candidates, selected, covariance = [], None, None
    for alpha in _alphas(alpha_candidates):
        candidate, matrix = _candidate(
            raw,
            mu,
            alpha,
            validation,
            float(kappa_max),
            n_train=raw.shape[0]
            if structural_rank_bound is None
            else structural_rank_bound,
        )
        candidates.append(candidate)
        if candidate.eligible and (
            selected is None or candidate.score < selected.score
        ):
            selected, covariance = candidate, matrix
    if selected is None:
        raise CovarianceEstimationError(
            "No candidate covariance passed the unchanged validation rule.",
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
        n_train=n_train,
        n_validation=validation.shape[0],
        kappa_max=float(kappa_max),
        mean_mode=mean_mode,
        method=method,
    )


def welch_covariance(
    series,
    *,
    n_samples=128,
    sample_rate_hz=4096,
    nperseg=8192,
    noverlap=4096,
):
    """Average fixed Hann periodograms without loading the whole recording.

    One-sided density values are converted to a two-sided spectrum before
    inverse transformation. No centering, true-variance rescaling, lag
    dewindowing, zero-padding of partial segments, or hidden repair occurs.
    """
    if (
        not isinstance(series, np.ndarray)
        or series.ndim != 1
        or series.dtype != np.dtype("float64")
        or type(n_samples) is not int
        or type(nperseg) is not int
        or type(noverlap) is not int
        or not 0 < n_samples <= nperseg
        or nperseg % 2
        or not 0 <= noverlap < nperseg
        or series.size < nperseg
        or not math.isfinite(sample_rate_hz)
        or sample_rate_hz <= 0
    ):
        raise ValueError("Invalid fixed Welch geometry or input series.")
    step = nperseg - noverlap
    if (series.size - nperseg) % step:
        raise ValueError("The fixed series must end on a complete Welch segment.")
    window = windows.hann(nperseg, sym=False)
    total = np.zeros(nperseg // 2 + 1, dtype=np.float64)
    segments = 0
    for start in range(0, series.size - nperseg + 1, step):
        segment = series[start : start + nperseg]
        if not np.isfinite(segment).all():
            raise ValueError("Welch inputs must be finite.")
        frequencies, spectrum = periodogram(
            segment,
            fs=sample_rate_hz,
            window=window,
            detrend=False,
            return_onesided=True,
            scaling="density",
        )
        total += spectrum
        segments += 1
    psd = total / segments
    if not np.isfinite(psd).all() or np.any(psd < 0):
        raise CovarianceEstimationError("The Welch spectrum is not finite nonnegative.")
    two_sided = psd.copy()
    two_sided[1:-1] *= 0.5
    acf = sample_rate_hz * np.fft.irfft(two_sided, n=nperseg)
    matrix = toeplitz(acf[:n_samples])
    return WelchCovariance(
        raw_covariance=_freeze(matrix),
        frequencies_hz=_freeze(frequencies),
        psd=_freeze(psd),
        acf=_freeze(acf[:n_samples]),
        segments=segments,
        n_train_samples=series.size,
    )
