"""Run a single free symbolic search in an isolated pinned Python/Julia process."""

import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from ringdown_sr.config import SearchBudget
from ringdown_sr.losses import CovarianceLoss, _real_array, mean_squared_error
from ringdown_sr.pilot import _environment, _provenance, _utc_now, _write_json

ROOT = Path(__file__).resolve().parents[2]
FORMAT = "ringdown-sr-search-arm-1"
BINARY = ("+", "-", "*", "/")
UNARY = ("exp", "sin", "cos")


def _check_prediction_replay(python_prediction, julia_prediction) -> dict:
    """Compare predictions in their own amplitude units, without a unit-size floor.

    Divide both vectors by their shared maximum absolute amplitude before
    comparison. This avoids underflow of an absolute tolerance for subnormal
    predictions and overflow of a raw difference at large amplitudes. A pair
    of identically zero vectors needs no division and agrees exactly.
    """
    python_values = _real_array(python_prediction, "python_prediction")
    julia_values = _real_array(julia_prediction, "julia_prediction")
    if (
        python_values.ndim != 1
        or python_values.size == 0
        or python_values.shape != julia_values.shape
    ):
        raise ValueError("Prediction replays need equal nonempty vector shapes.")
    scale = max(
        float(np.max(np.abs(python_values))), float(np.max(np.abs(julia_values)))
    )
    difference = 0.0
    if scale != 0.0:
        normalized_python = python_values / scale
        normalized_julia = julia_values / scale
        np.testing.assert_allclose(
            normalized_python,
            normalized_julia,
            rtol=1e-12,
            atol=1e-14,
            err_msg="Python and Julia predictions disagree at their amplitude scale.",
        )
        difference = float(np.max(np.abs(normalized_python - normalized_julia)))
    return {
        "amplitude_scale": scale,
        "scale_definition": "max_abs_of_both_predictions_no_floor",
        "max_normalized_difference": difference,
        "normalized_atol": 1e-14,
        "rtol": 1e-12,
    }


def _environment_snapshot(phase: str, *, julia_used: bool) -> dict:
    environment = _environment()
    environment["numerical_libraries"]["snapshot"] = phase
    environment["julia_used"] = julia_used
    return environment


def _adapter_source_hashes() -> dict:
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in (
            "scripts/run_python.py",
            "scripts/run_symbolic_worker.py",
            "julia/src/RingdownSRLoss.jl",
            "julia/src/RingdownSRSearch.jl",
        )
    }


def _initial_metadata() -> dict:
    """Capture immutable provenance before any bootstrap or worker can fail."""
    return {
        "format": FORMAT,
        "phase": "before_worker_start",
        "captured_at": _utc_now(),
        "provenance": _provenance(),
        "environment": _environment_snapshot("before_worker_start", julia_used=False),
        "adapter_source_sha256": _adapter_source_hashes(),
        "parent_pid": os.getpid(),
        "parent_python_executable": sys.executable,
    }


@dataclass(frozen=True)
class SearchRun:
    """Locate a completed or failed worker and its retained diagnostics."""

    output_directory: Path
    status: str


def search_parameters(budget: SearchBudget) -> dict:
    """Keep the reviewed grammar, loss, precision and search policy explicit."""
    return {
        "binary_operators": list(BINARY),
        "unary_operators": list(UNARY),
        "loss_function": "Main.RingdownSRSearch.objective",
        "model_selection": "accuracy",
        "loss_scale": "log",
        "maxsize": 20,
        "maxdepth": None,
        "complexity_of_operators": {op: 1 for op in (*BINARY, *UNARY)},
        "complexity_of_constants": 1,
        "complexity_of_variables": 1,
        "constraints": None,
        "nested_constraints": None,
        "parsimony": 0.0,
        "use_frequency": False,
        "use_frequency_in_tournament": False,
        "dimensionless_constants_only": False,
        "precision": 64,
        "turbo": False,
        "bumper": False,
        "autodiff_backend": None,
        "optimizer_algorithm": "BFGS",
        "optimizer_iterations": 20,
        "optimizer_nrestarts": 2,
        "random_state": budget.seed,
        "deterministic": True,
        "parallelism": "serial",
        "warm_start": False,
        "guesses": None,
        "batching": False,
        "denoise": False,
        "select_k_features": None,
        "early_stop_condition": None,
        "timeout_in_seconds": None,
        "max_evals": None,
        "niterations": budget.niterations,
        "populations": budget.populations,
        "population_size": budget.population_size,
        "ncycles_per_iteration": budget.ncycles_per_iteration,
        "progress": False,
        "verbosity": 0,
        "input_stream": "devnull",
        "update": False,
    }


