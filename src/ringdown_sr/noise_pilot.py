"""Execute and read-verify the frozen 144-search noise pilot without reselection."""

import math
import resource
import signal
import time
from contextlib import ExitStack
from pathlib import Path

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import confirmed_search as search
from . import noise_pilot_assessment as assessment
from . import noise_pilot_inputs as inputs
from . import noise_pilot_reference as reference
from . import noise_pilot_technical as technical
from .confirmed_pilot import _read, _snapshot_tree
from .confirmed_profile import COST_FIELDS
from .pilot import _write_json

FORMAT = "ringdown-sr-noise-pilot-series-1"
CASE_FORMAT = "ringdown-sr-noise-pilot-case-1"
CASE_SECONDS = 25200
VERIFY_SECONDS = 14400
ARMS = assessment.ARMS
SUMMARY = (
    "# Begrenzter Rauschpilot\n\n"
    "Originalauswahl je Viererpaket; getrennte Gewichtungsarme und Rauschmodelle. "
    "Explorativer Pilot, keine neue Erfolgsgrenze oder automatische Armwahl.\n"
)


def _json(path, consumed):
    return sources.read_json(_read(path, consumed))


def _identity(path):
    path = Path(path).absolute()
    if path != path.resolve() or not path.is_dir():
        raise ValueError("Use an existing artifact directory without symlinks.")
    return path


def _inventory(root, names, consumed):
    def check():
        if root.is_symlink() or {p.name for p in root.iterdir()} != set(names):
            raise ValueError("Noise-pilot artifact inventory changed.")
        if any((root / name).is_symlink() for name in names):
            raise ValueError("Noise-pilot artifact symlinks are forbidden.")

    check()
    consumed.callbacks.append(check)


def _publication_bytes(report):
    documents = {
        publication.REPORT: sources.json_bytes({**report, "status": "completed"}),
        publication.SUMMARY: SUMMARY.encode(),
    }
    return {
        **documents,
        publication.MANIFEST: sources.json_bytes(
            {name: sources.sha256(raw) for name, raw in documents.items()}
        ),
    }


def _released(root, consumed):
    expected = {
        name: _read(root / name, consumed)
        for name in (publication.REPORT, publication.SUMMARY, publication.MANIFEST)
    }
    report = sources.read_json(expected[publication.REPORT])
    if expected != _publication_bytes(report):
        raise ValueError("Noise-pilot publication checksum or summary changed.")
    consumed.callbacks.append(
        lambda: publication.verify_bytes(root, expected, locked=False)
    )
    consumed.check()
    return report


def _export(output, assemble, initial, closing):
    def build(consumed):
        consumed.callbacks.append(initial.check)
        report = assemble(consumed)
        expected = _publication_bytes(report)
        closing.extend((consumed, expected))
        return report, SUMMARY, {}

    result = publication.export_transaction(output, build, seconds=VERIFY_SECONDS)
    closing[0].callbacks.append(
        lambda: publication.verify_bytes(output, closing[1], locked=False)
    )
    closing[0].check()
    return result


def _usage():
    return [
        resource.getrusage(kind)
        for kind in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)
    ]


def _timing_path(root):
    return root.with_name(root.name + "-call.json")


def _call_record(started, before, after, report_raw, kind):
    return {
        "format": FORMAT + "-call",
        "kind": kind,
        "status": "completed",
        "scope": "entry_through_publication_and_handler_teardown_excluding_timing_write_and_final_rechecks",
        "wall_seconds": time.monotonic() - started,
        "cpu_user_seconds": sum(
            a.ru_utime - b.ru_utime for a, b in zip(after, before, strict=True)
        ),
        "cpu_system_seconds": sum(
            a.ru_stime - b.ru_stime for a, b in zip(after, before, strict=True)
        ),
        "source_report_sha256": sources.sha256(report_raw),
        "cpu_scope": "self_plus_reaped_children",
        "cpu_measurement_complete": _cpu_complete(sources.read_json(report_raw), kind),
    }


