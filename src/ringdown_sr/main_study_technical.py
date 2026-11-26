"""Run and replay all eight independently bound N103 technical workers."""

import math
import signal
import time
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path

import numpy as np

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import confirmed_profile as profile
from . import confirmed_search
from . import global_restarts as restarts
from . import iteration_time as costs
from . import main_study_inputs as inputs
from .noise_pilot_inputs import _cpu_usage
from .pilot import _utc_now, _write_json

FORMAT = "ringdown-sr-main-study-technical-2"
ARMS = inputs.ARMS
SIGNALS = ("signal_200_4ms", "signal_250_6ms")
SEARCH_CALLS = 8
WORKER_SECONDS = 600
TOTAL_SECONDS = 14400
VERIFY_SECONDS = 14400
TIMING = "technical_call.json"
TIMING_SCOPE = (
    "preparation_and_workers_through_publication_and_handler_restoration_"
    "excludes_timing_write_and_final_guards"
)
# Permit only OS resource-accounting / floating-point rounding at one microsecond.
COST_ROUNDING_SECONDS = 1e-6


def _cases(prepared, consumed):
    expected = inputs.case_specs(purpose="technical")
    if (
        prepared.manifest.get("technical") is not True
        or prepared.manifest.get("purpose") != "technical"
        or len(prepared.cases) != 2
        or list(prepared.cases) != [spec["id"] for spec in expected]
        or tuple(spec["signal_id"] for spec in expected) != SIGNALS
    ):
        raise ValueError("Technical preflight requires its two bound signal cases.")
    cases = []
    for spec in expected:
        case = inputs.read_case(prepared, spec["id"], consumed)
        if (
            sources.json_bytes(case.spec) != sources.json_bytes(spec)
            or case.spec["noise_model"] != "ar1"
            or case.spec["sampling"]["n_samples"] != 103
            or len(case.spec["search_seeds"]) != 1
            or case.spec["niterations"] != 10
            or set(case.record["arm_status"]) != set(ARMS)
            or any(case.record["arm_status"][arm] != "ready" for arm in ARMS)
        ):
            raise ValueError("Both technical cases must prepare all four N103 arms.")
        cases.append(case)
    return tuple(cases)


def _directory(root, case_id, arm):
    return root / "workers" / case_id / arm


def _case_identity(case):
    return {
        "id": case.spec["id"],
        "signal_id": case.spec["signal_id"],
        "search_seed": case.spec["search_seeds"][0],
    }


def _arrays(prepared, case, arm):
    arrays = inputs.arm_arrays(prepared, case, arm)
    checked = confirmed_search._arrays(
        arrays["time_s"], arrays["observed"], arrays.get("covariance")
    )
    if checked["time_s"].shape != (103,) or not np.array_equal(
        checked["time_s"], np.arange(103) / 4096
    ):
        raise ValueError("Technical inputs require the exact N103 main-study grid.")
    return checked


def _preparation(root, prepared, cases):
    return {
        "format": FORMAT,
        "technical": True,
        "profile": profile.PROFILE,
        "member_format": profile.MAIN_WIDTH_FORMAT,
        "prediction_failure_policy": confirmed_search.WIDTH_POLICY,
        "cases": [_case_identity(case) for case in cases],
        "n_samples": 103,
        "niterations": 10,
        "arms": list(ARMS),
        "search_calls": SEARCH_CALLS,
        "worker_limit_seconds": WORKER_SECONDS,
        "whole_limit_seconds": TOTAL_SECONDS,
        "software": prepared.manifest["software"],
        "input_manifest_sha256": sources.sha256(
            (root / "inputs/preparation.json").read_bytes()
        ),
        "input_fingerprints": {
            f"{case.spec['id']}/{arm}": confirmed_search._fingerprints(
                _arrays(prepared, case, arm)
            )
            for case in cases
            for arm in ARMS
        },
    }


