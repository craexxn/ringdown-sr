"""Run the prospectively paired duration and sampling blocks without retries."""

import copy
import hashlib
import math
import signal
import time
from contextlib import ExitStack
from pathlib import Path

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import confirmed_search as search
from . import noise_followup_assessment as assessment
from . import noise_followup_diagnostics as diagnostics_module
from . import noise_followup_inputs as inputs
from . import noise_followup_technical as technical
from .confirmed_pilot import _read
from .confirmed_profile import COST_FIELDS
from .noise_pilot import _identity, _usage
from .pilot import _write_json

FORMAT = "ringdown-sr-noise-followup-series-1"
CASE_FORMAT = "ringdown-sr-noise-followup-case-1"
REGISTRATION_FORMAT = "ringdown-sr-noise-followup-registration-1"
CALL_FORMAT = "ringdown-sr-noise-followup-call-1"
CASE_COUNT = 26
CASE_SECONDS = {"duration": 33000, "sampling": 17400}
VERIFY_SECONDS = 14400
SUMMARY = (
    "# Getrennter Dauer-/Rastervergleich\n\n"
    "Originalauswahl jedes Viererpakets; neue Suchen und vorab gebundene "
    "gemeinsame Kontrollen werden getrennt gezählt. Keine automatische "
    "Schätzerwahl, keine Wiederholung eines abgebrochenen Workers.\n"
)
CALL_SCOPE = (
    "entry_through_publication_and_handler_teardown_"
    "excluding_call_write_and_final_rechecks"
)


def _block(block):
    if type(block) is not str or block not in CASE_SECONDS:
        raise ValueError("Block must be duration or sampling.")
    return block


def _arms(block):
    return inputs.ARMS_A if _block(block) == "duration" else inputs.ARMS_B


def _json(path, consumed):
    return sources.read_json(_read(path, consumed))


