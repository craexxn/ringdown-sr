"""Replay two archived CSV regression trees natively, without fitting or searching."""

import argparse
import json
from pathlib import Path

import numpy as np

from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import backend_seed
from ringdown_sr.duration_replay import candidate_evidence, verify_loss_replay
from ringdown_sr.losses import mean_squared_error
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _sha256, _write_json
from ringdown_sr.representation_control import diagnose_candidate
from ringdown_sr.search_duration import load_module, source_hashes


def check():
    sources = source_hashes()
    fixture_path = symbolic.ROOT / "tests/fixtures/duration_replay_cases.json"
    fixture_bytes = fixture_path.read_bytes()
    fixture = json.loads(fixture_bytes)
    loader = load_module(
        symbolic.ROOT / "scripts/check_trigonometric_grammar_backend.py",
        "duration_fixed_replay_backend",
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
        path = symbolic.ROOT / "julia/src" / name
        if _sha256(path.read_bytes()) != sources["julia/src/" + name]:
            raise ValueError("Native regression source changed.")
        jl.include(str(path))
    backend = jl.RingdownSRSearch
    grammar = jl.TrigonometricGrammar
    arrays = frozen_data()
    # Historical losses belong to these actual input bits, not a new evaluation
    # of the analytical signal using this host's vector math implementation.
    arrays.update(
        {
            key: np.asarray(values, dtype=np.float64)
            for key, values in fixture["training_inputs"].items()
        }
    )
    array = lambda values: convert(jl.Array[jl.Float64], values)
    backend.bind_context(array(arrays["time_s"]), array(arrays["observed"]), None)
    seed = backend_seed(20261103)
    grammar.configure("no_nested_trig", seed)
    options = grammar.reference_options("no_nested_trig", seed)
    records = []
    for case in fixture["cases"]:
        tree = case["tree"]
        restored = symbolic._import_tree(tree, backend)
        assert symbolic._export_tree(restored, options) == tree
        assert bool(jl.SymbolicRegression.check_constraints(restored, options))
        assert (
            int(jl.SymbolicRegression.compute_complexity(restored, options))
            == case["complexity"]
        )
        native, loss = backend.replay(restored, options)
        native, loss = np.asarray(native, dtype=np.float64), float(loss)
        assert loss.hex() == case["native_loss"].hex()
        np.testing.assert_array_equal(
            native.view(np.uint64),
            np.asarray(case["native_prediction"]).view(np.uint64),
        )
        python = symbolic.evaluate_tree(tree, arrays["time_s"])
        python_loss = mean_squared_error(arrays["observed"] - python)
        record = verify_loss_replay(
            arrays["observed"], native, python, loss, loss, loss, python_loss, None
        )
        candidate = {
            "tree": tree,
            "complexity": case["complexity"],
            "display_equation": case["display_equation"],
            "loss": loss,
            "julia_reimport_loss": loss,
            "python_loss": python_loss,
            "prediction": native.tolist(),
            "residual": (arrays["observed"] - native).tolist(),
            "loss_replay": record,
        }
        assert (
            candidate_evidence(candidate, arrays["time_s"], arrays["observed"])
            == record
        )
        diagnosis = diagnose_candidate(
            candidate, 0, -1, arrays, "complexity_frequency", extended_structure=True
        )
        assert diagnosis["curve_marker"] == "within_tolerance"
        assert diagnosis["parameter_match"]["status"] == "matched"
        assert diagnosis["physical_analysis"]["raw_replay"]["status"] == "passed"
        assert diagnosis["physical_analysis"]["alias_replay"]["status"] == "passed"
        assert diagnosis["physical_identification"] == "not_assessed"
        records.append(
            {
                "csv_index": case["csv_index"],
                "loss_replay": record,
                "diagnosis": diagnosis,
            }
        )
    assert len(records) == 2 and int(backend.CALLS[()]) == 0
    assert source_hashes() == sources and fixture_path.read_bytes() == fixture_bytes
    return {
        "status": "verified",
        "scope": "two fixed post-hoc CSV trees; no search, fit or recovered original selection",
        "source_sha256": sources,
        "fixture_sha256": _sha256(fixture_bytes),
        "original_archive_sha256": fixture["archive_sha256"],
        "objective_calls": 0,
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
    _write_json(output, check())
    print(
        "Two native duration loss/structure regression cases passed; no search or fit."
    )
