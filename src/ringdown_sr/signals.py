"""Generate a uniformly sampled time axis and a single damped sinusoid."""

from numbers import Integral, Real

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _finite_scalar(value: float, name: str) -> float:
    """Validate a finite real scalar without silently accepting booleans."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a finite real scalar.")
    result = float(value)
    if not np.isfinite(result):
        raise ValueError(f"{name} must be a finite real scalar.")
    return result


def sample_times(n_samples: int, sample_rate_hz: float) -> NDArray[np.float64]:
    """Return t[k] = k / sample_rate_hz for k = 0, ..., n_samples - 1.

    The sampling interval is 1 / sample_rate_hz. The corresponding window
    duration is n_samples / sample_rate_hz; its right endpoint is excluded.
    No requested duration is rounded or converted to a sample count here.
    """
    if isinstance(n_samples, (bool, np.bool_)) or not isinstance(n_samples, Integral):
        raise TypeError("n_samples must be a positive integer.")
    if n_samples < 1:
        raise ValueError("n_samples must be a positive integer.")
    sample_rate_hz = _finite_scalar(sample_rate_hz, "sample_rate_hz")
    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive.")
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            return np.arange(n_samples, dtype=np.float64) / sample_rate_hz
    except FloatingPointError as error:
        raise ValueError("Sampling parameters produce non-finite times.") from error


def ringdown_signal(
    time_s: ArrayLike,
    *,
    amplitude: float,
    frequency_hz: float,
    decay_time_s: float,
    phase_rad: float = 0.0,
) -> NDArray[np.float64]:
    """Evaluate A * exp(-t / tau) * cos(2 * pi * f * t + phi).

    Times must form a nonempty, one-dimensional array of finite,
    nonnegative real values measured from the start of the signal.
    Amplitude is a signed dimensionless factor, frequency is in hertz,
    decay time is in seconds, and phase is in radians. Frequency may be
    zero; decay time must be positive. This function adds no noise and
    imposes no sampling or astrophysical parameter constraints.
    """
    times = np.asarray(time_s)
    if times.ndim != 1 or times.size == 0:
        raise ValueError("time_s must be a nonempty one-dimensional array.")
    if not np.issubdtype(times.dtype, np.number) or np.iscomplexobj(times):
        raise ValueError("time_s must contain real numbers.")
    times = times.astype(np.float64, copy=False)
    if not np.all(np.isfinite(times)) or np.any(times < 0):
        raise ValueError("time_s must contain finite nonnegative values.")

    amplitude = _finite_scalar(amplitude, "amplitude")
    frequency_hz = _finite_scalar(frequency_hz, "frequency_hz")
    decay_time_s = _finite_scalar(decay_time_s, "decay_time_s")
    phase_rad = _finite_scalar(phase_rad, "phase_rad")
    if frequency_hz < 0:
        raise ValueError("frequency_hz must be nonnegative.")
    if decay_time_s <= 0:
        raise ValueError("decay_time_s must be positive.")

    try:
        with np.errstate(over="raise", invalid="raise", under="ignore", divide="raise"):
            return (
                amplitude
                * np.exp(-times / decay_time_s)
                * np.cos(2 * np.pi * frequency_hz * times + phase_rad)
            )
    except FloatingPointError as error:
        raise ValueError("Signal parameters exceed the numerical range.") from error
