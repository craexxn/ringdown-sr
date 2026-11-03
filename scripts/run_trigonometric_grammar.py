"""Run exactly six frozen free searches, preserving fail-closed partial states."""

import argparse
import hashlib
import importlib.util
import io
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import ExitStack
from pathlib import Path

import numpy as np

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
from ringdown_sr.trigonometric_grammar import (
    CONDITIONS,
    FORMAT,
    LIMIT_SECONDS,
    PLAN,
    PLAN_COMMIT,
    PLAN_SHA256,
    PROFILE_FORMAT,
    RUNTIME,
    WORKER_LIMIT_SECONDS,
    common_options,
    comparison,
    expected_grammar_cases,
    planned_cells,
    profile_parameters,
    source_hashes,
    verify_manifest,
    verify_options,
    verify_tree_grammar,
)

ROOT = symbolic.ROOT


def load_base():
    spec = importlib.util.spec_from_file_location(
        "grammar_base", ROOT / "scripts/run_noiseless_control.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base()
EXTRA_FILES = (
    "profile.json",
    "manifest.json",
    "verification.json",
    "blas_control.json",
    "RingdownSRLoss.jl",
    "RingdownSRSearch.jl",
    "RepresentationProfiles.jl",
    "FreeOptimizerBudget.jl",
    "TrigonometricGrammar.jl",
)


class WallTimeLimit:
    """Bound child waits and interrupt blocking parent work on the reference OS."""

    def __init__(self, seconds):
        self.started = time.monotonic()
        self.seconds = seconds
        self.active = False

    def check(self):
        if self.remaining() <= 0:
            raise TimeoutError("Grammar comparison reached its wall-time limit.")

    def remaining(self):
        return self.seconds - (time.monotonic() - self.started)

    def __enter__(self):
        if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
            raise RuntimeError("An existing parent wall timer must not be replaced.")
        self.previous = signal.getsignal(signal.SIGALRM)

        def expire(signum, frame):
            raise TimeoutError("Grammar comparison reached its wall-time limit.")

        signal.signal(signal.SIGALRM, expire)
        self.active = True
        try:
            self.check()
            signal.setitimer(signal.ITIMER_REAL, self.remaining())
        except BaseException:
            self.cancel()
            raise
        return self

    def cancel(self):
        if self.active:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, self.previous)
            self.active = False

    def __exit__(self, *args):
        self.cancel()


def checked_hash(path, check):
    check()
    if path.is_symlink():
        raise ValueError("Symbolic links are not valid control artifacts.")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            check()
    check()
    return digest.hexdigest()


def artifact_hashes(output, anchors, check):
    """Check the bytes consumed for the final manifest against original anchors."""
    hashes = {}
    check()
    for path in output.rglob("*"):
        check()
        if path.is_symlink():
            raise ValueError("Symbolic links are not valid control artifacts.")
        name = path.relative_to(output).as_posix()
        if path.is_file() and name != "checksums.json":
            hashes[name] = checked_hash(path, check)
            if name in anchors and hashes[name] != anchors[name]:
                raise ValueError("A consumed or verified artifact changed: " + name)
    check()
    if not anchors.keys() <= hashes.keys():
        raise ValueError("A consumed or verified artifact is missing.")
    return hashes


def launch(command, *, stdout, remaining):
    if remaining <= 0:
        raise TimeoutError("Grammar comparison reached its wall-time limit.")
    process = subprocess.Popen(
        command, stdout=stdout, stderr=subprocess.STDOUT, start_new_session=True
    )
    try:
        code = process.wait(timeout=remaining)
        if code:
            symbolic._stop_worker(process)
        return subprocess.CompletedProcess(command, code)
    except BaseException:
        symbolic._stop_worker(process)
        raise


def verify_preflight(record, initial, sources, support, probe):
    if (
        record["format"] != FORMAT
        or record["status"] != "verified"
        or record["mode"] != "options"
        or record["callback_calls"] != 0
        or record["source_sha256"] != sources
        or len(record["profiles"]) != 6
    ):
        raise ValueError("Invalid options-only grammar preflight.")
    verify_snapshots(record, initial, probe)
    expected = {(c["condition"], c["budget"]["seed"]) for c in planned_cells()}
    seen, first = set(), None
    for profile in record["profiles"]:
        key = profile["condition"], profile["python_seed"]
        if key not in expected or key in seen:
            raise ValueError("Missing or duplicate grammar preflight cell.")
        seen.add(key)
        verify_options(profile, key[1], key[0], BASE, support)
        current = common_options(profile, support)
        if first is not None and current != first:
            raise ValueError("Unplanned native cross-grammar option difference.")
        first = current


