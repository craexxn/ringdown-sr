"""Run or read-only verify four bound fixed-structure scaling diagnostics."""

import argparse
import copy
import math
import os
from pathlib import Path

import numpy as np

from ringdown_sr import confirmed_profile as confirmed
from ringdown_sr import symbolic
from ringdown_sr import time_budget_profile as native
from ringdown_sr import white_scaling_worker as worker
from ringdown_sr.constant_diagnostic import backend_seed, ringdown_tree
from ringdown_sr.pilot import _environment, _json_bytes, _sha256, _write_json
from ringdown_sr.prediction_reference import verify_prediction
from ringdown_sr.representation_profiles import plugin_field_record, plugin_records

FORMAT = "ringdown-sr-white-scaling-fixed-1"


def vector(values):
    return [float(value).hex() for value in values]


def decode(values):
    return np.asarray([float.fromhex(value) for value in values], dtype=np.float64)


def options_record(jl, options):
    return {
        "backend_seed": int(options.seed),
        "backend_options": [
            {
                "name": str(field.name),
                "type": str(field.type),
                "value": str(field.value),
            }
            for field in jl.RingdownSRSearch.option_fields(options)
        ],
        "plugins_field": plugin_field_record(
            jl.RepresentationProfiles.plugin_field(options)
        ),
        "plugins": plugin_records(jl.RepresentationProfiles.plugin_records(options)),
        "optimizer_settings": {
            str(field.name): str(field.value)
            for field in jl.SearchTimeBudget.optimizer_settings(options)
        },
    }


def prepared(directory):
    directory = Path(directory)
    request, arrays, manifest = worker.verify_prepared(directory)
    fixed = confirmed.read(directory, "fixed_request.json")
    binding = confirmed.read(directory, "fixed_prepared.json")
    expected = {
        "request_sha256": _sha256((directory / "fixed_request.json").read_bytes()),
        "source_sha256": worker.source_hashes(),
        "prepared_sha256": _sha256((directory / "prepared.json").read_bytes()),
    }
    if (
        binding != expected
        or set(fixed) != {"format", "starts"}
        or fixed["format"] != FORMAT
    ):
        raise ValueError("Changed fixed-structure preparation.")
    amplitude = float(np.max(np.abs(arrays["observed"])))
    duration = 128 / 4096
    parameters = [
        [amplitude, -1 / tau, 2 * math.pi * frequency, math.pi / 2]
        for frequency in (128.0, 512.0)
        for tau in (duration / 8, duration / 2)
    ]
    starts = fixed["starts"]
    if (
        request["technical"]
        or len(arrays["time_s"]) != 128
        or not isinstance(starts, list)
        or len(starts) != 4
        or any(
            not isinstance(item, dict)
            or set(item) != {"name", "parameters"}
            or not isinstance(item["name"], str)
            or not item["name"]
            or vector(item["parameters"]) != vector(values)
            for item, values in zip(starts, parameters, strict=True)
        )
        or len({item["name"] for item in starts}) != 4
    ):
        raise ValueError("Changed fixed-structure starts or data role.")
    return request, arrays, manifest, fixed


