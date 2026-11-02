"""Failure injection for bounded trajectory orchestration, without any search."""

import copy
import importlib.util
import json
import signal
import sys
import time
from types import SimpleNamespace

import pytest
from test_free_optimizer_budget import option_fixture as budget_options
from test_noiseless_control import DRIVER as OLD
from test_noiseless_control import (
    fake_runtime,  # noqa: F401 -- Register the existing isolated fake worker.
    pools_environment,
)
from test_search_trajectory import member, write_replays
from test_structure import constant

from ringdown_sr import search_trajectory as policy
from ringdown_sr import symbolic
from ringdown_sr.losses import mean_squared_error
from ringdown_sr.noiseless_control import frozen_data
from ringdown_sr.pilot import _json_bytes, _sha256, _write_json

SPEC = importlib.util.spec_from_file_location(
    "trajectory_driver_tests", policy.ROOT / "scripts/run_search_trajectory.py"
)
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)
VERIFY_OBSERVATIONS = policy.verify_observations


def option_fixture(seed, observed):
    record = budget_options(seed, 100)
    record["observed"] = observed
    record["baseline_plugins"] = copy.deepcopy(record["plugins"])
    record["baseline_plugins_field"] = copy.deepcopy(record["plugins_field"])
    if observed:
        name = "Main.SearchTrajectory.SearchTrajectoryObserver"
        record["plugins"].append({"type": name, "fields": []})
        record["plugins_field"] = {
            "type": record["plugins_field"]["type"][:-1] + "," + name + "}",
            "value": record["plugins_field"]["value"][:-1] + "," + name + "())",
        }
    record["expected_plugins_field"] = copy.deepcopy(record["plugins_field"])
    for field in record["backend_options"]:
        if field["name"] == "loss_function":
            field.update(type=f"typeof({policy.OBJECTIVE})", value=policy.OBJECTIVE)
        elif field["name"] == "plugins":
            field.update(record["plugins_field"])
    return record


def fake_clock():
    return SimpleNamespace(
        started=time.monotonic(),
        remaining=lambda: 3600,
        check=lambda: None,
        cancel=lambda: None,
    )


