"""Generate white or stationary AR(1) Gaussian noise with an explicit RNG."""

import math
from numbers import Integral, Real

import numpy as np
from numpy.typing import NDArray


def gaussian_white_noise(
    n_samples: int,
    *,
    standard_deviation: float,
    rng: np.random.Generator,
) -> NDArray[np.float64]:
    """Draw independent N(0, standard_deviation**2) samples.

    The standard deviation has the same units as the signal amplitude.
    It describes the generating distribution; the realized samples are
    neither centered nor rescaled. The caller supplies and owns the RNG
    state, including the choice of bit generator and seed. Global NumPy
    random state is not used. No signal-dependent SNR scaling is applied.
    """
    if isinstance(n_samples, (bool, np.bool_)) or not isinstance(n_samples, Integral):
        raise TypeError("n_samples must be a positive integer.")
    if n_samples < 1:
        raise ValueError("n_samples must be a positive integer.")
    if isinstance(standard_deviation, (bool, np.bool_)) or not isinstance(
        standard_deviation, Real
    ):
        raise TypeError("standard_deviation must be a finite real scalar.")
    standard_deviation = float(standard_deviation)
    if not np.isfinite(standard_deviation) or standard_deviation < 0:
        raise ValueError("standard_deviation must be finite and nonnegative.")
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator.")

    values = rng.normal(loc=0.0, scale=standard_deviation, size=n_samples)
    if not np.all(np.isfinite(values)):
        raise ValueError("Noise parameters produce non-finite sample values.")
    return values


def _ar1_parameters(n_samples, standard_deviation, correlation):
    if isinstance(n_samples, (bool, np.bool_)) or not isinstance(n_samples, Integral):
        raise TypeError("n_samples must be a positive integer.")
    if n_samples < 1:
        raise ValueError("n_samples must be a positive integer.")
    for name, value in (
        ("standard_deviation", standard_deviation),
        ("correlation", correlation),
    ):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
            raise TypeError(f"{name} must be a finite real scalar.")
    sigma, rho = float(standard_deviation), float(correlation)
    if not math.isfinite(sigma) or sigma < 0:
        raise ValueError("standard_deviation must be finite and nonnegative.")
    if not math.isfinite(rho) or not -1 < rho < 1:
        raise ValueError("correlation must be finite and strictly between -1 and 1.")
    return sigma, rho


def gaussian_ar1_noise(
    n_samples: int,
    *,
    standard_deviation: float,
    correlation: float,
    rng: np.random.Generator,
) -> NDArray[np.float64]:
    """Draw stationary Gaussian AR(1) noise with marginal standard deviation.

    For one standard_normal(n_samples, dtype=float64) call, set u[0]=z[0]
    and u[k]=rho*u[k-1]+sqrt(1-rho**2)*z[k], then return sigma*u.
    Thus covariance[i,j]=sigma**2*rho**abs(i-j) from the first sample.
    No zero start, burn-in, sample centering, or SNR normalization is used.
    Invalid arguments are rejected before advancing the supplied Generator.
    """
    sigma, rho = _ar1_parameters(n_samples, standard_deviation, correlation)
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator.")
    values = rng.standard_normal(n_samples, dtype=np.float64)
    gain = math.sqrt((1 - rho) * (1 + rho))
    try:
        with np.errstate(over="raise", invalid="raise", under="ignore"):
            for index in range(1, n_samples):
                values[index] = rho * values[index - 1] + gain * values[index]
            values *= sigma
    except FloatingPointError as error:
        raise ValueError("AR(1) noise exceeds the finite float64 range.") from error
    if not np.all(np.isfinite(values)):
        raise ValueError("AR(1) noise exceeds the finite float64 range.")
    return values


def ar1_covariance(
    n_samples: int, *, standard_deviation: float, correlation: float
) -> NDArray[np.float64]:
    """Return the analytic stationary covariance sigma**2 * rho**abs(i-j).

    Zero sigma yields a zero matrix, unsuitable for positive-definite
    weighting. For positive sigma, its variance must be finite and positive
    in float64. No covariance estimation or regularization is performed.
    """
    sigma, rho = _ar1_parameters(n_samples, standard_deviation, correlation)
    variance = sigma * sigma
    if sigma > 0 and not 0 < variance < math.inf:
        raise ValueError("The positive variance is not representable in float64.")
    indices = np.arange(n_samples)
    return variance * np.power(rho, np.abs(indices[:, None] - indices[None, :]))
