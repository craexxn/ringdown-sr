"""Invoke unchanged historical workers through one bounded single-cell adapter."""

import argparse
import math
import platform
import signal
import time
from dataclasses import asdict
from functools import partial
from pathlib import Path

import numpy as np

from ringdown_sr import symbolic
from ringdown_sr.noiseless_control import fingerprint
from ringdown_sr.pilot import _json_bytes, _provenance, _sha256, _write_json
from ringdown_sr.representation_control import _markers, diagnose_candidate
from ringdown_sr.search_duration import load_module

HISTORIES = {
    "outer": (
        "5215c5e1c93f220a3f7ea59b1c37580d2f2b5ea4",
        "outer_search_ladder",
        20261210,
    ),
    "transfer": (
        "bc4025d13b4954dee779341026d282430521686a",
        "transfer_check",
        20261201,
    ),
}
ANCHOR = {
    "time_s": (
        [128],
        "50c345daa383e450558fca37cd20adf54f13549035ae53eeb0c528d140666c5c",
    ),
    "observed": (
        [128],
        "7947f112b6c2196cae5215803d4d7a50e2401755d5fddf786ce19fda0a2419aa",
    ),
    "diagnostic_time_s": (
        [889],
        "d93b19b716759c30734a68c0448a0f6bc619d00110dc458a461a237b2ebce854",
    ),
    "diagnostic_truth": (
        [889],
        "1339a1a9dc971a177bce24e7272c9d619a9dca4172fd937fbc27b45ff3a9df97",
    ),
}


def technical_arrays():
    times = np.arange(8, dtype=np.float64) / 8
    inner = (np.arange(7, dtype=np.float64) + 0.5) / 8
    return {
        "time_s": times,
        "observed": 1 + times,
        "diagnostic_time_s": inner,
        "diagnostic_truth": 1 + inner,
    }


def context(kind):
    name = HISTORIES[kind][1]
    factory = load_module(
        symbolic.ROOT / f"scripts/run_{name}.py", "crosscheck_factory"
    )
    control = factory.control
    driver = factory.load_driver()
    driver.WORKER_LIMIT_SECONDS = 900
    support = driver.BASE.load_support()
    probe = support.load_core_probe()
    return control, driver, support, probe


def checked_request(path, kind, action, support):
    request = support.read_json(path.read_bytes())
    common = {"scope", "kind", "commit", "inputs", "bridge_sha256"}
    extra = {"reference", "cell"} if action == "verify" else {"seed", "niterations"}
    if (
        set(request) != common | extra
        or request["kind"] != kind
        or request["commit"] != HISTORIES[kind][0]
        or request["bridge_sha256"] != _sha256(Path(__file__).read_bytes())
    ):
        raise ValueError("Wrong historical single-cell request or bridge source.")
    if _provenance()["git"] != {
        "available": True,
        "changes": [],
        "commit": HISTORIES[kind][0],
        "dirty": False,
    }:
        raise ValueError("Expected the clean historical Git checkout.")
    if action == "verify":
        if request["scope"] != "reference" or request["cell"] != (
            2 if kind == "outer" else 1
        ):
            raise ValueError("Wrong reference cell.")
    else:
        expected = (
            (73, 2) if request["scope"] == "technical" else (HISTORIES[kind][2], 500)
        )
        if request["scope"] not in ("technical", "scientific") or any(
            type(request[key]) is not int or request[key] != value
            for key, value in zip(("seed", "niterations"), expected, strict=True)
        ):
            raise ValueError("Only the fixed crossover or technical cell is allowed.")
        if request["scope"] == "scientific" and (
            platform.system() != "Linux"
            or platform.freedesktop_os_release().get("ID") != "manjaro"
        ):
            raise ValueError("Scientific crossovers run only on Manjaro.")
    with np.load(request["inputs"], allow_pickle=False) as saved:
        arrays = {key: saved[key].copy() for key in saved.files}
    expected = (
        {key: fingerprint(value) for key, value in technical_arrays().items()}
        if request["scope"] == "technical"
        else {
            key: {"shape": shape, "dtype": "<f8", "sha256": digest}
            for key, (shape, digest) in ANCHOR.items()
        }
    )
    if set(arrays) != set(expected) or any(
        arrays[key].dtype != np.float64 or fingerprint(arrays[key]) != value
        for key, value in expected.items()
    ):
        raise ValueError("Wrong fixed input roles or Float64 bits.")
    for value in arrays.values():
        value.flags.writeable = False
    return request, arrays


