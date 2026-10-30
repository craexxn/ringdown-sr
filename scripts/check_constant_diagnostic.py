"""Check native diagnostic instrumentation on technical fixtures, without the series."""

import argparse
from pathlib import Path

import numpy as np
from run_constant_diagnostic_worker import blas_check, native_runtime, verify_controls

from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import source_hashes
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _write_json


def check():
    sources = source_hashes()
    jl = native_runtime(symbolic.ROOT / "julia/src")
    from juliacall import convert

    def array(a):
        return convert(jl.Array[jl.Float64], np.asarray(a, dtype=np.float64))

    before = blas_check()
    # Separate native modules allow immutable contexts for pure controls and fixtures.
    arrays = frozen_data()
    jl.RingdownSRSearch.bind_context(
        array(arrays["time_s"]), array(arrays["observed"]), None
    )
    for budget in (20, 100):
        native = jl.ConstantDiagnostic.controls(
            array(arrays["time_s"]), array(arrays["observed"]), budget, 1234
        )
        verify_controls(
            {
                "controls": [
                    {
                        "tree": symbolic._export_tree(c.tree, c.options),
                        "loss_hex": float(c.loss).hex(),
                    }
                    for c in native
                ]
            },
            arrays,
        )
    jl.seval("module TechnicalConstantCheck end")
    ns = jl.TechnicalConstantCheck
    for name in (
        "RingdownSRLoss.jl",
        "RingdownSRSearch.jl",
        "RepresentationProfiles.jl",
        "ConstantDiagnostic.jl",
    ):
        jl.Base.include(ns, str(symbolic.ROOT / "julia/src" / name))
    time = np.arange(8) / 10
    observed = 2 * np.exp(-2 * time) * np.cos(3 * time + 0.2)
    ns.RingdownSRSearch.bind_context(array(time), array(observed), None)
    records = []
    for budget in (20, 100):
        args = (
            array(time),
            array(observed),
            array([1.9, -2.1, 2.9, 0.21]),
            budget,
            1234,
        )
        plain = ns.ConstantDiagnostic.run(*args, instrument=False)
        watched = ns.ConstantDiagnostic.run(*args)
        assert float(watched.loss) < float(watched.initial_loss)
        assert [str(x) for x in plain.rng_before] == [
            str(x) for x in watched.rng_before
        ]
        assert [str(x) for x in plain.rng_after] == [str(x) for x in watched.rng_after]
        assert float(plain.loss).hex() == float(watched.loss).hex()
        np.testing.assert_array_equal(
            np.asarray(plain.parameters), np.asarray(watched.parameters)
        )
        assert int(plain.fit_calls) == int(watched.fit_calls)
        assert len(watched.draws) == 2
        assert {int(s.local_index) for s in watched.states} == {1, 2, 3}
        prediction = np.asarray(watched.prediction)
        p = np.asarray(watched.parameters)
        reference = p[0] * (np.exp(p[1] * time) * np.cos(p[2] * time + p[3]))
        symbolic._check_prediction_replay(reference, prediction)
        np.testing.assert_allclose(
            float(watched.loss),
            np.sum((observed - prediction) ** 2) / len(time),
            rtol=1e-10,
        )
        records.append(
            {
                "iterations": budget,
                "loss": float(watched.loss),
                "fit_calls": int(watched.fit_calls),
                "instrumentation_identical": True,
            }
        )
    after = blas_check()
    if source_hashes() != sources:
        raise ValueError("Sources changed during native technical checks.")
    return {
        "format": "ringdown-sr-constant-technical-1",
        "status": "passed",
        "source_sha256": sources,
        "scope": "ten pure controls and four technical fixture optimizations; no scientific series or free search",
        "fixtures": records,
        "blas_before": before,
        "blas_after": after,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    path = parser.parse_args().output.resolve()
    if path.exists():
        raise FileExistsError(path)
    result = check()
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, result)
    print("Constant diagnostic technical checks passed; no scientific series.")
