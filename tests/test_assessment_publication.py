"""Publication counterexamples, including late mutation and repeated cancellation."""

import os
import signal
from contextlib import contextmanager
from pathlib import Path

import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr.assessment_sources import read_json, sha256


def build(consumed):
    return (
        {"series": ["synthetic"], "groups": ["synthetic"]},
        "Synthetic summary.\n",
        {"records.json": b"[]\n"},
    )


def locked(path):
    assert (path / publication.LOCK).exists()
    report = read_json((path / publication.REPORT).read_bytes())
    assert report["status"] == "failed" and report["release"] == "locked"
    assert report["series"] == report["groups"] == []
    assert not (path / publication.SUMMARY).exists()
    assert not (path / publication.MANIFEST).exists()
    assert not (path / publication.PENDING).exists()
    return read_json((path / "assessment_failure.json").read_bytes())


def test_success_manifest_and_deterministic_outputs(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    for output in (first, second):
        result = publication.export_transaction(output, build)
        assert result["status"] == "completed"
        assert not (output / publication.LOCK).exists()
        manifest = read_json((output / publication.MANIFEST).read_bytes())
        assert manifest == {
            p.name: sha256(p.read_bytes())
            for p in output.iterdir()
            if p.name != publication.MANIFEST
        }
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()
    }


@pytest.mark.parametrize(
    "name",
    [publication.SUMMARY, publication.MANIFEST, publication.PENDING, "records.json"],
)
def test_mutation_while_writing_pending_report_revokes_release(
    tmp_path, monkeypatch, name
):
    output = tmp_path / "output"
    write = Path.write_bytes

    def mutate(path, raw):
        result = write(path, raw)
        if path.name == publication.PENDING:
            write(output / name, b"late mutation")
        return result

    monkeypatch.setattr(Path, "write_bytes", mutate)
    with pytest.raises(ValueError, match="artifact changed"):
        publication.export_transaction(output, build)
    locked(output)


@pytest.mark.parametrize(
    "name",
    [publication.SUMMARY, publication.MANIFEST, publication.PENDING, "records.json"],
)
def test_each_write_failure_keeps_output_locked(tmp_path, monkeypatch, name):
    output = tmp_path / "output"
    write = Path.write_bytes

    def fail(path, raw):
        if path.name == name:
            raise OSError("injected publication write failure")
        return write(path, raw)

    monkeypatch.setattr(Path, "write_bytes", fail)
    with pytest.raises(OSError, match="injected"):
        publication.export_transaction(output, build)
    locked(output)


def test_changed_consumed_bytes_at_last_write_prevent_release(tmp_path, monkeypatch):
    original = tmp_path / "original.bin"
    original.write_bytes(b"original")
    output = tmp_path / "output"

    def with_source(consumed):
        consumed.add(original, original.read_bytes())
        return build(consumed)

    write = Path.write_bytes

    def mutate(path, raw):
        result = write(path, raw)
        if path.name == publication.PENDING:
            write(original, b"changed")
        return result

    monkeypatch.setattr(Path, "write_bytes", mutate)
    with pytest.raises(ValueError, match="Consumed file changed"):
        publication.export_transaction(output, with_source)
    locked(output)


@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM, signal.SIGALRM])
def test_actual_signal_cancels_and_restores_handler(tmp_path, sig):
    previous = signal.getsignal(sig)
    output = tmp_path / "output"

    def interrupted(consumed):
        os.kill(os.getpid(), sig)
        pytest.fail("Signal must abort the build.")

    with pytest.raises(TimeoutError if sig == signal.SIGALRM else InterruptedError):
        publication.export_transaction(output, interrupted)
    locked(output)
    assert signal.getsignal(sig) == previous
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)


@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
def test_failure_after_positive_rename_and_second_signal_during_failed_cleanup(
    tmp_path, monkeypatch, sig
):
    output = tmp_path / "output"
    replace, unlink = Path.replace, Path.unlink

    def publish_then_fail(path, destination):
        result = replace(path, destination)
        if path.name == publication.PENDING:
            assert read_json(Path(destination).read_bytes())["status"] == "completed"
            raise RuntimeError("after positive rename")
        return result

    failed = False

    def cleanup_failure(path, *args, **kwargs):
        nonlocal failed
        if path.name == publication.REPORT and not failed:
            failed = True
            os.kill(os.getpid(), sig)
            raise OSError("first cleanup failure")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "replace", publish_then_fail)
    monkeypatch.setattr(Path, "unlink", cleanup_failure)
    with pytest.raises(RuntimeError, match="positive rename"):
        publication.export_transaction(output, build)
    failure = locked(output)
    assert failure["deferred_signals"] == [sig]
    assert len(failure["cleanup_errors"]) == 1


