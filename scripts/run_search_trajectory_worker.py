"""Run one restricted trajectory cell with a passive native observation plugin."""

import argparse
import hashlib
import importlib.util
import json
import struct
import time
from pathlib import Path

from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import backend_seed
from ringdown_sr.pilot import _json_bytes, _sha256, _write_json
from ringdown_sr.representation_profiles import plugin_field_record, plugin_records
from ringdown_sr.search_trajectory import (
    FORMAT,
    OBSERVED_PLUGINS,
    TrajectoryPluginDescriptor,
    checked_profile,
    decode_raw_tree,
    profile_parameters,
    verify_manifest,
)

UNITS_FORMAT = "ringdown-sr-search-trajectory-units-1"
NATIVE_FILES = (
    "RepresentationProfiles.jl",
    "FreeOptimizerBudget.jl",
    "SearchTrajectory.jl",
)


def live_parameters(budget, observed):
    parameters = profile_parameters(budget, observed)
    expected = list(OBSERVED_PLUGINS) if observed else None
    if parameters.get("plugins") != expected:
        raise ValueError("Unexpected trajectory plugin request.")
    if observed:
        parameters["plugins"] = [
            TrajectoryPluginDescriptor(value) for value in expected
        ]
    return parameters


def option_record(jl, options, seed, observed):
    module = jl.SearchTrajectory
    module.verify_options(options, observed, backend_seed(seed))
    baseline = jl.FreeOptimizerBudget.reference_options(100, backend_seed(seed))
    expected = module.expected_options(observed, backend_seed(seed))
    return {
        "python_seed": seed,
        "backend_seed": backend_seed(seed),
        "observed": observed,
        "iterations": 100,
        "backend_options": [
            {"name": str(x.name), "type": str(x.type), "value": str(x.value)}
            for x in jl.RingdownSRSearch.option_fields(options)
        ],
        "optimizer_settings": {
            str(x.name): str(x.value)
            for x in jl.FreeOptimizerBudget.optimizer_settings(options)
        },
        "plugins_field": plugin_field_record(
            jl.RepresentationProfiles.plugin_field(options)
        ),
        "plugins": plugin_records(jl.RepresentationProfiles.plugin_records(options)),
        "baseline_plugins_field": plugin_field_record(
            jl.RepresentationProfiles.plugin_field(baseline)
        ),
        "baseline_plugins": plugin_records(
            jl.RepresentationProfiles.plugin_records(baseline)
        ),
        "expected_plugins_field": plugin_field_record(
            jl.RepresentationProfiles.plugin_field(expected)
        ),
    }


def restore_raw_tree(node, backend):
    if node["kind"] == "constant":
        value = struct.unpack(">d", bytes.fromhex(node["value_bits"]))[0]
        return backend.constant(value)
    if node["kind"] == "variable":
        return backend.variable(node["index"])
    children = [restore_raw_tree(child, backend) for child in node["children"]]
    factory = backend.unary if node["arity"] == 1 else backend.binary
    return factory(node["operator_index"], *children)


def export_units(directory, jl, options, observation):
    """Classify unique captured trees only after search, without numeric callbacks."""
    if observation["status"] == "disabled":
        if any(
            (directory / name).exists()
            for name in ("observations.jsonl", "observation_units.json")
        ):
            raise ValueError("Disabled observer produced observation files.")
        return {**observation, "units_bytes": 0, "total_bytes": 0}
    path = directory / "observations.jsonl"
    if path.is_symlink() or path.stat().st_size != observation["bytes_written"]:
        raise ValueError("Raw observation byte count changed.")
    # Bind the bytes consumed by the diagnostic, not a later regenerated hash.
    original_hash = hashlib.sha256()
    trees = {}
    calls = int(jl.RingdownSRSearch.CALLS[()])
    with path.open("rb") as stream:
        for line in stream:
            original_hash.update(line)
            event = json.loads(line)
            members = [
                *event["returned_population"],
                *(row["member"] for row in event["hall_of_fame"]),
            ]
            for member in members:
                tree = member["tree"]
                canonical = json.dumps(
                    tree, sort_keys=True, separators=(",", ":"), ensure_ascii=True
                ).encode()
                key = _sha256(canonical)
                if key in trees:
                    continue
                decode_raw_tree(tree)
                root = restore_raw_tree(tree, jl.RingdownSRSearch)
                record = jl.SearchTrajectory.units_status(root, options)
                trees[key] = {
                    "status": str(record.status),
                    "reason": None if record.reason is None else str(record.reason),
                }
    if _sha256(path.read_bytes()) != original_hash.hexdigest():
        raise ValueError("Raw observation changed during unit classification.")
    if int(jl.RingdownSRSearch.CALLS[()]) != calls:
        raise ValueError("Unit classification evaluated the numeric callback.")
    payload = _json_bytes({"format": UNITS_FORMAT, "trees": trees})
    total = observation["bytes_written"] + len(payload)
    if total > observation["max_bytes"]:
        raise ValueError("Combined observation files exceed the byte limit.")
    units_path = directory / "observation_units.json"
    with units_path.open("xb") as stream:
        written = stream.write(payload)
        if written != len(payload):
            raise OSError("Incomplete observation unit-status write.")
    return {
        **observation,
        "units_bytes": len(payload),
        "total_bytes": total,
        "raw_sha256": original_hash.hexdigest(),
        "units_sha256": _sha256(payload),
    }


