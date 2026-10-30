"""Internal pinned process for one fixed-structure diagnostic or pure controls."""

import argparse
import json
import math
import os
from pathlib import Path

import numpy as np

from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import SEEDS, backend_seed, verify_manifest
from ringdown_sr.noiseless_control import diagnose_candidate
from ringdown_sr.pilot import _environment, _write_json
from ringdown_sr.representation_profiles import plugin_records, validate_plugin_records


def native_runtime(runtime):
    if os.environ.get("PYTHON_JULIACALL_PROJECT") != str(symbolic.ROOT / "julia"):
        raise RuntimeError("Use scripts/run_python.py.")
    import pysr
    from juliacall import Main as jl

    if (
        pysr.__version__,
        str(jl.VERSION),
        str(jl.seval("Base.pkgversion(SymbolicRegression)")),
    ) != ("2.6.0", "1.13.1", "2.5.1"):
        raise ValueError("Wrong diagnostic backend versions.")
    for name in (
        "RingdownSRLoss.jl",
        "RingdownSRSearch.jl",
        "RepresentationProfiles.jl",
        "ConstantDiagnostic.jl",
    ):
        jl.include(str(runtime / name))
    return jl


def vector(values):
    return [float(x).hex() for x in values]


def option_record(jl, options):
    plugins = plugin_records(jl.RepresentationProfiles.plugin_records(options))
    validate_plugin_records(plugins, "baseline")
    return {
        "backend_options": [
            {"name": str(x.name), "type": str(x.type), "value": str(x.value)}
            for x in jl.RingdownSRSearch.option_fields(options)
        ],
        "optimizer_settings": {
            str(x.name): str(x.value)
            for x in jl.ConstantDiagnostic.optimizer_settings(options)
        },
        "plugins": plugins,
    }


def blas_check():
    # Reuse the actual-pool verifier without importing or running archived code.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "diagnostic_blas_probe", symbolic.ROOT / "scripts/probe_symbolic_numerics.py"
    )
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    probe.validate_core_request("Haswell")
    env = _environment()
    return {
        "environment": env,
        "verification": probe.verify_blas_control(env, "Haswell", require_julia=True),
    }


def verify_blas_snapshots(result):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "diagnostic_blas_verifier", symbolic.ROOT / "scripts/probe_symbolic_numerics.py"
    )
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    for phase in ("blas_before", "blas_after"):
        record = result[phase]
        if (
            probe.verify_blas_control(
                record["environment"], "Haswell", require_julia=True
            )
            != record["verification"]
        ):
            raise ValueError("Contradictory actual BLAS snapshot.")