def _cpu_complete(report, kind):
    if kind == "case":
        return all(
            member["costs"][key] is not None
            for package in report["packages"].values()
            if package["package_status"] != "not_run"
            for member in package["members"]
            for key in ("cpu_user_seconds", "cpu_system_seconds")
        )
    if kind == "series":
        return all(
            cost["cpu_measurement_complete"]
            for cost in report["case_call_costs"].values()
        )
    return True


def _inclusive_costs(timing, contained):
    """Reject impossible totals; ignore unknown components, never impute zero."""
    for target, source in (
        ("wall_seconds", "adapter_call_wall_seconds"),
        ("cpu_user_seconds", "cpu_user_seconds"),
        ("cpu_system_seconds", "cpu_system_seconds"),
    ):
        known = [
            record[source] for record in contained if record.get(source) is not None
        ]
        # A microsecond only accommodates cumulative OS-counter Float64 rounding.
        if known and timing[target] + 1e-6 < math.fsum(known):
            raise ValueError("Whole-call cost is smaller than its contained work.")


def _contained_costs(report, kind):
    if kind == "case":
        return [
            member["costs"]
            for package in report["packages"].values()
            if package["package_status"] != "not_run"
            for member in package["members"]
        ]
    if kind == "series":
        return [
            {**cost, "adapter_call_wall_seconds": cost["wall_seconds"]}
            for cost in report["case_call_costs"].values()
        ]
    return []


def _timing(root, consumed, *, kind):
    record = _json(_timing_path(root), consumed)
    if (
        set(record)
        != {
            "format",
            "kind",
            "status",
            "scope",
            "wall_seconds",
            "cpu_user_seconds",
            "cpu_system_seconds",
            "source_report_sha256",
            "cpu_scope",
            "cpu_measurement_complete",
        }
        or record["format"] != FORMAT + "-call"
        or record["kind"] != kind
        or record["status"] != "completed"
        or record["cpu_scope"] != "self_plus_reaped_children"
        or type(record["cpu_measurement_complete"]) is not bool
        or record["cpu_measurement_complete"]
        != _cpu_complete(
            _json(root / "completion" / publication.REPORT, consumed), kind
        )
        or record["scope"]
        != "entry_through_publication_and_handler_teardown_excluding_timing_write_and_final_rechecks"
        or record["source_report_sha256"]
        != sources.sha256(_read(root / "completion" / publication.REPORT, consumed))
    ):
        raise ValueError("Missing or inconsistent whole-call timing evidence.")
    for name in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        value = record[name]
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid measured whole-call cost.")
    return record


def _owned_run(output, operation, *, seconds, kind):
    """Keep cancellation and revocation through publication and handler teardown."""
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError("An existing alarm must not be replaced.")
    started, before = time.monotonic(), _usage()
    output = publication.validate_output(output)
    timing_path = publication.validate_output(_timing_path(output))
    clock = publication.Deadline(seconds)
    initial = publication.Consumption(clock)
    closing = []
    output.mkdir(parents=True)
    try:
        with ExitStack() as stack:

            def interrupted(signum, frame):
                raise InterruptedError(
                    "Noise pilot interrupted by signal " + str(signum)
                )

            for sig in (signal.SIGINT, signal.SIGTERM):
                previous = signal.signal(sig, interrupted)
                stack.callback(signal.signal, sig, previous)
            report = operation(output, initial, closing)
            initial.check()
            closing[0].check()
        initial.check()
        closing[0].check()
        after = _usage()
        timing = _call_record(
            started, before, after, closing[1][publication.REPORT], kind
        )
        initial.add(timing_path, sources.json_bytes(timing))
        _write_json(timing_path, timing)
        _inclusive_costs(
            _timing(output, initial, kind=kind), _contained_costs(report, kind)
        )
        initial.check()
        closing[0].check()
        return report
    except BaseException as error:
        completion = output / "completion"
        if completion.is_dir():
            publication.revoke(completion, error, clock)
        _write_json(
            output / "run_state.json",
            {
                "status": "aborted",
                "error": f"{type(error).__name__}: {error}",
            },
        )
        after = _usage()
        _write_json(
            timing_path,
            {
                "format": FORMAT + "-call",
                "kind": kind,
                "status": "aborted",
                "scope": "entry_through_abort_excluding_failure_record_write",
                "cpu_scope": "self_plus_reaped_children",
                "cpu_measurement_complete": False,
                "wall_seconds": time.monotonic() - started,
                "cpu_user_seconds": sum(
                    a.ru_utime - b.ru_utime for a, b in zip(after, before, strict=True)
                ),
                "cpu_system_seconds": sum(
                    a.ru_stime - b.ru_stime for a, b in zip(after, before, strict=True)
                ),
                "error": f"{type(error).__name__}: {error}",
            },
        )
        raise


