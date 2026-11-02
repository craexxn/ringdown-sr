"""Counterexamples for exact passive records, pair equality and front interpretation."""

import copy
import json
import math
import pickle
import struct
import sys
from types import SimpleNamespace

import numpy as np
import pytest
from test_free_optimizer_budget import option_fixture as budget_fixture
from test_noiseless_control import DRIVER as BASE
from test_noiseless_control import candidate, reference_tree
from test_structure import constant, operator, time_node

from ringdown_sr import search_trajectory as control
from ringdown_sr import symbolic
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _sha256


def option_fixture(seed, observed):
    result = budget_fixture(seed, 100)
    result["observed"] = observed
    result["baseline_plugins"] = copy.deepcopy(result["plugins"])
    result["baseline_plugins_field"] = copy.deepcopy(result["plugins_field"])
    if observed:
        plugin = "Main.SearchTrajectory.SearchTrajectoryObserver"
        result["plugins"].append({"type": plugin, "fields": []})
        field = result["plugins_field"]
        field["type"] = field["type"][:-1] + "," + plugin + "}"
        field["value"] = field["value"][:-1] + "," + plugin + "())"
    result["expected_plugins_field"] = copy.deepcopy(result["plugins_field"])
    for field in result["backend_options"]:
        if field["name"] == "loss_function":
            field.update(type=f"typeof({control.OBJECTIVE})", value=control.OBJECTIVE)
        elif field["name"] == "plugins":
            field.update(result["plugins_field"])
    return result


def raw_tree(tree):
    if tree["kind"] == "constant":
        return {
            "kind": "constant",
            "value_bits": struct.pack(">d", float.fromhex(tree["value_hex"])).hex(),
        }
    if tree["kind"] == "variable":
        return dict(tree)
    return {**tree, "children": [raw_tree(child) for child in tree["children"]]}


def member(tree, loss, **changes):
    raw = raw_tree(tree)
    _, count, _, _ = control.decode_raw_tree(raw)
    return {
        "tree": raw,
        "loss_bits": struct.pack(">d", loss).hex(),
        "cost_bits": struct.pack(">d", loss).hex(),
        "complexity_cache": count,
        "birth": 2,
        "ref": 9,
        "parent": -1,
        **changes,
    }


def write_observations(tmp_path, members, *, events=2, units=None, hof=True):
    path = tmp_path / "observations.jsonl"
    items = []
    for i in range(events):
        by_size = {m["complexity_cache"]: m for m in members}
        items.append(
            {
                "format": control.EVENT_FORMAT,
                "event_index": i + 1,
                "returned_population": [
                    copy.deepcopy(members[j % len(members)]) for j in range(32)
                ],
                "hall_of_fame": [
                    {"slot": k, "member": copy.deepcopy(v)}
                    for k, v in sorted(by_size.items())
                ]
                if hof
                else [],
            }
        )
    path.write_bytes(b"".join(json.dumps(item).encode() + b"\n" for item in items))
    mapping = {
        control.raw_tree_id(m["tree"]): {"status": "valid", "reason": None}
        for m in members
    }
    if units is not None:
        mapping.update(units)
    unit_path = tmp_path / "observation_units.json"
    unit_path.write_text(
        json.dumps({"format": control.UNITS_FORMAT, "trees": mapping}), encoding="utf-8"
    )
    return path, items


def test_frozen_cells_profiles_and_plan():
    assert [(c["budget"]["seed"], c["observed"]) for c in control.planned_cells()] == [
        (20261020, False),
        (20261020, True),
        (20261021, True),
        (20261021, False),
        (20261022, False),
        (20261022, True),
    ]
    assert all(
        c["iterations"] == 100 and c["budget"]["niterations"] == 200
        for c in control.planned_cells()
    )
    assert control.LIMIT_SECONDS == 3600 and control.WORKER_LIMIT_SECONDS == 600
    assert control.MAX_OBSERVATION_BYTES == 256 * 1024 * 1024
    assert _sha256((control.ROOT / control.PLAN).read_bytes()) == control.PLAN_SHA256


@pytest.mark.parametrize(
    "document",
    [
        {},
        {"format": control.PROFILE_FORMAT, "observed": 1},
        {"format": control.PROFILE_FORMAT, "observed": "true"},
        {"format": control.PROFILE_FORMAT, "observed": True, "truth": [1]},
        {"format": control.PROFILE_FORMAT, "observed": False, "iterations": 200},
    ],
)
def test_profiles_reject_truth_and_unapproved_overrides(document):
    with pytest.raises(ValueError):
        control.checked_profile(document)


