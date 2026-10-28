"""Run the nine reviewed noiseless development cells, retaining incomplete series."""

import argparse
import importlib.util
import io
import signal
from collections import Counter
from pathlib import Path

import numpy as np

from ringdown_sr import symbolic
from ringdown_sr.noiseless_control import (
    CURVE_LIMITS,
    FORMAT,
    FS,
    PARAMETER_LIMITS,
    PLAN_COMMIT,
    PLAN_SHA256,
    TRUTH,
    budget_summaries,
    diagnose_candidate,
    fingerprint,
    frozen_data,
    planned_cells,
)
from ringdown_sr.parameter_export import _candidate
from ringdown_sr.pilot import _sha256, _utc_now, _write_json

ROOT = symbolic.ROOT
PLAN = ROOT / "docs/noiseless_control_plan.md"


def load_support():
    """Reuse the existing controlled worker, launcher and pool verification."""
    spec = importlib.util.spec_from_file_location(
        "noiseless_repeat_support", ROOT / "scripts/repeat_symbolic_arm.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_hashes():
    paths = [
        *sorted((ROOT / "src/ringdown_sr").glob("*.py")),
        ROOT / "scripts/run_noiseless_control.py",
        ROOT / "scripts/repeat_symbolic_arm.py",
        ROOT / "scripts/probe_symbolic_numerics.py",
        ROOT / "scripts/run_python.py",
        ROOT / "scripts/run_symbolic_worker.py",
        PLAN,
        ROOT / "julia/src/RingdownSRLoss.jl",
        ROOT / "julia/src/RingdownSRSearch.jl",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        ROOT / "julia/Project.toml",
        ROOT / "julia/Manifest.toml",
    ]
    return {
        path.relative_to(ROOT).as_posix(): _sha256(path.read_bytes()) for path in paths
    }


def core_snapshot(probe):
    probe.validate_core_request("Haswell")
    snapshot = probe.metadata()
    snapshot["blas_control"] = probe.verify_blas_control(
        snapshot["environment"], "Haswell", require_julia=False
    )
    return snapshot


def verify_cell(directory, cell, arrays, support, probe, initial, tools):
    """Validate immutable inputs, original selection, source and worker snapshots."""
    contents = support.source_bytes(directory)

    def read(name):
        return support.read_json(contents[name])

    if read("request.json") != {"format": symbolic.FORMAT, "budget": cell["budget"]}:
        raise ValueError("The worker changed the reviewed request.")
    with np.load(io.BytesIO(contents["inputs.npz"]), allow_pickle=False) as saved:
        if set(saved.files) != {"time_s", "observed"} or any(
            saved[key].dtype.kind != "f"
            or saved[key].dtype.itemsize != 8
            or fingerprint(saved[key]) != fingerprint(arrays[key])
            for key in saved.files
        ):
            raise ValueError("The worker changed the frozen ordinary-search inputs.")
    metadata, first = read("metadata.json"), read("metadata_initial.json")
    if metadata["phase"] != "success" or metadata["provenance"] != first["provenance"]:
        raise ValueError("Incomplete worker or replaced parent provenance.")
    for key in ("provenance", "worker_provenance"):
        if metadata[key] != initial["provenance"]:
            raise ValueError("Worker source provenance changed.")
    for key in ("adapter_source_sha256", "worker_adapter_source_sha256"):
        if metadata[key] != initial["adapter_source_sha256"]:
            raise ValueError("Worker adapter sources changed.")
    control = support.verify_worker_control(
        directory, metadata, "Haswell", tools, probe
    )
    control_digest = read("checksums.json")["blas_control.json"]
    front = read("result.json")
    support.signature(front)
    if (
        front["evaluation_scope"] != "fitted_samples_only"
        or front["selection"] != "minimum_training_loss_then_complexity"
    ):
        raise ValueError("Unexpected recorded selection scope or policy.")
    selected = front["selected_index"]
    if selected != symbolic.select_candidate(front["candidates"]):
        raise ValueError("The recorded selection disagrees with its training rule.")
    parameters = read("pysr_parameters.json")
    expected = symbolic.search_parameters(symbolic.SearchBudget(**cell["budget"]))
    if any(
        parameters.get(key) != value or key not in parameters
        for key, value in expected.items()
    ):
        raise ValueError("Effective PySR parameters differ from the reviewed policy.")
    for index, candidate in enumerate(front["candidates"]):
        _candidate(candidate, index, selected, arrays["time_s"], FS)
    diagnoses = [
        diagnose_candidate(candidate, index, selected, arrays)
        for index, candidate in enumerate(front["candidates"])
    ]
    if support.source_bytes(directory) != contents:
        raise ValueError("Worker artifacts changed during diagnosis.")
    if _sha256((directory / "blas_control.json").read_bytes()) != control_digest:
        raise ValueError("Worker BLAS control changed during diagnosis.")
    return {
        "selected_index": selected,
        "selection_role": "recorded_only; no reranking",
        "candidate_count": len(diagnoses),
        "candidates": diagnoses,
        "front_structure_counts": dict(
            Counter(
                item["analysis"]["structure"]["structure_status"] for item in diagnoses
            )
        ),
        "front_first_reason_counts": dict(
            Counter(
                item["analysis"]["structure"]["reason"]
                for item in diagnoses
                if item["analysis"]["structure"]["reason"] is not None
            )
        ),
        "front_has_recognized": any(
            item["analysis"]["structure"]["structure_status"] == "recognized"
            for item in diagnoses
        ),
        "source_file_sha256": {name: _sha256(data) for name, data in contents.items()},
        "blas_control": control,
        "blas_control_sha256": control_digest,
        "recorded_initial_metadata": first,
        "recorded_metadata": metadata,
        "rng": front["rng"],
        "timing_seconds": front["timing_seconds"],
        "backend_evaluation_counter": front["backend_evaluation_counter"],
        "effective_parameters": parameters,
        "effective_backend_options": read("backend_options.json"),
    }


def policy_signature(diagnosis, support):
    parameters = support.parameters_without_output(diagnosis["effective_parameters"])
    backend = support.backend_without_output(diagnosis["effective_backend_options"])
    # These are the sole planned factors (the backend seed is recorded separately).
    return {
        "pysr": {
            key: value
            for key, value in parameters.items()
            if key not in {"random_state", "niterations"}
        },
        "backend": {
            key: value
            for key, value in backend.items()
            if key not in {"seed", "niterations"}
        },
    }


def summary_text(report):
    lines = [
        "# Rauschfreie Entwicklungsdiagnose",
        "",
        f"Serienstatus: `{report['status']}`. Keine physikalische Identifikation.",
        "",
        "Alle neun geplanten Zellen; fehlende Werte bleiben sichtbar.",
        "",
        "| Zelle | Seed | Iterationen | Status | Training RMS | Zwischenpunkte RMS | Zwischenpunkte Max | Struktur | Parameter |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for cell in report["cells"]:
        diagnosis = cell.get("diagnostics")
        selected = (
            diagnosis["candidates"][diagnosis["selected_index"]] if diagnosis else None
        )
        fields = [
            str(cell["number"]),
            str(cell["budget"]["seed"]),
            str(cell["budget"]["niterations"]),
            cell["status"],
        ]
        if selected:
            errors = selected["curve_errors"]
            fields += [
                str(errors["training"]["relative_rms"]),
                str(errors["diagnostic"]["relative_rms"]),
                str(errors["diagnostic"]["relative_max"]),
                selected["analysis"]["structure"]["structure_status"],
                selected["parameter_match"]["status"],
            ]
        else:
            fields += ["nicht verfügbar"] * 5
        lines.append("| " + " | ".join(fields) + " |")
    lines += [
        "",
        "## Deskriptive Budgetübersicht",
        "",
        "Nur vollständige Gruppen erhalten Minimum/Median/Maximum; JSON enthält die verfügbaren Nenner.",
        "",
    ]
    for budget, summary in report["budget_summaries"].items():
        lines += [
            f"- {budget} Iterationen: `{summary['status']}`, Zellzustände `{summary['cell_states']}`."
        ]
        if summary["statistics"]:
            for grid, metrics in summary["statistics"].items():
                for metric, values in metrics.items():
                    lines += [
                        f"  - {grid}/{metric}: {values['minimum']} / {values['median']} / {values['maximum']} ({values['finite_count']}/3 endlich)."
                    ]
    lines += [
        "",
        "Das Achtelraster hat einen Alias-Blindfleck bei Frequenzabständen 8·fs. Eine passende Aliasklasse und bestandene Rasterprüfungen beweisen keinen Verlauf zu beliebigen Zwischenzeiten.",
        "",
        "Alle Kandidaten, Originalauswahlen, Parameterdiagnosen, Fehlergründe und Herkunft stehen in report.json und den unveränderten Zellverzeichnissen.",
        "",
    ]
    if report.get("error"):
        lines += [f"Abbruchgrund: {report['error']}", ""]
    return "\n".join(lines)


def save_report(output, report):
    report["budget_summaries"] = budget_summaries(report["cells"])
    if "final_verification_error" in report:
        for summary in report["budget_summaries"].values():
            summary.update(
                status="not_assessed",
                reason="final_verification_failed",
                statistics=None,
                selected_diagnoses=None,
            )
    report["cell_states"] = dict(Counter(cell["status"] for cell in report["cells"]))
    report["started_count"] = sum("started_at_utc" in cell for cell in report["cells"])
    _write_json(output / "report.json", report)
    temporary = output / "summary.md.tmp"
    temporary.write_text(summary_text(report), encoding="utf-8")
    temporary.replace(output / "summary.md")


def run_control(output, *, label):
    """Run the fixed series once; infrastructure failures stop without replacements."""
    output = Path(output).resolve()
    if not isinstance(label, str) or not label.strip():
        raise ValueError("A nonempty machine label is required.")
    if output.exists():
        raise FileExistsError(output)
    if ROOT.is_relative_to(output) or any(
        output.is_relative_to(ROOT / name)
        for name in ("src", "scripts", "docs", "julia", ".git")
    ):
        raise ValueError("Output must not overlap repository sources.")
    plan = PLAN.read_bytes()
    if _sha256(plan) != PLAN_SHA256:
        raise ValueError("The method plan differs from the reviewed snapshot.")
    support = load_support()
    probe = support.load_core_probe()
    initial = core_snapshot(probe)
    sources, tools = source_hashes(), support.tool_hashes()
    arrays = frozen_data()
    expected_arrays = {key: fingerprint(value) for key, value in arrays.items()}
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "format": FORMAT,
        "status": "running",
        "label": label,
        "scope": "one noiseless development signal; descriptive three-seed budget control",
        "physical_identification": "not_assessed",
        "started_at_utc": _utc_now(),
        "plan": {"commit": PLAN_COMMIT, "sha256": PLAN_SHA256},
        "configuration": {
            "sample_rate_hz": FS,
            "n_samples": 128,
            "truth": TRUTH,
            "curve_limits": CURVE_LIMITS,
            "parameter_limits": PARAMETER_LIMITS,
            "covariance": None,
        },
        "cells": planned_cells(),
        "input_fingerprints": expected_arrays,
        "source_sha256": sources,
        "tool_source_sha256": tools,
        "control_initial": initial,
        "diagnoser": {"role": "post_selection_only", "initial": initial},
    }
    original_dispatch = symbolic._run_worker
    failure = None
    try:
        save_report(output, report)
        (output / "plan.md").write_bytes(plan)
        np.savez(
            output / "training.npz",
            **{key: arrays[key] for key in ("time_s", "observed")},
        )
        np.savez(
            output / "diagnostic.npz",
            **{key: arrays[key] for key in ("diagnostic_time_s", "diagnostic_truth")},
        )
        frozen_files = {
            name: _sha256((output / name).read_bytes())
            for name in ("training.npz", "diagnostic.npz", "plan.md")
        }
        report["frozen_file_sha256"] = frozen_files
        runtime = output / "runtime"
        runtime.mkdir()
        (runtime / "driver.py").write_bytes(Path(support.__file__).read_bytes())
        (runtime / "probe_symbolic_numerics.py").write_bytes(
            Path(probe.__file__).read_bytes()
        )
        (runtime / "orchestrator.py").write_bytes(Path(__file__).read_bytes())
        frozen_files.update(
            {
                path.relative_to(output).as_posix(): _sha256(path.read_bytes())
                for path in sorted(runtime.iterdir())
            }
        )
        symbolic._run_worker = support.controlled_dispatch(
            runtime, "Haswell", original_dispatch
        )
        first_policy = None
        for cell in report["cells"]:
            if (
                source_hashes() != sources
                or support.tool_hashes() != tools
                or any(
                    _sha256((output / name).read_bytes()) != digest
                    for name, digest in frozen_files.items()
                )
            ):
                raise ValueError("Control inputs, method plan or sources changed.")
            cell.update(status="running", started_at_utc=_utc_now())
            save_report(output, report)
            print(f"Starting cell {cell['number']}/9: {cell['budget']}", flush=True)
            run = symbolic.run_search_arm(
                arrays["time_s"],
                arrays["observed"],
                covariance=None,
                output=output / cell["directory"],
                budget=symbolic.SearchBudget(**cell["budget"]),
            )
            cell["search_status"] = run.status
            if run.status != "success":
                raise RuntimeError(
                    f"Worker failed in {cell['directory']}; see worker.log."
                )
            diagnosis = verify_cell(
                output / cell["directory"], cell, arrays, support, probe, initial, tools
            )
            cell["diagnostics"] = diagnosis
            policy = policy_signature(diagnosis, support)
            if first_policy is None:
                first_policy = policy
            elif policy != first_policy:
                raise ValueError("Unplanned effective PySR or backend option change.")
            if any(
                fingerprint(value) != expected_arrays[key]
                for key, value in arrays.items()
            ):
                raise ValueError("A shared in-memory reference changed.")
            cell.update(status="completed", finished_at_utc=_utc_now())
            save_report(output, report)
        report["status"] = "completed"
    except BaseException as error:
        failure = error
        interrupted = isinstance(error, (KeyboardInterrupt, SystemExit))
        report.update(
            status="aborted" if interrupted else "failed",
            error=f"{type(error).__name__}: {error}",
        )
        for cell in report["cells"]:
            if cell["status"] == "running":
                cell.update(
                    status="aborted" if interrupted else "failed",
                    finished_at_utc=_utc_now(),
                    error=report["error"],
                )
        raise
    finally:
        symbolic._run_worker = original_dispatch
        final_error = None
        try:
            final = core_snapshot(probe)
            report["control_final"] = final
            report["diagnoser"]["final"] = final
            if (
                any(
                    final[key] != initial[key]
                    for key in ("provenance", "adapter_source_sha256")
                )
                or source_hashes() != sources
                or support.tool_hashes() != tools
            ):
                raise ValueError("Sources or provenance changed during the control.")
            if any(
                fingerprint(value) != expected_arrays[key]
                for key, value in arrays.items()
            ):
                raise ValueError("A shared in-memory reference changed.")
            for name, digest in report.get("frozen_file_sha256", {}).items():
                if _sha256((output / name).read_bytes()) != digest:
                    raise ValueError("A frozen control input changed.")
            for cell in report["cells"]:
                for name, digest in (
                    cell.get("diagnostics", {}).get("source_file_sha256", {}).items()
                ):
                    if (
                        _sha256((output / cell["directory"] / name).read_bytes())
                        != digest
                    ):
                        raise ValueError("A diagnosed source artifact changed.")
                diagnosis = cell.get("diagnostics")
                if (
                    diagnosis
                    and _sha256(
                        (output / cell["directory"] / "blas_control.json").read_bytes()
                    )
                    != diagnosis["blas_control_sha256"]
                ):
                    raise ValueError("A worker BLAS control record changed.")
        except BaseException as error:  # noqa: BLE001 -- Preserve the primary error.
            final_error = error
            report.update(
                status="failed",
                final_verification_error=f"{type(error).__name__}: {error}",
            )
        report["finished_at_utc"] = _utc_now()
        save_report(output, report)
        checksums = {}
        for path in sorted(output.rglob("*")):
            if path.is_symlink():
                raise ValueError("Control artifacts must not be symbolic links.")
            if path.is_file() and path != output / "metadata.json":
                checksums[path.relative_to(output).as_posix()] = _sha256(
                    path.read_bytes()
                )
        _write_json(
            output / "metadata.json",
            {
                "format": FORMAT,
                "status": report["status"],
                "artifact_sha256": checksums,
                "integrity_scope": "recorded consistency, not external authenticity",
            },
        )
        if final_error is not None and failure is None:
            raise final_error
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    def terminate(_signal, _frame):
        raise KeyboardInterrupt("SIGTERM received; retain incomplete series.")

    previous = signal.signal(signal.SIGTERM, terminate)
    try:
        run_control(args.output, label=args.label)
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    main()