def verify_snapshots(record, initial, probe):
    for snapshot in (record["initial"], record["final"]):
        if any(
            snapshot[key] != initial[key]
            for key in ("provenance", "adapter_source_sha256")
        ):
            raise ValueError("Preflight source provenance changed.")
        if snapshot["blas_control"] != probe.verify_blas_control(
            snapshot["environment"], "Haswell", require_julia=True
        ):
            raise ValueError("Preflight actual BLAS snapshot disagrees.")


def inspect_backend(output, runtime, initial, sources, support, probe, remaining):
    documents, consumed = {}, {}
    for mode in ("options", "references"):
        for name, source in RUNTIME.items():
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
                remaining=remaining(),
            )
        if result.returncode:
            raise RuntimeError(f"Budget preflight failed; see {filename}.log.")
        consumed[filename] = (output / filename).read_bytes()
        documents[mode] = support.read_json(consumed[filename])
    options, references = documents["options"], documents["references"]
    verify_preflight(options, initial, sources, support, probe)
    verify_snapshots(references, initial, probe)
    if (
        references["format"] != FORMAT
        or references["status"] != "verified"
        or references["mode"] != "references"
        or references["source_sha256"] != sources
        or len(references["cases"]) != 6
        or references.get("grammar_cases") != expected_grammar_cases()
    ):
        raise ValueError("Incomplete native fixed-reference preflight.")
    if {(c["condition"], c["frequency_hz"]) for c in references["cases"]} != {
        (i, f) for i in CONDITIONS for f in (250, 4346, 33018)
    }:
        raise ValueError("Wrong native fixed-reference coverage.")
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
            raise ValueError("Unexpected grammar worker command.")
        directory = Path(command[3])
        if directory.resolve() != output / cell["directory"]:
            raise ValueError("Unexpected grammar worker directory.")
        request = BASE.load_support().read_json(
            (directory / "request.json").read_bytes()
        )
        if request != {"format": symbolic.FORMAT, "budget": cell["budget"]}:
            raise ValueError("Unexpected grammar worker request.")
        _write_json(
            directory / "profile.json",
            {"format": PROFILE_FORMAT, "condition": cell["condition"]},
        )
        _write_json(
            directory / "manifest.json",
            {
                "format": FORMAT,
                "sources": sources,
                "runtime": {k: sources[v] for k, v in RUNTIME.items()},
                "inputs": {
                    name: _sha256((directory / name).read_bytes())
                    for name in ("inputs.npz", "request.json", "profile.json")
                },
            },
        )
        verify_manifest(directory, runtime)
        for name in ("inputs.npz", "request.json", "profile.json", "manifest.json"):
            path = directory / name
            frozen[path.relative_to(output).as_posix()] = _sha256(path.read_bytes())
        return launch(
            [*command[:2], str(runtime / "worker.py"), command[3]],
            stdout=stdout,
            remaining=min(WORKER_LIMIT_SECONDS, remaining()),
        )

    return run


def worker_bytes(directory, support):
    contents = support.source_bytes(directory)
    checksums = support.read_json(contents["checksums.json"])
    for name in EXTRA_FILES:
        path = directory / name
        if path.is_symlink():
            raise ValueError("Worker artifacts must not be symbolic links.")
        contents[name] = path.read_bytes()
        if checksums.get(name) != _sha256(contents[name]):
            raise ValueError("Worker checksum mismatch: " + name)
    return contents


