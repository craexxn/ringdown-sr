"""Combine one schema-2 data preparation with three isolated symbolic searches."""

import json
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ringdown_sr.background import pilot_generators
from ringdown_sr.config import CovariancePilotConfig, SymbolicPilotConfig
from ringdown_sr.covariance_pilot import run_covariance_pilot
from ringdown_sr.losses import CovarianceLoss, mean_squared_error
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
from ringdown_sr.symbolic import (
    FORMAT,
    _check_prediction_replay,
    evaluate_tree,
    run_search_arm,
    select_candidate,
)

ARM_LABELS = {
    "ordinary": "Freie SR: gewöhnliche MSE",
    "known_covariance": "Freie SR: wahre Kovarianz",
    "estimated_covariance": "Freie SR: geschätzte Kovarianz",
}
ARM_ERRORS = (
    OSError,
    ValueError,
    TypeError,
    KeyError,
    IndexError,
    RuntimeError,
    AssertionError,
    OverflowError,
)


def _reference_toml(config: CovariancePilotConfig) -> bytes:
    """Serialize the fixed two-level schema without a new TOML dependency."""

    def value(item):
        if isinstance(item, (tuple, list)):
            return "[" + ", ".join(value(child) for child in item) + "]"
        return json.dumps(item, allow_nan=False)

    lines = ["schema_version = 2"]
    for table, fields in config.to_dict().items():
        if table != "schema_version":
            lines.extend(["", f"[{table}]"])
            lines.extend(f"{name} = {value(item)}" for name, item in fields.items())
    return ("\n".join(lines) + "\n").encode("utf-8")


def _verify_arm(directory: Path, time_s, observed, covariance, budget) -> dict:
    """Check the exact worker contract and every exported candidate before diagnosis."""
    request = json.loads((directory / "request.json").read_text())
    if request != {"format": FORMAT, "budget": asdict(budget)}:
        raise ValueError("The worker request does not match the shared search budget.")
    with np.load(directory / "inputs.npz", allow_pickle=False) as inputs:
        expected = {"time_s", "observed"} | (
            {"covariance"} if covariance is not None else set()
        )
        if set(inputs.files) != expected:
            raise ValueError("Unexpected worker inputs.")
        for name, array in (("time_s", time_s), ("observed", observed)):
            if not np.array_equal(inputs[name], array):
                raise ValueError(f"The worker changed {name} or sample order.")
        if covariance is not None and not np.array_equal(
            inputs["covariance"], covariance
        ):
            raise ValueError("The worker received a different covariance.")
    checksums = json.loads((directory / "checksums.json").read_text())
    required = {
        "inputs.npz",
        "request.json",
        "result.json",
        "metadata.json",
        "metadata_initial.json",
    }
    if not required <= checksums.keys():
        raise ValueError("Missing required worker checksums.")
    for name, digest in checksums.items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory.resolve()) or not path.is_file():
            raise ValueError("Invalid worker artifact path.")
        if _sha256(path.read_bytes()) != digest:
            raise ValueError(f"Worker checksum mismatch: {name}")
    result = json.loads((directory / "result.json").read_text())
    if (
        result["format"] != FORMAT
        or result["evaluation_scope"] != "fitted_samples_only"
    ):
        raise ValueError("Unexpected worker result format.")
    selected = select_candidate(result["candidates"])
    if (
        type(result["selected_index"]) is not int
        or result["selected_index"] != selected
    ):
        raise ValueError("The selected candidate is not the minimum training loss.")
    objective = None if covariance is None else CovarianceLoss(covariance)
    for candidate in result["candidates"]:
        prediction = np.asarray(candidate["prediction"], dtype=np.float64)
        if prediction.shape != observed.shape:
            raise ValueError("The candidate does not cover the full window.")
        _check_prediction_replay(evaluate_tree(candidate["tree"], time_s), prediction)
        residual = observed - prediction
        if not np.array_equal(candidate["residual"], residual):
            raise ValueError(
                "The exported residual must equal observed minus prediction."
            )
        loss = (
            mean_squared_error(residual)
            if objective is None
            else objective.mean_squared(residual)
        )
        np.testing.assert_allclose(candidate["loss"], loss, rtol=1e-10, atol=0)
    return result


