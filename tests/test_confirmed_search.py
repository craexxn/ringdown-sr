"""Check four-member execution, weighted bindings, publication and read-only replay."""

import copy
from types import SimpleNamespace

import numpy as np
import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import confirmed_search as search
from ringdown_sr.pilot import _write_json

SEEDS = (1101, 1102, 1103, 1104)


def fake_native(monkeypatch, *, statuses=None, losses=None, complexities=None):
    """Replace native work only; retain the complete package lifecycle."""
    events = []
    statuses = statuses or ["completed"] * 4
    losses = losses or [4.0, 2.0, 1.0, 3.0]
    complexities = complexities or [1] * 4
    software = {"software_commit": "a" * 40, "source_sha256": {}}
    provenance = {
        "git": {"available": True, "commit": "a" * 40, "dirty": False, "changes": []},
        "python_source_sha256": {},
        "python_source_set_sha256": search.sources.sha256(
            search.sources.json_bytes({})
        ),
        "project_file_sha256": {},
    }
    monkeypatch.setattr(
        search, "freeze_software", lambda consumed: copy.deepcopy(software)
    )
    monkeypatch.setattr(search, "_provenance", lambda: copy.deepcopy(provenance))

    def prepare(directory, time_s, observed, *, covariance, seed, technical):
        directory.mkdir()
        arrays = {"time_s": time_s, "observed": observed}
        if covariance is not None:
            arrays["covariance"] = covariance
        np.savez(directory / "inputs.npz", **arrays)
        _write_json(directory / "request.json", {"seed": seed, "technical": technical})
        events.append(("prepare", seed))

    def prepared(directory):
        return {
            name: (directory / name).read_bytes()
            for name in ("inputs.npz", "request.json")
        }

    def verify(directory):
        events.append(("verify", directory.name))
        return search.sources.read_json((directory / "verified.json").read_bytes())

    def run(directory, *, deadline):
        assert all(
            (directory.parent / f"member-{member + 1:02d}/request.json").is_file()
            for member in range(4)
        )
        assert (directory.parent / "prepared_bindings.json").is_file()
        request = search.sources.read_json((directory / "request.json").read_bytes())
        member = int(directory.name[-2:]) - 1
        events.append(("run", request["seed"]))
        status = statuses[member]
        if isinstance(status, BaseException):
            raise status
        arrays = search._input_arrays((directory / "inputs.npz").read_bytes())
        candidate = {
            "loss": losses[member],
            "complexity": complexities[member],
            "prediction": arrays["observed"].tolist(),
            "tree": {"kind": "constant", "value_hex": float(member).hex()},
            "display_equation": str(member),
        }
        record = {
            "status": status,
            "selected_index": 0 if status == "completed" else None,
            "selected": candidate if status == "completed" else None,
            "candidates": [candidate] if status == "completed" else [],
            "costs": {
                name: 10 if name == "callback_calls_during_fit" else 1.0
                for name in search.costs.COST_FIELDS
            },
            "numerical_environment": {"threads": 1},
            "provenance": copy.deepcopy(provenance),
            "seed": request["seed"],
            "technical": request["technical"],
            "profile": search.PROFILE,
            "input_fingerprints": search._fingerprints(arrays),
        }
        _write_json(directory / "verified.json", record)
        return verify(directory)

    monkeypatch.setattr(
        search,
        "profile",
        SimpleNamespace(
            prepare_member=prepare,
            prepared_files=prepared,
            run_member=run,
            verify_member=verify,
        ),
    )
    return events


def run_package(tmp_path, **kwargs):
    return search.run_confirmed_package(
        [0.0, 0.1, 0.2],
        [1.0, 0.5, -0.2],
        output=tmp_path / "package",
        seeds=SEEDS,
        technical=True,
        **kwargs,
    )


def reseal(output):
    """Recompute ordinary hashes so semantic checks must detect the contradiction."""
    _write_json(
        output / "prepared_bindings.json",
        {
            name: search.sources.sha256(raw)
            for name, raw in search._prepared_files(output).items()
        },
    )
    completion = output / "completion"
    _write_json(
        completion / "raw_checksums.json",
        {
            name: search.sources.sha256(raw)
            for name, raw in search.restarts.raw_files(output).items()
        },
    )
    _write_json(
        completion / publication.MANIFEST,
        {
            name: search.sources.sha256((completion / name).read_bytes())
            for name in (publication.REPORT, publication.SUMMARY, "raw_checksums.json")
        },
    )