@pytest.fixture
def runtime(request, monkeypatch, tmp_path):
    state = request.getfixturevalue("fake_runtime")
    monkeypatch.setattr(DRIVER, "BASE", OLD)
    # Signal mechanics themselves stay covered by the existing Linux tests.
    # This fixture permits pure failure-publication tests on Windows as well.
    if not hasattr(signal, "pthread_sigmask"):
        monkeypatch.setattr(signal, "pthread_sigmask", lambda *_: set(), raising=False)
        monkeypatch.setattr(signal, "SIG_BLOCK", 0, raising=False)
        monkeypatch.setattr(signal, "SIG_SETMASK", 1, raising=False)
    state.archive = tmp_path / "representation.tar.gz"
    state.archive.write_bytes(b"non-executed original archive fixture")
    arrays = frozen_data()
    monkeypatch.setattr(
        DRIVER,
        "read_archive",
        lambda archive: (b"non-executed original archive fixture", arrays),
    )
    state.alter = None
    state.preflight_alter = None
    state.observation_failure = None
    state.unresolved_members = 0
    state.unassessed_members = 0
    state.after_observation = None

    def preflight(output, runtime, initial, sources, support, probe, remaining):
        snapshot = copy.deepcopy(initial)
        snapshot["environment"] = pools_environment(True)
        snapshot["blas_control"] = probe.verify_blas_control(
            snapshot["environment"], "Haswell", require_julia=True
        )
        record = {
            "format": policy.FORMAT,
            "status": "verified",
            "mode": "options",
            "callback_calls": 0,
            "initial": snapshot,
            "final": snapshot,
            "source_sha256": sources,
            "profiles": [
                option_fixture(c["budget"]["seed"], c["observed"])
                for c in policy.planned_cells()
            ],
        }
        if state.preflight_alter:
            state.preflight_alter(record)
        DRIVER.verify_preflight(record, initial, sources, support, probe)
        _write_json(output / "options.json", record)
        return record, {"options.json": (output / "options.json").read_bytes()}

    monkeypatch.setattr(DRIVER, "inspect_backend", preflight)

    def observation(
        path,
        *,
        expected_events,
        arrays,
        front,
        check,
        expected_sha256,
        expected_record,
        expected_units_sha256,
        expected_replay_sha256,
        expected_inputs_sha256,
    ):
        check()
        if state.observation_failure:
            raise ValueError(state.observation_failure)
        assert expected_events == 400
        assert _sha256(path.read_bytes()) == expected_sha256
        assert (
            _sha256(path.with_name("observation_units.json").read_bytes())
            == expected_units_sha256
        )
        assert (
            _sha256(path.with_name("observation_replays.json").read_bytes())
            == expected_replay_sha256
        )
        assert (
            _sha256(path.with_name("inputs.npz").read_bytes()) == expected_inputs_sha256
        )
        if state.after_observation:
            state.after_observation(path.parent)
        return {
            "observation": copy.deepcopy(expected_record),
            "counts": {
                "returned_population": 12800,
                "hall_of_fame": 0,
                "verified": 12800 - state.unresolved_members - state.unassessed_members,
                "numerical_unresolved": state.unresolved_members,
                "not_assessed": state.unassessed_members,
            },
            "trees": [],
            "fixture": "parser separately tested",
        }

    monkeypatch.setattr(policy, "verify_observations", observation)

    def enrich(number, directory, docs):
        cell = policy.planned_cells()[number - 1]
        sources = policy.source_hashes()
        native = option_fixture(cell["budget"]["seed"], cell["observed"])
        docs["pysr_parameters.json"] = {
            **policy.profile_parameters(
                symbolic.SearchBudget(**cell["budget"]), cell["observed"]
            ),
            "output_directory": str(directory / "pysr"),
        }
        docs["backend_options.json"] = copy.deepcopy(native["backend_options"])
        docs["profile.json"] = {
            "format": policy.PROFILE_FORMAT,
            "observed": cell["observed"],
        }
        docs["manifest.json"] = {
            "format": policy.FORMAT,
            "sources": sources,
            "runtime": {k: sources[v] for k, v in policy.RUNTIME.items()},
            "inputs": {
                "request.json": _sha256(_json_bytes(docs["request.json"])),
                "profile.json": _sha256(_json_bytes(docs["profile.json"])),
                "inputs.npz": _sha256((directory / "inputs.npz").read_bytes()),
            },
        }
        for name in DRIVER.EXTRA_FILES:
            if name.endswith(".jl"):
                (directory / name).write_bytes(
                    (policy.ROOT / "julia/src" / name).read_bytes()
                )
        docs["result.json"]["callback_calls_during_fit"] = 10
        docs["result.json"]["timing_seconds"] = {
            "worker_setup": 0.0,
            "fit_including_jit_and_python_exports": float(number),
        }
        raw = b"Observation parser fixture; not native event data.\n"
        units = b"Unit parser fixture; not a native status.\n"
        replay = b"Replay parser fixture; not native replay data.\n"
        if cell["observed"]:
            (directory / "observations.jsonl").write_bytes(raw)
            (directory / "observation_units.json").write_bytes(units)
            (directory / "observation_replays.json").write_bytes(replay)
        observation_record = {
            "status": "completed" if cell["observed"] else "disabled",
            "event_count": 400 if cell["observed"] else 0,
            "member_count": 12800 if cell["observed"] else 0,
            "bytes_written": len(raw) if cell["observed"] else 0,
            "units_bytes": len(units) if cell["observed"] else 0,
            "replay_bytes": len(replay) if cell["observed"] else 0,
            "total_bytes": len(raw) + len(units) + len(replay)
            if cell["observed"]
            else 0,
            "max_bytes": policy.MAX_OBSERVATION_BYTES,
            "expected_events": 400,
        }
        if cell["observed"]:
            observation_record.update(
                raw_sha256=_sha256(raw),
                units_sha256=_sha256(units),
                replay_sha256=_sha256(replay),
            )
        docs["verification.json"] = {
            **native,
            "format": policy.FORMAT,
            "status": "verified",
            "callback_calls_during_fit": 10,
            "callback_calls_total": 11,
            "profile_sha256": _sha256(_json_bytes(docs["profile.json"])),
            "manifest_sha256": _sha256(_json_bytes(docs["manifest.json"])),
            "observation": observation_record,
            "observation_timing_seconds": {
                "hook": 0.0,
                "units_after_fit": 0.0,
                "replay_after_fit": 0.0,
            },
        }
        if state.alter:
            state.alter(number, directory, docs)

    state.hook = enrich
    state.run = lambda output: DRIVER.run_with_deadline(
        state.archive, output, label="fixture", clock=fake_clock()
    )
    return state


