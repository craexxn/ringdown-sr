"""Execute and read-verify the frozen paired iteration/search-time comparison."""

import io
import math
import os
import subprocess
import tempfile
import time
from contextlib import contextmanager, nullcontext
from pathlib import Path

import numpy as np

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import global_restarts as restarts
from . import seed_driver_crosscheck as cross
from . import time_budget_profile as profile
from . import time_control_import as controls
from .pilot import _provenance, _utc_now, _write_json
from .symbolic import ROOT, _stop_worker

FORMAT = "ringdown-sr-iteration-time-comparison-1"
BRIDGE = "scripts/time_budget_bridge.py"
bridge = profile.load_module(ROOT / BRIDGE, "iteration_time_bridge")
COST_FIELDS = (
    "worker_wall_seconds",
    "fit_wall_seconds",
    "cpu_user_seconds",
    "cpu_system_seconds",
    "callback_calls_during_fit",
    "adapter_call_wall_seconds",
)


def freeze_software(consumed):
    software = restarts.freeze_software(consumed)
    profile.configuration()
    names = {
        profile.PLAN,
        profile.CONFIGURATION,
        *profile.RUNTIME.values(),
        BRIDGE,
        "scripts/run_iteration_time.py",
        "scripts/check_iteration_time.py",
        "scripts/check_time_budget_dynamics.py",
    }
    for name in sorted(names):
        raw = (ROOT / name).read_bytes()
        if raw != consumed.git_file(software["software_commit"], name):
            raise ValueError("Uncommitted time-budget source: " + name)
        if name in {profile.PLAN, profile.CONFIGURATION} and raw != consumed.git_file(
            profile.PLAN_COMMIT, name
        ):
            raise ValueError("Changed frozen time-budget protocol.")
        consumed.add(ROOT / name, raw)
        software["source_sha256"][name] = sources.sha256(raw)
    return software


@contextmanager
def one_cpu():
    original = os.sched_getaffinity(0)
    try:
        os.sched_setaffinity(0, {min(original)})
        yield
    finally:
        os.sched_setaffinity(0, original)


def call_bridge(action, output, request, inputs, consumed, log, verification=None):
    consumed.check()
    deadline = consumed.clock.started + consumed.clock.seconds
    command, environment = cross.bridge_command(
        ROOT, action, "outer", output, request, deadline
    )
    command[4] = str(ROOT / BRIDGE)
    index = command.index("--kind")
    del command[index : index + 2]
    command += ["--inputs", str(inputs)]
    environment.update(profile.JULIA_THREADS)
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
                raise RuntimeError("Time-budget adapter failed; inspect " + str(log))
        except BaseException:
            _stop_worker(child)
            raise
    consumed.check()
    return time.monotonic() - started


def arrays_from(raw):
    with np.load(io.BytesIO(raw), allow_pickle=False) as saved:
        return {key: saved[key].copy() for key in saved.files}


def require_arrays(actual, expected):
    if {k: sources.fingerprint(v) for k, v in actual.items()} != {
        k: sources.fingerprint(v) for k, v in expected.items()
    }:
        raise ValueError("Stored input/grid roles or Float64 bits differ.")


def load_json(directory, name):
    return sources.read_json((directory / name).read_bytes())