def run(directory):
    runtime = Path(__file__).resolve().parent
    verify_manifest(directory, runtime)
    request = json.loads((directory / "request.json").read_bytes())
    jl = native_runtime(runtime)
    from juliacall import convert

    with np.load(directory / "inputs.npz", allow_pickle=False) as saved:
        if set(saved.files) != {"time_s", "observed"}:
            raise ValueError("Unexpected optimizer input roles.")
        time, observed = saved["time_s"], saved["observed"]
    array = lambda a: convert(jl.Array[jl.Float64], np.asarray(a, dtype=np.float64))
    jl.RingdownSRSearch.bind_context(array(time), array(observed), None)
    before = blas_check()
    seed = backend_seed(request["seed"])
    module = jl.ConstantDiagnostic
    if request.get("mode") == "controls":
        controls = module.controls(
            array(time), array(observed), request["iterations"], seed
        )
        records = []
        for case in controls:
            tree = symbolic._export_tree(case.tree, case.options)
            loss = float(case.loss)
            records.append({"tree": tree, "loss_hex": loss.hex()})
        result = {"request": request, "controls": records}
        result.update(option_record(jl, controls[0].options))
        result["rng_references"] = {}
        for python_seed in SEEDS:
            ref = module.rng_reference(backend_seed(python_seed))
            result["rng_references"][str(python_seed)] = {
                "before": [str(x) for x in ref.before],
                "after": [str(x) for x in ref.after],
                "draws": [vector(x) for x in ref.draws],
            }
    else:
        if set(request) != {"number", "start", "seed", "iterations"}:
            raise ValueError("Unexpected diagnostic request fields.")
        native = module.run(
            array(time),
            array(observed),
            array(request["start"]["parameters"]),
            request["iterations"],
            seed,
        )
        parameters = np.array(request["start"]["parameters"])
        draws = [np.asarray(x) for x in native.draws]
        plugins = plugin_records(
            jl.RepresentationProfiles.plugin_records(native.options)
        )
        validate_plugin_records(plugins, "baseline")
        result = {
            "request": request,
            "backend_seed": seed,
            "tree": symbolic._export_tree(native.tree, native.options),
            "initial_parameters": vector(parameters),
            "parameters": vector(native.parameters),
            "prediction": vector(native.prediction),
            "residual": vector(native.residual),
            "initial_loss": float(native.initial_loss),
            "loss": float(native.loss),
            "rng_type": "Random.Xoshiro",
            "rng_before": [str(x) for x in native.rng_before],
            "rng_after": [str(x) for x in native.rng_after],
            "restart_draws": [vector(x) for x in draws],
            "restart_parameters": [
                vector(np.where(parameters == 0, x, parameters * (1 + 0.5 * x)))
                for x in draws
            ],
            "states": [
                {
                    "kind": str(s.kind),
                    "local_index": int(s.local_index),
                    "step": int(s.step),
                    "parameters": vector(s.parameters),
                    "loss_hex": float(s.loss).hex(),
                    "gradient": vector(s.gradient),
                }
                for s in native.states
            ],
            "fit_callback_count": int(native.fit_calls),
            "total_callback_count": int(native.total_calls),
            "backend_evaluation_count": float(native.evaluations),
            "optimization_seconds": float(native.elapsed),
            "termination": {
                "status": "unavailable",
                "reason": "backend_does_not_return_local_optim_results",
            },
            "backend_options": [
                {"name": str(x.name), "type": str(x.type), "value": str(x.value)}
                for x in jl.RingdownSRSearch.option_fields(native.options)
            ],
            "plugins": plugins,
            "option_verification": "passed",
        }
        result.update(option_record(jl, native.options))
    result["blas_before"] = before
    result["blas_after"] = blas_check()
    verify_manifest(directory, runtime)
    _write_json(directory / "result.json", result)


def verify_controls(result, arrays):
    expected = (250, 4346, 33018)
    for i, record in enumerate(result["controls"]):
        tree = record["tree"]
        loss = float.fromhex(record["loss_hex"])
        if i == 4:
            if not math.isinf(loss) or tree["operator"] != "sin":
                raise ValueError("Units control failed.")
            continue
        prediction = symbolic.evaluate_tree(tree, arrays["time_s"])
        residual = arrays["observed"] - prediction
        independent = math.fsum(float(x) ** 2 for x in residual) / len(residual)
        if not math.isclose(loss, independent, rel_tol=1e-10, abs_tol=1e-26):
            raise ValueError("Control residual mismatch.")
        if i < 3:
            reference = np.exp(-125 * arrays["time_s"]) * np.cos(
                2 * np.pi * expected[i] * arrays["time_s"]
            )
            symbolic._check_prediction_replay(reference, prediction)
            candidate = {
                "tree": tree,
                "complexity": 13,
                "loss": loss,
                "display_equation": "fixed control",
            }
            diagnosis = diagnose_candidate(candidate, 0, 0, arrays)
            if diagnosis["curve_marker"] != (
                "outside_tolerance" if i == 1 else "within_tolerance"
            ):
                raise ValueError("Alias diagnostic control failed.")
        else:
            # Julia and NumPy reductions use different summation orders. Bound
            # roundoff against an independent faithfully rounded scalar sum.
            reference_mean = math.fsum(arrays["observed"]) / len(arrays["observed"])
            bound = np.finfo(float).eps * math.fsum(abs(x) for x in arrays["observed"])
            if np.any(np.abs(prediction - reference_mean) > bound):
                raise ValueError("Optimal constant control failed.")
    if len(result["controls"]) != 5:
        raise ValueError("Missing pure controls.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    run(parser.parse_args().directory.resolve())