def _binding(prepared):
    return sources.sha256(sources.json_bytes(prepared.manifest))


def _arrays(prepared, case):
    return {**prepared.common, **case.arrays}


def _input_hash(arrays):
    return sources.sha256(
        sources.json_bytes(
            {key: sources.fingerprint(value) for key, value in sorted(arrays.items())}
        )
    )


def _covariance(arrays, arm):
    if arm == "ordinary":
        return None
    return arrays[
        "covariance_true" if arm == "known_covariance" else "covariance_estimated"
    ]


def _not_run(case, arm):
    return {
        "package_status": "not_run",
        "selected_candidate": None,
        "selected_member": None,
        "search_calls": 0,
        "costs": {name: None for name in COST_FIELDS},
        "members": [
            {"status": "not_run", "seed": seed, "reason": case.record["status"]}
            for seed in case.spec["search_seeds"]
        ],
        "reason": case.record["status"],
        "arm": arm,
    }


def _package(root, arm, prepared, case, consumed):
    arrays = _arrays(prepared, case)
    if case.record["arm_status"][arm] == "not_run":
        if (root / "symbolic" / arm).exists():
            raise ValueError(
                "An unexecutable arm contains unexpected worker artifacts."
            )
        return _not_run(case, arm), None
    directory = root / "symbolic" / arm
    _snapshot_tree(directory, consumed)
    report = search.verify_confirmed_package(directory)
    covariance = _covariance(arrays, arm)
    expected_arrays = {"time_s": arrays["time_s"], "observed": arrays["observed"]}
    if covariance is not None:
        expected_arrays["covariance"] = covariance
    if (
        report["technical"] is not False
        or report["profile"] != search.PROFILE
        or report["seeds"] != case.spec["search_seeds"]
    ):
        raise ValueError("Package profile or seeds differ from the frozen pilot.")
    sources._same(
        report["software"],
        prepared.manifest["software"],
        "Package execution software differs from shared preparation.",
    )
    sources._same(
        report["input_fingerprints"],
        {key: sources.fingerprint(value) for key, value in expected_arrays.items()},
        "Package data or covariance differ from the assigned arm.",
    )
    raw = _read(directory / "completion" / publication.REPORT, consumed)
    consumed.check()
    return report, sources.sha256(raw)


def _case_report(root, prepared, case, consumed):
    _inventory(
        root, {"run_state.json", "reference.json", "symbolic", "completion"}, consumed
    )
    ready = {arm for arm in ARMS if case.record["arm_status"][arm] == "ready"}
    _inventory(root / "symbolic", ready, consumed)
    sources._same(
        _json(root / "run_state.json", consumed),
        {"status": "completed", "case": case.spec["id"]},
        "Incomplete noise-pilot case state.",
    )
    arrays = _arrays(prepared, case)
    reference_record = _json(root / "reference.json", consumed)
    if case.record["status"] == "data_failed":
        sources._same(
            reference_record,
            {"status": "not_run", "reason": "data_failed"},
            "Invalid unavailable-reference record.",
        )
    else:
        reference.verify_reference(reference_record, arrays)
    records, packages, environment = [], {}, None
    for arm in ARMS:
        package, digest = _package(root, arm, prepared, case, consumed)
        packages[arm] = package
        current = package.get("numerical_environment")
        if current is not None:
            if environment is not None:
                sources._same(
                    environment, current, "Weighting-arm numerical environments differ."
                )
            environment = current
        selected = package["selected_member"]
        records.append(
            assessment.assess_package(
                package,
                None if case.record["status"] == "data_failed" else arrays,
                amplitude=inputs.SIGNAL["amplitude"],
                source_identity={
                    "model": case.spec["noise_model"],
                    "block": case.spec["block"],
                    "arm": arm,
                    "package_sha256": digest,
                    "input_sha256": _input_hash(arrays),
                    "selected_member_path": None
                    if selected is None
                    else f"symbolic/{arm}/member-{selected + 1:02d}/result.json",
                },
            )
        )
    return {
        "format": CASE_FORMAT,
        "status": "completed",
        "case": case.spec,
        "preparation_sha256": _binding(prepared),
        "preparation_call": prepared.call,
        "software": prepared.manifest["software"],
        "preparation_record": case.record,
        "reference": reference_record,
        "planned_search_calls": 12,
        "planned_outputs": 3,
        "search_calls": sum(package["search_calls"] for package in packages.values()),
        "packages": packages,
        "assessments": records,
        "numerical_environment": environment,
        "physical_parameter_match": "not_assessed",
    }