def locked(output):
    report = json.loads((output / "report.json").read_bytes())
    assert report["status"] == "incomplete"
    assert report["final_verification"] == "failed"
    assert report["comparative_interpretation"] is None
    assert not (output / "checksums.json").exists()
    assert not (output / "report.json.tmp").exists()
    assert "Vergleichende Interpretation: gesperrt." in (
        output / "summary.md"
    ).read_text(encoding="utf-8")
    return report


def test_six_cells_preserve_fronts_pairs_and_publish_only_at_end(runtime, tmp_path):
    output = tmp_path / "complete"
    report = runtime.run(output)
    assert len(runtime.calls) == 6
    assert [c["observed"] for c in report["cells"]] == [
        False,
        True,
        True,
        False,
        False,
        True,
    ]
    assert len(report["pairs"]) == 3
    assert report["comparative_interpretation"]["status"] == "available"
    assert report["comparative_interpretation"]["member_assessment_complete"] is True
    assert [c["diagnostics"]["selected_index"] for c in report["cells"]] == [0] * 6
    assert [c["diagnostics"]["candidate_count"] for c in report["cells"]] == [2] * 6
    assert [
        c["diagnostics"]["observation"]["event_count"] for c in report["cells"]
    ] == [0, 400, 400, 0, 0, 400]
    assert report["historical_comparison"]["status"] == "not_assessed"
    assert report["replay_policy"] == {
        "path": policy.REPLAY_POLICY,
        "sha256": policy.REPLAY_POLICY_SHA256,
    }
    assert (output / "replay_policy.md").read_bytes() == (
        policy.ROOT / policy.REPLAY_POLICY
    ).read_bytes()
    assert report["comparative_interpretation"]["observation_member_counts"] == {
        "returned_population": 38400,
        "hall_of_fame": 0,
        "verified": 38400,
        "numerical_unresolved": 0,
        "not_assessed": 0,
    }
    for name, digest in json.loads((output / "checksums.json").read_bytes()).items():
        assert _sha256((output / name).read_bytes()) == digest


def test_completed_series_keeps_unresolved_members_explicit(runtime, tmp_path):
    runtime.unresolved_members = 2
    runtime.unassessed_members = 3
    output = tmp_path / "bounded_assessment"
    report = runtime.run(output)
    assert len(runtime.calls) == 6
    assert report["status"] == "completed"
    assert report["comparative_interpretation"]["member_assessment_complete"] is False
    counts = report["comparative_interpretation"]["observation_member_counts"]
    assert counts["numerical_unresolved"] == 6
    assert counts["not_assessed"] == 9
    assert counts["verified"] == 38385
    assert (
        "unresolved and unassessed members excluded"
        in report["comparative_interpretation"]["scope"]
    )
    text = (output / "summary.md").read_text(encoding="utf-8")
    assert "Numerisch offen" in text
    assert "Nicht bewertet" in text
    assert "12800 | 12795 | 2 | 3" in text
    assert "bleiben unbekannt und zählen nicht als Erfolge" in text


@pytest.mark.parametrize(
    "fault", ["missing", "control_file", "changed_after_consumption"]
)
def test_replay_artifacts_are_required_bound_and_rechecked(runtime, tmp_path, fault):
    def alter(number, directory, docs):
        if number == 1 and fault == "control_file":
            (directory / "observation_replays.json").write_bytes(b"forbidden")
        elif number == 2 and fault == "missing":
            (directory / "observation_replays.json").unlink()

    def change(directory):
        path = directory / "observation_replays.json"
        path.write_bytes(path.read_bytes() + b"late change")

    runtime.alter = alter
    if fault == "changed_after_consumption":
        runtime.after_observation = change
    output = tmp_path / "replay_failure"
    with pytest.raises(ValueError):
        runtime.run(output)
    report = locked(output)
    assert len(runtime.calls) == (1 if fault == "control_file" else 2)
    assert report["pairs"] == []


def test_invalid_member_denominators_block_completion(runtime, tmp_path):
    runtime.unresolved_members = 12801
    output = tmp_path / "bad_denominators"
    with pytest.raises(ValueError, match="observed-member denominators"):
        runtime.run(output)
    assert len(runtime.calls) == 2
    locked(output)


