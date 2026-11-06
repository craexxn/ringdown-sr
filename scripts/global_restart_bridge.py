"""Adapt the unchanged historical single-cell worker to the frozen restart plan."""

import argparse
import math
import platform
import signal
import subprocess
import time
from pathlib import Path

import numpy as np

from ringdown_sr import symbolic
from ringdown_sr.noiseless_control import fingerprint
from ringdown_sr.pilot import _json_bytes, _provenance, _sha256, _write_json
from ringdown_sr.search_duration import load_module

ROOT = Path(__file__).resolve().parents[1]
PLAN_COMMIT = "b00fc4a0a5a5a90e7d72f45d2b27788d1fd1585a"
PLAN_HASHES = {
    "docs/global_restart_comparison_plan.md": "15c68dcbd071adc64165f78dcea057c48a0292aa5e9c6358c474b55e46d76776",
    "data/global_restart_protocol.json": "892b1c66d8a715e2013bc2012ad049567c512c7d203a820fd173cd3c5e11417f",
}
LEGACY = ROOT / "scripts/seed_driver_crosscheck_bridge.py"


def configuration():
    import json

    for name, expected in PLAN_HASHES.items():
        if _sha256((ROOT / name).read_bytes()) != expected:
            raise ValueError("Changed frozen restart protocol.")
    return json.loads((ROOT / "data/global_restart_protocol.json").read_bytes())


def cells(technical=False):
    config = configuration()
    if technical:
        return [
            {"number": i + 1, "block": 0, "member": i, "seed": 73, "niterations": n}
            for i, n in enumerate((2, 3, 2))
        ]
    result = []
    for block, seeds in enumerate(config["blocks"], 1):
        for member, seed, iterations in [
            (0, seeds[0], config["reference_iterations"]),
            (None, seeds[0], config["long_iterations"]),
            *(
                (m, s, config["reference_iterations"])
                for m, s in enumerate(seeds[1:], 1)
            ),
        ]:
            result.append(
                {
                    "number": len(result) + 1,
                    "block": block,
                    "member": member,
                    "seed": seed,
                    "niterations": iterations,
                }
            )
    return result


def request_for(cell, inputs, technical=False):
    return {
        "scope": "technical" if technical else "scientific",
        "kind": "outer",
        "commit": configuration()["worker_commit"],
        "inputs": str(inputs),
        "bridge_sha256": _sha256(LEGACY.read_bytes()),
        "adapter_sha256": _sha256(Path(__file__).read_bytes()),
        "protocol": PLAN_HASHES,
        "cell": cell,
        "seed": cell["seed"],
        "niterations": cell["niterations"],
    }


def checked_request(path, inputs, action, legacy, support):
    request = support.read_json(path.read_bytes())
    if request.get("scope") not in ("technical", "scientific"):
        raise ValueError("Unknown restart scope.")
    technical = request["scope"] == "technical"
    if _json_bytes(request.get("cell")) not in [
        _json_bytes(c) for c in cells(technical)
    ]:
        raise ValueError("Unplanned restart cell.")
    expected = request_for(request["cell"], request.get("inputs"), technical)
    if _json_bytes(request) != _json_bytes(expected):
        raise ValueError("Changed restart request.")
    if _provenance()["git"] != {
        "available": True,
        "changes": [],
        "commit": configuration()["worker_commit"],
        "dirty": False,
    }:
        raise ValueError("Expected the unchanged historical worker checkout.")
    if (
        not technical
        and action != "verify"
        and (
            platform.system() != "Linux"
            or platform.freedesktop_os_release().get("ID") != "manjaro"
        )
    ):
        raise ValueError("Scientific restart searches run only on Manjaro.")
    if action != "verify" and Path(request["inputs"]) != inputs:
        raise ValueError("Search input path changed.")
    with np.load(inputs, allow_pickle=False) as saved:
        arrays = {key: saved[key].copy() for key in saved.files}
    fingerprints = (
        {key: fingerprint(value) for key, value in legacy.technical_arrays().items()}
        if technical
        else {
            key: {"shape": shape, "dtype": "<f8", "sha256": digest}
            for key, (shape, digest) in legacy.ANCHOR.items()
        }
    )
    if {key: fingerprint(value) for key, value in arrays.items()} != fingerprints:
        raise ValueError("Wrong fixed restart input bits or roles.")
    for value in arrays.values():
        value.flags.writeable = False
    return request, arrays


