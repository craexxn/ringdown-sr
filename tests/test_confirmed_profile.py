"""The opt-in member must retain its profile and reject integrity failures."""

from dataclasses import asdict

import numpy as np
import pytest

from ringdown_sr import confirmed_profile as profile
from ringdown_sr import symbolic
from ringdown_sr.pilot import _write_json


def request(*, technical=False):
    return {
        "format": profile.FORMAT,
        "profile": profile.PROFILE,
        "seed": 20261401,
        "technical": technical,
        "budget": asdict(
            symbolic.SearchBudget(seed=20261401, niterations=1 if technical else 1000)
        ),
    }


@pytest.mark.parametrize("technical,iterations", [(False, 1000), (True, 1)])
def test_explicit_profile_retains_local_budget_and_native_loss(technical, iterations):
    budget = profile.checked_request(request(technical=technical))
    actual = profile.parameters(budget)
    assert actual["niterations"] == iterations
    assert actual["optimizer_iterations"] == 300
    assert actual["optimizer_nrestarts"] == 5
    assert actual["use_frequency"] is actual["use_frequency_in_tournament"] is True
    assert actual["should_simplify"] is False
    assert actual["warmup_maxsize_by"] == 0
    assert actual["loss_function"] == "Main.SearchTimeBudget.objective"
    assert actual["batching"] is False
    assert actual["timeout_in_seconds"] is None
    assert actual["guesses"] is None


def test_legacy_default_search_parameters_are_unchanged():
    legacy = symbolic.search_parameters(symbolic.SearchBudget())
    assert legacy["optimizer_iterations"] == 20
    assert legacy["optimizer_nrestarts"] == 2
    assert legacy["use_frequency"] is legacy["use_frequency_in_tournament"] is False
    assert "should_simplify" not in legacy
    assert legacy["loss_function"] == "Main.RingdownSRSearch.objective"


@pytest.mark.parametrize(
    "field,value",
    [
        ("seed", True),
        ("seed", 0),
        ("seed", 2**31),
        ("technical", 1),
        ("profile", "legacy"),
        ("format", symbolic.FORMAT),
    ],
)
def test_request_cannot_silently_change_scope(field, value):
    document = request()
    document[field] = value
    with pytest.raises(ValueError):
        profile.checked_request(document)


@pytest.mark.parametrize(
    "field,value",
    [
        ("niterations", True),
        ("niterations", 2),
        ("niterations", 1.0),
        ("populations", 1),
        ("population_size", 64),
        ("ncycles_per_iteration", 1),
        ("seed", 4),
    ],
)
def test_effective_budget_aliases_and_changes_are_rejected(field, value):
    document = request(technical=True)
    document["budget"][field] = value
    with pytest.raises(ValueError):
        profile.checked_request(document)


@pytest.mark.parametrize(
    "message",
    [
        "ValueError: Unexpected actual equation_search invocation.",
        "KeyboardInterrupt: ",
        "InterruptedError: interrupted",
        "RuntimeError: unknown",
        "AssertionError: replay failed",
        'JuliaError: ErrorException("Wrong native option")',
    ],
)
@pytest.mark.parametrize("timed_out", [False, True])
def test_integrity_and_interrupts_are_not_fit_errors_even_after_timeout(
    message, timed_out
):
    with pytest.raises(ValueError, match="integrity"):
        profile.failure_status(
            {"phase": "failed", "failed_during": "fit", "error": message},
            timed_out=timed_out,
        )


@pytest.mark.parametrize("message", profile.NUMERICAL_ERRORS)
def test_only_explicit_fit_numerical_errors_are_allowed(message):
    metadata = {
        "phase": "failed",
        "failed_during": "fit",
        "error": message + " numerical case",
    }
    assert profile.failure_status(metadata) == "fit_error"
    assert profile.failure_status(metadata, timed_out=True) == "timeout"
    with pytest.raises(ValueError):
        profile.failure_status({**metadata, "failed_during": "replay"})


def test_early_timeout_allows_only_missing_not_contradictory_worker_origin():
    initial = {"provenance": {"git": {"commit": "bound"}}}
    manifest = {"sources": {"worker": "hash"}}
    early = {
        **initial,
        "adapter_source_sha256": manifest["sources"],
        "phase": "worker_start",
    }
    assert profile.failure_status(early, timed_out=True) == "timeout"
    profile._verify_origin(early, initial, manifest, completed=False)
    for key in ("worker_provenance", "worker_adapter_source_sha256"):
        with pytest.raises(ValueError, match="actual worker"):
            profile._verify_origin(
                {**early, key: {}}, initial, manifest, completed=False
            )
    with pytest.raises(ValueError, match="actual worker"):
        profile._verify_origin(
            {**early, "phase": "fit"}, initial, manifest, completed=False
        )


def test_guard_checks_actual_native_call_before_delegating():
    class Backend:
        @property
        def equation_search(self):
            pytest.fail("Guard must reject before actual native invocation.")

    guard = profile.native.SearchInvocationGuard(Backend(), 1000)
    with pytest.raises(ValueError, match="actual equation_search"):
        guard._jl_call_nogil(
            np.ones((1, 2)),
            np.ones(2),
            niterations=500,
            parallelism="serial",
            return_state=True,
            saved_state=None,
            guesses=None,
            weights=None,
        )
    with pytest.raises(ValueError, match="completed"):
        guard.record()


