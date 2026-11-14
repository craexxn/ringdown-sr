"""Synthetic native boundaries with real series publication and revocation."""

import copy
import json
import signal
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from ringdown_sr import assessment_publication as publication
from ringdown_sr import assessment_sources as sources
from ringdown_sr import noise_pilot as pilot
from ringdown_sr import noise_pilot_inputs as inputs
from ringdown_sr.pilot import _write_json


def read(path):
    return json.loads(Path(path).read_bytes())


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    """Mock only preparation/reference/native work, retaining real assessments."""
    times = np.arange(9, dtype=np.float64) / 4096
    diagnostic = (np.arange(8, dtype=np.float64) + 0.5) / 4096
    irregular = (np.arange(7, dtype=np.float64) + 0.3) / 4096
    common = {
        "time_s": times,
        "signal": np.exp(-4 * times),
        "diagnostic_time_s": diagnostic,
        "diagnostic_truth": np.exp(-4 * diagnostic),
        "irregular_time_s": irregular,
        "irregular_truth": np.exp(-4 * irregular),
    }
    software = {"commit": "1" * 40, "source_sha256": {"fixture.py": "2" * 64}}
    environment = {"julia": "synthetic", "threads": 1}
    cases = {}
    for spec in inputs.case_specs():
        noise = np.linspace(-0.05, 0.05, len(times), dtype=np.float64)
        arrays = {
            "noise": noise,
            "observed": common["signal"] + noise,
            "covariance_true": np.eye(len(times), dtype=np.float64) * 0.25,
            "covariance_estimated": np.eye(len(times), dtype=np.float64) * 0.30,
        }
        record = {"status": "ready", "arm_status": dict.fromkeys(pilot.ARMS, "ready")}
        cases[spec["id"]] = inputs.PreparedCase(copy.deepcopy(spec), arrays, record)
    prepared = inputs.PreparedInputs(
        {"technical": False, "software": software}, common, cases
    )
    preparation = tmp_path / "prepared"
    preparation.mkdir()
    source = preparation / "frozen_source.txt"
    source.write_text("unchanged committed fixture source")
    _write_json(preparation / "manifest.json", prepared.manifest)
    technical = tmp_path / "technical"
    (technical / "completion").mkdir(parents=True)
    technical_report = {
        "status": "completed",
        "software": software,
        "numerical_environment": environment,
        "requested_iterations": 10,
        "completed_workers": 3,
    }
    _write_json(technical / "completion" / publication.REPORT, technical_report)
    fixture = SimpleNamespace(
        prepared=prepared,
        preparation=preparation,
        technical=technical,
        source=source,
        events=[],
        reference_status="success",
        mutate_package=None,
        fail_package=None,
    )

    def verify_inputs(directory, consumed):
        assert Path(directory) == preparation
        pilot._read(source, consumed)
        sources._same(
            pilot._json(preparation / "manifest.json", consumed),
            fixture.prepared.manifest,
            "Changed fixture software.",
        )
        return fixture.prepared

    def verify_technical(directory, *, consumed):
        assert Path(directory) == technical
        result = pilot._json(technical / "completion" / publication.REPORT, consumed)
        if result["requested_iterations"] != 10 or result["completed_workers"] != 3:
            raise ValueError(
                "Technical preflight needs three completed ten-iteration workers."
            )
        return result

    def fit_reference(arrays):
        fixture.events.append(("reference",))
        return {
            "status": fixture.reference_status,
            "observed": sources.fingerprint(arrays["observed"]),
        }

    def verify_reference(record, arrays):
        if record["status"] not in {"success", "fit_error"}:
            raise ValueError("Unverified reference outcome.")
        sources._same(
            record["observed"],
            sources.fingerprint(arrays["observed"]),
            "Reference observed input changed.",
        )
        return record

    def run_package(time_s, observed, *, covariance, output, seeds):
        output = Path(output)
        case_id, arm = output.parent.parent.name, output.name
        if fixture.fail_package is not None:
            raise fixture.fail_package
        arrays = {"time_s": time_s, "observed": observed}
        if covariance is not None:
            arrays["covariance"] = covariance
        for member, seed in enumerate(seeds):
            fixture.events.append(("run", case_id, arm, member, seed))
        value = 0.25
        selected = {
            "tree": {"kind": "constant", "value_hex": value.hex()},
            "prediction": np.full_like(time_s, value).tolist(),
            "loss": 0.125,
            "complexity": 1,
            "display_equation": "0.25",
        }
        members = [
            {
                "member": member,
                "seed": seed,
                "status": "completed",
                "costs": {
                    **dict.fromkeys(pilot.COST_FIELDS, 0.0),
                    "callback_calls_during_fit": 123,
                },
            }
            for member, seed in enumerate(seeds)
        ]
        report = {
            "package_status": "success",
            "selected_member": 0,
            "selected_candidate": selected,
            "search_calls": 4,
            "members": members,
            "costs": {
                field: sum(member["costs"][field] for member in members)
                for field in pilot.COST_FIELDS
            },
            "numerical_environment": copy.deepcopy(environment),
            "technical": False,
            "profile": pilot.search.PROFILE,
            "seeds": list(seeds),
            "software": copy.deepcopy(software),
            "input_fingerprints": {
                key: sources.fingerprint(value) for key, value in arrays.items()
            },
        }
        if fixture.mutate_package is not None:
            fixture.mutate_package(case_id, arm, report)
        (output / "completion").mkdir(parents=True)
        _write_json(output / "completion" / publication.REPORT, report)
        return report

    monkeypatch.setattr(pilot.inputs, "verify_inputs", verify_inputs)
    monkeypatch.setattr(pilot.technical, "verify", verify_technical)
    monkeypatch.setattr(pilot.reference, "fit_reference", fit_reference)
    monkeypatch.setattr(pilot.reference, "verify_reference", verify_reference)
    monkeypatch.setattr(pilot.search, "run_confirmed_package", run_package)
    monkeypatch.setattr(
        pilot.search,
        "verify_confirmed_package",
        lambda directory: read(Path(directory) / "completion" / publication.REPORT),
    )
    return fixture


