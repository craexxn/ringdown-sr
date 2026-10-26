"""Repeat a stored arm twice without regenerating data or changing its budget."""

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
from dataclasses import asdict
from io import BytesIO
from pathlib import Path

import numpy as np

from ringdown_sr import symbolic
from ringdown_sr.pilot import _environment, _provenance, _utc_now, _write_json
from ringdown_sr.symbolic import FORMAT, SearchBudget, run_search_arm, search_parameters

FILES = (
    "inputs.npz",
    "request.json",
    "result.json",
    "metadata_initial.json",
    "metadata.json",
    "pysr_parameters.json",
    "backend_options.json",
)
REPORT_FORMAT = "ringdown-sr-arm-repeatability-1"
CONTROL_FORMAT = "ringdown-sr-search-blas-control-1"


def load_core_probe():
    """Load the unchanged, co-delivered fixed probe's verified pool checks."""
    path = Path(__file__).resolve().with_name("probe_symbolic_numerics.py")
    spec = importlib.util.spec_from_file_location("repeat_core_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def controlled_worker(directory, required):
    """Observe the existing worker at its own pre-fit and post-search boundaries."""
    if required != "Haswell":
        raise ValueError("The diagnostic worker requires the Haswell control.")
    probe = load_core_probe()
    probe.validate_core_request(required)
    info = {
        "format": CONTROL_FORMAT,
        "status": "running",
        "required_openblas_core": required,
        "tool_source_sha256": tool_hashes(),
        "snapshots": {},
    }
    path = directory / "blas_control.json"
    _write_json(path, info)
    original = symbolic._environment_snapshot

    def snapshot(phase, *, julia_used):
        environment = original(phase, julia_used=julia_used)
        if phase in ("before_fit", "after_search"):
            record = {
                "captured_at_utc": _utc_now(),
                "environment": environment,
                "openblas_coretype_environment": os.environ.get("OPENBLAS_CORETYPE"),
            }
            info["snapshots"][phase] = record
            _write_json(path, info)
            probe.validate_core_request(required)
            if not julia_used:
                raise ValueError("The search boundary must include loaded Julia.")
            record["blas_control"] = probe.verify_blas_control(
                environment, required, require_julia=True
            )
            if phase == "after_search":
                if set(info["snapshots"]) != {"before_fit", "after_search"}:
                    raise ValueError("Missing pre-fit BLAS control.")
                info["status"] = "verified"
            _write_json(path, info)
            print(f"Verified Haswell BLAS pools at {phase}; limits 1.", flush=True)
        return environment

    symbolic._environment_snapshot = snapshot
    try:
        symbolic.worker(directory)
        if info["status"] != "verified":
            raise ValueError("The worker did not visit both BLAS control boundaries.")
    except BaseException as error:
        info.update(status="failed", error=f"{type(error).__name__}: {error}")
        _write_json(path, info)
        raise
    finally:
        symbolic._environment_snapshot = original


def tool_hashes():
    parent = Path(__file__).resolve().parent
    return {
        name: digest((parent / filename).read_bytes())
        for name, filename in (
            ("driver.py", Path(__file__).name),
            ("probe_symbolic_numerics.py", "probe_symbolic_numerics.py"),
        )
    }


def controlled_dispatch(output, required, original):
    """Redirect only the standard worker entry; preserve launcher and process handling."""

    def run(command, *, stdout):
        expected = [
            sys.executable,
            str(symbolic.ROOT / "scripts/run_python.py"),
            str(symbolic.ROOT / "scripts/run_symbolic_worker.py"),
        ]
        if len(command) != 4 or command[:3] != expected:
            raise ValueError("Unexpected worker command for the controlled search.")
        return original(
            [
                *command[:2],
                str(output / "driver.py"),
                "--worker",
                command[3],
                "--require-openblas-core",
                required,
            ],
            stdout=stdout,
        )

    return run


def verify_worker_control(directory, metadata, required, expected_tools, probe):
    content = (directory / "blas_control.json").read_bytes()
    checksums = read_json((directory / "checksums.json").read_bytes())
    if checksums.get("blas_control.json") != digest(content):
        raise ValueError("Missing or mismatched worker BLAS control checksum.")
    info = read_json(content)
    if (
        info["format"] != CONTROL_FORMAT
        or info["status"] != "verified"
        or info["required_openblas_core"] != required
        or info["tool_source_sha256"] != expected_tools
        or set(info["snapshots"]) != {"before_fit", "after_search"}
    ):
        raise ValueError("Incomplete worker BLAS control or changed diagnostic tools.")
    for phase, field in (
        ("before_fit", "environment"),
        ("after_search", "environment_after_search"),
    ):
        record = info["snapshots"][phase]
        if (
            record["environment"] != metadata[field]
            or record["openblas_coretype_environment"] != required
        ):
            raise ValueError("Worker BLAS control differs from its search metadata.")
        if (
            probe.verify_blas_control(
                record["environment"], required, require_julia=True
            )
            != record["blas_control"]
        ):
            raise ValueError("Worker BLAS control does not match the loaded pools.")
    return info


def read_json(data):
    def reject(value):
        raise ValueError(f"Nonstandard JSON value: {value}")

    return json.loads(data, parse_constant=reject)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def array_fingerprint(values):
    values = np.ascontiguousarray(values, dtype="<f8")
    return {
        "shape": list(values.shape),
        "dtype": "<f8",
        "sha256": digest(values.tobytes()),
    }


def parameters_without_output(parameters):
    return {k: v for k, v in parameters.items() if k != "output_directory"}


def backend_without_output(fields):
    names = [field["name"] for field in fields]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate backend option name.")
    return {
        field["name"]: {k: field[k] for k in ("type", "value")}
        for field in fields
        if field["name"] != "output_directory"
    }


def signature(result):
    if result["format"] != FORMAT or not result["candidates"]:
        raise ValueError("Invalid completed search result.")
    front = []
    for candidate in result["candidates"]:
        loss = float(candidate["loss"])
        if not math.isfinite(loss) or loss < 0:
            raise ValueError("Candidate loss must be finite and nonnegative.")
        front.append(
            {
                "tree": candidate["tree"],
                "complexity": candidate["complexity"],
                "loss_hex": loss.hex(),
                "prediction": array_fingerprint(candidate["prediction"]),
                "residual": array_fingerprint(candidate["residual"]),
            }
        )
    index = result["selected_index"]
    if type(index) is not int or not 0 <= index < len(front):
        raise ValueError("Invalid selected index.")
    return {"front": front, "selected_index": index, "rng": result["rng"]}


def source_bytes(source):
    contents = {}
    for name in (*FILES, "checksums.json", "status.json"):
        path = (source / name).resolve()
        if not path.is_relative_to(source):
            raise ValueError("Source artifact escapes its arm directory.")
        contents[name] = path.read_bytes()
    if read_json(contents["status.json"])["status"] != "success":
        raise ValueError("The source arm must be successful.")
    checksums = read_json(contents["checksums.json"])
    for name in FILES:
        if checksums.get(name) != digest(contents[name]):
            raise ValueError(f"Source checksum mismatch: {name}")
    return contents


def repeat(source, output, *, label, required_openblas_core=None):
    """Run two fresh workers, recording exact snapshots and descriptive equality."""
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.is_relative_to(source):
        raise ValueError("Output must be outside the source arm.")
    if not label.strip():
        raise ValueError("A nonempty machine label is required.")
    probe = None
    initial_control = None
    expected_tools = None
    if required_openblas_core is not None:
        probe = load_core_probe()
        probe.validate_core_request(required_openblas_core)
        initial_control = probe.metadata()
        initial_control["blas_control"] = probe.verify_blas_control(
            initial_control["environment"], required_openblas_core, require_julia=False
        )
        expected_tools = tool_hashes()
    contents = source_bytes(source)
    request = read_json(contents["request.json"])
    if set(request) != {"format", "budget"} or request["format"] != FORMAT:
        raise ValueError("Unsupported source request.")
    budget = SearchBudget(**request["budget"])
    parameters = read_json(contents["pysr_parameters.json"])
    if any(
        key not in parameters or parameters[key] != value
        for key, value in search_parameters(budget).items()
    ):
        raise ValueError("Current search policy differs from the recorded source.")
    original = signature(read_json(contents["result.json"]))
    # Load only the bytes that were hashed, not a later re-read of the source.
    with np.load(BytesIO(contents["inputs.npz"]), allow_pickle=False) as inputs:
        if set(inputs.files) not in (
            {"time_s", "observed"},
            {"time_s", "observed", "covariance"},
        ):
            raise ValueError("Unexpected source arrays.")
        arrays = {key: inputs[key].copy() for key in inputs.files}
    for array in arrays.values():
        if (
            array.dtype.kind != "f"
            or array.dtype.itemsize != 8
            or not np.all(np.isfinite(array))
        ):
            raise ValueError("Source arrays must contain finite Float64 values.")
        array.flags.writeable = False
    fingerprints = {key: array_fingerprint(value) for key, value in arrays.items()}
    output.mkdir(parents=True, exist_ok=False)
    frozen = output / "source"
    frozen.mkdir()
    for name, data in contents.items():
        (frozen / name).write_bytes(data)
    (output / "driver.py").write_bytes(Path(__file__).read_bytes())
    if probe is not None:
        (output / "probe_symbolic_numerics.py").write_bytes(
            Path(probe.__file__).read_bytes()
        )
    report = {
        "format": REPORT_FORMAT,
        "status": "running",
        "label": label,
        "scope": "two local repetitions; no causal attribution or performance assessment",
        "started_at_utc": _utc_now(),
        "source_directory": str(source),
        "source_sha256": {name: digest(data) for name, data in contents.items()},
        "driver_sha256": digest(Path(__file__).read_bytes()),
        "provenance": _provenance(),
        "environment": _environment(),
        "budget": asdict(budget),
        "inputs": fingerprints,
        "source_signature": original,
        "runs": [],
        "comparison": None,
        "required_openblas_core": required_openblas_core,
        "control_initial": initial_control,
        "tool_source_sha256": expected_tools,
    }
    _write_json(output / "report.json", report)
    original_dispatch = symbolic._run_worker
    try:
        if probe is not None:
            symbolic._run_worker = controlled_dispatch(
                output, required_openblas_core, original_dispatch
            )
        for number in (1, 2):
            if source_bytes(source) != contents:
                raise ValueError(
                    "Source artifacts changed during the repetition check."
                )
            print(
                f"Starting repetition {number}/2; budget and inputs unchanged.",
                flush=True,
            )
            directory = output / f"run-{number}"
            record = {"directory": directory.name, "status": "running"}
            report["runs"].append(record)
            _write_json(output / "report.json", report)
            run = run_search_arm(
                arrays["time_s"],
                arrays["observed"],
                covariance=arrays.get("covariance"),
                output=directory,
                budget=budget,
            )
            record["status"] = run.status
            if run.status != "success":
                raise RuntimeError(
                    f"Repetition {number} failed; see {directory / 'worker.log'}"
                )
            source_bytes(directory)
            with np.load(directory / "inputs.npz", allow_pickle=False) as inputs:
                actual = {key: array_fingerprint(inputs[key]) for key in inputs.files}
            if (
                actual != fingerprints
                or read_json((directory / "request.json").read_bytes()) != request
            ):
                raise ValueError("A repetition changed the frozen inputs or request.")
            actual_parameters = read_json(
                (directory / "pysr_parameters.json").read_bytes()
            )
            if parameters_without_output(
                actual_parameters
            ) != parameters_without_output(parameters):
                raise ValueError("A repetition changed the recorded search policy.")
            result = read_json((directory / "result.json").read_bytes())
            metadata = read_json((directory / "metadata.json").read_bytes())
            if probe is not None:
                record.update(search_status=run.status, status="running")
                record["blas_control"] = verify_worker_control(
                    directory, metadata, required_openblas_core, expected_tools, probe
                )
                for key in ("provenance", "worker_provenance"):
                    if metadata[key] != initial_control["provenance"]:
                        raise ValueError("Search source provenance changed.")
                for key in ("adapter_source_sha256", "worker_adapter_source_sha256"):
                    if metadata[key] != initial_control["adapter_source_sha256"]:
                        raise ValueError("Search adapter sources changed.")
                if tool_hashes() != expected_tools:
                    raise ValueError("The diagnostic tool sources changed.")
                print(
                    "Verified OpenBLAS: Haswell for NumPy, SciPy and Julia; pool limits 1.",
                    flush=True,
                )
                record["status"] = "success"
            record.update(
                signature=signature(result),
                parameters=parameters_without_output(actual_parameters),
                backend_options=backend_without_output(
                    read_json((directory / "backend_options.json").read_bytes())
                ),
                candidate_count=len(result["candidates"]),
                code_records={
                    key: metadata[key]
                    for key in (
                        "provenance",
                        "worker_provenance",
                        "adapter_source_sha256",
                        "worker_adapter_source_sha256",
                    )
                },
            )
            selected = result["candidates"][result["selected_index"]]
            print(
                f"Repetition {number}: {len(result['candidates'])} candidates; "
                f"selected loss {float(selected['loss']):.17g}.",
                flush=True,
            )
            _write_json(output / "report.json", report)
        if source_bytes(source) != contents:
            raise ValueError("Source artifacts changed during the repetition check.")
        if probe is not None:
            final_control = probe.metadata()
            report["control_final"] = final_control
            final_control["blas_control"] = probe.verify_blas_control(
                final_control["environment"],
                required_openblas_core,
                require_julia=False,
            )
            if (
                any(
                    final_control[key] != initial_control[key]
                    for key in ("provenance", "adapter_source_sha256")
                )
                or tool_hashes() != expected_tools
            ):
                raise ValueError(
                    "Runtime or diagnostic sources changed during repetition."
                )
        first, second = report["runs"]
        a, b = first["signature"], second["signature"]
        report["comparison"] = {
            "inputs_bitwise_equal": True,
            "request_equal": True,
            "pysr_parameters_equal_except_output": first["parameters"]
            == second["parameters"],
            "backend_options_repr_equal_except_output": first["backend_options"]
            == second["backend_options"],
            "rng_records_equal": a["rng"] == b["rng"],
            "code_records_equal": first["code_records"] == second["code_records"],
            "front_bitwise_equal": a["front"] == b["front"],
            "selected_index_equal": a["selected_index"] == b["selected_index"],
            "selected_prediction_bitwise_equal": a["front"][a["selected_index"]][
                "prediction"
            ]
            == b["front"][b["selected_index"]]["prediction"],
            "source_matches_first_signature": original == a,
            "source_matches_second_signature": original == b,
            "source_artifacts_unchanged": True,
        }
        report["status"] = "completed"
    except BaseException as error:
        if report["runs"] and report["runs"][-1]["status"] == "running":
            report["runs"][-1]["status"] = "failed"
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        symbolic._run_worker = original_dispatch
        report["finished_at_utc"] = _utc_now()
        _write_json(output / "report.json", report)
        if probe is not None:
            _write_json(
                output / "checksums.json",
                {
                    path.relative_to(output).as_posix(): digest(path.read_bytes())
                    for path in sorted(output.rglob("*"))
                    if path.is_file() and path != output / "checksums.json"
                },
            )
    print(json.dumps(report["comparison"], indent=2), flush=True)
    print(f"Report: {output / 'report.json'}", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source", type=Path, nargs="?", help="A completed symbolic arm directory"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--label")
    parser.add_argument("--require-openblas-core", choices=("Haswell",))
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if args.require_openblas_core != "Haswell":
            parser.error("The diagnostic worker requires the Haswell control.")
        controlled_worker(args.worker.resolve(), args.require_openblas_core)
    elif args.source and args.output and args.label:
        repeat(
            args.source,
            args.output,
            label=args.label,
            required_openblas_core=args.require_openblas_core,
        )
    else:
        parser.error("Provide source, --output and --label.")


if __name__ == "__main__":
    main()
