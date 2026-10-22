"""Check search policy, process contracts, tree order and selection independently."""

import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from ringdown_sr import symbolic


def constant(value):
    return {"kind": "constant", "value_hex": float(value).hex()}


def operator(name, *children):
    names = symbolic.UNARY if len(children) == 1 else symbolic.BINARY
    return {
        "kind": "operator",
        "operator": name,
        "arity": len(children),
        "operator_index": names.index(name) + 1,
        "children": list(children),
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": -1},
        {"seed": 2**32},
        {"seed": True},
        {"seed": 1.5},
        {"niterations": 0},
        {"populations": 0},
        {"population_size": 15},
        {"ncycles_per_iteration": 0},
    ],
)
def test_budget_rejects_invalid_values(kwargs):
    with pytest.raises(ValueError):
        symbolic.SearchBudget(**kwargs)


def test_reviewed_search_policy():
    parameters = symbolic.search_parameters(symbolic.SearchBudget())
    assert parameters["precision"] == 64
    assert parameters["binary_operators"] == ["+", "-", "*", "/"]
    assert parameters["unary_operators"] == ["exp", "sin", "cos"]
    assert parameters["batching"] is False
    assert parameters["parsimony"] == 0
    assert parameters["use_frequency"] is False
    assert parameters["use_frequency_in_tournament"] is False
    assert parameters["guesses"] is None and parameters["warm_start"] is False
    assert parameters["autodiff_backend"] is None
    assert parameters["optimizer_algorithm"] == "BFGS"
    assert parameters["optimizer_iterations"] == 20
    assert parameters["optimizer_nrestarts"] == 2
    assert parameters["parallelism"] == "serial" and parameters["deterministic"] is True
    assert parameters["model_selection"] == "accuracy"
    assert parameters["niterations"] == 10 and parameters["populations"] == 2
    assert parameters["population_size"] == 32
    assert parameters["ncycles_per_iteration"] == 50
    assert parameters["maxsize"] == 20 and parameters["maxdepth"] is None
    assert parameters["denoise"] is False and parameters["select_k_features"] is None
    assert all(
        parameters[k] is None
        for k in ("early_stop_condition", "timeout_in_seconds", "max_evals")
    )
    assert parameters["dimensionless_constants_only"] is False
    assert parameters["turbo"] is False and parameters["bumper"] is False


@pytest.mark.parametrize(
    "value,status",
    [
        (0.0, "finite"),
        (math.inf, "positive_infinity"),
        (-math.inf, "negative_infinity"),
        (math.nan, "nan"),
    ],
)
def test_score_diagnostics_are_strict_json(value, status):
    result = symbolic.library_score(value)
    assert result["status"] == status
    assert result["value"] == 0 if status == "finite" else result["value"] is None
    assert result["source"] == "pysr.sr.calculate_scores"
    json.dumps(result, allow_nan=False)


def test_selection_replaces_an_earlier_candidate_and_breaks_ties_by_size():
    candidates = [
        {"loss": 3.0, "complexity": 1},
        {"loss": 1.0, "complexity": 5},
        {"loss": 1.0, "complexity": 3},
    ]
    assert symbolic.select_candidate(candidates) == 2
    assert symbolic.select_candidate(list(reversed(candidates))) == 0
    assert symbolic.select_candidate([*candidates, {"loss": 0.0, "complexity": 9}]) == 3


@pytest.mark.parametrize("candidates", [[], [{"loss": math.inf}], [{"loss": -1.0}]])
def test_selection_requires_admissible_candidates(candidates):
    with pytest.raises(ValueError):
        symbolic.select_candidate(candidates)


def test_tree_replay_preserves_order_and_float64_bits():
    # These algebraically equivalent expressions differ in floating-point arithmetic.
    left = operator("+", operator("+", constant(1e16), constant(-1e16)), constant(1))
    right = operator("+", constant(1e16), operator("+", constant(-1e16), constant(1)))
    np.testing.assert_array_equal(symbolic.evaluate_tree(left, [0, 1]), [1, 1])
    np.testing.assert_array_equal(symbolic.evaluate_tree(right, [0, 1]), [0, 0])
    value = np.nextafter(1.0, 2.0)
    assert symbolic.evaluate_tree(constant(value), [0])[0].hex() == value.hex()
    assert symbolic.evaluate_tree(constant(-0.0), [0])[0].hex() == (-0.0).hex()


