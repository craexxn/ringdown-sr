"""Check actual PySR option delivery and native observer fixtures without search."""

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np

from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import backend_seed
from ringdown_sr.pilot import _sha256, _utc_now, _write_json
from ringdown_sr.search_trajectory import (
    FIXTURE_CHECKS,
    FORMAT,
    SEEDS,
    decode_raw_tree,
    source_hashes,
    verify_options,
)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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
        raise ValueError("Unexpected pinned trajectory backend versions.")
    if (
        Path(str(jl.seval("Base.active_project()"))).resolve()
        != symbolic.ROOT / "julia/Project.toml"
    ):
        raise ValueError("Unexpected Julia project.")
    return jl


def actual_pysr_options(worker, seed, observed):
    """Stop the installed PySR path after real Options construction, before search."""
    import pysr
    from pysr import sr

    captured = []
    original = sr.SymbolicRegression

    class OptionsCaptured(Exception):
        pass

    class OptionsBoundary:
        def __getattr__(self, name):
            if name == "Options":
                return self.capture
            if name == "equation_search":
                raise AssertionError("The options preflight must never start search.")
            return getattr(original, name)

        def capture(self, *args, **kwargs):
            captured.append(original.Options(*args, **kwargs))
            raise OptionsCaptured

    budget = symbolic.SearchBudget(seed=seed, niterations=200)
    model = pysr.PySRRegressor(**worker.live_parameters(budget, observed))
    # These fit attributes are required only to build Options. No fit is called.
    model.complexity_of_variables_ = model.complexity_of_variables
    model.output_directory_ = "trajectory-options-preflight"
    runtime_params = model._validate_and_modify_params()
    sr.SymbolicRegression = OptionsBoundary()
    try:
        model._run(
            np.arange(8, dtype=np.float64).reshape(-1, 1) / 8,
            1 + np.arange(8, dtype=np.float64) / 8,
            runtime_params,
            None,
            backend_seed(seed),
            None,
            "serial",
            None,
        )
    except OptionsCaptured:
        pass
    else:
        raise AssertionError("PySR did not stop at the native Options boundary.")
    finally:
        sr.SymbolicRegression = original
    if len(captured) != 1:
        raise AssertionError("Expected exactly one actual PySR native Options object.")
    return captured[0]


def verify_fixture_wire(event_json):
    """Parse the real native JSON serializer output independently of Julia records."""
    event = json.loads(event_json)
    if (
        set(event) != {"format", "event_index", "returned_population", "hall_of_fame"}
        or event["format"] != "ringdown-sr-search-trajectory-event-1"
        or event["event_index"] != 1
        or len(event["returned_population"]) != 32
        or [row["slot"] for row in event["hall_of_fame"]] != [3, 6]
    ):
        raise ValueError("Native fixture JSON event shape changed.")
    members = event["returned_population"]
    for member in [*members, *(row["member"] for row in event["hall_of_fame"])]:
        if set(member) != {
            "tree",
            "loss_bits",
            "cost_bits",
            "complexity_cache",
            "birth",
            "ref",
            "parent",
        }:
            raise ValueError("Native fixture JSON member fields changed.")
        decode_raw_tree(member["tree"])
    bits = [members[index]["tree"]["value_bits"] for index in (2, 3, 4, 5)]
    if bits != [
        "8000000000000000",
        "7ff0000000000000",
        "fff0000000000000",
        "7ff8000000000042",
    ]:
        raise ValueError("Native JSON serialization changed signed or nonfinite bits.")
    if (
        members[2]["cost_bits"] != "8000000000000000"
        or [member["complexity_cache"] for member in members] != [-1] * 32
        or [member["birth"] for member in members] != list(range(101, 133))
        or [member["ref"] for member in members] != list(range(1, 33))
        or [member["parent"] for member in members] != list(range(32))
    ):
        raise ValueError("Native JSON serialization changed stored member metadata.")