def cell_for(request):
    return {
        "number": 1,
        "directory": "worker",
        "condition": "local_300_5",
        "arm": "local_300_5",
        "grammar": "unrestricted",
        "signal": "anchor",
        "budget": asdict(
            symbolic.SearchBudget(
                seed=request["seed"], niterations=request["niterations"]
            )
        ),
        "status": "planned",
    }


def verify_preflight(
    options, references, initial, sources, control, driver, support, probe, seed
):
    for mode, record in (("options", options), ("references", references)):
        if (
            record["format"] != control.FORMAT
            or record["mode"] != mode
            or record["status"] != "verified"
            or record["source_sha256"] != sources
        ):
            raise ValueError("Invalid historical preflight.")
        driver.verify_snapshots(record, initial, probe)
    if options["callback_calls"] != 0 or len(options["profiles"]) != 1:
        raise ValueError("Invalid single-seed options coverage.")
    profile = options["profiles"][0]
    if profile["condition"] != "local_300_5" or profile["python_seed"] != seed:
        raise ValueError("Wrong single-seed native options.")
    control.verify_options(profile, seed, "local_300_5", driver.BASE, support)
    if (
        len(references["cases"]) != 3
        or references["grammar_cases"] != control.expected_grammar_cases()
        or {(c["condition"], c["frequency_hz"]) for c in references["cases"]}
        != {("local_300_5", f) for f in (250, 4346, 33018)}
    ):
        raise ValueError("Incomplete unchanged fixed-reference coverage.")


def inspect(control, seed, mode):
    backend = load_module(
        symbolic.ROOT / "scripts/check_trigonometric_grammar_backend.py",
        "crosscheck_backend_" + mode,
    )
    for name in (
        "FORMAT",
        "CONDITIONS",
        "NATIVE_MODULE",
        "source_hashes",
        "verify_options",
        "common_options",
        "expected_grammar_cases",
    ):
        setattr(backend, name, getattr(control, name))
    backend.SEEDS = (seed,)
    backend.wrong_condition = lambda condition: "local_100_2"
    backend.SHOULD_SIMPLIFY = False
    backend.NATIVE_FILES += (control.NATIVE_MODULE + ".jl",)
    backend.diagnose_candidate = partial(diagnose_candidate, extended_structure=True)
    return backend.inspect(mode)


def evidence(directory, diagnosis, support, wall):
    read = lambda name: support.read_json((directory / name).read_bytes())
    return {
        "signature": support.signature(read("result.json")),
        "parameters": support.parameters_without_output(
            diagnosis["effective_parameters"]
        ),
        "backend_options": support.backend_without_output(
            diagnosis["effective_backend_options"]
        ),
        "callback_calls_during_fit": diagnosis["callback_calls_during_fit"],
        "markers": _markers(diagnosis["candidates"][diagnosis["selected_index"]]),
        "environment": read("metadata.json")["environment"],
        "environment_after_search": read("metadata.json")["environment_after_search"],
        "worker_wall_seconds": wall,
        "diagnostics": diagnosis,
    }


def verify_reference(output, request, arrays, control, driver, support, probe):
    root = Path(request["reference"])
    report = support.read_json((root / "report.json").read_bytes())
    cell = report["cells"][request["cell"] - 1]
    sources = control.source_hashes()
    if sources != report["source_sha256"]:
        raise ValueError("Historical reference sources differ from Git.")
    diagnosis = driver.verify_cell(
        root / cell["directory"],
        cell,
        arrays,
        support,
        probe,
        report["control_initial"],
        support.tool_hashes(),
        sources,
        support.read_json((root / "options.json").read_bytes()),
    )
    original = dict(cell["diagnostics"])
    wall = original.pop("worker_wall_seconds")
    if _json_bytes(diagnosis) != _json_bytes(original):
        raise ValueError("Independent historical parent diagnosis differs.")
    _write_json(output, evidence(root / cell["directory"], diagnosis, support, wall))


