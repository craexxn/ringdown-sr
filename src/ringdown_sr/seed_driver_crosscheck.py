"""Bound two historical worker crossovers without changing their search code."""

import copy
import io
import json
import os
import platform
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from contextlib import ExitStack
from pathlib import Path, PurePosixPath

import numpy as np

from . import transfer_check
from .pilot import _json_bytes, _provenance, _sha256, _utc_now, _write_json
from .search_duration import load_module
from .symbolic import ROOT, _stop_worker

FORMAT = "ringdown-sr-seed-driver-crosscheck-1"
PLAN = "docs/seed_driver_crosscheck_plan.md"
PLAN_COMMIT = "be6fc1bd2339df5b429684dfce8e992073d88506"
PLAN_SHA256 = "e6e2df830dd2e4254d60bd73a5b9e34678377c9bc1e6a2f81830592e4f85b15e"
BRIDGE = "scripts/seed_driver_crosscheck_bridge.py"
LIMIT_SECONDS = 3600
WORKER_LIMIT_SECONDS = 900
HISTORIES = {
    "outer": {
        "commit": "5215c5e1c93f220a3f7ea59b1c37580d2f2b5ea4",
        "archive_sha256": "ac7e841b79042e216d6aacae2961ffb8395f298bbcc7ecc11f1092c90b3deb40",
        "prefix": "outer-ladder-manjaro-001",
        "format": "ringdown-sr-outer-search-ladder-1",
        "reference_cell": 2,
        "reference_seed": 20261201,
        "count": 20,
        "curve": "within_tolerance",
    },
    "transfer": {
        "commit": "bc4025d13b4954dee779341026d282430521686a",
        "archive_sha256": "e363fe1be629973a460fc6e2188bf680c21b2c5519d331bc7e257968dcaaa139",
        "prefix": "transfer-manjaro-001",
        "format": "ringdown-sr-transfer-check-1",
        "reference_cell": 1,
        "reference_seed": 20261210,
        "count": 18,
        "curve": "outside_tolerance",
    },
}
CASES = (
    {"number": 1, "seed": 20261201, "reference": "outer", "target": "transfer"},
    {"number": 2, "seed": 20261210, "reference": "transfer", "target": "outer"},
)
SOURCE_FILES = (
    PLAN,
    BRIDGE,
    "src/ringdown_sr/seed_driver_crosscheck.py",
    "scripts/run_seed_driver_crosscheck.py",
    "scripts/check_seed_driver_crosscheck.py",
)


def read_json(contents):
    """Reject duplicate keys and non-finite JSON tokens before using evidence."""

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON field: " + key)
            result[key] = value
        return result

    def reject(value):
        raise ValueError("Non-finite JSON token: " + value)

    return json.loads(contents, object_pairs_hook=pairs, parse_constant=reject)


def git(*arguments, root=ROOT):
    return subprocess.check_output(["git", *arguments], cwd=root, timeout=30)


def source_hashes():
    hashes = transfer_check.source_hashes()
    hashes.update({name: _sha256((ROOT / name).read_bytes()) for name in SOURCE_FILES})
    if (
        hashes[PLAN] != PLAN_SHA256
        or _sha256(git("show", f"{PLAN_COMMIT}:{PLAN}")) != PLAN_SHA256
    ):
        raise ValueError("Missing or changed frozen crossover plan history.")
    return hashes


def safe_name(name):
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or str(path) != name:
        raise ValueError("Invalid artifact path: " + name)
    return path


def archive_files(contents, prefix):
    """Read regular files only, with bounded sizes; never execute archive code."""
    files, seen, total = {}, set(), 0
    with tarfile.open(fileobj=io.BytesIO(contents), mode="r:gz") as archive:
        for member in archive:
            name = member.name.rstrip("/") if member.isdir() else member.name
            path = safe_name(name)
            if path.parts[0] != prefix or name in seen:
                raise ValueError("Wrong archive root or duplicate member.")
            seen.add(name)
            if member.isdir():
                continue
            if not member.isfile() or member.size > 64 * 1024**2:
                raise ValueError("Unsupported or oversized archive member.")
            total += member.size
            if total > 256 * 1024**2 or len(seen) > 10000:
                raise ValueError("Oversized reference archive.")
            relative = str(path.relative_to(prefix))
            safe_name(relative)
            files[relative] = archive.extractfile(member).read()
    expected = read_json(files["checksums.json"])
    actual = {
        name: _sha256(value)
        for name, value in files.items()
        if name != "checksums.json"
    }
    if expected != actual:
        raise ValueError("Reference archive manifest is incomplete or inconsistent.")
    return files


