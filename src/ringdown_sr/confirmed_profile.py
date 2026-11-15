"""Opt-in R-profile members with bound full-window objectives and strict replay."""

import ast
import csv
import importlib
import io
import math
import os
import resource
import subprocess
import sys
import time
import tomllib
from dataclasses import asdict
from pathlib import Path

import numpy as np

from . import assessment_sources as sources
from . import symbolic
from . import time_budget_profile as native
from .constant_diagnostic import backend_seed
from .losses import CovarianceLoss
from .parameter_export import _node_count
from .pilot import _json_bytes, _provenance, _sha256, _write_json
from .prediction_reference import PLAN as PREDICTION_PLAN
from .prediction_reference import verify_prediction
from .representation_profiles import plugin_field_record, plugin_records
from .structure import _validated_tree

ROOT = symbolic.ROOT
FORMAT = "ringdown-sr-confirmed-member-1"
NOISE_TECHNICAL_FORMAT = "ringdown-sr-noise-technical-member-1"
NOISE_TECHNICAL_ITERATIONS = 10
NOISE_PLAN = "docs/noise_pilot_plan.md"
NOISE_PLAN_SHA256 = "2a8e521b7729a668832ca02b0c8dd587d46ddec4010d7657d71e7b4d4d295fb8"
PROFILE = "r4x1000-local300x5-v1"
WORKER_LIMIT_SECONDS = 1800
NATIVE_FILES = (
    "RingdownSRLoss.jl",
    "RingdownSRSearch.jl",
    "RepresentationProfiles.jl",
    "FreeOptimizerBudget.jl",
    "TrigonometricGrammar.jl",
    "LocalOptimizerBudget.jl",
    "SearchTimeBudget.jl",
    "SearchBudgetClock.jl",
)
SOURCE_FILES = (
    "scripts/run_python.py",
    "scripts/run_confirmed_worker.py",
    "scripts/check_confirmed_profile.py",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    "src/ringdown_sr/juliapkg.json",
    "julia/Project.toml",
    "julia/Manifest.toml",
    "julia/test/confirmed_profile.jl",
    native.PLAN,
    native.CONFIGURATION,
    PREDICTION_PLAN,
    *("julia/src/" + name for name in NATIVE_FILES),
)
PREPARED_FILES = ("request.json", "inputs.npz", "metadata_initial.json", *NATIVE_FILES)
COST_FIELDS = (
    "worker_wall_seconds",
    "fit_wall_seconds",
    "cpu_user_seconds",
    "cpu_system_seconds",
    "callback_calls_during_fit",
    "adapter_call_wall_seconds",
)
NUMERICAL_ERRORS = (
    "FloatingPointError:",
    "OverflowError:",
    "ZeroDivisionError:",
    "MemoryError:",
    "JuliaError: DomainError with ",
    "JuliaError: OverflowError:",
    "JuliaError: OutOfMemoryError()",
    "JuliaError: InexactError:",
)
UNUSABLE_FRONT_ERRORS = {
    "ValueError: No admissible candidates were exported.",
    "ValueError: Candidate losses must be finite and nonnegative.",
}


def read(directory, name):
    return sources.read_json((Path(directory) / name).read_bytes())


def source_hashes(*, request=None):
    """Bind every imported package source and every script reachable by guards."""
    names = {*SOURCE_FILES}
    if request is not None:
        checked_request(request)
        if request["format"] == NOISE_TECHNICAL_FORMAT:
            raw = (ROOT / NOISE_PLAN).read_bytes()
            if _sha256(raw) != NOISE_PLAN_SHA256:
                raise ValueError("Changed frozen noise-pilot technical plan.")
            names.add(NOISE_PLAN)
    names.update(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src/ringdown_sr").glob("*.py")
    )
    names.update(
        path.relative_to(ROOT).as_posix() for path in (ROOT / "scripts").glob("*.py")
    )
    return {name: _sha256((ROOT / name).read_bytes()) for name in sorted(names)}