def inspect(mode):
    sources = source_hashes()
    jl = native_runtime()
    base = load_module(
        "trajectory_preflight_base",
        symbolic.ROOT / "scripts/run_noiseless_control.py",
    )
    support = base.load_support()
    probe = support.load_core_probe()
    probe.validate_core_request("Haswell")

    def snapshot():
        result = probe.metadata(julia_used=True)
        result["blas_control"] = probe.verify_blas_control(
            result["environment"], "Haswell", require_julia=True
        )
        return result

    initial = snapshot()
    runtime = Path(__file__).resolve().parent
    names = (
        "RingdownSRLoss.jl",
        "RingdownSRSearch.jl",
        "RepresentationProfiles.jl",
        "FreeOptimizerBudget.jl",
        "SearchTrajectory.jl",
    )
    native_paths = [runtime / name for name in names]
    if not all(path.is_file() for path in native_paths):
        native_paths = [symbolic.ROOT / "julia/src" / name for name in names]
    for path in native_paths:
        if (
            path.is_symlink()
            or _sha256(path.read_bytes()) != sources["julia/src/" + path.name]
        ):
            raise ValueError("Preflight native source changed.")
        jl.include(str(path))
    worker_path = runtime / "worker.py"
    if not worker_path.is_file():
        worker_path = symbolic.ROOT / "scripts/run_search_trajectory_worker.py"
    if (
        worker_path.is_symlink()
        or _sha256(worker_path.read_bytes())
        != sources["scripts/run_search_trajectory_worker.py"]
    ):
        raise ValueError("Preflight worker source changed.")
    worker = load_module("trajectory_preflight_worker", worker_path)
    profiles, checks = [], []
    if mode == "options":
        for seed in SEEDS:
            for observed in (False, True):
                options = actual_pysr_options(worker, seed, observed)
                record = worker.option_record(jl, options, seed, observed)
                record["policy_verification"] = verify_options(
                    record, seed, observed, base, support
                )
                profiles.append(record)
    elif mode == "fixtures":
        fixture = jl.SearchTrajectory.fixture_checks()
        verify_fixture_wire(str(fixture.event_json))
        names = [str(value) for value in fixture.checks]
        options = jl.SearchTrajectory.expected_options(True, 42)
        for bits in (
            "8000000000000000",
            "bff0000000000000",
            "0000000000000001",
            "8000000000000001",
            "7ff8000000000042",
        ):
            tree = {"kind": "constant", "value_bits": bits}
            root = worker.restore_raw_tree(tree, jl.RingdownSRSearch)
            if (
                worker.native_tree_record(jl.SearchTrajectory.raw_tree(root, options))
                != tree
            ):
                raise ValueError("Python/native constant boundary changed exact bits.")
        names.append("python_native_constant_roundtrip")
        if len(names) != len(set(names)) or set(names) != set(FIXTURE_CHECKS):
            raise ValueError("Missing or duplicate native observer fixture checks.")
        checks = [{"name": name, "status": "passed"} for name in names]
    else:
        raise ValueError("Unknown trajectory preflight mode.")
    calls = int(jl.RingdownSRSearch.CALLS[()])
    if calls != 0:
        raise ValueError("Options/fixture preflight evaluated the numeric callback.")
    final = snapshot()
    if source_hashes() != sources or initial["provenance"] != final["provenance"]:
        raise ValueError("Preflight sources changed.")
    return {
        "format": FORMAT,
        "status": "verified",
        "mode": mode,
        "created_at_utc": _utc_now(),
        "scope": "no fit, equation_search or optimization",
        "pysr_options_path": (
            "installed PySRRegressor._run interrupted immediately after native "
            "Options construction; no equation_search"
            if mode == "options"
            else "not_used"
        ),
        "callback_calls": calls,
        "profiles": profiles,
        "checks": checks,
        "source_sha256": sources,
        "initial": initial,
        "final": final,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("options", "fixtures"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or any(
        output.is_relative_to(symbolic.ROOT / name)
        for name in ("src", "scripts", "docs", "julia", ".git")
    ):
        raise ValueError("Use a new preflight output outside sources.")
    document = inspect(args.mode)
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output, document)
    print(f"Trajectory {args.mode} passed; no fit/search/optimization.")
