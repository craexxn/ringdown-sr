"""Run frozen confirmation sections and read-verify paired package outcomes."""

import math
import resource
import signal
import subprocess
import tempfile
import time
from contextlib import ExitStack
from pathlib import Path

import numpy as np

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import global_restarts as restarts
from . import iteration_time as previous
from . import restart_budget_confirmation_profile as profile
from . import seed_driver_crosscheck as cross
from . import time_budget_profile as native
from .pilot import _provenance, _utc_now, _write_json
from .restart_budget import selected_output
from .restart_confirmation import binomial_interval
from .symbolic import ROOT, _stop_worker

FORMAT = profile.FORMAT
CALL_SCOPE = (
    "run_entry_through_publication_return_excluding_final_timing_write_and_rechecks"
)
load_json = previous.load_json


def freeze_software(consumed):
    software = previous.freeze_software(consumed)
    profile.configuration()
    names = {
        *profile.PLAN_HASHES,
        profile.BRIDGE,
        "scripts/run_restart_budget_confirmation.py",
        "scripts/check_restart_budget_confirmation.py",
    }
    for name in sorted(names):
        raw = (ROOT / name).read_bytes()
        if raw != consumed.git_file(software["software_commit"], name):
            raise ValueError("Uncommitted restart-budget-confirmation source: " + name)
        if name in profile.PLAN_HASHES and raw != consumed.git_file(
            profile.PLAN_COMMIT, name
        ):
            raise ValueError("Changed frozen restart-budget-confirmation commit.")
        consumed.add(ROOT / name, raw)
        software["source_sha256"][name] = sources.sha256(raw)
    return software