def checked_request(document):
    if (
        not isinstance(document, dict)
        or set(document) != {"format", "profile", "seed", "technical", "budget"}
        or document["format"] not in (FORMAT, NOISE_TECHNICAL_FORMAT)
        or document["profile"] != PROFILE
        or type(document["technical"]) is not bool
        or type(document["seed"]) is not int
        or not 0 < document["seed"] < 2**31
    ):
        raise ValueError("Invalid confirmed-profile request.")
    noise_technical = document["format"] == NOISE_TECHNICAL_FORMAT
    if noise_technical and not document["technical"]:
        raise ValueError("Noise-pilot technical format cannot request science.")
    expected = symbolic.SearchBudget(
        seed=document["seed"],
        niterations=NOISE_TECHNICAL_ITERATIONS
        if noise_technical
        else 1
        if document["technical"]
        else 1000,
    )
    symbolic.SearchBudget(**document["budget"])
    if _json_bytes(document["budget"]) != _json_bytes(asdict(expected)):
        raise ValueError("Changed confirmed-profile search budget.")
    return expected


def parameters(budget):
    return {**native.profile_parameters(budget, "iterations"), "should_simplify": False}


def checked_environment(environment):
    """Verify loaded BLAS roles and pinned scientific package versions."""
    from .seed_driver_crosscheck import environment_key

    probe = native.load_module(
        ROOT / "scripts/probe_symbolic_numerics.py", "confirmed_blas_probe"
    )
    blas = probe.verify_blas_control(environment, "Haswell", require_julia=True)
    if (
        environment.get("python_version")
        != (ROOT / ".python-version").read_text().strip()
        or environment.get("python_implementation") != "CPython"
        or environment.get("array_dtype") != "float64"
        or environment.get("julia_used") is not True
        or environment.get("thread_environment")
        != {
            key: "1"
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        }
    ):
        raise ValueError("Changed confirmed-worker Python/thread environment.")
    pinned = {
        entry["name"]: entry.get("version")
        for entry in tomllib.loads((ROOT / "uv.lock").read_text())["package"]
    }
    packages = {
        name.lower(): version for name, version in environment["packages"].items()
    }
    for name in (
        "numpy",
        "scipy",
        "pysr",
        "juliacall",
        "gmpy2",
        "sympy",
        "threadpoolctl",
    ):
        if packages.get(name) != pinned.get(name) or not pinned.get(name):
            raise ValueError("Changed confirmed-worker scientific package: " + name)
    return environment_key(environment), blas


def numerical_environment(metadata, runtime, *, completed):
    if runtime is None or metadata.get("environment", {}).get("julia_used") is not True:
        if completed or metadata.get("failed_during", metadata.get("phase")) in {
            "fit",
            "replay",
            "success",
        }:
            raise ValueError("Missing actual fitted-worker numerical environment.")
        return None
    before, blas = checked_environment(metadata["environment"])
    if _json_bytes(metadata.get("confirmed_blas_control")) != _json_bytes(blas):
        raise ValueError("Changed actual worker BLAS evidence.")
    julia_version = tomllib.loads((ROOT / "julia/Manifest.toml").read_text())[
        "julia_version"
    ]
    if (
        metadata.get("julia_version") != julia_version
        or metadata.get("symbolic_regression_version") != "2.5.1"
    ):
        raise ValueError("Changed actual native package versions.")
    if completed:
        after, after_blas = checked_environment(metadata["environment_after_search"])
        if _json_bytes(before) != _json_bytes(after) or _json_bytes(
            metadata.get("confirmed_blas_control_after")
        ) != _json_bytes(after_blas):
            raise ValueError("Numerical environment changed during confirmed fit.")
    return {
        "runtime": runtime,
        "environment": before,
        "julia_version": julia_version,
        "symbolic_regression_version": "2.5.1",
    }


def prepared_files(directory):
    return {
        name: (Path(directory) / name).read_bytes()
        for name in (*PREPARED_FILES, "prepared.json")
    }


def _inventory(directory):
    files = {}
    for path in sorted(Path(directory).rglob("*")):
        if path.is_symlink():
            raise ValueError("Confirmed-member artifacts must not be symlinks.")
        if path.is_file() and path.name != "member_checksums.json":
            files[path.relative_to(directory).as_posix()] = _sha256(path.read_bytes())
    return files


def prepare_member(
    directory, time_s, observed, *, covariance=None, seed, technical=False
):
    directory = Path(directory)
    request = {
        "format": FORMAT,
        "profile": PROFILE,
        "seed": seed,
        "technical": technical,
        "budget": asdict(
            symbolic.SearchBudget(seed=seed, niterations=1 if technical else 1000)
        ),
    }
    return _prepare_member(directory, time_s, observed, covariance, request)


