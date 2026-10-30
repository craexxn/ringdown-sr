"""Launch the frozen 48-call diagnostic, preserving fail-closed partial results."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from run_constant_diagnostic_worker import verify_controls

from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import (
    FORMAT,
    LIMIT_SECONDS,
    PLAN,
    RUNTIME,
    pair_differences,
    planned_calls,
    read_archive,
    source_hashes,
    verify_manifest,
    verify_options_record,
    verify_result,
)
from ringdown_sr.pilot import _provenance, _sha256, _utc_now, _write_json


def launch(command, log, remaining):
    if remaining <= 0:
        raise TimeoutError("Diagnostic wall-time limit reached.")
    process = subprocess.Popen(
        command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
    )
    try:
        code = process.wait(timeout=remaining)
        if code:
            raise RuntimeError(f"Diagnostic worker exited with {code}; see worker.log.")
    except BaseException:
        symbolic._stop_worker(process)
        raise


def run(archive, output):
    if output.exists() or any(
        output.is_relative_to(symbolic.ROOT / p)
        for p in ("src", "scripts", "docs", "julia", ".git")
    ):
        raise ValueError("Use a new output directory outside project sources.")
    provenance = _provenance()
    if provenance["git"]["dirty"] is not False:
        raise ValueError(
            "The scientific diagnostic requires a clean, committed checkout."
        )
    started = time.monotonic()
    original, arrays = read_archive(archive)
    sources = source_hashes()
    output.mkdir(parents=True)
    runtime = output / "runtime"
    runtime.mkdir()
    for name, src in RUNTIME.items():
        (runtime / name).write_bytes((symbolic.ROOT / src).read_bytes())
    (output / "plan.md").write_bytes((symbolic.ROOT / PLAN).read_bytes())
    np.savez(output / "diagnostic.npz", **arrays)
    frozen = {
        p.relative_to(output).as_posix(): _sha256(p.read_bytes())
        for p in [*runtime.iterdir(), output / "plan.md", output / "diagnostic.npz"]
    }
    report = {
        "format": FORMAT,
        "status": "running",
        "started_at": _utc_now(),
        "provenance": provenance,
        "source_sha256": sources,
        "cells": [],
        "controls": [],
        "final_verification": "pending",
        "pair_differences": None,
        "summaries": None,
    }
    files = dict(frozen)

    def remaining():
        return LIMIT_SECONDS - (time.monotonic() - started)

    def unchanged():
        if remaining() <= 0:
            raise TimeoutError("Diagnostic wall-time limit reached.")
        if source_hashes() != sources or archive.read_bytes() != original:
            raise ValueError("Sources or original input changed.")
        for name, digest in files.items():
            p = output / name
            if p.is_symlink() or _sha256(p.read_bytes()) != digest:
                raise ValueError("A consumed or verified diagnostic artifact changed.")

    def worker(request, directory):
        unchanged()
        directory.mkdir()
        _write_json(directory / "request.json", request)
        np.savez(
            directory / "inputs.npz", **{k: arrays[k] for k in ("time_s", "observed")}
        )
        _write_json(
            directory / "manifest.json",
            {
                "sources": sources,
                "runtime": {k: sources[v] for k, v in RUNTIME.items()},
                "inputs": {
                    k: _sha256((directory / k).read_bytes())
                    for k in ("inputs.npz", "request.json")
                },
            },
        )
        # Freeze bytes before the child consumes them, independently of its manifest.
        for p in directory.iterdir():
            files[p.relative_to(output).as_posix()] = _sha256(p.read_bytes())
        with (directory / "worker.log").open("w") as log:
            launch(
                [
                    sys.executable,
                    str(symbolic.ROOT / "scripts/run_python.py"),
                    str(runtime / "worker.py"),
                    str(directory),
                ],
                log,
                remaining(),
            )
        unchanged()
        verify_manifest(directory, runtime)
        result = json.loads((directory / "result.json").read_bytes())
        if result["request"] != request:
            raise ValueError("Changed worker request.")
        return result

    try:
        _write_json(output / "report.json", report)
        for iterations in (20, 100):
            request = {"mode": "controls", "iterations": iterations, "seed": 20261020}
            directory = output / f"controls-{iterations}"
            result = worker(request, directory)
            verify_controls(result, arrays)
            report["controls"].append(result)
            files[(directory / "result.json").relative_to(output).as_posix()] = _sha256(
                (directory / "result.json").read_bytes()
            )
        for request in planned_calls(arrays["observed"]):
            cell = {"request": request, "status": "running"}
            report["cells"].append(cell)
            _write_json(output / "report.json", report)
            directory = output / f"call-{request['number']:02d}"
            result = worker(request, directory)
            verify_options_record(
                result,
                next(
                    c
                    for c in report["controls"]
                    if c["request"]["iterations"] == request["iterations"]
                ),
            )
            diagnosis = verify_result(result, request, arrays)
            cell.update(status="completed", result=result, diagnosis=diagnosis)
            files[(directory / "result.json").relative_to(output).as_posix()] = _sha256(
                (directory / "result.json").read_bytes()
            )
            _write_json(output / "report.json", report)
        differences = pair_differences(report["cells"])
        unchanged()
        report["final_verification"] = "passed"
        report["pair_differences"] = differences
        report["summaries"] = {
            group: {
                str(budget): {
                    "count": 12,
                    "within_tolerance": sum(
                        c["diagnosis"]["curve_marker"] == "within_tolerance"
                        for c in report["cells"]
                        if c["request"]["start"]["name"].startswith(group)
                        and c["request"]["iterations"] == budget
                    ),
                }
                for budget in (20, 100)
            }
            for group in ("L", "R")
        }
        report["status"] = "completed"
    except BaseException as error:
        report.update(
            status="incomplete",
            error=f"{type(error).__name__}: {error}",
            final_verification="failed",
            pair_differences=None,
            summaries=None,
        )
        if report["cells"] and report["cells"][-1]["status"] == "running":
            report["cells"][-1]["status"] = "failed"
        raise
    finally:
        report["finished_at"] = _utc_now()
        report["wall_seconds"] = time.monotonic() - started
        _write_json(output / "report.json", report)
        _write_json(
            output / "checksums.json",
            {
                p.relative_to(output).as_posix(): _sha256(p.read_bytes())
                for p in output.rglob("*")
                if p.is_file() and p.name != "checksums.json"
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.archive.resolve(), args.output.resolve())
