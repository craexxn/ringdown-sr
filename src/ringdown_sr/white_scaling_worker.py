"""Isolated three-arm white-noise scaling workers with unchanged search policy."""

import copy
import importlib
import math
import os
import resource
import subprocess
import sys
import time
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path

import numpy as np

from . import assessment_sources as sources
from . import confirmed_profile as confirmed
from . import symbolic, weighted_replay
from . import time_budget_profile as native
from .constant_diagnostic import backend_seed
from .losses import CovarianceLoss, mean_squared_error
from .pilot import _json_bytes, _provenance, _sha256, _write_json
from .prediction_reference import verify_prediction
from .representation_profiles import plugin_field_record, plugin_records

ROOT = symbolic.ROOT
FORMAT = "ringdown-sr-white-scaling-member-1"
PROFILE = "white-scaling-local300x5-outer100-v1"
OBJECTIVE = "Main.WhiteLossScaling.objective"
ARMS = ("ordinary", "scaled", "covariance")
NATIVE_FILES = (*confirmed.NATIVE_FILES, "WhiteLossScaling.jl")
PREPARED_FILES = ("request.json", "inputs.npz", "metadata_initial.json", *NATIVE_FILES)
WORKER_LIMIT_SECONDS = 1800
PLAN = "docs/white_loss_scaling_plan.md"
PLAN_SHA256 = "3daa4d9c7701a8a99f841a5dc27cc3a7ae3cdbcbde1bbc8cd3f51eef2f202378"
MECHANISM_SOURCES = {
    "ConstantOptimization.jl": "6f80e48282e2f2d1c6b5834b35c7e1b06d1d1420c1a3acf6ada0dbc68c2ade0c",
    "LossFunctions.jl": "a428146c8fdbd0fda60b5b5b0f2a67ef2d81b920e840ae4d2bf09064480a4e2d",
}


def checked_mechanism_sources(jl):
    """Hash the actual loaded pinned package, including both mechanism sources."""
    directory = Path(str(jl.seval("dirname(pathof(SymbolicRegression))")))
    actual = {
        name: _sha256((directory / name).read_bytes()) for name in MECHANISM_SOURCES
    }
    if actual != MECHANISM_SOURCES:
        raise ValueError("Changed pinned scaling-mechanism backend sources.")
    return actual


def checked_request(document):
    """Reject scope, representation and budget changes before Julia starts."""
    if (
        not isinstance(document, dict)
        or set(document)
        != {"format", "profile", "arm", "sigma_hex", "scale_hex", "technical", "budget"}
        or document["format"] != FORMAT
        or document["profile"] != PROFILE
        or document["arm"] not in ARMS
        or type(document["technical"]) is not bool
        or type(document["sigma_hex"]) is not str
        or type(document["scale_hex"]) is not str
    ):
        raise ValueError("Invalid white-scaling worker request.")
    try:
        sigma = float.fromhex(document["sigma_hex"])
        scale = 1.0 / (sigma * sigma)
    except (ValueError, OverflowError, ZeroDivisionError) as error:
        raise ValueError("Invalid white-noise scale.") from error
    if (
        not math.isfinite(sigma)
        or sigma <= 0
        or sigma.hex() != document["sigma_hex"]
        or not math.isfinite(scale)
        or scale <= 0
        or scale.hex() != document["scale_hex"]
    ):
        raise ValueError("White-noise sigma and exact scale disagree.")
    budget = symbolic.SearchBudget(**document["budget"])
    if (
        not 0 < budget.seed < 2**31
        or budget.niterations not in ((2, 10) if document["technical"] else (100,))
        or _json_bytes(asdict(budget))
        != _json_bytes(
            asdict(
                symbolic.SearchBudget(seed=budget.seed, niterations=budget.niterations)
            )
        )
    ):
        raise ValueError("Changed white-scaling search budget.")
    return budget


def parameters(budget):
    return {**confirmed.parameters(budget), "loss_function": OBJECTIVE}


