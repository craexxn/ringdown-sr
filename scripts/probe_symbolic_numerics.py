"""Probe fixed Float64 trees and real backend optimization on frozen ordinary data."""

import argparse
import hashlib
import json
import math
import os
import sys
from io import BytesIO
from pathlib import Path

import numpy as np

from ringdown_sr.losses import mean_squared_error
from ringdown_sr.pilot import _environment, _provenance, _utc_now, _write_json
from ringdown_sr.symbolic import (
    FORMAT,
    ROOT,
    _adapter_source_hashes,
    _check_prediction_replay,
    _export_tree,
    _import_tree,
    _inputs,
    _run_worker,
    evaluate_tree,
)

PROBE_FORMAT = "ringdown-sr-fixed-numerics-1"
SOURCE_FILES = (
    "inputs.npz",
    "request.json",
    "result.json",
    "metadata_initial.json",
    "metadata.json",
    "pysr_parameters.json",
    "backend_options.json",
)
# These are diagnostic starts, not recovered historical optimizer starts.
CASES = (
    ("sine_wsl_constant", "sine", (-float.fromhex("0x1.a9a30ae4d1e60p-2"),)),
    ("sine_manjaro_constant", "sine", (-float.fromhex("0x1.a9a30bd659620p-2"),)),
    ("sine_start_half", "sine", (-0.5,)),
    ("sine_start_one", "sine", (-1.0,)),
    ("linear_start_positive", "linear", (1.0, -1.0)),
    ("linear_start_negative", "linear", (-1.0, 1.0)),
    ("amplitude_sine_start_one", "amplitude_sine", (1.0, -0.5)),
    ("amplitude_sine_start_half", "amplitude_sine", (0.5, -1.0)),
)

JULIA_SOURCE = r"""
module FixedNumericsProbe
using SymbolicRegression
using Random: Xoshiro, rand
using LinearAlgebra: BLAS, dot
using ..RingdownSRLoss: FixedWindowLoss, candidate_loss
const Backend = SymbolicRegression.ConstantOptimizationModule
const Optim = Backend.Optim

constant(value) = Node{Float64}(; val=value)
variable(index) = Node{Float64}(; feature=index)
unary(index, child) = Node{Float64}(; op=index, l=child)
binary(index, left, right) = Node{Float64}(; op=index, l=left, r=right)

function snapshot(tree, dataset, options)
    prediction, complete = eval_tree_array(tree, dataset.X, options)
    complete && prediction !== nothing || error("Incomplete fixed-tree evaluation.")
    residual = dataset.y - prediction
    return (;
        prediction=copy(prediction), residual,
        loss=SymbolicRegression.eval_loss(tree, dataset, options),
        sum_loss=sum(abs2, residual) / length(residual),
        dot_loss=dot(residual, residual) / length(residual),
    )
end

function run(time, observed, tree, seed)
    objective = FixedWindowLoss(time, observed)
    dataset = objective._dataset
    states = NamedTuple[]
    function observe(state)
        push!(states, (;
            kind=string(nameof(typeof(state))), parameters=copy(state.x),
            gradient=copy(state.g_x), loss=state.f_x,
        ))
        return false
    end
    options = Options(;
        binary_operators=[+, -, *, /], unary_operators=[exp, sin, cos],
        loss_function=objective, batching=false, turbo=false, bumper=false,
        dimensionless_constants_only=false, autodiff_backend=nothing,
        optimizer_algorithm=Optim.BFGS(; linesearch=Backend.LineSearches.BackTracking()),
        optimizer_nrestarts=2, optimizer_iterations=20,
        optimizer_options=(; callback=observe),
        deterministic=true, parsimony=0.0, maxsize=20,
        use_frequency=false, use_frequency_in_tournament=false,
    )
    supplied_constants = copy(SymbolicRegression.get_scalar_constants(tree)[1])
    member = PopMember(dataset, copy(tree), options; deterministic=true, ref=1)
    initial_parameters = copy(SymbolicRegression.get_optimizable_parameters(member.tree, options)[1])
    before = snapshot(member.tree, dataset, options)
    rng = Xoshiro(seed)
    rng_before = rand(copy(rng), UInt64, 8)
    member, evaluations = SymbolicRegression.optimize_constants(dataset, member, options; rng)
    after = snapshot(member.tree, dataset, options)
    parameters = copy(SymbolicRegression.get_optimizable_parameters(member.tree, options)[1])
    isequal(supplied_constants, SymbolicRegression.get_scalar_constants(tree)[1]) ||
        error("The supplied start tree changed.")
    return (;
        tree=SymbolicRegression.get_tree(member.tree), before, after,
        initial_parameters, parameters, member_loss=member.loss, states, evaluations,
        rng_before, rng_after=rand(copy(rng), UInt64, 8),
        options,
    )
end

function runtime()
    return (;
        version=string(VERSION), cpu_name=string(Sys.CPU_NAME),
        cpu_threads=Sys.CPU_THREADS, word_size=Sys.WORD_SIZE,
        julia_threads=Threads.nthreads(), gc_threads=Threads.ngcthreads(),
        blas_threads=BLAS.get_num_threads(), blas_config=string(BLAS.get_config()),
        cpu_target=get(ENV, "JULIA_CPU_TARGET", nothing),
        julia_num_threads=get(ENV, "JULIA_NUM_THREADS", nothing),
    )
end
end
"""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(data):
    def reject(value):
        raise ValueError(f"Nonstandard JSON number: {value}")

    return json.loads(data, parse_constant=reject)