def _diagnose(selected: dict, observed, signal, truth, covariance) -> dict:
    """Evaluate only the already frozen display selection; truth cannot select it."""
    prediction = np.asarray(selected["prediction"], dtype=np.float64)
    residual = observed - prediction
    return {
        "ordinary_mse": mean_squared_error(residual),
        "mse_to_clean_signal": mean_squared_error(prediction - signal),
        "q_used_per_sample": None
        if covariance is None
        else CovarianceLoss(covariance).mean_squared(residual),
        "q_true_per_sample": CovarianceLoss(truth).mean_squared(residual),
        "training_loss": selected["loss"],
        "evaluation_scope": "fitted_samples_only",
        "diagnostic_role": "post_selection_only",
        "residual_definition": "observed_minus_prediction",
    }


def _save_symbolic_plot(path: Path, arrays: dict) -> None:
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
    for name, label in ARM_LABELS.items():
        if "prediction_" + name in arrays:
            (line,) = top.plot(time_ms, arrays["prediction_" + name], "--", label=label)
            bottom.plot(
                time_ms, arrays["residual_" + name], color=line.get_color(), label=label
            )
    top.set(
        title="Freie SR – technische Beispielkurven auf den angepassten Samples",
        ylabel="Amplitude (dimensionslos)",
    )
    bottom.axhline(0, color="gray", linewidth=0.7)
    bottom.set(xlabel="Zeit (ms)", ylabel="Messdaten − Vorhersage")
    for axis in (top, bottom):
        axis.grid(alpha=0.2)
        if axis.get_legend_handles_labels()[0]:
            axis.legend(fontsize=8)
    figure.savefig(path, dpi=150)


