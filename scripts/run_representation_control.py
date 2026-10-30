"""Run the frozen nine-cell representation control with fail-closed verification."""

import argparse
import importlib.util
import io
import signal
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from ringdown_sr import symbolic
from ringdown_sr.noiseless_control import (
    CURVE_LIMITS,
    FS,
    PARAMETER_LIMITS,
    TRUTH,
    fingerprint,
    frozen_data,
)
from ringdown_sr.parameter_export import _candidate
from ringdown_sr.pilot import _sha256, _utc_now, _write_json
from ringdown_sr.representation_control import (
    FORMAT,
    PLAN_COMMIT,
    PLAN_SHA256,
    condition_summaries,
    diagnose_candidate,
    planned_cells,
    search_coordinates,
    seed_differences,
)
from ringdown_sr.representation_profiles import (
    PROFILE_FORMAT,
    RUNTIME_FILES,
    normalized_backend_fields,
    profile_parameters,
    source_hashes,
    validate_plugin_records,
    verify_manifest,
)

ROOT = symbolic.ROOT
PLAN = ROOT / "docs/search_representation_plan.md"
EXTRA_FILES = (
    "representation_profile.json",
    "representation_manifest.json",
    "representation_verification.json",
    "RepresentationProfiles.jl",
    "RingdownSRLoss.jl",
    "RingdownSRSearch.jl",
    "blas_control.json",
)