def prepare_noise_technical_member(
    directory, time_s, observed, *, covariance=None, seed
):
    """Prepare only the separately versioned ten-iteration noise-pilot probe."""
    request = {
        "format": NOISE_TECHNICAL_FORMAT,
        "profile": PROFILE,
        "seed": seed,
        "technical": True,
        "budget": asdict(
            symbolic.SearchBudget(seed=seed, niterations=NOISE_TECHNICAL_ITERATIONS)
        ),
    }
    return _prepare_member(directory, time_s, observed, covariance, request)


def _prepare_member(directory, time_s, observed, covariance, request):
    directory = Path(directory)
    checked_request(request)
    bound_sources = source_hashes(request=request)
    times, target, matrix = symbolic._inputs(time_s, observed, covariance)
    arrays = {"time_s": times, "observed": target}
    if matrix is not None:
        arrays["covariance"] = matrix
    directory.mkdir(parents=True, exist_ok=False)
    np.savez(directory / "inputs.npz", **arrays)
    _write_json(directory / "request.json", request)
    initial = symbolic._initial_metadata()
    initial.update(format=request["format"], adapter_source_sha256=bound_sources)
    _write_json(directory / "metadata_initial.json", initial)
    _write_json(directory / "metadata.json", initial)
    for name in NATIVE_FILES:
        (directory / name).write_bytes((ROOT / "julia/src" / name).read_bytes())
    manifest = {
        "format": request["format"],
        "sources": bound_sources,
        "provenance": initial["provenance"],
        "input_fingerprints": {
            key: sources.fingerprint(value) for key, value in arrays.items()
        },
        "files": {
            name: _sha256((directory / name).read_bytes()) for name in PREPARED_FILES
        },
    }
    _write_json(directory / "prepared.json", manifest)
    return manifest


def verify_prepared(directory):
    directory = Path(directory)
    request = read(directory, "request.json")
    checked_request(request)
    manifest = read(directory, "prepared.json")
    if manifest.get("format") != request["format"] or manifest.get(
        "sources"
    ) != source_hashes(request=request):
        raise ValueError("Changed confirmed-profile source binding.")
    if set(manifest.get("files", {})) != set(PREPARED_FILES) or any(
        _sha256((directory / name).read_bytes()) != digest
        for name, digest in manifest["files"].items()
    ):
        raise ValueError("Changed confirmed-profile preparation.")
    with np.load(directory / "inputs.npz", allow_pickle=False) as saved:
        if set(saved.files) not in (
            {"time_s", "observed"},
            {"time_s", "observed", "covariance"},
        ):
            raise ValueError("Unexpected confirmed-profile input roles.")
        arrays = {key: saved[key].copy() for key in saved.files}
    if any(value.dtype != np.dtype("float64") for value in arrays.values()):
        raise ValueError("Confirmed-profile inputs must retain Float64 representation.")
    symbolic._inputs(arrays["time_s"], arrays["observed"], arrays.get("covariance"))
    if manifest["input_fingerprints"] != {
        key: sources.fingerprint(value) for key, value in arrays.items()
    }:
        raise ValueError("Changed confirmed-profile input bits.")
    initial = read(directory, "metadata_initial.json")
    if (
        initial.get("format") != request["format"]
        or initial.get("provenance") != manifest["provenance"]
        or initial.get("adapter_source_sha256") != manifest["sources"]
    ):
        raise ValueError("Unbound parent provenance.")
    return request, arrays, manifest