@pytest.mark.parametrize("covariance", [None, np.diag([1.0, 2.0, 4.0])])
def test_four_fresh_workers_choose_native_loss_and_verify_without_writes(
    monkeypatch, tmp_path, covariance
):
    events = fake_native(monkeypatch)
    run = run_package(tmp_path, covariance=covariance)
    assert run.status == "success" and run.selected_member == 2
    assert run.selected_directory == run.output_directory / "member-03"
    assert run.costs["callback_calls_during_fit"] == 40
    assert [event[0] for event in events] == ["prepare"] * 4 + ["run", "verify"] * 4
    before = {
        p.relative_to(run.output_directory): p.read_bytes()
        for p in run.output_directory.rglob("*")
        if p.is_file()
    }
    report = search.verify_confirmed_package(run.output_directory)
    after = {
        p.relative_to(run.output_directory): p.read_bytes()
        for p in run.output_directory.rglob("*")
        if p.is_file()
    }
    assert before == after
    assert report["status"] == "completed" and report["package_status"] == "success"
    assert report["selected_candidate"] == run.selected_candidate
    assert report["loss"] == (
        "mean_squared_error"
        if covariance is None
        else "covariance_quadratic_form_per_sample"
    )
    assert report["search_calls"] == 4 and report["algorithm_outputs"] == 1
    assert len([e for e in events if e[0] == "run"]) == 4


@pytest.mark.parametrize(
    "complexities,selected", [([3, 2, 2, 4], 1), ([2, 2, 2, 2], 0)]
)
def test_package_ties_use_complexity_then_fixed_member(
    monkeypatch, tmp_path, complexities, selected
):
    fake_native(monkeypatch, losses=[1.0] * 4, complexities=complexities)
    assert run_package(tmp_path).selected_member == selected


@pytest.mark.parametrize(
    "statuses,chosen",
    [
        (["fit_error", "completed", "timeout", "completed"], 1),
        (["fit_error"] * 4, None),
        (["timeout"] * 4, None),
    ],
)
def test_failures_remain_in_denominator_and_all_calls_execute(
    monkeypatch, tmp_path, statuses, chosen
):
    events = fake_native(monkeypatch, statuses=statuses)
    run = run_package(tmp_path)
    report = search.verify_confirmed_package(run.output_directory)
    assert run.selected_member == chosen
    assert run.status == ("failed" if chosen is None else "success")
    assert len(report["members"]) == 4 and report["costs"]["worker_wall_seconds"] == 4
    assert len([event for event in events if event[0] == "run"]) == 4


@pytest.mark.parametrize(
    "error",
    [KeyboardInterrupt("stop"), InterruptedError("signal"), ValueError("guard")],
)
def test_integrity_failure_or_interruption_aborts_the_whole_package(
    monkeypatch, tmp_path, error
):
    events = fake_native(
        monkeypatch, statuses=["completed", error, "completed", "completed"]
    )
    with pytest.raises(type(error), match=str(error)):
        run_package(tmp_path)
    output = tmp_path / "package"
    assert len([event for event in events if event[0] == "run"]) == 2
    assert (output / "completion" / publication.LOCK).exists()
    assert (
        search.sources.read_json((output / "run_state.json").read_bytes())["status"]
        == "aborted"
    )
    with pytest.raises(ValueError, match="incomplete|locked"):
        search.verify_confirmed_package(output)


def test_unknown_cost_stays_unknown_after_selection(monkeypatch, tmp_path):
    fake_native(monkeypatch)
    original = search.profile.run_member

    def missing_cost(directory, **kwargs):
        record = original(directory, **kwargs)
        if directory.name == "member-01":
            record["costs"]["callback_calls_during_fit"] = None
        _write_json(directory / "verified.json", record)
        return record

    monkeypatch.setattr(search.profile, "run_member", missing_cost)
    run = run_package(tmp_path)
    assert run.costs["callback_calls_during_fit"] is None
    report = search.verify_confirmed_package(run.output_directory)
    assert not report["all_costs_observed"]


def test_package_does_not_select_on_replay_loss_or_library_score(monkeypatch, tmp_path):
    fake_native(monkeypatch)
    original = search.profile.run_member

    def different_diagnostics(directory, **kwargs):
        record = original(directory, **kwargs)
        candidate = record["candidates"][0]
        candidate.update(
            python_loss=10 - candidate["loss"], library_score=100 * candidate["loss"]
        )
        record["selected"] = candidate
        _write_json(directory / "verified.json", record)
        return record

    monkeypatch.setattr(search.profile, "run_member", different_diagnostics)
    run = run_package(tmp_path)
    assert run.selected_member == 2
    search.verify_confirmed_package(run.output_directory)