def _file_hash(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected a regular unchanged artifact file.")
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _tree_hashes(root, *, excluded=(), skip_directories=()):
    """Hash regular files with bounded memory; never retain large input bytes."""
    root = _identity(root)
    excluded, skip_directories = set(excluded), set(skip_directories)
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts[0] in skip_directories:
            continue
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Artifact trees contain only regular files/directories.")
        name = relative.as_posix()
        if path.is_file() and name not in excluded:
            result[name] = _file_hash(path)
    return result


def _hold_tree(root, consumed):
    expected = _tree_hashes(root)

    def unchanged():
        if _tree_hashes(root) != expected:
            raise ValueError("Consumed artifact tree changed.")

    consumed.callbacks.append(unchanged)
    return expected


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
        raise ValueError("Follow-up publication checksum or summary differs.")
    publication.verify_bytes(root, expected, locked=False)
    consumed.callbacks.append(
        lambda: publication.verify_bytes(root, expected, locked=False)
    )
    return report


def _export(output, report, frozen):
    output = publication.validate_output(output)
    expected = _publication_bytes(report)

    def build(consumed):
        consumed.callbacks.append(frozen.check)
        return report, SUMMARY, {}

    try:
        result = publication.export_transaction(output, build, seconds=VERIFY_SECONDS)
        frozen.callbacks.append(
            lambda: publication.verify_bytes(output, expected, locked=False)
        )
        frozen.check()
        return result
    except BaseException as error:
        if Path(output).is_dir():
            publication.revoke(Path(output), error, frozen.clock)
        raise


def _binding(prepared):
    return sources.sha256(sources.json_bytes(prepared.manifest))


def _input_hash(arrays):
    return sources.sha256(
        sources.json_bytes(
            {
                key: None if value is None else sources.fingerprint(value)
                for key, value in sorted(arrays.items())
            }
        )
    )


def _package_arrays(arrays):
    return search._arrays(
        arrays["time_s"], arrays["observed"], arrays.get("covariance")
    )


def _case_timing_path(root):
    return root.with_name(root.name + "-call.json")


def _costs_complete(packages):
    return all(
        package["costs"].get(name) is not None
        for package in packages
        for name in ("cpu_user_seconds", "cpu_system_seconds")
    )


def _timing(started, before, *, kind, status, source_report=None, error=None, **extra):
    after = _usage()
    return {
        "format": CALL_FORMAT,
        "kind": kind,
        "status": status,
        "scope": CALL_SCOPE,
        "cpu_scope": "self_plus_reaped_children",
        "wall_seconds": time.monotonic() - started,
        "cpu_user_seconds": sum(
            a.ru_utime - b.ru_utime for a, b in zip(after, before, strict=True)
        ),
        "cpu_system_seconds": sum(
            a.ru_stime - b.ru_stime for a, b in zip(after, before, strict=True)
        ),
        "source_report_sha256": source_report,
        "error": None if error is None else f"{type(error).__name__}: {error}",
        **extra,
    }


def _write_exclusive(path, record):
    with path.open("xb") as stream:
        stream.write(sources.json_bytes(record))


def _retain_failure(error, operation, label):
    try:
        operation()
    except BaseException as cleanup_error:  # noqa: BLE001 -- Preserve the initiating interruption.
        error.add_note(
            f"Could not retain {label}: {type(cleanup_error).__name__}: {cleanup_error}"
        )


def _validate_timing(record, *, kind):
    expected = {
        "format",
        "kind",
        "status",
        "scope",
        "cpu_scope",
        "wall_seconds",
        "cpu_user_seconds",
        "cpu_system_seconds",
        "source_report_sha256",
        "error",
        "cpu_measurement_complete",
        "block",
        *({"case"} if kind == "case" else {"new_case_ids", "reused_case_ids"}),
    }
    if (
        set(record) != expected
        or record.get("block") not in CASE_SECONDS
        or record.get("format") != CALL_FORMAT
        or record.get("kind") != kind
        or record.get("scope") != CALL_SCOPE
        or record.get("cpu_scope") != "self_plus_reaped_children"
        or record.get("status") not in {"completed", "paused", "aborted"}
        or type(record.get("cpu_measurement_complete")) is not bool
    ):
        raise ValueError("Invalid follow-up whole-call timing identity.")
    for name in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        value = record.get(name)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid measured follow-up call cost.")
    if (record["status"] == "aborted") != (record.get("error") is not None):
        raise ValueError("Contradictory follow-up call failure evidence.")
    digest = record["source_report_sha256"]
    if record["status"] == "completed":
        if (
            type(digest) is not str
            or len(digest) != 64
            or any(value not in "0123456789abcdef" for value in digest)
        ):
            raise ValueError("A completed call needs its publication hash.")
    elif digest is not None:
        raise ValueError("An incomplete call cannot certify a publication.")
    if record["status"] == "aborted" and (
        record["cpu_measurement_complete"]
        or type(record["error"]) is not str
        or not record["error"]
    ):
        raise ValueError("Aborted call costs must retain their incomplete scope.")


def _included_costs(timing, packages):
    for name, nested in (
        ("wall_seconds", "adapter_call_wall_seconds"),
        ("cpu_user_seconds", "cpu_user_seconds"),
        ("cpu_system_seconds", "cpu_system_seconds"),
    ):
        minimum = sum(
            package["costs"][nested]
            for package in packages
            if package["costs"].get(nested) is not None
        )
        if timing[name] + 1e-6 < minimum:
            raise ValueError("Whole-call costs are below their contained serial work.")


def _gates(prepared, technical_path, diagnostics, consumed):
    technical_guard = publication.Consumption(consumed.clock)
    diagnostic_guard = publication.Consumption(consumed.clock)
    technical_report = technical.verify(technical_path, consumed=technical_guard)
    diagnostic_report = diagnostics_module.verify(
        diagnostics, consumed=diagnostic_guard
    )
    consumed.callbacks.extend((technical_guard.check, diagnostic_guard.check))
    for label, report in (
        ("technical", technical_report),
        ("estimators", diagnostic_report),
    ):
        if report.get("status") != "completed":
            raise ValueError("Incomplete required follow-up gate: " + label)
        sources._same(
            report["software"],
            prepared.manifest["software"],
            "Gate and scientific preparation use different software: " + label,
        )
    if technical_report.get("numerical_environment") is None:
        raise ValueError("Technical preflight lacks its measured native environment.")
    return {
        "technical_report_sha256": sources.sha256(
            _read(Path(technical_path) / "completion" / publication.REPORT, consumed)
        ),
        "diagnostics_report_sha256": sources.sha256(
            _read(Path(diagnostics) / "completion" / publication.REPORT, consumed)
        ),
        "numerical_environment": technical_report["numerical_environment"],
    }


def _scientific(prepared):
    if (
        prepared.manifest.get("purpose") != "scientific"
        or prepared.manifest.get("technical") is not False
        or len(prepared.cases) != CASE_COUNT
    ):
        raise ValueError("Scientific blocks require their exact 26-case preparation.")


def _registration(prepared, block, gates, uniform_hash):
    return {
        "format": REGISTRATION_FORMAT,
        "block": block,
        "profile": search.PROFILE,
        "preparation_sha256": _binding(prepared),
        "software": prepared.manifest["software"],
        "case_order": list(prepared.cases),
        "new_conditions": list(_arms(block)),
        "control_conditions": list(inputs.ARMS_A[:2]) if block == "sampling" else [],
        "uniform_report_sha256": uniform_hash,
        "case_limit_seconds": CASE_SECONDS[block],
        "block_call_limit_seconds": CASE_COUNT * CASE_SECONDS[block] + VERIFY_SECONDS,
        "reuse_policy": "only_complete_verified_cases_no_worker_retry",
        **gates,
    }


def _not_run(case, condition):
    return {
        "package_status": "not_run",
        "selected_member": None,
        "selected_candidate": None,
        "selected_candidate_path": None,
        "planned_members": 4,
        "search_calls": 0,
        "members": [],
        "costs": dict.fromkeys(COST_FIELDS, 0.0),
        "numerical_environment": None,
        "reason": case.record["arm_status"][condition],
    }


def _package(root, prepared, case, condition, consumed):
    arrays = inputs.arm_arrays(prepared, case, condition)
    directory = root / "symbolic" / condition
    if case.record["arm_status"][condition] != "ready":
        if directory.exists():
            raise ValueError("An unavailable condition contains worker artifacts.")
        return _not_run(case, condition), None, arrays
    _hold_tree(directory, consumed)
    report = search.verify_confirmed_package(directory)
    if (
        report.get("technical") is not False
        or report.get("profile") != search.PROFILE
        or report.get("seeds") != case.spec["search_seeds"]
    ):
        raise ValueError("Package profile or seeds differ from its follow-up slot.")
    sources._same(
        report["software"],
        prepared.manifest["software"],
        "Package software differs from scientific preparation.",
    )
    sources._same(
        report["input_fingerprints"],
        search._fingerprints(_package_arrays(arrays)),
        "Package inputs or covariance differ from their assigned condition.",
    )
    raw = _read(directory / "completion" / publication.REPORT, consumed)
    return report, sources.sha256(raw), arrays


def _controls(uniform_case, uniform_hash):
    if uniform_case is None:
        return [], {}
    selected = {
        item["source_identity"]["condition"]: item
        for item in uniform_case["assessments"]
        if item["source_identity"]["condition"] in inputs.ARMS_A[:2]
    }
    if set(selected) != set(inputs.ARMS_A[:2]):
        raise ValueError("Missing predeclared uniform controls.")
    return [copy.deepcopy(selected[key]) for key in inputs.ARMS_A[:2]], {
        key: {
            "uniform_report_sha256": uniform_hash,
            "case_id": uniform_case["case"]["id"],
            "case_report_sha256": sources.sha256(
                _publication_bytes(uniform_case)[publication.REPORT]
            ),
            "package_sha256": selected[key]["source_identity"]["package_sha256"],
            "new_search_calls": 0,
        }
        for key in inputs.ARMS_A[:2]
    }


def _case_report(
    root, prepared, case, block, gates, consumed, uniform_case, uniform_hash
):
    ready = {arm for arm in _arms(block) if case.record["arm_status"][arm] == "ready"}

    def inventory():
        if {path.name for path in root.iterdir()} != {
            "run_state.json",
            "symbolic",
            "completion",
        } or any(path.is_symlink() for path in root.iterdir()):
            raise ValueError("Unexpected follow-up case inventory.")
        if {path.name for path in (root / "symbolic").iterdir()} != ready:
            raise ValueError("Follow-up condition inventory differs from preparation.")

    inventory()
    consumed.callbacks.append(inventory)
    sources._same(
        _json(root / "run_state.json", consumed),
        {"status": "completed", "case": case.spec["id"], "block": block},
        "Incomplete follow-up case state.",
    )
    records, references = _controls(uniform_case, uniform_hash)
    packages = {}
    environment = None
    for condition in _arms(block):
        package, digest, arrays = _package(root, prepared, case, condition, consumed)
        packages[condition] = package
        current = package.get("numerical_environment")
        if current is not None:
            sources._same(
                current,
                gates["numerical_environment"],
                "Scientific and technical numerical environments differ.",
            )
            environment = current
        selected = package["selected_member"]
        records.append(
            assessment.assess_package(
                package,
                arrays,
                amplitude=inputs.SIGNAL["amplitude"],
                source_identity={
                    "model": case.spec["noise_model"],
                    "block": case.spec["block"],
                    "condition": condition,
                    "grid": "jitter" if condition in inputs.ARMS_B else "uniform",
                    "package_sha256": digest,
                    "input_sha256": _input_hash(arrays),
                    "selected_member_path": None
                    if selected is None
                    else f"symbolic/{condition}/member-{selected + 1:02d}/result.json",
                },
            )
        )
    calls = sum(package["search_calls"] for package in packages.values())
    return {
        "format": CASE_FORMAT,
        "status": "completed",
        "block": block,
        "case": case.spec,
        "preparation_sha256": _binding(prepared),
        "software": prepared.manifest["software"],
        "preparation_record": case.record,
        "planned_new_search_calls": 4 * len(_arms(block)),
        "planned_new_outputs": len(_arms(block)),
        "new_search_calls": calls,
        "search_calls": calls,
        "reused_control_outputs": len(references),
        "packages": packages,
        "assessments": records,
        "control_references": references,
        "physical_parameter_match": "not_assessed",
        **gates,
        "numerical_environment": environment,
    }


def _case_timing(root, report, consumed):
    record = _json(_case_timing_path(root), consumed)
    _validate_timing(record, kind="case")
    if (
        record["status"] != "completed"
        or record["source_report_sha256"]
        != sources.sha256(_publication_bytes(report)[publication.REPORT])
        or record.get("block") != report["block"]
        or record.get("case") != report["case"]["id"]
        or record["cpu_measurement_complete"]
        != _costs_complete(report["packages"].values())
        or record["wall_seconds"] >= CASE_SECONDS[report["block"]]
    ):
        raise ValueError("Incomplete or unbound case-call timing.")
    _included_costs(record, report["packages"].values())
    return record


def _verify_case(
    root,
    prepared,
    case_id,
    block,
    gates,
    consumed,
    uniform_case=None,
    uniform_hash=None,
):
    root = _identity(root)
    # Case-local checks do not repeatedly stream every unrelated large input.
    local = publication.Consumption(consumed.clock)
    original = _released(root / "completion", local)
    case = inputs.read_case(prepared, case_id, local)
    report = _case_report(
        root, prepared, case, block, gates, local, uniform_case, uniform_hash
    )
    sources._same(original, report, "Case replay differs from its publication.")
    timing = _case_timing(root, report, local)
    local.check()
    consumed.callbacks.append(local.check)
    return report, timing


def _run_case(
    prepared, case_id, block, gates, output, uniform_case=None, uniform_hash=None
):
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError("An existing alarm must not be replaced.")
    started, before = time.monotonic(), _usage()
    root = publication.validate_output(output)
    timing_path = publication.validate_output(_case_timing_path(root))
    frozen = publication.Consumption(publication.Deadline(CASE_SECONDS[block]))
    root.mkdir(parents=True)
    (root / "symbolic").mkdir()
    report = None
    timing_written = False
    try:
        with ExitStack() as stack:
            _install_handlers(stack)
            case = inputs.read_case(prepared, case_id, frozen)
            _write_json(
                root / "run_state.json", {"status": "preparing", "case": case_id}
            )
            frozen.git_file.clear()
            for condition in _arms(block):
                frozen.check()
                _write_json(
                    root / "run_state.json",
                    {
                        "status": "running",
                        "case": case_id,
                        "condition": condition,
                        "block": block,
                    },
                )
                if case.record["arm_status"][condition] == "ready":
                    arrays = inputs.arm_arrays(prepared, case, condition)
                    search.run_confirmed_package(
                        arrays["time_s"],
                        arrays["observed"],
                        covariance=arrays.get("covariance"),
                        output=root / "symbolic" / condition,
                        seeds=case.spec["search_seeds"],
                    )
                    _hold_tree(root / "symbolic" / condition, frozen)
                frozen.check()
            _write_json(
                root / "run_state.json",
                {"status": "completed", "case": case_id, "block": block},
            )

            def build(consumed):
                consumed.callbacks.append(frozen.check)
                result = _case_report(
                    root,
                    prepared,
                    case,
                    block,
                    gates,
                    consumed,
                    uniform_case,
                    uniform_hash,
                )
                return result, SUMMARY, {}

            report = publication.export_transaction(
                root / "completion",
                build,
                seconds=max(0.001, CASE_SECONDS[block] - (time.monotonic() - started)),
            )
            expected = _publication_bytes(report)
            frozen.callbacks.append(
                lambda: publication.verify_bytes(
                    root / "completion", expected, locked=False
                )
            )
            frozen.check()
        frozen.check()
        timing = _timing(
            started,
            before,
            kind="case",
            status="completed",
            source_report=sources.sha256(expected[publication.REPORT]),
            cpu_measurement_complete=_costs_complete(report["packages"].values()),
            block=block,
            case=case_id,
        )
        _included_costs(timing, report["packages"].values())
        _write_exclusive(timing_path, timing)
        timing_written = True
        frozen.add(timing_path, sources.json_bytes(timing))
        _case_timing(root, report, frozen)
        frozen.check()
        return report, timing
    except BaseException as error:
        if (root / "completion").is_dir():
            publication.revoke(root / "completion", error, frozen.clock)
        _retain_failure(
            error,
            lambda error=error: _write_json(
                root / "run_state.json",
                {
                    "status": "aborted",
                    "case": case_id,
                    "block": block,
                    "error": f"{type(error).__name__}: {error}",
                },
            ),
            "aborted case state",
        )
        if timing_written or not timing_path.exists():
            _retain_failure(
                error,
                lambda error=error: (
                    _write_json if timing_written else _write_exclusive
                )(
                    timing_path,
                    _timing(
                        started,
                        before,
                        kind="case",
                        status="aborted",
                        error=error,
                        cpu_measurement_complete=False,
                        block=block,
                        case=case_id,
                    ),
                ),
                "aborted case-call costs",
            )
        raise


def _install_handlers(stack):
    def interrupted(signum, frame):
        raise InterruptedError("Follow-up interrupted by signal " + str(signum))

    for sig in (signal.SIGINT, signal.SIGTERM):
        previous = signal.signal(sig, interrupted)
        stack.callback(signal.signal, sig, previous)


def _root_inventory(root, *, complete):
    expected = {"registration.json", "run_state.json", "cases", "calls"}
    if complete:
        expected.add("completion")
    if {path.name for path in root.iterdir()} != expected:
        raise ValueError("Unexpected follow-up series inventory.")
    if any(path.is_symlink() for path in root.iterdir()):
        raise ValueError("Follow-up series paths cannot be symlinks.")


def _case_inventory(root, ids):
    expected = {name for case_id in ids for name in (case_id, case_id + "-call.json")}
    if {path.name for path in (root / "cases").iterdir()} != expected:
        raise ValueError("A case is incomplete or an unexpected case artifact exists.")


def _uniform(prepared, gates, block, uniform, consumed):
    if block == "duration":
        if uniform is not None:
            raise ValueError("The duration block cannot import historical controls.")
        return None, None, {}
    if uniform is None:
        raise ValueError(
            "The sampling block requires its completed paired duration block."
        )
    report, cases = _verify_bound(
        prepared, gates, _identity(uniform), "duration", None, None, {}, consumed
    )
    digest = sources.sha256(
        _read(Path(uniform) / "completion" / publication.REPORT, consumed)
    )
    return report, digest, cases


def _series_report(prepared, block, registration, case_reports, case_calls):
    records = [
        item for report in case_reports.values() for item in report["assessments"]
    ]
    return {
        "format": FORMAT,
        "status": "completed",
        "block": block,
        "technical": False,
        "software": prepared.manifest["software"],
        "preparation_sha256": _binding(prepared),
        "preparation_call": prepared.call,
        "registration_sha256": sources.sha256(sources.json_bytes(registration)),
        "technical_report_sha256": registration["technical_report_sha256"],
        "diagnostics_report_sha256": registration["diagnostics_report_sha256"],
        "uniform_report_sha256": registration["uniform_report_sha256"],
        "numerical_environment": registration["numerical_environment"],
        "planned_new_search_calls": CASE_COUNT * len(_arms(block)) * 4,
        "planned_new_outputs": CASE_COUNT * len(_arms(block)),
        "new_search_calls": sum(
            item["new_search_calls"] for item in case_reports.values()
        ),
        "search_calls": sum(item["new_search_calls"] for item in case_reports.values()),
        "reused_control_outputs": sum(
            item["reused_control_outputs"] for item in case_reports.values()
        ),
        "case_reports_sha256": {
            case_id: sources.sha256(_publication_bytes(report)[publication.REPORT])
            for case_id, report in case_reports.items()
        },
        "case_call_costs": case_calls,
        "control_references": {
            case_id: report["control_references"]
            for case_id, report in case_reports.items()
        },
        "cost_scope": "new case calls only; reused uniform controls have zero new calls and are never added twice; preparation, gates, plots and invocation costs remain separate inclusive scopes",
        "assessments": records,
        "summary": assessment.summary(records, block=block),
        "decision": "descriptive_paired_comparisons_no_automatic_method_selection",
    }


def _calls(root, consumed, *, final_report=None):
    directory = root / "calls"
    paths = sorted(directory.iterdir())
    if [path.name for path in paths] != [
        f"{index:04d}.json" for index in range(1, len(paths) + 1)
    ]:
        raise ValueError("Invocation cost history must be append-only and contiguous.")
    registration = _json(root / "registration.json", consumed)
    case_ids = set(registration["case_order"])
    records, previous_new = [], set()
    for path in paths:
        record = _json(path, consumed)
        _validate_timing(record, kind="series")
        if (
            type(record.get("new_case_ids")) is not list
            or type(record.get("reused_case_ids")) is not list
        ):
            raise ValueError("Invocation timing lacks case accounting.")
        all_ids = record["new_case_ids"] + record["reused_case_ids"]
        if (
            any(type(value) is not str or value not in case_ids for value in all_ids)
            or len(set(all_ids)) != len(all_ids)
            or record["block"] != registration["block"]
            or (
                record["status"] != "aborted"
                and record["wall_seconds"] >= registration["block_call_limit_seconds"]
            )
        ):
            raise ValueError(
                "Invocation timing differs from its registered case scope."
            )
        new_ids, reused_ids = (
            set(record["new_case_ids"]),
            set(record["reused_case_ids"]),
        )
        if (
            new_ids & previous_new
            or not reused_ids <= previous_new
            or (record["status"] != "aborted" and reused_ids != previous_new)
            or (record["status"] == "paused" and not new_ids)
        ):
            raise ValueError("Invocation history repeats or omits completed case work.")
        case_costs = []
        for case_id in record["new_case_ids"]:
            timing = _json(root / "cases" / (case_id + "-call.json"), consumed)
            _validate_timing(timing, kind="case")
            if (
                timing["status"] != "completed"
                or timing["case"] != case_id
                or timing["block"] != registration["block"]
            ):
                raise ValueError(
                    "Invocation claims an incomplete case as new completed work."
                )
            case_costs.append(timing)
        if record["status"] != "aborted" and record["cpu_measurement_complete"] != all(
            timing["cpu_measurement_complete"] for timing in case_costs
        ):
            raise ValueError("Invocation CPU completeness differs from its new cases.")
        for name in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
            if record[name] + 1e-6 < sum(timing[name] for timing in case_costs):
                raise ValueError("Invocation cost is below its newly executed cases.")
        previous_new.update(new_ids)
        if record["status"] == "completed" and (
            path != paths[-1] or previous_new != case_ids
        ):
            raise ValueError(
                "Completed invocation does not account for the whole block."
            )
        records.append(record)
    if {
        path.name for path in (root / "cases").iterdir() if path.is_dir()
    } != previous_new:
        raise ValueError(
            "Existing cases are incomplete or absent from invocation cost history."
        )
    if final_report is not None and (
        not records
        or records[-1]["status"] != "completed"
        or records[-1]["source_report_sha256"]
        != sources.sha256(_publication_bytes(final_report)[publication.REPORT])
    ):
        raise ValueError("The final invocation is not bound to the completed series.")
    return records


def run(
    preparation,
    technical_path,
    output,
    *,
    diagnostics,
    block="duration",
    uniform=None,
    max_cases=None,
):
    """Run new whole cases; reuse only complete verified cases, never workers."""
    block = _block(block)
    if max_cases is not None and (
        type(max_cases) is not int or not 1 <= max_cases <= CASE_COUNT
    ):
        raise ValueError("max_cases must be an integer between one and 26.")
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError("An existing alarm must not be replaced.")
    started, before = time.monotonic(), _usage()
    consumed = publication.Consumption(
        publication.Deadline(CASE_COUNT * CASE_SECONDS[block] + VERIFY_SECONDS)
    )
    prepared = inputs.verify_inputs(preparation, consumed)
    _scientific(prepared)
    gates = _gates(prepared, technical_path, diagnostics, consumed)
    uniform_report, uniform_hash, uniform_cases = _uniform(
        prepared, gates, block, uniform, consumed
    )
    registration = _registration(prepared, block, gates, uniform_hash)
    root = Path(output).absolute()
    if root.exists():
        root = _identity(root)
        complete = (root / "completion").exists()
        _root_inventory(root, complete=complete)
        sources._same(
            _json(root / "registration.json", consumed),
            registration,
            "Continuation registration differs from the fixed experiment.",
        )
        if complete:
            report, _ = _verify_bound(
                prepared,
                gates,
                root,
                block,
                uniform_report,
                uniform_hash,
                uniform_cases,
                consumed,
            )
            return report
        history = _calls(root, consumed)
    else:
        root = publication.validate_output(root)
        root.mkdir(parents=True)
        (root / "cases").mkdir()
        (root / "calls").mkdir()
        _write_json(root / "registration.json", registration)
        consumed.add(root / "registration.json", sources.json_bytes(registration))
        history = []
    call_path = root / "calls" / f"{len(history) + 1:04d}.json"
    case_reports, case_calls, new_ids, reused_ids = {}, {}, [], []
    state = {
        "status": "running",
        "block": block,
        "cases": [{"id": key, "status": "planned"} for key in prepared.cases],
    }
    report = None
    timing_written = False
    try:
        with ExitStack() as stack:
            _install_handlers(stack)
            known_ids = [
                entry["id"]
                for entry in state["cases"]
                if (root / "cases" / entry["id"]).exists()
            ]
            _case_inventory(root, known_ids)
            _write_json(root / "run_state.json", state)
            for entry in state["cases"]:
                case_id = entry["id"]
                case_root = root / "cases" / case_id
                controls = uniform_cases.get(case_id)
                if case_root.exists():
                    current, timing = _verify_case(
                        case_root,
                        prepared,
                        case_id,
                        block,
                        gates,
                        consumed,
                        controls,
                        uniform_hash,
                    )
                    reused_ids.append(case_id)
                elif max_cases is not None and len(new_ids) >= max_cases:
                    break
                else:
                    entry["status"] = "running"
                    state["current_case"] = case_id
                    _write_json(root / "run_state.json", state)
                    consumed.check()
                    current, timing = _run_case(
                        prepared,
                        case_id,
                        block,
                        gates,
                        case_root,
                        controls,
                        uniform_hash,
                    )
                    new_ids.append(case_id)
                case_reports[case_id], case_calls[case_id] = current, timing
                _hold_tree(case_root, consumed)
                _read(_case_timing_path(case_root), consumed)
                entry["status"] = "completed"
                state.pop("current_case", None)
                _write_json(root / "run_state.json", state)
                consumed.check()
            complete = len(case_reports) == CASE_COUNT
            state["status"] = "completed" if complete else "paused"
            _write_json(root / "run_state.json", state)
            if complete:
                report = _series_report(
                    prepared, block, registration, case_reports, case_calls
                )
                report = _export(root / "completion", report, consumed)
            consumed.check()
        timing = _timing(
            started,
            before,
            kind="series",
            status=state["status"],
            source_report=None
            if report is None
            else sources.sha256(_publication_bytes(report)[publication.REPORT]),
            cpu_measurement_complete=all(
                case_calls[key]["cpu_measurement_complete"] for key in new_ids
            ),
            block=block,
            new_case_ids=new_ids,
            reused_case_ids=reused_ids,
        )
        for name in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
            if timing[name] + 1e-6 < sum(case_calls[key][name] for key in new_ids):
                raise ValueError("Invocation cost is below its newly executed cases.")
        _write_exclusive(call_path, timing)
        timing_written = True
        consumed.add(call_path, sources.json_bytes(timing))
        _root_inventory(root, complete=report is not None)
        consumed.callbacks.append(
            lambda: _root_inventory(root, complete=report is not None)
        )
        consumed.callbacks.append(lambda: _case_inventory(root, list(case_reports)))
        _calls(root, consumed, final_report=report)
        consumed.check()
        return (
            report
            if report is not None
            else {
                "format": FORMAT,
                **state,
                "new_cases_this_call": len(new_ids),
                "scientific_completion": False,
            }
        )
    except BaseException as error:
        if (root / "completion").is_dir():
            publication.revoke(root / "completion", error, consumed.clock)
        state.update(status="aborted", error=f"{type(error).__name__}: {error}")
        _retain_failure(
            error,
            lambda: _write_json(root / "run_state.json", state),
            "aborted series state",
        )
        if timing_written or not call_path.exists():
            _retain_failure(
                error,
                lambda error=error: (
                    _write_json if timing_written else _write_exclusive
                )(
                    call_path,
                    _timing(
                        started,
                        before,
                        kind="series",
                        status="aborted",
                        error=error,
                        cpu_measurement_complete=False,
                        block=block,
                        new_case_ids=new_ids,
                        reused_case_ids=reused_ids,
                    ),
                ),
                "aborted series-call costs",
            )
        raise


def verify(
    preparation,
    technical_path,
    output,
    *,
    diagnostics,
    block=None,
    uniform=None,
    export=None,
    consumed=None,
):
    """Read-only replay of complete cases, paired controls, costs and aggregates."""
    root = _identity(output)
    external = consumed is not None
    if external and export is not None:
        raise ValueError("An externally guarded replay cannot create another export.")
    if consumed is None:
        consumed = publication.Consumption(publication.Deadline(VERIFY_SECONDS))
    original = _released(root / "completion", consumed)
    chosen_block = _block(original.get("block") if block is None else block)
    if original.get("format") != FORMAT or original.get("block") != chosen_block:
        raise ValueError("Wrong follow-up block format or identity.")
    prepared = inputs.verify_inputs(preparation, consumed)
    _scientific(prepared)
    gates = _gates(prepared, technical_path, diagnostics, consumed)
    uniform_report, uniform_hash, uniform_cases = _uniform(
        prepared, gates, chosen_block, uniform, consumed
    )
    report, _ = _verify_bound(
        prepared,
        gates,
        root,
        chosen_block,
        uniform_report,
        uniform_hash,
        uniform_cases,
        consumed,
    )
    if export is not None:
        return _export(export, report, consumed)
    return report


def _verify_bound(
    prepared,
    gates,
    root,
    chosen_block,
    uniform_report,
    uniform_hash,
    uniform_cases,
    consumed,
):
    """Replay with gates already verified in this invocation, retaining guards."""
    _root_inventory(root, complete=True)
    consumed.callbacks.append(lambda: _root_inventory(root, complete=True))
    original = _released(root / "completion", consumed)
    registration = _registration(prepared, chosen_block, gates, uniform_hash)
    sources._same(
        _json(root / "registration.json", consumed),
        registration,
        "Changed follow-up registration.",
    )
    ids = list(prepared.cases)
    _case_inventory(root, ids)
    consumed.callbacks.append(lambda: _case_inventory(root, ids))
    sources._same(
        _json(root / "run_state.json", consumed),
        {
            "status": "completed",
            "block": chosen_block,
            "cases": [{"id": key, "status": "completed"} for key in ids],
        },
        "Incomplete follow-up series state.",
    )
    reports, calls = {}, {}
    for case_id in ids:
        controls = uniform_cases.get(case_id)
        reports[case_id], calls[case_id] = _verify_case(
            root / "cases" / case_id,
            prepared,
            case_id,
            chosen_block,
            gates,
            consumed,
            controls,
            uniform_hash,
        )
    report = _series_report(prepared, chosen_block, registration, reports, calls)
    sources._same(
        original, report, "Recomputed follow-up series differs from its publication."
    )
    _calls(root, consumed, final_report=report)
    consumed.check()
    return report, reports
