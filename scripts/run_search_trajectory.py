"""Run the six accepted observation/control cells with fail-closed publication."""

import argparse
import importlib.util
import io
import math
import signal
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from ringdown_sr import search_trajectory as policy
from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import read_archive
from ringdown_sr.noiseless_control import (
    CURVE_LIMITS,
    FS,
    PARAMETER_LIMITS,
    TRUTH,
    fingerprint,
)
from ringdown_sr.parameter_export import _candidate
from ringdown_sr.pilot import _sha256, _utc_now, _write_json
from ringdown_sr.representation_control import diagnose_candidate

ROOT = symbolic.ROOT


def load_helpers():
    """Use a private instance of the already hardened publication implementation."""
    spec = importlib.util.spec_from_file_location(
        "trajectory_publication_helpers", ROOT / "scripts/run_free_optimizer_budget.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HELPERS = load_helpers()
BASE = HELPERS.BASE
WallTimeLimit = HELPERS.WallTimeLimit
checked_hash = HELPERS.checked_hash
artifact_hashes = HELPERS.artifact_hashes
launch = HELPERS.launch
EXTRA_FILES = (
    "profile.json",
    "manifest.json",
    "verification.json",
    "blas_control.json",
    "RingdownSRLoss.jl",
    "RingdownSRSearch.jl",
    "RepresentationProfiles.jl",
    "FreeOptimizerBudget.jl",
    "SearchTrajectory.jl",
)


def locked_interpretation(cells, *, final_verified):
    """Release comparative interpretation only after every cell and pair passed."""
    return {"comparative_interpretation": None}


def save_report(output, report):
    cells, pairs = report["cells"], report["pairs"]
    complete = (
        report["status"] == "completed"
        and report["final_verification"] == "passed"
        and len(cells) == 6
        and all(cell["status"] == "completed" for cell in cells)
        and len(pairs) == 3
        and all(pair["status"] == "passed" for pair in pairs)
    )
    report["comparative_interpretation"] = (
        {
            "status": "available",
            "scope": "observed return boundaries only; no causal search history",
            "paired_export_equality": "passed",
            "physical_identification": "not_assessed",
            "front_membership_implies_temporal_disappearance": False,
        }
        if complete
        else None
    )
    lines = [
        "# Begrenzte Beobachtung der freien Suche",
        "",
        f"Serienstatus: `{report['status']}`, Abschlussverifikation: `{report['final_verification']}`.",
        "",
        "| Zelle | Seed | Beobachtung | Status | Auswahlindex | Aufnahmen |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for cell in cells:
        diagnosis = cell.get("diagnostics", {})
        observation = diagnosis.get("observation", {})
        lines.append(
            "| "
            + " | ".join(
                map(
                    str,
                    (
                        cell["number"],
                        cell["budget"]["seed"],
                        "an" if cell["observed"] else "aus",
                        cell["status"],
                        diagnosis.get("selected_index", "nicht verfügbar"),
                        observation.get("event_count", "nicht verfügbar"),
                    ),
                )
            )
            + " |"
        )
    lines += [
        "",
        "Vergleichende Interpretation: "
        + ("freigegeben." if complete else "gesperrt."),
        "Freigabe verlangt sechs vollständige Zellen, drei bestandene Paarvergleiche und Abschlussprüfung.",
        "",
        "Frontzugehörigkeit und zeitliches Auftreten werden getrennt ausgewiesen.",
        "Fehlende Frontzugehörigkeit belegt kein Verschwinden aus Population oder Hall of Fame.",
        "Physikalische Identifikation bleibt not_assessed; der Achtelraster-Blindfleck bei 8·fs bleibt bestehen.",
        "",
    ]
    temporary = output / "summary.md.tmp"
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(output / "summary.md")
    _write_json(output / "report.json", report)


# Rebinding affects this private module instance, not the older control driver.
# Its unchanged source is included in the new policy's source manifest.
HELPERS.save_report = lambda output, report: save_report(output, report)
HELPERS.comparison = locked_interpretation


def finalize(output, report, anchors, unchanged, clock):
    if (
        len(report["cells"]) != 6
        or any(cell["status"] != "completed" for cell in report["cells"])
        or len(report["pairs"]) != 3
        or any(pair["status"] != "passed" for pair in report["pairs"])
    ):
        raise ValueError("All six cells and three observation/control pairs must pass.")
    return HELPERS.finalize(output, report, anchors, unchanged, clock)


def retain_incomplete(output, report, error, clock):
    return HELPERS.retain_incomplete(output, report, error, clock)


def verify_preflight(record, initial, sources, support, probe):
    if (
        record["format"] != policy.FORMAT
        or record["status"] != "verified"
        or record["mode"] != "options"
        or record["callback_calls"] != 0
        or record["source_sha256"] != sources
        or len(record["profiles"]) != 6
    ):
        raise ValueError("Invalid options-only trajectory preflight.")
    HELPERS.verify_snapshots(record, initial, probe)
    expected = {
        (cell["budget"]["seed"], cell["observed"]) for cell in policy.planned_cells()
    }
    seen, first = set(), None
    for profile in record["profiles"]:
        key = profile["python_seed"], profile["observed"]
        if type(key[0]) is not int or type(key[1]) is not bool:
            raise ValueError("Invalid preflight seed or observation flag.")
        if key not in expected or key in seen:
            raise ValueError("Missing or duplicate trajectory preflight profile.")
        seen.add(key)
        policy.verify_options(profile, key[0], key[1], BASE, support)
        current = policy.common_options(profile, support)
        if first is not None and current != first:
            raise ValueError("Unexpected native cross-profile option difference.")
        first = current


def inspect_backend(output, runtime, initial, sources, support, probe, remaining):
    documents, consumed = {}, {}
    for mode in ("options", "fixtures"):
        for name, source in policy.RUNTIME.items():
            path = runtime / name
            if path.is_symlink() or _sha256(path.read_bytes()) != sources[source]:
                raise ValueError("Runtime source changed before preflight consumption.")
        filename = mode + ".json"
        with (output / (filename + ".log")).open("w", encoding="utf-8") as log:
            result = launch(
                [
                    sys.executable,
                    str(ROOT / "scripts/run_python.py"),
                    str(runtime / "backend.py"),
                    "--mode",
                    mode,
                    "--output",
                    str(output / filename),
                ],
                stdout=log,
                remaining=min(remaining(), policy.WORKER_LIMIT_SECONDS),
            )
        if result.returncode:
            raise RuntimeError(f"Trajectory preflight failed; see {filename}.log.")
        consumed[filename] = (output / filename).read_bytes()
        documents[mode] = support.read_json(consumed[filename])
    options, fixtures = documents["options"], documents["fixtures"]
    verify_preflight(options, initial, sources, support, probe)
    HELPERS.verify_snapshots(fixtures, initial, probe)
    if (
        fixtures["format"] != policy.FORMAT
        or fixtures["status"] != "verified"
        or fixtures["mode"] != "fixtures"
        or fixtures["source_sha256"] != sources
        or fixtures["callback_calls"] != 0
        or len(fixtures["checks"]) != len(policy.FIXTURE_CHECKS)
        or any(
            set(check) != {"name", "status"} or check["status"] != "passed"
            for check in fixtures["checks"]
        )
        or {check["name"] for check in fixtures["checks"]} != set(policy.FIXTURE_CHECKS)
    ):
        raise ValueError("Incomplete passive-observer fixture preflight.")
    return options, consumed


def dispatch(runtime, cell, sources, frozen, output, remaining, unchanged):
    def run(command, *, stdout):
        unchanged()
        expected = [
            sys.executable,
            str(ROOT / "scripts/run_python.py"),
            str(ROOT / "scripts/run_symbolic_worker.py"),
        ]
        if len(command) != 4 or command[:3] != expected:
            raise ValueError("Unexpected trajectory worker command.")
        directory = Path(command[3])
        if directory.resolve() != output / cell["directory"]:
            raise ValueError("Unexpected trajectory worker directory.")
        request = BASE.load_support().read_json(
            (directory / "request.json").read_bytes()
        )
        if request != {"format": symbolic.FORMAT, "budget": cell["budget"]}:
            raise ValueError("Unexpected trajectory worker request.")
        _write_json(
            directory / "profile.json",
            {"format": policy.PROFILE_FORMAT, "observed": cell["observed"]},
        )
        _write_json(
            directory / "manifest.json",
            {
                "format": policy.FORMAT,
                "sources": sources,
                "runtime": {k: sources[v] for k, v in policy.RUNTIME.items()},
                "inputs": {
                    name: _sha256((directory / name).read_bytes())
                    for name in ("inputs.npz", "request.json", "profile.json")
                },
            },
        )
        policy.verify_manifest(directory, runtime)
        for name in ("inputs.npz", "request.json", "profile.json", "manifest.json"):
            path = directory / name
            frozen[path.relative_to(output).as_posix()] = _sha256(path.read_bytes())
        return launch(
            [*command[:2], str(runtime / "worker.py"), command[3]],
            stdout=stdout,
            remaining=min(remaining(), policy.WORKER_LIMIT_SECONDS),
        )

    return run


def worker_bytes(directory, support):
    for name in (*support.FILES, "checksums.json", "status.json", *EXTRA_FILES):
        if (directory / name).is_symlink():
            raise ValueError("Worker artifacts must not be symbolic links.")
    contents = support.source_bytes(directory)
    checksums = support.read_json(contents["checksums.json"])
    for name in EXTRA_FILES:
        contents[name] = (directory / name).read_bytes()
        if checksums.get(name) != _sha256(contents[name]):
            raise ValueError("Worker checksum mismatch: " + name)
    return contents


def verify_cell(
    directory,
    cell,
    arrays,
    support,
    probe,
    initial,
    tools,
    sources,
    preflight,
    *,
    check=lambda: None,
):
    check()
    contents = worker_bytes(directory, support)
    read = lambda name: support.read_json(contents[name])
    if read("request.json") != {
        "format": symbolic.FORMAT,
        "budget": cell["budget"],
    } or read("profile.json") != {
        "format": policy.PROFILE_FORMAT,
        "observed": cell["observed"],
    }:
        raise ValueError("Worker changed its request or profile.")
    with np.load(io.BytesIO(contents["inputs.npz"]), allow_pickle=False) as saved:
        if set(saved.files) != {"time_s", "observed"} or any(
            saved[key].dtype != np.float64
            or fingerprint(saved[key]) != fingerprint(arrays[key])
            for key in saved.files
        ):
            raise ValueError("Worker changed training roles or bits.")
    manifest = policy.verify_manifest(directory, directory.parent / "runtime")
    if manifest["sources"] != sources:
        raise ValueError("Worker consumed different sources.")
    for name in EXTRA_FILES:
        if (
            name.endswith(".jl")
            and _sha256(contents[name]) != sources["julia/src/" + name]
        ):
            raise ValueError("Worker consumed a changed native source.")
    metadata, first = read("metadata.json"), read("metadata_initial.json")
    if (
        metadata["phase"] != "success"
        or metadata["provenance"] != first["provenance"]
        or any(
            metadata[key] != initial["provenance"]
            for key in ("provenance", "worker_provenance")
        )
        or any(
            metadata[key] != initial["adapter_source_sha256"]
            for key in ("adapter_source_sha256", "worker_adapter_source_sha256")
        )
    ):
        raise ValueError("Worker provenance changed or worker incomplete.")
    control = support.verify_worker_control(
        directory, metadata, "Haswell", tools, probe
    )
    front = read("result.json")
    support.signature(front)
    if (
        front["evaluation_scope"] != "fitted_samples_only"
        or front["selection"] != "minimum_training_loss_then_complexity"
    ):
        raise ValueError("Changed original selection scope or policy.")
    parameters = read("pysr_parameters.json")
    expected = policy.profile_parameters(
        symbolic.SearchBudget(**cell["budget"]), cell["observed"]
    )
    if any(
        key not in parameters or parameters[key] != value
        for key, value in expected.items()
    ):
        raise ValueError("Wrong effective trajectory PySR parameters.")
    record, backend = read("verification.json"), read("backend_options.json")
    reference = next(
        p
        for p in preflight["profiles"]
        if p["observed"] is cell["observed"]
        and p["python_seed"] == cell["budget"]["seed"]
    )
    calls = front["callback_calls_during_fit"]
    if (
        record["format"] != policy.FORMAT
        or record["status"] != "verified"
        or record["observed"] is not cell["observed"]
        or record["iterations"] != 100
        or record["backend_options"] != backend
        or record["profile_sha256"] != _sha256(contents["profile.json"])
        or record["manifest_sha256"] != _sha256(contents["manifest.json"])
        or type(calls) is not int
        or calls <= 0
        or type(record["callback_calls_during_fit"]) is not int
        or record["callback_calls_during_fit"] != calls
        or type(record["callback_calls_total"]) is not int
        or record["callback_calls_total"] != calls + 1
    ):
        raise ValueError("Wrong native trajectory verification or callback accounting.")
    verified = policy.verify_options(
        record, cell["budget"]["seed"], cell["observed"], BASE, support
    )
    if any(
        type(front["rng"].get(key)) is not int or front["rng"][key] != value
        for key, value in (
            ("python_seed", cell["budget"]["seed"]),
            ("backend_seed", record["backend_seed"]),
        )
    ):
        raise ValueError("Wrong recorded trajectory RNG seed.")
    if support.backend_without_output(backend) != support.backend_without_output(
        reference["backend_options"]
    ) or any(
        record[key] != reference[key]
        for key in (
            "optimizer_settings",
            "plugins",
            "plugins_field",
            "baseline_plugins",
            "baseline_plugins_field",
            "expected_plugins_field",
        )
    ):
        raise ValueError("Actual backend differs from genuine native preflight.")
    observation_timing = record["observation_timing_seconds"]
    if (
        not isinstance(observation_timing, dict)
        or set(observation_timing) != {"hook", "units_after_fit"}
        or any(
            type(value) not in (int, float)
            or not math.isfinite(value)
            or value < 0
            or (not cell["observed"] and value != 0)
            for value in observation_timing.values()
        )
    ):
        raise ValueError("Invalid observation effort accounting.")
    analysis_started = time.perf_counter()
    selected, diagnoses = front["selected_index"], []
    for index, candidate in enumerate(front["candidates"]):
        check()
        _candidate(candidate, index, selected, arrays["time_s"], FS)
        training = BASE.verify_training_loss(candidate, arrays["observed"])
        diagnosis = diagnose_candidate(
            candidate, index, selected, arrays, "complexity_frequency"
        )
        diagnosis["training_verification"] = training
        diagnoses.append(diagnosis)
    if selected != symbolic.select_candidate(front["candidates"]):
        raise ValueError("Original selection contradicts its training rule.")
    hashes = {k: _sha256(v) for k, v in contents.items()}
    observation_path = directory / "observations.jsonl"
    observation = record["observation"]
    observation_analysis = None
    expected_events = cell["budget"]["niterations"] * cell["budget"]["populations"]
    if cell["observed"]:
        digest = read("checksums.json").get("observations.jsonl")
        units_digest = read("checksums.json").get("observation_units.json")
        if any(
            not isinstance(value, str) or len(value) != 64
            for value in (digest, units_digest)
        ):
            raise ValueError("Missing observation checksum.")
        observation_analysis = policy.verify_observations(
            observation_path,
            expected_events=expected_events,
            arrays=arrays,
            front=front,
            check=check,
            expected_sha256=digest,
            expected_record=observation,
            expected_units_sha256=units_digest,
        )
        observation = observation_analysis["observation"]
        hashes["observations.jsonl"] = digest
        hashes["observation_units.json"] = units_digest
    else:
        units_path = directory / "observation_units.json"
        if (
            observation_path.exists()
            or observation_path.is_symlink()
            or units_path.exists()
            or units_path.is_symlink()
            or observation
            != {
                "status": "disabled",
                "event_count": 0,
                "member_count": 0,
                "bytes_written": 0,
                "max_bytes": policy.MAX_OBSERVATION_BYTES,
                "units_bytes": 0,
                "total_bytes": 0,
                "expected_events": expected_events,
            }
        ):
            raise ValueError("Unexpected observations or counter in the control arm.")
    if worker_bytes(directory, support) != contents:
        raise ValueError("Consumed worker artifacts changed during diagnosis.")
    check()
    return {
        "selected_index": selected,
        "selection_role": "recorded_only; no reranking",
        "candidate_count": len(diagnoses),
        "candidates": diagnoses,
        "source_file_sha256": hashes,
        "blas_control": control,
        "rng": front["rng"],
        "timing_seconds": front["timing_seconds"],
        "callback_calls_during_fit": calls,
        "callback_calls_total": record["callback_calls_total"],
        "backend_evaluation_counter": front["backend_evaluation_counter"],
        "effective_parameters": parameters,
        "effective_backend_options": backend,
        "backend_policy_verification": verified,
        "native_verification": record,
        "observation": observation,
        "observation_analysis": observation_analysis,
        "observation_timing_seconds": observation_timing,
        "offline_analysis_seconds": time.perf_counter() - analysis_started,
    }


def verify_pair(output, first, second, support, check):
    if (
        first["budget"] != second["budget"]
        or first["observed"] is second["observed"]
        or first["status"] != "completed"
        or second["status"] != "completed"
    ):
        raise ValueError("A pair must contain complete matching off/on cells.")
    documents = []
    for cell in (first, second):
        check()
        path = output / cell["directory"] / "result.json"
        if path.is_symlink():
            raise ValueError("Paired fronts must not be symbolic links.")
        contents = path.read_bytes()
        if (
            _sha256(contents)
            != cell["diagnostics"]["source_file_sha256"]["result.json"]
        ):
            raise ValueError("Verified front changed before pair comparison.")
        documents.append(support.read_json(contents))
    comparison = policy.compare_pair(*documents)
    if (
        first["diagnostics"]["callback_calls_total"]
        != second["diagnostics"]["callback_calls_total"]
    ):
        raise ValueError("Paired total callback counts differ.")
    return {
        **comparison,
        "seed": first["budget"]["seed"],
        "cells": [first["number"], second["number"]],
    }


def copy_runtime(output, sources):
    runtime = output / "runtime"
    runtime.mkdir()
    hashes = {}
    for name, source in policy.RUNTIME.items():
        contents = (ROOT / source).read_bytes()
        if _sha256(contents) != sources[source]:
            raise ValueError("Source changed before runtime copy.")
        (runtime / name).write_bytes(contents)
        hashes[f"runtime/{name}"] = sources[source]
    return runtime, hashes


def run(archive, output, *, label):
    if not hasattr(signal, "setitimer") or not hasattr(signal, "pthread_sigmask"):
        raise RuntimeError(
            "Scientific trajectory runs require the Linux reference environment."
        )
    with WallTimeLimit(policy.LIMIT_SECONDS) as clock:
        return run_with_deadline(archive, output, label=label, clock=clock)


def run_with_deadline(archive, output, *, label, clock):
    archive, output = Path(archive).resolve(), Path(output).resolve()
    if (
        not label.strip()
        or output.exists()
        or ROOT.is_relative_to(output)
        or archive.is_relative_to(output)
        or any(
            output.is_relative_to(ROOT / name)
            for name in ("src", "scripts", "docs", "julia", ".git")
        )
    ):
        raise ValueError(
            "Use a machine label and new output outside sources and input."
        )
    support = BASE.load_support()
    probe = support.load_core_probe()
    initial = BASE.core_snapshot(probe)
    if initial["provenance"]["git"]["dirty"] is not False:
        raise ValueError("Scientific trajectory requires a clean, committed checkout.")
    original_archive, arrays = read_archive(archive)
    for values in arrays.values():
        values.flags.writeable = False
    fingerprints = {k: fingerprint(v) for k, v in arrays.items()}
    sources, tools = policy.source_hashes(), support.tool_hashes()
    output.mkdir(parents=True)
    files = {}
    report = {
        "format": policy.FORMAT,
        "status": "running",
        "label": label,
        "started_at_utc": _utc_now(),
        "scope": "adaptive development; observed return boundaries; no causal search history",
        "physical_identification": "not_assessed",
        "plan": {"commit": policy.PLAN_COMMIT, "sha256": policy.PLAN_SHA256},
        "configuration": {
            "truth": TRUTH,
            "curve_limits": CURVE_LIMITS,
            "parameter_limits": PARAMETER_LIMITS,
            "limit_seconds": policy.LIMIT_SECONDS,
            "worker_limit_seconds": policy.WORKER_LIMIT_SECONDS,
            "observation_byte_limit": policy.MAX_OBSERVATION_BYTES,
            "optimizer_iterations": 100,
            "optimizer_nrestarts": 2,
            "use_frequency": True,
            "use_frequency_in_tournament": True,
        },
        "input_fingerprints": fingerprints,
        "source_sha256": sources,
        "control_initial": initial,
        "cells": policy.planned_cells(),
        "pairs": [],
        "final_verification": "pending",
        "frozen_file_sha256": files,
        "historical_comparison": {
            "status": "not_assessed",
            "reason": "historical free-budget original archive not consumed; prior reported results remain separate",
        },
    }
    original = symbolic._run_worker

    def unchanged():
        clock.check()
        if (
            policy.source_hashes() != sources
            or support.tool_hashes() != tools
            or archive.read_bytes() != original_archive
            or any(fingerprint(v) != fingerprints[k] for k, v in arrays.items())
        ):
            raise ValueError("Sources or frozen trajectory input changed.")
        for name, digest in files.items():
            if checked_hash(output / name, clock.check) != digest:
                raise ValueError("Consumed or verified artifact changed: " + name)
        clock.check()

    try:
        save_report(output, report)
        runtime, runtime_hashes = copy_runtime(output, sources)
        files.update(runtime_hashes)
        (output / "plan.md").write_bytes((ROOT / policy.PLAN).read_bytes())
        np.savez(
            output / "training.npz",
            time_s=arrays["time_s"],
            observed=arrays["observed"],
        )
        np.savez(
            output / "diagnostic.npz",
            diagnostic_time_s=arrays["diagnostic_time_s"],
            diagnostic_truth=arrays["diagnostic_truth"],
        )
        for name in ("plan.md", "training.npz", "diagnostic.npz"):
            files[name] = _sha256((output / name).read_bytes())
        unchanged()
        preflight, consumed = inspect_backend(
            output, runtime, initial, sources, support, probe, clock.remaining
        )
        for name, contents in consumed.items():
            if (output / name).read_bytes() != contents:
                raise ValueError("Preflight artifact changed during verification.")
            files[name] = _sha256(contents)
        first_parameters = None
        for cell in report["cells"]:
            unchanged()
            cell.update(status="running", started_at_utc=_utc_now())
            save_report(output, report)
            symbolic._run_worker = dispatch(
                runtime, cell, sources, files, output, clock.remaining, unchanged
            )
            before = time.monotonic()
            print(
                f"Starting cell {cell['number']}/6: {cell['arm']} seed={cell['budget']['seed']}",
                flush=True,
            )
            worker = symbolic.run_search_arm(
                arrays["time_s"],
                arrays["observed"],
                covariance=None,
                output=output / cell["directory"],
                budget=symbolic.SearchBudget(**cell["budget"]),
            )
            worker_wall_seconds = time.monotonic() - before
            unchanged()
            if worker.status != "success":
                raise RuntimeError("Trajectory worker failed; inspect worker.log.")
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
                check=clock.check,
            )
            parameters = support.parameters_without_output(
                diagnosis["effective_parameters"]
            )
            parameters = {
                key: value for key, value in parameters.items() if key != "random_state"
            }
            # The observed profile's plugin argument has already been checked
            # absolutely above. Retain every other effective PySR parameter.
            parameters["plugins"] = None
            if first_parameters is not None and parameters != first_parameters:
                raise ValueError("Unplanned effective PySR cross-cell difference.")
            first_parameters = parameters
            diagnosis["worker_wall_seconds"] = worker_wall_seconds
            cell.update(
                status="completed", finished_at_utc=_utc_now(), diagnostics=diagnosis
            )
            for name, digest in diagnosis["source_file_sha256"].items():
                relative = f"{cell['directory']}/{name}"
                if relative in files and files[relative] != digest:
                    raise ValueError("Consumed input changed before verification.")
                files[relative] = digest
            unchanged()
            if cell["number"] % 2 == 0:
                first = report["cells"][cell["number"] - 2]
                report["pairs"].append(
                    verify_pair(output, first, cell, support, clock.check)
                )
                unchanged()
            save_report(output, report)
        report["control_final"] = BASE.core_snapshot(probe)
        if any(
            report["control_final"][key] != initial[key]
            for key in ("provenance", "adapter_source_sha256")
        ):
            raise ValueError("Final parent provenance changed.")
        unchanged()
        finalize(output, report, files, unchanged, clock)
    except BaseException as error:
        report.update(status="incomplete", error=f"{type(error).__name__}: {error}")
        for cell in report["cells"]:
            if cell["status"] == "running":
                cell.update(
                    status="aborted"
                    if isinstance(
                        error,
                        (
                            KeyboardInterrupt,
                            SystemExit,
                            TimeoutError,
                            subprocess.TimeoutExpired,
                        ),
                    )
                    else "failed",
                    error=report["error"],
                )
        retain_incomplete(output, report, error, clock)
        raise
    finally:
        symbolic._run_worker = original
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    def cancel(signum, frame):
        raise KeyboardInterrupt(f"Trajectory interrupted by signal {signum}.")

    previous = signal.signal(signal.SIGTERM, cancel)
    try:
        run(args.archive, args.output, label=args.label)
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    main()