def test_observer_descriptor_is_literal_json_and_portable_pickle():
    descriptor = control.ObserverDescriptor()
    assert json.loads(json.dumps({"plugins": [descriptor]})) == {
        "plugins": [control.OBSERVER]
    }
    restored = pickle.loads(pickle.dumps(descriptor))
    assert type(restored) is control.ObserverDescriptor
    assert restored == control.OBSERVER
    with pytest.raises(ValueError):
        control.ObserverDescriptor("unapproved plugin")


def test_explicit_baseline_descriptors_preserve_order_and_pickle_without_eval(
    monkeypatch,
):
    calls = []

    def baseline(index):
        calls.append(index)
        return f"baseline {index}"

    def observer():
        calls.append("observer")
        return "observer"

    monkeypatch.setitem(
        sys.modules,
        "juliacall",
        SimpleNamespace(
            Main=SimpleNamespace(
                SearchTrajectory=SimpleNamespace(
                    baseline_plugin=baseline, SearchTrajectoryObserver=observer
                )
            )
        ),
    )
    literals = [
        "Main.SearchTrajectory.baseline_plugin(1)",
        "Main.SearchTrajectory.baseline_plugin(2)",
        "Main.SearchTrajectory.baseline_plugin(3)",
        "Main.SearchTrajectory.SearchTrajectoryObserver()",
    ]
    assert list(control.OBSERVED_PLUGINS) == literals
    descriptors = [control.TrajectoryPluginDescriptor(value) for value in literals]
    assert json.loads(json.dumps(descriptors)) == literals
    restored = pickle.loads(pickle.dumps(descriptors))
    assert all(type(item) is control.TrajectoryPluginDescriptor for item in restored)
    assert [item.julia_plugin() for item in restored] == [
        "baseline 1",
        "baseline 2",
        "baseline 3",
        "observer",
    ]
    assert calls == [1, 2, 3, "observer"]


@pytest.mark.parametrize(
    "descriptor",
    [
        "Main.SearchTrajectory.baseline_plugin(0)",
        "Main.SearchTrajectory.baseline_plugin(4)",
        "Main.SearchTrajectory.baseline_plugin(true)",
        "Main.SearchTrajectory.baseline_plugin(1.0)",
        "Main.SearchTrajectory.baseline_plugin(1); rand()",
        "unapproved plugin",
        1,
        True,
        None,
    ],
)
def test_plugin_descriptor_rejects_unapproved_calls_and_indices(descriptor):
    with pytest.raises(ValueError):
        control.TrajectoryPluginDescriptor(descriptor)


@pytest.mark.parametrize(
    "fault", ["input", "runtime", "source", "missing_hash", "manifest_format"]
)
def test_worker_manifest_guards_consumed_inputs_runtime_and_source(
    tmp_path, monkeypatch, fault
):
    directory, runtime = tmp_path / "cell", tmp_path / "runtime"
    directory.mkdir()
    runtime.mkdir()
    sources = {value: _sha256(key.encode()) for key, value in control.RUNTIME.items()}
    monkeypatch.setattr(control, "source_hashes", lambda: sources)
    for key in control.RUNTIME:
        (runtime / key).write_bytes(key.encode())
    for name in ("request.json", "inputs.npz", "profile.json"):
        (directory / name).write_bytes(name.encode())
    manifest = {
        "format": control.FORMAT,
        "sources": copy.deepcopy(sources),
        "runtime": {key: sources[value] for key, value in control.RUNTIME.items()},
        "inputs": {
            name: _sha256((directory / name).read_bytes())
            for name in ("request.json", "inputs.npz", "profile.json")
        },
    }
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert control.verify_manifest(directory, runtime) == manifest
    if fault == "input":
        (directory / "inputs.npz").write_bytes(b"changed")
    elif fault == "runtime":
        (runtime / "worker.py").write_bytes(b"changed")
    elif fault == "source":
        manifest["sources"][control.RUNTIME["worker.py"]] = "0" * 64
    elif fault == "missing_hash":
        manifest["inputs"].pop("profile.json")
    else:
        manifest["format"] = "other"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError):
        control.verify_manifest(directory, runtime)


