"""Protect post-fit unit export and the options-only PySR boundary."""

import importlib.util
import json
import struct
import sys
from types import ModuleType, SimpleNamespace

import pytest

from ringdown_sr.pilot import _sha256
from ringdown_sr.search_trajectory import (
    MAX_OBSERVATION_BYTES,
    OBSERVED_PLUGINS,
    ROOT,
    TrajectoryPluginDescriptor,
)
from ringdown_sr.symbolic import SearchBudget


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


WORKER = load(
    "trajectory_worker_tests", ROOT / "scripts/run_search_trajectory_worker.py"
)
PREFLIGHT = load(
    "trajectory_preflight_tests", ROOT / "scripts/check_search_trajectory_backend.py"
)


def test_live_profile_preserves_original_plugin_order_and_appends_observer():
    parameters = WORKER.live_parameters(SearchBudget(seed=20261020), True)
    assert parameters["plugins"] == list(OBSERVED_PLUGINS)
    assert all(
        type(value) is TrajectoryPluginDescriptor for value in parameters["plugins"]
    )
    assert len(parameters["plugins"]) == 4
    assert json.loads(json.dumps(parameters))["plugins"] == list(OBSERVED_PLUGINS)
    assert WORKER.live_parameters(SearchBudget(seed=20261020), False)["plugins"] is None


@pytest.mark.parametrize(
    "plugins",
    [
        list(reversed(OBSERVED_PLUGINS)),
        list(OBSERVED_PLUGINS[1:]),
        [*OBSERVED_PLUGINS, OBSERVED_PLUGINS[-1]],
    ],
)
def test_live_profile_rejects_reordered_missing_and_duplicate_plugins(
    monkeypatch, plugins
):
    monkeypatch.setattr(
        WORKER, "profile_parameters", lambda *args: {"plugins": plugins}
    )
    with pytest.raises(ValueError, match="Unexpected trajectory plugin request"):
        WORKER.live_parameters(SearchBudget(seed=20261020), True)


@pytest.fixture
def unit_export(tmp_path):
    tree = {"kind": "constant", "value_bits": "3ff0000000000000"}
    member = {
        "tree": tree,
        "loss_bits": "0000000000000000",
        "cost_bits": "0000000000000000",
        "complexity_cache": 1,
        "birth": 1,
        "ref": 1,
        "parent": 0,
    }
    event = {
        "format": "ringdown-sr-search-trajectory-event-1",
        "event_index": 1,
        "returned_population": [member] * 32,
        "hall_of_fame": [{"slot": 1, "member": member}],
    }
    raw = (json.dumps(event, separators=(",", ":")) + "\n").encode()
    path = tmp_path / "observations.jsonl"
    path.write_bytes(raw)
    calls = {(): 7}
    classified = []

    def status(root, options):
        classified.append(root)
        return SimpleNamespace(status="valid", reason=None)

    jl = SimpleNamespace(
        RingdownSRSearch=SimpleNamespace(CALLS=calls, constant=lambda x: x),
        SearchTrajectory=SimpleNamespace(units_status=status),
    )
    record = {
        "status": "completed",
        "event_count": 1,
        "member_count": 33,
        "bytes_written": len(raw),
        "expected_events": 1,
        "max_bytes": MAX_OBSERVATION_BYTES,
    }
    return SimpleNamespace(
        directory=tmp_path,
        raw=raw,
        path=path,
        calls=calls,
        classified=classified,
        jl=jl,
        record=record,
    )


def test_unit_export_deduplicates_and_binds_consumed_bytes(unit_export):
    state = unit_export
    result = WORKER.export_units(state.directory, state.jl, None, state.record)
    units = (state.directory / "observation_units.json").read_bytes()
    document = json.loads(units)
    assert state.classified == [1.0]
    assert len(document["trees"]) == 1
    assert next(iter(document["trees"].values())) == {"status": "valid", "reason": None}
    assert result["raw_sha256"] == _sha256(state.raw)
    assert result["units_sha256"] == _sha256(units)
    assert result["total_bytes"] == len(state.raw) + len(units)
    assert state.calls[()] == 7


def test_combined_byte_cap_rejects_units_without_truncating_raw(unit_export):
    state = unit_export
    state.record["max_bytes"] = len(state.raw) + 1
    with pytest.raises(ValueError, match="Combined observation"):
        WORKER.export_units(state.directory, state.jl, None, state.record)
    assert state.path.read_bytes() == state.raw
    assert not (state.directory / "observation_units.json").exists()