def cell_record(directory, plan, arrays, irregular, *, reused=False):
    outcome = load_json(directory, "outcome.json")
    metadata = load_json(directory, "worker/metadata.json")
    status = load_json(directory, "worker/status.json")
    costs = {field: None for field in COST_FIELDS}
    costs.update(
        worker_wall_seconds=status.get("total_wall_seconds"),
        fit_wall_seconds=metadata.get("fit_wall_seconds"),
        adapter_call_wall_seconds=load_json(directory, "timing.json")["run_seconds"],
    )
    record = {
        "plan": plan,
        "reused": reused,
        "status": outcome["status"],
        "outcome": outcome,
        "costs": costs,
        "cost_scope": "worker/status.json total_wall_seconds: parent setup, worker launch/wait and result read; excludes adapter diagnostics",
        "compilation_seconds": "not_observed",
        "completed_outer_rounds": None,
        "stop": outcome.get(
            "failure_kind", "historical_completion_without_native_counter"
        ),
        "A": False,
        "A_and_original_family": False,
        "curve_grade": "no_output",
        "original_family_status": "no_output",
    }
    if not reused:
        resource = outcome["resources"]
        costs.update(
            {key: resource[key] for key in ("cpu_user_seconds", "cpu_system_seconds")}
        )
        record["worker_process_resources"] = resource
    if outcome["status"] == "completed":
        verified = load_json(directory, "verified.json")
        front = load_json(directory, "worker/result.json")
        assessments = restarts.assess_front(front, arrays, irregular)
        index = front["selected_index"]
        selected = assessments[index]
        grade = selected["supplemental"]["curve"]["grade"]
        family = selected["supplemental"]["original_family"]["status"]
        record.update(
            selected=front["candidates"][index],
            selected_assessment=selected,
            front_assessments=assessments,
            curve_grade=grade,
            original_family_status=family,
            A=grade == "A",
            A_and_original_family=grade == "A" and family == "proven_member",
            any_front_A=any(
                r["supplemental"]["curve"]["grade"] == "A" for r in assessments
            ),
            source_result_sha256=sources.sha256(
                (directory / "worker/result.json").read_bytes()
            ),
        )
        costs["callback_calls_during_fit"] = verified["callback_calls_during_fit"]
        if not reused:
            record.update(
                stop=outcome["stop"]["reason"],
                completed_outer_rounds=outcome["stop"]["clock"][
                    "completed_outer_rounds"
                ],
            )
    elif outcome["status"] != "worker_failed":
        raise ValueError("Incomplete planned time-budget cell.")
    cost_totals([record])
    return record


def cost_totals(cells):
    for cell in cells:
        for field in COST_FIELDS:
            value = cell["costs"][field]
            if value is not None and (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or value < 0
                or (field == "callback_calls_during_fit" and type(value) is not int)
            ):
                raise ValueError("Invalid measured cost: " + field)
    return {
        field: sum(c["costs"][field] for c in cells)
        if all(c["costs"][field] is not None for c in cells)
        else None
        for field in COST_FIELDS
    }


def comparison(cells):
    expected = {(seed, arm) for seed in profile.SEEDS for arm in ("I", "Z")}
    identities = [(cell["plan"]["seed"], cell["plan"]["arm"]) for cell in cells]
    if (
        len(cells) != 8
        or set(identities) != expected
        or any(cell["status"] not in {"completed", "worker_failed"} for cell in cells)
    ):
        raise ValueError(
            "Both arms must retain all four fixed cases, including failures."
        )
    totals = {}
    for arm in ("I", "Z"):
        group = [c for c in cells if c["plan"]["arm"] == arm]
        totals[arm] = {
            "denominator": 4,
            "A": sum(c["A"] for c in group),
            "A_and_original_family": sum(c["A_and_original_family"] for c in group),
            "failures": sum(c["status"] == "worker_failed" for c in group),
            "costs": cost_totals(group),
        }
    delta = totals["Z"]["A"] - totals["I"]["A"]
    worker = [totals[a]["costs"]["worker_wall_seconds"] for a in ("I", "Z")]
    decision = (
        "no_demonstrated_curve_gain"
        if delta == 0
        else "deterioration"
        if delta < 0
        else (
            "quality_gain_costs_incomplete"
            if any(v is None for v in worker)
            else "positive_development_signal"
            if worker[1] <= worker[0]
            else "quality_gain_with_more_cost"
        )
    )
    pairs = []
    for seed in profile.SEEDS:
        pair = {c["plan"]["arm"]: c for c in cells if c["plan"]["seed"] == seed}
        pairs.append(
            {
                "seed": seed,
                **{
                    arm: {
                        key: pair[arm][key]
                        for key in (
                            "status",
                            "curve_grade",
                            "original_family_status",
                            "A",
                            "A_and_original_family",
                            "costs",
                            "stop",
                        )
                    }
                    for arm in ("I", "Z")
                },
            }
        )
    return {
        "totals": totals,
        "pairs": pairs,
        "A_difference_Z_minus_I": delta,
        "interpretation": decision,
        "all_costs_observed": all(
            v is not None for a in totals.values() for v in a["costs"].values()
        ),
        "general_success_probability": "not_assessed",
        "automatic_execution": False,
    }


