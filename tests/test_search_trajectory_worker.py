"""Protect post-fit unit export and the options-only PySR boundary."""

import importlib.util
import json
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