def _run_case(preparation, case_id, output):
    def operation(root, consumed, closing):
        prepared = inputs.verify_inputs(preparation, consumed)
        case = prepared.cases[case_id]
        if prepared.manifest["technical"] is not False:
            raise ValueError(
                "Scientific cases require the full scientific preparation."
            )
        (root / "symbolic").mkdir()
        _write_json(root / "run_state.json", {"status": "preparing", "case": case_id})
        arrays = _arrays(prepared, case)
        reference_record = (
            {"status": "not_run", "reason": "data_failed"}
            if case.record["status"] == "data_failed"
            else reference.fit_reference(arrays)
        )
        consumed.add(root / "reference.json", sources.json_bytes(reference_record))
        _write_json(root / "reference.json", reference_record)
        consumed.check()
        consumed.git_file.clear()
        for arm in ARMS:
            consumed.check()
            _write_json(
                root / "run_state.json",
                {"status": "running", "case": case_id, "arm": arm},
            )
            if case.record["arm_status"][arm] == "ready":
                search.run_confirmed_package(
                    arrays["time_s"],
                    arrays["observed"],
                    covariance=_covariance(arrays, arm),
                    output=root / "symbolic" / arm,
                    seeds=case.spec["search_seeds"],
                )
                _snapshot_tree(root / "symbolic" / arm, consumed)
            consumed.check()
        _write_json(root / "run_state.json", {"status": "completed", "case": case_id})
        return _export(
            root / "completion",
            lambda closing_consumed: _case_report(
                root, prepared, case, closing_consumed
            ),
            consumed,
            closing,
        )

    return _owned_run(output, operation, seconds=CASE_SECONDS, kind="case")


def _verify_case(root, prepared, case, consumed):
    root = _identity(root)
    original = _released(root / "completion", consumed)
    report = _case_report(root, prepared, case, consumed)
    sources._same(
        original, report, "Recomputed case differs from its original publication."
    )
    timing = _timing(root, consumed, kind="case")
    _inclusive_costs(timing, _contained_costs(report, "case"))
    if timing["wall_seconds"] >= CASE_SECONDS:
        raise ValueError("Scientific case exceeded the frozen operational deadline.")
    consumed.check()
    return report, timing


def _technical_gate(path, prepared, consumed):
    report = technical.verify(path, consumed=consumed)
    sources._same(
        report["software"],
        prepared.manifest["software"],
        "Technical preflight and scientific preparation use different software.",
    )
    if report["status"] != "completed" or report["numerical_environment"] is None:
        raise ValueError("A completed N128 technical preflight is required.")
    return report