@pytest.mark.parametrize(
    "case", ["valid", "unresolved", "inconsistent_native_mse", "wrong_inputs_binding"]
)
def test_real_replay_parser_distinguishes_unresolved_from_fatal(
    runtime, monkeypatch, tmp_path, case
):
    """Exercise real parser handoff with independently controlled inert exports."""
    arrays = frozen_data()
    loss = mean_squared_error(arrays["observed"] - 1.0)
    original_member = member(constant(1.0), loss)
    # Keep inert parser fixtures small; this does not execute any search.
    planned = policy.planned_cells()
    for cell in planned:
        cell["budget"]["niterations"] = 1
    monkeypatch.setattr(policy, "planned_cells", lambda: copy.deepcopy(planned))

    def alter(number, directory, docs):
        record = docs["verification.json"]["observation"]
        record["expected_events"] = 2
        if not policy.planned_cells()[number - 1]["observed"]:
            return
        items = []
        for index in range(2):
            population = [copy.deepcopy(original_member) for _ in range(32)]
            if index == 0 and case == "unresolved":
                population[0]["loss_bits"] = policy._bits(2 * loss)
            items.append(
                {
                    "format": policy.EVENT_FORMAT,
                    "event_index": index + 1,
                    "returned_population": population,
                    "hall_of_fame": [],
                }
            )
        path = directory / "observations.jsonl"
        path.write_bytes(
            b"".join(
                json.dumps(item, sort_keys=True, allow_nan=False).encode() + b"\n"
                for item in items
            )
        )
        _write_json(
            directory / "observation_units.json",
            {
                "format": policy.UNITS_FORMAT,
                "trees": {
                    policy.raw_tree_id(original_member["tree"]): {
                        "status": "valid",
                        "reason": None,
                    }
                },
            },
        )
        replay = write_replays(path, arrays)
        if case == "inconsistent_native_mse":
            next(iter(replay["trees"].values()))["loss_bits"] = policy._bits(2 * loss)
        elif case == "wrong_inputs_binding":
            replay["inputs_sha256"] = "0" * 64
        _write_json(directory / "observation_replays.json", replay)
        record.update(event_count=2, member_count=64)
        for filename, size_key, hash_key in (
            ("observations.jsonl", "bytes_written", "raw_sha256"),
            ("observation_units.json", "units_bytes", "units_sha256"),
            ("observation_replays.json", "replay_bytes", "replay_sha256"),
        ):
            value = (directory / filename).read_bytes()
            record[size_key], record[hash_key] = len(value), _sha256(value)
        record["total_bytes"] = sum(
            record[key] for key in ("bytes_written", "units_bytes", "replay_bytes")
        )

    monkeypatch.setattr(policy, "verify_observations", VERIFY_OBSERVATIONS)
    runtime.alter = alter
    output = tmp_path / case
    if case in {"inconsistent_native_mse", "wrong_inputs_binding"}:
        with pytest.raises(ValueError):
            runtime.run(output)
        assert len(runtime.calls) == 2
        locked(output)
    else:
        report = runtime.run(output)
        assert report["final_verification"] == "passed"
        counts = report["comparative_interpretation"]["observation_member_counts"]
        unresolved = 3 if case == "unresolved" else 0
        assert counts["numerical_unresolved"] == unresolved
        assert counts["verified"] == 192 - unresolved
        assert counts["not_assessed"] == 0
        if unresolved:
            for cell in report["cells"]:
                if cell["observed"]:
                    analysis = cell["diagnostics"]["observation_analysis"]
                    assert (
                        analysis["occurrences"][0]["status"] == "numerical_unresolved"
                    )
                    assert (
                        analysis["occurrences"][0]["curve_marker"] != "within_tolerance"
                    )


