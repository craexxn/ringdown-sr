"""Run and persist one configured white-noise reference-fit control case."""

import hashlib
import json
import os
import platform
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib import import_module, metadata
from pathlib import Path

import numpy as np
import scipy
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ringdown_sr.config import parse_config
from ringdown_sr.losses import mean_squared_error
from ringdown_sr.noise import gaussian_white_noise
from ringdown_sr.reference_fit import ReferenceFitError, fit_ringdown
from ringdown_sr.signals import ringdown_signal, sample_times


@dataclass(frozen=True)
class PilotRun:
    """Report the reserved output directory and scientific computation status."""

    output_directory: Path
    status: str


def _json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(
        "utf-8"
    )


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _write_json(path: Path, value) -> None:
    # Only used inside a directory exclusively reserved by this invocation.
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(_json_bytes(value))
    temporary.replace(path)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _provenance() -> dict:
    """Identify the imported Python sources, without relying on the caller's cwd."""
    package = Path(__file__).resolve().parent
    candidate = package.parent.parent
    git = {"available": False, "commit": None, "dirty": None, "changes": []}
    try:

        def query(*args):
            return subprocess.check_output(
                ["git", "-C", str(candidate), *args],
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=5,
            ).rstrip("\n")

        if Path(query("rev-parse", "--show-toplevel")).resolve() == candidate:
            changes = query(
                "status", "--porcelain=v1", "--untracked-files=all"
            ).splitlines()
            git = {
                "available": True,
                "commit": query("rev-parse", "HEAD"),
                "dirty": bool(changes),
                "changes": changes,
            }
    except (OSError, subprocess.SubprocessError):
        pass
    files = {
        "ringdown_sr/" + path.relative_to(package).as_posix(): _sha256(
            path.read_bytes()
        )
        for path in sorted(package.rglob("*.py"))
    }
    project_files = {}
    if (candidate / "src" / "ringdown_sr").resolve() == package:
        for name in (
            "pyproject.toml",
            "uv.lock",
            ".python-version",
            "src/ringdown_sr/juliapkg.json",
            "julia/Project.toml",
            "julia/Manifest.toml",
        ):
            path = candidate / name
            project_files[name] = _sha256(path.read_bytes()) if path.is_file() else None
    return {
        "git": git,
        "python_source_sha256": files,
        "python_source_set_sha256": _sha256(_json_bytes(files)),
        "project_file_sha256": project_files,
    }


def _diagnostic(collect, expected_type: type) -> dict:
    """Keep optional numerical-library diagnostics from blocking a pilot run."""
    try:
        details = collect()
        if not isinstance(details, expected_type):
            raise TypeError("Diagnostic provider returned an unexpected data type.")
        _json_bytes(details)
    except (
        AttributeError,
        ImportError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as error:
        return {
            "status": "unavailable",
            "details": None,
            "error": f"{type(error).__name__}: {error}",
        }
    return {"status": "available", "details": details, "error": None}


def _environment() -> dict:
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": dict(
            sorted(
                (item.metadata["Name"], item.version)
                for item in metadata.distributions()
                if item.metadata["Name"]
            )
        ),
        "thread_environment": {
            key: os.environ.get(key)
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
        "numerical_libraries": {
            "snapshot": "before_generation",
            "numpy_build": _diagnostic(lambda: np.show_config(mode="dicts"), dict),
            "scipy_build": _diagnostic(lambda: scipy.show_config(mode="dicts"), dict),
            # Already present in the locked PySR dependency tree; optional here.
            # Read loaded native-library information without changing thread limits.
            "threadpools": _diagnostic(
                lambda: import_module("threadpoolctl").threadpool_info(), list
            ),
        },
        "array_dtype": "float64",
        "julia_used": False,
    }


def _save_samples(path: Path, arrays: dict) -> None:
    np.savetxt(
        path,
        np.column_stack(list(arrays.values())),
        delimiter=",",
        header=",".join(arrays),
        comments="",
        fmt="%.17g",
        encoding="utf-8",
    )


def _save_plot(path: Path, arrays: dict) -> None:
    figure = Figure(figsize=(10, 6), layout="constrained")
    FigureCanvasAgg(figure)
    top, bottom = figure.subplots(2, 1, sharex=True)
    milliseconds = arrays["time_s"] * 1000
    top.scatter(
        milliseconds,
        arrays["observed"],
        color="gray",
        s=14,
        alpha=0.6,
        label="Verrauschte Messdaten",
    )
    top.plot(milliseconds, arrays["signal"], label="Bekanntes Signal", linewidth=2)
    top.plot(
        milliseconds, arrays["prediction"], "--", label="Klassischer Fit", linewidth=2
    )
    top.set(
        title="Konfigurierter Pilot – bekannter Formansatz",
        ylabel="Amplitude (dimensionslos)",
    )
    bottom.plot(
        milliseconds, arrays["residual"], color="darkorange", label="Messdaten − Fit"
    )
    bottom.axhline(0, color="gray", linewidth=0.7)
    bottom.set(xlabel="Zeit (ms)", ylabel="Residuum")
    for axis in (top, bottom):
        axis.legend()
        axis.grid(alpha=0.2)
    figure.savefig(path, dpi=150)