def _records(root, prepared, cases, consumed):
    records, environment = {}, None
    for case in cases:
        for arm in ARMS:
            consumed.check()
            record = profile.verify_member(_directory(root, case.spec["id"], arm))
            if (
                record.get("format") != profile.MAIN_WIDTH_FORMAT
                or record.get("requested_iterations") != 10
                or type(record.get("requested_iterations")) is not int
                or record.get("profile") != profile.PROFILE
                or record.get("technical") is not True
                or type(record.get("seed")) is not int
                or record["seed"] != case.spec["search_seeds"][0]
                or record.get("status") != "completed"
                or record.get("numerical_environment") is None
                or set(record["costs"]) != set(costs.COST_FIELDS)
            ):
                raise ValueError("All eight exact technical workers must complete.")
            totals = costs.cost_totals([record])
            if any(value is None for value in totals.values()) or (
                totals["worker_wall_seconds"] >= WORKER_SECONDS
            ):
                raise ValueError("Technical worker exceeds its limit or lacks costs.")
            sources._same(
                record["input_fingerprints"],
                confirmed_search._fingerprints(_arrays(prepared, case, arm)),
                "Technical worker input or covariance differs from preparation.",
            )
            confirmed_search._check_provenance(
                record["provenance"], prepared.manifest["software"]
            )
            if environment is not None:
                sources._same(
                    record["numerical_environment"],
                    environment,
                    "Technical worker numerical environments differ.",
                )
            environment = record["numerical_environment"]
            records[f"{case.spec['id']}/{arm}"] = record
    return records, environment


def _raw_hashes(root):
    from .noise_followup import _tree_hashes

    return _tree_hashes(root, excluded={TIMING}, skip_directories={"completion"})


def _hold_raw(root, consumed):
    expected = _raw_hashes(root)

    def unchanged():
        if _raw_hashes(root) != expected:
            raise ValueError("Technical preflight evidence inventory changed.")

    consumed.callbacks.append(unchanged)
    return expected


def _inventory(root):
    expected = {
        "inputs",
        "inputs-call.json",
        "preparation.json",
        "completion",
        "workers",
        TIMING,
    }
    if root.is_symlink() or {path.name for path in root.iterdir()} != expected:
        raise ValueError("Incomplete technical preflight root inventory.")
    if any(path.is_symlink() for path in root.iterdir()):
        raise ValueError("Technical preflight artifacts cannot be symlinks.")
    workers = root / "workers"
    expected_cases = {spec["id"] for spec in inputs.case_specs(purpose="technical")}
    if not workers.is_dir() or {p.name for p in workers.iterdir()} != expected_cases:
        raise ValueError("Technical preflight worker-case inventory differs.")
    for case_id in expected_cases:
        case_root = workers / case_id
        if not case_root.is_dir() or {p.name for p in case_root.iterdir()} != set(ARMS):
            raise ValueError("Technical preflight worker-arm inventory differs.")
        if any(not path.is_dir() or path.is_symlink() for path in case_root.iterdir()):
            raise ValueError(
                "Technical worker directories must be regular directories."
            )


def _report(root, prepared, cases, records, environment):
    return {
        "format": FORMAT,
        "status": "completed",
        "technical": True,
        "prediction_failure_policy": confirmed_search.WIDTH_POLICY,
        "software": prepared.manifest["software"],
        "numerical_environment": environment,
        "preparation_sha256": sources.sha256((root / "preparation.json").read_bytes()),
        "search_calls": SEARCH_CALLS,
        "n_samples": 103,
        "niterations": 10,
        "cases": [_case_identity(case) for case in cases],
        "arms": list(ARMS),
        "members": records,
        "costs": costs.cost_totals(list(records.values())),
        "scientific_success_assessed": False,
    }


def _summary():
    return (
        "# Technischer Hauptstudienvorlauf\n\n"
        "Acht getrennte Worker mit N=103 und je zehn äußeren Iterationen: "
        "zwei Signalbedingungen mit jeweils gewöhnlicher, bekannter und "
        "aus 64/4096 Sekunden Hintergrund geschätzter Kovarianzgewichtung. "
        "Lokales Profil 300/5, eigene technische Eingaben und Seeds. "
        "Alle Worker und ihre lesenden Nachrechnungen sind abgeschlossen. "
        "Keine wissenschaftliche Erfolgsbewertung oder Laufzeitgarantie.\n"
    )


def _documents(report, payloads):
    documents = {
        **payloads,
        publication.REPORT: sources.json_bytes(report),
        publication.SUMMARY: _summary().encode(),
    }
    return {
        **documents,
        publication.MANIFEST: sources.json_bytes(
            {name: sources.sha256(raw) for name, raw in documents.items()}
        ),
    }