@pytest.mark.parametrize(
    "fault",
    [
        "callback",
        "tree",
        "selection",
        "residual",
        "loss",
        "native_seed",
        "plugin",
        "profile",
        "unexpected_control_observations",
    ],
)
def test_consistently_rehashed_forgery_cannot_release_pair(runtime, tmp_path, fault):
    def alter(number, directory, docs):
        if number != 2:
            return
        front = docs["result.json"]
        if fault == "callback":
            front["callback_calls_during_fit"] += 1
            docs["verification.json"]["callback_calls_during_fit"] += 1
            docs["verification.json"]["callback_calls_total"] += 1
        elif fault == "tree":
            front["candidates"][0]["tree"]["value_hex"] = float(1).hex()
        elif fault == "selection":
            front["selected_index"] = 1
        elif fault in {"residual", "loss"}:
            if fault == "residual":
                front["candidates"][1]["residual"][0] += 0.25
            else:
                front["candidates"][1]["loss"] *= 0.5
        elif fault == "native_seed":
            docs["verification.json"]["backend_seed"] = front["rng"]["backend_seed"] = 7
        elif fault == "plugin":
            docs["verification.json"]["plugins"][0]["fields"][0]["value"] = "99.0"
        elif fault == "profile":
            docs["profile.json"]["truth"] = [250, 0.008]
        else:
            docs["verification.json"]["observed"] = False

    runtime.alter = alter
    output = tmp_path / fault
    with pytest.raises((ValueError, KeyError, AssertionError)):
        runtime.run(output)
    report = locked(output)
    assert len(runtime.calls) == 2
    assert report["pairs"] == []
    assert all(c["status"] == "planned" for c in report["cells"][2:])


def test_pair_checks_all_candidate_fields_not_only_original_selection(
    runtime, tmp_path
):
    def alter(number, directory, docs):
        if number == 2:
            docs["result.json"]["candidates"][1]["display_equation"] = (
                "changed nonselected display"
            )

    runtime.alter = alter
    output = tmp_path / "nonselected"
    with pytest.raises(ValueError, match="exported search results differ"):
        runtime.run(output)
    assert len(runtime.calls) == 2
    locked(output)


@pytest.mark.parametrize("fault", ["missing", "negative", "extra", "control_nonzero"])
def test_invalid_observation_effort_cannot_release_comparison(runtime, tmp_path, fault):
    def alter(number, directory, docs):
        if number != 1:
            return
        timing = docs["verification.json"]["observation_timing_seconds"]
        if fault == "missing":
            timing.pop("hook")
        elif fault == "negative":
            timing["hook"] = -1.0
        elif fault == "extra":
            timing["unaccounted"] = 1.0
        else:
            timing["units_after_fit"] = 1.0

    runtime.alter = alter
    output = tmp_path / "effort"
    with pytest.raises(ValueError, match="observation effort accounting"):
        runtime.run(output)
    report = locked(output)
    assert len(runtime.calls) == 1
    assert all(cell["status"] == "planned" for cell in report["cells"][1:])


@pytest.mark.parametrize(
    "reason",
    [
        "missing event",
        "duplicate event",
        "byte limit",
        "replay byte limit",
        "wrong replay input hash",
        "replay tree coverage",
        "inconsistent replay MSE",
    ],
)
def test_observation_verification_failure_stops_before_pair(runtime, tmp_path, reason):
    runtime.observation_failure = reason
    output = tmp_path / "observation"
    with pytest.raises(ValueError, match=reason):
        runtime.run(output)
    report = locked(output)
    assert len(runtime.calls) == 2
    assert report["cells"][1]["status"] == "failed"
    assert report["pairs"] == []


@pytest.mark.parametrize("fault", ["missing", "duplicate", "callback", "plugin"])
def test_bad_preflight_stops_before_any_search(runtime, tmp_path, fault):
    def alter(record):
        if fault == "missing":
            record["profiles"].pop()
        elif fault == "duplicate":
            record["profiles"][-1] = copy.deepcopy(record["profiles"][0])
        elif fault == "callback":
            record["callback_calls"] = 1
        else:
            record["profiles"][0]["plugins"][0]["fields"][0]["value"] = "9"

    runtime.preflight_alter = alter
    output = tmp_path / "preflight"
    with pytest.raises(ValueError):
        runtime.run(output)
    report = locked(output)
    assert not runtime.calls
    assert all(c["status"] == "planned" for c in report["cells"])


