"""Check native diagnostic instrumentation on technical fixtures, without the series."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from run_constant_diagnostic_worker import (
    blas_check,
    native_runtime,
    option_record,
    verify_controls,
)

from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import (
    RUNTIME,
    backend_seed,
    source_hashes,
    verify_manifest,
    verify_options_record,
    verify_result,
)
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _sha256, _write_json


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
    # Exercise the real runtime copy, launcher, export and parent verifier too.
    process_records = []
    fixture_arrays = {
        "time_s": time,
        "observed": observed,
        "diagnostic_time_s": time[1:] - 0.05,
        "diagnostic_truth": 2
        * np.exp(-2 * (time[1:] - 0.05))
        * np.cos(3 * (time[1:] - 0.05) + 0.2),
    }
    with tempfile.TemporaryDirectory(prefix="constant-technical-") as temporary:
        root = Path(temporary)
        runtime = root / "runtime"
        runtime.mkdir()
        for name, src in RUNTIME.items():
            (runtime / name).write_bytes((symbolic.ROOT / src).read_bytes())
        for budget in (20, 100):
            directory = root / str(budget)
            directory.mkdir()
            request = {
                "number": 1,
                "start": {"name": "TECH", "parameters": [1.9, -2.1, 2.9, 0.21]},
                "seed": 1234,
                "iterations": budget,
            }
            _write_json(directory / "request.json", request)
            np.savez(directory / "inputs.npz", time_s=time, observed=observed)
            _write_json(
                directory / "manifest.json",
                {
                    "sources": sources,
                    "runtime": {name: sources[src] for name, src in RUNTIME.items()},
                    "inputs": {
                        name: _sha256((directory / name).read_bytes())
                        for name in ("request.json", "inputs.npz")
                    },
                },
            )
            subprocess.run(
                [
                    sys.executable,
                    str(symbolic.ROOT / "scripts/run_python.py"),
                    str(runtime / "worker.py"),
                    str(directory),
                ],
                check=True,
                timeout=180,
            )
            verify_manifest(directory, runtime)
            result = json.loads((directory / "result.json").read_bytes())
            verify_result(result, request, fixture_arrays)
            reference_options = jl.ConstantDiagnostic.controls(
                array(arrays["time_s"]),
                array(arrays["observed"]),
                budget,
                backend_seed(1234),
            )[0].options
            reference = option_record(jl, reference_options)
            rng = jl.ConstantDiagnostic.rng_reference(backend_seed(1234))
            reference["rng_references"] = {
                "1234": {
                    "before": [str(x) for x in rng.before],
                    "after": [str(x) for x in rng.after],
                    "draws": [[float(x).hex() for x in row] for row in rng.draws],
                }
            }
            verify_options_record(result, reference)
            process_records.append(result)
    after = blas_check()
    if source_hashes() != sources:
        raise ValueError("Sources changed during native technical checks.")
    return {
        "format": "ringdown-sr-constant-technical-1",
        "status": "passed",
        "source_sha256": sources,
        "scope": "ten pure controls, four direct and two isolated technical fixture optimizations; no scientific series or free search",
        "fixtures": records,
        "isolated_workers": process_records,
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