def anchor_arrays():
    _, arrays = transfer_check.read_inputs(ROOT / transfer_check.INPUT)
    return transfer_check.arrays_for_cell(arrays, {"signal": "anchor"})


def reference_arrays(files, kind):
    arrays = {}
    for name in ("training.npz", "diagnostic.npz"):
        with np.load(io.BytesIO(files[name]), allow_pickle=False) as saved:
            arrays.update({key: saved[key].copy() for key in saved.files})
    if kind == "transfer":
        arrays["observed"] = arrays["observed"][0]
        arrays["diagnostic_truth"] = arrays["diagnostic_truth"][0]
    expected = anchor_arrays()
    if set(arrays) != set(expected) or any(
        arrays[key].dtype != np.float64
        or arrays[key].shape != expected[key].shape
        or arrays[key].tobytes() != expected[key].tobytes()
        for key in expected
    ):
        raise ValueError("Historical anchor data roles or Float64 bits changed.")
    return arrays


def read_reference(path, kind):
    spec = HISTORIES[kind]
    contents = Path(path).read_bytes()
    if _sha256(contents) != spec["archive_sha256"]:
        raise ValueError("Wrong original reference archive: " + kind)
    files = archive_files(contents, spec["prefix"])
    report = read_json(files["report.json"])
    provenance = report["control_initial"]["provenance"]
    if (
        report["format"] != spec["format"]
        or report["status"] != "completed"
        or report["final_verification"] != "passed"
        or len(report["cells"]) != spec["count"]
        or provenance["git"]
        != {"available": True, "changes": [], "commit": spec["commit"], "dirty": False}
        or report["control_final"]["provenance"] != provenance
    ):
        raise ValueError("Incomplete or wrong historical reference provenance.")
    for name, digest in report["frozen_file_sha256"].items():
        if _sha256(files[name]) != digest:
            raise ValueError("Changed historical consumption anchor.")
    for name, digest in report["source_sha256"].items():
        safe_name(name)
        if _sha256(git("show", f"{spec['commit']}:{name}")) != digest:
            raise ValueError("Historical source does not match Git: " + name)
    cell = report["cells"][spec["reference_cell"] - 1]
    if (
        cell["number"] != spec["reference_cell"]
        or cell["directory"] != f"cell-{spec['reference_cell']:02d}"
        or cell["budget"]["seed"] != spec["reference_seed"]
        or cell["budget"]["niterations"] != 500
        or cell["condition"] != "local_300_5"
        or cell["grammar"] != "unrestricted"
        or cell["status"] != "completed"
        or (kind == "transfer" and cell["signal"] != "anchor")
    ):
        raise ValueError("Wrong selected historical reference cell.")
    chosen = cell["diagnostics"]["candidates"][cell["diagnostics"]["selected_index"]]
    if chosen["curve_marker"] != spec["curve"]:
        raise ValueError("Historical reference outcome differs from the frozen plan.")
    reference_arrays(files, kind)
    return contents, files


def environment_key(environment):
    """Compare scientific runtime metadata while ignoring pool paths and ordering."""
    result = copy.deepcopy(environment)
    libraries = result["numerical_libraries"]
    libraries.pop("snapshot", None)
    pools = libraries["threadpools"]["details"]
    for pool in pools:
        pool.pop("filepath", None)
    libraries["threadpools"]["details"] = sorted(pools, key=lambda x: _json_bytes(x))
    return result


def comparison(reference, fresh):
    """Keep a valid mismatch informative; never confuse matching markers with fronts."""
    keys = ("signature", "parameters", "backend_options", "callback_calls_during_fit")
    matches = {name: reference[name] == fresh[name] for name in keys}
    return {
        "matches": matches,
        "all_search_features_equal": all(matches.values()),
        "reference_markers": reference["markers"],
        "fresh_markers": fresh["markers"],
        "markers_equal": reference["markers"] == fresh["markers"],
        "reference_worker_wall_seconds": reference["worker_wall_seconds"],
        "fresh_worker_wall_seconds": fresh["worker_wall_seconds"],
    }


def hashes(directory):
    result = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlink in crossover artifacts.")
        if path.is_file() and path.relative_to(directory).as_posix() not in (
            "crosscheck_report.json",
            "crosscheck_summary.md",
            "crosscheck_checksums.json",
        ):
            result[path.relative_to(directory).as_posix()] = _sha256(path.read_bytes())
    return result