def run_series(tmp_path, boundary):
    root = tmp_path / "series"
    return root, pilot.run(boundary.preparation, boundary.technical, root)


def run_case(tmp_path, boundary):
    root = tmp_path / "case"
    return root, pilot._run_case(boundary.preparation, "white-01", root)


def revoked(root):
    completion = root / "completion"
    assert read(root / "run_state.json")["status"] == "aborted"
    assert not (completion / publication.MANIFEST).exists()
    if completion.is_dir():
        assert (completion / publication.LOCK).is_file()
        assert read(completion / publication.REPORT)["status"] == "failed"


def change_case(boundary, case_id, status):
    original = boundary.prepared.cases[case_id]
    arrays = copy.deepcopy(original.arrays)
    arms = dict.fromkeys(pilot.ARMS, "ready")
    if status == "data_failed":
        arrays, arms = {}, dict.fromkeys(pilot.ARMS, "not_run")
    else:
        arrays.pop("covariance_estimated")
        arms["estimated_covariance"] = "not_run"
    boundary.prepared.cases[case_id] = inputs.PreparedCase(
        original.spec, arrays, {"status": status, "arm_status": arms}
    )


def test_all_twelve_cases_keep_frozen_order_four_seeds_and_all_three_arms(
    tmp_path, boundary
):
    root, report = run_series(tmp_path, boundary)
    runs = [event[1:] for event in boundary.events if event[0] == "run"]
    expected = [
        (spec["id"], arm, member, seed)
        for spec in inputs.case_specs()
        for arm in pilot.ARMS
        for member, seed in enumerate(spec["search_seeds"])
    ]
    assert runs == expected and len(runs) == 144
    assert report["search_calls"] == report["planned_search_calls"] == 144
    assert report["planned_algorithm_outputs"] == len(report["assessments"]) == 36
    assert list(report["case_reports_sha256"]) == list(boundary.prepared.cases)
    before = list(boundary.events)
    reread = pilot.verify(boundary.preparation, boundary.technical, root)
    assert reread == report and boundary.events == before
    assert read(pilot._timing_path(root))["status"] == "completed"
    assert not (root / "completion" / publication.LOCK).exists()


