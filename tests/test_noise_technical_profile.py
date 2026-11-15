"""Keep the ten-iteration probe distinct from historical and scientific members."""

from dataclasses import asdict

import numpy as np
import pytest

from ringdown_sr import confirmed_profile as profile
from ringdown_sr import symbolic
from ringdown_sr.pilot import _write_json


def request():
    return {
        "format": profile.NOISE_TECHNICAL_FORMAT,
        "profile": profile.PROFILE,
        "seed": 2026111413,
        "technical": True,
        "budget": asdict(symbolic.SearchBudget(seed=2026111413, niterations=10)),
    }


def prepare(tmp_path):
    directory = tmp_path / "member"
    profile.prepare_noise_technical_member(
        directory, [0.0, 1.0], [1.0, 0.0], seed=2026111413
    )
    return directory


def seal(directory):
    _write_json(directory / "member_checksums.json", profile._inventory(directory))


def failed_member(tmp_path):
    directory = prepare(tmp_path)
    metadata = profile.read(directory, "metadata_initial.json")
    metadata["phase"] = "worker_start"
    _write_json(directory / "metadata.json", metadata)
    _write_json(
        directory / "outcome.json",
        {
            "format": profile.NOISE_TECHNICAL_FORMAT,
            "status": "timeout",
            "returncode": -15,
            "timed_out": True,
            "worker_wall_seconds": 600.0,
            "adapter_call_wall_seconds": 600.0,
            "cpu_user_seconds": None,
            "cpu_system_seconds": None,
        },
    )
    seal(directory)
    return directory


def test_ten_iteration_probe_retains_all_scientific_profile_options():
    budget = profile.checked_request(request())
    actual = profile.parameters(budget)
    assert actual["niterations"] == 10
    assert actual["optimizer_iterations"] == 300
    assert actual["optimizer_nrestarts"] == 5
    assert actual["use_frequency"] is actual["use_frequency_in_tournament"] is True
    assert actual["should_simplify"] is False
    assert actual["warmup_maxsize_by"] == 0
    assert actual["loss_function"] == "Main.SearchTimeBudget.objective"
    assert actual["timeout_in_seconds"] is None


@pytest.mark.parametrize("iterations", [1, 9, 11, 1000, True, 10.0])
def test_probe_budget_cannot_be_changed_or_aliased(iterations):
    document = request()
    document["budget"]["niterations"] = iterations
    with pytest.raises(ValueError):
        profile.checked_request(document)


@pytest.mark.parametrize(
    "field,value",
    [
        ("format", profile.FORMAT),
        ("technical", False),
        ("technical", 1),
        ("seed", 0),
        ("seed", 2**31),
        ("profile", "unbound-probe"),
    ],
)
def test_probe_cannot_be_relabelled_as_a_historical_or_scientific_member(field, value):
    document = request()
    document[field] = value
    with pytest.raises(ValueError):
        profile.checked_request(document)


@pytest.mark.parametrize("technical,iterations", [(True, 1), (False, 1000)])
def test_historical_prepare_keeps_original_request_and_source_contract(
    tmp_path, technical, iterations
):
    directory = tmp_path / "legacy"
    profile.prepare_member(
        directory, [0.0, 1.0], [1.0, 0.0], seed=2026111413, technical=technical
    )
    document, _, manifest = profile.verify_prepared(directory)
    assert document["format"] == manifest["format"] == profile.FORMAT
    assert document["budget"]["niterations"] == iterations
    assert manifest["sources"] == profile.source_hashes()
    assert profile.NOISE_PLAN not in manifest["sources"]


def test_new_preparation_binds_its_plan_and_parent_format(tmp_path):
    directory = prepare(tmp_path)
    document, arrays, manifest = profile.verify_prepared(directory)
    assert document == request()
    assert arrays["time_s"].tolist() == [0.0, 1.0]
    assert manifest["format"] == profile.NOISE_TECHNICAL_FORMAT
    assert manifest["sources"][profile.NOISE_PLAN] == profile.NOISE_PLAN_SHA256
    initial = profile.read(directory, "metadata_initial.json")
    assert initial["format"] == profile.NOISE_TECHNICAL_FORMAT
    assert initial["adapter_source_sha256"] == manifest["sources"]


def test_changed_frozen_plan_cannot_be_bound(monkeypatch, tmp_path):
    monkeypatch.setattr(profile, "ROOT", tmp_path)
    path = tmp_path / profile.NOISE_PLAN
    path.parent.mkdir(parents=True)
    path.write_text("Changed scientific protocol.\n")
    with pytest.raises(ValueError, match="frozen noise-pilot"):
        profile.source_hashes(request=request())


@pytest.mark.parametrize("artifact", ["prepared.json", "metadata_initial.json"])
def test_resealed_preparation_cannot_mix_member_formats(tmp_path, artifact):
    directory = prepare(tmp_path)
    document = profile.read(directory, artifact)
    document["format"] = profile.FORMAT
    _write_json(directory / artifact, document)
    if artifact == "metadata_initial.json":
        manifest = profile.read(directory, "prepared.json")
        manifest["files"][artifact] = profile._sha256(
            (directory / artifact).read_bytes()
        )
        _write_json(directory / "prepared.json", manifest)
    with pytest.raises(ValueError):
        profile.verify_prepared(directory)