def source_hashes():
    """Bind transitive Python code and the new native objective separately."""
    if _sha256((ROOT / PLAN).read_bytes()) != PLAN_SHA256:
        raise ValueError("Changed frozen white-scaling plan.")
    hashes = confirmed.source_hashes()
    for name in ("julia/src/WhiteLossScaling.jl", PLAN):
        hashes[name] = _sha256((ROOT / name).read_bytes())
    return dict(sorted(hashes.items()))


def prepare_member(
    directory, time_s, observed, *, arm, sigma, seed, technical=False, niterations=None
):
    """Prepare a new directory; no scientific data or truth is generated here."""
    iterations = (10 if technical else 100) if niterations is None else niterations
    sigma = float(sigma)
    request = {
        "format": FORMAT,
        "profile": PROFILE,
        "arm": arm,
        "sigma_hex": sigma.hex(),
        "scale_hex": (1.0 / (sigma * sigma)).hex(),
        "technical": technical,
        "budget": asdict(symbolic.SearchBudget(seed=seed, niterations=iterations)),
    }
    checked_request(request)
    covariance = (
        np.eye(len(time_s), dtype=np.float64) * (sigma * sigma)
        if arm == "covariance"
        else None
    )
    times, target, matrix = symbolic._inputs(time_s, observed, covariance)
    arrays = {"time_s": times, "observed": target}
    if matrix is not None:
        arrays["covariance"] = matrix
    bound_sources = source_hashes()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    np.savez(directory / "inputs.npz", **arrays)
    _write_json(directory / "request.json", request)
    initial = symbolic._initial_metadata()
    initial.update(format=FORMAT, adapter_source_sha256=bound_sources)
    _write_json(directory / "metadata_initial.json", initial)
    _write_json(directory / "metadata.json", initial)
    for name in NATIVE_FILES:
        (directory / name).write_bytes((ROOT / "julia/src" / name).read_bytes())
    manifest = {
        "format": FORMAT,
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
    if directory.is_symlink():
        raise ValueError("Worker directory cannot be a symlink.")
    request = confirmed.read(directory, "request.json")
    checked_request(request)
    manifest = confirmed.read(directory, "prepared.json")
    if (
        manifest.get("format") != FORMAT
        or manifest.get("sources") != source_hashes()
        or set(manifest.get("files", {})) != set(PREPARED_FILES)
        or any(
            (directory / name).is_symlink()
            or _sha256((directory / name).read_bytes()) != digest
            for name, digest in manifest["files"].items()
        )
    ):
        raise ValueError("Changed white-scaling source or preparation.")
    with np.load(directory / "inputs.npz", allow_pickle=False) as saved:
        expected = {"time_s", "observed"}
        if request["arm"] == "covariance":
            expected.add("covariance")
        if set(saved.files) != expected:
            raise ValueError("Wrong white-scaling input roles.")
        arrays = {name: saved[name].copy() for name in saved.files}
    if any(value.dtype != np.dtype("float64") for value in arrays.values()):
        raise ValueError("White-scaling inputs must retain Float64 bits.")
    symbolic._inputs(arrays["time_s"], arrays["observed"], arrays.get("covariance"))
    sigma = float.fromhex(request["sigma_hex"])
    if "covariance" in arrays and not np.array_equal(
        arrays["covariance"], np.eye(len(arrays["time_s"])) * (sigma * sigma)
    ):
        raise ValueError("The covariance must be exactly sigma squared times identity.")
    if manifest["input_fingerprints"] != {
        key: sources.fingerprint(value) for key, value in arrays.items()
    }:
        raise ValueError("Changed white-scaling input bits.")
    initial = confirmed.read(directory, "metadata_initial.json")
    if (
        initial.get("format") != FORMAT
        or initial.get("provenance") != manifest["provenance"]
        or initial.get("adapter_source_sha256") != manifest["sources"]
    ):
        raise ValueError("Unbound white-scaling parent provenance.")
    return request, arrays, manifest


def loss_evidence(request, *args, **kwargs):
    """Keep base replay fields literal and certify the declared scalar transform."""
    if request["arm"] != "scaled":
        return weighted_replay.verify_loss_replay(*args, **kwargs)
    (
        observed,
        native_prediction,
        python_prediction,
        raw,
        replay,
        table,
        python_loss,
        loss_object,
    ) = args
    if loss_object is not None:
        raise ValueError("Scaled MSE cannot carry a covariance object.")
    scale = float.fromhex(request["scale_hex"])
    if float(raw).hex() != float(scale * replay).hex():
        raise ValueError(
            "Native scaled loss differs from the declared Float64 multiplication."
        )
    np.testing.assert_allclose(table, raw, rtol=1e-10, atol=0)
    base = weighted_replay.verify_loss_replay(
        observed,
        native_prediction,
        python_prediction,
        replay,
        replay,
        replay,
        python_loss,
        None,
        **kwargs,
    )
    return {
        "format": "ringdown-sr-scaled-mse-replay-1",
        "status": "passed",
        "metric": "mse_times_inverse_sigma_squared",
        "scale_hex": request["scale_hex"],
        "table_loss": float(table),
        "raw_objective_loss": float(raw),
        "base_native_mse": float(replay),
        "base_python_mse": float(python_loss),
        "scaled_python_loss": float(scale * python_loss),
        "prediction_replay": kwargs["prediction_check"],
        "base_mse_evidence": base,
    }


def candidate_fields(request, extra, table_loss):
    return {
        **confirmed.WorkerHooks.candidate_fields(extra, table_loss),
        "loss_metric": "ordinary_mse"
        if request["arm"] == "ordinary"
        else "mse_over_sigma_squared",
        "reimport_and_python_loss_metric": "covariance_q_over_n"
        if request["arm"] == "covariance"
        else "ordinary_mse",
        "objective_multiplier_hex": request["scale_hex"]
        if request["arm"] == "scaled"
        else (1.0).hex(),
    }


def verify_normalization(request, observed, result, *, native_factor=None):
    """Check the pinned zero-expression baseline against an exact rational sum.

    The native reduction is norm(r)/sqrt(N), squared. Its existing rational
    reduction envelope is extended only for the declared scalar multiplication
    or scalar whitening by the recorded diagonal Cholesky factor. A diagonal
    solve may use either division or a reciprocal followed by multiplication;
    two rounded operations before squaring cover both implementations. No
    unit-sized absolute tolerance or clean signal enters this check.
    """
    values = np.asarray(observed, dtype=np.float64)
    if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("Invalid normalization input vector.")
    for value in values:
        weighted_replay.duration_replay._normal_or_zero(float(value))
        weighted_replay.duration_replay._normal_or_zero(float(value * value))
    u = Fraction(1, 2**53)
    lower, upper = weighted_replay._reduction_bounds(values.size)
    reference = sum((Fraction(float(x)) ** 2 for x in values), Fraction()) / values.size
    if request["arm"] == "scaled":
        reference *= Fraction(float.fromhex(request["scale_hex"]))
        lower *= 1 - u
        upper *= 1 + u
    elif request["arm"] == "covariance":
        sigma = float.fromhex(request["sigma_hex"])
        diagonal = float(np.sqrt(sigma * sigma))
        expected = np.eye(values.size) * diagonal
        if native_factor is None or not np.array_equal(native_factor, expected):
            raise ValueError("Changed exact diagonal native factor.")
        reference /= Fraction(diagonal) ** 2
        lower *= (1 - u) ** 4
        upper *= (1 + u) ** 4
    elif native_factor is not None:
        raise ValueError("MSE normalization must not carry a native factor.")
    baseline, zero = result.get("baseline_loss"), result.get("zero_expression_loss")
    if (
        type(baseline) not in (int, float)
        or type(zero) not in (int, float)
        or not math.isfinite(baseline)
        or not math.isfinite(zero)
        or baseline < 0
        or float(baseline).hex() != float(zero).hex()
        or result.get("zero_expression_loss_status") != "finite"
        or result.get("use_baseline") is not True
        or not lower * reference <= Fraction(float(zero)) <= upper * reference
    ):
        raise ValueError(
            "Baseline loss disagrees with the independent zero-expression reference."
        )
    expected_normalization = max(float(baseline), 0.01)
    normalization = result.get("cost_normalization")
    if (
        type(normalization) not in (int, float)
        or float(normalization).hex() != expected_normalization.hex()
    ):
        raise ValueError("Changed effective baseline normalization or floor.")
    return {
        "status": "passed",
        "baseline_tree": "constant_zero",
        "baseline_floor": 0.01,
        "floor_active": baseline < 0.01,
        "reference": weighted_replay._fraction_record(reference),
        "relative_lower": weighted_replay._fraction_record(lower),
        "relative_upper": weighted_replay._fraction_record(upper),
    }


class WorkerHooks(confirmed.WorkerHooks):
    """Opt-in hooks; no historical worker or result contract is rewritten."""

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

    def configure(self, jl, budget, matrix):
        self.jl = jl
        verify_prepared(self.directory)
        for name in NATIVE_FILES[2:]:
            jl.include(str(self.directory / name))
        jl.WhiteLossScaling.configure(
            self.request["arm"],
            float.fromhex(self.request["sigma_hex"]),
            backend_seed(budget.seed),
        )
        if matrix is not None:
            self.factor = np.asarray(
                jl.seval("Matrix(RingdownSRSearch.CONTEXT[]._factor)"), dtype=np.float64
            )
            np.savez(self.directory / "native_factor.npz", lower=self.factor)

    def before_fit(self, metadata, jl, budget):
        verify_prepared(self.directory)
        metadata["worker_adapter_source_sha256"] = source_hashes()
        _, metadata["confirmed_blas_control"] = confirmed.checked_environment(
            metadata["environment"]
        )
        if metadata["worker_provenance"] != self.manifest["provenance"]:
            raise ValueError("Worker provenance differs from preparation.")
        self.runtime = native.checked_runtime(jl)
        _write_json(self.directory / "native_runtime.json", self.runtime)
        _write_json(
            self.directory / "backend_sources.json", native.checked_backend_sources(jl)
        )
        _write_json(
            self.directory / "mechanism_sources.json", checked_mechanism_sources(jl)
        )
        self.module = importlib.import_module("pysr.sr")
        self.original = self.module.SymbolicRegression
        self.guard = native.SearchInvocationGuard(self.original, budget.niterations)
        self.module.SymbolicRegression = self.guard
        jl.SearchBudgetClock.configure()

    def after_fit(self, jl, options, calls):
        checked_mechanism_sources(jl)
        if confirmed.read(
            self.directory, "backend_sources.json"
        ) != native.checked_backend_sources(jl):
            raise ValueError("Native backend changed during the fit.")
        if (
            self.guard is None
            or self.module.SymbolicRegression is not self.guard
            or self.runtime != native.checked_runtime(jl)
        ):
            raise ValueError("Changed native invocation or runtime.")
        _write_json(self.directory / "search_invocation.json", self.guard.record())
        clock = jl.SearchBudgetClock.record()
        _write_json(
            self.directory / "search_clock.json",
            {str(key): getattr(clock, str(key)) for key in jl.keys(clock)},
        )
        record = jl.WhiteLossScaling.verification_record(options)
        _write_json(
            self.directory / "native_verification.json",
            {
                "status": str(record.status),
                "condition": "iterations",
                "arm": self.request["arm"],
                "sigma_hex": float(record.sigma).hex(),
                "scale_hex": float(record.scale).hex(),
                "backend_seed": int(record.backend_seed),
                "callback_calls_during_fit": calls,
                "plugins_field": plugin_field_record(record.plugins_field),
                "plugins": plugin_records(record.plugins),
                "optimizer_settings": {
                    str(x.name): str(x.value) for x in record.optimizer_settings
                },
            },
        )

    def loss_replay(self, *args, **kwargs):
        return loss_evidence(self.request, *args, **kwargs)

    def candidate_fields(self, extra, table_loss):
        return candidate_fields(self.request, extra, table_loss)

    def finish(self, metadata):
        checked_mechanism_sources(self.jl)
        if confirmed.read(
            self.directory, "backend_sources.json"
        ) != native.checked_backend_sources(self.jl):
            raise ValueError("Native backend changed during replay.")
        _, metadata["confirmed_blas_control_after"] = confirmed.checked_environment(
            metadata["environment_after_search"]
        )
        confirmed.numerical_environment(metadata, self.runtime, completed=True)
        _write_json(self.directory / "metadata.json", metadata)
        verify_prepared(self.directory)
        if (
            metadata.get("worker_provenance") != _provenance()
            or metadata.get("worker_adapter_source_sha256") != source_hashes()
        ):
            raise ValueError("White-scaling provenance changed during consumption.")


def worker(directory):
    symbolic.worker(Path(directory).resolve(), hooks=WorkerHooks(directory))


def run_member(directory, *, deadline):
    """Run one fresh process and retain costs even on an integrity failure."""
    directory = Path(directory).resolve()
    verify_prepared(directory)
    started = time.monotonic()
    if not math.isfinite(deadline) or deadline <= started:
        raise TimeoutError("White-scaling deadline expired before worker start.")
    if (directory / "outcome.json").exists() or (directory / "worker.log").exists():
        raise ValueError("A worker directory cannot be run twice.")
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
        str(ROOT / "scripts/run_white_scaling_worker.py"),
        str(directory),
    ]
    with (directory / "worker.log").open("xb") as log:
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
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    outcome = {
        "format": FORMAT,
        "status": "completed"
        if code == 0 and not timed_out
        else "timeout"
        if timed_out
        else "failed",
        "returncode": code,
        "timed_out": timed_out,
        "worker_wall_seconds": time.monotonic() - started,
        "cpu_user_seconds": None if timed_out else after.ru_utime - before.ru_utime,
        "cpu_system_seconds": None if timed_out else after.ru_stime - before.ru_stime,
    }
    _write_json(directory / "outcome.json", outcome)
    _write_json(directory / "member_checksums.json", confirmed._inventory(directory))
    return verify_member(directory)


