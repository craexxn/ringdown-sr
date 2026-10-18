"""Read the explicit, versioned configuration of one white-noise pilot run."""

import math
import tomllib
from dataclasses import asdict, dataclass
from numbers import Real
from pathlib import Path


@dataclass(frozen=True)
class SamplingConfig:
    n_samples: int
    sample_rate_hz: float


@dataclass(frozen=True)
class SignalConfig:
    amplitude: float
    frequency_hz: float
    decay_time_s: float
    phase_rad: float


@dataclass(frozen=True)
class NoiseConfig:
    kind: str
    standard_deviation: float
    bit_generator: str
    seed: int


@dataclass(frozen=True)
class FitConfig:
    weighting: str
    frequency_bounds_hz: tuple[float, float]
    decay_time_bounds_s: tuple[float, float]
    initial_points: tuple[tuple[float, float], ...]
    max_nfev: int


@dataclass(frozen=True)
class PilotConfig:
    schema_version: int
    sampling: SamplingConfig
    signal: SignalConfig
    noise: NoiseConfig
    fit: FitConfig

    def to_dict(self) -> dict:
        """Return the fully explicit configuration, without local paths."""
        return asdict(self)


def _fields(table, required: set[str], name: str) -> dict:
    if not isinstance(table, dict) or set(table) != required:
        raise ValueError(f"{name} requires exactly these fields: {sorted(required)}.")
    return table


def _number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a finite real number.")
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} exceeds the float64 range.") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite real number.")
    return result


def _integer(value, name: str, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}.")
    return value


def _pair(value, name: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{name} must contain exactly two numbers.")
    return tuple(_number(item, name) for item in value)


def parse_config(content: bytes) -> PilotConfig:
    """Reject incomplete, unknown, nonfinite, or incompatible TOML inputs."""
    try:
        data = tomllib.loads(content.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"Invalid UTF-8 TOML configuration: {error}") from error
    _fields(data, {"schema_version", "sampling", "signal", "noise", "fit"}, "root")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("schema_version must be 1.")
    sampling = _fields(
        data["sampling"], set(SamplingConfig.__annotations__), "sampling"
    )
    signal = _fields(data["signal"], set(SignalConfig.__annotations__), "signal")
    noise = _fields(data["noise"], set(NoiseConfig.__annotations__), "noise")
    fit = _fields(data["fit"], set(FitConfig.__annotations__), "fit")
    n = _integer(sampling["n_samples"], "sampling.n_samples", 5)
    fs = _number(sampling["sample_rate_hz"], "sampling.sample_rate_hz")
    if fs <= 0 or not math.isfinite(n / fs):
        raise ValueError("Sampling rate must be positive and window duration finite.")
    s = SignalConfig(
        **{name: _number(value, f"signal.{name}") for name, value in signal.items()}
    )
    if not 0 <= s.frequency_hz < fs / 2 or s.decay_time_s <= 0:
        raise ValueError(
            "Signal requires 0 <= frequency < Nyquist and decay_time_s > 0."
        )
    sigma = _number(noise["standard_deviation"], "noise.standard_deviation")
    seed = _integer(noise["seed"], "noise.seed", 0)
    if noise["kind"] != "gaussian_white" or noise["bit_generator"] != "PCG64":
        raise ValueError("Only gaussian_white noise with PCG64 is supported.")
    if sigma < 0:
        raise ValueError("noise.standard_deviation must be nonnegative.")
    if fit["weighting"] not in ("ordinary", "known_white"):
        raise ValueError("fit.weighting must be ordinary or known_white.")
    if fit["weighting"] == "known_white" and not 0 < sigma * sigma < math.inf:
        raise ValueError("known_white requires a positive, finite float64 variance.")
    f_bounds = _pair(fit["frequency_bounds_hz"], "fit.frequency_bounds_hz")
    tau_bounds = _pair(fit["decay_time_bounds_s"], "fit.decay_time_bounds_s")
    if not 0 < f_bounds[0] < f_bounds[1] < fs / 2:
        raise ValueError(
            "Fit frequency bounds must lie strictly between zero and Nyquist."
        )
    if not 0 < tau_bounds[0] < tau_bounds[1]:
        raise ValueError("Fit decay-time bounds must be positive and increasing.")
    if not isinstance(fit["initial_points"], list) or not fit["initial_points"]:
        raise ValueError(
            "fit.initial_points must be a nonempty list of (f, tau) pairs."
        )
    starts = tuple(
        _pair(point, "fit.initial_points") for point in fit["initial_points"]
    )
    if any(
        not (f_bounds[0] < f < f_bounds[1] and tau_bounds[0] < tau < tau_bounds[1])
        for f, tau in starts
    ):
        raise ValueError("All initial_points must lie strictly inside the fit bounds.")
    budget = _integer(fit["max_nfev"], "fit.max_nfev", 1)
    return PilotConfig(
        1,
        SamplingConfig(n, fs),
        s,
        NoiseConfig("gaussian_white", sigma, "PCG64", seed),
        FitConfig(fit["weighting"], f_bounds, tau_bounds, starts, budget),
    )


def load_config(path: str | Path) -> PilotConfig:
    """Read a configuration without creating output or drawing random samples."""
    return parse_config(Path(path).read_bytes())