def test_all_grammar_operators_against_explicit_reference():
    t = {"kind": "variable", "index": 1}
    tree = operator(
        "+",
        operator(
            "*",
            operator("exp", operator("*", constant(-2), t)),
            operator(
                "cos", operator("+", operator("*", constant(3), t), constant(0.2))
            ),
        ),
        operator("/", operator("sin", t), operator("-", constant(2), t)),
    )
    time = np.array([0.0, 0.1, 0.3])
    expected = np.exp(-2 * time) * np.cos(3 * time + 0.2) + np.sin(time) / (2 - time)
    np.testing.assert_allclose(symbolic.evaluate_tree(tree, time), expected, rtol=1e-15)


@pytest.mark.parametrize(
    "tree",
    [
        {"kind": "variable", "index": 2},
        constant(math.inf),
        {
            "kind": "operator",
            "arity": 1,
            "operator_index": 1,
            "operator": "cos",
            "children": [constant(1)],
        },
        operator("/", constant(1), constant(0)),
        operator("exp", constant(1000)),
    ],
)
def test_tree_replay_rejects_invalid_trees(tree):
    with pytest.raises(ValueError):
        symbolic.evaluate_tree(tree, [0, 1])


def test_tiny_sign_reversal_with_identical_losses_is_rejected():
    prediction = np.array([1e-21, -1e-21])
    reversed_prediction = -prediction
    objective = symbolic.CovarianceLoss(np.eye(2) * 1e-42)
    # The old fixed-atol check and the loss check both accept this counterexample.
    np.testing.assert_allclose(prediction, reversed_prediction, rtol=1e-12, atol=1e-14)
    np.testing.assert_allclose(
        [
            objective.mean_squared(prediction),
            objective.mean_squared(reversed_prediction),
        ],
        [1.0, 1.0],
        rtol=1e-14,
        atol=0,
    )
    with pytest.raises(AssertionError, match="amplitude scale"):
        symbolic._check_prediction_replay(prediction, reversed_prediction)


@pytest.mark.parametrize("amplitude", [1e-200, 1e-21, 1.0, 1e200])
def test_prediction_replay_is_invariant_to_amplitude_units(amplitude):
    expected = np.array([1.0, -2.0, 0.0]) * amplitude
    nearby = np.array([1.0 + 2e-14, -2.0, 1e-15]) * amplitude
    diagnostic = symbolic._check_prediction_replay(nearby, expected)
    assert diagnostic["amplitude_scale"] == 2 * amplitude
    assert diagnostic["max_normalized_difference"] < 2e-14
    with pytest.raises(AssertionError):
        symbolic._check_prediction_replay(expected * 1.001, expected)


def test_prediction_replay_zero_subnormal_and_large_amplitudes():
    zeros = symbolic._check_prediction_replay([0.0, -0.0], [0.0, 0.0])
    assert zeros["amplitude_scale"] == zeros["max_normalized_difference"] == 0.0
    subnormal = np.nextafter(0.0, 1.0)
    tiny = symbolic._check_prediction_replay([subnormal], [subnormal])
    assert tiny["amplitude_scale"] == subnormal
    assert tiny["max_normalized_difference"] == 0.0
    for first, second in (
        ([subnormal], [-subnormal]),
        ([0.0], [1e-21]),
        ([1e308], [-1e308]),
    ):
        with np.errstate(over="raise"), pytest.raises(AssertionError):
            symbolic._check_prediction_replay(first, second)


@pytest.mark.parametrize(
    "first,second",
    [([], []), ([1.0, 2.0], [1.0]), ([[1.0]], [[1.0]]), ([math.nan], [0.0])],
)
def test_prediction_replay_requires_finite_equal_vectors(first, second):
    with pytest.raises(ValueError):
        symbolic._check_prediction_replay(first, second)


@pytest.mark.parametrize(
    "time,target,covariance",
    [
        ([], [], None),
        ([-1], [1], None),
        ([0, 1], [1], None),
        ([True], [1], None),
        ([0], [math.nan], None),
        ([0], [1], [[0]]),
        ([0, 1], [1, 2], [[1]]),
        ([0, 1], [1, 2], [[1, 0.2], [0, 1]]),
    ],
)
def test_bad_inputs_do_not_reserve_outputs(tmp_path, time, target, covariance):
    output = tmp_path / "absent"
    with pytest.raises(ValueError):
        symbolic.run_search_arm(time, target, covariance=covariance, output=output)
    assert not output.exists()