def call_bridge(action, output, request, inputs, consumed, log, verification=None):
    consumed.check()
    deadline = min(
        consumed.clock.started + consumed.clock.seconds,
        time.monotonic() + native.LIMIT_SECONDS,
    )
    command, environment = cross.bridge_command(
        ROOT, action, "outer", output, request, deadline
    )
    command[4] = str(ROOT / profile.BRIDGE)
    index = command.index("--kind")
    del command[index : index + 2]
    command += ["--inputs", str(inputs)]
    environment.update(native.JULIA_THREADS)
    if verification is not None:
        command += ["--verification", str(verification)]
    started = time.monotonic()
    with log.open("wb") as stream:
        child = subprocess.Popen(
            command,
            cwd=ROOT,
            env=environment,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            if child.wait(timeout=max(0.01, deadline - time.monotonic())):
                raise RuntimeError("Restart-budget adapter failed; inspect " + str(log))
        except BaseException:
            _stop_worker(child)
            raise
    consumed.check()
    return time.monotonic() - started


def comparison(cells, name, technical=False):
    plans = profile.plans(name, technical)
    if sources.json_bytes([c["plan"] for c in cells]) != sources.json_bytes(
        plans
    ) or any(c["status"] not in {"completed", "worker_failed"} for c in cells):
        raise ValueError(
            "Retain every planned restart-budget-confirmation cell and its original slot."
        )
    previous.cost_totals(cells)
    pairs = []
    for block in range(1, len(profile.case(name, technical)["seeds"]) + 1):
        outputs = {}
        for arm in ("R", "L"):
            members = sorted(
                (
                    c
                    for c in cells
                    if c["plan"]["block"] == block and c["plan"]["arm"] == arm
                ),
                key=lambda c: c["plan"]["member"],
            )
            outputs[arm] = selected_output(members)
        pairs.append(
            {
                "block": block,
                "seeds": profile.case(name, technical)["seeds"][block - 1],
                "outputs": outputs,
            }
        )
    totals = {}
    for arm in ("R", "L"):
        group = [p["outputs"][arm] for p in pairs]
        counts = {
            key: sum(c[key] for c in group) for key in ("A", "A_and_original_family")
        }
        totals[arm] = {
            "denominator": len(group),
            **counts,
            "failures": sum(c["status"] == "worker_failed" for c in group),
            "failed_members": sum(c["failed_members"] for c in group),
            "costs": previous.cost_totals(group),
            "uncertainty": None
            if technical
            else {key: binomial_interval(n, len(group)) for key, n in counts.items()},
        }
    contrasts = {}
    for endpoint in ("A", "A_and_original_family"):
        differences = [
            int(p["outputs"]["R"][endpoint]) - int(p["outputs"]["L"][endpoint])
            for p in pairs
        ]
        contrasts[endpoint] = {
            "gains": differences.count(1),
            "losses": differences.count(-1),
            "ties": differences.count(0),
        }
    complete_costs = all(
        v is not None for t in totals.values() for v in t["costs"].values()
    )
    return {
        "signal": name,
        "pairs": pairs,
        "totals": totals,
        "R_minus_L": contrasts,
        "algorithm_outputs": 2 * len(pairs),
        "all_costs_observed": complete_costs,
        "R_meets_signal_threshold": None
        if technical
        else totals["R"]["A_and_original_family"]
        >= profile.configuration()["minimum_joint_successes"],
        "L_meets_signal_threshold": None
        if technical
        else totals["L"]["A_and_original_family"]
        >= profile.configuration()["minimum_joint_successes"],
        "automatic_execution": False,
    }


def confirmation_decision(sections):
    """Require the per-signal primary threshold, keeping the control separate."""
    names = [section["signal"] for section in sections]
    if (
        len(names) != len(set(names))
        or set(names) != set(profile.names())
        or any(section["scope"] != "scientific" for section in sections)
    ):
        raise ValueError("A confirmation decision needs every scientific signal.")
    successes = {"R": [], "L": []}
    minimum = profile.configuration()["minimum_joint_successes"]
    for section in sections:
        totals = section["comparison"]["totals"]
        if section["comparison"]["signal"] != section["signal"] or set(totals) != {
            "R",
            "L",
        }:
            raise ValueError("Confirmation signal or arm assignment differs.")
        denominator = len(profile.case(section["signal"])["seeds"])
        for arm in ("R", "L"):
            count = totals[arm]
            if (
                type(count["denominator"]) is not int
                or count["denominator"] != denominator
                or any(
                    type(count[key]) is not int
                    for key in ("A", "A_and_original_family")
                )
                or not 0 <= count["A_and_original_family"] <= count["A"] <= denominator
            ):
                raise ValueError("Invalid complete per-signal confirmation counts.")
            successes[arm].append(count["A_and_original_family"] >= minimum)
    return {
        "transition_criterion_met": all(successes["R"]),
        "L_control_criterion_met": all(successes["L"]),
    }


def summary(report):
    lines = [
        "# Unabhängige Bestätigung zweier Neustartpakete",
        "",
        "Umfang: `" + report["scope"] + "`.",
        "",
        "| Signal | Arm | A / geplante Pakete | A und Originalfamilie | Paketausfälle | Mitgliedsausfälle |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    comparisons = report.get("comparisons", [report.get("comparison")])
    for item in comparisons:
        for arm, totals in item["totals"].items():
            lines.append(
                f"| {item['signal']} | {arm} | {totals['A']}/{totals['denominator']} | {totals['A_and_original_family']}/{totals['denominator']} | {totals['failures']} | {totals['failed_members']} |"
            )
    lines += [
        "",
        "Praktische Bestätigungsgrenze R: `"
        + str(report.get("transition_criterion_met"))
        + "`; getrennte Kontrollgrenze L: `"
        + str(report.get("L_control_criterion_met"))
        + "`. Beide Entscheidungen erst nach vollständiger wissenschaftlicher Gesamtverifikation; `None` bedeutet noch nicht freigegeben.",
        "",
        "Wissenschaftlich R: 4 × 1.000, L: 2 × 2.000; beide in physischer Zeit t mit lokal 300/5. Technisch R: 4 × 1, L: 2 × 2 auf zwei künstlichen Signalen.",
        "Jedes Paket liefert genau eine Auswahl nach nativer Trainings-MSE, Originalkomplexität und vorab festgelegter Mitgliedsposition. Kosten enthalten alle Mitglieder einschließlich Ausfällen; gleiche Iterationssummen bedeuten keine gleichen Rechenkosten.",
        "R benötigt mindestens 8/10 A-Ausgaben mit nachgewiesener gültiger Originalfamilie auf jedem der drei neuen festen Signale. L wird separat beurteilt und heilt keinen R-Misserfolg. Fortsetzungen und ungeklärte Nachweise erfüllen den gemeinsamen Endpunkt nicht.",
        "Paarungen, marginale exakte 95-%-Binomialintervalle, kontinuierliche Fehler, offene Nachweise und Kosten im JSON. Keine gepoolte Erfolgsquote, keine Überlegenheitsentscheidung, kein Hybrid und keine automatische Profilübernahme oder wissenschaftliche Ausführung; Parameterübereinstimmung not_assessed.",
    ]
    return "\n".join(lines) + "\n"


def bound_inventory(root, plans):
    return previous.bound_inventory(root, plans)


def environment_at(directory):
    options = load_json(directory, "options.json")
    native.validate_runtime(options["budget_runtime"])
    return {
        "environment": cross.environment_key(options["initial"]["environment"]),
        "runtime": options["budget_runtime"],
    }


def _run(output, name, technical, closing):
    plans = profile.plans(name, technical)
    if not technical:
        cross.scientific_platform()
    output = publication.validate_output(output)
    output.mkdir(parents=True)
    state = {
        "format": FORMAT,
        "status": "preparing",
        "scope": "technical" if technical else "scientific",
        "signal": name,
        "cells": [{"plan": p, "status": "planned"} for p in plans],
    }
    _write_json(output / "run_state.json", state)

    def build(consumed):
        closing.append(consumed)
        software = freeze_software(consumed)
        arrays, grid = profile.inputs(name, technical)
        np.savez(output / "anchor.npz", **arrays)
        np.savez(output / "irregular.npz", **grid)
        preparation = {
            "format": FORMAT,
            "scope": state["scope"],
            "signal": name,
            "software": software,
            "provenance": _provenance(),
            "plans": plans,
            "protocol_commit": profile.PLAN_COMMIT,
            "started_at_utc": _utc_now(),
        }
        _write_json(output / "preparation.json", preparation)

        def hold_current():
            restarts.freeze_files(
                consumed,
                output,
                {
                    n: r
                    for n, r in restarts.raw_files(output).items()
                    if n != "run_state.json"
                },
            )

        hold_current()
        environment = None
        with previous.one_cpu():
            for plan in plans:
                n = plan["number"]
                request = output / f"request-{n:02d}.json"
                _write_json(
                    request,
                    profile.request_for(
                        plan,
                        output / "anchor.npz",
                        software["software_commit"],
                        technical,
                    ),
                )
                destination = output / f"cell-{n:02d}"
                call_bridge(
                    "prepare",
                    destination,
                    request,
                    output / "anchor.npz",
                    consumed,
                    output / f"cell-{n:02d}-prepare.log",
                )
                current = environment_at(destination)
                if environment is not None and current != environment:
                    raise ValueError(
                        "Prepared restart-budget-confirmation environments/hardware differ."
                    )
                environment = current
                hold_current()
            bound = {
                n: sources.sha256(r)
                for n, r in restarts.raw_files(output).items()
                if n != "run_state.json"
            }
            if set(bound) != bound_inventory(output, plans):
                raise ValueError(
                    "Incomplete pre-search restart-budget-confirmation inventory."
                )
            _write_json(output / "prepared_bindings.json", bound)
            hold_current()
            consumed.git_file.clear()
            state["status"] = "running"
            for slot in state["cells"]:
                plan = slot["plan"]
                n = plan["number"]
                destination = output / f"cell-{n:02d}"
                request = output / f"request-{n:02d}.json"
                slot["status"] = "running"
                _write_json(output / "run_state.json", state)
                elapsed = call_bridge(
                    "run",
                    destination,
                    request,
                    output / "anchor.npz",
                    consumed,
                    output / f"cell-{n:02d}-run.log",
                )
                _write_json(destination / "timing.json", {"run_seconds": elapsed})
                call_bridge(
                    "verify",
                    destination,
                    request,
                    output / "anchor.npz",
                    consumed,
                    output / f"cell-{n:02d}-verify.log",
                    output / f"cell-{n:02d}-verification.json",
                )
                outcome = load_json(destination, "outcome.json")
                slot["status"] = outcome["status"]
                if outcome["status"] == "completed":
                    evidence = load_json(destination, "verified.json")
                    if any(
                        cross.environment_key(evidence[k]) != environment["environment"]
                        for k in ("environment", "environment_after_search")
                    ):
                        raise ValueError(
                            "Numerical environment changed during restart-budget-confirmation."
                        )
                hold_current()
        cells = [
            previous.cell_record(output / f"cell-{p['number']:02d}", p, arrays, grid)
            for p in plans
        ]
        state["status"] = "completed"
        _write_json(output / "run_state.json", state)
        raw = previous.hold_inventory(consumed, output, restarts.raw_files(output))
        report = {
            "format": FORMAT,
            "scope": state["scope"],
            "signal": name,
            "software": software,
            "numerical_environment": environment,
            "cells": cells,
            "comparison": comparison(cells, name, technical),
            "real_new_search_calls": len(plans),
            "algorithm_outputs": 2 * len(profile.case(name, technical)["seeds"]),
            "historical_costs": previous.cost_totals([]),
            "algorithm_costs": previous.cost_totals(cells),
            "prepublication_wall_seconds": time.monotonic() - consumed.clock.started,
            "physical_parameter_match": "not_assessed",
            "finished_at_utc": _utc_now(),
        }
        return report, summary(report), {"raw_checksums.json": sources.json_bytes(raw)}

    try:
        return publication.export_transaction(
            output / "completion", build, seconds=profile.signal_seconds(technical)
        )
    except BaseException as error:
        state.update(status="aborted", error=f"{type(error).__name__}: {error}")
        for slot in state["cells"]:
            if slot["status"] == "running":
                slot["status"] = "aborted"
        _write_json(output / "run_state.json", state)
        raise


def run(output, name, *, technical=False):
    """Keep the PR77 closing-time and late-revocation contract for each section."""
    started = time.monotonic()
    before = [
        resource.getrusage(k) for k in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)
    ]
    output = Path(output).absolute()
    timing_path = publication.validate_output(
        output.with_name(output.name + "-call.json")
    )
    closing, completed = [], False
    with ExitStack() as stack:

        def interrupt(signum, frame):
            raise InterruptedError(
                "Restart-budget interrupted by signal " + str(signum)
            )

        for sig in (signal.SIGINT, signal.SIGTERM):
            previous_handler = signal.signal(sig, interrupt)
            stack.callback(signal.signal, sig, previous_handler)
        try:
            report = _run(output, name, technical, closing)
            completed = True
            elapsed = time.monotonic() - started
            after = [
                resource.getrusage(k)
                for k in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)
            ]
            record = {
                "format": FORMAT + "-call-timing",
                "status": "completed",
                "scope": CALL_SCOPE,
                "wall_seconds": elapsed,
                "cpu_user_seconds": sum(
                    a.ru_utime - b.ru_utime for a, b in zip(after, before, strict=True)
                ),
                "cpu_system_seconds": sum(
                    a.ru_stime - b.ru_stime for a, b in zip(after, before, strict=True)
                ),
                "source_report_sha256": sources.sha256(
                    (output / "completion" / publication.REPORT).read_bytes()
                ),
            }
            _write_json(timing_path, record)
            closing[0].add(timing_path, timing_path.read_bytes())
            closing[0].check()
            if time.monotonic() - started > profile.signal_seconds(technical):
                raise TimeoutError(
                    "Whole restart-budget-confirmation section exceeded its deadline."
                )
            stack.close()
            return report
        except BaseException as error:
            if completed:
                publication.revoke(output / "completion", error, closing[0].clock)
                state = load_json(output, "run_state.json")
                state.update(status="aborted", error=f"{type(error).__name__}: {error}")
                _write_json(output / "run_state.json", state)
            raise