def test_estimation_failure_retains_ordinary_known_and_exact_denominators(
    tmp_path, boundary
):
    change_case(boundary, "white-01", "covariance_failed")
    root, report = run_series(tmp_path, boundary)
    assert report["search_calls"] == 140
    assert len([e for e in boundary.events if e[0] == "run"]) == 140
    model = report["summary"]["models"]["white"]
    assert model["contrasts"]["known_minus_ordinary"]["available"] == 6
    assert model["contrasts"]["known_minus_ordinary"]["mcse"] is not None
    assert model["contrasts"]["estimated_minus_ordinary"]["available"] == 5
    assert model["contrasts"]["estimated_minus_ordinary"]["mcse"] is None
    arm = model["arms"]["estimated_covariance"]
    assert arm["failure_denominator"] == 6 and arm["failed_or_not_run"] == 1
    record = next(
        r
        for r in report["assessments"]
        if r["source_identity"]["model"] == "white"
        and r["source_identity"]["block"] == 1
        and r["source_identity"]["arm"] == "estimated_covariance"
    )
    assert record["status"] == "not_run" and record["search_calls"] == 0
    assert all(value is None for value in record["costs"].values())
    assert pilot.verify(boundary.preparation, boundary.technical, root) == report


def test_shared_data_failure_retains_all_three_unrun_packages(tmp_path, boundary):
    change_case(boundary, "white-01", "data_failed")
    root, report = run_series(tmp_path, boundary)
    assert report["search_calls"] == 132
    assert len([e for e in boundary.events if e[0] == "reference"]) == 11
    case = read(root / "cases/white-01/completion" / publication.REPORT)
    assert case["reference"] == {"status": "not_run", "reason": "data_failed"}
    assert all(p["package_status"] == "not_run" for p in case["packages"].values())
    assert all(len(p["members"]) == 4 for p in case["packages"].values())
    assert pilot.verify(boundary.preparation, boundary.technical, root) == report


def test_classical_numerical_fit_failure_does_not_block_symbolic_arms(
    tmp_path, boundary
):
    boundary.reference_status = "fit_error"
    _, report = run_case(tmp_path, boundary)
    assert report["reference"]["status"] == "fit_error"
    assert report["search_calls"] == 12
    assert all(record["status"] == "success" for record in report["assessments"])


@pytest.mark.parametrize(
    "mutation", ["software", "seeds", "profile", "input", "environment", "technical"]
)
def test_package_mismatches_abort_without_releasing_case(tmp_path, boundary, mutation):
    def mutate(case_id, arm, report):
        if arm != "known_covariance":
            return
        if mutation == "software":
            report["software"]["commit"] = "f" * 40
        elif mutation == "seeds":
            report["seeds"] = report["seeds"][::-1]
        elif mutation == "profile":
            report["profile"] = "other"
        elif mutation == "input":
            report["input_fingerprints"]["covariance"]["sha256"] = "f" * 64
        elif mutation == "environment":
            report["numerical_environment"]["threads"] = 2
        else:
            report["technical"] = True

    boundary.mutate_package = mutate
    with pytest.raises(ValueError):
        run_case(tmp_path, boundary)
    revoked(tmp_path / "case")