def _verify_native(directory, request):
    budget = checked_request(request)
    if confirmed.read(directory, "search_invocation.json") != native.invocation_record(
        budget.niterations
    ):
        raise ValueError("Changed native equation_search invocation.")
    clock = confirmed.read(directory, "search_clock.json")
    for key, value in {
        "requested_iterations": budget.niterations,
        "populations": 2,
        "processed_population_cycles": 2 * budget.niterations,
        "completed_outer_rounds": budget.niterations,
        "residual_population_cycles": 0,
        "iteration_limit_reached": True,
        "timeout_reached": False,
        "technical_counter_stop": False,
    }.items():
        if type(clock.get(key)) is not type(value) or clock[key] != value:
            raise ValueError("Changed or unfinished native iteration budget.")
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
            raise ValueError("Invalid native clock cost.")
    if (
        type(clock.get("checks")) is not int
        or clock["checks"] <= 0
        or not abs(clock.get("clock_difference_seconds", math.inf)) <= 1
    ):
        raise ValueError("Invalid native clock evidence.")
    record = confirmed.read(directory, "native_verification.json")
    if (
        any(
            record.get(key) != request[key] for key in ("arm", "sigma_hex", "scale_hex")
        )
        or record.get("status") != "verified"
    ):
        raise ValueError("Changed native scaling binding.")
    normalized = copy.deepcopy(record)
    normalized["backend_options"] = confirmed.read(directory, "backend_options.json")
    objectives = [
        field
        for field in normalized["backend_options"]
        if field["name"] == "loss_function"
    ]
    if len(objectives) != 1 or objectives[0] not in [
        {"name": "loss_function", "type": f"typeof({name})", "value": name}
        for name in (OBJECTIVE, OBJECTIVE.removeprefix("Main."))
    ]:
        raise ValueError("Wrong effective white-scaling objective.")
    objectives[0].update(type=f"typeof({native.OBJECTIVE})", value=native.OBJECTIVE)
    base = native.load_module(
        ROOT / "scripts/run_noiseless_control.py", "white_scaling_policy"
    )
    native.verify_options(
        normalized, budget.seed, "iterations", base, base.load_support()
    )
    saved = confirmed.read(directory, "pysr_parameters.json")
    if any(
        _json_bytes(saved.get(key)) != _json_bytes(value)
        for key, value in parameters(budget).items()
    ):
        raise ValueError("Changed effective white-scaling Python options.")
    return record


