"""Counterexamples for frozen restart scope, selection and publication boundaries."""

import copy
import random
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import global_restarts as restarts
from ringdown_sr.signals import ringdown_signal


def test_frozen_twenty_calls_share_reference_without_reusing_history():
    cells = restarts.bridge.cells()
    assert len(cells) == 20
    seeds = []
    for block, first in enumerate((20261201, 20261210, 20261211, 20261212), 1):
        group = [c for c in cells if c["block"] == block]
        assert [c["niterations"] for c in group] == [500, 2000, 500, 500, 500]
        assert [c["member"] for c in group] == [0, None, 1, 2, 3]
        assert group[0]["seed"] == group[1]["seed"] == first
        seeds += [c["seed"] for c in group if c["member"] is not None]
    assert len(set(seeds)) == 16
    assert [c["number"] for c in cells] == list(range(1, 21))


def test_grid_is_independent_stratified_reproducible_and_breaks_lattice_alias():
    python_state, numpy_state = random.getstate(), np.random.get_state()
    points = restarts.grid()
    assert random.getstate() == python_state
    after = np.random.get_state()
    assert after[0] == numpy_state[0]
    np.testing.assert_array_equal(after[1], numpy_state[1])
    assert after[2:] == numpy_state[2:]
    np.testing.assert_array_equal(points["time_s"], restarts.grid()["time_s"])
    assert np.all(np.diff(points["time_s"]) > 0)
    stratum = points["time_s"] / (127 / 4096) * 1024
    assert np.all(np.floor(stratum) == np.arange(1024))
    assert np.all(points["time_s"] * 32768 != np.floor(points["time_s"] * 32768))
    regular = np.arange(1017) / 32768

    def signal(times, frequency):
        return ringdown_signal(
            times, amplitude=1, frequency_hz=frequency, decay_time_s=0.008
        )

    # Independent analytic alias: adding one sampling frequency changes phase
    # by an integer multiple of 2*pi on every old point, but not these points.
    np.testing.assert_allclose(signal(regular, 250), signal(regular, 33018), atol=3e-13)
    assert (
        np.sqrt(np.mean((points["truth"] - signal(points["time_s"], 33018)) ** 2)) > 0.1
    )


def member(loss, complexity=3, **extra):
    return {
        "status": "completed",
        "selected": {"loss": loss, "complexity": complexity},
        **extra,
    }


def test_package_selection_uses_only_native_loss_complexity_then_position():
    members = [
        member(2, 1, truth="perfect"),
        member(1, 4, grade="A"),
        member(1, 3, grade="D"),
        member(1, 3, grade="A"),
    ]
    before = copy.deepcopy(members)
    assert restarts.package_selection(members) == 2
    assert members == before
    members[0].update(status="worker_failed")
    members[2]["selected"]["loss"] = float("nan")
    members[3]["selected"]["loss"] = float("inf")
    assert restarts.package_selection(members) == 1
    members[1]["status"] = "worker_failed"
    assert restarts.package_selection(members) is None


def fixture_cells():
    result = []
    for plan in restarts.bridge.cells():
        is_a = plan["member"] is None or plan["member"] == 2
        record = {
            "supplemental": {
                "curve": {"grade": "A" if is_a else "D"},
                "original_family": {"status": "unresolved"},
            }
        }
        result.append(
            {
                "plan": plan,
                **member(1 if plan["member"] == 2 else 2),
                "selected_assessment": record,
                "costs": {
                    "worker_wall_seconds": 10.0,
                    "callback_calls_during_fit": 100,
                    "adapter_call_wall_seconds": 12.0,
                },
            }
        )
    return result


def test_comparison_counts_shared_reference_once_physically_and_all_failed_members():
    cells = fixture_cells()
    cells[3]["status"] = "worker_failed"
    cells[3]["costs"]["callback_calls_during_fit"] = None
    result = restarts.comparison(cells)
    assert all(v["planned"] == 4 for v in result["totals"].values())
    assert result["totals"]["reference"]["A"] == 0
    assert result["totals"]["long"]["A"] == 4
    assert result["totals"]["restarts"]["A"] == 3
    assert result["totals"]["restarts"]["costs"]["callback_calls_during_fit"] is None
    assert result["totals"]["restarts"]["costs"]["worker_wall_seconds"] == 160
    assert restarts.costs(cells)["worker_wall_seconds"] == 200
    assert result["preferred_development_arm"] == "long"
    assert (
        result["next_step"] == "consider_profile_adoption_then_independent_confirmation"
    )
    assert result["blocks"][0]["outputs"]["restarts"]["failed_members"] == 1
    assert len(result["contrasts"]) == 3
    assert all(len(c["pairs"]) == 4 for c in result["contrasts"].values())


def test_tied_improvements_do_not_hide_unknown_cost_or_tie_on_adapter_overhead():
    cells = fixture_cells()
    # Make logical arm costs tie exactly, including different adapter overhead.
    for cell in cells:
        if cell["plan"]["member"] is None:
            cell["costs"].update(
                worker_wall_seconds=40.0,
                callback_calls_during_fit=400,
                adapter_call_wall_seconds=99.0,
            )
    assert restarts.comparison(cells)["preferred_development_arm"] is None
    cells[1]["costs"]["callback_calls_during_fit"] = None
    assert restarts.comparison(cells)["preferred_development_arm"] is None
    cells[1]["status"] = "planned"
    with pytest.raises(ValueError, match="planned calls"):
        restarts.comparison(cells)


