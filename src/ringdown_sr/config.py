"""Read an explicit, versioned white-noise or AR(1) pilot configuration."""

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
class AR1NoiseConfig(NoiseConfig):
    correlation: float


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


@dataclass(frozen=True)
class BackgroundConfig:
    n_train: int
    n_validation: int
    n_check: int
    bit_generator: str
    seed: int
    stream_scheme: str


@dataclass(frozen=True)
class CovarianceConfig:
    mean_mode: str
    alpha_candidates: tuple[float, ...]
    kappa_max: float


@dataclass(frozen=True)
class CovariancePilotConfig(PilotConfig):
    background: BackgroundConfig
    covariance_estimation: CovarianceConfig


@dataclass(frozen=True)
class SearchBudget:
    """Technical search budgets; these are not research performance settings."""

    seed: int = 20261020
    niterations: int = 10
    populations: int = 2
    population_size: int = 32
    ncycles_per_iteration: int = 50

    def __post_init__(self):
        for name, value in asdict(self).items():
            minimum = 0 if name == "seed" else 16 if name == "population_size" else 1
            if type(value) is not int or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}.")
        if self.seed >= 2**32:
            raise ValueError("seed must be smaller than 2**32 for PySR's RandomState.")


@dataclass(frozen=True)
class SymbolicPilotConfig(CovariancePilotConfig):
    symbolic_search: SearchBudget

    def reference_config(self) -> CovariancePilotConfig:
        """Keep every data, covariance and classical-fit setting unchanged."""
        return CovariancePilotConfig(
            2,
            self.sampling,
            self.signal,
            self.noise,
            self.fit,
            self.background,
            self.covariance_estimation,
        )


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
    version = data.get("schema_version")
    if type(version) is not int or version not in (1, 2, 3):
        raise ValueError("schema_version must be 1, 2 or 3.")
    root_fields = {"schema_version", "sampling", "signal", "noise", "fit"}
    if version >= 2:
        root_fields |= {"background", "covariance_estimation"}
    if version == 3:
        root_fields.add("symbolic_search")
    _fields(data, root_fields, "root")
    sampling = _fields(
        data["sampling"], set(SamplingConfig.__annotations__), "sampling"
    )
    signal = _fields(data["signal"], set(SignalConfig.__annotations__), "signal")
    noise_fields = set(NoiseConfig.__annotations__)
    if isinstance(data["noise"], dict) and data["noise"].get("kind") == "gaussian_ar1":
        noise_fields.add("correlation")
    noise = _fields(data["noise"], noise_fields, "noise")
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
    if (
        noise["kind"] not in ("gaussian_white", "gaussian_ar1")
        or noise["bit_generator"] != "PCG64"
    ):
        raise ValueError(
            "Only gaussian_white or gaussian_ar1 noise with PCG64 is supported."
        )
    if sigma < 0:
        raise ValueError("noise.standard_deviation must be nonnegative.")
    noise_config = NoiseConfig(noise["kind"], sigma, "PCG64", seed)
    if noise["kind"] == "gaussian_ar1":
        rho = _number(noise["correlation"], "noise.correlation")
        if not -1 < rho < 1:
            raise ValueError("noise.correlation must lie strictly between -1 and 1.")
        if sigma > 0 and not 0 < sigma * sigma < math.inf:
            raise ValueError(
                "AR(1) covariance requires a representable positive variance."
            )
        noise_config = AR1NoiseConfig(noise["kind"], sigma, "PCG64", seed, rho)
    weightings = (
        ("compare_covariances",)
        if version >= 2
        else ("ordinary", "known_white", "known_covariance")
    )
    if fit["weighting"] not in weightings:
        raise ValueError(
            f"fit.weighting for schema {version} must be one of {weightings}."
        )
    if fit["weighting"] == "known_white" and noise["kind"] != "gaussian_white":
        raise ValueError("known_white requires gaussian_white noise.")
    if fit["weighting"] != "ordinary" and not 0 < sigma * sigma < math.inf:
        raise ValueError(
            "Known covariance weighting requires a positive finite variance."
        )
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
    common = (
        version,
        SamplingConfig(n, fs),
        s,
        noise_config,
        FitConfig(fit["weighting"], f_bounds, tau_bounds, starts, budget),
    )
    if version == 1:
        return PilotConfig(*common)
    background = _fields(
        data["background"], set(BackgroundConfig.__annotations__), "background"
    )
    amounts = {
        name: _integer(background[name], f"background.{name}", 1)
        for name in ("n_train", "n_validation", "n_check")
    }
    background_seed = _integer(background["seed"], "background.seed", 0)
    if (
        background["bit_generator"] != "PCG64"
        or background["stream_scheme"] != "seedsequence_role_v1"
    ):
        raise ValueError("Background requires PCG64 and seedsequence_role_v1.")
    covariance = _fields(
        data["covariance_estimation"],
        set(CovarianceConfig.__annotations__),
        "covariance_estimation",
    )
    if covariance["mean_mode"] != "known_zero":
        raise ValueError('covariance_estimation.mean_mode must be "known_zero".')
    grid = covariance["alpha_candidates"]
    if not isinstance(grid, list) or not grid:
        raise ValueError("alpha_candidates must be a nonempty list.")
    alphas = tuple(_number(value, "alpha_candidates") for value in grid)
    if any(not 0 <= alpha <= 1 for alpha in alphas) or len(set(alphas)) != len(alphas):
        raise ValueError("alpha_candidates must be unique and lie in [0, 1].")
    kappa = _number(covariance["kappa_max"], "covariance_estimation.kappa_max")
    if kappa <= 1:
        raise ValueError("covariance_estimation.kappa_max must exceed one.")
    extra = (
        BackgroundConfig(
            **amounts,
            bit_generator="PCG64",
            seed=background_seed,
            stream_scheme="seedsequence_role_v1",
        ),
        CovarianceConfig("known_zero", alphas, kappa),
    )
    if version == 3:
        search = _fields(
            data["symbolic_search"],
            set(SearchBudget.__annotations__),
            "symbolic_search",
        )
        return SymbolicPilotConfig(*common, *extra, SearchBudget(**search))
    return CovariancePilotConfig(
        *common,
        *extra,
    )


def load_config(path: str | Path) -> PilotConfig:
    """Read a configuration without creating output or drawing random samples."""
    return parse_config(Path(path).read_bytes())