def save_report(output, report):
    complete = report["status"] == "completed" and len(report["comparisons"]) == 2
    report["outcome"] = (
        "both_crossovers_reproduced"
        if complete
        and all(c["all_search_features_equal"] for c in report["comparisons"])
        else "valid_crossovers_differ"
        if complete
        else "not_assessed"
    )
    lines = [
        "# Seed-/Treiber-Kreuzvergleich",
        "",
        f"Status: `{report['status']}`; Befund: `{report['outcome']}`.",
        "",
    ]
    if not complete:
        lines.append(
            "Gesamtinterpretation gesperrt; verfügbare Teilstände bleiben erhalten."
        )
    else:
        lines += [
            "| Zelle | Seed | Zielpfad | Gesamte Front gleich | Alle Suchmerkmale gleich |",
            "| --- | --- | --- | --- | --- |",
        ]
        for case, result in zip(CASES, report["comparisons"], strict=True):
            lines.append(
                f"| {case['number']} | {case['seed']} | {case['target']} | {result['matches']['signature']} | {result['all_search_features_equal']} |"
            )
        lines += [
            "",
            "Beide Gegenrichtungen reproduzieren die historischen Suchergebnisse. Das stützt Seedabhängigkeit für diese zwei Fälle und spricht gegen einen Unterschied dieser Workerpfade als Erklärung."
            if report["outcome"] == "both_crossovers_reproduced"
            else "Mindestens ein gültiger Unterschied liegt vor. Die getrennten Merkmale und Originalfronten geben einen Ansatzpunkt für die technische Ursachenanalyse; ein Codefehler ist damit noch nicht bewiesen.",
            "",
            "| Zelle | Kurve alt / neu | Struktur alt / neu | Parameter alt / neu |",
            "| --- | --- | --- | --- |",
        ]
        for case, result in zip(CASES, report["comparisons"], strict=True):
            markers = [
                f"{result['reference_markers'][key]} / {result['fresh_markers'][key]}"
                for key in ("curve", "structure", "parameters")
            ]
            lines.append("| " + " | ".join([str(case["number"]), *markers]) + " |")
        lines += [
            "",
            "Zwei gezielt gewählte Fälle; keine Erfolgswahrscheinlichkeit oder automatische Budgeterhöhung. Physikalische Identifikation bleibt not_assessed.",
        ]
    temporary = output / "crosscheck_summary.md.tmp"
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(output / "crosscheck_summary.md")
    _write_json(output / "crosscheck_report.json", report)


