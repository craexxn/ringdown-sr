"""Run the frozen main study in two ordered, independently released sections."""

import math
import signal
import time
from contextlib import ExitStack
from pathlib import Path

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import confirmed_search as search
from . import main_study_assessment as assessment
from . import main_study_inputs as inputs
from . import main_study_technical as technical
from .confirmed_pilot import _read
from .confirmed_profile import COST_FIELDS
from .noise_followup import _input_hash, _tree_hashes
from .noise_pilot import _identity, _usage
from .pilot import _write_json

FORMAT = "ringdown-sr-main-study-section-2"
CASE_FORMAT = "ringdown-sr-main-study-case-2"
REGISTRATION_FORMAT = "ringdown-sr-main-study-registration-2"
CALL_FORMAT = "ringdown-sr-main-study-call-1"
SIGNALS = ("signal_200_4ms", "signal_250_6ms")
ARMS = ("ordinary", "known_covariance", "estimated_64s", "estimated_4096s")
CASE_COUNT = 40
TOTAL_CASE_COUNT = 80
CASE_SECONDS = 33000
VERIFY_SECONDS = 14400
SECTION_SECONDS = CASE_COUNT * CASE_SECONDS + VERIFY_SECONDS
SUMMARY = (
    "# Hauptstudie zur Hintergrunddauer\n\n"
    "Unveränderte Trainingsverlust-Auswahl jedes Viererpakets. Kurvenfehler, "
    "Originalfamilie, Domain und Kosten bleiben getrennt; keine automatische "
    "Methodenwahl, keine Ersatzseeds und kein Wiederanlauf abgebrochener Abschnitte.\n"
)
CALL_SCOPE = (
    "entry_through_publication_and_handler_teardown_"
    "excluding_call_write_and_final_rechecks"
)


def _signal_id(value):
    if type(value) is not str or value not in SIGNALS:
        raise ValueError("Unknown frozen main-study signal section.")
    return value


def _json(path, consumed):
    return sources.read_json(_read(path, consumed))


def _hold_tree(root, consumed):
    expected = _tree_hashes(root)

    def unchanged():
        if _tree_hashes(root) != expected:
            raise ValueError("Consumed main-study artifact tree changed.")

    consumed.callbacks.append(unchanged)
    return expected


def _binding(prepared):
    return sources.sha256(sources.json_bytes(prepared.manifest))


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
        raise ValueError("Main-study publication checksum or summary differs.")
    publication.verify_bytes(root, expected, locked=False)
    consumed.callbacks.append(
        lambda: publication.verify_bytes(root, expected, locked=False)
    )
    return report


def _export(output, report, frozen):
    expected = _publication_bytes(report)
    owned = False

    def build(consumed):
        nonlocal owned
        owned = True
        consumed.callbacks.append(frozen.check)
        return report, SUMMARY, {}

    try:
        result = publication.export_transaction(
            output,
            build,
            seconds=max(
                0.001, frozen.clock.seconds - (time.monotonic() - frozen.clock.started)
            ),
        )
        frozen.callbacks.append(
            lambda: publication.verify_bytes(Path(output), expected, locked=False)
        )
        frozen.check()
        return result
    except BaseException as error:
        if owned:
            publication.revoke(Path(output), error, frozen.clock)
        raise


def _call_path(root):
    return root.with_name(root.name + "-call.json")


def _separate(output, originals):
    """Keep both output and cost sidecar outside every consumed source tree."""
    for candidate in (Path(output).absolute(), _call_path(Path(output).absolute())):
        for original in originals:
            if original is None:
                continue
            source = Path(original).absolute().resolve()
            if candidate.is_relative_to(source) or source.is_relative_to(candidate):
                raise ValueError(
                    "Main-study output must be separate from consumed originals."
                )


def _write_exclusive(path, value):
    with path.open("xb") as stream:
        stream.write(sources.json_bytes(value))


def _safe_update(path, value):
    if (
        path.is_symlink()
        or path.absolute() != path.resolve()
        or path.with_suffix(path.suffix + ".tmp").is_symlink()
    ):
        raise ValueError("Cannot update a redirected call artifact.")
    _write_json(path, value)


def _retain_failure(error, operation, label):
    try:
        operation()
    except BaseException as cleanup_error:  # noqa: BLE001 -- Preserve the initiating failure.
        error.add_note(
            f"Could not retain {label}: {type(cleanup_error).__name__}: {cleanup_error}"
        )