def run(directory):
    directory = Path(directory).resolve()
    request, arrays, _, fixed = prepared(directory)
    if (directory / "fixed_result.json").exists():
        raise ValueError("Fixed workers cannot overwrite results.")
    if os.environ.get("PYTHON_JULIACALL_PROJECT") != str(symbolic.ROOT / "julia"):
        raise RuntimeError("Use scripts/run_python.py.")
    import pysr
    from juliacall import Main as jl
    from juliacall import convert

    if (
        pysr.__version__,
        str(jl.VERSION),
        str(jl.seval("Base.pkgversion(SymbolicRegression)")),
    ) != ("2.6.0", "1.13.1", "2.5.1"):
        raise ValueError("Unexpected pinned runtime.")
    for name in worker.NATIVE_FILES:
        jl.include(str(directory / name))
    array = lambda values: convert(
        jl.Array[jl.Float64], np.asarray(values, dtype=np.float64)
    )
    jl.RingdownSRSearch.bind_context(
        array(arrays["time_s"]),
        array(arrays["observed"]),
        None if "covariance" not in arrays else array(arrays["covariance"]),
    )
    module = jl.WhiteLossScaling
    seed = backend_seed(request["budget"]["seed"])
    module.configure(request["arm"], float.fromhex(request["sigma_hex"]), seed)
    reference_options = options_record(jl, module.reference_options(seed))
    runtime = native.checked_runtime(jl)
    backend_sources = native.checked_backend_sources(jl)
    actual_mechanism = worker.checked_mechanism_sources(jl)
    environment = _environment()
    environment["julia_used"] = True
    _, blas_before = confirmed.checked_environment(environment)
    records = []
    reference = module.rng_reference(seed)
    rng_reference = {
        "before": [str(value) for value in reference.before],
        "after": [str(value) for value in reference.after],
        "draws": [vector(values) for values in reference.draws],
    }
    for start in fixed["starts"]:
        result = module.run_fixed(array(start["parameters"]), seed)
        tree = symbolic._export_tree(result.tree, result.options)
        parameters = decode(vector(result.parameters))
        if tree != ringdown_tree(parameters):
            raise ValueError("Native fixed tree changed its original structure.")
        prediction = np.asarray(result.prediction, dtype=np.float64)
        python_prediction = symbolic.evaluate_tree(tree, arrays["time_s"])
        proof = verify_prediction(tree, arrays["time_s"], python_prediction, prediction)
        raw_loss = float(result.loss)
        initial_loss = float(result.initial_loss)
        if (
            not math.isfinite(raw_loss)
            or raw_loss < 0
            or not math.isfinite(initial_loss)
        ):
            raise ValueError("Unusable native fixed-structure loss.")
        a, b, c, d = parameters
        # Exact round-trip decimal constants, preserving the native thirteen nodes.
        formula = f"({a!r} * (exp({b!r} * t) * cos(({c!r} * t) + {d!r})))"
        records.append(
            {
                "start": start,
                "tree": tree,
                "display_equation": formula,
                "display_equation_source": "unchanged_native_tree_with_roundtrip_decimal_constants",
                "units": {"t": "s", "output": "1"},
                "initial_parameters": vector(result.initial_parameters),
                "parameters": vector(result.parameters),
                "prediction": vector(result.prediction),
                "residual": vector(result.residual),
                "initial_loss": initial_loss,
                "loss": raw_loss,
                "prediction_replay": proof,
                "fit_callback_count": int(result.fit_calls),
                "total_callback_count": int(result.total_calls),
                "backend_evaluation_count": float(result.evaluations),
                "optimization_seconds": float(result.elapsed),
                "rng_type": "Random.Xoshiro",
                "rng_before": [str(value) for value in result.rng_before],
                "rng_after": [str(value) for value in result.rng_after],
                "restart_draws": [vector(values) for values in result.draws],
                "restart_parameters": [
                    vector(
                        np.where(
                            np.asarray(start["parameters"]) == 0,
                            values,
                            np.asarray(start["parameters"])
                            * (1 + 0.5 * np.asarray(values)),
                        )
                    )
                    for values in result.draws
                ],
                "states": [
                    {
                        "kind": str(state.kind),
                        "local_index": int(state.local_index),
                        "step": int(state.step),
                        "parameters": vector(state.parameters),
                        "loss_hex": float(state.loss).hex(),
                        "gradient": vector(state.gradient),
                    }
                    for state in result.states
                ],
                "local_steps": [int(value) for value in result.local_steps],
                "termination": {
                    "status": "unavailable",
                    "reason": "backend_discards_local_optim_results",
                },
                "backend_options": [
                    {
                        "name": str(field.name),
                        "type": str(field.type),
                        "value": str(field.value),
                    }
                    for field in jl.RingdownSRSearch.option_fields(result.options)
                ],
                "plugins_field": plugin_field_record(
                    jl.RepresentationProfiles.plugin_field(result.options)
                ),
                "plugins": plugin_records(
                    jl.RepresentationProfiles.plugin_records(result.options)
                ),
                "optimizer_settings": {
                    str(field.name): str(field.value)
                    for field in jl.SearchTimeBudget.optimizer_settings(result.options)
                },
            }
        )
        print(f"Fixed start {start['name']}: completed.", flush=True)
    environment_after = _environment()
    environment_after["julia_used"] = True
    _, blas_after = confirmed.checked_environment(environment_after)
    if (
        runtime != native.checked_runtime(jl)
        or backend_sources != native.checked_backend_sources(jl)
        or actual_mechanism != worker.checked_mechanism_sources(jl)
    ):
        raise ValueError("Native sources or runtime changed during fixed diagnostics.")
    prepared(directory)
    report = {
        "format": FORMAT,
        "request": request,
        "fixed_request": fixed,
        "records": records,
        "reference_options": reference_options,
        "rng_reference": rng_reference,
        "runtime": runtime,
        "backend_sources": backend_sources,
        "mechanism_sources": actual_mechanism,
        "environment_before": environment,
        "environment_after": environment_after,
        "blas_before": blas_before,
        "blas_after": blas_after,
    }
    _write_json(directory / "fixed_result.json", report)
    _write_json(
        directory / "fixed_result_sha256.json",
        {
            "fixed_result.json": _sha256(
                (directory / "fixed_result.json").read_bytes()
            ),
        },
    )
    verify_fixed(directory)