def read_section(source, consumed, software, temporary):
    """Verify all original worker evidence before trusting any reported endpoint."""
    completion = source / "completion"
    manifest_bytes = (completion / publication.MANIFEST).read_bytes()
    manifest = sources.read_json(manifest_bytes)
    if set(manifest) != {
        publication.REPORT,
        publication.SUMMARY,
        "raw_checksums.json",
    } or {p.name for p in completion.iterdir()} != {*manifest, publication.MANIFEST}:
        raise ValueError("Incomplete or locked restart-budget-confirmation section.")
    for name, digest in manifest.items():
        raw = (completion / name).read_bytes()
        if sources.sha256(raw) != digest:
            raise ValueError("Restart-budget completion checksum differs.")
        consumed.add(completion / name, raw)
    consumed.add(completion / publication.MANIFEST, manifest_bytes)

    def unlocked():
        if (completion / publication.LOCK).exists():
            raise ValueError("Restart-budget source release was revoked.")

    consumed.callbacks.append(unlocked)
    original = load_json(completion, publication.REPORT)
    if (
        original["format"] != FORMAT
        or original["status"] != "completed"
        or original["scope"] not in {"technical", "scientific"}
    ):
        raise ValueError("No completed restart-budget-confirmation section.")
    technical = original["scope"] == "technical"
    name = original["signal"]
    plans = profile.plans(name, technical)
    call_path = source.with_name(source.name + "-call.json")
    call_bytes = call_path.read_bytes()
    call = sources.read_json(call_bytes)
    if (
        set(call)
        != {
            "format",
            "status",
            "scope",
            "wall_seconds",
            "cpu_user_seconds",
            "cpu_system_seconds",
            "source_report_sha256",
        }
        or call["format"] != FORMAT + "-call-timing"
        or call["status"] != "completed"
        or call["scope"] != CALL_SCOPE
        or call["source_report_sha256"] != manifest[publication.REPORT]
        or type(original["prepublication_wall_seconds"]) not in (int, float)
        or not math.isfinite(original["prepublication_wall_seconds"])
        or any(
            type(call[k]) not in (int, float)
            or not math.isfinite(call[k])
            or call[k] < 0
            for k in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds")
        )
        or not 0
        <= original["prepublication_wall_seconds"]
        <= call["wall_seconds"]
        <= profile.signal_seconds(technical)
    ):
        raise ValueError("Invalid restart-budget-confirmation whole-call timing.")
    consumed.add(call_path, call_bytes)
    preparation = load_json(source, "preparation.json")
    if (
        preparation["software"] != software
        or original["software"] != software
        or preparation["provenance"] != _provenance()
    ):
        raise ValueError(
            "Verify from the exact clean restart-budget-confirmation checkout/runtime."
        )
    if any(
        preparation[k] != v
        for k, v in {
            "format": FORMAT,
            "scope": original["scope"],
            "signal": name,
            "plans": plans,
            "protocol_commit": profile.PLAN_COMMIT,
        }.items()
    ):
        raise ValueError("Changed restart-budget-confirmation preparation or schedule.")
    raw = restarts.raw_files(source)
    expected = load_json(completion, "raw_checksums.json")
    if {n: sources.sha256(r) for n, r in raw.items()} != expected:
        raise ValueError("Restart-budget raw inventory/checksums differ.")
    previous.hold_inventory(consumed, source, raw)
    bound = load_json(source, "prepared_bindings.json")
    if set(bound) != bound_inventory(source, plans) or any(
        expected.get(n) != digest for n, digest in bound.items()
    ):
        raise ValueError("Incomplete pre-search restart-budget-confirmation bindings.")
    arrays, grid = profile.inputs(name, technical)
    previous.require_arrays(previous.arrays_from(raw["anchor.npz"]), arrays)
    previous.require_arrays(previous.arrays_from(raw["irregular.npz"]), grid)
    environment = None
    for plan in plans:
        n = plan["number"]
        directory = source / f"cell-{n:02d}"
        request = source / f"request-{n:02d}.json"
        if load_json(source, request.name)["cell"] != plan:
            raise ValueError("Restart-budget cell assigned to wrong signal/slot.")
        current = environment_at(directory)
        if environment is not None and current != environment:
            raise ValueError("Restart-budget environments/hardware differ.")
        environment = current
        call_bridge(
            "verify",
            directory,
            request,
            source / "anchor.npz",
            consumed,
            temporary / f"{name}-{n}.log",
            temporary / f"{name}-{n}.json",
        )
    actual = [
        previous.cell_record(source / f"cell-{p['number']:02d}", p, arrays, grid)
        for p in plans
    ]
    state = load_json(source, "run_state.json")
    if state != {
        "format": FORMAT,
        "status": "completed",
        "scope": original["scope"],
        "signal": name,
        "cells": [{"plan": c["plan"], "status": c["status"]} for c in actual],
    }:
        raise ValueError("Restart-budget completion state differs.")
    recomputed = {
        "cells": actual,
        "comparison": comparison(actual, name, technical),
        "numerical_environment": environment,
        "real_new_search_calls": len(plans),
        "algorithm_outputs": 2 * len(profile.case(name, technical)["seeds"]),
        "historical_costs": previous.cost_totals([]),
        "algorithm_costs": previous.cost_totals(actual),
        "physical_parameter_match": "not_assessed",
    }
    for key, value in recomputed.items():
        if sources.json_bytes(original[key]) != sources.json_bytes(value):
            raise ValueError(
                "Recomputed restart-budget-confirmation result differs: " + key
            )
    return {
        "signal": name,
        "scope": original["scope"],
        "source_report_sha256": manifest[publication.REPORT],
        "whole_call_timing": call,
        "whole_call_timing_sha256": sources.sha256(call_bytes),
        "verified_cells": len(actual),
        **recomputed,
    }