def library_score(value: float) -> dict:
    """Preserve nonfinite library diagnostics without nonstandard JSON numbers."""
    status = (
        "finite"
        if math.isfinite(value)
        else "nan"
        if math.isnan(value)
        else "positive_infinity"
        if value > 0
        else "negative_infinity"
    )
    return {
        "value": value if status == "finite" else None,
        "status": status,
        "source": "pysr.sr.calculate_scores",
        "library_version": "2.6.0",
        "loss_scale": "log",
    }


def select_candidate(candidates: list[dict]) -> int:
    """Choose minimum raw fitted-sample loss, then minimum complexity."""
    if not candidates:
        raise ValueError("No admissible candidates were exported.")
    for candidate in candidates:
        if not math.isfinite(candidate["loss"]) or candidate["loss"] < 0:
            raise ValueError("Candidate losses must be finite and nonnegative.")
    return min(
        range(len(candidates)),
        key=lambda i: (candidates[i]["loss"], candidates[i]["complexity"]),
    )


def evaluate_tree(tree: dict, time_s) -> np.ndarray:
    """Replay the original binary evaluation order, without algebraic simplification."""
    time_values = _real_array(time_s, "time_s")

    def visit(node):
        if node["kind"] == "constant":
            value = float.fromhex(node["value_hex"])
            if not math.isfinite(value):
                raise ValueError("Tree constants must be finite.")
            return np.full(time_values.shape, value)
        if node["kind"] == "variable" and node["index"] == 1:
            return time_values.copy()
        if node["kind"] != "operator":
            raise ValueError("Unsupported tree node.")
        children = [visit(child) for child in node["children"]]
        arity, index = node["arity"], node["operator_index"]
        names = UNARY if arity == 1 else BINARY if arity == 2 else ()
        if type(index) is not int or not 1 <= index <= len(names):
            raise ValueError("Invalid operator index.")
        if len(children) != arity or node["operator"] != names[index - 1]:
            raise ValueError("Tree operator metadata does not match the grammar.")
        operations = {
            "+": np.add,
            "-": np.subtract,
            "*": np.multiply,
            "/": np.divide,
            "exp": np.exp,
            "sin": np.sin,
            "cos": np.cos,
        }
        return operations[node["operator"]](*children)

    with np.errstate(all="ignore"):
        prediction = visit(tree)
    if not np.all(np.isfinite(prediction)):
        raise ValueError("Tree prediction is not finite.")
    return prediction


def _inputs(time_s, observed, covariance):
    time_values = _real_array(time_s, "time_s").copy()
    target = _real_array(observed, "observed").copy()
    if (
        time_values.ndim != 1
        or time_values.size == 0
        or target.shape != time_values.shape
        or np.any(time_values < 0)
    ):
        raise ValueError(
            "time_s and observed need equal nonempty vector shapes and t >= 0."
        )
    matrix = (
        None if covariance is None else _real_array(covariance, "covariance").copy()
    )
    if matrix is not None and CovarianceLoss(matrix).n_samples != time_values.size:
        raise ValueError("Covariance shape must match the full sample window.")
    return time_values, target, matrix


