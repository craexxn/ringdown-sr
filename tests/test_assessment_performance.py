"""Optimization boundaries must retain fresh checks and exact original records."""

import subprocess

import pytest
import test_assessment_sources as archive_fixtures
import test_future_assessment as fixtures
from test_symbolic_pilot import read

from ringdown_sr import assessment_sources as sources
from ringdown_sr import future_assessment as future
from ringdown_sr.assessment_publication import (
    LOCK,
    REPORT,
    Consumption,
    Deadline,
    export_transaction,
)

software = fixtures.software
replay_source = fixtures.replay_source
synthetic = archive_fixtures.synthetic


@pytest.fixture
def git_source(tmp_path, monkeypatch):
    root = tmp_path / "repository"
    root.mkdir()

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    path = root / "source.txt"
    path.write_bytes(b"first")
    git("add", "source.txt")
    git("commit", "-qm", "first")
    commit = git("rev-parse", "HEAD")
    monkeypatch.setattr(sources, "ROOT", root)
    calls = []
    check_output = subprocess.check_output

    def count(args, *rest, **kwargs):
        if args[:2] == ["git", "show"]:
            calls.append(tuple(args))
        return check_output(args, *rest, **kwargs)

    monkeypatch.setattr(subprocess, "check_output", count)
    return root, commit, git, calls


def test_git_cache_is_not_shared_after_success_or_failure(git_source, tmp_path):
    _, commit, _, calls = git_source

    def build(consumed, fail=False):
        assert consumed.git_file(commit, "source.txt") == b"first"
        assert consumed.git_file(commit, "source.txt") == b"first"
        if fail:
            raise ValueError("synthetic build failure")
        return {"groups": []}, "summary\n", {}

    export_transaction(tmp_path / "first", build)
    assert len(calls) == 1
    with pytest.raises(ValueError, match="synthetic build failure"):
        export_transaction(tmp_path / "failed", lambda c: build(c, True))
    assert len(calls) == 2 and (tmp_path / "failed" / LOCK).exists()
    export_transaction(tmp_path / "next", build)
    assert len(calls) == 3
    assert sources._git_file(commit, "source.txt") == b"first"
    assert len(calls) == 4


def test_moving_refs_are_fresh_while_full_commits_and_names_remain_separate(git_source):
    root, first, git, calls = git_source
    cached = sources.GitFileCache()
    assert cached("HEAD", "source.txt") == b"first"
    assert cached(first, "source.txt") == b"first"
    (root / "source.txt").write_bytes(b"second")
    (root / "other.txt").write_bytes(b"other")
    git("add", ".")
    git("commit", "-qm", "second")
    second = git("rev-parse", "HEAD")
    assert cached("HEAD", "source.txt") == b"second"
    assert cached(first, "source.txt") == b"first"
    assert cached(second, "source.txt") == b"second"
    assert cached(second, "other.txt") == b"other"
    assert len(calls) == 5
    with pytest.raises(ValueError, match="Unsafe archive path"):
        cached(first, "../source.txt")
    assert len(calls) == 5