@pytest.mark.parametrize("observed", [False, True])
def test_only_common_guard_and_observer_change_approved_100_profile(observed):
    budget = symbolic.SearchBudget(seed=20261020, niterations=200)
    before = control.budget_control.profile_parameters(budget, 100)
    parameters = control.profile_parameters(budget, observed)
    assert {k for k in before if before[k] != parameters[k]} == {"loss_function"}
    assert parameters["plugins"] == (
        list(control.OBSERVED_PLUGINS) if observed else None
    )
    assert symbolic.search_parameters(budget)["optimizer_iterations"] == 20


@pytest.mark.parametrize("seed", control.SEEDS)
def test_options_are_absolute_for_first_cell_and_every_seed(seed):
    values = [option_fixture(seed, observed) for observed in (False, True)]
    unchanged = copy.deepcopy(values)
    for observed, record in zip((False, True), values, strict=True):
        assert (
            control.verify_options(record, seed, observed, BASE, BASE.load_support())[
                "status"
            ]
            == "passed"
        )
    assert control.common_options(
        values[0], BASE.load_support()
    ) == control.common_options(values[1], BASE.load_support())
    assert values == unchanged
    assert "plugins" in control.common_options(values[0], BASE.load_support())["fields"]


@pytest.mark.parametrize(
    "fault",
    [
        "seed",
        "maxsize",
        "objective",
        "observer_fields",
        "observer_position",
        "original_fields",
        "concrete_plugins",
        "expected_plugins",
        "enabled",
    ],
)
def test_forged_or_unplanned_native_options_fail(fault):
    record = option_fixture(20261020, True)
    if fault == "seed":
        record["backend_seed"] = 42
    elif fault in {"maxsize", "objective"}:
        name = "maxsize" if fault == "maxsize" else "loss_function"
        next(x for x in record["backend_options"] if x["name"] == name)["value"] = "19"
    elif fault == "observer_fields":
        record["plugins"][-1]["fields"] = [
            {"name": "seed", "type": "Int64", "value": "42"}
        ]
    elif fault == "observer_position":
        record["plugins"].reverse()
    elif fault == "original_fields":
        record["plugins"][0]["fields"][0]["value"] = "0.0"
        record["baseline_plugins"] = copy.deepcopy(record["plugins"][:3])
    elif fault == "concrete_plugins":
        record["plugins_field"]["value"] += "changed"
        record["expected_plugins_field"] = copy.deepcopy(record["plugins_field"])
        next(x for x in record["backend_options"] if x["name"] == "plugins").update(
            record["plugins_field"]
        )
    elif fault == "expected_plugins":
        record["expected_plugins_field"]["value"] += "changed"
    else:
        record["observed"] = False
    with pytest.raises(ValueError):
        control.verify_options(record, 20261020, True, BASE, BASE.load_support())


def test_hof_member_can_remain_at_last_event_without_final_front_membership(tmp_path):
    time = np.arange(128, dtype=np.float64) / 4096
    inner = np.array([(j + k / 8) / 4096 for j in range(127) for k in range(1, 8)])
    arrays = {
        "time_s": time,
        "observed": 1 + time,
        "diagnostic_time_s": inner,
        "diagnostic_truth": 1 + inner,
    }
    exact = operator("+", constant(1), time_node())
    approximate = operator(
        "+", time_node(), operator("exp", operator("*", constant(0.0001), time_node()))
    )
    a, b = candidate(exact, arrays), candidate(approximate, arrays)
    path, _ = write_observations(
        tmp_path, [member(exact, a["loss"]), member(approximate, b["loss"])]
    )
    result = control.verify_observations(
        path, expected_events=2, arrays=arrays, front={"candidates": [a]}
    )
    q = next(t for t in result["trees"] if t["has_exp"])
    assert q["diagnostics"]["curve_marker"] == "within_tolerance"
    assert q["sources"]["hall_of_fame"]["last_event"] == 2
    assert q["sources"]["hall_of_fame"]["occurrences"] == 2
    assert q["in_final_front"] is False
    assert not any("disappear" in key for key in q)
    assert result["observation"]["member_count"] == 68
    assert result["unique_tree_count"] == 2