def test_worker_receives_only_inputs_budget_and_literal_paths(tmp_path, monkeypatch):
    directory = tmp_path / "search with spaces $literal"
    time = np.array([0.0, 1.0])
    target = np.array([1.0, 0.0])
    matrix = np.array([[2.5, 1.5], [1.5, 4.5]])

    def launch(command, **kwargs):
        assert command == [
            sys.executable,
            str(symbolic.ROOT / "scripts/run_python.py"),
            str(symbolic.ROOT / "scripts/run_symbolic_worker.py"),
            str(directory),
        ]
        assert "shell" not in kwargs
        request = json.loads((directory / "request.json").read_text())
        assert set(request) == {"format", "budget"}
        with np.load(directory / "inputs.npz", allow_pickle=False) as values:
            assert set(values.files) == {"time_s", "observed", "covariance"}
            np.testing.assert_array_equal(values["covariance"], matrix)
        symbolic._write_json(
            directory / "result.json",
            {
                "format": symbolic.FORMAT,
                "candidates": [{"loss": 1.0}],
            },
        )
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(symbolic, "_run_worker", launch)
    result = symbolic.run_search_arm(time, target, covariance=matrix, output=directory)
    assert result.status == "success"
    assert json.loads((directory / "status.json").read_text())["returncode"] == 0
    np.testing.assert_array_equal(time, [0, 1])
    np.testing.assert_array_equal(target, [1, 0])
    np.testing.assert_array_equal(matrix, [[2.5, 1.5], [1.5, 4.5]])
    with pytest.raises(FileExistsError):
        symbolic.run_search_arm(time, target, output=directory)


def test_nonzero_worker_preserves_logs_and_failure(tmp_path, monkeypatch):
    def fail(command, **kwargs):
        initial = json.loads((tmp_path / "failure/metadata_initial.json").read_text())
        assert initial["phase"] == "before_worker_start"
        assert initial["provenance"]["python_source_sha256"]
        assert initial["environment"]["python_version"]
        kwargs["stdout"].write("worker failed with diagnostic\n")
        return subprocess.CompletedProcess(command, 17)

    monkeypatch.setattr(symbolic, "_run_worker", fail)
    result = symbolic.run_search_arm([0, 1], [1, 0], output=tmp_path / "failure")
    assert result.status == "failed"
    assert "diagnostic" in (result.output_directory / "worker.log").read_text()
    assert (
        json.loads((result.output_directory / "status.json").read_text())["returncode"]
        == 17
    )
    assert (result.output_directory / "inputs.npz").exists()
    assert json.loads(
        (result.output_directory / "metadata.json").read_text()
    ) == initial_metadata(result.output_directory)


def initial_metadata(directory):
    return json.loads((directory / "metadata_initial.json").read_text())