def _stop_worker(process):
    """Terminate only the process/session created by this invocation."""

    def send(posix_signal):
        try:
            if os.name == "posix":
                os.killpg(process.pid, posix_signal)
            elif process.poll() is None:
                process.terminate()
        except ProcessLookupError:
            pass

    send(signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    finally:
        if os.name == "posix":
            send(signal.SIGKILL)
        process.wait()


def _run_worker(command, *, stdout):
    # A fresh session lets cancellation also stop the launcher's Python child.
    process = subprocess.Popen(
        command,
        stdout=stdout,
        stderr=subprocess.STDOUT,
        start_new_session=(os.name == "posix"),
    )
    try:
        returncode = process.wait()
        if returncode != 0:
            _stop_worker(process)
        return subprocess.CompletedProcess(command, returncode)
    except BaseException:
        _stop_worker(process)
        raise


def run_search_arm(
    time_s, observed, *, covariance=None, output, budget=None
) -> SearchRun:
    """Run one fresh arm; retain inputs, logs and failures in an exclusive directory.

    Only the supplied sample vectors, optional fixed covariance and search budget
    enter the worker request. No signal truth or background controls are accepted.
    This API requires a repository checkout and the project's pinned interpreter.
    """
    budget = SearchBudget() if budget is None else budget
    if not isinstance(budget, SearchBudget):
        raise TypeError("budget must be a SearchBudget.")
    time_values, target, matrix = _inputs(time_s, observed, covariance)
    directory = Path(output).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    arrays = {"time_s": time_values, "observed": target}
    if matrix is not None:
        arrays["covariance"] = matrix
    np.savez(directory / "inputs.npz", **arrays)
    _write_json(
        directory / "request.json", {"format": FORMAT, "budget": asdict(budget)}
    )
    _write_json(directory / "status.json", {"status": "running", "format": FORMAT})
    started = time.perf_counter()
    try:
        metadata = _initial_metadata()
        _write_json(directory / "metadata_initial.json", metadata)
        _write_json(directory / "metadata.json", metadata)
        with (directory / "worker.log").open("w", encoding="utf-8") as log:
            completed = _run_worker(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "run_python.py"),
                    str(ROOT / "scripts" / "run_symbolic_worker.py"),
                    str(directory),
                ],
                stdout=log,
            )
        status = "success" if completed.returncode == 0 else "failed"
        if status == "success":
            result = json.loads((directory / "result.json").read_text())
            if result["format"] != FORMAT or not result["candidates"]:
                raise ValueError("Worker returned an invalid result.")
        details = {"status": status, "returncode": completed.returncode}
    except BaseException as error:
        _write_json(
            directory / "status.json",
            {
                "status": "failed",
                "format": FORMAT,
                "error": f"{type(error).__name__}: {error}",
            },
        )
        raise
    details.update(format=FORMAT, total_wall_seconds=time.perf_counter() - started)
    _write_json(directory / "status.json", details)
    return SearchRun(directory, status)


def _export_tree(root, options) -> dict:
    degree = int(root.degree)
    if degree == 0:
        return (
            {"kind": "constant", "value_hex": float(root.val).hex()}
            if root.constant
            else {"kind": "variable", "index": int(root.feature)}
        )
    names = UNARY if degree == 1 else BINARY
    index = int(root.op)
    # Check the effective backend operator, not only the requested Python list.
    if str(options.operators.ops[degree - 1][index - 1]) != names[index - 1]:
        raise ValueError("Unexpected effective operator mapping.")
    children = [root.l] if degree == 1 else [root.l, root.r]
    return {
        "kind": "operator",
        "arity": degree,
        "operator_index": index,
        "operator": names[index - 1],
        "children": [_export_tree(child, options) for child in children],
    }


def _import_tree(node, backend):
    if node["kind"] == "constant":
        return backend.constant(float.fromhex(node["value_hex"]))
    if node["kind"] == "variable":
        return backend.variable(node["index"])
    children = [_import_tree(child, backend) for child in node["children"]]
    factory = backend.unary if node["arity"] == 1 else backend.binary
    return factory(node["operator_index"], *children)