def prepare(output, request, request_path, control, driver, support, probe):
    output.mkdir()
    runtime = output / "runtime"
    runtime.mkdir()
    sources = control.source_hashes()
    initial = driver.BASE.core_snapshot(probe)
    files = {}
    for name, source in control.RUNTIME.items():
        (runtime / name).write_bytes((symbolic.ROOT / source).read_bytes())
        files["runtime/" + name] = sources[source]
    documents = {}
    for mode in ("options", "references"):
        documents[mode] = inspect(control, request["seed"], mode)
        _write_json(output / (mode + ".json"), documents[mode])
        files[mode + ".json"] = _sha256(_json_bytes(documents[mode]))
    verify_preflight(
        documents["options"],
        documents["references"],
        initial,
        sources,
        control,
        driver,
        support,
        probe,
        request["seed"],
    )
    if control.source_hashes() != sources or any(
        (output / name).is_symlink() or _sha256((output / name).read_bytes()) != digest
        for name, digest in files.items()
    ):
        raise ValueError("Historical sources changed during preparation.")
    _write_json(
        output / "prepared.json",
        {
            "request_sha256": _sha256(request_path.read_bytes()),
            "input_sha256": _sha256(Path(request["inputs"]).read_bytes()),
            "bridge_sha256": request["bridge_sha256"],
            "sources": sources,
            "initial": initial,
            "tools": support.tool_hashes(),
            "cell": cell_for(request),
            "files": files,
        },
    )


def run_cell(
    output, request, arrays, request_path, control, driver, support, probe, clock
):
    prepared_bytes = (output / "prepared.json").read_bytes()
    prepared = support.read_json(prepared_bytes)
    sources, files, cell = prepared["sources"], prepared["files"], prepared["cell"]
    if cell != cell_for(request) or prepared["tools"] != support.tool_hashes():
        raise ValueError("Changed prepared cell or verifier tools.")

    def unchanged():
        clock.check()
        if (
            control.source_hashes() != sources
            or _sha256(request_path.read_bytes()) != prepared["request_sha256"]
            or _sha256(Path(request["inputs"]).read_bytes()) != prepared["input_sha256"]
            or _sha256(Path(__file__).read_bytes()) != prepared["bridge_sha256"]
            or (output / "prepared.json").read_bytes() != prepared_bytes
            or any(
                (output / name).is_symlink()
                or _sha256((output / name).read_bytes()) != digest
                for name, digest in files.items()
            )
        ):
            raise ValueError("Consumed historical artifacts or sources changed.")

    unchanged()
    preflight = support.read_json((output / "options.json").read_bytes())
    references = support.read_json((output / "references.json").read_bytes())
    verify_preflight(
        preflight,
        references,
        prepared["initial"],
        sources,
        control,
        driver,
        support,
        probe,
        request["seed"],
    )
    original = symbolic._run_worker
    before = time.monotonic()
    try:
        symbolic._run_worker = driver.dispatch(
            output / "runtime", cell, sources, files, output, clock.remaining, unchanged
        )
        result = symbolic.run_search_arm(
            arrays["time_s"],
            arrays["observed"],
            covariance=None,
            output=output / "worker",
            budget=symbolic.SearchBudget(**cell["budget"]),
        )
    finally:
        symbolic._run_worker = original
    wall = time.monotonic() - before
    if result.status != "success":
        raise RuntimeError("Historical worker failed; inspect worker/worker.log.")
    diagnosis = driver.verify_cell(
        output / "worker",
        cell,
        arrays,
        support,
        probe,
        prepared["initial"],
        prepared["tools"],
        sources,
        preflight,
    )
    files.update(
        {
            "worker/" + name: digest
            for name, digest in diagnosis["source_file_sha256"].items()
        }
    )
    unchanged()
    _write_json(
        output / "verified.json", evidence(output / "worker", diagnosis, support, wall)
    )
    unchanged()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("verify", "prepare", "run"), required=True)
    parser.add_argument("--kind", choices=tuple(HISTORIES), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    args = parser.parse_args()
    remaining = args.deadline - time.monotonic()
    if not math.isfinite(remaining) or not 0 < remaining <= 3600:
        raise ValueError("Invalid or expired crossover deadline.")
    control, driver, support, probe = context(args.kind)
    with driver.WallTimeLimit(remaining) as clock:

        def interrupted(signum, frame):
            raise InterruptedError(
                f"Historical adapter interrupted by signal {signum}."
            )

        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, interrupted)
        request, arrays = checked_request(args.request, args.kind, args.action, support)
        if args.action != "run" and args.output.exists():
            raise ValueError("Refuse to overwrite historical adapter output.")
        if args.action == "verify":
            verify_reference(
                args.output, request, arrays, control, driver, support, probe
            )
        elif args.action == "prepare":
            prepare(args.output, request, args.request, control, driver, support, probe)
        else:
            run_cell(
                args.output,
                request,
                arrays,
                args.request,
                control,
                driver,
                support,
                probe,
                clock,
            )
        clock.check()


if __name__ == "__main__":
    main()