def source_snapshot(source):
    contents = {}
    for name in (*SOURCE_FILES, "checksums.json", "status.json"):
        path = (source / name).resolve()
        if not path.is_relative_to(source):
            raise ValueError("Source artifact escapes the source directory.")
        contents[name] = path.read_bytes()
    if read_json(contents["status.json"])["status"] != "success":
        raise ValueError("The source arm must be successful.")
    checksums = read_json(contents["checksums.json"])
    for name in SOURCE_FILES:
        if checksums.get(name) != digest(contents[name]):
            raise ValueError(f"Source checksum mismatch: {name}")
    if read_json(contents["request.json"])["format"] != FORMAT:
        raise ValueError("Unsupported source format.")
    required = {
        "optimizer_algorithm": "BFGS",
        "optimizer_iterations": 20,
        "optimizer_nrestarts": 2,
        "optimizer_f_calls_limit": None,
        "autodiff_backend": None,
        "batching": False,
        "turbo": False,
        "bumper": False,
        "dimensionless_constants_only": False,
    }
    parameters = read_json(contents["pysr_parameters.json"])
    if any(
        key not in parameters or parameters[key] != val for key, val in required.items()
    ):
        raise ValueError("The source optimizer policy is not supported by this probe.")
    with np.load(BytesIO(contents["inputs.npz"]), allow_pickle=False) as data:
        if set(data.files) != {"time_s", "observed"}:
            raise ValueError(
                "This probe accepts only an ordinary arm without covariance."
            )
        arrays = {key: data[key].copy() for key in data.files}
    for values in arrays.values():
        if values.dtype.kind != "f" or values.dtype.itemsize != 8:
            raise ValueError("Inputs must use Float64 without precision conversion.")
    _inputs(arrays["time_s"], arrays["observed"], None)
    return contents, arrays


def number(value):
    value = float(value)
    return {
        "value": value if math.isfinite(value) else None,
        "hex": value.hex(),
        "status": "finite" if math.isfinite(value) else "nonfinite",
    }


def vector(values):
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise ValueError("Expected a vector.")
    return [number(value) for value in array]


def input_fingerprints(arrays):
    return {
        name: {
            "shape": list(value.shape),
            "sha256_little_endian_float64": digest(
                np.ascontiguousarray(value, dtype="<f8").tobytes()
            ),
        }
        for name, value in arrays.items()
    }


def start_tree(model, values):
    def constant(value):
        return {"kind": "constant", "value_hex": float(value).hex()}

    def op(name, *children):
        names = ("exp", "sin", "cos") if len(children) == 1 else ("+", "-", "*", "/")
        return {
            "kind": "operator",
            "arity": len(children),
            "operator": name,
            "operator_index": names.index(name) + 1,
            "children": list(children),
        }

    time = {"kind": "variable", "index": 1}
    if model == "sine":
        # Preserve the observed original binary order: t * k.
        return op("sin", op("*", time, constant(values[0])))
    if model == "linear":
        return op("+", constant(values[0]), op("*", constant(values[1]), time))
    if model == "amplitude_sine":
        return op(
            "*", constant(values[0]), op("sin", op("*", time, constant(values[1])))
        )
    raise ValueError(f"Unknown diagnostic model: {model}")


