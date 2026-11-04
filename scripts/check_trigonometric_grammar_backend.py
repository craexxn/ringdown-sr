"""Inspect six native option objects or fixed references, without fit or search."""

import argparse
import importlib.util
import math
import os
from pathlib import Path

import numpy as np

from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import backend_seed
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _utc_now, _write_json
from ringdown_sr.representation_control import diagnose_candidate
from ringdown_sr.representation_profiles import plugin_field_record, plugin_records
from ringdown_sr.trigonometric_grammar import (
    CONDITIONS,
    FORMAT,
    SEEDS,
    common_options,
    expected_grammar_cases,
    source_hashes,
    verify_options,
)

SHOULD_SIMPLIFY = True


def load_base():
    spec = importlib.util.spec_from_file_location(
        "grammar_base", symbolic.ROOT / "scripts/run_noiseless_control.py"
    )
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    return base


def native_runtime():
    if os.environ.get("PYTHON_JULIACALL_PROJECT") != str(symbolic.ROOT / "julia"):
        raise RuntimeError("Use the pinned scripts/run_python.py launcher.")
    import pysr
    from juliacall import Main as jl

    if (
        pysr.__version__,
        str(jl.VERSION),
        str(jl.seval("Base.pkgversion(SymbolicRegression)")),
    ) != ("2.6.0", "1.13.1", "2.5.1"):
        raise ValueError("Unexpected pinned grammar backend versions.")
    if (
        Path(str(jl.seval("Base.active_project()"))).resolve()
        != symbolic.ROOT / "julia/Project.toml"
    ):
        raise ValueError("Unexpected Julia project.")
    return jl


def option_record(jl, module, options, seed, condition):
    module.verify_options(
        options, condition, backend_seed(seed), should_simplify=SHOULD_SIMPLIFY
    )
    return {
        "python_seed": seed,
        "backend_seed": backend_seed(seed),
        "condition": condition,
        "backend_options": [
            {"name": str(x.name), "type": str(x.type), "value": str(x.value)}
            for x in jl.RingdownSRSearch.option_fields(options)
        ],
        "optimizer_settings": {
            str(x.name): str(x.value) for x in module.optimizer_settings(options)
        },
        "plugins_field": plugin_field_record(
            jl.RepresentationProfiles.plugin_field(options)
        ),
        "plugins": plugin_records(jl.RepresentationProfiles.plugin_records(options)),
    }


def grammar_cases(jl, backend, options, condition):
    c, t, u, b = backend.constant, backend.variable(1), backend.unary, backend.binary
    nodes = {
        "linear": b(1, c(1.0), t),
        "cosine": u(3, b(1, b(3, c(2.0), t), c(0.3))),
        "exponential": u(1, b(3, c(-2.0), t)),
        "exp_of_cos": u(1, u(3, t)),
        "cos_of_exp": u(3, u(1, t)),
        "trig_siblings": b(3, u(2, t), u(3, t)),
    }
    for outer_name, outer in (("sin", 2), ("cos", 3)):
        for inner_name, inner in (("sin", 2), ("cos", 3)):
            nodes[f"{outer_name}_{inner_name}_direct"] = u(outer, u(inner, t))
            nodes[f"{outer_name}_{inner_name}_arithmetic"] = u(
                outer, b(1, c(0.1), b(3, c(2.0), u(inner, t)))
            )
    records = [
        {
            "condition": condition,
            "case": name,
            "accepted": bool(jl.SymbolicRegression.check_constraints(tree, options)),
        }
        for name, tree in nodes.items()
    ]
    expected = [r for r in expected_grammar_cases() if r["condition"] == condition]
    if records != expected:
        raise ValueError("The native checker disagrees with the declared syntax rule.")
    return records