def worker(directory: Path) -> None:
    """Internal process entry point, invoked only through the pinned launcher."""
    if os.environ.get("PYTHON_JULIACALL_PROJECT") != str(ROOT / "julia"):
        raise RuntimeError("Run this worker through scripts/run_python.py.")
    started = time.perf_counter()
    # Start from the on-disk snapshot, never recapture/replace the parent's origin.
    metadata = json.loads((directory / "metadata_initial.json").read_text())
    metadata.update(
        phase="worker_start",
        worker_started_at=_utc_now(),
        worker_pid=os.getpid(),
        python_executable=sys.executable,
    )
    _write_json(directory / "metadata.json", metadata)
    try:
        _worker_search(directory, metadata, started)
    except BaseException as error:
        metadata.update(
            failed_during=metadata["phase"],
            phase="failed",
            failed_at=_utc_now(),
            error=f"{type(error).__name__}: {error}",
        )
        _write_json(directory / "metadata.json", metadata)
        raise


def _worker_search(directory: Path, metadata: dict, started: float) -> None:
    request = json.loads((directory / "request.json").read_text())
    if set(request) != {"format", "budget"} or request["format"] != FORMAT:
        raise ValueError("Unsupported search-arm request.")
    budget = SearchBudget(**request["budget"])
    with np.load(directory / "inputs.npz", allow_pickle=False) as inputs:
        if set(inputs.files) not in (
            {"time_s", "observed"},
            {"time_s", "observed", "covariance"},
        ):
            raise ValueError("Unexpected worker inputs.")
        time_values, target, matrix = _inputs(
            inputs["time_s"],
            inputs["observed"],
            inputs.get("covariance"),
        )

    import pysr
    from juliacall import Main as jl
    from juliacall import convert as jl_convert

    if pysr.__version__ != "2.6.0":
        raise RuntimeError("The adapter requires PySR 2.6.0.")
    if str(jl.seval("string(Base.pkgversion(SymbolicRegression))")) != "2.5.1":
        raise RuntimeError("The adapter requires SymbolicRegression 2.5.1.")
    for name in ("RingdownSRLoss.jl", "RingdownSRSearch.jl"):
        source = directory / name
        source.write_bytes((ROOT / "julia" / "src" / name).read_bytes())
        jl.include(str(source))
    backend = jl.RingdownSRSearch

    def array(values):
        return jl_convert(jl.Array[jl.Float64], np.asarray(values, dtype=np.float64))

    backend.bind_context(
        array(time_values), array(target), None if matrix is None else array(matrix)
    )
    parameters = search_parameters(budget)
    model = pysr.PySRRegressor(
        **parameters, output_directory=str(directory / "pysr"), run_id="search"
    )
    _write_json(directory / "pysr_parameters.json", model.get_params())
    metadata.update(
        phase="fit",
        before_fit_at=_utc_now(),
        worker_provenance=_provenance(),
        worker_adapter_source_sha256=_adapter_source_hashes(),
        environment=_environment_snapshot("before_fit", julia_used=True),
        julia_version=str(jl.seval("string(VERSION)")),
        symbolic_regression_version=str(
            jl.seval("string(Base.pkgversion(SymbolicRegression))")
        ),
        active_julia_project=str(jl.seval("Base.active_project()")),
    )
    _write_json(directory / "metadata.json", metadata)
    before_fit = time.perf_counter()
    model.fit(
        time_values[:, None], target, variable_names=["t"], X_units=["s"], y_units="1"
    )
    after_fit = time.perf_counter()
    metadata.update(
        phase="replay",
        after_fit_at=_utc_now(),
        fit_wall_seconds=after_fit - before_fit,
    )
    _write_json(directory / "metadata.json", metadata)
    search_calls = int(backend.CALLS[()])
    options = backend.LAST_OPTIONS[()]
    dataset = backend.LAST_DATASET[()]
    baseline = float(dataset.baseline_loss)
    use_baseline = bool(dataset.use_baseline)
    normalization = baseline if use_baseline and baseline >= 0.01 else 0.01
    # Exercise the callback actually installed by PySR through backend dispatch.
    zero_expression_loss = float(
        jl.SymbolicRegression.eval_loss(backend.constant(0.0), dataset, options)
    )
    fields = [
        {"name": str(field.name), "type": str(field.type), "value": str(field.value)}
        for field in backend.option_fields(options)
    ]
    _write_json(directory / "backend_options.json", fields)
    (directory / "search_state.jls").write_bytes(bytes(model.julia_state_stream_))
    (directory / "search_options.jls").write_bytes(bytes(model.julia_options_stream_))
    hof = model.julia_state_[1]
    members = jl.SymbolicRegression.calculate_pareto_frontier(hof)
    rows = model.equations_
    if len(members) != len(rows):
        raise ValueError("Python and Julia Pareto fronts do not match.")
    candidates = []
    loss_object = None if matrix is None else CovarianceLoss(matrix)
    for member, (_, row) in zip(members, rows.iterrows(), strict=True):
        root = jl.SymbolicRegression.get_tree(member.tree)
        tree = _export_tree(root, options)
        restored = _import_tree(tree, backend)
        if _export_tree(restored, options) != tree:
            raise ValueError("Tree round trip changed the exported expression.")
        prediction, replay_loss = backend.replay(restored, options)
        prediction = np.asarray(prediction, dtype=np.float64)
        python_prediction = evaluate_tree(tree, time_values)
        prediction_replay = _check_prediction_replay(python_prediction, prediction)
        residual = target - prediction
        python_residual = target - python_prediction
        python_loss = (
            mean_squared_error(python_residual)
            if loss_object is None
            else loss_object.mean_squared(python_residual)
        )
        raw_loss = float(member.loss)
        np.testing.assert_allclose(
            [replay_loss, row["loss"], python_loss], raw_loss, rtol=1e-10, atol=0
        )
        complexity = int(jl.SymbolicRegression.compute_complexity(member.tree, options))
        if complexity != int(row["complexity"]):
            raise ValueError("Python and Julia complexities do not match.")
        candidates.append(
            {
                "complexity": complexity,
                "loss": raw_loss,
                "tree": tree,
                "display_equation": str(row["equation"]),
                "library_score": library_score(float(row["score"])),
                "prediction": prediction.tolist(),
                "residual": residual.tolist(),
                "julia_reimport_loss": float(replay_loss),
                "python_loss": python_loss,
                "prediction_replay": prediction_replay,
                "units_status": "accepted_by_backend_wildcard_checker",
            }
        )
    selected = select_candidate(candidates)
    result = {
        "format": FORMAT,
        "evaluation_scope": "fitted_samples_only",
        "candidates": candidates,
        "selected_index": selected,
        "selection": "minimum_training_loss_then_complexity",
        "baseline_loss": baseline,
        "use_baseline": use_baseline,
        "cost_normalization": normalization,
        "zero_expression_loss": (
            zero_expression_loss if math.isfinite(zero_expression_loss) else None
        ),
        "zero_expression_loss_status": (
            "finite" if math.isfinite(zero_expression_loss) else "nonfinite"
        ),
        "callback_calls_during_fit": search_calls,
        "backend_evaluation_counter": {
            "status": "unavailable",
            "reason": "not returned by equation_search",
        },
        "rng": {
            "python_seed": budget.seed,
            "backend_seed": int(options.seed),
            "state_status": "not_exported; serialized search state is not a complete RNG checkpoint",
        },
        "timing_seconds": {
            "worker_setup": before_fit - started,
            "fit_including_jit_and_python_exports": after_fit - before_fit,
        },
    }
    _write_json(directory / "result.json", result)
    metadata.update(
        phase="success",
        completed_at=_utc_now(),
        environment_after_search=_environment_snapshot("after_search", julia_used=True),
    )
    _write_json(directory / "metadata.json", metadata)
    checksums = {
        path.relative_to(directory).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
        and path.name not in {"worker.log", "status.json", "checksums.json"}
    }
    _write_json(directory / "checksums.json", checksums)
    print(
        f"Free PySR search passed: {len(candidates)} replayed Pareto candidates.",
        flush=True,
    )