def _series_report(root, preparation, technical_path, consumed):
    _inventory(root, {"run_state.json", "cases", "completion"}, consumed)
    prepared = inputs.verify_inputs(preparation, consumed)
    if prepared.manifest["technical"] is not False or len(prepared.cases) != 12:
        raise ValueError(
            "The scientific series requires exactly twelve prepared cases."
        )
    gate = _technical_gate(technical_path, prepared, consumed)
    ids = list(prepared.cases)
    _inventory(
        root / "cases",
        {name for case_id in ids for name in (case_id, case_id + "-call.json")},
        consumed,
    )
    sources._same(
        _json(root / "run_state.json", consumed),
        {
            "status": "completed",
            "cases": [{"id": case_id, "status": "completed"} for case_id in ids],
        },
        "Scientific case inventory is incomplete.",
    )
    records, case_reports, call_costs = [], {}, {}
    for case_id, case in prepared.cases.items():
        report, timing = _verify_case(
            root / "cases" / case_id, prepared, case, consumed
        )
        if report["numerical_environment"] is not None:
            sources._same(
                report["numerical_environment"],
                gate["numerical_environment"],
                "Scientific and technical numerical environments differ.",
            )
        records.extend(report["assessments"])
        case_reports[case_id] = sources.sha256(
            _read(
                root / "cases" / case_id / "completion" / publication.REPORT, consumed
            )
        )
        call_costs[case_id] = timing
    return {
        "format": FORMAT,
        "status": "completed",
        "technical": False,
        "planned_search_calls": 144,
        "planned_algorithm_outputs": 36,
        "search_calls": sum(record["search_calls"] for record in records),
        "preparation_sha256": _binding(prepared),
        "preparation_call": prepared.call,
        "software": prepared.manifest["software"],
        "technical_report_sha256": sources.sha256(
            _read(Path(technical_path) / "completion" / publication.REPORT, consumed)
        ),
        "numerical_environment": gate["numerical_environment"],
        "case_reports_sha256": case_reports,
        "case_call_costs": call_costs,
        "cost_scope": "case calls include their members, reference fits and closing checks; common preparation and technical preflight are separate, never add contained times twice",
        "assessments": records,
        "summary": assessment.summary(records),
        "decision": "descriptive_pilot_requires_separate_followup_plan",
    }


def run(preparation, technical_path, output):
    """Run all twelve cases in the frozen order, without automatic replacement."""

    def operation(root, consumed, closing):
        prepared = inputs.verify_inputs(preparation, consumed)
        if prepared.manifest["technical"] is not False or len(prepared.cases) != 12:
            raise ValueError(
                "The pilot requires its twelve-case scientific preparation."
            )
        _technical_gate(technical_path, prepared, consumed)
        (root / "cases").mkdir()
        state = {
            "status": "running",
            "cases": [{"id": key, "status": "planned"} for key in prepared.cases],
        }
        _write_json(root / "run_state.json", state)
        consumed.git_file.clear()
        for entry in state["cases"]:
            consumed.check()
            entry["status"] = "running"
            _write_json(root / "run_state.json", state)
            _run_case(preparation, entry["id"], root / "cases" / entry["id"])
            _snapshot_tree(root / "cases" / entry["id"], consumed)
            _read(root / "cases" / (entry["id"] + "-call.json"), consumed)
            consumed.check()
            entry["status"] = "completed"
            _write_json(root / "run_state.json", state)
        state["status"] = "completed"
        _write_json(root / "run_state.json", state)
        return _export(
            root / "completion",
            lambda closing_consumed: _series_report(
                root, preparation, technical_path, closing_consumed
            ),
            consumed,
            closing,
        )

    return _owned_run(
        output, operation, seconds=12 * CASE_SECONDS + VERIFY_SECONDS, kind="series"
    )


def verify(preparation, technical_path, output, *, export=None):
    """Read-only replay of every original package, diagnosis and series aggregate."""
    root = _identity(output)
    consumed = publication.Consumption(publication.Deadline(VERIFY_SECONDS))

    def assemble(checks):
        original = _released(root / "completion", checks)
        report = _series_report(root, preparation, technical_path, checks)
        sources._same(
            report, original, "Recomputed scientific series differs from publication."
        )
        timing = _timing(root, checks, kind="series")
        _inclusive_costs(timing, _contained_costs(report, "series"))
        checks.check()
        return report

    if export is None:
        with consumed.clock.active():
            report = assemble(consumed)
            consumed.check()
        consumed.check()
        return report

    def operation(destination, checks, closing):
        _write_json(
            destination / "run_state.json",
            {"status": "completed", "mode": "read_only_verification"},
        )
        return _export(destination / "completion", assemble, checks, closing)

    return _owned_run(export, operation, seconds=VERIFY_SECONDS, kind="verification")