@pytest.fixture
def worker_failure_runtime(monkeypatch):
    """Stub external runtime boundaries so failures exercise the real worker lifecycle."""
    import pandas as pd

    state = {"source": "before-search", "fit_calls": 0, "fail_fit": False}

    def provenance():
        return {
            "git": {"commit": state["source"]},
            "python_source_sha256": {"ringdown_sr/symbolic.py": state["source"]},
        }

    monkeypatch.setattr(symbolic, "_provenance", provenance)
    monkeypatch.setattr(
        symbolic,
        "_environment",
        lambda: {
            "python_version": "3.12.14",
            "packages": {"pysr": "2.6.0"},
            "numerical_libraries": {},
        },
    )
    backend = SimpleNamespace(
        bind_context=lambda *args: None,
        CALLS={(): 1},
        LAST_OPTIONS={(): SimpleNamespace(seed=123)},
        LAST_DATASET={(): SimpleNamespace(baseline_loss=1.0, use_baseline=True)},
        constant=lambda value: value,
        option_fields=lambda options: [],
    )
    member = SimpleNamespace(tree="fixed tree", loss=0.2)
    jl = SimpleNamespace(
        Array={float: "Float64Array"},
        Float64=float,
        RingdownSRSearch=backend,
        include=lambda path: None,
        seval=lambda code: "2.5.1" if "pkgversion" in code else "1.13.1",
        SymbolicRegression=SimpleNamespace(
            eval_loss=lambda *args: 0.5,
            calculate_pareto_frontier=lambda hof: [member],
            get_tree=lambda tree: tree,
            compute_complexity=lambda tree, options: state.get("complexity", 1),
        ),
    )

    class Model:
        def __init__(self, **kwargs):
            self.equations_ = pd.DataFrame(
                {
                    "loss": [state.get("loss", 0.2)],
                    "complexity": [state.get("complexity", 1)],
                    "score": [0.0],
                    "equation": ["fixed test tree"],
                }
            )
            self.julia_state_ = (None, "hof")
            self.julia_state_stream_ = self.julia_options_stream_ = b"state"

        def get_params(self):
            return {"precision": 64}

        def fit(self, *args, **kwargs):
            state["fit_calls"] += 1
            state["source"] = "changed-during-fit"
            if state["fail_fit"]:
                raise RuntimeError("injected fit failure")

    monkeypatch.setitem(
        sys.modules, "pysr", SimpleNamespace(__version__="2.6.0", PySRRegressor=Model)
    )
    monkeypatch.setitem(
        sys.modules,
        "juliacall",
        SimpleNamespace(Main=jl, convert=lambda _, values: values),
    )
    monkeypatch.setenv("PYTHON_JULIACALL_PROJECT", str(symbolic.ROOT / "julia"))
    state.update(backend=backend, member=member)
    return state


@pytest.mark.parametrize("phase", ["fit", "replay"])
def test_failed_fit_or_replay_retains_initial_and_runtime_provenance(
    tmp_path, monkeypatch, worker_failure_runtime, phase
):
    state = worker_failure_runtime
    state["fail_fit"] = phase == "fit"

    def replay_failure(*args):
        raise RuntimeError("injected replay failure")

    monkeypatch.setattr(symbolic, "_export_tree", replay_failure)
    initial_bytes = []

    def launch(command, **kwargs):
        directory = Path(command[-1])
        initial_bytes.append((directory / "metadata_initial.json").read_bytes())
        with pytest.raises(RuntimeError, match=f"injected {phase} failure"):
            symbolic.worker(directory)
        return subprocess.CompletedProcess(command, 17)

    monkeypatch.setattr(symbolic, "_run_worker", launch)
    run = symbolic.run_search_arm([0.0, 1.0], [1.0, 0.0], output=tmp_path / phase)
    directory = run.output_directory
    assert run.status == "failed" and state["fit_calls"] == 1
    assert (directory / "metadata_initial.json").read_bytes() == initial_bytes[0]
    first = initial_metadata(directory)
    current = json.loads((directory / "metadata.json").read_text())
    assert first["provenance"]["git"]["commit"] == "before-search"
    assert current["provenance"] == first["provenance"]
    assert current["adapter_source_sha256"] == first["adapter_source_sha256"]
    assert current["worker_provenance"]["git"]["commit"] == "before-search"
    assert current["worker_provenance"]["python_source_sha256"]
    assert current["environment"]["numerical_libraries"]["snapshot"] == "before_fit"
    assert current["environment"]["julia_used"] is True
    assert current["phase"] == "failed" and current["failed_during"] == phase
    assert current["worker_pid"] == os.getpid() and current["julia_version"] == "1.13.1"
    assert state["source"] == "changed-during-fit"


def test_import_failure_preserves_origin_before_runtime_is_available(
    tmp_path, monkeypatch
):
    monkeypatch.setitem(sys.modules, "pysr", None)
    monkeypatch.setenv("PYTHON_JULIACALL_PROJECT", str(symbolic.ROOT / "julia"))

    def launch(command, **kwargs):
        with pytest.raises(ModuleNotFoundError):
            symbolic.worker(Path(command[-1]))
        return subprocess.CompletedProcess(command, 17)

    monkeypatch.setattr(symbolic, "_run_worker", launch)
    run = symbolic.run_search_arm([0.0], [1.0], output=tmp_path / "import-failure")
    current = json.loads((run.output_directory / "metadata.json").read_text())
    assert current["phase"] == "failed" and current["failed_during"] == "worker_start"
    assert current["provenance"] == initial_metadata(run.output_directory)["provenance"]
    assert current["provenance"]["python_source_sha256"]
    assert current["environment"]["python_version"]
    assert "julia_version" not in current


