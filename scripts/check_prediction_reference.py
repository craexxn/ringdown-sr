"""Replay 44 fixed trees and check MPFR ranges/native node order without searching."""

import argparse
import copy
import json
import time
from fractions import Fraction
from pathlib import Path

import gmpy2
import numpy as np

from ringdown_sr import prediction_reference as reference
from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import backend_seed
from ringdown_sr.duration_replay import candidate_evidence
from ringdown_sr.losses import mean_squared_error
from ringdown_sr.pilot import _sha256, _write_json
from ringdown_sr.search_duration import load_module, source_hashes


def constant(x):
    return {"kind": "constant", "value_hex": float(x).hex()}


def operator(name, *children):
    names = symbolic.UNARY if len(children) == 1 else symbolic.BINARY
    return {
        "kind": "operator",
        "operator": name,
        "arity": len(children),
        "operator_index": names.index(name) + 1,
        "children": list(children),
    }


def check():
    sources = source_hashes()
    path = symbolic.ROOT / "tests/fixtures/duration_prediction_cases.json"
    contents = path.read_bytes()
    fixture = json.loads(contents)
    arrays = {
        k: np.array(v, dtype=np.float64) for k, v in fixture["training_inputs"].items()
    }
    loader = load_module(
        symbolic.ROOT / "scripts/check_trigonometric_grammar_backend.py",
        "prediction_native_reference",
    )
    jl = loader.native_runtime()
    from juliacall import convert

    for name in (
        "RingdownSRLoss.jl",
        "RingdownSRSearch.jl",
        "RepresentationProfiles.jl",
        "FreeOptimizerBudget.jl",
        "TrigonometricGrammar.jl",
    ):
        jl.include(str(symbolic.ROOT / "julia/src" / name))
    backend, grammar = jl.RingdownSRSearch, jl.TrigonometricGrammar
    array = lambda v: convert(jl.Array[jl.Float64], v)
    backend.bind_context(array(arrays["time_s"]), array(arrays["observed"]), None)
    records = []
    started = time.monotonic()
    reference_seconds = 0.0
    for case in fixture["cases"]:
        candidate = copy.deepcopy(case["candidate"])
        condition = "unrestricted" if case["cell"] in (1, 4) else "no_nested_trig"
        seed = backend_seed(20261104 if case["cell"] == 5 else 20261103)
        options = grammar.reference_options(condition, seed, should_simplify=False)
        tree = symbolic._import_tree(candidate["tree"], backend)
        assert symbolic._export_tree(tree, options) == candidate["tree"]
        assert bool(jl.SymbolicRegression.check_constraints(tree, options))
        assert (
            int(jl.SymbolicRegression.compute_complexity(tree, options))
            == candidate["complexity"]
        )
        native, loss = backend.replay(tree, options)
        native = np.asarray(native, dtype=np.float64)
        assert float(loss).hex() == candidate["julia_reimport_loss"].hex()
        np.testing.assert_array_equal(
            native.view(np.uint64), np.asarray(candidate["prediction"]).view(np.uint64)
        )
        python = symbolic.evaluate_tree(candidate["tree"], arrays["time_s"])
        before = time.monotonic()
        proof = reference.verify_prediction(
            candidate["tree"], arrays["time_s"], python, native
        )
        reference_seconds += time.monotonic() - before
        assert proof["precision_bits"] == 128
        candidate["python_loss"] = mean_squared_error(arrays["observed"] - python)
        candidate.setdefault("loss_replay", {"table_loss": candidate["loss"]})
        loss_proof = candidate_evidence(
            candidate, arrays["time_s"], arrays["observed"], prediction_check=proof
        )
        records.append(
            {
                "cell": case["cell"],
                "index": case["index"],
                "origin": case["origin"],
                "prediction": proof,
                "loss": loss_proof,
            }
        )
    # A separately implemented directed reference in the pinned Julia MPFR.
    directed = jl.seval("""function prediction_directed_test(op, x, p, upper)
        setprecision(BigFloat, p) do
            setrounding(BigFloat, upper ? RoundUp : RoundDown) do
                f = op == "exp" ? exp : op == "sin" ? sin : cos
                q = Rational{BigInt}(f(BigFloat(x)))
                (string(numerator(q)), string(denominator(q)))
            end
        end
    end""")
    assertions = 0
    for precision in reference.PRECISIONS:
        for name in ("exp", "sin", "cos"):
            for x in (
                -745.0,
                -1.0,
                0.0,
                float.fromhex("-0x1.9e8846667be65p-11"),
                1.0,
                700.0,
            ):
                for upper, rounding in (
                    (False, gmpy2.RoundDown),
                    (True, gmpy2.RoundUp),
                ):
                    numerator, denominator = directed(name, x, precision, upper)
                    independent = Fraction(int(str(numerator)), int(str(denominator)))
                    assert (
                        reference._directed(name, Fraction(x), precision, rounding)
                        == independent
                    )
                    assertions += 1
    # Native exported evaluation must retain the multiplication rounding point.
    options = grammar.reference_options(
        "unrestricted", backend_seed(20261103), should_simplify=False
    )
    for power in (27, 52):
        tree = operator(
            "-",
            operator("*", constant(1 + 2.0**-power), constant(1 - 2.0**-power)),
            constant(1),
        )
        native, _ = backend.replay(symbolic._import_tree(tree, backend), options)
        assert np.all(np.asarray(native) == 0.0)
        assert float(jl.fma(1 + 2.0**-power, 1 - 2.0**-power, -1.0)) == -(
            2.0 ** (-2 * power)
        )
        reference.verify_prediction(
            tree,
            arrays["time_s"],
            symbolic.evaluate_tree(tree, arrays["time_s"]),
            np.asarray(native),
        )
        assertions += 3
    tree = operator(
        "+",
        operator(
            "-",
            operator("-", {"kind": "variable", "index": 1}, constant(1e16)),
            constant(-1e16),
        ),
        constant(1),
    )
    # This operation-order counterexample mixes dimensions, so test the native
    # evaluator directly, without claiming admission by the physical loss.
    native, complete = jl.SymbolicRegression.eval_tree_array(
        symbolic._import_tree(tree, backend),
        array(arrays["time_s"].reshape(1, -1)),
        options,
    )
    assert bool(complete) and np.all(np.asarray(native) == 1.0)
    reference.verify_prediction(
        tree,
        arrays["time_s"],
        symbolic.evaluate_tree(tree, arrays["time_s"]),
        np.asarray(native),
    )
    assertions += 2
    assert int(backend.CALLS[()]) == 0
    assert source_hashes() == sources and path.read_bytes() == contents
    return {
        "status": "verified",
        "scope": "44 fixed trees, directed cross-library ranges and native node order; no search or fit",
        "fixture_sha256": _sha256(contents),
        "original_archive_sha256": fixture["archive_sha256"],
        "source_sha256": sources,
        "objective_calls": 0,
        "julia": str(jl.VERSION),
        "julia_mpfr": str(jl.seval("Base.MPFR.version()")),
        "reference_runtime": reference.binding()["library"],
        "independent_assertions": assertions,
        "reference_seconds_44": reference_seconds,
        "total_check_seconds": time.monotonic() - started,
        "cases": records,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    if output.exists() or any(
        output.is_relative_to(symbolic.ROOT / name)
        for name in ("src", "scripts", "tests", "docs", "julia", ".git")
    ):
        raise ValueError("Use a new technical output outside sources.")
    result = check()
    _write_json(output, result)
    print(
        f"44 fixed-tree prediction and loss checks passed; {result['independent_assertions']} independent/native assertions; no search or fit."
    )