@pytest.mark.parametrize(
    "mutation",
    ["missing", "software", "unfinished", "environment", "iterations", "workers"],
)
def test_technical_gate_is_mandatory_before_first_search(tmp_path, boundary, mutation):
    path = boundary.technical / "completion" / publication.REPORT
    gate = read(path)
    if mutation == "missing":
        path.unlink()
    else:
        if mutation == "software":
            gate["software"]["commit"] = "0" * 40
        elif mutation == "unfinished":
            gate["status"] = "running"
        elif mutation == "environment":
            gate["numerical_environment"] = None
        elif mutation == "iterations":
            gate["requested_iterations"] = 9
        else:
            gate["completed_workers"] = 2
        _write_json(path, gate)
    with pytest.raises((ValueError, FileNotFoundError)):
        run_series(tmp_path, boundary)
    assert not boundary.events
    revoked(tmp_path / "series")


@pytest.mark.parametrize(
    "error",
    [
        ValueError("worker provenance"),
        RuntimeError("invocation guard"),
        KeyboardInterrupt(),
    ],
)
def test_native_integrity_and_interrupt_are_not_ordinary_package_failures(
    tmp_path, boundary, error
):
    boundary.fail_package = error
    with pytest.raises(type(error)):
        run_case(tmp_path, boundary)
    revoked(tmp_path / "case")


@pytest.mark.parametrize(
    "mutation", ["source", "published_summary", "state", "interrupt"]
)
def test_changes_after_publication_returns_revoke_case(
    tmp_path, boundary, monkeypatch, mutation
):
    original = publication.export_transaction

    def export(output, *args, **kwargs):
        report = original(output, *args, **kwargs)
        if Path(output) == tmp_path / "case/completion":
            assert not (Path(output) / publication.LOCK).exists()
            if mutation == "source":
                boundary.source.write_text("changed after publication")
            elif mutation == "published_summary":
                (Path(output) / publication.SUMMARY).write_text("changed")
            elif mutation == "state":
                _write_json(tmp_path / "case/run_state.json", {"status": "running"})
            else:
                handler = signal.getsignal(signal.SIGTERM)
                assert callable(handler)
                handler(signal.SIGTERM, None)
        return report

    monkeypatch.setattr(publication, "export_transaction", export)
    with pytest.raises((ValueError, InterruptedError)):
        run_case(tmp_path, boundary)
    revoked(tmp_path / "case")


@pytest.mark.parametrize("mutation", ["source", "interrupt"])
def test_last_unlock_is_still_within_revocable_boundary(
    tmp_path, boundary, monkeypatch, mutation
):
    original = Path.unlink
    changed = []

    def unlink(path, *args, **kwargs):
        result = original(path, *args, **kwargs)
        if path == tmp_path / "case/completion" / publication.LOCK and not changed:
            changed.append(mutation)
            if mutation == "source":
                boundary.source.write_text("changed at unlock")
            else:
                handler = signal.getsignal(signal.SIGINT)
                assert callable(handler)
                handler(signal.SIGINT, None)
        return result

    monkeypatch.setattr(Path, "unlink", unlink)
    with pytest.raises((ValueError, InterruptedError)):
        run_case(tmp_path, boundary)
    assert changed == [mutation]
    revoked(tmp_path / "case")


@pytest.mark.parametrize("mutation", ["source", "publication", "interrupt"])
def test_outer_signal_handler_teardown_is_still_revocable(
    tmp_path, boundary, monkeypatch, mutation
):
    original = signal.signal
    caller_handler = signal.getsignal(signal.SIGTERM)
    changed = []

    def restore(sig, handler):
        current = signal.getsignal(sig)
        result = original(sig, handler)
        if (
            sig == signal.SIGTERM
            and handler == caller_handler
            and getattr(current, "__qualname__", "").endswith(
                "_owned_run.<locals>.interrupted"
            )
            and not changed
        ):
            changed.append(mutation)
            assert (tmp_path / "case/completion" / publication.MANIFEST).exists()
            if mutation == "source":
                boundary.source.write_text("changed during handler teardown")
            elif mutation == "publication":
                (tmp_path / "case/completion" / publication.SUMMARY).write_text(
                    "changed during teardown"
                )
            else:
                raise InterruptedError("teardown interrupt")
        return result

    monkeypatch.setattr(signal, "signal", restore)
    with pytest.raises((ValueError, InterruptedError)):
        run_case(tmp_path, boundary)
    assert changed == [mutation]
    revoked(tmp_path / "case")