def summary(report):
    lines = [
        "# Iterationen gegenüber Suchzeit",
        "",
        f"Modus: `{report['mode']}`, Umfang: `{report['scope']}`.",
        "",
    ]
    if report["comparison"] is not None:
        lines += [
            "| Arm | A / geplant | A und Originalfamilie |",
            "| --- | --- | --- |",
        ]
        for arm, value in report["comparison"]["totals"].items():
            lines.append(
                f"| {arm} | {value['A']}/4 | {value['A_and_original_family']}/4 |"
            )
        lines += [
            "",
            "Einordnung: `" + report["comparison"]["interpretation"] + "`.",
            "",
        ]
    lines += [
        "Alle Paarungen, Ausfälle, kontinuierlichen Fehler und getrennten Kosten stehen im JSON-Bericht.",
        "Unbekannte Kosten sind nicht null. Keine allgemeine Erfolgswahrscheinlichkeit; neue Parameterübereinstimmungen nicht bewertet.",
    ]
    return "\n".join(lines) + "\n"


def bound_inventory(root, plans):
    required = {"anchor.npz", "irregular.npz", "preparation.json"}
    for plan in plans:
        number = plan["number"]
        prefix = f"cell-{number:02d}/"
        prepared = load_json(root / prefix, "prepared.json")
        required.update(prefix + name for name in prepared["files"])
        required.update(
            {
                prefix + "prepared.json",
                f"request-{number:02d}.json",
                f"cell-{number:02d}-prepare.log",
            }
        )
    return required


def hold_inventory(consumed, root, files):
    restarts.freeze_files(consumed, root, files)
    expected = {name: sources.sha256(raw) for name, raw in files.items()}

    def unchanged():
        if {
            name: sources.sha256(raw) for name, raw in restarts.raw_files(root).items()
        } != expected:
            raise ValueError("Time-budget artifact inventory changed.")

    consumed.callbacks.append(unchanged)
    return expected


def controls_context(archive, digest, consumed, parent):
    return (
        controls.verified_archive(archive, digest, consumed, parent)
        if archive
        else nullcontext((None, None))
    )


def imported_cells(source, arrays, irregular, technical):
    slots = [1] if technical else profile.configuration()["reuse_cells"]
    seeds = [73] if technical else list(profile.SEEDS)
    return [
        cell_record(
            source / f"cell-{number:02d}",
            {
                "number": number,
                "block": block + 1,
                "seed": seed,
                "arm": "I",
                "condition": "historical_local_300_5",
                "niterations": 2 if technical else 2000,
            },
            arrays,
            irregular,
            reused=True,
        )
        for block, (number, seed) in enumerate(zip(slots, seeds, strict=True))
    ]