def checked_evaluation(record, tree, time, observed):
    prediction = np.asarray(record.prediction, dtype=np.float64)
    residual = np.asarray(record.residual, dtype=np.float64)
    python_prediction = evaluate_tree(tree, time)
    replay = _check_prediction_replay(python_prediction, prediction)
    if not np.array_equal(
        residual.view(np.uint64), (observed - prediction).view(np.uint64)
    ):
        raise ValueError("Julia and Python subtraction disagree bitwise.")
    loss = float(record.loss)
    if not math.isfinite(loss) or loss < 0:
        raise ValueError("The fixed-tree loss must be finite and nonnegative.")
    python_loss = mean_squared_error(observed - python_prediction)
    np.testing.assert_allclose(python_loss, loss, rtol=1e-10, atol=0)
    return {
        "prediction": vector(prediction),
        "residual": vector(residual),
        "loss": number(loss),
        "sum_loss": number(record.sum_loss),
        "dot_loss": number(record.dot_loss),
        "python_loss": number(python_loss),
        "python_prediction": vector(python_prediction),
        "prediction_replay": replay,
    }


def metadata(*, julia_used=False):
    environment = _environment()
    environment["julia_used"] = julia_used
    environment["numerical_libraries"]["snapshot"] = "fixed_numerics_probe"
    return {
        "captured_at_utc": _utc_now(),
        "provenance": _provenance(),
        "adapter_source_sha256": _adapter_source_hashes(),
        "environment": environment,
        "openblas_coretype_environment": os.environ.get("OPENBLAS_CORETYPE"),
    }


