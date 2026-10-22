"""Compare three fixed-covariance fits with strictly separate background roles."""

import math
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from scipy.linalg import cholesky, norm, solve_triangular

from ringdown_sr.background import (
    background_random_record,
    draw_noise_window,
    generate_background,
    noise_draw_record,
    pilot_generators,
)
from ringdown_sr.config import CovariancePilotConfig
from ringdown_sr.covariance_estimation import (
    CovarianceEstimationError,
    estimate_covariance,
)
from ringdown_sr.losses import CovarianceLoss, mean_squared_error
from ringdown_sr.noise import ar1_covariance
from ringdown_sr.pilot import (
    PilotRun,
    _environment,
    _json_bytes,
    _provenance,
    _save_samples,
    _sha256,
    _utc_now,
    _write_json,
)
from ringdown_sr.reference_fit import ReferenceFitError, fit_ringdown
from ringdown_sr.signals import ringdown_signal, sample_times

FIT_LABELS = {
    "ordinary": "Gewöhnlicher Fit",
    "known_covariance": "Fit mit wahrer Kovarianz",
    "estimated_covariance": "Fit mit geschätzter Kovarianz",
}
NUMERICAL_ERRORS = (
    ValueError,
    FloatingPointError,
    OverflowError,
    np.linalg.LinAlgError,
)


def _background_score(covariance, windows, diagnostic: dict) -> None:
    """Score frozen check data, retaining finite partial diagnostics on failure."""
    diagnostic.update(
        n_windows=len(windows), log_determinant=None, quadratic_mean=None, score=None
    )
    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        factor = cholesky(covariance, lower=True, check_finite=False)
        logdet = 2 * float(np.log(factor.diagonal()).sum())
        if not math.isfinite(logdet):
            raise ValueError(
                "Check-window log determinant exceeds the finite float64 range."
            )
        diagnostic["log_determinant"] = logdet
        transformed = solve_triangular(
            factor, windows.T, lower=True, check_finite=False
        )
        if not np.all(np.isfinite(transformed)):
            raise ValueError("Check-window whitening exceeds the finite float64 range.")
        scaled_norm = float(
            norm((transformed / math.sqrt(len(windows))).ravel(), check_finite=False)
        )
        quadratic = scaled_norm * scaled_norm
        if not math.isfinite(quadratic):
            raise ValueError("Check-window quadratic exceeds the finite float64 range.")
        diagnostic["quadratic_mean"] = quadratic
        score = logdet + quadratic
    if not math.isfinite(score):
        raise ValueError("Check-window score exceeds the finite float64 range.")
    diagnostic["score"] = score


def _relative_matrix_error(estimated, truth) -> float:
    """Return relative Frobenius error after common scaling, for diagnosis only."""
    scale = max(float(np.max(np.abs(estimated))), float(np.max(np.abs(truth))))
    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        reference = truth / scale
        denominator = float(norm(reference.ravel()))
        if denominator == 0 or not math.isfinite(denominator):
            raise ValueError("Reference covariance norm is not representable.")
        value = float(norm((estimated / scale - reference).ravel())) / denominator
    if not math.isfinite(value):
        raise ValueError("Relative covariance error exceeds the finite float64 range.")
    return value


def _fit_details(fit, weighting, covariance_file) -> dict:
    return {
        "method": "separable_known_ringdown",
        "weighting": weighting,
        "covariance_file": covariance_file,
        "parameters": {
            name: getattr(fit, name)
            for name in ("amplitude", "frequency_hz", "decay_time_s", "phase_rad")
        },
        "selected_start_index": fit.selected_start_index,
        "active_mask": fit.active_mask,
        "nonlinear_jacobian_rank": fit.nonlinear_jacobian_rank,
        "attempts": [asdict(attempt) for attempt in fit.attempts],
    }


def _save_comparison_plot(path: Path, arrays: dict) -> None:
    figure = Figure(figsize=(11, 7), layout="constrained")
    FigureCanvasAgg(figure)
    top, bottom = figure.subplots(2, 1, sharex=True)
    time_ms = arrays["time_s"] * 1000
    top.scatter(
        time_ms, arrays["observed"], s=12, color="gray", alpha=0.55, label="Messdaten"
    )
    top.plot(
        time_ms, arrays["signal"], color="black", linewidth=2, label="Bekanntes Signal"
    )
    for name, label in FIT_LABELS.items():
        (line,) = top.plot(time_ms, arrays["prediction_" + name], "--", label=label)
        bottom.plot(
            time_ms, arrays["residual_" + name], color=line.get_color(), label=label
        )
    top.set(
        title="Drei Kontrollfits – bekannter Formansatz",
        ylabel="Amplitude (dimensionslos)",
    )
    bottom.axhline(0, color="gray", linewidth=0.7)
    bottom.set(xlabel="Zeit (ms)", ylabel="Messdaten − Fit")
    for axis in (top, bottom):
        axis.legend(fontsize=8)
        axis.grid(alpha=0.2)
    figure.savefig(path, dpi=150)