def verify_member(directory):
    """Check original rows, input bits, runtime and every candidate without a fit."""
    directory = Path(directory)
    request, arrays, manifest = verify_prepared(directory)
    initial_inventory = confirmed._inventory(directory)
    if confirmed.read(directory, "member_checksums.json") != initial_inventory:
        raise ValueError("Changed member inventory or checksum.")
    outcome = confirmed.read(directory, "outcome.json")
    metadata = confirmed.read(directory, "metadata.json")
    if metadata.get("format") != FORMAT:
        raise ValueError("Changed white-scaling metadata format.")
    if (
        set(outcome)
        != {
            "format",
            "status",
            "returncode",
            "timed_out",
            "worker_wall_seconds",
            "cpu_user_seconds",
            "cpu_system_seconds",
        }
        or outcome["format"] != FORMAT
        or type(outcome["returncode"]) is not int
        or type(outcome["timed_out"]) is not bool
    ):
        raise ValueError("Invalid white-scaling outcome.")
    completed = outcome["status"] == "completed"
    if outcome["status"] not in {"completed", "failed", "timeout"}:
        raise ValueError("Unrecognized white-scaling outcome.")
    confirmed._verify_origin(
        metadata,
        confirmed.read(directory, "metadata_initial.json"),
        manifest,
        completed=completed,
    )
    for key in ("worker_wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        if key.startswith("cpu_") and outcome["timed_out"] and outcome[key] is None:
            continue
        if (
            type(outcome[key]) not in (int, float)
            or not math.isfinite(outcome[key])
            or outcome[key] < 0
        ):
            raise ValueError("Invalid white-scaling resource cost.")
    if not completed:
        # Failed artifacts are retained but cannot silently become a usable arm.
        raise ValueError(
            f"White-scaling worker did not complete: {metadata.get('error', outcome['status'])}"
        )
    if (
        outcome["returncode"] != 0
        or outcome["timed_out"]
        or metadata.get("phase") != "success"
    ):
        raise ValueError("Contradictory successful worker status.")
    runtime = confirmed.read(directory, "native_runtime.json")
    native.validate_runtime(runtime)
    if (
        confirmed.read(directory, "backend_sources.json")
        != native.configuration()["reviewed_backend_sources"]
    ):
        raise ValueError("Changed native backend sources.")
    if confirmed.read(directory, "mechanism_sources.json") != MECHANISM_SOURCES:
        raise ValueError("Changed scaling-mechanism source binding.")
    environment = confirmed.numerical_environment(metadata, runtime, completed=True)
    record = _verify_native(directory, request)
    result = confirmed.read(directory, "result.json")
    if (
        result.get("format") != symbolic.FORMAT
        or result.get("evaluation_scope") != "fitted_samples_only"
        or result.get("selection") != "minimum_training_loss_then_complexity"
    ):
        raise ValueError("Changed base result contract.")
    candidates = result["candidates"]
    confirmed.verify_front(directory, candidates)
    selected = symbolic.select_candidate(candidates)
    budget = checked_request(request)
    if (
        type(result.get("selected_index")) is not int
        or result["selected_index"] != selected
        or result["rng"]["python_seed"] != budget.seed
        or result["rng"]["backend_seed"] != backend_seed(budget.seed)
    ):
        raise ValueError("Changed native training selection or seed.")
    factor = loss_object = None
    if "covariance" in arrays:
        loss_object = CovarianceLoss(arrays["covariance"])
        with np.load(directory / "native_factor.npz", allow_pickle=False) as saved:
            if saved.files != ["lower"] or saved["lower"].dtype != np.dtype("float64"):
                raise ValueError("Invalid native Cholesky factor record.")
            factor = saved["lower"].copy()
    normalization_evidence = verify_normalization(
        request, arrays["observed"], result, native_factor=factor
    )
    for candidate in candidates:
        prediction = symbolic.evaluate_tree(candidate["tree"], arrays["time_s"])
        proof = verify_prediction(
            candidate["tree"], arrays["time_s"], prediction, candidate["prediction"]
        )
        extra = (
            {}
            if factor is None
            else {
                "covariance": arrays["covariance"],
                "native_factor": factor,
                "native_whitened": np.asarray(candidate["native_whitened_residual"]),
            }
        )
        python_residual = arrays["observed"] - prediction
        python_loss = (
            mean_squared_error(python_residual)
            if loss_object is None
            else loss_object.mean_squared(python_residual)
        )
        if float(candidate["python_loss"]).hex() != float(python_loss).hex():
            raise ValueError("Changed independent Python loss.")
        evidence = loss_evidence(
            request,
            arrays["observed"],
            candidate["prediction"],
            prediction,
            candidate["loss"],
            candidate["julia_reimport_loss"],
            candidate["table_loss"],
            python_loss,
            loss_object,
            prediction_check=proof,
            **extra,
        )
        if (
            _json_bytes(evidence) != _json_bytes(candidate["loss_replay"])
            or _json_bytes(proof) != _json_bytes(candidate["prediction_replay"])
            or not np.array_equal(
                candidate["residual"],
                arrays["observed"] - np.asarray(candidate["prediction"]),
            )
        ):
            raise ValueError("Changed candidate replay evidence.")
        fields = candidate_fields(request, extra, candidate["table_loss"])
        if any(
            _json_bytes(candidate.get(key)) != _json_bytes(value)
            for key, value in fields.items()
        ):
            raise ValueError("Changed candidate objective semantics.")
    calls = result["callback_calls_during_fit"]
    if (
        type(calls) is not int
        or calls <= 0
        or calls != record["callback_calls_during_fit"]
    ):
        raise ValueError("Invalid objective evaluation cost.")
    fit_seconds = metadata.get("fit_wall_seconds")
    if (
        type(fit_seconds) not in (int, float)
        or not math.isfinite(fit_seconds)
        or fit_seconds < 0
    ):
        raise ValueError("Missing actual fit cost.")
    verify_prepared(directory)
    if confirmed._inventory(directory) != initial_inventory:
        raise ValueError("Evidence changed during read-only verification.")
    return {
        "format": FORMAT,
        "status": "completed",
        "request": request,
        "selected_index": selected,
        "selected": candidates[selected],
        "candidates": candidates,
        "costs": {
            **outcome,
            "fit_wall_seconds": fit_seconds,
            "callback_calls_during_fit": calls,
        },
        "numerical_environment": environment,
        "input_fingerprints": manifest["input_fingerprints"],
        "baseline_loss": result["baseline_loss"],
        "cost_normalization": result["cost_normalization"],
        "zero_expression_loss": result["zero_expression_loss"],
        "use_baseline": result["use_baseline"],
        "normalization_evidence": normalization_evidence,
        "provenance": manifest["provenance"],
    }
