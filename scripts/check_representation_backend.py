"""Inspect genuine pinned options/plugins for every profile and seed, without fit."""

import argparse
import importlib.util
import os
from pathlib import Path

import numpy as np

from ringdown_sr import symbolic
from ringdown_sr.pilot import _sha256, _utc_now, _write_json
from ringdown_sr.representation_profiles import (
    CONDITIONS,
    normalized_backend_fields,
    plugin_field_record,
    plugin_records,
    validate_plugin_records,
)

ROOT = symbolic.ROOT


def load_base():
    spec = importlib.util.spec_from_file_location(
        "representation_base", ROOT / "scripts/run_noiseless_control.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inspect_profiles():
    if os.environ.get("PYTHON_JULIACALL_PROJECT") != str(ROOT / "julia"):
        raise RuntimeError("Use the pinned scripts/run_python.py launcher.")
    import pysr
    from juliacall import Main as jl

    if (
        pysr.__version__ != "2.6.0"
        or str(jl.seval("string(Base.pkgversion(SymbolicRegression))")) != "2.5.1"
    ):
        raise RuntimeError("Unexpected pinned backend versions.")
    if (
        Path(str(jl.seval("Base.active_project()"))).resolve()
        != ROOT / "julia/Project.toml"
    ):
        raise RuntimeError("Unexpected active Julia project.")
    base = load_base()
    support = base.load_support()
    probe = support.load_core_probe()
    probe.validate_core_request("Haswell")
    initial = probe.metadata(julia_used=True)
    initial["blas_control"] = probe.verify_blas_control(
        initial["environment"], "Haswell", require_julia=True
    )
    for name in (
        "RingdownSRLoss.jl",
        "RingdownSRSearch.jl",
        "RepresentationProfiles.jl",
    ):
        jl.include(str(ROOT / "julia/src" / name))
    profiles = []
    for condition in CONDITIONS:
        for seed in (20261020, 20261021, 20261022):
            backend_seed = int(np.random.RandomState(seed).randint(0, 2**31 - 1))
            options = jl.RepresentationProfiles.reference_options(
                condition, backend_seed
            )
            expected = jl.RepresentationProfiles.expected_plugins(
                condition, backend_seed
            )
            jl.RepresentationProfiles.verify_options(
                options, condition, backend_seed, expected
            )
            fields = [
                {
                    "name": str(field.name),
                    "type": str(field.type),
                    "value": str(field.value),
                }
                for field in jl.RingdownSRSearch.option_fields(options)
            ]
            plugins_field = plugin_field_record(
                jl.RepresentationProfiles.plugin_field(options)
            )
            plugins = plugin_records(jl.RepresentationProfiles.plugin_records(options))
            validate_plugin_records(plugins, condition)
            normalized = normalized_backend_fields(fields, condition, plugins_field)
            checked = base.verify_backend_policy(
                normalized,
                {
                    "seed": seed,
                    "niterations": 200,
                    "populations": 2,
                    "population_size": 32,
                    "ncycles_per_iteration": 50,
                },
                {"python_seed": seed, "backend_seed": backend_seed},
                support,
            )
            profiles.append(
                {
                    "condition": condition,
                    "python_seed": seed,
                    "backend_seed": backend_seed,
                    "backend_options": fields,
                    "plugins_field": plugins_field,
                    "plugins": plugins,
                    "common_policy_verification": checked,
                }
            )
    if int(jl.RingdownSRSearch.CALLS[()]) != 0:
        raise ValueError("The options-only preflight evaluated the search callback.")
    probe.validate_core_request("Haswell")
    final = probe.metadata(julia_used=True)
    final["blas_control"] = probe.verify_blas_control(
        final["environment"], "Haswell", require_julia=True
    )
    if initial["provenance"] != final["provenance"]:
        raise ValueError("Sources changed during the options preflight.")
    return {
        "format": "ringdown-sr-representation-preflight-1",
        "status": "verified",
        "created_at_utc": _utc_now(),
        "scope": "genuine options only; no fit, search or optimization",
        "profiles": profiles,
        "callback_calls": 0,
        "initial": initial,
        "final": final,
        "source_sha256": {
            name: _sha256((ROOT / name).read_bytes())
            for name in (
                "scripts/check_representation_backend.py",
                "src/ringdown_sr/representation_profiles.py",
                "julia/src/RepresentationProfiles.jl",
                "julia/src/RingdownSRSearch.jl",
                "julia/src/RingdownSRLoss.jl",
            )
        },
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
        raise ValueError("Preflight output must not overlap sources.")
    result = inspect_profiles()
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, result)
    print(
        "Representation backend preflight passed: nine genuine options objects; no fit/search."
    )


if __name__ == "__main__":
    main()