def test_failed_probe_verification_exposes_exact_mode_and_is_read_only(tmp_path):
    directory = failed_member(tmp_path)
    before = {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
    result = profile.verify_member(directory)
    assert result["format"] == profile.NOISE_TECHNICAL_FORMAT
    assert result["requested_iterations"] == 10
    assert result["technical"] is True
    assert result["status"] == "timeout"
    assert result["selected"] is None
    assert result["costs"]["cpu_user_seconds"] is None
    assert result["costs"]["callback_calls_during_fit"] is None
    assert before == {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}


@pytest.mark.parametrize("artifact", ["outcome.json", "metadata.json"])
def test_resealed_failure_cannot_change_its_member_format(tmp_path, artifact):
    directory = failed_member(tmp_path)
    record = profile.read(directory, artifact)
    record["format"] = profile.FORMAT
    _write_json(directory / artifact, record)
    seal(directory)
    with pytest.raises(ValueError):
        profile.verify_member(directory)


@pytest.mark.parametrize("field", ["worker_provenance", "worker_adapter_source_sha256"])
def test_probe_timeout_still_rejects_worker_origin_contradictions(tmp_path, field):
    directory = failed_member(tmp_path)
    metadata = profile.read(directory, "metadata.json")
    metadata[field] = {}
    _write_json(directory / "metadata.json", metadata)
    seal(directory)
    with pytest.raises(ValueError, match="actual worker"):
        profile.verify_member(directory)


@pytest.mark.parametrize(
    "message",
    [
        "KeyboardInterrupt: stopped",
        "ValueError: Unexpected actual equation_search invocation.",
    ],
)
def test_probe_timeout_cannot_hide_interrupts_or_guard_errors(tmp_path, message):
    directory = failed_member(tmp_path)
    metadata = profile.read(directory, "metadata.json")
    metadata.update(phase="failed", failed_during="fit", error=message)
    _write_json(directory / "metadata.json", metadata)
    seal(directory)
    with pytest.raises(ValueError, match="integrity"):
        profile.verify_member(directory)


def test_probe_rechecks_outcome_after_consumption(tmp_path, monkeypatch):
    directory = failed_member(tmp_path)
    original = profile.failure_status

    def mutate(metadata, **kwargs):
        result = original(metadata, **kwargs)
        outcome = profile.read(directory, "outcome.json")
        outcome["worker_wall_seconds"] = 17.0
        _write_json(directory / "outcome.json", outcome)
        seal(directory)
        return result

    monkeypatch.setattr(profile, "failure_status", mutate)
    with pytest.raises(ValueError, match="changed during"):
        profile.verify_member(directory)


def test_shared_launcher_preserves_probe_format_and_parent_deadline(
    tmp_path, monkeypatch
):
    directory = prepare(tmp_path)
    observed = {}

    class TimedOutProcess:
        returncode = None

        def __init__(self, command, **kwargs):
            observed["command"] = command
            assert kwargs["start_new_session"] is True

        def wait(self, timeout):
            observed["timeout"] = timeout
            raise profile.subprocess.TimeoutExpired("technical probe", timeout)

    def stop(process):
        process.returncode = -15

    monkeypatch.setattr(profile.subprocess, "Popen", TimedOutProcess)
    monkeypatch.setattr(profile.symbolic, "_stop_worker", stop)
    result = profile.run_member(directory, deadline=profile.time.monotonic() + 600)
    assert 0 < observed["timeout"] <= 600
    assert str(profile.ROOT / "scripts/run_confirmed_worker.py") in observed["command"]
    assert (
        profile.read(directory, "outcome.json")["format"]
        == profile.NOISE_TECHNICAL_FORMAT
    )
    assert result["format"] == profile.NOISE_TECHNICAL_FORMAT
    assert result["requested_iterations"] == 10
    assert result["status"] == "timeout"


@pytest.mark.parametrize("iterations", [1, 1000])
def test_actual_probe_guard_rejects_legacy_iteration_counts(iterations):
    class Backend:
        @property
        def equation_search(self):
            pytest.fail("A contradictory invocation must not reach the native backend.")

    guard = profile.native.SearchInvocationGuard(Backend(), 10)
    with pytest.raises(ValueError, match="actual equation_search"):
        guard._jl_call_nogil(
            np.ones((1, 2)),
            np.ones(2),
            niterations=iterations,
            parallelism="serial",
            return_state=True,
            saved_state=None,
            guesses=None,
            weights=None,
        )


def test_native_probe_completion_requires_all_ten_outer_rounds(tmp_path, monkeypatch):
    directory = tmp_path / "native"
    directory.mkdir()
    _write_json(
        directory / "search_invocation.json", profile.native.invocation_record(10)
    )
    clock = {
        "requested_iterations": 10,
        "populations": 2,
        "processed_population_cycles": 20,
        "completed_outer_rounds": 10,
        "residual_population_cycles": 0,
        "iteration_limit_reached": True,
        "timeout_reached": False,
        "technical_counter_stop": False,
        "main_loop_call_wall_seconds": 1.0,
        "elapsed_at_last_check_seconds": 1.0,
        "monotonic_to_last_check_seconds": 1.0,
        "checks": 20,
        "clock_difference_seconds": 0.0,
    }
    _write_json(directory / "search_clock.json", clock)
    monkeypatch.setattr(
        profile, "_verify_options", lambda *args: {"status": "verified"}
    )
    assert profile._native_completion(directory, request())["status"] == "verified"
    clock["completed_outer_rounds"] = 1
    _write_json(directory / "search_clock.json", clock)
    with pytest.raises(ValueError, match="iteration budget"):
        profile._native_completion(directory, request())