def _timing(started, wall, usage, report_raw, *, error=None):
    current = _cpu_usage()
    return {
        "format": FORMAT,
        "status": "completed" if error is None else "aborted",
        "error": None if error is None else f"{type(error).__name__}: {error}",
        "report_sha256": None if report_raw is None else sources.sha256(report_raw),
        "started_at_utc": started,
        "finished_at_utc": _utc_now(),
        "wall_seconds": time.monotonic() - wall,
        "cpu_user_seconds": current[0] - usage[0],
        "cpu_system_seconds": current[1] - usage[1],
        "cpu_scope": "self_plus_reaped_children",
        "cpu_measurement_complete": error is None,
        "measurement_scope": TIMING_SCOPE
        if error is None
        else (
            "aborted_call_through_handler_restoration_and_revocation_"
            "excludes_call_write"
        ),
    }


def _verify_timing(record, report_raw, preparation_call):
    if (
        set(record)
        != {
            "format",
            "status",
            "error",
            "report_sha256",
            "started_at_utc",
            "finished_at_utc",
            "wall_seconds",
            "cpu_user_seconds",
            "cpu_system_seconds",
            "cpu_scope",
            "cpu_measurement_complete",
            "measurement_scope",
        }
        or record["format"] != FORMAT
        or record["status"] != "completed"
        or record["error"] is not None
        or record["cpu_scope"] != "self_plus_reaped_children"
        or record["cpu_measurement_complete"] is not True
        or record["report_sha256"] != sources.sha256(report_raw)
        or record["measurement_scope"] != TIMING_SCOPE
    ):
        raise ValueError("Unbound technical preflight call timing.")
    for name in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
        value = record[name]
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid technical preflight resource cost.")
    if record["wall_seconds"] >= TOTAL_SECONDS:
        raise ValueError("Technical preflight whole-call deadline exceeded.")
    if preparation_call is None:
        raise ValueError("Missing full input-preparation call cost.")
    members = sources.read_json(report_raw)["members"].values()
    for field, member_field in (
        ("wall_seconds", "adapter_call_wall_seconds"),
        ("cpu_user_seconds", "cpu_user_seconds"),
        ("cpu_system_seconds", "cpu_system_seconds"),
    ):
        # These disjoint serial scopes contain their own nested work; do not add
        # fit/worker wall times or partial preparation timing again.
        known = [preparation_call[field]] + [
            member["costs"][member_field] for member in members
        ]
        minimum = sum(value for value in known if value is not None)
        if record[field] + COST_ROUNDING_SECONDS < minimum:
            raise ValueError("Full technical call cost is below its included parts.")
    start, finish = (
        datetime.fromisoformat(record[name])
        for name in ("started_at_utc", "finished_at_utc")
    )
    if start.utcoffset() is None or finish.utcoffset() is None or finish < start:
        raise ValueError("Invalid technical preflight timestamps.")


