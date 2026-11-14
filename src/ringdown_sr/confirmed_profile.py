"""Opt-in R-profile members with bound full-window objectives and strict replay."""

import importlib
import math
import os
import resource
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from . import assessment_sources as sources
from . import symbolic
from . import time_budget_profile as native
from .constant_diagnostic import backend_seed
from .losses import CovarianceLoss
from .pilot import _json_bytes, _provenance, _sha256, _write_json
from .prediction_reference import verify_prediction
from .representation_profiles import plugin_field_record, plugin_records

ROOT = symbolic.ROOT
FORMAT = "ringdown-sr-confirmed-member-1"
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


def source_hashes():
    """Bind every imported package source and every script reachable by guards."""
    names = {*SOURCE_FILES}
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
        or document["format"] != FORMAT
        or document["profile"] != PROFILE
        or type(document["technical"]) is not bool
        or type(document["seed"]) is not int
        or not 0 < document["seed"] < 2**31
    ):
        raise ValueError("Invalid confirmed-profile request.")
    expected = symbolic.SearchBudget(
        seed=document["seed"], niterations=1 if document["technical"] else 1000
    )
    symbolic.SearchBudget(**document["budget"])
    if _json_bytes(document["budget"]) != _json_bytes(asdict(expected)):
        raise ValueError("Changed confirmed-profile search budget.")
    return expected


def parameters(budget):
    return {**native.profile_parameters(budget, "iterations"), "should_simplify": False}


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
    checked_request(request)
    times, target, matrix = symbolic._inputs(time_s, observed, covariance)
    arrays = {"time_s": times, "observed": target}
    if matrix is not None:
        arrays["covariance"] = matrix
    directory.mkdir(parents=True, exist_ok=False)
    np.savez(directory / "inputs.npz", **arrays)
    _write_json(directory / "request.json", request)
    initial = symbolic._initial_metadata()
    initial.update(format=FORMAT, adapter_source_sha256=source_hashes())
    _write_json(directory / "metadata_initial.json", initial)
    _write_json(directory / "metadata.json", initial)
    for name in NATIVE_FILES:
        (directory / name).write_bytes((ROOT / "julia/src" / name).read_bytes())
    manifest = {
        "format": FORMAT,
        "sources": source_hashes(),
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
    manifest = read(directory, "prepared.json")
    if manifest.get("format") != FORMAT or manifest.get("sources") != source_hashes():
        raise ValueError("Changed confirmed-profile source binding.")
    if set(manifest.get("files", {})) != set(PREPARED_FILES) or any(
        _sha256((directory / name).read_bytes()) != digest
        for name, digest in manifest["files"].items()
    ):
        raise ValueError("Changed confirmed-profile preparation.")
    request = read(directory, "request.json")
    checked_request(request)
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
        initial.get("provenance") != manifest["provenance"]
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
        metadata["worker_adapter_source_sha256"] = source_hashes()
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
        verify_prepared(self.directory)
        if (
            metadata.get("worker_provenance") != _provenance()
            or metadata.get("worker_adapter_source_sha256") != source_hashes()
        ):
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
    verify_prepared(directory)
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
        "format": FORMAT,
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
        or outcome.get("format") != FORMAT
        or outcome.get("status") not in {"completed", "fit_error", "timeout"}
        or type(outcome.get("returncode")) is not int
        or type(outcome.get("timed_out")) is not bool
    ):
        raise ValueError("Invalid confirmed-member terminal outcome.")
    completed = outcome.get("status") == "completed"
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
    if runtime is not None:
        native.validate_runtime(runtime)
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
        if outcome.get("status") != failure_status(
            metadata, timed_out=outcome.get("timed_out") is True
        ):
            raise ValueError("Changed numerical failure classification.")
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
        "status": outcome["status"],
        "selected_index": selected,
        "selected": None if selected is None else candidates[selected],
        "candidates": candidates,
        "costs": costs,
        "numerical_environment": runtime,
        "provenance": manifest["provenance"],
        "seed": request["seed"],
        "technical": request["technical"],
        "profile": PROFILE,
        "input_fingerprints": manifest["input_fingerprints"],
    }