@pytest.mark.parametrize(
    "stage",
    [
        "after_publication",
        "stage_cleanup",
        "late_observation_mutation",
        "late_replay_mutation",
    ],
)
def test_publication_or_cleanup_failure_revokes_released_interpretation(
    runtime, monkeypatch, tmp_path, stage
):
    output = tmp_path / stage
    replace = type(output).replace
    cleanup = DRIVER.HELPERS.tempfile.TemporaryDirectory.__exit__
    injected = False

    def publish(path, target):
        nonlocal injected
        result = replace(path, target)
        if (
            stage == "after_publication"
            and target == output / "report.json"
            and not injected
            and json.loads(target.read_bytes())["final_verification"] == "passed"
        ):
            injected = True
            raise RuntimeError("after positive rename")
        if (
            stage in {"late_observation_mutation", "late_replay_mutation"}
            and target == output / "checksums.json"
            and not injected
        ):
            injected = True
            name = (
                "observation_replays.json"
                if stage == "late_replay_mutation"
                else "observations.jsonl"
            )
            raw = output / "cell-02" / name
            raw.write_bytes(raw.read_bytes() + b"changed")
            local = raw.parent / "checksums.json"
            values = json.loads(local.read_bytes())
            values[raw.name] = _sha256(raw.read_bytes())
            _write_json(local, values)
        return result

    def clean(*args):
        nonlocal injected
        result = cleanup(*args)
        if stage == "stage_cleanup" and not injected:
            injected = True
            raise RuntimeError("stage cleanup failed")
        return result

    monkeypatch.setattr(type(output), "replace", publish)
    monkeypatch.setattr(DRIVER.HELPERS.tempfile.TemporaryDirectory, "__exit__", clean)
    with pytest.raises((RuntimeError, ValueError)):
        runtime.run(output)
    assert injected
    assert len(runtime.calls) == 6
    locked(output)


def test_failed_first_revocation_does_not_leave_positive_package(
    runtime, monkeypatch, tmp_path
):
    output = tmp_path / "revoke"
    replace, unlink = type(output).replace, type(output).unlink
    published, interrupted = False, False

    def publish(path, target):
        nonlocal published
        result = replace(path, target)
        if (
            target == output / "report.json"
            and not published
            and json.loads(target.read_bytes())["final_verification"] == "passed"
        ):
            published = True
            raise RuntimeError("primary publication failure")
        return result

    def revoke(path, *args, **kwargs):
        nonlocal interrupted
        if published and path == output / "report.json" and not interrupted:
            interrupted = True
            raise KeyboardInterrupt("first revocation interrupted")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(type(output), "replace", publish)
    monkeypatch.setattr(type(output), "unlink", revoke)
    with pytest.raises(RuntimeError, match="primary publication failure"):
        runtime.run(output)
    assert published and interrupted
    locked(output)


def test_worker_dispatch_uses_minimum_of_remaining_and_per_worker_limit(
    runtime, monkeypatch, tmp_path
):
    cell = policy.planned_cells()[0]
    output = tmp_path / "dispatch"
    output.mkdir()
    directory = output / cell["directory"]
    directory.mkdir()
    sources = policy.source_hashes()
    native, _ = DRIVER.copy_runtime(output, sources)
    _write_json(
        directory / "request.json",
        {"format": symbolic.FORMAT, "budget": cell["budget"]},
    )
    (directory / "inputs.npz").write_bytes(b"dispatch-only not consumed arrays")
    captured = []
    monkeypatch.setattr(
        DRIVER, "launch", lambda *args, **kwargs: captured.append(kwargs["remaining"])
    )
    for remaining in (700, 17):
        dispatcher = DRIVER.dispatch(
            native,
            cell,
            sources,
            {},
            output,
            lambda value=remaining: value,
            lambda: None,
        )
        dispatcher(
            [
                sys.executable,
                str(policy.ROOT / "scripts/run_python.py"),
                str(policy.ROOT / "scripts/run_symbolic_worker.py"),
                str(directory),
            ],
            stdout=None,
        )
    assert captured == [600, 17]


def test_reused_output_and_source_overlap_rejected(runtime, tmp_path):
    output = tmp_path / "already"
    output.mkdir()
    for target in (output, policy.ROOT, runtime.archive.parent):
        with pytest.raises(ValueError):
            runtime.run(target)
    assert not runtime.calls


def test_scientific_command_requires_reference_linux_timer(monkeypatch):
    if hasattr(signal, "setitimer"):
        monkeypatch.delattr(signal, "setitimer")
    with pytest.raises(RuntimeError, match="Linux reference"):
        DRIVER.run("missing.tar.gz", "missing-output", label="fixture")