def verify_cell(
    directory, cell, arrays, support, probe, initial, tools, sources, preflight
):
    contents = worker_bytes(directory, support)
    read = lambda name: support.read_json(contents[name])
    if read("request.json") != {
        "format": symbolic.FORMAT,
        "budget": cell["budget"],
    } or read("profile.json") != {
        "format": PROFILE_FORMAT,
        "condition": cell["condition"],
    }:
        raise ValueError("Worker changed its request or profile.")
    with np.load(io.BytesIO(contents["inputs.npz"]), allow_pickle=False) as saved:
        if set(saved.files) != {"time_s", "observed"} or any(
            saved[key].dtype != np.float64
            or fingerprint(saved[key]) != fingerprint(arrays[key])
            for key in saved.files
        ):
            raise ValueError("Worker changed the training input roles or bits.")
    manifest = verify_manifest(directory, directory.parent / "runtime")
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
    expected = profile_parameters(
        symbolic.SearchBudget(**cell["budget"]), cell["condition"]
    )
    if any(
        key not in parameters or parameters[key] != value
        for key, value in expected.items()
    ):
        raise ValueError("Wrong effective grammar PySR parameters.")
    record = read("verification.json")
    backend = read("backend_options.json")
    reference = next(
        p
        for p in preflight["profiles"]
        if p["condition"] == cell["condition"]
        and p["python_seed"] == cell["budget"]["seed"]
    )
    calls = front["callback_calls_during_fit"]
    if (
        record["format"] != FORMAT
        or record["status"] != "verified"
        or record["condition"] != cell["condition"]
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
        raise ValueError("Wrong native grammar verification or callback accounting.")
    policy = verify_options(
        record, cell["budget"]["seed"], cell["condition"], BASE, support
    )
    if any(
        type(front["rng"].get(key)) is not int or front["rng"][key] != value
        for key, value in (
            ("python_seed", cell["budget"]["seed"]),
            ("backend_seed", record["backend_seed"]),
        )
    ):
        raise ValueError("Wrong recorded free-search RNG seed.")
    if support.backend_without_output(backend) != support.backend_without_output(
        reference["backend_options"]
    ) or any(
        record[key] != reference[key]
        for key in ("optimizer_settings", "plugins", "plugins_field")
    ):
        raise ValueError("Actual backend differs from the genuine native preflight.")
    selected = front["selected_index"]
    diagnoses = []
    for index, candidate in enumerate(front["candidates"]):
        _candidate(candidate, index, selected, arrays["time_s"], FS)
        verify_tree_grammar(candidate["tree"], cell["condition"])
        checked = BASE.verify_training_loss(candidate, arrays["observed"])
        diagnosis = diagnose_candidate(
            candidate, index, selected, arrays, "complexity_frequency"
        )
        diagnosis["training_verification"] = checked
        diagnoses.append(diagnosis)
    if selected != symbolic.select_candidate(front["candidates"]):
        raise ValueError("The original selection contradicts its training rule.")
    if worker_bytes(directory, support) != contents:
        raise ValueError("Consumed worker artifacts changed during diagnosis.")
    return {
        "selected_index": selected,
        "selection_role": "recorded_only; no reranking",
        "candidate_count": len(diagnoses),
        "candidates": diagnoses,
        "source_file_sha256": {k: _sha256(v) for k, v in contents.items()},
        "blas_control": control,
        "rng": front["rng"],
        "timing_seconds": front["timing_seconds"],
        "callback_calls_during_fit": calls,
        "callback_calls_total": record["callback_calls_total"],
        "backend_evaluation_counter": front["backend_evaluation_counter"],
        "effective_parameters": parameters,
        "effective_backend_options": backend,
        "backend_policy_verification": policy,
        "native_verification": record,
    }


def save_report(output, report):
    report.update(
        comparison(
            report["cells"],
            final_verified=report["final_verification"] == "passed"
            and report["status"] == "completed",
        )
    )
    lines = [
        "# Trigonometrischer Grammatikvergleich",
        "",
        f"Serienstatus: `{report['status']}`, Abschlussverifikation: `{report['final_verification']}`.",
        "",
        "Bekannter Entwicklungsfall; beide Häufigkeitsschalter an; physikalische Identifikation `not_assessed`.",
        "",
        "| Zelle | Seed | Grammatik | Status | Auswahlindex | Kurve | Struktur | Parameter |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for cell in report["cells"]:
        diagnosis = cell.get("diagnostics")
        selected = (
            diagnosis["candidates"][diagnosis["selected_index"]] if diagnosis else None
        )
        values = [
            cell["number"],
            cell["budget"]["seed"],
            cell["condition"],
            cell["status"],
            diagnosis["selected_index"] if diagnosis else "nicht verfügbar",
            selected["curve_marker"] if selected else "nicht verfügbar",
            selected["search_analysis"]["structure"]["structure_status"]
            if selected
            else "nicht verfügbar",
            selected["parameter_match"]["status"] if selected else "nicht verfügbar",
        ]
        lines.append("| " + " | ".join(map(str, values)) + " |")
    lines += [
        "",
        "Gruppenstatistiken und Paardifferenzen sind bis zu sechs verifizierten Zellen und bestandener Abschlussprüfung gesperrt.",
        "",
    ]
    if report["comparison"] is not None:
        value = report["comparison"]
        labels = {
            "more_successes": "Mehr erfolgreiche Originalauswahlen unter A",
            "fewer_successes": "Weniger erfolgreiche Originalauswahlen unter A",
            "no_successes": "Keine erfolgreiche Originalauswahl unter beiden Grammatiken",
            "equal_successes": "Kein Mehrerfolg am primären Zählendpunkt",
        }
        lines += [
            f"C_K={value['C_K']}/3, C_A={value['C_A']}/3: {labels[value['outcome']]}. Keine allgemeine Überlegenheit ableiten.",
            "",
            "| Seed | Erfolg K | Erfolg A |",
            "| --- | --- | --- |",
        ]
        lines += [
            f"| {p['seed']} | {p['success_K']} | {p['success_A']} |"
            for p in report["pair_differences"]
        ]
        lines += [
            "",
            "Struktur-/Parameterunterstützung betrifft ausschließlich dieselbe erfolgreiche Originalauswahl. Gute nicht ausgewählte Frontkandidaten bleiben separat.",
        ]
    lines += [
        "",
        "Vollständige Fronten, Fehler, endliche Nenner, Status, Aufwand und Differenzen stehen in report.json. Das Achtelraster behält den Alias-Blindfleck bei 8·fs = 32768 Hz.",
        "",
    ]
    temporary = output / "summary.md.tmp"
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(output / "summary.md")
    _write_json(output / "report.json", report)


def finalize(output, report, anchors, unchanged, clock):
    """Stage the complete package; publish the positive report as the last commit."""
    observed = artifact_hashes(output, anchors, clock.check)
    anchors.update(
        (name, digest)
        for name, digest in observed.items()
        if name not in {"report.json", "summary.md"}
    )
    report.update(
        status="completed",
        final_verification="passed",
        finished_at_utc=_utc_now(),
        wall_seconds=time.monotonic() - clock.started,
    )
    with tempfile.TemporaryDirectory(
        prefix=f".{output.name}-finalizing-", dir=output.parent
    ) as temporary:
        stage = Path(temporary)
        save_report(stage, report)
        clock.check()
        staged = {
            name: checked_hash(stage / name, clock.check)
            for name in ("report.json", "summary.md")
        }
        hashes = artifact_hashes(output, anchors, clock.check)
        hashes.update(staged)
        _write_json(stage / "checksums.json", hashes)
        manifest_hash = checked_hash(stage / "checksums.json", clock.check)
        unchanged()
        for name in ("summary.md", "checksums.json"):
            expected = manifest_hash if name == "checksums.json" else staged[name]
            if checked_hash(stage / name, clock.check) != expected:
                raise ValueError("Staged final artifact changed: " + name)
            (stage / name).replace(output / name)
            clock.check()
        report_bytes = (stage / "report.json").read_bytes()
        if _sha256(report_bytes) != staged["report.json"]:
            raise ValueError("Staged positive report changed.")
    # Stage cleanup is part of finalization, before the public commit point.
    clock.check()
    pending = output / "report.json.tmp"
    pending.write_bytes(report_bytes)
    # A manifest must never bless new bytes in place of consumed artifacts.
    final_hashes = artifact_hashes(output, anchors, clock.check)
    if final_hashes.pop("report.json.tmp") != staged["report.json"]:
        raise ValueError("Pending positive report changed.")
    final_hashes["report.json"] = staged["report.json"]
    if (
        final_hashes != hashes
        or checked_hash(output / "checksums.json", clock.check) != manifest_hash
    ):
        raise ValueError("Final package changed during publication.")
    unchanged()
    if checked_hash(pending, clock.check) != staged["report.json"]:
        raise ValueError("Pending positive report changed.")
    pending.replace(output / "report.json")
    clock.check()
    clock.cancel()


def retain_incomplete(output, report, error, clock):
    """Revoke public success artifacts before attempting best-effort abort output."""
    previous_mask = signal.pthread_sigmask(
        signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM}
    )
    with ExitStack() as signals:
        # Restore handlers before unmasking pending cancellations. Deferring
        # handlers also cover process signals received through another thread.
        signals.callback(signal.pthread_sigmask, signal.SIG_SETMASK, previous_mask)
        received = []

        def defer(signum, frame):
            received.append(signum)

        for signum in (signal.SIGINT, signal.SIGTERM):
            previous = signal.signal(signum, defer)
            signals.callback(signal.signal, signum, previous)
        clock.cancel()
        report.update(
            status="incomplete",
            final_verification="failed",
            final_verification_error=f"{type(error).__name__}: {error}",
            finished_at_utc=_utc_now(),
            wall_seconds=time.monotonic() - clock.started,
            abort_cleanup_errors=[],
            abort_signals=received,
        )
        report.update(comparison(report["cells"], final_verified=False))

        def attempt(operation, action):
            try:
                action()
            except BaseException as cleanup_error:  # noqa: BLE001 -- Each revocation must survive another failure or interruption.
                report["abort_cleanup_errors"].append(
                    {
                        "operation": operation,
                        "error": f"{type(cleanup_error).__name__}: {cleanup_error}",
                    }
                )
                return False
            return True

        failed = []
        for name in (
            "checksums.json",
            "report.json",
            "summary.md",
            "report.json.tmp",
            "summary.md.tmp",
            "checksums.json.tmp",
        ):
            path = output / name
            if not attempt("unlink " + name, lambda p=path: p.unlink(missing_ok=True)):
                failed.append(path)
        # Retry only failed removals once; never rerun a worker or verification.
        for path in failed:
            attempt(
                "unlink retry " + path.name, lambda p=path: p.unlink(missing_ok=True)
            )
        try:
            save_report(output, report)
        except BaseException as persistence_error:  # noqa: BLE001 -- Never let a failed summary prevent the locked machine report.
            report["abort_persistence_error"] = (
                f"{type(persistence_error).__name__}: {persistence_error}"
            )
            if not attempt(
                "write locked report",
                lambda: _write_json(output / "report.json", report),
            ):
                attempt(
                    "remove unpersisted report",
                    lambda: (output / "report.json").unlink(missing_ok=True),
                )


def common_parameters(parameters):
    return {
        k: v
        for k, v in parameters.items()
        if k not in {"random_state", "nested_constraints"}
    }


def run(archive, output, *, label):
    with WallTimeLimit(LIMIT_SECONDS) as clock:
        return run_with_deadline(archive, output, label=label, clock=clock)


def run_with_deadline(archive, output, *, label, clock):
    archive, output = Path(archive).resolve(), Path(output).resolve()
    if (
        not label.strip()
        or output.exists()
        or ROOT.is_relative_to(output)
        or any(
            output.is_relative_to(ROOT / name)
            for name in ("src", "scripts", "docs", "julia", ".git")
        )
    ):
        raise ValueError(
            "Use a machine label and a new output directory outside sources."
        )
    support = BASE.load_support()
    probe = support.load_core_probe()
    initial = BASE.core_snapshot(probe)
    if initial["provenance"]["git"]["dirty"] is not False:
        raise ValueError("Scientific comparison requires a clean, committed checkout.")
    original_archive, arrays = read_archive(archive)
    for values in arrays.values():
        values.flags.writeable = False
    fingerprints = {k: fingerprint(v) for k, v in arrays.items()}
    sources, tools = source_hashes(), support.tool_hashes()
    output.mkdir(parents=True)
    files = {}
    report = {
        "format": FORMAT,
        "status": "running",
        "label": label,
        "started_at_utc": _utc_now(),
        "scope": "adaptive development; one known noiseless signal; no general validation",
        "physical_identification": "not_assessed",
        "plan": {"commit": PLAN_COMMIT, "sha256": PLAN_SHA256},
        "configuration": {
            "truth": TRUTH,
            "curve_limits": CURVE_LIMITS,
            "parameter_limits": PARAMETER_LIMITS,
            "limit_seconds": LIMIT_SECONDS,
            "worker_limit_seconds": WORKER_LIMIT_SECONDS,
            "optimizer_iterations": 100,
            "use_frequency": True,
            "use_frequency_in_tournament": True,
        },
        "input_fingerprints": fingerprints,
        "source_sha256": sources,
        "control_initial": initial,
        "cells": planned_cells(),
        "final_verification": "pending",
        "frozen_file_sha256": files,
    }
    original = symbolic._run_worker

    def remaining():
        return clock.remaining()

    def unchanged():
        clock.check()
        if (
            source_hashes() != sources
            or support.tool_hashes() != tools
            or archive.read_bytes() != original_archive
            or any(fingerprint(v) != fingerprints[k] for k, v in arrays.items())
        ):
            raise ValueError("Sources or frozen scientific input changed.")
        clock.check()
        for name, digest in files.items():
            path = output / name
            if checked_hash(path, clock.check) != digest:
                raise ValueError("A consumed or verified artifact changed: " + name)
        clock.check()

    try:
        save_report(output, report)
        runtime = output / "runtime"
        runtime.mkdir()
        for name, source in RUNTIME.items():
            contents = (ROOT / source).read_bytes()
            if _sha256(contents) != sources[source]:
                raise ValueError("Source changed before runtime copy.")
            (runtime / name).write_bytes(contents)
            files[f"runtime/{name}"] = sources[source]
        (output / "plan.md").write_bytes((ROOT / PLAN).read_bytes())
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
        for path in [
            output / "plan.md",
            output / "training.npz",
            output / "diagnostic.npz",
        ]:
            files[path.relative_to(output).as_posix()] = _sha256(path.read_bytes())
        unchanged()
        preflight, consumed = inspect_backend(
            output, runtime, initial, sources, support, probe, remaining
        )
        for name, contents in consumed.items():
            if (output / name).read_bytes() != contents:
                raise ValueError("Preflight artifact changed during verification.")
            files[name] = _sha256(contents)
        first_policy = None
        for cell in report["cells"]:
            unchanged()
            cell.update(status="running", started_at_utc=_utc_now())
            save_report(output, report)
            symbolic._run_worker = dispatch(
                runtime, cell, sources, files, output, remaining, unchanged
            )
            before = time.monotonic()
            print(
                f"Starting cell {cell['number']}/{len(report['cells'])}: "
                f"{cell['arm']} seed={cell['budget']['seed']} "
                f"niterations={cell['budget']['niterations']}",
                flush=True,
            )
            worker = symbolic.run_search_arm(
                arrays["time_s"],
                arrays["observed"],
                covariance=None,
                output=output / cell["directory"],
                budget=symbolic.SearchBudget(**cell["budget"]),
            )
            unchanged()
            if worker.status != "success":
                raise RuntimeError("Grammar worker failed; see worker.log.")
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
            parameters = support.parameters_without_output(
                diagnosis["effective_parameters"]
            )
            common = common_parameters(parameters)
            if first_policy is not None and first_policy != common:
                raise ValueError("Unplanned effective PySR cross-cell difference.")
            first_policy = common
            diagnosis["worker_wall_seconds"] = time.monotonic() - before
            cell.update(
                status="completed", finished_at_utc=_utc_now(), diagnostics=diagnosis
            )
            for name, digest in diagnosis["source_file_sha256"].items():
                relative = f"{cell['directory']}/{name}"
                if relative in files and files[relative] != digest:
                    raise ValueError("Consumed input changed before verification.")
                files[relative] = digest
            unchanged()
            save_report(output, report)
        final = BASE.core_snapshot(probe)
        report["control_final"] = final
        if any(
            final[key] != initial[key]
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
        raise KeyboardInterrupt(f"Grammar comparison interrupted by signal {signum}.")

    previous = signal.signal(signal.SIGTERM, cancel)
    try:
        run(args.archive, args.output, label=args.label)
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    main()