def run(output):
    """Prepare once, execute eight guarded workers, and publish only full success."""
    clock = publication.Deadline(TOTAL_SECONDS)
    started, wall, usage = _utc_now(), time.monotonic(), _cpu_usage()
    root = publication.validate_output(output)
    root.mkdir(parents=True)
    frozen = publication.Consumption(clock)
    published = []
    try:
        with ExitStack() as stack:

            def interrupt(signum, frame):
                raise InterruptedError(
                    "Technical preflight interrupted by signal " + str(signum)
                )

            for sig in (signal.SIGINT, signal.SIGTERM):
                previous = signal.signal(sig, interrupt)
                stack.callback(signal.signal, sig, previous)
            # Input preparation owns its alarm; never nest that transaction.
            inputs.prepare_inputs(root / "inputs", purpose="technical")
            prepared = inputs.verify_inputs(root / "inputs", frozen)
            cases = _cases(prepared, frozen)
            preparation = _preparation(root, prepared, cases)
            _write_json(root / "preparation.json", preparation)
            frozen.add(
                root / "preparation.json", (root / "preparation.json").read_bytes()
            )
            for case in cases:
                for arm in ARMS:
                    directory = _directory(root, case.spec["id"], arm)
                    arrays = _arrays(prepared, case, arm)
                    profile.prepare_main_width_member(
                        directory,
                        **arrays,
                        seed=case.spec["search_seeds"][0],
                        technical=True,
                    )
                    _, _, manifest = profile.verify_prepared(directory)
                    confirmed_search._check_provenance(
                        manifest["provenance"], prepared.manifest["software"]
                    )
                    restarts.freeze_files(
                        frozen, directory, profile.prepared_files(directory)
                    )
            frozen.check()
            frozen.git_file.clear()

            def build(consumed):
                consumed.callbacks.append(frozen.check)
                for case in cases:
                    for arm in ARMS:
                        consumed.check()
                        directory = _directory(root, case.spec["id"], arm)
                        profile.run_member(
                            directory,
                            deadline=min(
                                time.monotonic() + WORKER_SECONDS,
                                clock.started + clock.seconds,
                            ),
                        )
                        restarts.freeze_files(
                            consumed, directory, restarts.raw_files(directory)
                        )
                records, environment = _records(root, prepared, cases, consumed)
                payloads = {
                    "raw_checksums.json": sources.json_bytes(_hold_raw(root, consumed))
                }
                report = _report(root, prepared, cases, records, environment)
                published.append((consumed, _documents(report, payloads)))
                return report, _summary(), payloads

            clock.check()
            report = publication.export_transaction(
                root / "completion",
                build,
                seconds=clock.started + clock.seconds - time.monotonic(),
            )
            consumed, expected = published[0]
            restarts.freeze_files(consumed, root / "completion", expected)
            consumed.callbacks.append(
                lambda: publication.verify_bytes(
                    root / "completion", expected, locked=False
                )
            )
            consumed.check()
            stack.close()
            consumed.check()
            timing = _timing(started, wall, usage, expected[publication.REPORT])
            _verify_timing(timing, expected[publication.REPORT], prepared.call)
            _write_json(root / TIMING, timing)
            consumed.add(root / TIMING, sources.json_bytes(timing))
            consumed.callbacks.append(lambda: _inventory(root))
            consumed.check()
        frozen.check()
        consumed.check()
        return report
    except BaseException as error:
        if (root / "completion").is_dir():
            publication.revoke(root / "completion", error, clock)
        try:
            report_raw = published[0][1][publication.REPORT] if published else None
            _write_json(
                root / TIMING, _timing(started, wall, usage, report_raw, error=error)
            )
        except BaseException as cost_error:  # noqa: BLE001 -- Preserve the initiating interruption.
            error.add_note(
                "Could not retain aborted technical-call costs: "
                f"{type(cost_error).__name__}: {cost_error}"
            )
        raise


def verify(output, consumed=None):
    """Recompute the technical result without a reference fit, search, or write."""
    root = Path(output).absolute()
    if root != root.resolve() or not root.is_dir():
        raise ValueError("Expected an existing technical preflight without symlinks.")
    if consumed is None:
        consumed = publication.Consumption(publication.Deadline(VERIFY_SECONDS))
    _inventory(root)
    consumed.callbacks.append(lambda: _inventory(root))
    completion = root / "completion"
    names = {
        publication.REPORT,
        publication.SUMMARY,
        publication.MANIFEST,
        "raw_checksums.json",
    }
    if {path.name for path in completion.iterdir()} != names:
        raise ValueError("Technical preflight completion is incomplete or locked.")
    exported = {name: (completion / name).read_bytes() for name in names}
    publication.verify_bytes(completion, exported, locked=False)
    consumed.callbacks.append(
        lambda: publication.verify_bytes(completion, exported, locked=False)
    )
    restarts.freeze_files(consumed, completion, exported)
    if sources.read_json(exported[publication.MANIFEST]) != {
        name: sources.sha256(raw)
        for name, raw in exported.items()
        if name != publication.MANIFEST
    }:
        raise ValueError("Technical preflight publication checksum differs.")
    if _hold_raw(root, consumed) != sources.read_json(exported["raw_checksums.json"]):
        raise ValueError("Technical preflight raw inventory differs.")
    prepared = inputs.verify_inputs(root / "inputs", consumed)
    cases = _cases(prepared, consumed)
    sources._same(
        profile.read(root, "preparation.json"),
        _preparation(root, prepared, cases),
        "Changed technical preflight preparation.",
    )
    records, environment = _records(root, prepared, cases, consumed)
    report = _report(root, prepared, cases, records, environment)
    if exported != _documents(
        report, {"raw_checksums.json": exported["raw_checksums.json"]}
    ):
        raise ValueError("Technical preflight report or summary differs from replay.")
    timing_raw = (root / TIMING).read_bytes()
    consumed.add(root / TIMING, timing_raw)
    _verify_timing(
        sources.read_json(timing_raw), exported[publication.REPORT], prepared.call
    )
    consumed.check()
    return report