def run(
    output,
    *,
    mode="reuse_pr76",
    reason="",
    archive=None,
    archive_sha256=None,
    technical=False,
):
    plans = bridge.cells(mode, technical)
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Record the execution-mode reason before any new fit.")
    if (archive is None) != (archive_sha256 is None) or (
        mode == "reuse_pr76" and archive is None
    ):
        raise ValueError(
            "Reuse requires the original PR76 archive and SHA-256; no automatic fallback."
        )
    if not technical:
        cross.scientific_platform()
    output = publication.validate_output(output)
    output.mkdir(parents=True)
    state = {
        "format": FORMAT,
        "status": "preparing",
        "mode": mode,
        "scope": "technical" if technical else "scientific",
        "cells": [{"plan": plan, "status": "planned"} for plan in plans],
    }
    _write_json(output / "run_state.json", state)

    def build(consumed):
        software = freeze_software(consumed)
        arrays = (
            profile.load_module(
                ROOT / cross.BRIDGE, "time_input_arrays"
            ).technical_arrays()
            if technical
            else cross.anchor_arrays()
        )
        irregular = restarts.grid(technical)
        old_cells, finding = [], None
        with (
            one_cpu(),
            controls_context(archive, archive_sha256, consumed, output.parent) as (
                source,
                identity,
            ),
        ):
            if source is not None:
                finding = controls.eligibility(source, identity, technical)
            if mode == "reuse_pr76":
                if not finding["eligible"]:
                    _write_json(output / "control_eligibility.json", finding)
                    raise ValueError(
                        "Whole PR76 arm is not reusable; inspect control_eligibility.json. Explicit fresh_all remains separate."
                    )
                require_arrays(
                    arrays_from((source / "anchor.npz").read_bytes()), arrays
                )
                actual_grid = arrays_from((source / "irregular.npz").read_bytes())
                require_arrays(actual_grid, irregular)
                irregular = actual_grid
                (output / "irregular.npz").write_bytes(
                    (source / "irregular.npz").read_bytes()
                )
                old_cells = imported_cells(source, arrays, irregular, technical)
            else:
                np.savez(output / "irregular.npz", **irregular)
            np.savez(output / "anchor.npz", **arrays)
            preparation = {
                "format": FORMAT,
                "scope": state["scope"],
                "mode": mode,
                "reason": reason,
                "software": software,
                "provenance": _provenance(),
                "plans": plans,
                "protocol_commit": profile.PLAN_COMMIT,
                "control_eligibility": finding,
                "archive_sha256": archive_sha256,
                "started_at_utc": _utc_now(),
            }
            _write_json(output / "preparation.json", preparation)
            restarts.freeze_files(
                consumed,
                output,
                {
                    n: r
                    for n, r in restarts.raw_files(output).items()
                    if n != "run_state.json"
                },
            )
            environment = runtime = None
            for plan in plans:
                number = plan["number"]
                request = output / f"request-{number:02d}.json"
                _write_json(
                    request,
                    bridge.request_for(
                        plan,
                        output / "anchor.npz",
                        mode,
                        software["software_commit"],
                        technical,
                    ),
                )
                destination = output / f"cell-{number:02d}"
                call_bridge(
                    "prepare",
                    destination,
                    request,
                    output / "anchor.npz",
                    consumed,
                    output / f"cell-{number:02d}-prepare.log",
                )
                options = load_json(destination, "options.json")
                current = cross.environment_key(options["initial"]["environment"])
                current_runtime = options["budget_runtime"]
                if environment is not None and (
                    environment != current or runtime != current_runtime
                ):
                    raise ValueError(
                        "Environment or hardware/threads differ before the first fit."
                    )
                environment, runtime = current, current_runtime
                if mode == "reuse_pr76" and any(
                    c["environment"] != environment or c["budget_runtime"] != runtime
                    for c in finding["controls"]
                ):
                    raise ValueError(
                        "PR76 controls differ from the new preparation environment/runtime."
                    )
                restarts.freeze_files(
                    consumed,
                    output,
                    {
                        n: r
                        for n, r in restarts.raw_files(output).items()
                        if n != "run_state.json"
                    },
                )
            bound = {
                n: sources.sha256(r)
                for n, r in restarts.raw_files(output).items()
                if n != "run_state.json"
            }
            if set(bound) != bound_inventory(output, plans):
                raise ValueError("Incomplete pre-search inventory.")
            _write_json(output / "prepared_bindings.json", bound)
            consumed.add(
                output / "prepared_bindings.json",
                (output / "prepared_bindings.json").read_bytes(),
            )
            consumed.git_file.clear()
            for slot in state["cells"]:
                number = slot["plan"]["number"]
                destination = output / f"cell-{number:02d}"
                slot["status"] = "running"
                _write_json(output / "run_state.json", state)
                elapsed = call_bridge(
                    "run",
                    destination,
                    output / f"request-{number:02d}.json",
                    output / "anchor.npz",
                    consumed,
                    output / f"cell-{number:02d}-run.log",
                )
                _write_json(destination / "timing.json", {"run_seconds": elapsed})
                # Verify each attempt, including allowed failures, before accepting it.
                call_bridge(
                    "verify",
                    destination,
                    output / f"request-{number:02d}.json",
                    output / "anchor.npz",
                    consumed,
                    output / f"cell-{number:02d}-verify.log",
                    output / f"cell-{number:02d}-verification.json",
                )
                outcome = load_json(destination, "outcome.json")
                slot["status"] = outcome["status"]
                if outcome["status"] == "completed":
                    evidence = load_json(destination, "verified.json")
                    if any(
                        cross.environment_key(evidence[k]) != environment
                        for k in ("environment", "environment_after_search")
                    ):
                        raise ValueError("Numerical environment changed during search.")
                restarts.freeze_files(
                    consumed,
                    output,
                    {
                        n: r
                        for n, r in restarts.raw_files(output).items()
                        if n != "run_state.json"
                    },
                )
            cells = old_cells + [
                cell_record(output / f"cell-{p['number']:02d}", p, arrays, irregular)
                for p in plans
            ]
            if technical and mode == "fresh_all":
                if not cross.comparison(
                    load_json(output / "cell-01", "verified.json"),
                    load_json(output / "cell-04", "verified.json"),
                )["all_search_features_equal"]:
                    raise ValueError("Repeated technical iteration front differs.")
                if [c["stop"] for c in cells] != [
                    "iteration_limit",
                    "regular_timeout",
                    "iteration_reserve",
                    "iteration_limit",
                ]:
                    raise ValueError("Technical stopping reasons differ.")
        state["status"] = "completed"
        _write_json(output / "run_state.json", state)
        expected = hold_inventory(consumed, output, restarts.raw_files(output))
        report = {
            "format": FORMAT,
            "scope": state["scope"],
            "mode": mode,
            "software": software,
            "cells": cells,
            "comparison": None if technical else comparison(cells),
            "real_new_search_calls": len(plans),
            "historical_costs": cost_totals(old_cells),
            "new_costs": cost_totals([c for c in cells if not c["reused"]]),
            "algorithm_costs": cost_totals(cells),
            "control_eligibility": finding,
            "total_wall_seconds": time.monotonic() - consumed.clock.started,
            "physical_parameter_match": "not_assessed",
            "finished_at_utc": _utc_now(),
        }
        return (
            report,
            summary(report),
            {"raw_checksums.json": sources.json_bytes(expected)},
        )

    try:
        return publication.export_transaction(
            output / "completion", build, seconds=profile.LIMIT_SECONDS
        )
    except BaseException as error:
        state.update(status="aborted", error=f"{type(error).__name__}: {error}")
        for slot in state["cells"]:
            if slot["status"] == "running":
                slot["status"] = "aborted"
        _write_json(output / "run_state.json", state)
        raise