def verify(sources_, output, *, complete=False):
    roots = [Path(p).absolute() for p in sources_]
    output = Path(output).absolute()
    if (
        not roots
        or len(roots) != len(set(roots))
        or any(
            p != p.resolve()
            or p == output
            or p.is_relative_to(output)
            or output.is_relative_to(p)
            for p in roots
        )
    ):
        raise ValueError(
            "Use distinct original sections and a separate verification output."
        )
    if not complete and len(roots) != 1:
        raise ValueError("Single-section verification needs one source.")

    closing = []

    def build(consumed):
        closing.append(consumed)
        software = freeze_software(consumed)
        with tempfile.TemporaryDirectory(
            prefix=".restart-budget-confirmation-verify-", dir=output.parent
        ) as directory:
            sections = [
                read_section(p, consumed, software, Path(directory)) for p in roots
            ]
        scope = sections[0]["scope"]
        technical = scope == "technical"
        if any(
            s["scope"] != scope
            or s["numerical_environment"] != sections[0]["numerical_environment"]
            for s in sections
        ):
            raise ValueError(
                "Restart-budget sections mix scopes or numerical environments."
            )
        names = [s["signal"] for s in sections]
        if len(set(names)) != len(names) or (
            complete and set(names) != set(profile.names(technical))
        ):
            raise ValueError(
                "All fixed signals are required exactly once for series release."
            )
        sections.sort(key=lambda s: profile.names(technical).index(s["signal"]))
        decision = (
            {"transition_criterion_met": None, "L_control_criterion_met": None}
            if technical or not complete
            else confirmation_decision(sections)
        )
        report = {
            "format": FORMAT
            + ("-series-verification" if complete else "-verification"),
            "software": software,
            "scope": scope,
            "complete_series": complete,
            "sections": sections,
            "comparisons": [s["comparison"] for s in sections],
            "verified_cells": sum(s["verified_cells"] for s in sections),
            "search_calls": 0,
            "algorithm_outputs": sum(
                section["algorithm_outputs"] for section in sections
            ),
            "algorithm_costs": previous.cost_totals(
                [c for s in sections for c in s["cells"]]
            ),
            "sum_section_call_wall_seconds_excluding_pauses": sum(
                s["whole_call_timing"]["wall_seconds"] for s in sections
            ),
            **decision,
            "automatic_execution": False,
            "physical_parameter_match": "not_assessed",
        }
        return report, summary(report), {}

    seconds = profile.configuration()[
        "series_verify_seconds" if complete else "verify_seconds"
    ]
    completed = False
    with ExitStack() as stack:

        def interrupt(signum, frame):
            raise InterruptedError(
                "Restart-budget verification interrupted by signal " + str(signum)
            )

        for sig in (signal.SIGINT, signal.SIGTERM):
            previous_handler = signal.signal(sig, interrupt)
            stack.callback(signal.signal, sig, previous_handler)
        try:
            report = publication.export_transaction(output, build, seconds=seconds)
            completed = True
            closing[0].check()
            stack.close()
            return report
        except BaseException as error:
            if completed:
                publication.revoke(output, error, closing[0].clock)
            raise
