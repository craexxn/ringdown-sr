"""Check fixed coordinate/alias trees through the pinned callback, without fit."""

import argparse
import math
import os
from pathlib import Path

import numpy as np

from ringdown_sr import symbolic
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _utc_now, _write_json
from ringdown_sr.representation_control import (
    CONDITIONS,
    condition_settings,
    diagnose_candidate,
    search_coordinates,
)
from ringdown_sr.representation_profiles import source_hashes

ROOT = symbolic.ROOT


def inspect_references():
    sources = source_hashes()
    if os.environ.get("PYTHON_JULIACALL_PROJECT") != str(ROOT / "julia"):
        raise RuntimeError("Use the pinned scripts/run_python.py launcher.")
    import pysr
    from juliacall import JuliaError, convert
    from juliacall import Main as jl

    if (
        pysr.__version__ != "2.6.0"
        or str(jl.seval("string(VERSION)")) != "1.13.1"
        or str(jl.seval("string(Base.pkgversion(SymbolicRegression))")) != "2.5.1"
    ):
        raise ValueError("Unexpected reference backend versions.")
    arrays = frozen_data()
    bits = arrays["observed"].view(np.uint64).copy()
    np.testing.assert_array_equal(arrays["time_s"], np.arange(128) / 4096)
    expected_inner = np.array([j / 32768 for j in range(1, 1016) if j % 8])
    np.testing.assert_array_equal(arrays["diagnostic_time_s"], expected_inner)
    results = []

    def array(values):
        return convert(jl.Array[jl.Float64], np.asarray(values, dtype=np.float64))

    for number, condition in enumerate(CONDITIONS):
        # Fixed references have separate native contexts and never enter a fit.
        name = f"RepresentationReference{number}"
        jl.seval(f"module {name} end")
        namespace = getattr(jl, name)
        for source in (
            "RingdownSRLoss.jl",
            "RingdownSRSearch.jl",
            "RepresentationProfiles.jl",
        ):
            jl.Base.include(namespace, str(ROOT / "julia/src" / source))
        backend = namespace.RingdownSRSearch
        profile = namespace.RepresentationProfiles
        coordinate = search_coordinates(arrays, condition)
        scale = condition_settings(condition)["time_scale"]
        np.testing.assert_array_equal(
            coordinate["time_s"], np.arange(128) / (4096 / scale)
        )
        np.testing.assert_array_equal(coordinate["observed"].view(np.uint64), bits)
        backend.bind_context(
            array(coordinate["time_s"]), array(coordinate["observed"]), None
        )
        profile.configure(condition, 465951028)
        options = profile.reference_options(condition, 465951028)
        dataset = backend.CONTEXT[()]._dataset
        c, t, u, b = (
            backend.constant,
            backend.variable(1),
            backend.unary,
            backend.binary,
        )
        for frequency in (250, 4346, 33018):
            root = b(
                3,
                c(1.0),
                b(
                    3,
                    u(1, b(3, c(-125 / scale), t)),
                    u(3, b(3, c(2 * math.pi * frequency / scale), t)),
                ),
            )
            assert int(jl.SymbolicRegression.compute_complexity(root, options)) == 11
            loss = float(jl.SymbolicRegression.eval_loss(root, dataset, options))
            assert math.isfinite(loss) and loss < 1e-24
            prediction, replay_loss = backend.replay(root, options)
            prediction = np.asarray(prediction)
            independent = np.exp(-125 * arrays["time_s"]) * np.cos(
                2 * np.pi * frequency * arrays["time_s"]
            )
            symbolic._check_prediction_replay(independent, prediction)
            native_mse = float(
                np.linalg.norm(arrays["observed"] - prediction) ** 2 / 128
            )
            np.testing.assert_allclose(loss, native_mse, rtol=1e-12, atol=0)
            np.testing.assert_allclose(replay_loss, loss, rtol=0, atol=0)
            tree = symbolic._export_tree(root, options)
            item = {
                "tree": tree,
                "complexity": 11,
                "loss": loss,
                "display_equation": "fixed reference",
            }
            diagnosis = diagnose_candidate(item, 0, 0, arrays, condition)
            assert diagnosis["curve_marker"] == (
                "outside_tolerance" if frequency == 4346 else "within_tolerance"
            )
            assert diagnosis["parameter_match"]["status"] == "matched"
            physical = diagnosis["physical_analysis"]
            np.testing.assert_allclose(
                physical["raw_parameters"]["frequency_raw_hz"]["value"],
                frequency,
                rtol=1e-12,
            )
            np.testing.assert_allclose(
                physical["raw_parameters"]["decay_time_s"]["value"], 0.008, rtol=1e-12
            )
            np.testing.assert_allclose(
                physical["alias"]["frequency_alias_hz"]["value"], 250, rtol=1e-12
            )
            assert (
                physical["raw_replay"]["status"]
                == physical["alias_replay"]["status"]
                == "passed"
            )
            # Verify native full-tree evaluation on the independent eighth-grid too.
            inner, complete = jl.SymbolicRegression.eval_tree_array(
                root, array(coordinate["diagnostic_time_s"].reshape(1, -1)), options
            )
            assert complete
            symbolic._check_prediction_replay(
                symbolic.evaluate_tree(tree, scale * expected_inner), np.asarray(inner)
            )
            if frequency == 33018:
                off_grid = np.array([1 / (16 * 4096)])
                np.testing.assert_allclose(
                    symbolic.evaluate_tree(tree, scale * off_grid),
                    -np.exp(-125 * off_grid) * np.cos(2 * np.pi * 250 * off_grid),
                    rtol=1e-12,
                    atol=1e-14,
                )
            results.append(
                {
                    "condition": condition,
                    "physical_frequency_hz": frequency,
                    "native_mse": loss,
                    "independent_residual_mse": native_mse,
                    "complexity": 11,
                    "diagnosis": diagnosis,
                }
            )
        assert math.isinf(float(jl.SymbolicRegression.eval_loss(t, dataset, options)))
        # A changed seed must fail before the numeric callback can increment.
        before = int(backend.CALLS[()])
        bad = profile.reference_options(condition, 465951029)
        try:
            jl.SymbolicRegression.eval_loss(c(0.0), dataset, bad)
        except JuliaError:
            pass
        else:
            raise AssertionError("Native seed guard accepted a forged option object.")
        assert int(backend.CALLS[()]) == before
        profile.verification_record(options)
    if source_hashes() != sources:
        raise ValueError("Sources changed during fixed-reference checks.")
    return {
        "format": "ringdown-sr-representation-references-1",
        "status": "verified",
        "scope": "nine fixed coordinate/alias references; no fit/search/optimization",
        "created_at_utc": _utc_now(),
        "source_sha256": sources,
        "cases": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    path = parser.parse_args().output.resolve()
    if path.exists():
        raise FileExistsError(path)
    if any(
        path.is_relative_to(ROOT / name)
        for name in ("src", "scripts", "docs", "julia", ".git")
    ):
        raise ValueError("Output must not overlap sources.")
    result = inspect_references()
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, result)
    print(
        "Representation references passed: nine fixed trees, units, aliases and native guard; no fit/search."
    )


if __name__ == "__main__":
    main()