def run_symbolic_pilot(
    config: SymbolicPilotConfig,
    original: bytes,
    source_filename: str,
    output_directory,
    *,
    _assessment=None,
) -> PilotRun:
    """Persist schema 3, retaining classical references and all individual SR arms."""
    # Detect collisions before output reservation; the reference stage draws anew
    # from these same initial states, exactly once, using the existing schema-2 code.
    pilot_generators(config.noise.seed, config.background.seed)
    reference_config = config.reference_config()
    reference_bytes = _reference_toml(reference_config)
    output = Path(output_directory).resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    metadata = {
        "schema_version": 3,
        "status": "running",
        "started_at_utc": _utc_now(),
        "provenance": _provenance(),
        "environment": _environment(),
        "configuration": {
            "source_filename": source_filename,
            "original_sha256": _sha256(original),
            "resolved_sha256": _sha256(_json_bytes(config.to_dict())),
        },
        "artifact_sha256": {},
    }
    if _assessment is not None:
        metadata["supplemental_assessment"] = _assessment.install(output)
    _write_json(output / "metadata_initial.json", metadata)
    _write_json(output / "metadata.json", metadata)
    (output / "config.toml").write_bytes(original)
    (output / "reference_config.toml").write_bytes(reference_bytes)
    _write_json(output / "resolved_config.json", config.to_dict())
    if _assessment is not None:
        _assessment.bind_initial(output)
    result = {
        "schema_version": 3,
        "status": "running",
        "stage": "reference",
        "shared_inputs_file": "reference/comparison_inputs.npz",
        "reference": {
            "status": "not_run",
            "schema_version": 2,
            "result_file": "reference/result.json",
        },
        "symbolic_arms": {
            name: {
                "status": "not_run",
                "result_file": f"symbolic/{name}/result.json",
                "selected": None,
                "metrics": None,
                "error": None,
            }
            for name in ARM_LABELS
        },
        "evaluation_scope": "fitted_samples_only",
        "error": None,
    }
    _write_json(output / "result.json", result)
    arrays = {}
    try:
        result["reference"]["status"] = "running"
        _write_json(output / "result.json", result)
        reference = run_covariance_pilot(
            reference_config,
            reference_bytes,
            "reference_config.toml",
            output / "reference",
            _capture_inputs=True,
        )
        result["reference"]["status"] = reference.status
        if reference.status != "success":
            raise RuntimeError(
                "Classical data preparation/reference comparison failed; see reference/result.json."
            )
        reference_result = json.loads(
            (reference.output_directory / "result.json").read_text()
        )
        result["covariance_estimation"] = dict(
            reference_result["covariance_estimation"]
        )
        for key in ("covariance_file", "raw_covariance_file"):
            result["covariance_estimation"][key] = (
                "reference/" + result["covariance_estimation"][key]
            )
        reference_meta = json.loads(
            (reference.output_directory / "metadata.json").read_text()
        )
        handoff = reference.output_directory / "comparison_inputs.npz"
        if reference_meta["artifact_sha256"].get("comparison_inputs.npz") != _sha256(
            handoff.read_bytes()
        ):
            raise ValueError("Reference input snapshot checksum mismatch.")
        with np.load(
            reference.output_directory / "comparison_inputs.npz", allow_pickle=False
        ) as inputs:
            data = {name: inputs[name].copy() for name in inputs.files}
        for array in data.values():
            array.setflags(write=False)
        arrays.update(
            {name: data[name] for name in ("time_s", "signal", "noise", "observed")}
        )
        result["stage"] = "symbolic_search"
        _write_json(output / "result.json", result)
        for name in ARM_LABELS:
            covariance = (
                None
                if name == "ordinary"
                else data[
                    "covariance_true"
                    if name == "known_covariance"
                    else "covariance_estimated"
                ]
            )
            record = result["symbolic_arms"][name]
            record["status"] = "running"
            _write_json(output / "result.json", result)
            try:
                arm = run_search_arm(
                    data["time_s"],
                    data["observed"],
                    covariance=covariance,
                    output=output / "symbolic" / name,
                    budget=config.symbolic_search,
                )
                if arm.status != "success":
                    raise RuntimeError(
                        f"Search worker failed; see symbolic/{name}/worker.log."
                    )
                record["status"] = "replay"
                candidates = _verify_arm(
                    arm.output_directory,
                    data["time_s"],
                    data["observed"],
                    covariance,
                    config.symbolic_search,
                )
                index = candidates["selected_index"]
                selected = candidates["candidates"][index]
                record["selected"] = {
                    "index": index,
                    "complexity": selected["complexity"],
                    "display_equation": selected["display_equation"],
                    "training_loss": selected["loss"],
                    "selection": "minimum_training_loss_then_complexity",
                    "parameter_interpretation": "not_attempted",
                }
                record["metrics"] = _diagnose(
                    selected,
                    data["observed"],
                    data["signal"],
                    data["covariance_true"],
                    covariance,
                )
                arrays["prediction_" + name] = np.asarray(selected["prediction"])
                arrays["residual_" + name] = (
                    data["observed"] - arrays["prediction_" + name]
                )
                record["status"] = "success"
            except ARM_ERRORS as error:
                record.update(
                    status="failed",
                    error={"type": type(error).__name__, "message": str(error)},
                )
            _write_json(output / "result.json", result)
        failed = [
            name
            for name, record in result["symbolic_arms"].items()
            if record["status"] != "success"
        ]
        result.update(
            status="comparison_failed" if failed else "success", stage="complete"
        )
        if failed:
            result["error"] = {
                "type": "ComparisonIncomplete",
                "message": "Failed SR arms: " + ", ".join(failed),
            }
    except ARM_ERRORS as error:
        if result["reference"]["status"] == "running":
            result["reference"]["status"] = "failed"
        result.update(
            status="failed", error={"type": type(error).__name__, "message": str(error)}
        )
    except BaseException as error:
        result.update(
            status="aborted",
            error={"type": type(error).__name__, "message": str(error)},
        )
        raise
    finally:
        try:
            if arrays:
                _save_samples(output / "samples.csv", arrays)
                _save_symbolic_plot(output / "plot.png", arrays)
        except BaseException as error:
            result.update(
                status="export_failed",
                error={"type": type(error).__name__, "message": str(error)},
            )
            raise
        finally:
            _write_json(output / "result.json", result)
            metadata.update(
                status=result["status"],
                finished_at_utc=_utc_now(),
                elapsed_seconds=time.perf_counter() - started,
            )
            metadata["artifact_sha256"] = {
                path.relative_to(output).as_posix(): _sha256(path.read_bytes())
                for path in sorted(output.rglob("*"))
                if path.is_file() and path != output / "metadata.json"
            }
            _write_json(output / "metadata.json", metadata)
    return PilotRun(output, result["status"])
