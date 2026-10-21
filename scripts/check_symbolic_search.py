"""Exercise real PySR searches, isolated contexts, exact trees and score edges."""

import hashlib
import json
import os
import tempfile
from pathlib import Path

import numpy as np

from ringdown_sr.symbolic import (
    ROOT,
    SearchBudget,
    _export_tree,
    _import_tree,
    evaluate_tree,
    library_score,
    run_search_arm,
    select_candidate,
)


def check_tree_and_score_references():
    # This reference process has its own context; search arms cannot reuse it.
    import pandas as pd
    import pysr
    from juliacall import JuliaError
    from juliacall import Main as jl
    from juliacall import convert as jl_convert
    from pysr.sr import calculate_scores

    assert pysr.__version__ == "2.6.0"
    first = calculate_scores(pd.DataFrame({"complexity": [1], "loss": [0.0]}))
    transition = calculate_scores(
        pd.DataFrame({"complexity": [1, 3], "loss": [1.0, 0.0]})
    )
    assert library_score(float(first.iloc[0]["score"]))["value"] == 0.0
    assert (
        library_score(float(transition.iloc[1]["score"]))["status"]
        == "positive_infinity"
    )
    json.dumps(library_score(float(transition.iloc[1]["score"])), allow_nan=False)

    jl.include(str(ROOT / "julia/src/RingdownSRLoss.jl"))
    jl.include(str(ROOT / "julia/src/RingdownSRSearch.jl"))
    backend = jl.RingdownSRSearch

    def array(values):
        return jl_convert(jl.Array[jl.Float64], np.asarray(values, dtype=np.float64))

    time = np.array([0.0, 0.1, 0.2])
    observed = np.array([1.0, 0.0, -1.0])
    covariance = np.array([[4.0, 2.0, 0.0], [2.0, 5.0, 1.0], [0.0, 1.0, 3.0]])
    backend.bind_context(array(time), array(observed), array(covariance))
    options = jl.seval("""
        SymbolicRegression.Options(
            operators=SymbolicRegression.OperatorEnum(((exp, sin, cos), (+, -, *, /))),
            maxsize=20, dimensionless_constants_only=false,
            loss_function=Main.RingdownSRSearch.objective,
            batching=false, turbo=false, bumper=false,
        )
    """)
    c, t = backend.constant, backend.variable(1)
    u, b = backend.unary, backend.binary
    # Independent, fully specified expression exercises every supported operator.
    root = b(
        1,
        b(3, u(1, b(3, c(-2.0), t)), u(3, b(1, b(3, c(3.0), t), c(0.2)))),
        b(4, u(2, b(3, c(1.0), t)), b(2, c(2.0), b(3, c(1.0), t))),
    )
    tree = _export_tree(root, options)
    restored = _import_tree(json.loads(json.dumps(tree, allow_nan=False)), backend)
    assert _export_tree(restored, options) == tree
    prediction, loss = backend.replay(restored, options)
    expected = np.exp(-2 * time) * np.cos(3 * time + 0.2) + np.sin(time) / (2 - time)
    np.testing.assert_allclose(prediction, expected, rtol=1e-14, atol=1e-15)
    np.testing.assert_allclose(
        evaluate_tree(tree, time), expected, rtol=1e-14, atol=1e-15
    )
    residual = observed - expected
    reference_loss = residual @ np.linalg.solve(covariance, residual) / time.size
    np.testing.assert_allclose(loss, reference_loss, rtol=1e-13, atol=0)
    # Full tree round trips retain a nondecimal Float64 and signed zero too.
    for value in (np.nextafter(1.0, 2.0), -0.0, np.nextafter(0.0, 1.0)):
        exported = _export_tree(c(float(value)), options)
        assert exported["value_hex"] == float(value).hex()
        assert _export_tree(_import_tree(exported, backend), options) == exported
    try:
        backend.bind_context(array(time), array(observed), None)
    except JuliaError as error:
        assert "already bound" in str(error)
    else:
        raise AssertionError("A second context was accepted in one worker.")
    print(
        "Exact tree, independent full-covariance replay and actual PySR score edges passed."
    )


def check_arm(directory, covariance, expected_zero):
    run = run_search_arm(
        [0.0, 1.0],
        [1.0, 0.0],
        covariance=covariance,
        output=directory,
        budget=SearchBudget(
            niterations=1, populations=1, population_size=16, ncycles_per_iteration=2
        ),
    )
    if run.status != "success":
        raise AssertionError((directory / "worker.log").read_text())
    result = json.loads((directory / "result.json").read_text())
    metadata = json.loads((directory / "metadata.json").read_text())
    assert metadata["worker_pid"] != os.getpid()
    assert result["callback_calls_during_fit"] > 0
    np.testing.assert_allclose(
        result["zero_expression_loss"], expected_zero, rtol=1e-14, atol=0
    )
    assert result["selected_index"] == select_candidate(result["candidates"])
    checksums = json.loads((directory / "checksums.json").read_text())
    for name, expected in checksums.items():
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == expected
    with np.load(directory / "inputs.npz", allow_pickle=False) as inputs:
        assert set(inputs.files) == (
            {"time_s", "observed"}
            if covariance is None
            else {"time_s", "observed", "covariance"}
        )
    for candidate in result["candidates"]:
        predicted = evaluate_tree(candidate["tree"], [0.0, 1.0])
        residual = np.array([1.0, 0.0]) - predicted
        matrix = np.eye(2) if covariance is None else np.array(covariance)
        independent = residual @ np.linalg.solve(matrix, residual) / 2
        np.testing.assert_allclose(candidate["loss"], independent, rtol=1e-10, atol=0)
    print(
        f"Isolated {directory.name}: {len(result['candidates'])} candidates, zero loss {expected_zero}."
    )
    return result


def main():
    if os.environ.get("PYTHON_JULIACALL_PROJECT") != str(ROOT / "julia"):
        raise SystemExit("Run through scripts/run_python.py.")
    check_tree_and_score_references()
    with tempfile.TemporaryDirectory(prefix="ringdown-sr-search-") as temporary:
        root = Path(temporary)
        covariance = [[2.5, 1.5], [1.5, 4.5]]
        a = check_arm(root / "A weighted", covariance, 0.25)
        check_arm(root / "B ordinary", None, 0.5)
        again = check_arm(root / "A repeated", covariance, 0.25)
        np.testing.assert_allclose(
            a["candidates"][a["selected_index"]]["loss"],
            again["candidates"][again["selected_index"]]["loss"],
            rtol=1e-12,
            atol=0,
        )
    print("Free PySR adapter and A-B-A process isolation check passed.")


if __name__ == "__main__":
    main()