def verify_fixed(directory):
    directory = Path(directory)
    request, arrays, _, fixed = prepared(directory)
    report = confirmed.read(directory, "fixed_result.json")
    if confirmed.read(directory, "fixed_result_sha256.json") != {
        "fixed_result.json": _sha256((directory / "fixed_result.json").read_bytes()),
    }:
        raise ValueError("Changed fixed-structure result.")
    if (
        report["format"] != FORMAT
        or report["request"] != request
        or report["fixed_request"] != fixed
    ):
        raise ValueError("Changed fixed diagnostic binding.")
    native.validate_runtime(report["runtime"])
    if report["backend_sources"] != native.configuration()["reviewed_backend_sources"]:
        raise ValueError("Changed native backend source binding.")
    if report["mechanism_sources"] != worker.MECHANISM_SOURCES:
        raise ValueError("Changed native loss or optimizer source binding.")
    reference_options = copy.deepcopy(report["reference_options"])
    reference_options["condition"] = "iterations"
    for field in reference_options["backend_options"]:
        if field["name"] == "loss_function":
            if field not in [
                {"name": "loss_function", "type": f"typeof({name})", "value": name}
                for name in (worker.OBJECTIVE, worker.OBJECTIVE.removeprefix("Main."))
            ]:
                raise ValueError("Changed fixed reference objective.")
            field.update(type=f"typeof({native.OBJECTIVE})", value=native.OBJECTIVE)
    base = native.load_module(
        symbolic.ROOT / "scripts/run_noiseless_control.py", "white_scaling_fixed_policy"
    )
    native.verify_options(
        reference_options,
        request["budget"]["seed"],
        "iterations",
        base,
        base.load_support(),
    )
    for phase in ("before", "after"):
        _, blas = confirmed.checked_environment(report[f"environment_{phase}"])
        if _json_bytes(blas) != _json_bytes(report[f"blas_{phase}"]):
            raise ValueError("Changed fixed-worker BLAS evidence.")
    records = report["records"]
    if len(records) != 4:
        raise ValueError("Incomplete fixed-structure worker.")
    scale = 1.0 if request["arm"] == "ordinary" else float.fromhex(request["scale_hex"])
    for start, record in zip(fixed["starts"], records, strict=True):
        if record["start"] != start or record["initial_parameters"] != vector(
            start["parameters"]
        ):
            raise ValueError("Changed fixed-structure initial constants.")
        parameters = decode(record["parameters"])
        if record["tree"] != ringdown_tree(parameters):
            raise ValueError("Changed final fixed tree.")
        prediction = symbolic.evaluate_tree(record["tree"], arrays["time_s"])
        saved_prediction = decode(record["prediction"])
        proof = verify_prediction(
            record["tree"], arrays["time_s"], prediction, saved_prediction
        )
        if _json_bytes(proof) != _json_bytes(record["prediction_replay"]):
            raise ValueError("Changed fixed prediction proof.")
        residual = arrays["observed"] - saved_prediction
        if not np.array_equal(residual, decode(record["residual"])):
            raise ValueError("Changed fixed residual.")
        expected = (
            scale * math.fsum(float(value) ** 2 for value in residual) / residual.size
        )
        if not math.isclose(record["loss"], expected, rel_tol=64 * 2**-52, abs_tol=0):
            raise ValueError("Independent loss reference disagrees.")
        initial_prediction = symbolic.evaluate_tree(
            ringdown_tree(start["parameters"]), arrays["time_s"]
        )
        initial_expected = (
            scale
            * math.fsum(
                float(value) ** 2 for value in arrays["observed"] - initial_prediction
            )
            / residual.size
        )
        if not math.isclose(
            record["initial_loss"], initial_expected, rel_tol=1e-10, abs_tol=0
        ):
            raise ValueError("Changed initial loss.")
        if record["loss"] > record["initial_loss"] or (
            record["loss"] == record["initial_loss"]
            and record["parameters"] != record["initial_parameters"]
        ):
            raise ValueError("Fixed optimizer strict-improvement rule contradicted.")
        reference = report["rng_reference"]
        if (
            record["rng_type"] != "Random.Xoshiro"
            or any(
                record[key] != reference[ref]
                for key, ref in (
                    ("rng_before", "before"),
                    ("rng_after", "after"),
                    ("restart_draws", "draws"),
                )
            )
            or len(record["restart_draws"]) != 5
        ):
            raise ValueError("Changed actual restart randomness.")
        values = np.asarray(start["parameters"])
        expected_starts = [
            vector(
                np.where(values == 0, decode(draw), values * (1 + 0.5 * decode(draw)))
            )
            for draw in record["restart_draws"]
        ]
        if expected_starts != record["restart_parameters"]:
            raise ValueError("Changed optimizer restart constants.")
        states = record["states"]
        if {state["local_index"] for state in states} != set(range(1, 7)) or any(
            state["kind"] != "BFGSState" for state in states
        ):
            raise ValueError("Missing actual local optimizer traces.")
        for index in range(1, 7):
            steps = [state["step"] for state in states if state["local_index"] == index]
            if steps != list(range(record["local_steps"][index - 1])):
                raise ValueError("Changed optimizer state ordering.")
        for key in (
            "fit_callback_count",
            "total_callback_count",
            "backend_evaluation_count",
            "optimization_seconds",
        ):
            if (
                type(record[key]) not in (int, float)
                or not math.isfinite(record[key])
                or record[key] <= 0
            ):
                raise ValueError("Invalid fixed-structure cost.")
        settings = record["optimizer_settings"]
        baseline = report["reference_options"]
        fields = {field["name"]: field for field in record["backend_options"]}
        expected_fields = {
            field["name"]: field for field in baseline["backend_options"]
        }
        if (
            len(fields) != len(record["backend_options"])
            or set(fields) != set(expected_fields)
            or any(
                fields[name] != expected_fields[name]
                for name in fields
                if name not in {"loss_function", "optimizer_options"}
            )
        ):
            raise ValueError("Changed fixed effective options.")
        if (
            set(settings) != set(baseline["optimizer_settings"])
            or any(
                settings[name] != baseline["optimizer_settings"][name]
                for name in settings
                if name != "callback"
            )
            or settings["callback"] == "nothing"
        ):
            raise ValueError("Changed fixed effective optimizer settings.")
        if (
            record["plugins"] != baseline["plugins"]
            or record["plugins_field"] != baseline["plugins_field"]
        ):
            raise ValueError("Changed fixed plugins.")
        if any(
            settings.get(key) != value
            for key, value in {
                "iterations": "300",
                "g_abstol": "1.0e-8",
                "f_calls_limit": "10000",
                "f_abstol": "0.0",
                "f_reltol": "0.0",
                "x_abstol": "0.0",
                "x_reltol": "0.0",
            }.items()
        ):
            raise ValueError("Changed recorded local optimizer settings.")
    prepared(directory)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--verify", action="store_true")
    arguments = parser.parse_args()
    if arguments.verify:
        verify_fixed(arguments.directory)
        print("Fixed white-scaling read-only verification passed.")
    else:
        run(arguments.directory)


if __name__ == "__main__":
    main()