@pytest.mark.parametrize(
    "field,value",
    [
        ("worker_wall_seconds", True),
        ("fit_wall_seconds", -1),
        ("callback_calls_during_fit", 0.5),
    ],
)
def test_invalid_costs_never_become_zero_or_unknown(
    monkeypatch, tmp_path, field, value
):
    fake_native(monkeypatch)
    original = search.profile.run_member

    def invalid_cost(directory, **kwargs):
        record = original(directory, **kwargs)
        record["costs"][field] = value
        return record

    monkeypatch.setattr(search.profile, "run_member", invalid_cost)
    with pytest.raises(ValueError, match="cost"):
        run_package(tmp_path)


def test_member_provenance_must_match_the_package_commit(monkeypatch, tmp_path):
    fake_native(monkeypatch)
    original = search.profile.run_member

    def other_commit(directory, **kwargs):
        record = original(directory, **kwargs)
        record["provenance"]["git"]["commit"] = "b" * 40
        return record

    monkeypatch.setattr(search.profile, "run_member", other_commit)
    with pytest.raises(ValueError, match="provenance"):
        run_package(tmp_path)


def test_bound_source_mutation_stops_further_workers(monkeypatch, tmp_path):
    events = fake_native(monkeypatch)
    source = tmp_path / "runtime.py"
    source.write_text("original")
    original_freeze = search.freeze_software
    original_run = search.profile.run_member

    def freeze(consumed):
        consumed.add(source, source.read_bytes())
        return original_freeze(consumed)

    def mutate(directory, **kwargs):
        record = original_run(directory, **kwargs)
        source.write_text("changed")
        return record

    monkeypatch.setattr(search, "freeze_software", freeze)
    monkeypatch.setattr(search.profile, "run_member", mutate)
    with pytest.raises(ValueError, match="Consumed file changed"):
        run_package(tmp_path)
    assert len([e for e in events if e[0] == "run"]) == 1


def test_changed_prepared_request_stops_before_the_first_fit(monkeypatch, tmp_path):
    events = fake_native(monkeypatch)
    original = search.profile.prepare_member

    def mutate(directory, *args, **kwargs):
        original(directory, *args, **kwargs)
        if directory.name == "member-04":
            (directory.parent / "member-01/request.json").write_text("changed")

    monkeypatch.setattr(search.profile, "prepare_member", mutate)
    with pytest.raises(ValueError, match="Consumed file changed"):
        run_package(tmp_path)
    assert not [event for event in events if event[0] == "run"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("seed", 999),
        ("technical", False),
        ("profile", "legacy"),
        ("status", "unknown"),
        ("selected_index", True),
        ("numerical_environment", None),
    ],
)
def test_member_contract_contradictions_revoke_publication(
    monkeypatch, tmp_path, field, value
):
    fake_native(monkeypatch)
    original = search.profile.run_member

    def changed(directory, **kwargs):
        record = original(directory, **kwargs)
        if directory.name == "member-03":
            record[field] = value
        return record

    monkeypatch.setattr(search.profile, "run_member", changed)
    with pytest.raises(ValueError):
        run_package(tmp_path)
    assert (tmp_path / "package/completion" / publication.LOCK).exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("loss", True),
        ("loss", -1),
        ("loss", float("inf")),
        ("complexity", True),
        ("complexity", 0),
    ],
)
def test_invalid_original_selection_is_never_a_normal_failure(
    monkeypatch, tmp_path, field, value
):
    fake_native(monkeypatch)
    original = search.profile.run_member

    def changed(directory, **kwargs):
        record = original(directory, **kwargs)
        record["candidates"][0][field] = value
        record["selected"] = record["candidates"][0]
        return record

    monkeypatch.setattr(search.profile, "run_member", changed)
    with pytest.raises(ValueError):
        run_package(tmp_path)


@pytest.mark.parametrize(
    "seed_values",
    [
        (1, 2, 3),
        (1, 2, 3, 3),
        (0, 2, 3, 4),
        (True, 2, 3, 4),
        (2**31, 2, 3, 4),
        (1.0, 2, 3, 4),
    ],
)
def test_bad_seed_packages_fail_before_reserving_output(tmp_path, seed_values):
    with pytest.raises(ValueError, match="four distinct"):
        search.run_confirmed_package(
            [0], [1], output=tmp_path / "run", seeds=seed_values
        )
    assert not (tmp_path / "run").exists()