def _timing(
    started,
    before,
    *,
    kind,
    signal_id,
    status,
    report=None,
    error=None,
    cpu_measurement_complete=False,
    case_id=None,
    new_case_ids=(),
):
    after = _usage()
    return {
        "format": CALL_FORMAT,
        "kind": kind,
        "signal_id": signal_id,
        "case_id": case_id,
        "new_case_ids": list(new_case_ids),
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
        "source_report_sha256": None
        if report is None
        else sources.sha256(_publication_bytes(report)[publication.REPORT]),
        "error": None if error is None else f"{type(error).__name__}: {error}",
        "cpu_measurement_complete": cpu_measurement_complete,
    }


def _validate_timing(record, *, kind, signal_id, report, case_id=None, ids=()):
    keys = {
        "format",
        "kind",
        "signal_id",
        "case_id",
        "new_case_ids",
        "status",
        "scope",
        "cpu_scope",
        "wall_seconds",
        "cpu_user_seconds",
        "cpu_system_seconds",
        "source_report_sha256",
        "error",
        "cpu_measurement_complete",
    }
    if (
        set(record) != keys
        or record["format"] != CALL_FORMAT
        or record["kind"] != kind
        or record["signal_id"] != signal_id
        or record["case_id"] != case_id
        or record["new_case_ids"] != list(ids)
        or record["status"] != "completed"
        or record["scope"] != CALL_SCOPE
        or record["cpu_scope"] != "self_plus_reaped_children"
        or record["error"] is not None
        or type(record["cpu_measurement_complete"]) is not bool
        or record["source_report_sha256"]
        != sources.sha256(_publication_bytes(report)[publication.REPORT])
    ):
        raise ValueError("Incomplete or unbound main-study call costs.")
    for name in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        value = record[name]
        if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid measured main-study call cost.")
    limit = (
        CASE_SECONDS
        if kind == "case"
        else SECTION_SECONDS
        if kind == "section"
        else VERIFY_SECONDS
    )
    if record["wall_seconds"] >= limit:
        raise ValueError("Completed call exceeded its predeclared deadline.")


def _costs_complete(packages):
    return all(
        package["costs"].get(name) is not None
        for package in packages
        for name in ("cpu_user_seconds", "cpu_system_seconds")
    )


def _included_costs(timing, records, *, package=False):
    for name in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        nested = (
            "adapter_call_wall_seconds" if package and name == "wall_seconds" else name
        )
        minimum = sum(
            values[nested]
            for record in records
            if (values := record["costs"] if package else record).get(nested)
            is not None
        )
        if timing[name] + 1e-6 < minimum:
            raise ValueError("Whole-call cost is below its contained serial work.")


def _install_handlers(stack):
    def interrupted(signum, frame):
        raise InterruptedError("Main study interrupted by signal " + str(signum))

    for sig in (signal.SIGINT, signal.SIGTERM):
        previous = signal.signal(sig, interrupted)
        stack.callback(signal.signal, sig, previous)


def _scientific(prepared):
    expected = inputs.case_specs(purpose="scientific")
    if (
        prepared.manifest.get("purpose") != "scientific"
        or prepared.manifest.get("technical") is not False
        or len(prepared.cases) != TOTAL_CASE_COUNT
        or list(prepared.cases.values()) != list(expected)
    ):
        raise ValueError(
            "Main sections require the exact complete 80-case preparation."
        )


def _section_ids(prepared, signal_id):
    _signal_id(signal_id)
    ids = [
        key for key, spec in prepared.cases.items() if spec["signal_id"] == signal_id
    ]
    if len(ids) != CASE_COUNT:
        raise ValueError("A main signal section requires exactly 40 planned cases.")
    return ids


def _arm_order(prepared, case_id):
    spec = prepared.cases[case_id]
    position = _section_ids(prepared, spec["signal_id"]).index(case_id)
    shift = position % len(ARMS)
    return ARMS[shift:] + ARMS[:shift]