def bridge_command(checkout, action, kind, output, request, deadline):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(checkout / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [
        sys.executable,
        "-c",
        # Replace the launcher process so cancellation waits for the bridge to
        # stop its separately isolated search worker before killing this group.
        (
            "import os, runpy, sys; launcher = runpy.run_path(sys.argv[1]); "
            "env = launcher['prepare_runtime'](launcher['ROOT']); "
            "os.execve(sys.executable, [sys.executable, *sys.argv[2:]], env)"
        ),
        str(checkout / "scripts/run_python.py"),
        str(ROOT / BRIDGE),
        "--action",
        action,
        "--kind",
        kind,
        "--output",
        str(output),
        "--request",
        str(request),
        "--deadline",
        str(deadline),
    ]
    return command, environment


def finalize(output, report, unchanged, clock):
    """Publish success last, checking all consumed bytes through finalization."""
    unchanged()
    report.update(
        status="completed",
        finished_at_utc=_utc_now(),
        wall_seconds=time.monotonic() - clock.started,
    )
    with tempfile.TemporaryDirectory(
        prefix=".crosscheck-final-", dir=output.parent
    ) as temporary:
        stage = Path(temporary)
        save_report(stage, report)
        staged = {
            name: (stage / name).read_bytes()
            for name in ("crosscheck_report.json", "crosscheck_summary.md")
        }
        expected = {
            **hashes(output),
            **{name: _sha256(value) for name, value in staged.items()},
        }
        _write_json(stage / "crosscheck_checksums.json", expected)
        manifest = (stage / "crosscheck_checksums.json").read_bytes()
        unchanged()
        (output / "crosscheck_summary.md").write_bytes(staged["crosscheck_summary.md"])
        (output / "crosscheck_checksums.json").write_bytes(manifest)
    unchanged()
    actual = hashes(output)
    actual.update(
        {
            "crosscheck_report.json": _sha256(staged["crosscheck_report.json"]),
            "crosscheck_summary.md": _sha256(
                (output / "crosscheck_summary.md").read_bytes()
            ),
        }
    )
    if (
        actual != expected
        or (output / "crosscheck_checksums.json").read_bytes() != manifest
    ):
        raise ValueError("Final crossover artifacts changed during publication.")
    pending = output / "crosscheck_report.json.tmp"
    pending.write_bytes(staged["crosscheck_report.json"])
    if pending.read_bytes() != staged["crosscheck_report.json"]:
        raise ValueError("Pending crossover report changed.")
    unchanged()
    pending.replace(output / "crosscheck_report.json")
    clock.check()


def call_bridge(checkout, action, kind, output, request, clock):
    command, environment = bridge_command(
        checkout, action, kind, output, request, clock.started + clock.seconds
    )
    log = output.parent / f"{output.name}-{action}.log"
    with log.open("wb") as stream:
        child = subprocess.Popen(
            command,
            cwd=checkout,
            env=environment,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            code = child.wait(timeout=clock.remaining())
            if code:
                raise RuntimeError("Historical bridge failed; inspect " + str(log))
        except BaseException:
            _stop_worker(child)
            raise
    clock.check()


def scientific_platform():
    if (
        platform.system() != "Linux"
        or platform.freedesktop_os_release().get("ID") != "manjaro"
    ):
        raise ValueError(
            "Scientific crossover searches run only on the original Manjaro machine."
        )


def retain_failure(output, report, error, clock):
    """Keep revoking success even if cleanup itself fails or is interrupted."""
    clock.cancel()
    report.update(
        status="failed",
        outcome="not_assessed",
        error=f"{type(error).__name__}: {error}",
        wall_seconds=time.monotonic() - clock.started,
        abort_cleanup_errors=[],
        abort_signals=[],
    )
    previous_mask = signal.pthread_sigmask(
        signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM}
    )
    with ExitStack() as handlers:
        handlers.callback(signal.pthread_sigmask, signal.SIG_SETMASK, previous_mask)

        def defer(signum, frame):
            report["abort_signals"].append(signum)

        for sig in (signal.SIGINT, signal.SIGTERM):
            previous = signal.signal(sig, defer)
            handlers.callback(signal.signal, sig, previous)
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)

        def attempt(name, action):
            try:
                action()
                return True
            except BaseException as cleanup_error:  # noqa: BLE001 -- Continue revoking every success artifact.
                report["abort_cleanup_errors"].append(
                    {
                        "operation": name,
                        "error": f"{type(cleanup_error).__name__}: {cleanup_error}",
                    }
                )
                return False

        failed = []
        for name in (
            "crosscheck_report.json",
            "crosscheck_checksums.json",
            "crosscheck_summary.md",
            "crosscheck_report.json.tmp",
            "crosscheck_summary.md.tmp",
        ):
            path = output / name
            if not attempt("unlink " + name, lambda p=path: p.unlink(missing_ok=True)):
                failed.append(path)
        for path in failed:
            attempt(
                "retry unlink " + path.name, lambda p=path: p.unlink(missing_ok=True)
            )
        attempt(
            "write failure evidence",
            lambda: _write_json(output / "crosscheck_failure.json", report),
        )
        if not attempt("write locked summary", lambda: save_report(output, report)):
            attempt(
                "write locked report",
                lambda: _write_json(output / "crosscheck_report.json", report),
            )