def verify_prepared(output, request_path, inputs, request, legacy, context):
    control, _driver, support, _probe = context
    prepared = support.read_json((output / "prepared.json").read_bytes())
    if (
        prepared["request_sha256"] != _sha256(request_path.read_bytes())
        or prepared["input_sha256"] != _sha256(inputs.read_bytes())
        or prepared["bridge_sha256"] != _sha256(LEGACY.read_bytes())
        or prepared["sources"] != control.source_hashes()
        or prepared["tools"] != support.tool_hashes()
        or prepared["cell"] != legacy.cell_for(request)
    ):
        raise ValueError("Prepared restart bindings changed.")
    for name, digest in prepared["files"].items():
        path = output / name
        if path.is_symlink() or _sha256(path.read_bytes()) != digest:
            raise ValueError("Prepared historical artifact changed: " + name)
    required = {"runtime/" + name for name in control.RUNTIME} | {
        "options.json",
        "references.json",
    }
    if set(prepared["files"]) != required:
        raise ValueError("Prepared file inventory is incomplete.")
    legacy.verify_preflight(
        support.read_json((output / "options.json").read_bytes()),
        support.read_json((output / "references.json").read_bytes()),
        prepared["initial"],
        prepared["sources"],
        *context,
        request["seed"],
    )
    return prepared


def failure_kind(error, metadata):
    if isinstance(error, subprocess.TimeoutExpired):
        return "worker_timeout"
    if str(error) != "Historical worker failed; inspect worker/worker.log.":
        return None
    if metadata.get("failed_during") == "fit":
        return "fit_error"
    if metadata.get("failed_during") == "replay" and metadata.get("error") in {
        "ValueError: No admissible candidates were exported.",
        "ValueError: Candidate losses must be finite and nonnegative.",
        "ValueError: Replay losses must be finite nonnegative scalars.",
        "ValueError: The loss exceeds the finite float64 range.",
    }:
        return "unusable_native_loss"
    return None


def verify_failed_worker(output, arrays, prepared, context, kind):
    control, _driver, support, _probe = context
    worker = output / "worker"
    read = lambda name: support.read_json((worker / name).read_bytes())
    status, metadata = read("status.json"), read("metadata.json")
    if status["status"] != "failed" or (output / "verified.json").exists():
        raise ValueError("Failed worker carries success evidence.")
    if kind == "worker_timeout":
        if not status.get("error", "").startswith("TimeoutExpired:"):
            raise ValueError("Missing timeout evidence.")
    elif kind != failure_kind(
        RuntimeError("Historical worker failed; inspect worker/worker.log."), metadata
    ):
        raise ValueError("Unconfirmed or misclassified worker failure.")
    if kind not in {"worker_timeout", "fit_error", "unusable_native_loss"}:
        raise ValueError("Unknown worker failure category.")
    if read("request.json") != {
        "format": symbolic.FORMAT,
        "budget": prepared["cell"]["budget"],
    }:
        raise ValueError("Failed worker budget changed.")
    with np.load(worker / "inputs.npz", allow_pickle=False) as saved:
        if set(saved.files) != {"time_s", "observed"} or any(
            fingerprint(saved[key]) != fingerprint(arrays[key]) for key in saved.files
        ):
            raise ValueError("Failed worker input roles or bits changed.")
    manifest = control.verify_manifest(worker, output / "runtime")
    if (
        manifest["sources"] != prepared["sources"]
        or metadata["provenance"] != prepared["initial"]["provenance"]
    ):
        raise ValueError("Failed worker source provenance changed.")
    if read("profile.json") != {
        "format": control.PROFILE_FORMAT,
        "condition": "local_300_5",
    }:
        raise ValueError("Failed worker profile changed.")