def test_failed_git_reads_are_not_cached(git_source, monkeypatch):
    _, commit, _, _ = git_source
    output = subprocess.check_output
    attempts = 0

    def fail_once(args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise subprocess.CalledProcessError(1, args)
        return output(args, **kwargs)

    monkeypatch.setattr(subprocess, "check_output", fail_once)
    cached = sources.GitFileCache()
    with pytest.raises(subprocess.CalledProcessError):
        cached(commit, "source.txt")
    assert cached(commit, "source.txt") == b"first"
    assert cached(commit, "source.txt") == b"first"
    assert attempts == 2


@pytest.mark.parametrize("change", ["content", "symlink", "size"])
def test_archive_reader_is_once_per_checkpoint_and_never_reused_across_them(
    tmp_path, monkeypatch, change
):
    path = tmp_path / "archive.tar.gz"
    path.write_bytes(b"original")
    consumed = Consumption(Deadline(30))
    consumed.add_archive(path, b"original")
    calls = []
    bounded = sources.bounded_read

    def read_once(path):
        calls.append(path)
        return bounded(path)

    monkeypatch.setattr(sources, "bounded_read", read_once)
    consumed.check()
    assert calls == [path]
    if change == "content":
        path.write_bytes(b"modified")
    elif change == "symlink":
        other = tmp_path / "copy"
        other.write_bytes(b"original")
        path.unlink()
        path.symlink_to(other)
    else:
        monkeypatch.setattr(sources, "MAX_ARCHIVE", 8)
        path.write_bytes(b"oversized")
    with pytest.raises(ValueError):
        consumed.check()
    assert calls == [path, path]


@pytest.mark.parametrize("checkpoint", [1, 2, 3, 4, 5])
def test_archive_mutation_at_each_publication_checkpoint_revokes_release(
    tmp_path, monkeypatch, checkpoint
):
    path = tmp_path / "source.tar.gz"
    path.write_bytes(b"original")
    output = tmp_path / "output"
    check = Consumption.check
    calls = 0

    def change_at_boundary(consumed):
        nonlocal calls
        calls += 1
        if calls == checkpoint:
            path.write_bytes(b"modified")
        check(consumed)

    def build(consumed):
        consumed.add_archive(path, b"original")
        return {"groups": [{"valid": True}]}, "summary\n", {}

    monkeypatch.setattr(Consumption, "check", change_at_boundary)
    with pytest.raises(ValueError, match="Original archive changed"):
        export_transaction(output, build)
    assert calls == checkpoint
    assert (output / LOCK).exists()
    assert read(output / REPORT)["status"] == "failed"
    assert read(output / REPORT)["groups"] == []


def test_frozen_archive_bytes_avoid_one_read_but_retain_the_post_import_check(
    synthetic, monkeypatch
):
    write, path, _, _ = synthetic
    write()
    raw = path.read_bytes()
    bounded = sources.bounded_read
    calls = []

    def count(path):
        calls.append(path)
        return bounded(path)

    monkeypatch.setattr(sources, "bounded_read", count)
    result = sources.read_verified_series(path, "synthetic-series", contents=raw)
    assert calls == [path] and len(result.records) == 2
    path.write_bytes(b"modified")
    with pytest.raises(ValueError, match="Original archive changed"):
        sources.read_verified_series(path, "synthetic-series", contents=raw)
    assert calls == [path, path]


def test_last_archive_read_remains_after_preceding_source_callbacks(tmp_path):
    path = tmp_path / "original.tar.gz"
    path.write_bytes(b"original")
    output = tmp_path / "output"
    checkpoints = 0

    def preceding_check():
        nonlocal checkpoints
        checkpoints += 1
        if checkpoints == 5:
            assert not (output / LOCK).exists()
            path.write_bytes(b"modified")

    def build(consumed):
        consumed.callbacks.append(preceding_check)
        consumed.add_archive(path, b"original")
        return {"groups": [{"valid": True}]}, "summary\n", {}

    with pytest.raises(ValueError, match="Original archive changed"):
        export_transaction(output, build)
    assert checkpoints == 5 and (output / LOCK).exists()
    assert read(output / REPORT)["groups"] == []


def test_prediction_reuse_preserves_records_and_evaluates_each_grid_once(
    replay_source, tmp_path, monkeypatch
):
    source, original, _ = replay_source
    evaluate = future.evaluate_tree
    grids = []

    def once(tree, times):
        grids.append(times.tobytes())
        return evaluate(tree, times)

    monkeypatch.setattr(future, "evaluate_tree", once)
    output = tmp_path / "replay"
    future.export_assessment(source, output)
    assert len(grids) == 2 * len(future.ARMS)
    assert len(set(grids)) == 2
    assert read(output / "assessment_records.json") == read(
        original / "assessment_records.json"
    )