def inspect(mode):
    sources = source_hashes()
    jl = native_runtime()
    base = load_base()
    support = base.load_support()
    probe = support.load_core_probe()
    probe.validate_core_request("Haswell")

    def snapshot():
        record = probe.metadata(julia_used=True)
        record["blas_control"] = probe.verify_blas_control(
            record["environment"], "Haswell", require_julia=True
        )
        return record

    initial = snapshot()
    runtime = Path(__file__).resolve().parent
    native_files = (
        "RingdownSRLoss.jl",
        "RingdownSRSearch.jl",
        "RepresentationProfiles.jl",
        "FreeOptimizerBudget.jl",
        "TrigonometricGrammar.jl",
    )
    paths = [runtime / name for name in native_files]
    if not all(path.is_file() for path in paths):
        paths = [symbolic.ROOT / "julia/src" / name for name in native_files]
    for path in paths:
        from ringdown_sr.pilot import _sha256

        if (
            path.is_symlink()
            or _sha256(path.read_bytes()) != sources["julia/src/" + path.name]
        ):
            raise ValueError("Preflight Julia source changed.")
    cases, profiles, grammar = [], [], []
    if mode == "options":
        for path in paths:
            jl.include(str(path))
        module = jl.TrigonometricGrammar
        first = None
        for condition in CONDITIONS:
            for seed in SEEDS:
                options = module.reference_options(
                    condition, backend_seed(seed), should_simplify=SHOULD_SIMPLIFY
                )
                record = option_record(jl, module, options, seed, condition)
                record["policy_verification"] = verify_options(
                    record, seed, condition, base, support
                )
                common = common_options(record, support)
                if first is not None and common != first:
                    raise ValueError("Unexpected cross-grammar backend difference.")
                first = common
                profiles.append(record)
        if int(jl.RingdownSRSearch.CALLS[()]) != 0:
            raise ValueError("Options-only preflight used the numeric callback.")
    else:
        from juliacall import JuliaError, convert

        arrays = frozen_data()
        array = lambda value: convert(
            jl.Array[jl.Float64], np.asarray(value, dtype=np.float64)
        )
        for condition in CONDITIONS:
            name = f"GrammarReference{condition}"
            jl.seval(f"module {name} end")
            namespace = getattr(jl, name)
            for path in paths:
                jl.Base.include(namespace, str(path))
            backend, module = namespace.RingdownSRSearch, namespace.TrigonometricGrammar
            backend.bind_context(
                array(arrays["time_s"]), array(arrays["observed"]), None
            )
            module.configure(
                condition, backend_seed(SEEDS[0]), should_simplify=SHOULD_SIMPLIFY
            )
            options = module.reference_options(
                condition, backend_seed(SEEDS[0]), should_simplify=SHOULD_SIMPLIFY
            )
            grammar.extend(grammar_cases(jl, backend, options, condition))
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
                        u(1, b(3, c(-125.0), t)),
                        u(3, b(3, c(2 * math.pi * frequency), t)),
                    ),
                )
                if not jl.SymbolicRegression.check_constraints(root, options):
                    raise ValueError(
                        "The fixed ringdown reference violates the grammar."
                    )
                loss = float(jl.SymbolicRegression.eval_loss(root, dataset, options))
                prediction, replay = backend.replay(root, options)
                independent = np.exp(-125 * arrays["time_s"]) * np.cos(
                    2 * np.pi * frequency * arrays["time_s"]
                )
                symbolic._check_prediction_replay(independent, np.asarray(prediction))
                residual_mse = (
                    math.fsum(
                        float(x) ** 2
                        for x in arrays["observed"] - np.asarray(prediction)
                    )
                    / 128
                )
                if (
                    not math.isfinite(loss)
                    or loss >= 1e-24
                    or not math.isclose(loss, residual_mse, rel_tol=1e-12, abs_tol=0)
                    or float(replay) != loss
                ):
                    raise ValueError(
                        "Fixed reference loss disagrees with the original tree."
                    )
                tree = symbolic._export_tree(root, options)
                diagnosis = diagnose_candidate(
                    {
                        "tree": tree,
                        "complexity": 11,
                        "loss": loss,
                        "display_equation": "fixed reference",
                    },
                    0,
                    0,
                    arrays,
                    "complexity_frequency",
                )
                if (
                    diagnosis["curve_marker"]
                    != (
                        "outside_tolerance" if frequency == 4346 else "within_tolerance"
                    )
                    or diagnosis["parameter_match"]["status"] != "matched"
                ):
                    raise ValueError("Fixed alias-reference diagnostic mismatch.")
                inner, complete = jl.SymbolicRegression.eval_tree_array(
                    root, array(arrays["diagnostic_time_s"].reshape(1, -1)), options
                )
                if not complete:
                    raise ValueError("Incomplete inner-grid native evaluation.")
                symbolic._check_prediction_replay(
                    symbolic.evaluate_tree(tree, arrays["diagnostic_time_s"]),
                    np.asarray(inner),
                )
                if frequency == 33018:
                    point = np.array([1 / (16 * 4096)])
                    np.testing.assert_allclose(
                        symbolic.evaluate_tree(tree, point),
                        -np.exp(-125 * point) * np.cos(2 * np.pi * 250 * point),
                        rtol=1e-12,
                        atol=1e-14,
                    )
                cases.append(
                    {
                        "condition": condition,
                        "frequency_hz": frequency,
                        "native_mse": loss,
                        "independent_residual_mse": residual_mse,
                        "diagnosis": diagnosis,
                    }
                )
            if not math.isinf(
                float(jl.SymbolicRegression.eval_loss(u(2, t), dataset, options))
            ):
                raise ValueError("Wrong-unit reference was accepted.")
            before = int(backend.CALLS[()])
            for bad in (
                module.reference_options(condition, backend_seed(SEEDS[0]) + 1),
                module.reference_options(
                    CONDITIONS[1 - CONDITIONS.index(condition)], backend_seed(SEEDS[0])
                ),
            ):
                try:
                    jl.SymbolicRegression.eval_loss(c(0.0), dataset, bad)
                except JuliaError:
                    pass
                else:
                    raise ValueError("Native guard accepted a wrong seed or grammar.")
                if int(backend.CALLS[()]) != before:
                    raise ValueError(
                        "Native guard failed after numeric callback entry."
                    )
            module.verification_record(options)
    final = snapshot()
    if source_hashes() != sources or initial["provenance"] != final["provenance"]:
        raise ValueError("Preflight sources changed.")
    return {
        "format": FORMAT,
        "mode": mode,
        "status": "verified",
        "created_at_utc": _utc_now(),
        "scope": "no fit, search or optimization",
        "callback_calls": 0 if mode == "options" else None,
        "profiles": profiles,
        "cases": cases,
        "grammar_cases": grammar,
        "source_sha256": sources,
        "initial": initial,
        "final": final,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("options", "references"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    path = args.output.resolve()
    if path.exists() or any(
        path.is_relative_to(symbolic.ROOT / name)
        for name in ("src", "scripts", "docs", "julia", ".git")
    ):
        raise ValueError("Use a new preflight output outside sources.")
    result = inspect(args.mode)
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, result)
    print(f"Trigonometric grammar {args.mode} passed; no fit/search/optimization.")