def test_caller_mutation_cannot_change_later_worker_inputs(monkeypatch, tmp_path):
    fake_native(monkeypatch)
    times, observed, matrix = np.array([0.0, 0.1]), np.array([1.0, 0.5]), np.eye(2)
    expected = [array.copy() for array in (times, observed, matrix)]
    original = search.profile.prepare_member

    def mutate_caller(directory, *args, **kwargs):
        times[:] = 7
        observed[:] = 8
        matrix[:] = 9
        return original(directory, *args, **kwargs)

    monkeypatch.setattr(search.profile, "prepare_member", mutate_caller)
    run = search.run_confirmed_package(
        times,
        observed,
        covariance=matrix,
        output=tmp_path / "run",
        seeds=SEEDS,
        technical=True,
    )
    for member in range(4):
        with np.load(
            run.output_directory / f"member-{member + 1:02d}/inputs.npz"
        ) as saved:
            for key, value in zip(
                ("time_s", "observed", "covariance"), expected, strict=True
            ):
                np.testing.assert_array_equal(saved[key], value)
    search.verify_confirmed_package(run.output_directory)


@pytest.mark.parametrize(
    "change",
    ["covariance", "seed", "selection", "cost", "source_commit", "environment"],
)
def test_read_verification_rejects_semantic_changes_even_with_resealed_hashes(
    monkeypatch, tmp_path, change
):
    fake_native(monkeypatch)
    output = run_package(tmp_path, covariance=np.eye(3)).output_directory
    if change == "covariance":
        arrays = search._input_arrays((output / "inputs.npz").read_bytes())
        arrays["covariance"][0, 0] = 2
        np.savez(output / "inputs.npz", **arrays)
    elif change == "source_commit":
        preparation = search.sources.read_json(
            (output / "preparation.json").read_bytes()
        )
        preparation["software"]["software_commit"] = "b" * 40
        _write_json(output / "preparation.json", preparation)
    else:
        path = output / "member-03/verified.json"
        record = search.sources.read_json(path.read_bytes())
        if change == "seed":
            record["seed"] = 999
        elif change == "selection":
            record["selected"]["loss"] = 0.0
        elif change == "cost":
            record["costs"]["worker_wall_seconds"] = -1
        else:
            record["numerical_environment"] = {"threads": 2}
        _write_json(path, record)
    reseal(output)
    with pytest.raises(ValueError):
        search.verify_confirmed_package(output)


@pytest.mark.parametrize("phase", ["unlock", "after_export"])
def test_late_mutation_revokes_a_previously_written_success(
    monkeypatch, tmp_path, phase
):
    fake_native(monkeypatch)
    if phase == "unlock":
        original = search.Path.unlink

        def mutate(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if path.name == publication.LOCK:
                (path.parent.parent / "inputs.npz").write_bytes(b"changed")
            return result

        monkeypatch.setattr(search.Path, "unlink", mutate)
    else:
        original = publication.export_transaction

        def mutate(*args, **kwargs):
            result = original(*args, **kwargs)
            (tmp_path / "package/member-01/verified.json").write_text("changed")
            return result

        monkeypatch.setattr(publication, "export_transaction", mutate)
    with pytest.raises(ValueError, match="changed|inventory"):
        run_package(tmp_path)
    output = tmp_path / "package"
    assert (output / "completion" / publication.LOCK).exists()
    assert "selected_candidate" not in search.sources.read_json(
        (output / "completion" / publication.REPORT).read_bytes()
    )


def test_read_only_verifier_sees_late_lock_reappearance(monkeypatch, tmp_path):
    fake_native(monkeypatch)
    output = run_package(tmp_path).output_directory
    original = search.profile.verify_member

    def revoke(directory):
        record = original(directory)
        if directory.name == "member-04":
            (output / "completion" / publication.LOCK).write_text("revoked")
        return record

    monkeypatch.setattr(search.profile, "verify_member", revoke)
    with pytest.raises(ValueError, match="revoked"):
        search.verify_confirmed_package(output)


@pytest.mark.parametrize("change", ["selection", "costs"])
def test_resealed_aggregate_is_recomputed_from_original_members(
    monkeypatch, tmp_path, change
):
    fake_native(monkeypatch)
    output = run_package(tmp_path).output_directory
    path = output / "completion" / publication.REPORT
    report = search.sources.read_json(path.read_bytes())
    if change == "selection":
        report["selected_member"] = 0
        report["selected_candidate"] = report["members"][0]["selected"]
    else:
        report["costs"]["worker_wall_seconds"] = 1.0
    _write_json(path, report)
    reseal(output)
    with pytest.raises(ValueError, match="selection, costs or report"):
        search.verify_confirmed_package(output)