def run_pilot(config_path: str | Path, output_directory: str | Path) -> PilotRun:
    """Reserve a new directory and persist inputs, outcome, and provenance.

    Invalid configurations and existing destinations are rejected before
    creating run files. Expected numerical failures are persisted and return
    a failure status. An interrupted or unhandled export failure leaves a
    manifest marked running, never a completed success. No existing run is
    overwritten, resumed, or deleted. Paths are relative to the caller's cwd.
    """
    config_path = Path(config_path)
    original = config_path.read_bytes()
    config = parse_config(original)
    resolved = config.to_dict()
    # Capture before creating output; results/ is excluded from Git.
    provenance = _provenance()
    environment = _environment()
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    manifest = {
        "schema_version": 1,
        "status": "running",
        "started_at_utc": _utc_now(),
        "finished_at_utc": None,
        "elapsed_seconds": None,
        "configuration": {
            "source_filename": config_path.name,
            "original_sha256": _sha256(original),
            "resolved_sha256": _sha256(_json_bytes(resolved)),
        },
        "provenance": provenance,
        "environment": environment,
        "random": {
            "bit_generator": "PCG64",
            "seed": config.noise.seed,
            "calls": [],
            "state_before": None,
            "state_after": None,
        },
        "artifact_sha256": {},
    }
    _write_json(output / "metadata.json", manifest)
    (output / "config.toml").write_bytes(original)
    _write_json(output / "resolved_config.json", resolved)
    arrays = {}
    result = {
        "schema_version": 1,
        "status": None,
        "stage": "generation",
        "truth": asdict(config.signal),
        "fit": None,
        "metrics": None,
        "error": None,
    }
    status = "generation_failed"
    try:
        time_s = sample_times(**asdict(config.sampling))
        signal = ringdown_signal(time_s, **asdict(config.signal))
        rng = np.random.Generator(np.random.PCG64(config.noise.seed))
        manifest["random"]["state_before"] = rng.bit_generator.state
        call = {
            "method": "normal",
            "loc": 0.0,
            "scale": config.noise.standard_deviation,
            "size": len(signal),
            "completed": False,
        }
        manifest["random"]["calls"].append(call)
        noise = gaussian_white_noise(
            len(signal), standard_deviation=config.noise.standard_deviation, rng=rng
        )
        manifest["random"]["state_after"] = rng.bit_generator.state
        call["completed"] = True
        with np.errstate(over="raise", invalid="raise"):
            observed = signal + noise
        arrays.update(time_s=time_s, signal=signal, noise=noise, observed=observed)
        result["sampling"] = {
            **asdict(config.sampling),
            "window_duration_s": len(time_s) / config.sampling.sample_rate_hz,
            "last_sample_time_s": float(time_s[-1]),
        }
        result["stage"] = "fit"
        status = "fit_failed"
        covariance = None
        if config.fit.weighting == "known_white":
            covariance = config.noise.standard_deviation**2 * np.eye(len(time_s))
        fit = fit_ringdown(
            time_s,
            observed,
            frequency_bounds_hz=config.fit.frequency_bounds_hz,
            decay_time_bounds_s=config.fit.decay_time_bounds_s,
            initial_points=config.fit.initial_points,
            max_nfev=config.fit.max_nfev,
            covariance=covariance,
        )
        arrays.update(prediction=fit.prediction, residual=fit.residual)
        result["fit"] = {
            "method": "separable_known_ringdown",
            "weighting": config.fit.weighting,
            "parameters": {
                name: getattr(fit, name)
                for name in ("amplitude", "frequency_hz", "decay_time_s", "phase_rad")
            },
            "selected_start_index": fit.selected_start_index,
            "active_mask": fit.active_mask,
            "nonlinear_jacobian_rank": fit.nonlinear_jacobian_rank,
            "attempts": [asdict(attempt) for attempt in fit.attempts],
        }
        status = "evaluation_failed"
        result["stage"] = "evaluation"
        result["metrics"] = {
            "ordinary_mse": fit.ordinary_mse,
            "covariance_mean_squared": fit.covariance_mean_squared,
            "mse_to_clean_signal": mean_squared_error(fit.prediction - signal),
            "evaluation_scope": "fitted_samples_only",
            "residual_definition": "observed_minus_prediction",
        }
        status = "success"
        result["stage"] = "complete"
    except ReferenceFitError as error:
        result["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "attempts": [asdict(attempt) for attempt in error.attempts],
        }
    except (
        ValueError,
        FloatingPointError,
        OverflowError,
        np.linalg.LinAlgError,
    ) as error:
        result["error"] = {"type": type(error).__name__, "message": str(error)}
    result["status"] = status
    _write_json(output / "result.json", result)
    if arrays:
        _save_samples(output / "samples.csv", arrays)
    if status == "success":
        _save_plot(output / "plot.png", arrays)
    manifest["artifact_sha256"] = {
        path.name: _sha256(path.read_bytes())
        for path in sorted(output.iterdir())
        if path.is_file() and path.name != "metadata.json"
    }
    manifest.update(
        status=status,
        finished_at_utc=_utc_now(),
        elapsed_seconds=time.perf_counter() - started,
    )
    _write_json(output / "metadata.json", manifest)
    return PilotRun(output, status)
