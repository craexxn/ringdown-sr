"""Generate Gaussian white noise with an explicit random-number generator."""

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