def test_modified_raw_stream_cannot_be_blessed_after_units(unit_export):
    state = unit_export

    def alter(root, options):
        state.path.write_bytes(b"X" + state.raw[1:])
        return SimpleNamespace(status="valid", reason=None)

    state.jl.SearchTrajectory.units_status = alter
    with pytest.raises(ValueError, match="changed during unit"):
        WORKER.export_units(state.directory, state.jl, None, state.record)
    assert not (state.directory / "observation_units.json").exists()


def test_unit_classifier_cannot_consume_numeric_callbacks(unit_export):
    state = unit_export

    def alter(root, options):
        state.calls[()] += 1
        return SimpleNamespace(status="valid", reason=None)

    state.jl.SearchTrajectory.units_status = alter
    with pytest.raises(ValueError, match="numeric callback"):
        WORKER.export_units(state.directory, state.jl, None, state.record)
    assert not (state.directory / "observation_units.json").exists()


def test_disabled_observer_refuses_observation_files(unit_export):
    state = unit_export
    with pytest.raises(ValueError, match="Disabled observer"):
        WORKER.export_units(state.directory, state.jl, None, {"status": "disabled"})


@pytest.fixture
def replay_export(unit_export):
    state = unit_export
    state.observation = WORKER.export_units(
        state.directory, state.jl, None, state.record
    )
    state.inputs = b"immutable original training bytes"
    (state.directory / "inputs.npz").write_bytes(state.inputs)
    state.input_hash = _sha256(state.inputs)
    state.replayed = []
    state.guards = []

    def replay(root, options):
        state.replayed.append(root)
        return SimpleNamespace(
            status="available",
            reason=None,
            loss_bits="0000000000000000",
            prediction_bits=[struct.pack(">d", root).hex()] * 8,
        )

    state.jl.SearchTrajectory.training_replay = replay
    state.jl.SearchTrajectory.raw_tree = lambda root, options: SimpleNamespace(
        kind="constant", value_bits=struct.pack(">d", root).hex()
    )
    state.jl.SearchTrajectory.begin_replay_guard = lambda options: state.calls[()]
    state.jl.SearchTrajectory.verify_replay_guard = lambda guard, options: (
        state.guards.append(guard)
    )
    return state


def export_replay(state):
    return WORKER.export_replays(
        state.directory,
        state.jl,
        None,
        state.observation,
        expected_inputs_sha256=state.input_hash,
    )


def test_native_export_deduplicates_and_binds_all_consumed_files(replay_export):
    state = replay_export
    result = export_replay(state)
    payload = (state.directory / "observation_replays.json").read_bytes()
    document = json.loads(payload)
    assert document["format"] == "ringdown-sr-search-trajectory-replays-1"
    assert document["inputs_sha256"] == state.input_hash
    assert document["raw_sha256"] == state.observation["raw_sha256"]
    assert document["units_sha256"] == state.observation["units_sha256"]
    assert len(document["trees"]) == 1
    assert state.replayed == [1.0]
    assert state.guards == [7]
    assert result["replay_sha256"] == _sha256(payload)
    assert result["replay_bytes"] == len(payload)
    assert result["total_bytes"] == state.observation["total_bytes"] + len(payload)
    assert state.path.read_bytes() == state.raw


@pytest.mark.parametrize(
    "name", ["observations.jsonl", "observation_units.json", "inputs.npz"]
)
def test_native_export_rejects_files_changed_during_replay(replay_export, name):
    state = replay_export
    original = state.jl.SearchTrajectory.training_replay

    def altered(root, options):
        path = state.directory / name
        path.write_bytes(b"X" + path.read_bytes()[1:])
        return original(root, options)

    state.jl.SearchTrajectory.training_replay = altered
    with pytest.raises(ValueError, match="changed"):
        export_replay(state)
    assert not (state.directory / "observation_replays.json").exists()


def test_native_export_rejects_roundtrip_change_before_evaluation(replay_export):
    state = replay_export
    state.jl.SearchTrajectory.raw_tree = lambda root, options: SimpleNamespace(
        kind="constant", value_bits="8000000000000000"
    )
    with pytest.raises(ValueError, match="roundtrip"):
        export_replay(state)
    assert state.replayed == []
    assert not (state.directory / "observation_replays.json").exists()


def test_native_export_callback_violation_is_fatal(replay_export):
    state = replay_export
    original = state.jl.SearchTrajectory.training_replay

    def altered(root, options):
        state.calls[()] += 1
        return original(root, options)

    state.jl.SearchTrajectory.training_replay = altered
    with pytest.raises(ValueError, match="numeric callback"):
        export_replay(state)
    assert not (state.directory / "observation_replays.json").exists()


def test_native_export_state_guard_failure_is_fatal(replay_export):
    state = replay_export

    def reject(guard, options):
        raise RuntimeError("Native replay changed the RNG.")

    state.jl.SearchTrajectory.verify_replay_guard = reject
    with pytest.raises(RuntimeError, match="RNG"):
        export_replay(state)
    assert not (state.directory / "observation_replays.json").exists()