def test_worker_rejects_tiny_sign_error_even_when_loss_replays_agree(
    tmp_path, monkeypatch, worker_failure_runtime
):
    state = worker_failure_runtime
    state.update(loss=1.0, complexity=7)
    state["member"].loss = 1.0
    prediction = np.array([1e-21, -1e-21])
    state["backend"].replay = lambda *args: (-prediction, 1.0)
    tree = operator(
        "*",
        constant(1e-21),
        operator(
            "cos", operator("*", constant(np.pi), {"kind": "variable", "index": 1})
        ),
    )
    # Stub only the external tree transfer; evaluate the Python AST and all
    # production replay checks normally. Both covariance losses would be 1.
    monkeypatch.setattr(symbolic, "_export_tree", lambda *args: tree)
    monkeypatch.setattr(symbolic, "_import_tree", lambda *args: "restored tree")

    def launch(command, **kwargs):
        with pytest.raises(AssertionError, match="amplitude scale"):
            symbolic.worker(Path(command[-1]))
        return subprocess.CompletedProcess(command, 17)

    monkeypatch.setattr(symbolic, "_run_worker", launch)
    run = symbolic.run_search_arm(
        [0.0, 1.0],
        [0.0, 0.0],
        covariance=np.eye(2) * 1e-42,
        output=tmp_path / "sign-error",
    )
    assert run.status == "failed"
    current = json.loads((run.output_directory / "metadata.json").read_text())
    assert (
        current["failed_during"] == "replay" and "amplitude scale" in current["error"]
    )


def test_success_without_result_is_failed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        symbolic,
        "_run_worker",
        lambda command, **kw: subprocess.CompletedProcess(command, 0),
    )
    with pytest.raises(FileNotFoundError):
        symbolic.run_search_arm([0], [1], output=tmp_path / "missing")
    assert (
        json.loads((tmp_path / "missing/status.json").read_text())["status"] == "failed"
    )


def test_worker_cannot_import_julia_without_launcher(tmp_path, monkeypatch):
    monkeypatch.delenv("PYTHON_JULIACALL_PROJECT", raising=False)
    with pytest.raises(RuntimeError, match="run_python.py"):
        symbolic.worker(tmp_path)


def test_interrupt_preserves_failed_status(tmp_path, monkeypatch):
    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(symbolic, "_run_worker", interrupt)
    with pytest.raises(KeyboardInterrupt):
        symbolic.run_search_arm([0], [1], output=tmp_path / "interrupt")
    result = json.loads((tmp_path / "interrupt/status.json").read_text())
    assert result["status"] == "failed" and "KeyboardInterrupt" in result["error"]


@pytest.mark.skipif(os.name != "posix", reason="Process groups are used on Linux/WSL.")
def test_interrupt_stops_owned_worker_and_its_child(tmp_path, monkeypatch):
    pid_file = tmp_path / "child-pid"
    child = "import time; time.sleep(60)"
    source = (
        "import pathlib,subprocess,sys,time\n"
        f"p=subprocess.Popen([sys.executable,'-c',{child!r}])\n"
        f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid))\n"
        "p.wait()\n"
    )

    class InterruptedProcess(subprocess.Popen):
        interrupted = False

        def wait(self, *args, **kwargs):
            if not self.interrupted:
                self.interrupted = True
                deadline = time.monotonic() + 5
                while not pid_file.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                assert pid_file.exists(), "Test child did not start."
                raise KeyboardInterrupt
            return super().wait(*args, **kwargs)

    monkeypatch.setattr(symbolic.subprocess, "Popen", InterruptedProcess)
    with (tmp_path / "process.log").open("w") as log, pytest.raises(KeyboardInterrupt):
        symbolic._run_worker([sys.executable, "-c", source], stdout=log)
    child_pid = int(pid_file.read_text())
    stat = Path(f"/proc/{child_pid}/stat")
    deadline = time.monotonic() + 2
    while (
        stat.exists()
        and stat.read_text().split()[2] != "Z"
        and time.monotonic() < deadline
    ):
        time.sleep(0.01)
    assert not stat.exists() or stat.read_text().split()[2] == "Z"
