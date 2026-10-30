"""Wrap the unchanged search worker with a fixed profile and native pre-loss guard."""

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np

from ringdown_sr import symbolic
from ringdown_sr.pilot import _sha256, _write_json
from ringdown_sr.representation_profiles import (
    checked_profile,
    plugin_field_record,
    plugin_records,
    profile_parameters,
    verify_manifest,
)


def run(directory):
    directory = Path(directory).resolve()
    parent = Path(__file__).resolve().parent
    manifest_bytes = (directory / "representation_manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    verify_manifest(manifest, directory, parent)
    profile_bytes = (directory / "representation_profile.json").read_bytes()
    condition = checked_profile(json.loads(profile_bytes))
    request = json.loads((directory / "request.json").read_bytes())
    budget = symbolic.SearchBudget(**request["budget"])
    expected_seed = int(np.random.RandomState(budget.seed).randint(0, 2**31 - 1))
    spec = importlib.util.spec_from_file_location(
        "representation_repeat", parent / "driver.py"
    )
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    original_parameters = symbolic.search_parameters
    original_snapshot = symbolic._environment_snapshot

    def snapshot(phase, *, julia_used):
        if phase == "before_fit":
            from juliacall import Main as jl

            source = symbolic.ROOT / "julia/src/RepresentationProfiles.jl"
            copy = directory / "RepresentationProfiles.jl"
            copy.write_bytes(source.read_bytes())
            if (
                _sha256(copy.read_bytes())
                != manifest["sources"]["julia/src/RepresentationProfiles.jl"]
            ):
                raise ValueError("Native profile source changed before consumption.")
            jl.include(str(copy))
            jl.RepresentationProfiles.configure(condition, expected_seed)
        elif phase == "after_search":
            from juliacall import Main as jl

            record = jl.RepresentationProfiles.verification_record(
                jl.RingdownSRSearch.LAST_OPTIONS[()]
            )
            if (
                directory / "representation_profile.json"
            ).read_bytes() != profile_bytes:
                raise ValueError(
                    "The representation profile changed during the worker."
                )
            result = json.loads((directory / "result.json").read_bytes())
            verify_manifest(manifest, directory, parent)
            if (
                directory / "representation_manifest.json"
            ).read_bytes() != manifest_bytes:
                raise ValueError("Worker manifest changed during consumption.")
            _write_json(
                directory / "representation_verification.json",
                {
                    "format": "ringdown-sr-representation-verification-1",
                    "status": str(record.status),
                    "condition": str(record.condition),
                    "backend_seed": int(record.backend_seed),
                    "plugins_field": plugin_field_record(record.plugins_field),
                    "plugins": plugin_records(record.plugins),
                    "callback_calls_total": int(record.callback_calls),
                    "callback_calls_during_fit": result["callback_calls_during_fit"],
                    "profile_sha256": _sha256(profile_bytes),
                    "manifest_sha256": _sha256(manifest_bytes),
                    "julia_source_sha256": _sha256(
                        (directory / "RepresentationProfiles.jl").read_bytes()
                    ),
                },
            )
        return original_snapshot(phase, julia_used=julia_used)

    symbolic.search_parameters = lambda requested_budget: profile_parameters(
        requested_budget, condition
    )
    symbolic._environment_snapshot = snapshot
    try:
        support.controlled_worker(directory, "Haswell")
    finally:
        symbolic.search_parameters = original_parameters
        symbolic._environment_snapshot = original_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    run(parser.parse_args().directory)


if __name__ == "__main__":
    main()