def test_error_after_removing_lock_revokes_already_visible_success(
    tmp_path, monkeypatch
):
    output = tmp_path / "output"
    unlink = Path.unlink

    def after_unlock(path, *args, **kwargs):
        result = unlink(path, *args, **kwargs)
        if path.name == publication.LOCK:
            raise TimeoutError("deadline after unlocking")
        return result

    monkeypatch.setattr(Path, "unlink", after_unlock)
    with pytest.raises(TimeoutError):
        publication.export_transaction(output, build)
    locked(output)


def test_second_failure_while_writing_locked_report_retains_failure_evidence(
    tmp_path, monkeypatch
):
    output = tmp_path / "output"
    write = Path.write_bytes

    def fail(path, raw):
        if path.name in (publication.PENDING, publication.REPORT):
            raise OSError("persistent report write failure")
        return write(path, raw)

    monkeypatch.setattr(Path, "write_bytes", fail)
    with pytest.raises(OSError):
        publication.export_transaction(output, build)
    assert (output / publication.LOCK).exists()
    assert not (output / publication.REPORT).exists()
    assert not (output / publication.MANIFEST).exists()
    failure = read_json((output / "assessment_failure.json").read_bytes())
    assert failure["status"] == "failed" and len(failure["cleanup_errors"]) == 2


@pytest.mark.parametrize(
    "marker",
    [
        "report.json",
        "checksums.json",
        publication.REPORT,
        publication.MANIFEST,
        publication.LOCK,
    ],
)
def test_no_output_inside_original_or_existing_assessment(tmp_path, marker):
    original = tmp_path / "original"
    original.mkdir()
    (original / marker).write_bytes(b"unchanged")
    with pytest.raises(ValueError, match="existing run"):
        publication.export_transaction(original / "nested", build)
    assert list(original.iterdir()) == [original / marker]
    assert (original / marker).read_bytes() == b"unchanged"


def test_existing_output_and_symlink_parent_rejected(tmp_path):
    existing = tmp_path / "existing"
    existing.mkdir()
    (existing / "keep").write_bytes(b"untouched")
    alias = tmp_path / "alias"
    alias.symlink_to(existing, target_is_directory=True)
    for path in (existing, alias / "new"):
        with pytest.raises(ValueError):
            publication.export_transaction(path, build)
    assert (existing / "keep").read_bytes() == b"untouched"
    assert not (existing / "new").exists()


def test_existing_alarm_is_not_replaced_and_reserves_no_output(tmp_path):
    signal.setitimer(signal.ITIMER_REAL, 60)
    try:
        with pytest.raises(RuntimeError, match="existing alarm"):
            publication.export_transaction(tmp_path / "output", build)
        assert signal.getitimer(signal.ITIMER_REAL)[0] > 55
        assert not (tmp_path / "output").exists()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


@pytest.mark.parametrize("seconds", [0, -1, True, float("nan"), float("inf")])
def test_invalid_deadline_rejected_before_output(tmp_path, seconds):
    with pytest.raises(ValueError):
        publication.export_transaction(tmp_path / "output", build, seconds=seconds)
    assert not (tmp_path / "output").exists()


def test_expired_cooperative_deadline():
    clock = publication.Deadline(60)
    clock.started -= 61
    with pytest.raises(TimeoutError):
        clock.check()


def test_error_during_deadline_context_teardown_also_revokes(tmp_path, monkeypatch):
    active = publication.Deadline.active

    @contextmanager
    def failing_exit(clock):
        with active(clock):
            yield clock
        raise RuntimeError("context teardown failure")

    monkeypatch.setattr(publication.Deadline, "active", failing_exit)
    output = tmp_path / "output"
    with pytest.raises(RuntimeError, match="teardown"):
        publication.export_transaction(output, build)
    locked(output)