def run(directory):
    directory = Path(directory).resolve()
    runtime = Path(__file__).resolve().parent
    manifest_bytes = (directory / "manifest.json").read_bytes()
    manifest = verify_manifest(directory, runtime)
    profile_bytes = (directory / "profile.json").read_bytes()
    observed = checked_profile(json.loads(profile_bytes))
    request = json.loads((directory / "request.json").read_bytes())
    budget = symbolic.SearchBudget(**request["budget"])
    seed = backend_seed(budget.seed)
    spec = importlib.util.spec_from_file_location(
        "trajectory_repeat", runtime / "driver.py"
    )
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    original_parameters, original_snapshot = (
        symbolic.search_parameters,
        symbolic._environment_snapshot,
    )
    native = None

    def snapshot(phase, *, julia_used):
        nonlocal native
        if phase == "before_fit":
            from juliacall import Main as jl

            for name in NATIVE_FILES:
                contents = (runtime / name).read_bytes()
                if _sha256(contents) != manifest["sources"]["julia/src/" + name]:
                    raise ValueError("Native trajectory source changed before use.")
                (directory / name).write_bytes(contents)
                jl.include(str(directory / name))
            native = jl.SearchTrajectory
            native.configure(
                observed,
                seed,
                str(directory / "observations.jsonl"),
                budget.niterations * budget.populations,
            )
        elif phase == "after_search":
            from juliacall import Main as jl

            options = jl.RingdownSRSearch.LAST_OPTIONS[()]
            raw = native.finish_observation()
            observation = {
                "status": str(raw.status),
                **{
                    name: int(getattr(raw, name))
                    for name in (
                        "event_count",
                        "member_count",
                        "bytes_written",
                        "max_bytes",
                        "expected_events",
                    )
                },
            }
            units_started = time.perf_counter()
            observation = export_units(directory, jl, options, observation)
            observation_timing = {
                "hook": float(raw.hook_seconds),
                "units_after_fit": time.perf_counter() - units_started
                if observed
                else 0.0,
            }
            record = native.verification_record(options)
            details = option_record(jl, options, budget.seed, observed)
            verify_manifest(directory, runtime)
            if (directory / "manifest.json").read_bytes() != manifest_bytes or (
                directory / "profile.json"
            ).read_bytes() != profile_bytes:
                raise ValueError("Worker manifest or profile changed during use.")
            front = json.loads((directory / "result.json").read_bytes())
            _write_json(
                directory / "verification.json",
                {
                    **details,
                    "format": FORMAT,
                    "status": str(record.status),
                    "callback_calls_total": int(record.callback_calls),
                    "callback_calls_during_fit": front["callback_calls_during_fit"],
                    "profile_sha256": _sha256(profile_bytes),
                    "manifest_sha256": _sha256(manifest_bytes),
                    "observation": observation,
                    "observation_timing_seconds": observation_timing,
                },
            )
        return original_snapshot(phase, julia_used=julia_used)

    symbolic.search_parameters = lambda requested: live_parameters(requested, observed)
    symbolic._environment_snapshot = snapshot
    try:
        support.controlled_worker(directory, "Haswell")
    finally:
        symbolic.search_parameters, symbolic._environment_snapshot = (
            original_parameters,
            original_snapshot,
        )
        if native is not None:
            native.abort_observation()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    run(parser.parse_args().directory)