def run(outer_archive, transfer_archive, output):
    driver = load_module(
        ROOT / "scripts/run_trigonometric_grammar.py", "crosscheck_clock"
    )
    clock = driver.WallTimeLimit(LIMIT_SECONDS)
    scientific_platform()
    sources = source_hashes()
    provenance = _provenance()
    if provenance["git"].get("dirty") is not False:
        raise ValueError("Use a clean, committed crossover checkout.")
    output = Path(output).resolve()
    if (
        output.exists()
        or ROOT.is_relative_to(output)
        or any(
            output.is_relative_to(ROOT / n)
            for n in ("src", "scripts", "docs", "data", "julia", ".git")
        )
    ):
        raise ValueError("Use a new crossover output outside source directories.")
    workroot = output.parent / ("." + output.name + "-checkouts")
    if workroot.exists():
        raise ValueError("The new helper-worktree destination already exists.")
    output.mkdir(parents=True)
    report = {
        "format": FORMAT,
        "status": "running",
        "outcome": "not_assessed",
        "started_at_utc": _utc_now(),
        "source_sha256": sources,
        "provenance": provenance,
        "plan": {"commit": PLAN_COMMIT, "sha256": PLAN_SHA256},
        "cases": list(CASES),
        "comparisons": [],
        "physical_identification": "not_assessed",
        "cleanup": [],
    }
    owned, frozen = [], {}
    previous = {}

    def interrupted(signum, frame):
        raise InterruptedError(f"Crossover interrupted by signal {signum}.")

    def unchanged():
        clock.check()
        if source_hashes() != sources or _provenance() != provenance:
            raise ValueError("Crossover adapter sources changed.")
        current = hashes(output)
        if any(current.get(k) != v for k, v in frozen.items()):
            raise ValueError("Consumed crossover artifacts changed.")

    try:
        with clock:
            for sig in (signal.SIGINT, signal.SIGTERM):
                previous[sig] = signal.signal(sig, interrupted)
            save_report(output, report)
            inputs = output / "inputs"
            inputs.mkdir()
            np.savez(inputs / "anchor.npz", **anchor_arrays())
            references = output / "references"
            references.mkdir()
            workroot.mkdir()
            for kind, archive in (
                ("outer", outer_archive),
                ("transfer", transfer_archive),
            ):
                contents, files = read_reference(archive, kind)
                (inputs / f"{kind}.tar.gz").write_bytes(contents)
                target = references / kind
                for name, value in files.items():
                    path = target / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(value)
                checkout = workroot / kind
                git(
                    "worktree",
                    "add",
                    "--detach",
                    str(checkout),
                    HISTORIES[kind]["commit"],
                )
                owned.append(checkout)
                for name in (
                    "uv.lock",
                    "pyproject.toml",
                    ".python-version",
                    "julia/Project.toml",
                    "julia/Manifest.toml",
                    "src/ringdown_sr/juliapkg.json",
                ):
                    if (checkout / name).read_bytes() != (ROOT / name).read_bytes():
                        raise ValueError("Historical dependency pins differ: " + name)
            frozen.update(hashes(output))
            verified, prepared = {}, {}
            for kind in HISTORIES:
                request = output / f"{kind}-reference-request.json"
                _write_json(
                    request,
                    {
                        "scope": "reference",
                        "kind": kind,
                        "commit": HISTORIES[kind]["commit"],
                        "reference": str(references / kind),
                        "cell": HISTORIES[kind]["reference_cell"],
                        "inputs": str(inputs / "anchor.npz"),
                        "bridge_sha256": sources[BRIDGE],
                    },
                )
                destination = output / f"{kind}-reference.json"
                call_bridge(
                    workroot / kind, "verify", kind, destination, request, clock
                )
                verified[kind] = read_json(destination.read_bytes())
                unchanged()
                frozen.update(hashes(output))
            for case in CASES:
                kind = case["target"]
                request = output / f"cell-{case['number']:02d}-request.json"
                _write_json(
                    request,
                    {
                        "scope": "scientific",
                        "kind": kind,
                        "commit": HISTORIES[kind]["commit"],
                        "seed": case["seed"],
                        "niterations": 500,
                        "inputs": str(inputs / "anchor.npz"),
                        "bridge_sha256": sources[BRIDGE],
                    },
                )
                destination = output / f"cell-{case['number']:02d}"
                call_bridge(
                    workroot / kind, "prepare", kind, destination, request, clock
                )
                prepared[case["number"]] = (destination, request)
                environment = read_json((destination / "options.json").read_bytes())[
                    "initial"
                ]["environment"]
                for reference in verified.values():
                    if environment_key(environment) != environment_key(
                        reference["environment"]
                    ):
                        raise ValueError(
                            "Historical/current numerical environments differ; no scientific crossover started."
                        )
                unchanged()
                frozen.update(hashes(output))
            for case in CASES:
                unchanged()
                destination, request = prepared[case["number"]]
                call_bridge(
                    workroot / case["target"],
                    "run",
                    case["target"],
                    destination,
                    request,
                    clock,
                )
                fresh = read_json((destination / "verified.json").read_bytes())
                if any(
                    environment_key(fresh[key])
                    != environment_key(verified[case["reference"]][key])
                    for key in ("environment", "environment_after_search")
                ):
                    raise ValueError("Worker environment differs from its reference.")
                report["comparisons"].append(
                    comparison(verified[case["reference"]], fresh)
                )
                unchanged()
                frozen.update(hashes(output))
                save_report(output, report)
            unchanged()
            # Successful cleanup belongs to the total deadline, before success.
            for checkout in reversed(owned.copy()):
                git("worktree", "remove", str(checkout))
                owned.remove(checkout)
                report["cleanup"].append({"kind": checkout.name, "status": "removed"})
            workroot.rmdir()
            finalize(output, report, unchanged, clock)
    except BaseException as error:
        retain_failure(output, report, error, clock)
        raise
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        for checkout in reversed(owned):
            try:
                git("worktree", "remove", str(checkout))
            except subprocess.CalledProcessError:
                print(
                    f"Helper worktree retained for inspection: {checkout}",
                    file=sys.stderr,
                )
        if workroot.exists() and not any(workroot.iterdir()):
            workroot.rmdir()
    return report