def test_forms_keep_source_specific_event_ordinals_and_occurrence_denominators(
    tmp_path,
):
    arrays = frozen_data()
    trees = [constant(0), constant(1), operator("*", constant(6), time_node())]
    candidates = [candidate(tree, arrays) for tree in trees]
    a, b, other = [member(c["tree"], c["loss"]) for c in candidates]
    path, _ = write_observations(tmp_path, [a, b, other], events=4)
    populations = [[other] * 32, [a] * 16 + [b] * 16, [other] * 32, [b] * 32]
    halls = [[other], [a, other], [a, other], [a, other]]
    events = [
        {
            "format": control.EVENT_FORMAT,
            "event_index": index,
            "returned_population": population,
            "hall_of_fame": [
                {"slot": entry["complexity_cache"], "member": entry} for entry in hall
            ],
        }
        for index, (population, hall) in enumerate(
            zip(populations, halls, strict=True), 1
        )
    ]
    path.write_bytes(b"".join(json.dumps(event).encode() + b"\n" for event in events))
    result = control.verify_observations(
        path, expected_events=4, arrays=arrays, front={"candidates": [candidates[0]]}
    )
    first, second = [
        next(item for item in result["trees"] if item["tree"] == entry["tree"])
        for entry in (a, b)
    ]
    assert first["form_sha256"] == second["form_sha256"]
    form = result["forms"][first["form_sha256"]]
    assert form == {
        "tree_count": 2,
        "occurrences": 67,
        "sources": {
            "returned_population": {
                "first_event": 2,
                "last_event": 4,
                "occurrences": 64,
                "event_indices": [2, 4],
            },
            "hall_of_fame": {
                "first_event": 2,
                "last_event": 4,
                "occurrences": 3,
                "event_indices": [2, 3, 4],
            },
        },
    }
    assert first["sources"]["returned_population"]["occurrences"] == 16
    assert second["sources"]["returned_population"]["occurrences"] == 48
    assert second["sources"]["returned_population"]["last_event"] == 4
    assert second["in_final_front"] is False
    assert result["observation"]["member_count"] == 135
    assert result["unique_tree_count"] == 3 and result["unique_form_count"] == 2
    assert sum(item["occurrences"] for item in result["forms"].values()) == 135


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "duplicate",
        "truncated",
        "population_size",
        "slot_duplicate",
        "cache",
        "mse",
        "operator",
        "units_missing",
        "units_extra",
        "unit_finite_conflict",
        "raw_hash",
        "unit_hash",
        "counter",
    ],
)
def test_corrupt_or_incomplete_observations_fail(tmp_path, fault):
    arrays = frozen_data()
    record = candidate(reference_tree(), arrays)
    path, events = write_observations(
        tmp_path, [member(record["tree"], record["loss"])]
    )
    kwargs = {}
    units_path = path.with_name("observation_units.json")
    if fault == "missing":
        events.pop()
    elif fault == "duplicate":
        events[1]["event_index"] = 1
    elif fault == "population_size":
        events[0]["returned_population"].pop()
    elif fault == "slot_duplicate":
        events[0]["hall_of_fame"] *= 2
    elif fault == "cache":
        events[0]["returned_population"][0]["complexity_cache"] = 18
    elif fault == "mse":
        events[0]["returned_population"][0]["loss_bits"] = struct.pack(">d", 1.0).hex()
    elif fault == "operator":
        events[0]["returned_population"][0]["tree"]["operator"] = "/"
    elif fault.startswith("units_") or fault == "unit_finite_conflict":
        units = json.loads(units_path.read_bytes())
        if fault == "units_missing":
            units["trees"].clear()
        elif fault == "units_extra":
            units["trees"]["0" * 64] = {"status": "valid", "reason": None}
        else:
            for key in units["trees"]:
                units["trees"][key] = {
                    "status": "invalid",
                    "reason": "dimensional_violation",
                }
        units_path.write_text(json.dumps(units), encoding="utf-8")
    elif fault == "raw_hash":
        kwargs["expected_sha256"] = "0" * 64
    elif fault == "unit_hash":
        kwargs["expected_units_sha256"] = "0" * 64
    elif fault == "counter":
        kwargs["expected_record"] = {"event_count": 2}
    path.write_bytes(b"".join(json.dumps(e).encode() + b"\n" for e in events))
    if fault == "truncated":
        path.write_bytes(path.read_bytes()[:-1])
    with pytest.raises(ValueError):
        control.verify_observations(
            path,
            expected_events=2,
            arrays=arrays,
            front={"candidates": [record]},
            **kwargs,
        )


