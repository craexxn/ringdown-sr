"""Strict passive-observation profiles and read-only, source-separated diagnostics."""

import copy
import hashlib
import json
import math
import re
import struct
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import numpy as np

from . import free_optimizer_budget as budget_control
from .config import SearchBudget
from .losses import mean_squared_error
from .parameter_export import _read_json
from .pilot import _sha256
from .representation_control import diagnose_candidate
from .representation_profiles import validate_plugin_records
from .symbolic import BINARY, ROOT, UNARY, _check_prediction_replay, evaluate_tree
from .symbolic import FORMAT as ARM_FORMAT

FORMAT = "ringdown-sr-search-trajectory-2"
PROFILE_FORMAT = "ringdown-sr-search-trajectory-profile-1"
EVENT_FORMAT = "ringdown-sr-search-trajectory-event-1"
UNITS_FORMAT = "ringdown-sr-search-trajectory-units-1"
REPLAY_FORMAT = "ringdown-sr-search-trajectory-replays-1"
REPLAY_POLICY = "docs/search_trajectory_replay_policy.md"
REPLAY_POLICY_SHA256 = (
    "e65a52ffd7292599e3d70957414977ede792bad6a64cebbe0e59c080ef241842"
)
PLAN = "docs/search_trajectory_plan.md"
PLAN_COMMIT = "fbfbc3781f80968f978b388e32bfc8375d6f8725"
PLAN_SHA256 = "fcc52e4099f197df676adc10c3163fc78e87d2a2d4661488b9ce929512da37f3"
SEEDS = budget_control.SEEDS
LIMIT_SECONDS = 3600
WORKER_LIMIT_SECONDS = 600
MAX_OBSERVATION_BYTES = 256 * 1024 * 1024
MAX_TOTAL_OBSERVATION_BYTES = 3 * MAX_OBSERVATION_BYTES
OBJECTIVE = "Main.SearchTrajectory.objective"
OBSERVER = "Main.SearchTrajectory.SearchTrajectoryObserver()"
BASELINE_PLUGINS = tuple(
    f"Main.SearchTrajectory.baseline_plugin({index})" for index in (1, 2, 3)
)
OBSERVED_PLUGINS = (*BASELINE_PLUGINS, OBSERVER)
FIXTURE_CHECKS = (
    "exact_tree_roundtrip",
    "nonfinite_bits_preserved",
    "rng_unchanged",
    "population_hof_and_plugin_states_unchanged",
    "complexity_cache_unchanged",
    "callback_count_unchanged",
    "byte_cap_rejected_without_truncation",
    "unexpected_event_rejected",
    "pareto_filter_does_not_remove_hof_member",
    "native_training_replay_bits_and_statuses",
    "native_training_replay_preserves_rng_context_options",
    "python_native_constant_roundtrip",
)
RUNTIME = {
    "driver.py": "scripts/repeat_symbolic_arm.py",
    "probe_symbolic_numerics.py": "scripts/probe_symbolic_numerics.py",
    "worker.py": "scripts/run_search_trajectory_worker.py",
    "backend.py": "scripts/check_search_trajectory_backend.py",
    **{
        name: "julia/src/" + name
        for name in (
            "RingdownSRLoss.jl",
            "RingdownSRSearch.jl",
            "RepresentationProfiles.jl",
            "FreeOptimizerBudget.jl",
            "SearchTrajectory.jl",
        )
    },
}
_BITS = re.compile(r"[0-9a-f]{16}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class TrajectoryPluginDescriptor(str):
    """Keep the four fixed PySR plugin descriptors literal and stably importable."""

    def __new__(cls, value):
        if type(value) is not str or value not in OBSERVED_PLUGINS:
            raise ValueError("Only fixed trajectory plugin descriptors are allowed.")
        return super().__new__(cls, value)

    def julia_plugin(self):
        from juliacall import Main as jl

        if self == OBSERVER:
            return jl.SearchTrajectory.SearchTrajectoryObserver()
        return jl.SearchTrajectory.baseline_plugin(
            BASELINE_PLUGINS.index(str(self)) + 1
        )


class ObserverDescriptor(TrajectoryPluginDescriptor):
    """Retain the observer-only constructor and its stable pickle import path."""

    def __new__(cls, value=OBSERVER):
        if type(value) is not str or value != OBSERVER:
            raise ValueError("Only the fixed passive observer descriptor is allowed.")
        return super().__new__(cls, value)


def source_hashes():
    """Include all consumed helpers and the independently frozen methods plan."""
    hashes = budget_control.source_hashes()
    names = {
        *hashes,
        *RUNTIME.values(),
        PLAN,
        REPLAY_POLICY,
        "scripts/run_search_trajectory.py",
        "scripts/check_search_trajectory_integration.py",
    }
    for name in names:
        path = ROOT / name
        if path.is_symlink():
            raise ValueError("Consumed trajectory sources must not be symbolic links.")
        hashes[name] = _sha256(path.read_bytes())
    if hashes[PLAN] != PLAN_SHA256:
        raise ValueError("The frozen search-trajectory plan changed.")
    if hashes[REPLAY_POLICY] != REPLAY_POLICY_SHA256:
        raise ValueError("The frozen native-replay policy changed.")
    return dict(sorted(hashes.items()))


def checked_profile(document):
    if (
        type(document) is not dict
        or set(document) != {"format", "observed"}
        or document["format"] != PROFILE_FORMAT
        or type(document["observed"]) is not bool
    ):
        raise ValueError("Invalid restricted search-trajectory profile.")
    return document["observed"]


def profile_parameters(budget, observed):
    checked_profile({"format": PROFILE_FORMAT, "observed": observed})
    result = budget_control.profile_parameters(budget, 100)
    result.update(
        loss_function=OBJECTIVE, plugins=list(OBSERVED_PLUGINS) if observed else None
    )
    return result


def planned_cells():
    return [
        {
            "number": 2 * block + offset + 1,
            "directory": f"cell-{2 * block + offset + 1:02d}",
            "iterations": 100,
            "observed": observed,
            "arm": "observer_on" if observed else "observer_off",
            "budget": asdict(SearchBudget(seed=seed, niterations=200)),
            "status": "planned",
        }
        for block, seed in enumerate(SEEDS)
        for offset, observed in enumerate(
            (False, True) if block % 2 == 0 else (True, False)
        )
    ]


def verify_manifest(directory, runtime):
    directory, runtime = Path(directory), Path(runtime)
    path = directory / "manifest.json"
    if directory.is_symlink() or runtime.is_symlink() or path.is_symlink():
        raise ValueError("Trajectory manifests must not use symbolic links.")
    manifest = _read_json(path.read_bytes())
    sources = source_hashes()
    if (
        type(manifest) is not dict
        or set(manifest) != {"format", "sources", "runtime", "inputs"}
        or manifest["format"] != FORMAT
        or manifest["sources"] != sources
        or manifest["runtime"] != {k: sources[v] for k, v in RUNTIME.items()}
        or type(manifest["inputs"]) is not dict
        or set(manifest["inputs"]) != {"request.json", "inputs.npz", "profile.json"}
    ):
        raise ValueError("Changed search-trajectory manifest.")
    for root, hashes in (
        (runtime, manifest["runtime"]),
        (directory, manifest["inputs"]),
    ):
        for name, digest in hashes.items():
            path = root / name
            if path.is_symlink() or _sha256(path.read_bytes()) != digest:
                raise ValueError("Changed consumed trajectory file: " + name)
    return manifest


def _field(value):
    if (
        type(value) is not dict
        or set(value) != {"type", "value"}
        or any(type(v) is not str or not v for v in value.values())
    ):
        raise ValueError("Invalid concrete plugin field.")
    return value


def _normalized_options(record, observed, support):
    """Normalize only the checked observer extension and shared objective wrapper."""
    checked_profile({"format": PROFILE_FORMAT, "observed": observed})
    if type(record.get("observed")) is not bool or record["observed"] != observed:
        raise ValueError("Wrong native observation profile.")
    baseline = record["baseline_plugins"]
    validate_plugin_records(baseline, "complexity_frequency")
    actual = record["plugins"]
    if type(actual) is not list or actual[:3] != baseline:
        raise ValueError("The original plugins changed or were reordered.")
    if not observed:
        if actual != baseline:
            raise ValueError("The control arm must not install an observer.")
    else:
        if len(actual) != 4 or actual[-1] not in [
            {"type": name, "fields": []}
            for name in (
                "SearchTrajectory.SearchTrajectoryObserver",
                "Main.SearchTrajectory.SearchTrajectoryObserver",
            )
        ]:
            raise ValueError("Unexpected observer plugin type, position or fields.")
    baseline_field = _field(record["baseline_plugins_field"])
    actual_field = _field(record["plugins_field"])
    if actual_field != _field(record["expected_plugins_field"]):
        raise ValueError("Actual plugins differ from the independent native reference.")
    fields = support.backend_without_output(record["backend_options"])
    if fields.get("plugins") != actual_field:
        raise ValueError("Concrete plugins disagree with their native snapshot.")
    if not observed and actual_field != baseline_field:
        raise ValueError("The control plugin field differs from the baseline.")
    if observed:
        # Pinned Options appends one empty plugin to the original tuple.
        clean = lambda value: "".join(value.replace("Main.", "").split())
        kind, value = clean(baseline_field["type"]), clean(baseline_field["value"])
        observer = clean(actual[-1]["type"])
        if (
            not kind.startswith("Tuple{")
            or not kind.endswith("}")
            or not value.startswith("(")
            or not value.endswith(")")
            or clean(actual_field["type"]) != kind[:-1] + "," + observer + "}"
            or clean(actual_field["value"]) != value[:-1] + "," + observer + "())"
        ):
            raise ValueError("The observer is not the sole concrete plugin extension.")
    names = (OBJECTIVE, OBJECTIVE.removeprefix("Main."))
    if fields.get("loss_function") not in [
        {"type": f"typeof({name})", "value": name} for name in names
    ]:
        raise ValueError("Wrong common trajectory objective guard.")
    normalized = copy.deepcopy(record)
    normalized["plugins"] = copy.deepcopy(baseline)
    normalized["plugins_field"] = copy.deepcopy(baseline_field)
    for field in normalized["backend_options"]:
        if field["name"] == "plugins":
            field.update(baseline_field)
        elif field["name"] == "loss_function":
            field.update(
                type=f"typeof({budget_control.OBJECTIVE})",
                value=budget_control.OBJECTIVE,
            )
    return normalized


def verify_options(record, seed, observed, base, support):
    normalized = _normalized_options(record, observed, support)
    result = budget_control.verify_options(normalized, seed, 100, base, support)
    return {**result, "observer": observed, "plugin_count": 4 if observed else 3}


def common_options(record, support):
    normalized = _normalized_options(record, record["observed"], support)
    # The budget is fixed at 100; only the independently checked seed is omitted.
    fields = support.backend_without_output(normalized["backend_options"])
    return {
        "fields": {key: value for key, value in fields.items() if key != "seed"},
        "optimizer_settings": normalized["optimizer_settings"],
        "plugins": normalized["plugins"],
    }


def raw_tree_id(tree):
    return _sha256(
        json.dumps(
            tree, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode()
    )


def float_from_bits(bits):
    if type(bits) is not str or not _BITS.fullmatch(bits):
        raise ValueError("Expected exactly 16 lowercase hexadecimal Float64 bits.")
    return struct.unpack(">d", bytes.fromhex(bits))[0]


def _bits(value):
    return struct.pack(">d", value).hex()


def decode_raw_tree(tree):
    """Validate before traversal; preserve binary order and every constant bit."""
    count, has_exp, finite = 0, False, True

    def visit(node):
        nonlocal count, has_exp, finite
        count += 1
        if count > 20 or type(node) is not dict:
            raise ValueError("Observation tree exceeds the pinned node bound.")
        kind = node.get("kind")
        if kind == "constant" and set(node) == {"kind", "value_bits"}:
            value = float_from_bits(node["value_bits"])
            finite &= math.isfinite(value)
            return {"kind": kind, "value_hex": value.hex()}
        if kind == "variable" and set(node) == {"kind", "index"}:
            if type(node["index"]) is not int or node["index"] != 1:
                raise ValueError("Observation trees may only use the time feature.")
            return dict(node)
        if kind != "operator" or set(node) != {
            "kind",
            "arity",
            "operator_index",
            "operator",
            "children",
        }:
            raise ValueError("Invalid observation tree node schema.")
        arity, index = node["arity"], node["operator_index"]
        names = UNARY if arity == 1 else BINARY if arity == 2 else ()
        if (
            type(arity) is not int
            or type(index) is not int
            or not 1 <= index <= len(names)
            or node["operator"] != names[index - 1]
            or type(node["children"]) is not list
            or len(node["children"]) != arity
        ):
            raise ValueError("Observation operator metadata differs from the grammar.")
        has_exp |= node["operator"] == "exp"
        return {**node, "children": [visit(child) for child in node["children"]]}

    result = visit(tree)
    return result, count, has_exp, finite


def _export_to_raw(tree):
    if tree.get("kind") == "constant":
        if set(tree) != {"kind", "value_hex"}:
            raise ValueError("Invalid original-front constant schema.")
        value = float.fromhex(tree["value_hex"])
        if not math.isfinite(value):
            raise ValueError("Original front constants must be finite.")
        return {"kind": "constant", "value_bits": _bits(value)}
    if tree.get("kind") == "variable":
        return dict(tree)
    return {**tree, "children": [_export_to_raw(c) for c in tree["children"]]}


def _unit_records(content):
    result = _read_json(content)
    if (
        type(result) is not dict
        or set(result) != {"format", "trees"}
        or result["format"] != UNITS_FORMAT
        or type(result["trees"]) is not dict
    ):
        raise ValueError("Invalid post-fit units record.")
    allowed = {
        ("valid", None),
        ("invalid", "dimensional_violation"),
        ("not_assessed", "nonfinite_constant"),
        ("not_assessed", "numerical_unresolved"),
    }
    for key, value in result["trees"].items():
        if (
            not _SHA256.fullmatch(key)
            or type(value) is not dict
            or set(value) != {"status", "reason"}
            or (value["status"], value["reason"]) not in allowed
        ):
            raise ValueError("Invalid post-fit unit status or tree identity.")
    return result["trees"]


def _loss_comparison(left, right):
    difference = abs(left - right)
    scale = max(abs(left), abs(right))
    return {
        "left": left,
        "right": right,
        "absolute_difference": difference,
        "relative_difference_symmetric": difference / scale if scale else 0.0,
        "rtol": 1e-10,
        "atol": 0.0,
        "status": "passed"
        if math.isclose(left, right, rel_tol=1e-10, abs_tol=0)
        else "failed",
    }


def _replay_records(content, inputs_hash, units_hash):
    result = _read_json(content)
    if (
        type(result) is not dict
        or set(result)
        != {"format", "inputs_sha256", "raw_sha256", "units_sha256", "trees"}
        or result["format"] != REPLAY_FORMAT
        or type(result["trees"]) is not dict
        or any(
            type(result[key]) is not str or not _SHA256.fullmatch(result[key])
            for key in ("inputs_sha256", "raw_sha256", "units_sha256")
        )
        or result["inputs_sha256"] != inputs_hash
        or result["units_sha256"] != units_hash
    ):
        raise ValueError("Invalid native replay schema or source binding.")
    for key, value in result["trees"].items():
        if (
            not _SHA256.fullmatch(key)
            or type(value) is not dict
            or set(value) != {"status", "reason", "loss_bits", "prediction_bits"}
        ):
            raise ValueError("Invalid native replay tree record.")
        if value["status"] == "available":
            if (
                value["reason"] is not None
                or type(value["prediction_bits"]) is not list
            ):
                raise ValueError("Invalid available native replay.")
            loss = float_from_bits(value["loss_bits"])
            prediction = [float_from_bits(bits) for bits in value["prediction_bits"]]
            if (
                not math.isfinite(loss)
                or loss < 0
                or not all(map(math.isfinite, prediction))
            ):
                raise ValueError(
                    "Available native replay must be finite and nonnegative."
                )
        elif (
            value["status"] != "not_assessed"
            or value["reason"]
            not in {
                "dimensional_violation",
                "nonfinite_constant",
                "numerical_unresolved",
            }
            or value["loss_bits"] is not None
            or value["prediction_bits"] is not None
        ):
            raise ValueError("Invalid unavailable native replay.")
    return result


def _tree_diagnosis(raw, arrays, units, replay):
    tree, size, has_exp, finite = decode_raw_tree(raw)
    result = {
        "tree": raw,
        "complexity": size,
        "has_exp": has_exp,
        "units": units,
        "ordinary_mse": None,
        "diagnostics": None,
        "status": "not_assessed",
        "reason": None,
        "native_replay": replay,
        "comparisons": {},
    }
    if units["status"] != "valid":
        if replay["status"] != "not_assessed" or replay["reason"] != units["reason"]:
            raise ValueError("Native replay contradicts its units record.")
    elif (
        replay["status"] == "not_assessed"
        and replay["reason"] != "numerical_unresolved"
    ):
        raise ValueError("Unavailable replay contradicts valid native units.")
    if not finite:
        if units != {"status": "not_assessed", "reason": "nonfinite_constant"}:
            raise ValueError(
                "Nonfinite constants contradict their native units record."
            )
        return {**result, "reason": "nonfinite_constant"}
    if units["reason"] == "nonfinite_constant":
        raise ValueError("Finite constants contradict their native units record.")
    if units["status"] != "valid":
        return {**result, "reason": units["reason"]}
    if replay["status"] != "available":
        return {**result, "reason": "native_replay_numerical_unresolved"}
    native_prediction = np.array(
        [float_from_bits(bits) for bits in replay["prediction_bits"]]
    )
    if native_prediction.shape != arrays["observed"].shape:
        raise ValueError("Native replay predictions must cover every training sample.")
    native_loss = float_from_bits(replay["loss_bits"])
    try:
        with np.errstate(over="raise", invalid="raise"):
            native_mse = mean_squared_error(arrays["observed"] - native_prediction)
    except (ValueError, OverflowError, FloatingPointError) as error:
        raise ValueError(
            "Native replay predictions contradict its finite loss."
        ) from error
    same_predictions = _loss_comparison(native_loss, native_mse)
    if same_predictions["status"] != "passed":
        raise ValueError("Native replay loss contradicts MSE of native predictions.")
    result["comparisons"]["native_loss_vs_native_prediction_mse"] = same_predictions
    result["native_mse"] = native_mse
    try:
        prediction = evaluate_tree(tree, arrays["time_s"])
        with np.errstate(all="raise"):
            residual = np.asarray(arrays["observed"], dtype=np.float64) - prediction
        mse = mean_squared_error(residual)
    except (ValueError, OverflowError, FloatingPointError):
        return {**result, "reason": "nonfinite_training_prediction_or_loss"}
    result["ordinary_mse"] = mse
    result["comparisons"]["native_vs_python_tree_mse"] = _loss_comparison(
        native_loss, mse
    )
    scale = max(
        float(np.max(np.abs(prediction))), float(np.max(np.abs(native_prediction)))
    )
    normalized_difference = (
        float(np.max(np.abs(prediction / scale - native_prediction / scale)))
        if scale
        else 0.0
    )
    prediction_comparison = {
        "status": "passed",
        "amplitude_scale": scale,
        "max_normalized_difference": normalized_difference,
        "rtol": 1e-12,
        "normalized_atol": 1e-14,
    }
    try:
        _check_prediction_replay(prediction, native_prediction)
    except AssertionError:
        prediction_comparison["status"] = "failed"
    result["comparisons"]["native_vs_python_prediction"] = prediction_comparison
    reasons = []
    if result["comparisons"]["native_vs_python_tree_mse"]["status"] != "passed":
        reasons.append("native_python_loss_mismatch")
    if prediction_comparison["status"] != "passed":
        reasons.append("native_python_prediction_mismatch")
    candidate = {
        "tree": tree,
        "complexity": size,
        "loss": mse,
        "display_equation": "observed original tree; no replacement selection",
    }
    diagnosis = diagnose_candidate(candidate, 0, -1, arrays, "complexity_frequency")
    if reasons:
        diagnosis["curve_marker"] = "not_assessed"
        diagnosis["parameter_match"].update(
            status="not_assessed", reason="unresolved_native_python_replay"
        )
        return {
            **result,
            "diagnostics": diagnosis,
            "status": "numerical_unresolved",
            "reason": reasons[0],
            "reasons": reasons,
        }
    return {
        **result,
        "status": "available",
        "ordinary_mse": mse,
        "diagnostics": diagnosis,
    }


def _bounded_bytes(path, limit, check):
    check()
    if path.is_symlink():
        raise ValueError("Observation artifacts must not be symbolic links.")
    chunks, size = [], 0
    with path.open("rb") as stream:
        while chunk := stream.read(min(1024 * 1024, limit - size + 1)):
            size += len(chunk)
            if size > limit:
                raise ValueError("Observation artifact exceeds its byte limit.")
            chunks.append(chunk)
            check()
    return b"".join(chunks)


def _bounded_digest(path, limit, check):
    check()
    if path.is_symlink():
        raise ValueError("Observation artifacts must not be symbolic links.")
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as stream:
        while chunk := stream.read(min(1024 * 1024, limit - size + 1)):
            size += len(chunk)
            if size > limit:
                raise ValueError("Observation artifact exceeds its byte limit.")
            digest.update(chunk)
            check()
    return digest.hexdigest()


def verify_observations(
    path,
    *,
    expected_events,
    arrays,
    front,
    check=lambda: None,
    expected_sha256=None,
    expected_record=None,
    units_path=None,
    expected_units_sha256=None,
    replay_path=None,
    expected_replay_sha256=None,
    expected_inputs_sha256=None,
):
    """Stream immutable raw occurrences; assess unique trees only after the search."""
    path = Path(path)
    units_path = (
        Path(units_path)
        if units_path is not None
        else path.with_name("observation_units.json")
    )
    replay_path = (
        Path(replay_path)
        if replay_path is not None
        else path.with_name("observation_replays.json")
    )
    if type(expected_inputs_sha256) is not str or not _SHA256.fullmatch(
        expected_inputs_sha256
    ):
        raise ValueError("The verified training-input checksum is required.")
    if type(expected_events) is not int or expected_events <= 0:
        raise ValueError("Expected event count must be a positive integer.")
    for file in (path, units_path, replay_path):
        if file.is_symlink() or not file.is_file():
            raise ValueError("Observation artifacts must be regular files.")
    check()
    sizes = path.stat().st_size, units_path.stat().st_size, replay_path.stat().st_size
    if sum(sizes) > MAX_OBSERVATION_BYTES:
        raise ValueError("Observation files exceed the frozen byte limit.")
    units_bytes = _bounded_bytes(
        units_path, MAX_OBSERVATION_BYTES - sizes[0] - sizes[2], check
    )
    replay_bytes = _bounded_bytes(
        replay_path, MAX_OBSERVATION_BYTES - sizes[0] - len(units_bytes), check
    )
    replay_hash = _sha256(replay_bytes)
    if expected_replay_sha256 is not None and replay_hash != expected_replay_sha256:
        raise ValueError("Changed native replay artifact.")
    units_hash = _sha256(units_bytes)
    if expected_units_sha256 is not None and units_hash != expected_units_sha256:
        raise ValueError("Changed post-fit unit artifact.")
    units = _unit_records(units_bytes)
    replays = _replay_records(replay_bytes, expected_inputs_sha256, units_hash)
    final_ids = set()
    for candidate in front["candidates"]:
        raw = _export_to_raw(candidate["tree"])
        decode_raw_tree(raw)
        final_ids.add(raw_tree_id(raw))
    unique, forms = {}, {}
    total, members, events = 0, 0, 0
    counts = Counter(
        returned_population=0,
        hall_of_fame=0,
        verified=0,
        numerical_unresolved=0,
        not_assessed=0,
    )
    occurrences = []
    digest = hashlib.sha256()

    def shape(node):
        if node["kind"] == "constant":
            return {"kind": "constant"}
        if node["kind"] == "variable":
            return node
        return {**node, "children": [shape(child) for child in node["children"]]}

    def occurrence(member, source, position, event_index):
        nonlocal members
        if type(member) is not dict or set(member) != {
            "tree",
            "loss_bits",
            "cost_bits",
            "complexity_cache",
            "birth",
            "ref",
            "parent",
        }:
            raise ValueError("Invalid raw observation member schema.")
        for name in ("complexity_cache", "birth", "ref", "parent"):
            if type(member[name]) is not int or not -(2**63) <= member[name] < 2**63:
                raise ValueError("Invalid raw observation integer metadata.")
        _, size, _, _ = decode_raw_tree(member["tree"])
        if member["complexity_cache"] not in (-1, size):
            raise ValueError("Cached complexity contradicts the exact observed tree.")
        if source == "hall_of_fame" and position != size:
            raise ValueError("Hall-of-Fame slot contradicts the observed complexity.")
        loss, cost = (
            float_from_bits(member["loss_bits"]),
            float_from_bits(member["cost_bits"]),
        )
        if math.isfinite(loss) and loss < 0:
            raise ValueError("A finite ordinary training loss must be nonnegative.")
        key = raw_tree_id(member["tree"])
        if key not in units or key not in replays["trees"]:
            raise ValueError("An observed tree is missing from a diagnostic artifact.")
        if key not in unique:
            analysis = _tree_diagnosis(
                member["tree"], arrays, units[key], replays["trees"][key]
            )
            form = raw_tree_id(shape(member["tree"]))
            unique[key] = {
                **analysis,
                "tree_sha256": key,
                "form_sha256": form,
                "in_final_front": key in final_ids,
                "sources": {},
                "occurrence_statuses": Counter(),
            }
            forms.setdefault(form, {"tree_count": 0, "occurrences": 0, "sources": {}})[
                "tree_count"
            ] += 1
        entry = unique[key]
        reasons = list(entry.get("reasons", []))
        if entry["reason"] and entry["reason"] not in reasons:
            reasons.append(entry["reason"])
        comparisons = dict(entry["comparisons"])
        if math.isfinite(loss) and units[key]["status"] == "invalid":
            raise ValueError("Finite saved loss contradicts invalid native units.")
        if math.isfinite(loss) and "native_mse" in entry:
            comparisons["saved_vs_native_loss"] = _loss_comparison(
                loss, float_from_bits(entry["native_replay"]["loss_bits"])
            )
            if comparisons["saved_vs_native_loss"]["status"] != "passed":
                reasons.append("saved_native_loss_mismatch")
        if not math.isfinite(loss):
            reasons.append("nonfinite_backend_loss")
            status = "not_assessed"
        elif entry["status"] == "available":
            status = "numerical_unresolved" if reasons else "verified"
        else:
            status = entry["status"]
        # A nonfinite cost is retained and cannot be counted as a positive member.
        if not math.isfinite(cost):
            status = "not_assessed"
            reasons.append("nonfinite_backend_cost")
        curve_marker = (
            entry["diagnostics"]["curve_marker"]
            if status == "verified"
            else "not_assessed"
        )
        parameter_marker = (
            entry["diagnostics"]["parameter_match"]["status"]
            if status == "verified"
            else "not_assessed"
        )
        occurrences.append(
            {
                "tree_sha256": key,
                "event_index": event_index,
                "source": source,
                "position": position,
                "loss_bits": member["loss_bits"],
                "cost_bits": member["cost_bits"],
                "status": status,
                "reasons": reasons,
                "comparisons": comparisons,
                "curve_marker": curve_marker,
                "parameter_marker": parameter_marker,
            }
        )
        item = entry["sources"].setdefault(
            source,
            {
                "first_event": event_index,
                "last_event": event_index,
                "occurrences": 0,
                "event_indices": [],
                "verified_occurrences": 0,
                "curve_success_occurrences": 0,
                "parameter_success_occurrences": 0,
                "status_counts": Counter(
                    verified=0, numerical_unresolved=0, not_assessed=0
                ),
            },
        )
        item["last_event"] = event_index
        item["occurrences"] += 1
        if not item["event_indices"] or item["event_indices"][-1] != event_index:
            item["event_indices"].append(event_index)
        item["verified_occurrences"] += status == "verified"
        item["status_counts"][status] += 1
        item["parameter_success_occurrences"] += parameter_marker == "matched"
        item["curve_success_occurrences"] += (
            status == "verified"
            and entry["diagnostics"]["curve_marker"] == "within_tolerance"
        )
        entry["occurrence_statuses"][status] += 1
        counts[source] += 1
        counts[status] += 1
        form = forms[entry["form_sha256"]]
        form["occurrences"] += 1
        form_source = form["sources"].setdefault(
            source,
            {
                "first_event": event_index,
                "last_event": event_index,
                "occurrences": 0,
                "event_indices": [],
                "status_counts": Counter(
                    verified=0, numerical_unresolved=0, not_assessed=0
                ),
                "curve_success_occurrences": 0,
                "parameter_success_occurrences": 0,
            },
        )
        form_source["last_event"] = event_index
        form_source["occurrences"] += 1
        form_source["status_counts"][status] += 1
        form_source["curve_success_occurrences"] += curve_marker == "within_tolerance"
        form_source["parameter_success_occurrences"] += parameter_marker == "matched"
        if (
            not form_source["event_indices"]
            or form_source["event_indices"][-1] != event_index
        ):
            form_source["event_indices"].append(event_index)
        members += 1

    with path.open("rb") as stream:
        while True:
            check()
            line = stream.readline(MAX_OBSERVATION_BYTES + 1)
            if not line:
                break
            total += len(line)
            if total + len(units_bytes) + len(replay_bytes) > MAX_OBSERVATION_BYTES:
                raise ValueError("Observation stream exceeds the frozen byte limit.")
            if not line.endswith(b"\n"):
                raise ValueError("Truncated observation event.")
            digest.update(line)
            event = _read_json(line)
            events += 1
            if (
                type(event) is not dict
                or set(event)
                != {"format", "event_index", "returned_population", "hall_of_fame"}
                or event["format"] != EVENT_FORMAT
                or type(event["event_index"]) is not int
                or event["event_index"] != events
                or events > expected_events
                or type(event["returned_population"]) is not list
                or len(event["returned_population"]) != 32
                or type(event["hall_of_fame"]) is not list
                or len(event["hall_of_fame"]) > 20
            ):
                raise ValueError("Missing, duplicate or malformed observation event.")
            for position, member in enumerate(event["returned_population"], 1):
                occurrence(member, "returned_population", position, events)
            slots = []
            for item in event["hall_of_fame"]:
                if (
                    type(item) is not dict
                    or set(item) != {"slot", "member"}
                    or type(item["slot"]) is not int
                    or not 1 <= item["slot"] <= 20
                    or (slots and item["slot"] <= slots[-1])
                ):
                    raise ValueError("Missing order or duplicated Hall-of-Fame slot.")
                slots.append(item["slot"])
                occurrence(item["member"], "hall_of_fame", item["slot"], events)
    raw_hash = digest.hexdigest()
    if (
        events != expected_events
        or set(unique) != set(units)
        or set(unique) != set(replays["trees"])
    ):
        raise ValueError("Incomplete observations or mismatched unit-tree coverage.")
    if expected_sha256 is not None and raw_hash != expected_sha256:
        raise ValueError("Changed raw observation artifact.")
    if replays["raw_sha256"] != raw_hash:
        raise ValueError("Native replays are bound to different raw observations.")
    summary = {
        "status": "completed",
        "event_count": events,
        "member_count": members,
        "bytes_written": total,
        "units_bytes": len(units_bytes),
        "replay_bytes": len(replay_bytes),
        "total_bytes": total + len(units_bytes) + len(replay_bytes),
        "max_bytes": MAX_OBSERVATION_BYTES,
        "expected_events": expected_events,
        "raw_sha256": raw_hash,
        "units_sha256": units_hash,
        "replay_sha256": replay_hash,
    }
    if expected_record is not None and expected_record != summary:
        raise ValueError(
            "Native observation counters disagree with recorded artifacts."
        )
    check()
    if (
        path.is_symlink()
        or units_path.is_symlink()
        or replay_path.is_symlink()
        or (
            _bounded_digest(path, total, check) != raw_hash
            or _bounded_bytes(units_path, len(units_bytes), check) != units_bytes
            or _bounded_bytes(replay_path, len(replay_bytes), check) != replay_bytes
        )
    ):
        raise ValueError("Observation artifacts changed during diagnosis.")
    for entry in unique.values():
        verified = entry["occurrence_statuses"]["verified"]
        entry["aggregation_scope"] = (
            "all_occurrences_must_verify_for_tree_markers; valid_occurrences_count_separately"
        )
        if verified != sum(entry["occurrence_statuses"].values()):
            entry.update(
                status="numerical_unresolved"
                if verified or entry["occurrence_statuses"]["numerical_unresolved"]
                else "not_assessed",
                reason="mixed_occurrence_verification"
                if verified
                else entry["reason"] or "no_verified_occurrence",
            )
            if entry["diagnostics"] is not None:
                entry["diagnostics"]["curve_marker"] = "not_assessed"
                entry["diagnostics"]["parameter_match"].update(
                    status="not_assessed", reason="no_verified_observed_loss_and_cost"
                )
    check()
    return {
        "format": FORMAT,
        "status": "verified",
        "verification_scope": "complete artifacts and classified occurrences; numerical status remains per occurrence",
        "observation": summary,
        "source_file_sha256": {
            path.name: raw_hash,
            units_path.name: units_hash,
            replay_path.name: replay_hash,
        },
        "counts": dict(counts),
        "unique_tree_count": len(unique),
        "unique_form_count": len(forms),
        "trees": list(unique.values()),
        "occurrences": occurrences,
        "forms": forms,
        "physical_identification": "not_assessed",
        "interpretation": "occurrences by source only; final-front absence is not disappearance",
    }


def compare_pair(control, observed):
    """Require exact exported search results, excluding only validated elapsed times."""

    def signature(front):
        if (
            type(front) is not dict
            or front.get("format") != ARM_FORMAT
            or not front.get("candidates")
            or type(front.get("selected_index")) is not int
            or not 0 <= front["selected_index"] < len(front["candidates"])
            or type(front.get("callback_calls_during_fit")) is not int
            or front["callback_calls_during_fit"] <= 0
        ):
            raise ValueError("Invalid complete trajectory pair result.")
        timing = front.get("timing_seconds")
        if (
            type(timing) is not dict
            or set(timing) != {"worker_setup", "fit_including_jit_and_python_exports"}
            or any(
                type(v) not in (int, float) or not math.isfinite(v) or v < 0
                for v in timing.values()
            )
        ):
            raise ValueError("Invalid excluded timing metadata.")

        def exact(value):
            if type(value) is float:
                if not math.isfinite(value):
                    raise ValueError("Nonfinite values are not pair equality evidence.")
                return ("float64", _bits(value))
            if type(value) is dict:
                return {key: exact(item) for key, item in value.items()}
            if type(value) is list:
                return [exact(item) for item in value]
            return (type(value).__name__, value)

        return exact(
            {key: value for key, value in front.items() if key != "timing_seconds"}
        )

    if signature(control) != signature(observed):
        raise ValueError("Observer/control exported search results differ.")
    return {
        "status": "passed",
        "comparison": "all original result fields, float64_bits",
        "excluded_fields": ["timing_seconds"],
        "scope": "exported sizes/order/trees/selection/predictions/residuals/losses/callbacks; not hidden states",
    }