def test_prepare_binds_all_fixed_inputs_and_preserves_original_arrays(tmp_path):
    times, observed = np.array([0.0, 1.0]), np.array([1.0, 0.0])
    covariance = np.array([[2.5, 1.5], [1.5, 4.5]])
    output = tmp_path / "member"
    profile.prepare_member(
        output, times, observed, covariance=covariance, seed=20261401, technical=True
    )
    immutable = profile.prepared_files(output)
    times[0] = 99
    observed[0] = 99
    covariance[0, 0] = 99
    checked, arrays, _ = profile.verify_prepared(output)
    assert checked["technical"] is True
    assert arrays["time_s"].tolist() == [0.0, 1.0]
    assert arrays["observed"].tolist() == [1.0, 0.0]
    assert arrays["covariance"].tolist() == [[2.5, 1.5], [1.5, 4.5]]
    _write_json(output / "metadata.json", {"phase": "running"})
    assert immutable == profile.prepared_files(output)
    (output / "inputs.npz").write_bytes(b"changed")
    with pytest.raises(ValueError, match="preparation"):
        profile.verify_prepared(output)


def test_artifact_parser_rejects_duplicate_keys_and_nonfinite(tmp_path):
    for content in (b'{"seed":1,"seed":2}', b'{"loss":NaN}'):
        (tmp_path / "record.json").write_bytes(content)
        with pytest.raises(ValueError):
            profile.read(tmp_path, "record.json")


def failed_member(tmp_path, *, phase="worker_start", error=None, timed_out=True):
    output = tmp_path / "failed"
    manifest = profile.prepare_member(
        output, [0.0, 1.0], [1.0, 0.0], seed=20261401, technical=True
    )
    initial = profile.read(output, "metadata_initial.json")
    metadata = {**initial, "phase": phase}
    if phase == "fit":
        metadata.update(
            worker_provenance=initial["provenance"],
            worker_adapter_source_sha256=manifest["sources"],
        )
    if error is not None:
        metadata.update(phase="failed", failed_during=phase, error=error)
    _write_json(output / "metadata.json", metadata)
    _write_json(
        output / "outcome.json",
        {
            "format": profile.FORMAT,
            "status": "timeout" if timed_out else "fit_error",
            "returncode": -15 if timed_out else 1,
            "timed_out": timed_out,
            "worker_wall_seconds": 12.0,
            "adapter_call_wall_seconds": 12.0,
            "cpu_user_seconds": None if timed_out else 3.0,
            "cpu_system_seconds": None if timed_out else 1.0,
        },
    )
    rebind_checksums(output)
    return output


def rebind_checksums(output):
    _write_json(
        output / "member_checksums.json",
        {
            path.relative_to(output).as_posix(): profile._sha256(path.read_bytes())
            for path in output.rglob("*")
            if path.is_file() and path.name != "member_checksums.json"
        },
    )


def test_read_only_failed_member_preserves_unknown_cpu_and_fixed_denominator(tmp_path):
    output = failed_member(tmp_path)
    before = {p: p.read_bytes() for p in output.rglob("*") if p.is_file()}
    record = profile.verify_member(output)
    assert record["status"] == "timeout"
    assert record["selected"] is None
    assert record["candidates"] == []
    assert record["costs"]["cpu_user_seconds"] is None
    assert record["costs"]["callback_calls_during_fit"] is None
    assert record["costs"]["worker_wall_seconds"] == 12
    assert before == {p: p.read_bytes() for p in output.rglob("*") if p.is_file()}


@pytest.mark.parametrize("field", ["worker_provenance", "worker_adapter_source_sha256"])
def test_failed_member_reverification_rejects_actual_worker_contradictions(
    tmp_path, field
):
    output = failed_member(
        tmp_path, phase="fit", error="OverflowError: ordinary range", timed_out=False
    )
    assert profile.verify_member(output)["status"] == "fit_error"
    metadata = profile.read(output, "metadata.json")
    metadata[field] = {}
    _write_json(output / "metadata.json", metadata)
    rebind_checksums(output)
    with pytest.raises(ValueError, match="actual worker"):
        profile.verify_member(output)


@pytest.mark.parametrize(
    "message",
    [
        "KeyboardInterrupt: stopped",
        "ValueError: Unexpected actual equation_search invocation.",
    ],
)
def test_failed_member_reverification_cannot_hide_interrupt_or_guard_behind_timeout(
    tmp_path, message
):
    output = failed_member(tmp_path, phase="fit", error=message)
    with pytest.raises(ValueError, match="integrity"):
        profile.verify_member(output)


def test_failed_member_late_change_is_not_released(tmp_path, monkeypatch):
    output = failed_member(tmp_path)
    original = profile.failure_status

    def mutate(metadata, **kwargs):
        result = original(metadata, **kwargs)
        outcome = profile.read(output, "outcome.json")
        outcome["worker_wall_seconds"] = 99.0
        _write_json(output / "outcome.json", outcome)
        rebind_checksums(output)
        return result

    monkeypatch.setattr(profile, "failure_status", mutate)
    with pytest.raises(ValueError, match="changed during"):
        profile.verify_member(output)


def test_checker_rejects_changed_covariance_even_with_same_zero_expression_loss():
    checker = profile.native.load_module(
        profile.ROOT / "scripts/check_confirmed_profile.py", "confirmed_checker_fixture"
    )
    original = checker.fixture("full")
    altered = {**original, "covariance": np.array([[3.0, 2.0], [2.0, 4.0]])}
    y = original["observed"]
    original_zero = y @ np.linalg.solve(original["covariance"], y) / y.size
    altered_zero = y @ np.linalg.solve(altered["covariance"], y) / y.size
    assert original_zero == altered_zero == 0.25
    record = {
        "input_fingerprints": {
            key: profile.sources.fingerprint(value) for key, value in altered.items()
        }
    }
    with pytest.raises(ValueError, match="fixture"):
        checker.verify_fixture(record, "full")