def test_bridge_command_loads_new_adapter_and_stops_group_on_cancellation(
    monkeypatch, tmp_path
):
    captured = {}

    class Child:
        def __init__(self, command, **kwargs):
            captured.update(command=command, **kwargs)

        def wait(self, **kwargs):
            raise KeyboardInterrupt

    monkeypatch.setattr(restarts.subprocess, "Popen", Child)
    monkeypatch.setattr(
        restarts, "_stop_worker", lambda child: captured.update(stopped=True)
    )
    consumed = publication.Consumption(publication.Deadline(10))
    with pytest.raises(KeyboardInterrupt):
        restarts.call_bridge(
            tmp_path,
            "verify",
            tmp_path,
            tmp_path / "request",
            tmp_path / "inputs",
            consumed,
            tmp_path / "log",
            tmp_path / "verified",
        )
    assert captured["command"][4] == str(restarts.ROOT / restarts.BRIDGE)
    assert "--kind" not in captured["command"]
    assert captured["command"][captured["command"].index("--action") + 1] == "verify"
    assert captured["start_new_session"] and captured["stopped"]


@pytest.mark.parametrize(
    "where", ["before_first_search", "after_lock_removal", "cleanup"]
)
def test_run_transaction_revokes_changed_sources_and_late_interruptions(
    monkeypatch, tmp_path, where
):
    output = tmp_path / "run"
    watched = tmp_path / "bound-source"
    watched.write_text("original")
    events = []

    def freeze(consumed):
        consumed.add(watched, watched.read_bytes())
        return {"software_commit": "fixture", "source_sha256": {}}

    @contextmanager
    def checkout(parent):
        yield tmp_path
        if where == "cleanup":
            raise InterruptedError("cleanup interrupted")

    def call(
        checkout, action, destination, request, inputs, consumed, log, verification=None
    ):
        if action == "prepare":
            destination.mkdir()
            restarts._write_json(
                destination / "options.json", {"initial": {"environment": {}}}
            )
        else:
            events.append("search")
            restarts._write_json(
                destination / "outcome.json", {"status": "worker_failed"}
            )
        if where == "before_first_search" and action == "prepare":
            watched.write_text("changed")
        consumed.check()
        return 1.0

    monkeypatch.setattr(restarts, "freeze_software", freeze)
    monkeypatch.setattr(restarts, "historical_checkout", checkout)
    monkeypatch.setattr(restarts, "call_bridge", call)
    monkeypatch.setattr(restarts.cross, "environment_key", lambda e: e)
    monkeypatch.setattr(restarts.cross, "scientific_platform", lambda: None)
    monkeypatch.setattr(restarts, "assemble", lambda *args: [])
    monkeypatch.setattr(restarts, "comparison", lambda *args: {})
    monkeypatch.setattr(restarts, "summary", lambda *args: "fixture")
    original_unlink = Path.unlink

    def unlink(path, *args, **kwargs):
        original_unlink(path, *args, **kwargs)
        if where == "after_lock_removal" and path.name == publication.LOCK:
            raise KeyboardInterrupt

    monkeypatch.setattr(Path, "unlink", unlink)
    with pytest.raises((ValueError, InterruptedError, KeyboardInterrupt)):
        restarts.run(output)
    completion = output / "completion"
    assert (completion / publication.LOCK).exists()
    if (completion / publication.REPORT).exists():
        assert (
            restarts.sources.read_json((completion / publication.REPORT).read_bytes())[
                "status"
            ]
            != "completed"
        )
    assert not (completion / publication.MANIFEST).exists()
    assert len(events) == (0 if where == "before_first_search" else 20)
    state = restarts.sources.read_json((output / "run_state.json").read_bytes())
    assert len(state["cells"]) == 20 and state["status"] == "aborted"


def test_scientific_run_platform_guard_precedes_output_creation(monkeypatch, tmp_path):
    def reject():
        raise ValueError("Manjaro required")

    monkeypatch.setattr(restarts.cross, "scientific_platform", reject)
    with pytest.raises(ValueError, match="Manjaro"):
        restarts.run(tmp_path / "science")
    assert not (tmp_path / "science").exists()


def test_ci_adds_only_the_tiny_control_and_preserves_runtime_plan_coverage():
    workflow = (restarts.ROOT / ".github/workflows/technical-checks.yml").read_text()
    step = workflow.split(
        "- name: Verify restart comparison on three tiny technical workers\n"
    )[1].split("\n  technical-checks:")[0]
    assert "scripts/check_global_restarts.py" in step
    assert "scripts/run_global_restarts.py" not in step
    assert "exit 1" in step and "OPENBLAS_CORETYPE=Haswell" in step
    script = (restarts.ROOT / "scripts/check_global_restarts.py").read_text()
    assert "technical=True" in script and "verify(" in script