def _save_covariance_plot(path: Path, matrices: dict, alpha: float) -> None:
    figure = Figure(figsize=(12, 4), layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots(1, 3)
    limit = max(float(np.max(np.abs(matrix))) for matrix in matrices.values())
    titles = [
        "Wahre Kovarianz",
        "Rohe Schätzung",
        f"Regularisierte Schätzung (α={alpha:g})",
    ]
    for axis, matrix, title in zip(axes, matrices.values(), titles, strict=True):
        view = axis.imshow(
            matrix, cmap="coolwarm", vmin=-limit, vmax=limit, origin="lower"
        )
        axis.set(title=title, xlabel="Sampleindex", ylabel="Sampleindex")
    figure.colorbar(view, ax=list(axes), label="Kovarianz (Amplitude²)", shrink=0.8)
    figure.savefig(path, dpi=150)


def run_covariance_pilot(
    config: CovariancePilotConfig,
    original: bytes,
    source_filename: str,
    output_directory: str | Path,
    *,
    _capture_inputs: bool = False,
) -> PilotRun:
    """Persist a schema-2 control without refits, fallbacks or output overwrites."""
    # Reject overlapping streams before reserving output or generating any data.
    generators = pilot_generators(config.noise.seed, config.background.seed)
    resolved = config.to_dict()
    provenance, environment = _provenance(), _environment()
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    signal_random = noise_draw_record(config.noise, config.sampling.n_samples, 1)
    signal_random.update(seed=config.noise.seed, derivation="direct_seed_v1")
    manifest = {
        "schema_version": 2,
        "status": "running",
        "started_at_utc": _utc_now(),
        "finished_at_utc": None,
        "elapsed_seconds": None,
        "configuration": {
            "source_filename": source_filename,
            "original_sha256": _sha256(original),
            "resolved_sha256": _sha256(_json_bytes(resolved)),
        },
        "provenance": provenance,
        "environment": environment,
        "random": {
            "signal": signal_random,
            "background": background_random_record(
                config.noise, config.sampling, config.background
            ),
        },
        "artifact_sha256": {},
    }
    _write_json(output / "metadata.json", manifest)
    (output / "config.toml").write_bytes(original)
    _write_json(output / "resolved_config.json", resolved)
    arrays, background, matrices = {}, {}, {}
    result = {
        "schema_version": 2,
        "status": None,
        "stage": "generation",
        "truth": asdict(config.signal),
        "covariance_estimation": None,
        "fits": {
            name: {"status": "not_run", "fit": None, "metrics": None, "error": None}
            for name in FIT_LABELS
        },
        "diagnostics": {
            "evaluation_scope": "post_selection_only",
            "relative_frobenius_error": None,
            "background_check": {},
        },
        "error": None,
    }
    status = "generation_failed"
    try:
        time_s = sample_times(**asdict(config.sampling))
        signal = ringdown_signal(time_s, **asdict(config.signal))
        arrays.update(time_s=time_s, signal=signal)
        rng = generators["signal"]
        signal_random["state_before"] = rng.bit_generator.state
        try:
            noise = draw_noise_window(config.noise, len(time_s), rng)
            signal_random["calls"]["completed_calls"] = 1
        finally:
            signal_random["state_after"] = rng.bit_generator.state
        with np.errstate(over="raise", invalid="raise"):
            observed = signal + noise
        arrays.update(noise=noise, observed=observed)
        time_s.setflags(write=False)
        observed.setflags(write=False)
        result["sampling"] = {
            **asdict(config.sampling),
            "window_duration_s": len(time_s) / config.sampling.sample_rate_hz,
            "last_sample_time_s": float(time_s[-1]),
        }
        matrices["true"] = (
            ar1_covariance(
                len(time_s),
                standard_deviation=config.noise.standard_deviation,
                correlation=config.noise.correlation,
            )
            if config.noise.kind == "gaussian_ar1"
            else config.noise.standard_deviation**2 * np.eye(len(time_s))
        )
        result["noise_model"] = {
            "kind": config.noise.kind,
            "covariance_source": "analytic_stationary_ar1"
            if config.noise.kind == "gaussian_ar1"
            else "analytic_white",
            "covariance_file": "covariance_true.csv",
        }
        generate_background(
            config.noise,
            config.sampling,
            config.background,
            windows=background,
            random=manifest["random"]["background"],
            generators=generators,
        )
        status, result["stage"] = "estimation_failed", "covariance_estimation"
        estimate = estimate_covariance(
            background["train"],
            background["validation"],
            **asdict(config.covariance_estimation),
        )
        matrices.update(raw=estimate.raw_covariance, estimated=estimate.covariance)
        if _capture_inputs:
            # Exact binary handoff to schema 3; the ordinary schema-2 export is unchanged.
            np.savez(
                output / "comparison_inputs.npz",
                time_s=time_s,
                signal=signal,
                noise=noise,
                observed=observed,
                covariance_true=matrices["true"],
                covariance_estimated=matrices["estimated"],
            )
        result["covariance_estimation"] = {
            "method": estimate.method,
            "mean_mode": estimate.mean_mode,
            "n_train": estimate.n_train,
            "n_validation": estimate.n_validation,
            "kappa_max": estimate.kappa_max,
            "mu": estimate.mu,
            "alpha_selected": estimate.alpha_selected,
            "candidates": [asdict(candidate) for candidate in estimate.candidates],
            "raw_covariance_file": "covariance_raw.csv",
            "covariance_file": "covariance_estimated.csv",
            "refit": False,
        }
        status, result["stage"] = "fit_failed", "fit"
        for name in FIT_LABELS:
            record = result["fits"][name]
            covariance = (
                None
                if name == "ordinary"
                else matrices["true" if name == "known_covariance" else "estimated"]
            )
            try:
                fit = fit_ringdown(
                    time_s,
                    observed,
                    frequency_bounds_hz=config.fit.frequency_bounds_hz,
                    decay_time_bounds_s=config.fit.decay_time_bounds_s,
                    initial_points=config.fit.initial_points,
                    max_nfev=config.fit.max_nfev,
                    covariance=covariance,
                )
            except (ReferenceFitError, *NUMERICAL_ERRORS) as error:
                record.update(
                    status="fit_failed",
                    error={"type": type(error).__name__, "message": str(error)},
                )
                if isinstance(error, ReferenceFitError):
                    record["error"]["attempts"] = [
                        asdict(attempt) for attempt in error.attempts
                    ]
                continue
            record["fit"] = _fit_details(
                fit,
                name,
                None
                if name == "ordinary"
                else f"covariance_{'true' if name == 'known_covariance' else 'estimated'}.csv",
            )
            arrays.update(
                {"prediction_" + name: fit.prediction, "residual_" + name: fit.residual}
            )
            record["metrics"] = {
                "ordinary_mse": fit.ordinary_mse,
                "mse_to_clean_signal": None,
                "q_used_per_sample": fit.covariance_mean_squared,
                "q_true_per_sample": None,
                "evaluation_scope": "fitted_samples_only",
                "residual_definition": "observed_minus_prediction",
            }
            try:
                record["metrics"]["mse_to_clean_signal"] = mean_squared_error(
                    fit.prediction - signal
                )
                record["metrics"]["q_true_per_sample"] = CovarianceLoss(
                    matrices["true"]
                ).mean_squared(fit.residual)
                record["status"] = "success"
            except NUMERICAL_ERRORS as error:
                record.update(
                    status="evaluation_failed",
                    error={"type": type(error).__name__, "message": str(error)},
                )
        failed = [
            name
            for name, record in result["fits"].items()
            if record["status"] != "success"
        ]
        if failed:
            status = (
                "fit_failed"
                if any(
                    record["status"] == "fit_failed"
                    for record in result["fits"].values()
                )
                else "evaluation_failed"
            )
            result["error"] = {
                "type": "ComparisonIncomplete",
                "message": "Failed variants: " + ", ".join(failed),
            }
            result["stage"] = "fit" if status == "fit_failed" else "evaluation"
        else:
            status, result["stage"] = "evaluation_failed", "diagnostics"
            result["diagnostics"]["relative_frobenius_error"] = _relative_matrix_error(
                matrices["estimated"], matrices["true"]
            )
            for name in ("true", "estimated"):
                diagnostic = {}
                result["diagnostics"]["background_check"][name] = diagnostic
                _background_score(matrices[name], background["check"], diagnostic)
            status, result["stage"] = "success", "complete"
    except CovarianceEstimationError as error:
        if error.raw_covariance is not None:
            matrices["raw"] = error.raw_covariance
        result["covariance_estimation"] = {
            "mu": error.mu,
            "alpha_selected": None,
            "candidates": [asdict(candidate) for candidate in error.candidates],
        }
        result["error"] = {"type": type(error).__name__, "message": str(error)}
    except NUMERICAL_ERRORS as error:
        result["error"] = {"type": type(error).__name__, "message": str(error)}
    result["status"] = status
    _write_json(output / "result.json", result)
    if arrays:
        _save_samples(output / "samples.csv", arrays)
    for name, matrix in background.items():
        np.savetxt(
            output / f"background_{name}.csv",
            matrix,
            delimiter=",",
            fmt="%.17g",
            encoding="utf-8",
        )
    for name, matrix in matrices.items():
        np.savetxt(
            output / f"covariance_{name}.csv",
            matrix,
            delimiter=",",
            fmt="%.17g",
            encoding="utf-8",
        )
    if status == "success":
        _save_comparison_plot(output / "plot.png", arrays)
        _save_covariance_plot(
            output / "covariance_plot.png", matrices, estimate.alpha_selected
        )
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
