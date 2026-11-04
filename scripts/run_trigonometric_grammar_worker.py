"""Internal free worker with one restricted grammar and a common native guard."""

import argparse
import importlib.util
import json
from pathlib import Path

from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import backend_seed
from ringdown_sr.pilot import _sha256, _write_json
from ringdown_sr.representation_profiles import plugin_field_record, plugin_records
from ringdown_sr.trigonometric_grammar import (
    FORMAT,
    checked_profile,
    profile_parameters,
    verify_manifest,
)

SHOULD_SIMPLIFY = True
NATIVE_MODULE = "TrigonometricGrammar"
NATIVE_FILES = (
    "RepresentationProfiles.jl",
    "FreeOptimizerBudget.jl",
    "TrigonometricGrammar.jl",
)


def run(directory):
    directory = Path(directory).resolve()
    runtime = Path(__file__).resolve().parent
    manifest_bytes = (directory / "manifest.json").read_bytes()
    manifest = verify_manifest(directory, runtime)
    profile_bytes = (directory / "profile.json").read_bytes()
    condition = checked_profile(json.loads(profile_bytes))
    request = json.loads((directory / "request.json").read_bytes())
    budget = symbolic.SearchBudget(**request["budget"])
    seed = backend_seed(budget.seed)
    spec = importlib.util.spec_from_file_location(
        "grammar_repeat", runtime / "driver.py"
    )
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    original_parameters, original_snapshot = (
        symbolic.search_parameters,
        symbolic._environment_snapshot,
    )

    def snapshot(phase, *, julia_used):
        if phase == "before_fit":
            from juliacall import Main as jl

            for name in NATIVE_FILES:
                contents = (runtime / name).read_bytes()
                if _sha256(contents) != manifest["sources"]["julia/src/" + name]:
                    raise ValueError(
                        "Native grammar source changed before consumption."
                    )
                (directory / name).write_bytes(contents)
                jl.include(str(directory / name))
            getattr(jl, NATIVE_MODULE).configure(
                condition, seed, should_simplify=SHOULD_SIMPLIFY
            )
        elif phase == "after_search":
            from juliacall import Main as jl

            options = jl.RingdownSRSearch.LAST_OPTIONS[()]
            record = getattr(jl, NATIVE_MODULE).verification_record(options)
            verify_manifest(directory, runtime)
            if (directory / "manifest.json").read_bytes() != manifest_bytes or (
                directory / "profile.json"
            ).read_bytes() != profile_bytes:
                raise ValueError(
                    "Worker manifest or profile changed during consumption."
                )
            front = json.loads((directory / "result.json").read_bytes())
            _write_json(
                directory / "verification.json",
                {
                    "format": FORMAT,
                    "status": str(record.status),
                    "condition": str(record.condition),
                    "backend_seed": int(record.backend_seed),
                    "plugins_field": plugin_field_record(record.plugins_field),
                    "plugins": plugin_records(record.plugins),
                    "optimizer_settings": {
                        str(x.name): str(x.value) for x in record.optimizer_settings
                    },
                    "callback_calls_total": int(record.callback_calls),
                    "callback_calls_during_fit": front["callback_calls_during_fit"],
                    "profile_sha256": _sha256(profile_bytes),
                    "manifest_sha256": _sha256(manifest_bytes),
                    "backend_options": json.loads(
                        (directory / "backend_options.json").read_bytes()
                    ),
                },
            )
        return original_snapshot(phase, julia_used=julia_used)

    symbolic.search_parameters = lambda requested: profile_parameters(
        requested, condition
    )
    symbolic._environment_snapshot = snapshot
    try:
        support.controlled_worker(directory, "Haswell")
    finally:
        symbolic.search_parameters, symbolic._environment_snapshot = (
            original_parameters,
            original_snapshot,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    run(parser.parse_args().directory)