class WorkerHooks:
    """Explicit versioned hooks; legacy symbolic workers never construct these."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.request, self.arrays, self.manifest = verify_prepared(directory)
        self.module = self.original = self.guard = self.runtime = self.factor = None
        self.jl = None

    def read_request(self, document):
        if document != self.request:
            raise ValueError("Worker request changed before consumption.")
        return checked_request(document)

    parameters = staticmethod(parameters)
    prediction_replay = staticmethod(verify_prediction)

    @staticmethod
    def loss_replay(*args, **kwargs):
        from .weighted_replay import verify_loss_replay

        return verify_loss_replay(*args, **kwargs)

    def configure(self, jl, budget, matrix):
        self.jl = jl
        verify_prepared(self.directory)
        for name in NATIVE_FILES[2:]:
            jl.include(str(self.directory / name))
        jl.SearchTimeBudget.configure(
            "iterations", backend_seed(budget.seed), should_simplify=False
        )
        if matrix is not None:
            self.factor = np.asarray(
                jl.seval("Matrix(RingdownSRSearch.CONTEXT[]._factor)"), dtype=np.float64
            )
            np.savez(self.directory / "native_factor.npz", lower=self.factor)

    def before_fit(self, metadata, jl, budget):
        verify_prepared(self.directory)
        metadata["worker_adapter_source_sha256"] = source_hashes(request=self.request)
        _, metadata["confirmed_blas_control"] = checked_environment(
            metadata["environment"]
        )
        if metadata["worker_provenance"] != self.manifest["provenance"]:
            raise ValueError("Worker provenance differs from preparation.")
        self.runtime = native.checked_runtime(jl)
        _write_json(self.directory / "native_runtime.json", self.runtime)
        _write_json(
            self.directory / "backend_sources.json", native.checked_backend_sources(jl)
        )
        self.module = importlib.import_module("pysr.sr")
        self.original = self.module.SymbolicRegression
        self.guard = native.SearchInvocationGuard(self.original, budget.niterations)
        self.module.SymbolicRegression = self.guard
        jl.SearchBudgetClock.configure()

    def after_fit(self, jl, options, calls):
        if read(
            self.directory, "backend_sources.json"
        ) != native.checked_backend_sources(jl):
            raise ValueError("Actual native backend sources changed during fit.")
        if self.guard is None or self.module.SymbolicRegression is not self.guard:
            raise ValueError("Missing actual confirmed-profile invocation guard.")
        if self.runtime != native.checked_runtime(jl):
            raise ValueError("Native runtime changed during fit.")
        _write_json(self.directory / "search_invocation.json", self.guard.record())
        clock = jl.SearchBudgetClock.record()
        _write_json(
            self.directory / "search_clock.json",
            {str(key): getattr(clock, str(key)) for key in jl.keys(clock)},
        )
        record = jl.SearchTimeBudget.verification_record(options)
        _write_json(
            self.directory / "native_verification.json",
            {
                "status": str(record.status),
                "condition": str(record.condition),
                "backend_seed": int(record.backend_seed),
                "callback_calls_during_fit": calls,
                "plugins_field": plugin_field_record(record.plugins_field),
                "plugins": plugin_records(record.plugins),
                "optimizer_settings": {
                    str(x.name): str(x.value) for x in record.optimizer_settings
                },
            },
        )

    def candidate_arguments(self, jl, residual, covariance):
        if covariance is None:
            return {}
        from juliacall import convert

        vector = convert(jl.Vector[jl.Float64], residual)
        whitened = np.asarray(
            jl.seval("r -> RingdownSRSearch.CONTEXT[]._factor \\ r")(vector),
            dtype=np.float64,
        )
        return {
            "covariance": covariance,
            "native_factor": self.factor,
            "native_whitened": whitened,
        }

    @staticmethod
    def candidate_fields(extra, table_loss):
        return {
            "table_loss": table_loss,
            **(
                {"native_whitened_residual": extra["native_whitened"].tolist()}
                if extra
                else {}
            ),
        }

    def finish(self, metadata):
        if read(
            self.directory, "backend_sources.json"
        ) != native.checked_backend_sources(self.jl):
            raise ValueError("Actual native backend sources changed during replay.")
        _, metadata["confirmed_blas_control_after"] = checked_environment(
            metadata["environment_after_search"]
        )
        numerical_environment(metadata, self.runtime, completed=True)
        _write_json(self.directory / "metadata.json", metadata)
        verify_prepared(self.directory)
        if metadata.get("worker_provenance") != _provenance() or metadata.get(
            "worker_adapter_source_sha256"
        ) != source_hashes(request=self.request):
            raise ValueError("Confirmed-profile provenance changed during consumption.")

    def close(self):
        if self.module is not None:
            self.module.SymbolicRegression = self.original


def worker(directory):
    symbolic.worker(Path(directory).resolve(), hooks=WorkerHooks(directory))


def failure_status(metadata, *, timed_out=False):
    message = metadata.get("error")
    if message is not None:
        ordinary_fit = (
            metadata.get("failed_during") == "fit"
            and isinstance(message, str)
            and message.startswith(NUMERICAL_ERRORS)
        )
        unusable_front = (
            metadata.get("failed_during") == "replay"
            and message in UNUSABLE_FRONT_ERRORS
        )
        if not (ordinary_fit or unusable_front):
            raise ValueError("Unclassified worker failure or integrity violation.")
        return "timeout" if timed_out else "fit_error"
    if timed_out and metadata.get("phase") in {
        "before_worker_start",
        "worker_start",
        "fit",
        "replay",
    }:
        return "timeout"
    raise ValueError("Missing ordinary numerical failure evidence.")


def _verify_origin(metadata, initial, manifest, *, completed):
    if (
        metadata.get("provenance") != initial["provenance"]
        or metadata.get("adapter_source_sha256") != manifest["sources"]
        or (
            manifest.get("format") == NOISE_TECHNICAL_FORMAT
            and metadata.get("format") != NOISE_TECHNICAL_FORMAT
        )
    ):
        raise ValueError("Changed parent provenance or adapter.")
    phase = metadata.get("failed_during", metadata.get("phase"))
    for key, expected in (
        ("worker_provenance", initial["provenance"]),
        ("worker_adapter_source_sha256", manifest["sources"]),
    ):
        if (
            completed or phase in {"fit", "replay", "success"} or key in metadata
        ) and metadata.get(key) != expected:
            raise ValueError("Missing or contradictory actual worker provenance.")


def run_member(directory, *, deadline):
    directory = Path(directory).resolve()
    request, _, _ = verify_prepared(directory)
    started = time.monotonic()
    if not math.isfinite(deadline) or deadline <= started:
        raise TimeoutError("Confirmed-profile deadline expired before worker start.")
    environment = os.environ.copy()
    environment.update(native.JULIA_THREADS)
    environment.update(
        {
            name: "1"
            for name in (
                "OPENBLAS_NUM_THREADS",
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        }
    )
    environment["OPENBLAS_CORETYPE"] = "Haswell"
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    timed_out = False
    command = [
        sys.executable,
        str(ROOT / "scripts/run_python.py"),
        str(ROOT / "scripts/run_confirmed_worker.py"),
        str(directory),
    ]
    with (directory / "worker.log").open("wb") as log:
        process = subprocess.Popen(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=environment,
            start_new_session=True,
        )
        try:
            code = process.wait(
                timeout=min(WORKER_LIMIT_SECONDS, deadline - time.monotonic())
            )
        except subprocess.TimeoutExpired:
            timed_out = True
            symbolic._stop_worker(process)
            code = process.returncode
        except BaseException:
            symbolic._stop_worker(process)
            raise
    elapsed = time.monotonic() - started
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    metadata = read(directory, "metadata.json")
    if code == 0 and not timed_out:
        status = "completed"
    else:
        if not timed_out and (type(code) is not int or code <= 0):
            raise ValueError("Confirmed-profile worker interrupted by signal.")
        status = failure_status(metadata, timed_out=timed_out)
    outcome = {
        "format": request["format"],
        "status": status,
        "returncode": code,
        "timed_out": timed_out,
        "worker_wall_seconds": elapsed,
        "adapter_call_wall_seconds": elapsed,
        # Killing the launcher's process group can orphan an unreaped worker;
        # RUSAGE_CHILDREN then cannot certify that worker's accumulated CPU.
        "cpu_user_seconds": None if timed_out else after.ru_utime - before.ru_utime,
        "cpu_system_seconds": None if timed_out else after.ru_stime - before.ru_stime,
    }
    _write_json(directory / "outcome.json", outcome)
    _write_json(
        directory / "member_checksums.json",
        _inventory(directory),
    )
    return verify_member(directory)


def _verify_options(directory, request):
    record = read(directory, "native_verification.json")
    record["backend_options"] = read(directory, "backend_options.json")
    base = native.load_module(
        ROOT / "scripts/run_noiseless_control.py", "confirmed_policy"
    )
    native.verify_options(
        record, request["seed"], "iterations", base, base.load_support()
    )
    saved = read(directory, "pysr_parameters.json")
    expected = parameters(checked_request(request))
    if any(
        _json_bytes(saved.get(key)) != _json_bytes(value)
        for key, value in expected.items()
    ):
        raise ValueError("Changed effective confirmed-profile PySR options.")
    if record.get("status") != "verified":
        raise ValueError("Missing native profile verification.")
    return record


def _native_completion(directory, request):
    budget = checked_request(request)
    if _json_bytes(read(directory, "search_invocation.json")) != _json_bytes(
        native.invocation_record(budget.niterations)
    ):
        raise ValueError("Changed actual equation_search invocation.")
    clock = read(directory, "search_clock.json")
    if any(
        type(clock.get(key)) is not type(value) or clock[key] != value
        for key, value in {
            "requested_iterations": budget.niterations,
            "populations": 2,
            "processed_population_cycles": 2 * budget.niterations,
            "completed_outer_rounds": budget.niterations,
            "residual_population_cycles": 0,
            "iteration_limit_reached": True,
            "timeout_reached": False,
            "technical_counter_stop": False,
        }.items()
    ):
        raise ValueError("Unfinished or changed native iteration budget.")
    for key in (
        "main_loop_call_wall_seconds",
        "elapsed_at_last_check_seconds",
        "monotonic_to_last_check_seconds",
    ):
        if (
            type(clock.get(key)) not in (int, float)
            or not math.isfinite(clock[key])
            or clock[key] < 0
        ):
            raise ValueError("Invalid native clock evidence.")
    if (
        type(clock.get("checks")) is not int
        or clock["checks"] <= 0
        or not abs(clock.get("clock_difference_seconds", math.inf)) <= 1
    ):
        raise ValueError("Invalid native stop-clock evidence.")
    record = _verify_options(directory, request)
    return record


def verify_front(directory, candidates):
    """Bind every exported row to the final native front without deserialization."""
    raw = (Path(directory) / "pysr/search/hall_of_fame.csv").read_text(encoding="utf-8")
    table = csv.DictReader(io.StringIO(raw), strict=True)
    if table.fieldnames != ["Complexity", "Loss", "Equation"]:
        raise ValueError("Changed native hall-of-fame table contract.")
    rows = list(table)
    if len(rows) != len(candidates):
        raise ValueError(
            "Exported candidate inventory differs from the native end front."
        )
    for candidate, row in zip(candidates, rows, strict=True):
        _validated_tree(candidate["tree"])
        if (
            set(row) != {"Complexity", "Loss", "Equation"}
            or type(candidate.get("complexity")) is not int
            or candidate["complexity"] != _node_count(candidate["tree"])
            or row["Complexity"] != str(candidate["complexity"])
            or type(candidate.get("loss")) not in (int, float)
            or not math.isfinite(candidate["loss"])
            or candidate["loss"] < 0
            or float(row["Loss"]).hex() != float(candidate["loss"]).hex()
            or row["Equation"] != candidate.get("display_equation")
            or _json_bytes(equation_tree(row["Equation"]))
            != _json_bytes(candidate["tree"])
        ):
            raise ValueError(
                "Exported loss, equation or complexity differs from the native end front."
            )


def equation_tree(equation):
    """Read only the bounded native display grammar; never evaluate source text."""
    if type(equation) is not str or len(equation) > 4096:
        raise ValueError("Invalid native equation length.")
    try:
        root = ast.parse(equation, mode="eval").body
    except (SyntaxError, ValueError, RecursionError) as error:
        raise ValueError("Invalid native equation syntax.") from error
    count = 0
    binary = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}

    def number(node, sign=1):
        if not isinstance(node, ast.Constant) or type(node.value) not in (int, float):
            raise ValueError("Only numeric constants may have a unary sign.")
        value = sign * float(node.value)
        if not math.isfinite(value):
            raise ValueError("Native constants must be finite Float64 values.")
        return {"kind": "constant", "value_hex": value.hex()}

    def visit(node):
        nonlocal count
        count += 1
        if count > 20:
            raise ValueError("Native equation exceeds the bound of 20 nodes.")
        if isinstance(node, ast.Constant):
            return number(node)
        if isinstance(node, ast.UnaryOp) and type(node.op) in {ast.UAdd, ast.USub}:
            return number(node.operand, -1 if isinstance(node.op, ast.USub) else 1)
        if isinstance(node, ast.Name) and node.id == "t":
            return {"kind": "variable", "index": 1}
        if isinstance(node, ast.BinOp) and type(node.op) in binary:
            operator = binary[type(node.op)]
            return {
                "kind": "operator",
                "arity": 2,
                "operator_index": symbolic.BINARY.index(operator) + 1,
                "operator": operator,
                "children": [visit(node.left), visit(node.right)],
            }
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in symbolic.UNARY
            and len(node.args) == 1
            and not node.keywords
        ):
            return {
                "kind": "operator",
                "arity": 1,
                "operator_index": symbolic.UNARY.index(node.func.id) + 1,
                "operator": node.func.id,
                "children": [visit(node.args[0])],
            }
        raise ValueError("Native equation contains an unsupported syntax node.")

    return visit(root)


def verify_member(directory):
    """Re-read the original member without importing Julia or performing a fit."""
    from .weighted_replay import candidate_evidence

    directory = Path(directory)
    request, arrays, manifest = verify_prepared(directory)
    hashes = read(directory, "member_checksums.json")
    actual = _inventory(directory)
    if hashes != actual:
        raise ValueError("Changed member file inventory or checksum.")
    outcome, metadata = (
        read(directory, "outcome.json"),
        read(directory, "metadata.json"),
    )
    if (
        set(outcome)
        != {
            "format",
            "status",
            "returncode",
            "timed_out",
            "worker_wall_seconds",
            "adapter_call_wall_seconds",
            "cpu_user_seconds",
            "cpu_system_seconds",
        }
        or outcome.get("format") != request["format"]
        or outcome.get("status") not in {"completed", "fit_error", "timeout"}
        or type(outcome.get("returncode")) is not int
        or type(outcome.get("timed_out")) is not bool
    ):
        raise ValueError("Invalid confirmed-member terminal outcome.")
    completed = outcome.get("status") == "completed"
    if not completed and outcome["status"] != failure_status(
        metadata, timed_out=outcome["timed_out"]
    ):
        raise ValueError("Changed numerical failure classification.")
    _verify_origin(
        metadata,
        read(directory, "metadata_initial.json"),
        manifest,
        completed=completed,
    )
    costs = {key: outcome.get(key) for key in COST_FIELDS}
    for key in (
        "worker_wall_seconds",
        "adapter_call_wall_seconds",
        "cpu_user_seconds",
        "cpu_system_seconds",
    ):
        if not completed and key.startswith("cpu_") and costs[key] is None:
            continue
        if (
            type(costs[key]) not in (int, float)
            or not math.isfinite(costs[key])
            or costs[key] < 0
        ):
            raise ValueError("Missing finite worker resource cost.")
    costs["fit_wall_seconds"] = metadata.get("fit_wall_seconds")
    if costs["fit_wall_seconds"] is not None and (
        type(costs["fit_wall_seconds"]) not in (int, float)
        or not math.isfinite(costs["fit_wall_seconds"])
        or costs["fit_wall_seconds"] < 0
    ):
        raise ValueError("Invalid observed fit wall cost.")
    runtime_path = directory / "native_runtime.json"
    runtime = read(directory, runtime_path.name) if runtime_path.exists() else None
    native_required = completed or metadata.get(
        "failed_during", metadata.get("phase")
    ) in {"fit", "replay", "success"}
    backend_path = directory / "backend_sources.json"
    if (native_required and (runtime is None or not backend_path.is_file())) or (
        backend_path.exists()
        and read(directory, backend_path.name)
        != native.configuration()["reviewed_backend_sources"]
    ):
        raise ValueError(
            "Missing or contradictory actual native runtime/source evidence."
        )
    if runtime is not None:
        native.validate_runtime(runtime)
    environment = numerical_environment(metadata, runtime, completed=completed)
    candidates, selected = [], None
    if completed:
        if (
            outcome.get("returncode") != 0
            or outcome.get("timed_out") is not False
            or metadata.get("phase") != "success"
        ):
            raise ValueError("Invalid completed worker status.")
        if (
            runtime is None
            or read(directory, "backend_sources.json")
            != native.configuration()["reviewed_backend_sources"]
        ):
            raise ValueError("Missing actual native runtime/source evidence.")
        record = _native_completion(directory, request)
        result = read(directory, "result.json")
        if (
            result.get("format") != symbolic.FORMAT
            or result.get("evaluation_scope") != "fitted_samples_only"
            or result.get("selection") != "minimum_training_loss_then_complexity"
            or type(result.get("selected_index")) is not int
        ):
            raise ValueError("Changed original candidate result contract.")
        candidates = result["candidates"]
        verify_front(directory, candidates)
        for candidate in candidates:
            if (
                type(candidate.get("loss")) not in (int, float)
                or type(candidate.get("complexity")) is not int
                or candidate["complexity"] <= 0
            ):
                raise ValueError("Invalid original candidate ordering fields.")
        selected = symbolic.select_candidate(candidates)
        if (
            selected != result["selected_index"]
            or result["rng"]["python_seed"] != request["seed"]
            or result["rng"]["backend_seed"] != backend_seed(request["seed"])
        ):
            raise ValueError("Changed original native candidate selection or seeds.")
        factor = None
        loss_object = None
        if "covariance" in arrays:
            loss_object = CovarianceLoss(arrays["covariance"])
            with np.load(directory / "native_factor.npz", allow_pickle=False) as saved:
                if saved.files != ["lower"] or saved["lower"].dtype != np.dtype(
                    "float64"
                ):
                    raise ValueError("Invalid native covariance factor artifact.")
                factor = saved["lower"].copy()
        for candidate in candidates:
            evidence = candidate_evidence(
                candidate,
                arrays["time_s"],
                arrays["observed"],
                arrays.get("covariance"),
                native_factor=factor,
                loss_object=loss_object,
            )
            proof = evidence["prediction_replay"]
            if (
                _json_bytes(evidence) != _json_bytes(candidate.get("loss_replay"))
                or _json_bytes(proof) != _json_bytes(candidate.get("prediction_replay"))
                or candidate.get("table_loss") != evidence["table_loss"]
                or not np.array_equal(
                    np.asarray(candidate["residual"]),
                    arrays["observed"] - np.asarray(candidate["prediction"]),
                )
            ):
                raise ValueError("Changed candidate replay evidence or residual.")
        calls = result.get("callback_calls_during_fit")
        if (
            type(calls) is not int
            or calls <= 0
            or record["callback_calls_during_fit"] != calls
        ):
            raise ValueError("Missing actual objective callback cost.")
        costs["callback_calls_during_fit"] = calls
        if (
            type(costs["fit_wall_seconds"]) not in (int, float)
            or not math.isfinite(costs["fit_wall_seconds"])
            or costs["fit_wall_seconds"] < 0
        ):
            raise ValueError("Missing completed fit wall cost.")
    else:
        if not outcome.get("timed_out") and (
            type(outcome.get("returncode")) is not int or outcome["returncode"] <= 0
        ):
            raise ValueError("Missing failed worker exit evidence.")
        if (directory / "result.json").exists():
            raise ValueError("Failed worker carries success evidence.")
        if (directory / "native_verification.json").exists():
            if (
                runtime is None
                or read(directory, "backend_sources.json")
                != native.configuration()["reviewed_backend_sources"]
            ):
                raise ValueError(
                    "Missing failed worker native runtime/source evidence."
                )
            record = _native_completion(directory, request)
            calls = record.get("callback_calls_during_fit")
            if type(calls) is not int or calls <= 0:
                raise ValueError("Invalid observed failed-worker callback cost.")
            costs["callback_calls_during_fit"] = calls
    verify_prepared(directory)
    if (
        _inventory(directory) != actual
        or read(directory, "member_checksums.json") != hashes
    ):
        raise ValueError("Member evidence changed during read-only verification.")
    return {
        **(
            {
                "format": NOISE_TECHNICAL_FORMAT,
                "requested_iterations": NOISE_TECHNICAL_ITERATIONS,
            }
            if request["format"] == NOISE_TECHNICAL_FORMAT
            else {}
        ),
        "status": outcome["status"],
        "selected_index": selected,
        "selected": None if selected is None else candidates[selected],
        "candidates": candidates,
        "costs": costs,
        "numerical_environment": environment,
        "provenance": manifest["provenance"],
        "seed": request["seed"],
        "technical": request["technical"],
        "profile": PROFILE,
        "input_fingerprints": manifest["input_fingerprints"],
    }
