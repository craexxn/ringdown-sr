"""Check search policy, process contracts, tree order and selection independently."""

import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

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