def test_native_export_combined_cap_rejects_without_truncating_sources(replay_export):
    state = replay_export
    originals = {
        name: (state.directory / name).read_bytes()
        for name in ("observations.jsonl", "observation_units.json", "inputs.npz")
    }
    state.observation["max_bytes"] = state.observation["total_bytes"] + 1
    with pytest.raises(ValueError, match="byte limit"):
        export_replay(state)
    assert not (state.directory / "observation_replays.json").exists()
    assert all(
        (state.directory / name).read_bytes() == payload
        for name, payload in originals.items()
    )


def test_native_export_never_overwrites_existing_replay(replay_export):
    state = replay_export
    path = state.directory / "observation_replays.json"
    path.write_bytes(b"existing evidence")
    with pytest.raises(FileExistsError):
        export_replay(state)
    assert path.read_bytes() == b"existing evidence"


@pytest.mark.parametrize(
    "reason", ["dimensional_violation", "nonfinite_constant", "numerical_unresolved"]
)
def test_native_unavailable_status_preserves_reason_and_null_values(reason):
    assert WORKER.native_replay_record(
        SimpleNamespace(
            status="not_assessed",
            reason=reason,
            loss_bits=None,
            prediction_bits=None,
        )
    ) == {
        "status": "not_assessed",
        "reason": reason,
        "loss_bits": None,
        "prediction_bits": None,
    }


@pytest.mark.parametrize(
    "loss_bits,prediction_bits",
    [
        ("7ff0000000000000", ["0000000000000000"]),
        ("bff0000000000000", ["0000000000000000"]),
        ("0000000000000000", ["7ff8000000000000"]),
        ("0000000000000000", []),
    ],
)
def test_native_available_records_reject_invalid_values(loss_bits, prediction_bits):
    with pytest.raises(ValueError, match="must be finite"):
        WORKER.native_replay_record(
            SimpleNamespace(
                status="available",
                reason=None,
                loss_bits=loss_bits,
                prediction_bits=prediction_bits,
            )
        )


def test_disabled_native_export_has_zero_bytes_and_no_artifact(tmp_path):
    result = WORKER.export_replays(
        tmp_path,
        None,
        None,
        {"status": "disabled", "total_bytes": 0},
        expected_inputs_sha256="unused",
    )
    assert result == {"status": "disabled", "total_bytes": 0, "replay_bytes": 0}
    assert list(tmp_path.iterdir()) == []
    (tmp_path / "observation_replays.json").write_bytes(b"unexpected")
    with pytest.raises(ValueError, match="Disabled observer"):
        WORKER.export_replays(
            tmp_path,
            None,
            None,
            {"status": "disabled"},
            expected_inputs_sha256="unused",
        )


def test_options_boundary_builds_native_options_but_never_searches(monkeypatch):
    calls = []
    native = SimpleNamespace(Options=lambda **kwargs: calls.append(kwargs) or kwargs)
    sr = SimpleNamespace(SymbolicRegression=native)
    fake = ModuleType("pysr")
    fake.sr = sr

    class Model:
        def __init__(self, **kwargs):
            self.complexity_of_variables = 1

        def _validate_and_modify_params(self):
            return {"validated": True}

        def _run(self, *args):
            sr.SymbolicRegression.Options(seed=args[4], plugin="observer")
            raise AssertionError("The options boundary did not stop the path.")

    fake.PySRRegressor = Model
    monkeypatch.setitem(sys.modules, "pysr", fake)
    worker = SimpleNamespace(live_parameters=lambda budget, observed: {})
    result = PREFLIGHT.actual_pysr_options(worker, 20261020, True)
    assert calls == [result]
    assert result["plugin"] == "observer"
    assert sr.SymbolicRegression is native


def test_options_boundary_restores_pysr_global_after_early_failure(monkeypatch):
    native = SimpleNamespace()
    sr = SimpleNamespace(SymbolicRegression=native)
    fake = ModuleType("pysr")
    fake.sr = sr

    class Model:
        def __init__(self, **kwargs):
            self.complexity_of_variables = 1

        def _validate_and_modify_params(self):
            return {}

        def _run(self, *args):
            raise RuntimeError("before options")

    fake.PySRRegressor = Model
    monkeypatch.setitem(sys.modules, "pysr", fake)
    worker = SimpleNamespace(live_parameters=lambda budget, observed: {})
    with pytest.raises(RuntimeError, match="before options"):
        PREFLIGHT.actual_pysr_options(worker, 20261020, False)
    assert sr.SymbolicRegression is native