@pytest.mark.parametrize(
    "mutation", ["case", "case_timing", "series_timing", "extra", "partial_pairs"]
)
def test_read_verification_rejects_missing_inventory_timing_or_aggregate(
    tmp_path, boundary, mutation
):
    root, _ = run_series(tmp_path, boundary)
    before = list(boundary.events)
    if mutation == "case":
        (root / "cases/white-01/run_state.json").unlink()
    elif mutation == "case_timing":
        (root / "cases/white-01-call.json").unlink()
    elif mutation == "series_timing":
        pilot._timing_path(root).unlink()
    elif mutation == "extra":
        (root / "cases/extra.json").write_text("{}")
    else:
        completion = root / "completion"
        report = read(completion / publication.REPORT)
        report["assessments"].pop()
        for name, raw in pilot._publication_bytes(report).items():
            (completion / name).write_bytes(raw)
    with pytest.raises((ValueError, FileNotFoundError)):
        pilot.verify(boundary.preparation, boundary.technical, root)
    assert boundary.events == before


def test_verification_export_cannot_escape_late_source_change(
    tmp_path, boundary, monkeypatch
):
    root, _ = run_series(tmp_path, boundary)
    destination = tmp_path / "verification"
    original = publication.export_transaction

    def export(output, *args, **kwargs):
        result = original(output, *args, **kwargs)
        if Path(output) == destination / "completion":
            boundary.source.write_text("changed after verification publication")
        return result

    monkeypatch.setattr(publication, "export_transaction", export)
    with pytest.raises(ValueError):
        pilot.verify(boundary.preparation, boundary.technical, root, export=destination)
    revoked(destination)


@pytest.mark.parametrize(
    ("total", "member_field"),
    [
        ("wall_seconds", "adapter_call_wall_seconds"),
        ("cpu_user_seconds", "cpu_user_seconds"),
        ("cpu_system_seconds", "cpu_system_seconds"),
    ],
)
def test_zero_case_total_cannot_hide_known_member_work(
    tmp_path, boundary, monkeypatch, total, member_field
):
    def positive_cost(case_id, arm, report):
        report["members"][0]["costs"][member_field] = 1.0
        report["costs"][member_field] = 1.0

    boundary.mutate_package = positive_cost
    fixture_case_timing(monkeypatch, total, 4.0)
    root, _ = run_case(tmp_path, boundary)
    timing = read(pilot._timing_path(root))
    timing[total] = 0.0
    _write_json(pilot._timing_path(root), timing)
    consumed = publication.Consumption(publication.Deadline(60))
    with pytest.raises(ValueError, match="smaller than its contained work"):
        pilot._verify_case(
            root, boundary.prepared, boundary.prepared.cases["white-01"], consumed
        )


def test_known_member_costs_larger_than_case_calls_prevent_series_aggregate(
    tmp_path, boundary
):
    def impossible_cost(case_id, arm, report):
        report["members"][0]["costs"]["adapter_call_wall_seconds"] = 1000.0
        report["costs"]["adapter_call_wall_seconds"] = 1000.0

    boundary.mutate_package = impossible_cost
    with pytest.raises(ValueError, match="smaller than its contained work"):
        run_series(tmp_path, boundary)
    revoked(tmp_path / "series")