def verify_result(output, request, arrays, prepared, legacy, context):
    _control, driver, support, probe = context
    old = support.read_json((output / "outcome.json").read_bytes())
    if old["status"] == "worker_failed":
        verify_failed_worker(output, arrays, prepared, context, old["failure_kind"])
        return old
    if old["status"] != "completed":
        raise ValueError("Unfinished restart worker.")
    diagnosis = driver.verify_cell(
        output / "worker",
        prepared["cell"],
        arrays,
        support,
        probe,
        prepared["initial"],
        prepared["tools"],
        prepared["sources"],
        support.read_json((output / "options.json").read_bytes()),
    )
    verified = support.read_json((output / "verified.json").read_bytes())
    actual = legacy.evidence(
        output / "worker", diagnosis, support, verified["worker_wall_seconds"]
    )
    if _json_bytes(actual) != _json_bytes(verified):
        raise ValueError("Independent native restart verification differs.")
    return old


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("prepare", "run", "verify"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--verification", type=Path)
    parser.add_argument("--deadline", type=float, required=True)
    args = parser.parse_args()
    remaining = args.deadline - time.monotonic()
    if (
        not math.isfinite(remaining)
        or not 0 < remaining <= configuration()["total_seconds"]
    ):
        raise ValueError("Invalid restart deadline.")
    legacy = load_module(LEGACY, "restart_legacy_bridge")
    context = legacy.context("outer")
    _control, driver, support, _probe = context
    driver.WORKER_LIMIT_SECONDS = configuration()["worker_seconds"]
    with driver.WallTimeLimit(remaining) as clock:

        def interrupted(signum, frame):
            raise InterruptedError(f"Restart adapter interrupted by signal {signum}.")

        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, interrupted)
        request, arrays = checked_request(
            args.request, args.inputs, args.action, legacy, support
        )
        if args.action == "prepare":
            legacy.prepare(args.output, request, args.request, *context)
        else:
            prepared = verify_prepared(
                args.output, args.request, args.inputs, request, legacy, context
            )
            if args.action == "verify":
                if args.verification is None or args.verification.exists():
                    raise ValueError("Use a new independent verification destination.")
                outcome = verify_result(
                    args.output, request, arrays, prepared, legacy, context
                )
                verify_prepared(
                    args.output, args.request, args.inputs, request, legacy, context
                )
                _write_json(args.verification, outcome)
            else:
                if (args.output / "worker").exists():
                    raise ValueError("Refuse to repeat a planned search.")
                started = time.monotonic()
                try:
                    legacy.run_cell(
                        args.output, request, arrays, args.request, *context, clock
                    )
                    outcome = {"status": "completed"}
                except (RuntimeError, subprocess.TimeoutExpired) as error:
                    # Only an actual failed search may consume a planned slot;
                    # preparation/replay/integrity failures abort the entire series.
                    worker = args.output / "worker"
                    if not (worker / "status.json").exists():
                        raise
                    status = support.read_json((worker / "status.json").read_bytes())
                    metadata = support.read_json(
                        (worker / "metadata.json").read_bytes()
                    )
                    kind = failure_kind(error, metadata)
                    if kind is None or status["status"] != "failed":
                        raise
                    verify_failed_worker(args.output, arrays, prepared, context, kind)
                    outcome = {
                        "status": "worker_failed",
                        "failure_kind": kind,
                        "error": f"{type(error).__name__}: {error}",
                    }
                outcome["adapter_run_wall_seconds"] = time.monotonic() - started
                verify_prepared(
                    args.output, args.request, args.inputs, request, legacy, context
                )
                clock.check()
                _write_json(args.output / "outcome.json", outcome)


if __name__ == "__main__":
    main()