def load_base():
    spec = importlib.util.spec_from_file_location(
        "representation_base", ROOT / "scripts/run_noiseless_control.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base()


def read_json(path):
    return BASE.load_support().read_json(path.read_bytes())


def dispatch(runtime, cell, sources, original):
    """Keep the established launcher and process-group cancellation unchanged."""

    def run(command, *, stdout):
        expected = [
            sys.executable,
            str(ROOT / "scripts/run_python.py"),
            str(ROOT / "scripts/run_symbolic_worker.py"),
        ]
        if len(command) != 4 or command[:3] != expected:
            raise ValueError("Unexpected representation worker command.")
        directory = Path(command[3])
        request = read_json(directory / "request.json")
        if request != {"format": symbolic.FORMAT, "budget": cell["budget"]}:
            raise ValueError("Unexpected representation worker budget.")
        _write_json(
            directory / "representation_profile.json",
            {
                "format": PROFILE_FORMAT,
                "condition": cell["condition"],
            },
        )
        manifest = {
            "format": "ringdown-sr-representation-manifest-1",
            "sources": sources,
            "runtime": {
                name: sources[source] for name, source in RUNTIME_FILES.items()
            },
            "inputs": {
                name: _sha256((directory / name).read_bytes())
                for name in (
                    "request.json",
                    "inputs.npz",
                    "representation_profile.json",
                )
            },
        }
        verify_manifest(manifest, directory, runtime)
        _write_json(directory / "representation_manifest.json", manifest)
        return original(
            [*command[:2], str(runtime / "run_representation_worker.py"), command[3]],
            stdout=stdout,
        )

    return run


def inspect_backend(output, runtime, original, initial, sources, support, probe):
    """Run options and fixed references in separate pinned processes before any cell."""
    for script, filename in (
        ("check_representation_backend.py", "preflight.json"),
        ("check_representation_references.py", "references.json"),
    ):
        with (output / (filename + ".log")).open("w", encoding="utf-8") as log:
            result = original(
                [
                    sys.executable,
                    str(ROOT / "scripts/run_python.py"),
                    str(runtime / script),
                    "--output",
                    str(output / filename),
                ],
                stdout=log,
            )
        if result.returncode:
            raise RuntimeError(f"Representation preflight failed; see {filename}.log.")
    preflight = read_json(output / "preflight.json")
    references = read_json(output / "references.json")
    verify_preflight(preflight, initial, sources, support, probe)
    if references["status"] != "verified" or references["source_sha256"] != sources:
        raise ValueError("Invalid fixed-reference verification.")
    return preflight


def verify_preflight(record, initial, sources, support, probe):
    if (
        record["format"] != "ringdown-sr-representation-preflight-1"
        or record["status"] != "verified"
        or record["callback_calls"] != 0
        or record["source_sha256"] != sources
        or len(record["profiles"]) != 9
    ):
        raise ValueError("Invalid options-only preflight.")
    for snapshot in (record["initial"], record["final"]):
        if any(
            snapshot[key] != initial[key]
            for key in ("provenance", "adapter_source_sha256")
        ):
            raise ValueError("Preflight source provenance changed.")
        if snapshot["blas_control"] != probe.verify_blas_control(
            snapshot["environment"], "Haswell", require_julia=True
        ):
            raise ValueError("Preflight BLAS record changed.")
    expected = {(c["condition"], c["budget"]["seed"]): c for c in planned_cells()}
    seen = set()
    first = None
    for profile in record["profiles"]:
        key = profile["condition"], profile["python_seed"]
        if key not in expected or key in seen:
            raise ValueError("Missing or repeated preflight cell.")
        seen.add(key)
        validate_plugin_records(profile["plugins"], profile["condition"])
        normalized = normalized_backend_fields(
            profile["backend_options"], key[0], profile["plugins_field"]
        )
        BASE.verify_backend_policy(
            normalized,
            expected[key]["budget"],
            {
                "python_seed": key[1],
                "backend_seed": profile["backend_seed"],
            },
            support,
        )
        fields = support.backend_without_output(normalized)
        # Only exclude individually checked seeds and the fully verified plugin field.
        common = {k: v for k, v in fields.items() if k not in {"seed", "plugins"}}
        if first is not None and common != first:
            raise ValueError("Unplanned cross-profile backend difference.")
        first = common


def worker_bytes(directory, support):
    contents = support.source_bytes(directory)
    checksums = support.read_json(contents["checksums.json"])
    for name in EXTRA_FILES:
        path = directory / name
        if path.is_symlink():
            raise ValueError("Worker artifacts must not be symbolic links.")
        contents[name] = path.read_bytes()
        if checksums.get(name) != _sha256(contents[name]):
            raise ValueError(f"Worker checksum mismatch: {name}")
    return contents


def verify_cell(
    directory, cell, arrays, support, probe, initial, tools, sources, preflight
):
    contents = worker_bytes(directory, support)
    read = lambda name: support.read_json(contents[name])
    coordinates = search_coordinates(arrays, cell["condition"])
    if read("request.json") != {"format": symbolic.FORMAT, "budget": cell["budget"]}:
        raise ValueError("Worker changed the reviewed request.")
    with np.load(io.BytesIO(contents["inputs.npz"]), allow_pickle=False) as saved:
        if set(saved.files) != {"time_s", "observed"} or any(
            saved[key].dtype.kind != "f"
            or saved[key].dtype.itemsize != 8
            or fingerprint(saved[key]) != fingerprint(coordinates[key])
            for key in saved.files
        ):
            raise ValueError("Worker changed the frozen coordinate/observation bits.")
    profile = {"format": PROFILE_FORMAT, "condition": cell["condition"]}
    if read("representation_profile.json") != profile:
        raise ValueError("Worker profile changed.")
    manifest = read("representation_manifest.json")
    if manifest["sources"] != sources:
        raise ValueError("Worker consumed different sources.")
    verify_manifest(manifest, directory, directory.parent / "runtime")
    for name in (
        "RingdownSRLoss.jl",
        "RingdownSRSearch.jl",
        "RepresentationProfiles.jl",
    ):
        if _sha256(contents[name]) != sources["julia/src/" + name]:
            raise ValueError("Worker consumed a different Julia source.")
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
    front = read("result.json")
    support.signature(front)
    if (
        front["evaluation_scope"] != "fitted_samples_only"
        or front["selection"] != "minimum_training_loss_then_complexity"
    ):
        raise ValueError("Unexpected selection scope or policy.")
    selected = front["selected_index"]
    parameters = read("pysr_parameters.json")
    expected = profile_parameters(
        symbolic.SearchBudget(**cell["budget"]), cell["condition"]
    )
    if any(
        key not in parameters or parameters[key] != value
        for key, value in expected.items()
    ):
        raise ValueError("Effective PySR parameters differ from the reviewed profile.")
    record = read("representation_verification.json")
    reference = next(
        p
        for p in preflight["profiles"]
        if (p["condition"], p["python_seed"])
        == (cell["condition"], cell["budget"]["seed"])
    )
    validate_plugin_records(record["plugins"], cell["condition"])
    calls = front["callback_calls_during_fit"]
    if (
        record["format"] != "ringdown-sr-representation-verification-1"
        or record["status"] != "verified"
        or record["condition"] != cell["condition"]
        or type(record["backend_seed"]) is not int
        or record["backend_seed"] != reference["backend_seed"]
        or record["plugins"] != reference["plugins"]
        or record["plugins_field"] != reference["plugins_field"]
        or record["profile_sha256"] != _sha256(contents["representation_profile.json"])
        or record["manifest_sha256"]
        != _sha256(contents["representation_manifest.json"])
        or record["julia_source_sha256"]
        != _sha256(contents["RepresentationProfiles.jl"])
        or type(calls) is not int
        or calls <= 0
        or type(record["callback_calls_during_fit"]) is not int
        or record["callback_calls_during_fit"] != calls
        or type(record["callback_calls_total"]) is not int
        or record["callback_calls_total"] != calls + 1
    ):
        raise ValueError("Invalid native profile verification or callback accounting.")
    backend_fields = read("backend_options.json")
    normalized = normalized_backend_fields(
        backend_fields, cell["condition"], reference["plugins_field"]
    )
    checked = BASE.verify_backend_policy(
        normalized, cell["budget"], front["rng"], support
    )
    if support.backend_without_output(backend_fields) != support.backend_without_output(
        reference["backend_options"]
    ):
        raise ValueError("Actual backend options differ from the genuine preflight.")
    checks = []
    for index, candidate in enumerate(front["candidates"]):
        _candidate(
            candidate,
            index,
            selected,
            coordinates["time_s"],
            FS / cell["settings"]["time_scale"],
        )
        checks.append(BASE.verify_training_loss(candidate, arrays["observed"]))
    if selected != symbolic.select_candidate(front["candidates"]):
        raise ValueError("Original selection disagrees with the training rule.")
    diagnoses = [
        diagnose_candidate(candidate, index, selected, arrays, cell["condition"])
        for index, candidate in enumerate(front["candidates"])
    ]
    for diagnosis, check in zip(diagnoses, checks, strict=True):
        diagnosis["training_verification"] = check
    if worker_bytes(directory, support) != contents:
        raise ValueError("Consumed worker artifacts changed during diagnosis.")
    return {
        "selected_index": selected,
        "selection_role": "recorded_only; no reranking",
        "candidate_count": len(diagnoses),
        "candidates": diagnoses,
        "front_structure_counts": dict(
            Counter(
                d["search_analysis"]["structure"]["structure_status"] for d in diagnoses
            )
        ),
        "front_first_reason_counts": dict(
            Counter(
                d["search_analysis"]["structure"]["reason"]
                for d in diagnoses
                if d["search_analysis"]["structure"]["reason"] is not None
            )
        ),
        "source_file_sha256": {name: _sha256(data) for name, data in contents.items()},
        "blas_control": control,
        "recorded_initial_metadata": first,
        "recorded_metadata": metadata,
        "rng": front["rng"],
        "timing_seconds": front["timing_seconds"],
        "callback_calls_during_fit": calls,
        "callback_calls_total": record["callback_calls_total"],
        "backend_evaluation_counter": front["backend_evaluation_counter"],
        "effective_parameters": parameters,
        "effective_backend_options": backend_fields,
        "backend_policy_verification": checked,
        "representation_verification": record,
    }


def policy_signature(diagnosis, support):
    parameters = support.parameters_without_output(diagnosis["effective_parameters"])
    return {
        key: value
        for key, value in parameters.items()
        if key not in {"random_state", "use_frequency", "use_frequency_in_tournament"}
    }


def summary_text(report):
    lines = [
        "# Zeitdarstellungs-Kontrolle",
        "",
        f"Serienstatus: `{report['status']}`.",
        "",
        "Entwicklungsdiagnose; physikalische Identifikation: `not_assessed`.",
        "",
        "Suchkoordinate u und physikalische Zeit t bleiben Sekunden; der vollständige Baum wird als q(alpha*t) ausgewertet.",
        "",
        "| Zelle | Seed | Bedingung | Status | Training RMS | Zwischenpunkte RMS | Struktur | Parameter |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for cell in report["cells"]:
        fields = [
            str(cell["number"]),
            str(cell["budget"]["seed"]),
            cell["condition"],
            cell["status"],
        ]
        diagnosis = cell.get("diagnostics")
        if diagnosis:
            selected = diagnosis["candidates"][diagnosis["selected_index"]]
            fields += [
                str(selected["curve_errors"][grid]["relative_rms"])
                for grid in ("training", "diagnostic")
            ]
            fields += [
                selected["search_analysis"]["structure"]["structure_status"],
                selected["parameter_match"]["status"],
            ]
        else:
            fields += ["nicht verfügbar"] * 4
        lines.append("| " + " | ".join(fields) + " |")
    lines += [
        "",
        "Bedingungen: nur vollständige Dreiergruppen erhalten deskriptive Minima/Mediane/Maxima mit endlichen Nennern.",
        "Seed-Differenzen: Variante minus frische Baseline; fehlende Werte bleiben null. Einzelwerte, Status, Aufwand, alle Kandidaten und getrennte Diagnosen stehen in report.json.",
        "",
        "Das Achtelraster behält den Alias-Blindfleck bei 8·fs = 32768 Hz.",
        "",
    ]
    for condition, summary in report["condition_summaries"].items():
        lines += [f"## {condition}: {summary['status']}", ""]
        if summary["statistics"] is not None:
            lines += [
                "| Kennzahl | Minimum | Median | Maximum | verfügbar |",
                "| --- | --- | --- | --- | --- |",
            ]
            for name, values in summary["statistics"].items():
                lines.append(
                    f"| {name} | {values['minimum']} | {values['median']} | "
                    f"{values['maximum']} | {values['finite_count']}/3 |"
                )
            lines += [
                "",
                f"Getrennte Markierungen: `{summary['selected_diagnoses']}`.",
                "",
            ]
    lines += ["## Differenzen je Seed zur frischen Baseline", ""]
    for pair in report["seed_differences"]:
        lines += [f"### {pair['seed']} / {pair['condition']}: {pair['status']}", ""]
        if pair["metrics"] is None:
            lines += [f"Grund: `{pair['reason']}`.", ""]
            continue
        lines += [
            "| Kennzahl | Baseline | Variante | Differenz | Status |",
            "| --- | --- | --- | --- | --- |",
        ]
        for name, value in pair["metrics"].items():
            lines.append(
                f"| {name} | {value['baseline']} | {value['variant']} | "
                f"{value['difference']} | {value['status']} |"
            )
        lines += [
            "",
            "Einzelstatus und Gründe sowie Callbackzahlen und Zeiten: `report.json`.",
            "",
        ]
    for key in ("error", "final_verification_error"):
        if report.get(key):
            lines += [f"{key}: {report[key]}", ""]
    return "\n".join(lines)


def save_report(output, report):
    verified = report.get("final_verification") == "passed"
    report["condition_summaries"] = condition_summaries(
        report["cells"], final_verified=verified
    )
    report["seed_differences"] = seed_differences(
        report["cells"], final_verified=verified
    )
    if not verified:
        reason = (
            "final_verification_failed"
            if report.get("final_verification") == "failed"
            else "final_verification_pending"
        )
        for item in [
            *report["condition_summaries"].values(),
            *report["seed_differences"],
        ]:
            item["reason"] = reason
    report["cell_states"] = dict(Counter(cell["status"] for cell in report["cells"]))
    report["started_count"] = sum("started_at_utc" in cell for cell in report["cells"])
    _write_json(output / "report.json", report)
    temporary = output / "summary.md.tmp"
    temporary.write_text(summary_text(report), encoding="utf-8")
    temporary.replace(output / "summary.md")


def run_control(output, *, label):
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
        raise ValueError("The representation method plan changed.")
    support = BASE.load_support()
    probe = support.load_core_probe()
    initial = BASE.core_snapshot(probe)
    sources, tools = source_hashes(), support.tool_hashes()
    arrays = frozen_data()
    coordinates = {
        condition: search_coordinates(arrays, condition)
        for condition in ("baseline", "time_stretch", "complexity_frequency")
    }
    expected_arrays = {key: fingerprint(value) for key, value in arrays.items()}
    output.mkdir(parents=True, exist_ok=False)
    frozen_files = {}
    report = {
        "format": FORMAT,
        "status": "running",
        "label": label,
        "scope": "one noiseless development signal; three separate representation conditions",
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
        "frozen_file_sha256": frozen_files,
        "final_verification": "pending",
    }
    original = symbolic._run_worker
    failure = None

    def verify_frozen():
        if source_hashes() != sources or support.tool_hashes() != tools:
            raise ValueError("Control sources changed.")
        if any(
            fingerprint(value) != expected_arrays[key] for key, value in arrays.items()
        ):
            raise ValueError("A shared physical reference changed.")
        for condition, values in coordinates.items():
            expected = search_coordinates(arrays, condition)
            if any(
                fingerprint(value) != fingerprint(expected[key])
                for key, value in values.items()
            ):
                raise ValueError("A derived search coordinate changed.")
        for name, digest in frozen_files.items():
            path = output / name
            if path.is_symlink() or _sha256(path.read_bytes()) != digest:
                raise ValueError("A frozen control input or runtime copy changed.")

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
        for condition, values in coordinates.items():
            np.savez(
                output / (condition + ".npz"),
                **{key: values[key] for key in ("time_s", "observed")},
            )
        runtime = output / "runtime"
        runtime.mkdir()
        for name, source in RUNTIME_FILES.items():
            (runtime / name).write_bytes((ROOT / source).read_bytes())
        frozen_files.update(
            {
                p.relative_to(output).as_posix(): _sha256(p.read_bytes())
                for p in [output / "plan.md", *output.glob("*.npz"), *runtime.iterdir()]
            }
        )
        preflight = inspect_backend(
            output, runtime, original, initial, sources, support, probe
        )
        for name in ("preflight.json", "references.json"):
            frozen_files[name] = _sha256((output / name).read_bytes())
        report["preflight"] = {
            "status": "verified",
            "files": ["preflight.json", "references.json"],
        }
        first_policy = None
        for cell in report["cells"]:
            verify_frozen()
            cell.update(status="running", started_at_utc=_utc_now())
            save_report(output, report)
            symbolic._run_worker = dispatch(runtime, cell, sources, original)
            print(
                f"Starting cell {cell['number']}/9: {cell['condition']} {cell['budget']}",
                flush=True,
            )
            values = coordinates[cell["condition"]]
            run = symbolic.run_search_arm(
                values["time_s"],
                values["observed"],
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
                output / cell["directory"],
                cell,
                arrays,
                support,
                probe,
                initial,
                tools,
                sources,
                preflight,
            )
            cell["diagnostics"] = diagnosis
            policy = policy_signature(diagnosis, support)
            if first_policy is not None and policy != first_policy:
                raise ValueError("Unplanned effective PySR option change.")
            first_policy = policy
            verify_frozen()
            cell.update(status="completed", finished_at_utc=_utc_now())
            save_report(output, report)
        report["status"] = "completed"
    except BaseException as error:
        failure = error
        status = (
            "aborted"
            if isinstance(error, (KeyboardInterrupt, SystemExit))
            else "failed"
        )
        report.update(status=status, error=f"{type(error).__name__}: {error}")
        for cell in report["cells"]:
            if cell["status"] == "running":
                cell.update(
                    status=status, finished_at_utc=_utc_now(), error=report["error"]
                )
        raise
    finally:
        symbolic._run_worker = original
        final_error = None
        try:
            final = BASE.core_snapshot(probe)
            report["control_final"] = final
            report["diagnoser"]["final"] = final
            if any(
                final[key] != initial[key]
                for key in ("provenance", "adapter_source_sha256")
            ):
                raise ValueError("Control provenance changed.")
            verify_frozen()
            for cell in report["cells"]:
                for name, digest in (
                    cell.get("diagnostics", {}).get("source_file_sha256", {}).items()
                ):
                    path = output / cell["directory"] / name
                    if path.is_symlink() or _sha256(path.read_bytes()) != digest:
                        raise ValueError(
                            "A consumed worker artifact changed after diagnosis."
                        )
            for path in output.rglob("*"):
                if path.is_symlink():
                    raise ValueError("Control artifacts must not be symbolic links.")
            report["final_verification"] = "passed"
        except BaseException as error:  # noqa: BLE001 -- Retain the primary failure.
            final_error = error
            report.update(
                status="failed",
                final_verification="failed",
                final_verification_error=f"{type(error).__name__}: {error}",
            )
        report["finished_at_utc"] = _utc_now()
        save_report(output, report)
        _write_json(
            output / "metadata.json",
            {
                "format": FORMAT,
                "status": report["status"],
                "artifact_sha256": {
                    p.relative_to(output).as_posix(): _sha256(p.read_bytes())
                    for p in sorted(output.rglob("*"))
                    if p.is_file()
                    and not p.is_symlink()
                    and p != output / "metadata.json"
                },
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