def _gates(prepared, technical_path, consumed):
    local = publication.Consumption(consumed.clock)
    report = technical.verify(technical_path, consumed=local)
    consumed.callbacks.append(local.check)
    if (
        report.get("status") != "completed"
        or report.get("prediction_failure_policy") != search.WIDTH_POLICY
        or report.get("n_samples") != 103
        or report.get("niterations") != 10
        or report.get("search_calls") != 8
        or report.get("numerical_environment") is None
    ):
        raise ValueError("Main study needs its complete eight-worker N103 preflight.")
    sources._same(
        report["software"],
        prepared.manifest["software"],
        "Gate and scientific preparation use different software.",
    )
    return {
        "technical_report_sha256": sources.sha256(
            _read(Path(technical_path) / "completion" / publication.REPORT, consumed)
        ),
        "numerical_environment": report["numerical_environment"],
    }


def _previous(prepared, gates, signal_id, previous, consumed):
    if signal_id == SIGNALS[0]:
        if previous is not None:
            raise ValueError("The first signal cannot import a previous section.")
        return None
    if previous is None:
        raise ValueError("The second signal needs the completed first signal section.")
    report = _verify_bound(
        prepared, gates, _identity(previous), SIGNALS[0], None, consumed
    )
    return sources.sha256(_publication_bytes(report)[publication.REPORT])


def _registration(prepared, signal_id, gates, previous_hash):
    ids = _section_ids(prepared, signal_id)
    return {
        "format": REGISTRATION_FORMAT,
        "signal_id": signal_id,
        "profile": search.PROFILE,
        "prediction_failure_policy": search.WIDTH_POLICY,
        "preparation_sha256": _binding(prepared),
        "software": prepared.manifest["software"],
        "full_study_case_order": list(prepared.cases),
        "case_order": ids,
        "arm_order": {case_id: list(_arm_order(prepared, case_id)) for case_id in ids},
        "case_limit_seconds": CASE_SECONDS,
        "section_limit_seconds": SECTION_SECONDS,
        "previous_section_report_sha256": previous_hash,
        "continuation_policy": "only_completed_sections_read_only_no_partial_section_resume",
        **gates,
    }


def _not_run(case, arm):
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
        "reason": case.record["arm_status"][arm],
    }


def _package(root, prepared, case, arm, consumed):
    arrays = inputs.arm_arrays(prepared, case, arm)
    directory = root / "symbolic" / arm
    if case.record["arm_status"][arm] != "ready":
        if directory.exists() or directory.is_symlink():
            raise ValueError("An unavailable condition contains worker artifacts.")
        return _not_run(case, arm), None, arrays
    _hold_tree(directory, consumed)
    report = search.verify_confirmed_package(directory)
    if (
        report.get("technical") is not False
        or report.get("prediction_failure_policy") != search.WIDTH_POLICY
        or report.get("profile") != search.PROFILE
        or report.get("seeds") != case.spec["search_seeds"]
    ):
        raise ValueError(
            "Package policy, profile or seeds differ from its main-study slot."
        )
    sources._same(
        report["software"],
        prepared.manifest["software"],
        "Package software differs from preparation.",
    )
    sources._same(
        report["input_fingerprints"],
        search._fingerprints(
            search._arrays(
                arrays["time_s"], arrays["observed"], arrays.get("covariance")
            )
        ),
        "Package inputs or covariance differ from their assigned condition.",
    )
    raw = _read(directory / "completion" / publication.REPORT, consumed)
    return report, sources.sha256(raw), arrays