def validate_core_request(required):
    """Require a process-start setting; never change loaded libraries in place."""
    if required is None:
        return
    if required != "Haswell":
        raise ValueError("Only the common Haswell control is supported.")
    if os.environ.get("OPENBLAS_CORETYPE") != required:
        raise ValueError("Set OPENBLAS_CORETYPE=Haswell before starting Python.")
    for key in (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        if os.environ.get(key) != "1":
            raise ValueError(f"Set {key}=1 before starting the controlled probe.")


def verify_blas_control(environment, required, *, require_julia):
    """Verify actual loaded pools, including the separately loaded Julia BLAS."""
    if required is None:
        return {"status": "not_requested", "required_core": None}
    if required != "Haswell":
        raise ValueError("Only the common Haswell control is supported.")
    snapshot = environment["numerical_libraries"]["threadpools"]
    if snapshot["status"] != "available" or not isinstance(snapshot["details"], list):
        raise ValueError("Threadpool information is required to verify the core.")
    roles = set()
    observed = []
    for pool in snapshot["details"]:
        if pool.get("user_api") not in ("blas", "openmp"):
            continue
        if type(pool.get("num_threads")) is not int or pool["num_threads"] != 1:
            raise ValueError(f"A loaded pool does not report limit 1: {pool}")
        if pool["user_api"] != "blas":
            continue
        if (
            pool.get("internal_api") != "openblas"
            or pool.get("architecture") != required
        ):
            raise ValueError(f"A loaded BLAS pool does not report {required}: {pool}")
        path = str(pool.get("filepath", "")).replace("\\", "/").lower()
        role = (
            "numpy"
            if "/numpy.libs/" in path or "/numpy/.libs/" in path
            else "scipy"
            if "/scipy.libs/" in path or "/scipy/.libs/" in path
            else "julia"
            if "/lib/julia/" in path
            else None
        )
        if role:
            roles.add(role)
        observed.append(
            {
                "role": role,
                "filepath": pool["filepath"],
                "architecture": pool["architecture"],
                "num_threads": pool["num_threads"],
            }
        )
    needed = {"numpy", "scipy"} | ({"julia"} if require_julia else set())
    if not needed.issubset(roles):
        raise ValueError(f"Missing verified BLAS roles: {sorted(needed - roles)}")
    return {
        "status": "verified",
        "required_core": required,
        "roles": sorted(roles),
        "pools": observed,
    }


def worker(directory, *, required_openblas_core=None):
    if os.environ.get("PYTHON_JULIACALL_PROJECT") != str(ROOT / "julia"):
        raise RuntimeError("Run the worker through the pinned launcher.")
    info = metadata()
    info["required_openblas_core"] = required_openblas_core
    info["phase"] = "before_julia_import"
    _write_json(directory / "metadata.json", info)
    try:
        validate_core_request(required_openblas_core)
        import pysr
        from juliacall import Main as jl
        from juliacall import convert as jl_convert

        if (
            pysr.__version__ != "2.6.0"
            or str(jl.seval("string(Base.pkgversion(SymbolicRegression))")) != "2.5.1"
        ):
            raise RuntimeError(
                "The probe requires the reviewed pinned backend versions."
            )
        if (
            Path(str(jl.seval("Base.active_project()"))).resolve()
            != ROOT / "julia" / "Project.toml"
        ):
            raise RuntimeError("Unexpected active Julia project.")
        _, arrays = source_snapshot(directory.parent / "source")

        def array(values):
            return jl_convert(
                jl.Array[jl.Float64], np.asarray(values, dtype=np.float64)
            )

        kernel_bytes = (ROOT / "julia" / "src" / "RingdownSRLoss.jl").read_bytes()
        if (
            digest(kernel_bytes)
            != info["adapter_source_sha256"]["julia/src/RingdownSRLoss.jl"]
        ):
            raise ValueError("The Julia loss source changed before loading.")
        (directory / "RingdownSRLoss.jl").write_bytes(kernel_bytes)
        jl.include(str(directory / "RingdownSRLoss.jl"))
        jl.seval(JULIA_SOURCE)
        backend = jl.FixedNumericsProbe
        info.update(
            phase="blas_control_before_probes", before=metadata(julia_used=True)
        )
        _write_json(directory / "metadata.json", info)
        info["before"]["blas_control"] = verify_blas_control(
            info["before"]["environment"], required_openblas_core, require_julia=True
        )
        info["phase"] = "before_probes"
        runtime = backend.runtime()
        info["julia"] = {
            key: str(getattr(runtime, key))
            for key in ("version", "cpu_name", "blas_config")
        }
        info["julia"].update(
            {
                key: int(getattr(runtime, key))
                for key in (
                    "cpu_threads",
                    "word_size",
                    "julia_threads",
                    "gc_threads",
                    "blas_threads",
                )
            }
        )
        info["julia"].update(
            {
                key: None
                if getattr(runtime, key) is None
                else str(getattr(runtime, key))
                for key in ("cpu_target", "julia_num_threads")
            }
        )
        _write_json(directory / "metadata.json", info)
        result = {"format": PROBE_FORMAT, "rng_seed": 465951028, "cases": []}
        _write_json(directory / "result.json", result)
        for name, model, starts in CASES:
            tree = start_tree(model, starts)
            outcome = backend.run(
                array(arrays["time_s"]),
                array(arrays["observed"]),
                _import_tree(tree, backend),
                465951028,
            )
            restored = _export_tree(outcome.tree, outcome.options)
            before = checked_evaluation(
                outcome.before, tree, arrays["time_s"], arrays["observed"]
            )
            after = checked_evaluation(
                outcome.after, restored, arrays["time_s"], arrays["observed"]
            )
            expected_kind = "NewtonState" if len(starts) == 1 else "BFGSState"
            states = [
                {
                    "kind": str(state.kind),
                    "parameters": vector(state.parameters),
                    "gradient": vector(state.gradient),
                    "loss": number(state.loss),
                }
                for state in outcome.states
            ]
            if not states or any(state["kind"] != expected_kind for state in states):
                raise ValueError("The actual optimizer path does not match the case.")
            if vector(outcome.initial_parameters) != vector(starts):
                raise ValueError(
                    "The backend changed the prescribed starting parameters."
                )
            np.testing.assert_allclose(
                float(outcome.member_loss),
                float(outcome.after.loss),
                rtol=1e-12,
                atol=0,
            )
            options = outcome.options
            result["cases"].append(
                {
                    "name": name,
                    "model": model,
                    "initial_tree": tree,
                    "optimized_tree": restored,
                    "initial_parameters": vector(outcome.initial_parameters),
                    "parameters": vector(outcome.parameters),
                    "before": before,
                    "after": after,
                    "states": states,
                    "member_loss": number(outcome.member_loss),
                    "reported_evaluations": number(outcome.evaluations),
                    "rng_before_uint64": [str(v) for v in outcome.rng_before],
                    "rng_after_uint64": [str(v) for v in outcome.rng_after],
                    "optimizer_options": str(jl.repr(options.optimizer_options)),
                    "optimizer_algorithm": str(jl.repr(options.optimizer_algorithm)),
                    "optimizer_nrestarts": int(options.optimizer_nrestarts),
                }
            )
            _write_json(directory / "result.json", result)
            print(
                f"{name}: {expected_kind}; loss {float(outcome.before.loss):.17g} -> {float(outcome.after.loss):.17g}",
                flush=True,
            )
        info.update(phase="blas_control_after_probes", after=metadata(julia_used=True))
        _write_json(directory / "metadata.json", info)
        info["after"]["blas_control"] = verify_blas_control(
            info["after"]["environment"], required_openblas_core, require_julia=True
        )
        if any(
            info["after"][key] != info[key]
            for key in ("provenance", "adapter_source_sha256")
        ):
            raise ValueError("The runtime source files changed during the worker.")
        info["phase"] = "completed"
    except BaseException as error:
        info.update(phase="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        info["finished_at_utc"] = _utc_now()
        _write_json(directory / "metadata.json", info)


def probe(source, output, *, label, required_openblas_core=None):
    source, output = Path(source).resolve(), Path(output).resolve()
    if not label.strip() or output.is_relative_to(source):
        raise ValueError("Use a nonempty label and a new output outside the source.")
    validate_core_request(required_openblas_core)
    contents, arrays = source_snapshot(source)
    initial = metadata()
    initial["blas_control"] = verify_blas_control(
        initial["environment"], required_openblas_core, require_julia=False
    )
    output.mkdir(parents=True, exist_ok=False)
    frozen = output / "source"
    frozen.mkdir()
    for name, data in contents.items():
        (frozen / name).write_bytes(data)
    driver = Path(__file__).read_bytes()
    (output / "driver.py").write_bytes(driver)
    (output / "probe.jl").write_text(JULIA_SOURCE, encoding="utf-8")
    report = {
        "format": PROBE_FORMAT,
        "status": "running",
        "label": label,
        "scope": "fixed ordinary trees; diagnostic starts; no free search or causal claim",
        "started_at_utc": _utc_now(),
        "initial": initial,
        "required_openblas_core": required_openblas_core,
        "source_sha256": {name: digest(data) for name, data in contents.items()},
        "inputs": input_fingerprints(arrays),
        "driver_sha256": digest(driver),
        "julia_probe_sha256": digest(JULIA_SOURCE.encode()),
        "runs": [],
    }
    _write_json(output / "report.json", report)
    try:
        for index in (1, 2):
            directory = output / f"run-{index}"
            directory.mkdir()
            record = {"directory": directory.name, "status": "running"}
            report["runs"].append(record)
            _write_json(output / "report.json", report)
            print(f"Starting fixed-tree probe {index}/2.", flush=True)
            command = [
                sys.executable,
                str(ROOT / "scripts" / "run_python.py"),
                str(output / "driver.py"),
            ]
            if required_openblas_core:
                command.extend(["--require-openblas-core", required_openblas_core])
            command.extend(["--worker", str(directory)])
            with (directory / "worker.log").open("w") as log:
                completed = _run_worker(command, stdout=log)
            if completed.returncode:
                print((directory / "worker.log").read_text()[-8000:], file=sys.stderr)
                raise RuntimeError(
                    f"Fixed-tree worker failed; see {directory / 'worker.log'}"
                )
            result = read_json((directory / "result.json").read_bytes())
            if len(result["cases"]) != len(CASES):
                raise ValueError("A worker did not finish every diagnostic case.")
            if required_openblas_core:
                worker_metadata = read_json((directory / "metadata.json").read_bytes())
                if worker_metadata["phase"] != "completed":
                    raise ValueError(
                        "The controlled worker did not complete its checks."
                    )
                for phase in ("before", "after"):
                    verify_blas_control(
                        worker_metadata[phase]["environment"],
                        required_openblas_core,
                        require_julia=True,
                    )
                print(
                    "Verified OpenBLAS: Haswell for NumPy, SciPy and Julia; pool limits 1.",
                    flush=True,
                )
            record["status"] = "completed"
            if source_snapshot(source)[0] != contents:
                raise ValueError("Source artifacts changed during the probe.")
        first, second = [
            read_json((output / f"run-{i}" / "result.json").read_bytes())
            for i in (1, 2)
        ]
        final = metadata()
        if any(
            final[key] != initial[key]
            for key in ("provenance", "adapter_source_sha256")
        ):
            raise ValueError("The runtime source files changed during the probe.")
        report.update(status="completed", local_results_bitwise_equal=first == second)
    except BaseException as error:
        if report["runs"] and report["runs"][-1]["status"] == "running":
            report["runs"][-1]["status"] = "failed"
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        report["finished_at_utc"] = _utc_now()
        report["final"] = metadata()
        _write_json(output / "report.json", report)
        _write_json(
            output / "checksums.json",
            {
                path.relative_to(output).as_posix(): digest(path.read_bytes())
                for path in sorted(output.rglob("*"))
                if path.is_file() and path != output / "checksums.json"
            },
        )
    print(
        f"Completed; local result identity: {report['local_results_bitwise_equal']}",
        flush=True,
    )
    print(f"Report: {output / 'report.json'}", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="?")
    parser.add_argument("--label")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-openblas-core", choices=("Haswell",))
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, required_openblas_core=args.require_openblas_core)
    elif args.source and args.label and args.output:
        probe(
            args.source,
            args.output,
            label=args.label,
            required_openblas_core=args.require_openblas_core,
        )
    else:
        parser.error("source, --label and --output are required")


if __name__ == "__main__":
    main()