@pytest.mark.parametrize(
    "kind", ["infinite_loss", "invalid_units", "nan_constant", "nan_cost"]
)
def test_legitimate_unusable_members_are_retained_without_positive_markers(
    tmp_path, kind
):
    arrays = frozen_data()
    record = candidate(reference_tree(), arrays)
    item = member(record["tree"], record["loss"])
    unit = {"status": "valid", "reason": None}
    if kind in {"infinite_loss", "invalid_units"}:
        item["loss_bits"] = struct.pack(">d", math.inf).hex()
    if kind == "invalid_units":
        unit = {"status": "invalid", "reason": "dimensional_violation"}
    elif kind == "nan_constant":
        item["tree"] = {"kind": "constant", "value_bits": "7ff8000000000042"}
        item["complexity_cache"] = 1
        item["loss_bits"] = struct.pack(">d", math.inf).hex()
        unit = {"status": "not_assessed", "reason": "nonfinite_constant"}
    elif kind == "nan_cost":
        item["cost_bits"] = "7ff8000000000042"
    path, _ = write_observations(
        tmp_path, [item], units={control.raw_tree_id(item["tree"]): unit}
    )
    result = control.verify_observations(
        path, expected_events=2, arrays=arrays, front={"candidates": [record]}
    )
    saved = result["trees"][0]
    assert saved["tree"] == item["tree"]
    assert saved["status"] == "not_assessed"
    assert result["counts"]["not_assessed"] == 66
    if saved["diagnostics"] is not None:
        assert saved["diagnostics"]["curve_marker"] == "not_assessed"
        assert saved["diagnostics"]["parameter_match"]["status"] == "not_assessed"
    assert saved["sources"]["hall_of_fame"]["curve_success_occurrences"] == 0


def test_byte_limit_and_late_mutation_abort_without_modifying_source(
    tmp_path, monkeypatch
):
    arrays = frozen_data()
    record = candidate(constant(0), arrays)
    path, _ = write_observations(tmp_path, [member(record["tree"], record["loss"])])
    before = path.read_bytes()
    with monkeypatch.context() as scoped:
        scoped.setattr(control, "MAX_OBSERVATION_BYTES", len(before))
        with pytest.raises(ValueError, match="byte limit"):
            control.verify_observations(
                path, expected_events=2, arrays=arrays, front={"candidates": [record]}
            )
    assert path.read_bytes() == before
    calls = 0

    def changed():
        nonlocal calls
        calls += 1
        if calls == 5:
            path.write_bytes(before.replace(b'"birth": 2', b'"birth": 3'))

    with pytest.raises(ValueError, match="changed during diagnosis"):
        control.verify_observations(
            path,
            expected_events=2,
            arrays=arrays,
            front={"candidates": [record]},
            check=changed,
        )


def pair_fixture():
    arrays = frozen_data()
    return {
        "format": symbolic.FORMAT,
        "candidates": [candidate(constant(0), arrays)],
        "selected_index": 0,
        "callback_calls_during_fit": 32,
        "timing_seconds": {
            "worker_setup": 1.0,
            "fit_including_jit_and_python_exports": 2.0,
        },
        "rng": {"python_seed": 20261020, "backend_seed": 465951028},
    }


@pytest.mark.parametrize(
    "fault",
    [
        "index",
        "callbacks",
        "prediction_bits",
        "residual",
        "loss",
        "tree",
        "rng",
        "extra_field",
        "nonfinite",
        "timing_field",
    ],
)
def test_pairs_fail_on_any_unplanned_export_change(fault):
    before, after = pair_fixture(), pair_fixture()
    if fault == "index":
        after["selected_index"] = True
    elif fault == "callbacks":
        after["callback_calls_during_fit"] += 1
    elif fault == "prediction_bits":
        after["candidates"][0]["prediction"][0] = -0.0
    elif fault in {"residual", "loss", "tree"}:
        if fault == "residual":
            after["candidates"][0]["residual"][0] += 1e-15
        elif fault == "loss":
            after["candidates"][0]["loss"] += 1e-15
        else:
            after["candidates"][0]["tree"] = constant(1)
    elif fault == "rng":
        after["rng"]["python_seed"] += 1
    elif fault == "extra_field":
        after["unapproved"] = True
    elif fault == "nonfinite":
        before["candidates"][0]["loss"] = after["candidates"][0]["loss"] = math.nan
    else:
        after["timing_seconds"]["unknown"] = 1
    with pytest.raises(ValueError):
        control.compare_pair(before, after)


def test_pair_allows_only_validated_timing_values_to_change():
    before, after = pair_fixture(), pair_fixture()
    after["timing_seconds"]["worker_setup"] = 50.0
    assert control.compare_pair(before, after)["status"] == "passed"