@pytest.mark.parametrize("field", ["cpu_user_seconds", "cpu_system_seconds"])
def test_unknown_failed_member_costs_remain_null_but_known_part_still_bounds_total(
    tmp_path, boundary, monkeypatch, field
):
    def partially_known(case_id, arm, report):
        report["members"][0]["costs"][field] = 0.25
        for member in report["members"][1:]:
            member["status"] = "timeout"
            member["costs"][field] = None
        report["costs"][field] = None

    boundary.mutate_package = partially_known
    fixture_case_timing(monkeypatch, field, 1.0)
    root, _ = run_case(tmp_path, boundary)
    timing_path = pilot._timing_path(root)
    timing = read(timing_path)
    timing[field] = 1.0
    _write_json(timing_path, timing)
    consumed = publication.Consumption(publication.Deadline(60))
    verified, verified_timing = pilot._verify_case(
        root, boundary.prepared, boundary.prepared.cases["white-01"], consumed
    )
    assert verified_timing[field] == 1.0
    assert verified_timing["cpu_scope"] == "self_plus_reaped_children"
    assert verified_timing["cpu_measurement_complete"] is False
    for package in verified["packages"].values():
        assert package["costs"][field] is None
        assert package["members"][0]["costs"][field] == 0.25
        assert all(m["costs"][field] is None for m in package["members"][1:])
    timing["cpu_measurement_complete"] = True
    _write_json(timing_path, timing)
    with pytest.raises(ValueError, match="inconsistent whole-call timing"):
        pilot._verify_case(
            root,
            boundary.prepared,
            boundary.prepared.cases["white-01"],
            publication.Consumption(publication.Deadline(60)),
        )
    timing["cpu_measurement_complete"] = False
    timing[field] = 0.0
    _write_json(timing_path, timing)
    with pytest.raises(ValueError, match="smaller than its contained work"):
        pilot._verify_case(
            root,
            boundary.prepared,
            boundary.prepared.cases["white-01"],
            publication.Consumption(publication.Deadline(60)),
        )


@pytest.mark.parametrize(
    "field", ["wall_seconds", "cpu_user_seconds", "cpu_system_seconds"]
)
def test_zero_series_total_cannot_hide_case_calls_or_publish_verification(
    tmp_path, boundary, field
):
    root, report = run_series(tmp_path, boundary)
    # These are real measured orchestration costs; native and fit work is mocked.
    assert sum(cost[field] for cost in report["case_call_costs"].values()) > 1e-6
    timing_path = pilot._timing_path(root)
    timing = read(timing_path)
    timing[field] = 0.0
    _write_json(timing_path, timing)
    destination = tmp_path / "invalid-cost-verification"
    with pytest.raises(ValueError, match="smaller than its contained work"):
        pilot.verify(boundary.preparation, boundary.technical, root, export=destination)
    revoked(destination)


def fixture_case_timing(monkeypatch, field, value):
    """Supply a controlled synthetic cost witness before real guarded publication.

    Unlike an impossible native cost, this permits creating a valid fixture
    first; tests then change the total alone to probe read-only containment.
    """
    original = pilot._call_record

    def measured(started, before, after, report_raw, kind):
        record = original(started, before, after, report_raw, kind)
        return {**record, field: value} if kind == "case" else record

    monkeypatch.setattr(pilot, "_call_record", measured)


@pytest.mark.parametrize(
    "field", ["wall_seconds", "cpu_user_seconds", "cpu_system_seconds"]
)
def test_late_inflated_timing_write_cannot_redefine_measured_cost(
    tmp_path, boundary, monkeypatch, field
):
    original = pilot._write_json
    changed = []

    def write(path, record):
        original(path, record)
        if (
            Path(path) == tmp_path / "case-call.json"
            and record["status"] == "completed"
        ):
            assert record[field] >= 0
            changed.append(field)
            # Inflation satisfies the inclusive lower bound, but contradicts the
            # exact measured record already constructed by the caller.
            original(path, {**record, field: record[field] + 10.0})

    monkeypatch.setattr(pilot, "_write_json", write)
    with pytest.raises(
        ValueError, match="Conflicting consumption snapshot|Consumed file changed"
    ):
        run_case(tmp_path, boundary)
    assert changed == [field]
    revoked(tmp_path / "case")
