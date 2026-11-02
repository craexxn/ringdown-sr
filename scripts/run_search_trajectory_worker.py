"""Run one restricted trajectory cell with a passive native observation plugin."""

import argparse
import hashlib
import importlib.util
import json
import math
import struct
import time
from pathlib import Path

from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import backend_seed
from ringdown_sr.parameter_export import _read_json
from ringdown_sr.pilot import _json_bytes, _sha256, _write_json
from ringdown_sr.representation_profiles import plugin_field_record, plugin_records
from ringdown_sr.search_trajectory import (
    FORMAT,
    OBSERVED_PLUGINS,
    TrajectoryPluginDescriptor,
    checked_profile,
    decode_raw_tree,
    float_from_bits,
    profile_parameters,
    raw_tree_id,
    verify_manifest,
)

UNITS_FORMAT = "ringdown-sr-search-trajectory-units-1"
REPLAYS_FORMAT = "ringdown-sr-search-trajectory-replays-1"
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


def native_tree_record(record):
    kind = str(record.kind)
    if kind == "constant":
        return {"kind": kind, "value_bits": str(record.value_bits)}
    if kind == "variable":
        return {"kind": kind, "index": int(record.index)}
    return {
        "kind": kind,
        "arity": int(record.arity),
        "operator_index": int(record.operator_index),
        "operator": str(record.operator),
        "children": [native_tree_record(child) for child in record.children],
    }


def native_replay_record(record):
    status = str(record.status)
    reason = None if record.reason is None else str(record.reason)
    if status == "not_assessed":
        if (
            reason
            not in {
                "dimensional_violation",
                "nonfinite_constant",
                "numerical_unresolved",
            }
            or record.loss_bits is not None
            or record.prediction_bits is not None
        ):
            raise ValueError("Invalid unavailable native replay record.")
        return {
            "status": status,
            "reason": reason,
            "loss_bits": None,
            "prediction_bits": None,
        }
    if status != "available" or reason is not None:
        raise ValueError("Invalid native replay status.")
    loss_bits = str(record.loss_bits)
    prediction_bits = [str(value) for value in record.prediction_bits]
    loss = float_from_bits(loss_bits)
    if (
        not math.isfinite(loss)
        or loss < 0
        or not prediction_bits
        or not all(math.isfinite(float_from_bits(value)) for value in prediction_bits)
    ):
        raise ValueError("An available native replay must be finite.")
    return {
        "status": status,
        "reason": None,
        "loss_bits": loss_bits,
        "prediction_bits": prediction_bits,
    }


def export_units(directory, jl, options, observation):
    """Classify unique captured trees only after search, without numeric callbacks."""
    if observation["status"] == "disabled":
        if any(
            (directory / name).exists() or (directory / name).is_symlink()
            for name in (
                "observations.jsonl",
                "observation_units.json",
                "observation_replays.json",
            )
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


def export_replays(directory, jl, options, observation, *, expected_inputs_sha256):
    """Replay each captured tree after fit; never replace its saved backend loss."""
    replay_path = directory / "observation_replays.json"
    if observation["status"] == "disabled":
        if replay_path.exists() or replay_path.is_symlink():
            raise ValueError("Disabled observer produced native replay artifacts.")
        return {**observation, "replay_bytes": 0}

    def consumed(path, expected):
        if path.is_symlink() or not path.is_file():
            raise ValueError("Native replay inputs must be regular files.")
        contents = path.read_bytes()
        if _sha256(contents) != expected:
            raise ValueError("A native replay input changed: " + path.name)
        return contents

    inputs_path, units_path = (
        directory / "inputs.npz",
        directory / "observation_units.json",
    )
    raw_path = directory / "observations.jsonl"
    consumed(inputs_path, expected_inputs_sha256)
    units_bytes = consumed(units_path, observation["units_sha256"])
    units = _read_json(units_bytes)["trees"]
    if (
        raw_path.is_symlink()
        or not raw_path.is_file()
        or raw_path.stat().st_size != observation["bytes_written"]
        or len(units_bytes) != observation["units_bytes"]
        or observation["total_bytes"] != observation["bytes_written"] + len(units_bytes)
    ):
        raise ValueError("Changed observation sizes before native replay.")
    guard = jl.SearchTrajectory.begin_replay_guard(options)
    calls = int(jl.RingdownSRSearch.CALLS[()])
    original_hash = hashlib.sha256()
    trees = {}
    with raw_path.open("rb") as stream:
        for line in stream:
            original_hash.update(line)
            event = _read_json(line)
            members = [
                *event["returned_population"],
                *(row["member"] for row in event["hall_of_fame"]),
            ]
            for member in members:
                tree = member["tree"]
                key = raw_tree_id(tree)
                if key in trees:
                    continue
                decode_raw_tree(tree)
                if key not in units:
                    raise ValueError("Native replay tree is missing from units export.")
                root = restore_raw_tree(tree, jl.RingdownSRSearch)
                restored = native_tree_record(
                    jl.SearchTrajectory.raw_tree(root, options)
                )
                if restored != tree:
                    raise ValueError(
                        "Native replay tree roundtrip changed exact bits or order."
                    )
                record = native_replay_record(
                    jl.SearchTrajectory.training_replay(root, options)
                )
                if units[key]["status"] != "valid" and (
                    record["status"] != "not_assessed"
                    or record["reason"] != units[key]["reason"]
                ):
                    raise ValueError(
                        "Native replay contradicts the original units classification."
                    )
                trees[key] = record
    if original_hash.hexdigest() != observation["raw_sha256"] or set(trees) != set(
        units
    ):
        raise ValueError(
            "Changed raw observation or incomplete native replay coverage."
        )
    jl.SearchTrajectory.verify_replay_guard(guard, options)
    if int(jl.RingdownSRSearch.CALLS[()]) != calls:
        raise ValueError("Native replay evaluated the numeric callback.")
    consumed(raw_path, observation["raw_sha256"])
    consumed(units_path, observation["units_sha256"])
    consumed(inputs_path, expected_inputs_sha256)
    payload = _json_bytes(
        {
            "format": REPLAYS_FORMAT,
            "inputs_sha256": expected_inputs_sha256,
            "raw_sha256": original_hash.hexdigest(),
            "units_sha256": observation["units_sha256"],
            "trees": trees,
        }
    )
    total = observation["total_bytes"] + len(payload)
    if total > observation["max_bytes"]:
        raise ValueError("Combined observation files exceed the byte limit.")
    with replay_path.open("xb") as stream:
        if stream.write(payload) != len(payload):
            raise OSError("Incomplete native replay write.")
    return {
        **observation,
        "replay_bytes": len(payload),
        "replay_sha256": _sha256(payload),
        "total_bytes": total,
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
            replay_started = time.perf_counter()
            observation = export_replays(
                directory,
                jl,
                options,
                observation,
                expected_inputs_sha256=manifest["inputs"]["inputs.npz"],
            )
            observation_timing["replay_after_fit"] = (
                time.perf_counter() - replay_started if observed else 0.0
            )
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