def _case_report(root, prepared, case, gates, consumed):
    case_id = case.spec["id"]
    signal_id = case.spec["signal_id"]
    ready = {arm for arm in ARMS if case.record["arm_status"][arm] == "ready"}

    def inventory():
        if {p.name for p in root.iterdir()} != {
            "run_state.json",
            "symbolic",
            "completion",
        } or any(p.is_symlink() for p in root.iterdir()):
            raise ValueError("Unexpected main-study case inventory.")
        if {p.name for p in (root / "symbolic").iterdir()} != ready:
            raise ValueError("Case arm inventory differs from preparation.")

    inventory()
    consumed.callbacks.append(inventory)
    sources._same(
        _json(root / "run_state.json", consumed),
        {"status": "completed", "case": case_id, "signal_id": signal_id},
        "Incomplete main-study case state.",
    )
    packages, records = {}, []
    for arm in ARMS:
        package, digest, arrays = _package(root, prepared, case, arm, consumed)
        packages[arm] = package
        if package.get("numerical_environment") is not None:
            sources._same(
                package["numerical_environment"],
                gates["numerical_environment"],
                "Scientific and technical numerical environments differ.",
            )
        selected = package["selected_member"]
        records.append(
            assessment.assess_package(
                package,
                arrays,
                amplitude=case.spec["signal"]["amplitude"],
                source_identity={
                    "signal_id": signal_id,
                    "case_id": case_id,
                    "model": case.spec["noise_model"],
                    "block": case.spec["block"],
                    "condition": arm,
                    "grid": "uniform",
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
        "prediction_failure_policy": search.WIDTH_POLICY,
        "status": "completed",
        "signal_id": signal_id,
        "case": case.spec,
        "preparation_sha256": _binding(prepared),
        "software": prepared.manifest["software"],
        "technical_report_sha256": gates["technical_report_sha256"],
        "numerical_environment": gates["numerical_environment"],
        "arm_order": list(_arm_order(prepared, case_id)),
        "planned_search_calls": 16,
        "search_calls": sum(p["search_calls"] for p in packages.values()),
        "packages": packages,
        "assessments": records,
    }


def _case_timing(root, report, consumed):
    timing = _json(_call_path(root), consumed)
    _validate_timing(
        timing,
        kind="case",
        signal_id=report["signal_id"],
        case_id=report["case"]["id"],
        report=report,
    )
    if timing["cpu_measurement_complete"] != _costs_complete(
        report["packages"].values()
    ):
        raise ValueError("Case CPU completeness differs from its workers.")
    _included_costs(timing, report["packages"].values(), package=True)
    return timing


def _verify_case(root, prepared, case_id, gates, consumed):
    local = publication.Consumption(consumed.clock)
    root = _identity(root)
    original = _released(root / "completion", local)
    case = inputs.read_case(prepared, case_id, local)
    report = _case_report(root, prepared, case, gates, local)
    sources._same(original, report, "Main-study case replay differs from publication.")
    timing = _case_timing(root, report, local)
    local.check()
    consumed.callbacks.append(local.check)
    return report, timing


def _run_case(prepared, case_id, gates, output):
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError("An existing alarm must not be replaced.")
    started, before = time.monotonic(), _usage()
    root = publication.validate_output(output)
    call_path = publication.validate_output(_call_path(root))
    frozen = publication.Consumption(publication.Deadline(CASE_SECONDS))
    signal_id = prepared.cases[case_id]["signal_id"]
    report, timing_written = None, False
    root.mkdir(parents=True)
    (root / "symbolic").mkdir()
    try:
        with ExitStack() as stack:
            _install_handlers(stack)
            case = inputs.read_case(prepared, case_id, frozen)
            _write_json(
                root / "run_state.json",
                {"status": "preparing", "case": case_id, "signal_id": signal_id},
            )
            frozen.git_file.clear()
            for arm in _arm_order(prepared, case_id):
                frozen.check()
                _write_json(
                    root / "run_state.json",
                    {
                        "status": "running",
                        "case": case_id,
                        "condition": arm,
                        "signal_id": signal_id,
                    },
                )
                if case.record["arm_status"][arm] == "ready":
                    arrays = inputs.arm_arrays(prepared, case, arm)
                    search.run_confirmed_package(
                        arrays["time_s"],
                        arrays["observed"],
                        covariance=arrays.get("covariance"),
                        output=root / "symbolic" / arm,
                        seeds=case.spec["search_seeds"],
                        withhold_on_reference_width=True,
                    )
                    _hold_tree(root / "symbolic" / arm, frozen)
                frozen.check()
            _write_json(
                root / "run_state.json",
                {"status": "completed", "case": case_id, "signal_id": signal_id},
            )

            def build(consumed):
                consumed.callbacks.append(frozen.check)
                return _case_report(root, prepared, case, gates, consumed), SUMMARY, {}

            report = publication.export_transaction(
                root / "completion",
                build,
                seconds=max(0.001, CASE_SECONDS - (time.monotonic() - started)),
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
            signal_id=signal_id,
            case_id=case_id,
            status="completed",
            report=report,
            cpu_measurement_complete=_costs_complete(report["packages"].values()),
        )
        _included_costs(timing, report["packages"].values(), package=True)
        _write_exclusive(call_path, timing)
        timing_written = True
        frozen.add(call_path, sources.json_bytes(timing))
        _case_timing(root, report, frozen)
        frozen.check()
        return report, timing
    except BaseException as error:
        if (root / "completion").is_dir():
            publication.revoke(root / "completion", error, frozen.clock)
        _retain_failure(
            error,
            lambda error=error: _safe_update(
                root / "run_state.json",
                {
                    "status": "aborted",
                    "case": case_id,
                    "signal_id": signal_id,
                    "error": f"{type(error).__name__}: {error}",
                },
            ),
            "aborted case state",
        )
        if timing_written or not call_path.exists():
            _retain_failure(
                error,
                lambda error=error: (
                    _safe_update if timing_written else _write_exclusive
                )(
                    call_path,
                    _timing(
                        started,
                        before,
                        kind="case",
                        signal_id=signal_id,
                        case_id=case_id,
                        status="aborted",
                        error=error,
                    ),
                ),
                "aborted case-call costs",
            )
        raise


def _root_inventory(root, ids):
    if {p.name for p in root.iterdir()} != {
        "registration.json",
        "run_state.json",
        "cases",
        "completion",
    } or any(p.is_symlink() for p in root.iterdir()):
        raise ValueError("Unexpected or incomplete main-study section inventory.")
    expected = {name for case_id in ids for name in (case_id, case_id + "-call.json")}
    if {p.name for p in (root / "cases").iterdir()} != expected:
        raise ValueError("A planned case is incomplete or unplanned artifacts exist.")


def _state(signal_id, ids, status):
    return {
        "status": status,
        "signal_id": signal_id,
        "cases": [{"id": key, "status": status} for key in ids],
    }


def _signal_normalization(prepared, signal_id):
    """Report marginal-noise ratios against amplitude and the original N103 truth."""
    specs = [prepared.cases[case_id] for case_id in _section_ids(prepared, signal_id)]
    spec = specs[0]
    amplitude = abs(float(spec["signal"]["amplitude"]))
    sigma = float(spec["standard_deviation"])
    if (
        not math.isfinite(amplitude)
        or amplitude <= 0
        or not math.isfinite(sigma)
        or sigma <= 0
        or any(
            other["signal"] != spec["signal"]
            or other["standard_deviation"] != spec["standard_deviation"]
            for other in specs
        )
    ):
        raise ValueError(
            "Signal normalization requires consistent finite block parameters."
        )
    common = inputs.common_for_case(prepared.common, spec)
    truth = common["signal"]
    times = common["time_s"]
    if (
        len(truth) != 103
        or len(times) != 103
        or any(not math.isfinite(float(value)) for value in truth)
        or any(float(value) != index / 4096 for index, value in enumerate(times))
    ):
        raise ValueError("Signal normalization requires the original finite N103 grid.")
    scale = max(abs(float(value)) for value in truth)
    if scale == 0:
        raise ValueError("Signal normalization requires a positive clean-signal RMS.")
    rms = scale * (
        math.hypot(*(float(value) / scale for value in truth)) / math.sqrt(103)
    )
    if not math.isfinite(rms) or rms <= 0:
        raise ValueError("Signal normalization is not representable.")
    ratios = (sigma / amplitude, sigma / rms)
    if not all(math.isfinite(value) for value in ratios):
        raise ValueError("Signal normalization is not representable.")
    return {
        "signal_id": signal_id,
        "amplitude": amplitude,
        "noise_standard_deviation": sigma,
        "noise_over_amplitude": ratios[0],
        "training_signal_rms": rms,
        "noise_over_training_signal_rms": ratios[1],
        "rms_reference": "clean_signal_equal_weight_training_samples",
        "n_samples": 103,
        "signal_unit": "dimensionless",
        "time_unit": "s",
        "training_time_s_fingerprint": sources.fingerprint(times),
        "training_signal_fingerprint": sources.fingerprint(truth),
        "interpretation": "marginal_noise_ratios_not_detector_snr",
    }


def _section_report(prepared, signal_id, registration, reports, calls):
    records = [
        record for report in reports.values() for record in report["assessments"]
    ]
    count = sum(report["search_calls"] for report in reports.values())
    return {
        "format": FORMAT,
        "prediction_failure_policy": registration["prediction_failure_policy"],
        "status": "completed",
        "signal_id": signal_id,
        "signal_normalization": _signal_normalization(prepared, signal_id),
        "technical": False,
        "software": prepared.manifest["software"],
        "preparation_sha256": _binding(prepared),
        "preparation_call": prepared.call,
        "registration_sha256": sources.sha256(sources.json_bytes(registration)),
        "technical_report_sha256": registration["technical_report_sha256"],
        "previous_section_report_sha256": registration[
            "previous_section_report_sha256"
        ],
        "numerical_environment": registration["numerical_environment"],
        "planned_search_calls": CASE_COUNT * len(ARMS) * 4,
        "planned_outputs": CASE_COUNT * len(ARMS),
        "full_study_planned_search_calls": TOTAL_CASE_COUNT * len(ARMS) * 4,
        "full_study_planned_outputs": TOTAL_CASE_COUNT * len(ARMS),
        "search_calls": count,
        "new_search_calls": count,
        "case_reports_sha256": {
            case_id: sources.sha256(_publication_bytes(report)[publication.REPORT])
            for case_id, report in reports.items()
        },
        "case_call_costs": calls,
        "cost_scope": "this section's new case calls only; previous section, preparation, preflight, verification and export remain separate inclusive scopes",
        "assessments": records,
        "summary": assessment.summary(records, signal_id=signal_id),
        "decision": "paired_effect_estimation_no_automatic_method_selection",
    }


def _section_timing(root, report, ids, consumed):
    timing = _json(_call_path(root), consumed)
    _validate_timing(
        timing, kind="section", signal_id=report["signal_id"], report=report, ids=ids
    )
    calls = report["case_call_costs"].values()
    if timing["cpu_measurement_complete"] != all(
        c["cpu_measurement_complete"] for c in calls
    ):
        raise ValueError("Section CPU completeness differs from its case calls.")
    _included_costs(timing, calls)
    return timing


def _verify_bound(prepared, gates, root, signal_id, previous_hash, consumed):
    ids = _section_ids(prepared, signal_id)
    _root_inventory(root, ids)
    consumed.callbacks.append(lambda: _root_inventory(root, ids))
    original = _released(root / "completion", consumed)
    registration = _registration(prepared, signal_id, gates, previous_hash)
    sources._same(
        _json(root / "registration.json", consumed),
        registration,
        "Changed main-study section registration.",
    )
    sources._same(
        _json(root / "run_state.json", consumed),
        _state(signal_id, ids, "completed"),
        "Incomplete main-study section state.",
    )
    reports, calls = {}, {}
    for case_id in ids:
        reports[case_id], calls[case_id] = _verify_case(
            root / "cases" / case_id, prepared, case_id, gates, consumed
        )
    report = _section_report(prepared, signal_id, registration, reports, calls)
    sources._same(
        original, report, "Main-study section replay differs from publication."
    )
    _section_timing(root, report, ids, consumed)
    consumed.check()
    return report


def run(preparation, technical_path, output, *, signal_id, previous=None):
    """Execute a whole fresh section, or read-verify an already completed one."""
    signal_id = _signal_id(signal_id)
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError("An existing alarm must not be replaced.")
    root = Path(output).absolute()
    _separate(root, (preparation, technical_path, previous))
    if root.exists() or root.is_symlink():
        # Never repair, append to, or retry an interrupted section.
        return verify(
            preparation, technical_path, root, signal_id=signal_id, previous=previous
        )
    root = publication.validate_output(root)
    call_path = publication.validate_output(_call_path(root))
    started, before = time.monotonic(), _usage()
    consumed = publication.Consumption(publication.Deadline(SECTION_SECONDS))
    root.mkdir(parents=True)
    (root / "cases").mkdir()
    report, timing_written = None, False
    new_ids, reports, calls = [], {}, {}
    state = {"status": "preparing", "signal_id": signal_id, "cases": []}
    try:
        with ExitStack() as stack:
            _install_handlers(stack)
            _write_json(root / "run_state.json", state)
            prepared = inputs.verify_inputs(preparation, consumed)
            _scientific(prepared)
            gates = _gates(prepared, technical_path, consumed)
            previous_hash = _previous(prepared, gates, signal_id, previous, consumed)
            registration = _registration(prepared, signal_id, gates, previous_hash)
            _write_exclusive(root / "registration.json", registration)
            consumed.add(root / "registration.json", sources.json_bytes(registration))
            ids = _section_ids(prepared, signal_id)
            state = _state(signal_id, ids, "planned")
            state["status"] = "running"
            _write_json(root / "run_state.json", state)
            for entry in state["cases"]:
                case_id = entry["id"]
                entry["status"] = "running"
                state["current_case"] = case_id
                _write_json(root / "run_state.json", state)
                consumed.check()
                current, timing = _run_case(
                    prepared, case_id, gates, root / "cases" / case_id
                )
                new_ids.append(case_id)
                reports[case_id], calls[case_id] = current, timing
                _hold_tree(root / "cases" / case_id, consumed)
                _read(_call_path(root / "cases" / case_id), consumed)
                entry["status"] = "completed"
                state.pop("current_case", None)
                _write_json(root / "run_state.json", state)
                consumed.check()
            state["status"] = "completed"
            _write_json(root / "run_state.json", state)
            report = _section_report(prepared, signal_id, registration, reports, calls)
            report = _export(root / "completion", report, consumed)
            consumed.check()
        consumed.check()
        timing = _timing(
            started,
            before,
            kind="section",
            signal_id=signal_id,
            status="completed",
            report=report,
            new_case_ids=new_ids,
            cpu_measurement_complete=all(
                c["cpu_measurement_complete"] for c in calls.values()
            ),
        )
        _included_costs(timing, calls.values())
        _write_exclusive(call_path, timing)
        timing_written = True
        consumed.add(call_path, sources.json_bytes(timing))
        _root_inventory(root, ids)
        consumed.callbacks.append(lambda: _root_inventory(root, ids))
        _section_timing(root, report, ids, consumed)
        consumed.check()
        return report
    except BaseException as error:
        if (root / "completion").is_dir():
            publication.revoke(root / "completion", error, consumed.clock)
        state.update(status="aborted", error=f"{type(error).__name__}: {error}")
        _retain_failure(
            error,
            lambda error=error: _safe_update(root / "run_state.json", state),
            "aborted section state",
        )
        if timing_written or not call_path.exists():
            _retain_failure(
                error,
                lambda error=error: (
                    _safe_update if timing_written else _write_exclusive
                )(
                    call_path,
                    _timing(
                        started,
                        before,
                        kind="section",
                        signal_id=signal_id,
                        status="aborted",
                        error=error,
                        new_case_ids=new_ids,
                    ),
                ),
                "aborted section costs",
            )
        raise


def verify(
    preparation,
    technical_path,
    output,
    *,
    signal_id=None,
    previous=None,
    export=None,
    consumed=None,
):
    """Replay without scientific work; optional separate export records replay cost."""
    if consumed is not None and export is not None:
        raise ValueError("An externally guarded replay cannot create another export.")
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0) and consumed is None:
        raise RuntimeError("An existing alarm must not be replaced.")
    destination = None if export is None else publication.validate_output(export)
    if destination is not None:
        _separate(destination, (preparation, technical_path, output, previous))
    call_path = (
        None
        if destination is None
        else publication.validate_output(_call_path(destination))
    )
    started, before = time.monotonic(), _usage()
    guard = consumed or publication.Consumption(publication.Deadline(VERIFY_SECONDS))
    chosen = signal_id
    report, owned, timing_written = None, False, False
    try:
        root = _identity(output)
        original = _released(root / "completion", guard)
        chosen = _signal_id(
            original.get("signal_id") if signal_id is None else signal_id
        )
        if original.get("format") != FORMAT or original.get("signal_id") != chosen:
            raise ValueError("Wrong main-study section format or identity.")
        prepared = inputs.verify_inputs(preparation, guard)
        _scientific(prepared)
        gates = _gates(prepared, technical_path, guard)
        previous_hash = _previous(prepared, gates, chosen, previous, guard)
        report = _verify_bound(prepared, gates, root, chosen, previous_hash, guard)
        if destination is not None:
            # export_transaction exclusively reserves its destination itself.
            report = _export(destination, report, guard)
            owned = True
            timing = _timing(
                started,
                before,
                kind="verification",
                signal_id=chosen,
                status="completed",
                report=report,
                cpu_measurement_complete=True,
            )
            _validate_timing(
                timing, kind="verification", signal_id=chosen, report=report
            )
            _write_exclusive(call_path, timing)
            timing_written = True
            guard.add(call_path, sources.json_bytes(timing))
        guard.check()
        return report
    except BaseException as error:
        if owned and destination.is_dir():
            publication.revoke(destination, error, guard.clock)
        if call_path is not None and (timing_written or not call_path.exists()):
            _retain_failure(
                error,
                lambda error=error: (
                    _safe_update if timing_written else _write_exclusive
                )(
                    call_path,
                    _timing(
                        started,
                        before,
                        kind="verification",
                        signal_id=chosen,
                        status="aborted",
                        error=error,
                    ),
                ),
                "aborted verification costs",
            )
        raise