def verify(source, output, *, archive=None, archive_sha256=None):
    """Recompute all assessments and bindings, without native searches or fits."""
    source, output = Path(source).absolute(), Path(output).absolute()
    if (
        source != source.resolve()
        or source == output
        or output.is_relative_to(source)
        or source.is_relative_to(output)
    ):
        raise ValueError("Use a separate read-verification destination.")

    def build(consumed):
        software = freeze_software(consumed)
        completion = source / "completion"
        if (completion / publication.LOCK).exists():
            raise ValueError("Source comparison is locked.")
        manifest = load_json(completion, publication.MANIFEST)
        if set(manifest) != {
            publication.REPORT,
            publication.SUMMARY,
            "raw_checksums.json",
        }:
            raise ValueError("Incomplete comparison manifest.")
        for name, digest in manifest.items():
            raw = (completion / name).read_bytes()
            if sources.sha256(raw) != digest:
                raise ValueError("Completion checksum differs.")
            consumed.add(completion / name, raw)
        consumed.add(
            completion / publication.MANIFEST,
            (completion / publication.MANIFEST).read_bytes(),
        )
        original = load_json(completion, publication.REPORT)
        if (
            original["format"] != FORMAT
            or original["status"] != "completed"
            or original["scope"] not in {"technical", "scientific"}
        ):
            raise ValueError("No completed iteration/time comparison.")
        prepared = load_json(source, "preparation.json")
        if prepared["software"] != software or original["software"] != software:
            raise ValueError(
                "Verify from the exact clean execution checkout and runtime."
            )
        if (
            prepared["format"] != FORMAT
            or prepared["scope"] != original["scope"]
            or prepared["protocol_commit"] != profile.PLAN_COMMIT
            or not prepared["reason"].strip()
        ):
            raise ValueError("Changed bound execution mode/protocol.")
        if prepared["mode"] != original["mode"]:
            raise ValueError("Changed execution mode.")
        files = restarts.raw_files(source)
        expected = load_json(completion, "raw_checksums.json")
        if {n: sources.sha256(r) for n, r in files.items()} != expected:
            raise ValueError("Original raw inventory/checksums differ.")
        hold_inventory(consumed, source, files)

        def unlocked():
            if (completion / publication.LOCK).exists():
                raise ValueError("Source release was revoked.")

        consumed.callbacks.append(unlocked)
        technical, mode = original["scope"] == "technical", original["mode"]
        plans = bridge.cells(mode, technical)
        if prepared["plans"] != plans:
            raise ValueError("Planned cell list changed.")
        bound = load_json(source, "prepared_bindings.json")
        if set(bound) != bound_inventory(source, plans) or any(
            expected.get(n) != digest for n, digest in bound.items()
        ):
            raise ValueError("Pre-search binding inventory differs.")
        arrays, irregular = (
            arrays_from(files["anchor.npz"]),
            arrays_from(files["irregular.npz"]),
        )
        require_arrays(irregular, restarts.grid(technical))
        if (
            archive_sha256 != prepared["archive_sha256"]
            or (archive is None) != (archive_sha256 is None)
            or (mode == "reuse_pr76" and archive is None)
        ):
            raise ValueError("Supply the same original control archive/SHA-256.")
        old_cells, finding = [], None
        with (
            controls_context(archive, archive_sha256, consumed, output.parent) as (
                control_source,
                identity,
            ),
            tempfile.TemporaryDirectory(
                prefix=".time-replay-", dir=output.parent
            ) as temporary,
        ):
            if control_source is not None:
                finding = controls.eligibility(control_source, identity, technical)
            if (
                finding != prepared["control_eligibility"]
                or finding != original["control_eligibility"]
            ):
                raise ValueError("Control eligibility evidence changed.")
            if mode == "reuse_pr76":
                if not finding["eligible"]:
                    raise ValueError("Unconfirmed reused control arm.")
                require_arrays(
                    arrays_from((control_source / "anchor.npz").read_bytes()), arrays
                )
                if (
                    files["irregular.npz"]
                    != (control_source / "irregular.npz").read_bytes()
                ):
                    raise ValueError("Original diagnostic points were not preserved.")
                old_cells = imported_cells(control_source, arrays, irregular, technical)
            for plan in plans:
                number = plan["number"]
                request = source / f"request-{number:02d}.json"
                if load_json(source, request.name)["cell"] != plan:
                    raise ValueError("Cell assigned to the wrong slot.")
                call_bridge(
                    "verify",
                    source / f"cell-{number:02d}",
                    request,
                    source / "anchor.npz",
                    consumed,
                    Path(temporary) / f"{number}.log",
                    Path(temporary) / f"{number}.json",
                )
        actual = old_cells + [
            cell_record(source / f"cell-{p['number']:02d}", p, arrays, irregular)
            for p in plans
        ]
        if sources.json_bytes(actual) != sources.json_bytes(original["cells"]):
            raise ValueError("Recomputed original assessments/costs differ.")
        if original["comparison"] != (None if technical else comparison(actual)):
            raise ValueError("Paired interpretation differs.")
        for key, value in {
            "real_new_search_calls": len(plans),
            "historical_costs": cost_totals(old_cells),
            "new_costs": cost_totals([c for c in actual if not c["reused"]]),
            "algorithm_costs": cost_totals(actual),
            "physical_parameter_match": "not_assessed",
        }.items():
            if original[key] != value:
                raise ValueError(
                    "Changed call count, costs or parameter status: " + key
                )
        return (
            {
                "format": FORMAT + "-verification",
                "software": software,
                "scope": original["scope"],
                "verified_cells": len(actual),
                "search_calls": 0,
                "source_report_sha256": sources.sha256(
                    (completion / publication.REPORT).read_bytes()
                ),
            },
            "# Lesende Verifikation\n\nAlle geplanten Fälle, Originalauswahlen und Kosten geprüft; keine Suche.\n",
            {},
        )

    return publication.export_transaction(output, build, seconds=3600)
