"""Run and verify one frozen global-restart development comparison."""

import io
import math
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import future_assessment as future
from . import outer_search_ladder as ladder
from . import remainder_assessment as remainder
from . import seed_driver_crosscheck as cross
from . import structure_assessment as structure
from .pilot import _provenance, _utc_now, _write_json
from .search_duration import load_module
from .signals import ringdown_signal
from .supplemental_assessment import grade_curve
from .symbolic import ROOT, SearchBudget, _stop_worker, select_candidate

FORMAT = "ringdown-sr-global-restart-comparison-1"
BRIDGE = "scripts/global_restart_bridge.py"
bridge = load_module(ROOT / BRIDGE, "restart_protocol_bridge")
ARMS = ("reference", "long", "restarts")


def grid(technical=False):
    """Draw one independent, nonlattice point in each predetermined stratum."""
    config = bridge.configuration()
    rng = np.random.Generator(np.random.PCG64(config["grid_seed"]))
    span = 7 / 8 if technical else 127 / 4096
    values = []
    for index in range(config["grid_points"]):
        for _ in range(config["grid_attempts"]):
            fraction = rng.random()
            value = (index + fraction) / config["grid_points"] * span
            if 0 < fraction < 1 and not (value * 32768).is_integer():
                values.append(value)
                break
        else:
            raise ValueError("Could not generate the frozen nonlattice grid.")
    times = np.array(values, dtype=np.float64)
    truth = (
        1 + times
        if technical
        else ringdown_signal(
            times, amplitude=1, frequency_hz=250, decay_time_s=0.008, phase_rad=0
        )
    )
    return {"time_s": times, "truth": truth}


def freeze_software(consumed):
    software = future.freeze_software(consumed)
    bridge.configuration()
    for name, digest in bridge.PLAN_HASHES.items():
        raw = (ROOT / name).read_bytes()
        if sources.sha256(raw) != digest or raw != consumed.git_file(
            bridge.PLAN_COMMIT, name
        ):
            raise ValueError("Missing or changed frozen protocol commit.")
        consumed.add(ROOT / name, raw)
        software["source_sha256"][name] = digest
    # The historical worker is immutable; current input/legacy bridge bytes
    # must also be in the execution snapshot before any search starts.
    for name in (
        cross.BRIDGE,
        BRIDGE,
        "scripts/run_global_restarts.py",
        "scripts/check_global_restarts.py",
        "data/transfer_check_inputs.npz",
        "data/transfer_check_inputs.json",
    ):
        raw = (ROOT / name).read_bytes()
        if raw != consumed.git_file(software["software_commit"], name):
            raise ValueError("Uncommitted restart source: " + name)
        consumed.add(ROOT / name, raw)
        software["source_sha256"][name] = sources.sha256(raw)
    return software


def raw_files(root):
    files = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts[0] == "completion":
            continue
        if path.is_symlink():
            raise ValueError("Restart evidence must not contain symlinks.")
        if path.is_file():
            files[relative.as_posix()] = path.read_bytes()
    return files


def freeze_files(consumed, root, files):
    for name, raw in files.items():
        consumed.add(root / name, raw)


@contextmanager
def historical_checkout(parent):
    """Own exactly one temporary detached worktree and retain failed cleanup."""
    directory = Path(tempfile.mkdtemp(prefix=".restart-worker-", dir=parent))
    checkout = directory / "checkout"
    owned = False
    try:
        cross.git(
            "worktree",
            "add",
            "--detach",
            str(checkout),
            bridge.configuration()["worker_commit"],
        )
        owned = True
        for name in (
            "uv.lock",
            "pyproject.toml",
            ".python-version",
            "julia/Project.toml",
            "julia/Manifest.toml",
            "src/ringdown_sr/juliapkg.json",
        ):
            if (checkout / name).read_bytes() != (ROOT / name).read_bytes():
                raise ValueError("Historical dependency pins differ: " + name)
        yield checkout
    finally:
        if owned:
            cross.git("worktree", "remove", str(checkout))
        directory.rmdir()


def call_bridge(
    checkout, action, output, request, inputs, consumed, log, verification=None
):
    consumed.check()
    deadline = consumed.clock.started + consumed.clock.seconds
    command, environment = cross.bridge_command(
        checkout, action, "outer", output, request, deadline
    )
    command[4] = str(ROOT / BRIDGE)
    position = command.index("--kind")
    del command[position : position + 2]
    command += ["--inputs", str(inputs)]
    if verification is not None:
        command += ["--verification", str(verification)]
    before = time.monotonic()
    with log.open("wb") as stream:
        child = subprocess.Popen(
            command,
            cwd=checkout,
            env=environment,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            code = child.wait(timeout=max(0.01, deadline - time.monotonic()))
            if code:
                raise RuntimeError("Restart adapter failed; inspect " + str(log))
        except BaseException:
            _stop_worker(child)
            raise
    consumed.check()
    return time.monotonic() - before


def package_selection(members):
    """Use native loss, complexity and fixed member order; never diagnostics."""
    admissible = []
    for position, member in enumerate(members):
        if member["status"] != "completed":
            continue
        chosen = member["selected"]
        loss, complexity = chosen["loss"], chosen["complexity"]
        if type(loss) not in (int, float) or not math.isfinite(loss) or loss < 0:
            continue
        if type(complexity) is not int or complexity < 1:
            raise ValueError("Invalid package complexity.")
        admissible.append((loss, complexity, position))
    return min(admissible)[2] if admissible else None


def assess_front(front, arrays, irregular):
    """Preserve every original candidate and the original selection index."""
    selected = front["selected_index"]
    if type(selected) is not int or selected != select_candidate(front["candidates"]):
        raise ValueError("Original native-loss selection changed.")
    binding = structure.interval_binding(arrays["time_s"])
    references = {
        "training": {"time_s": arrays["time_s"], "truth": arrays["observed"]},
        "diagnostic": {
            "time_s": arrays["diagnostic_time_s"],
            "truth": arrays["diagnostic_truth"],
        },
    }
    records = []
    for index, candidate in enumerate(front["candidates"]):
        errors = {
            role: future.endpoint(candidate["tree"], values["time_s"], values["truth"])
            for role, values in references.items()
        }
        record = {
            "source_identity": {
                "original_index": index,
                "original_selected_index": selected,
                "source_candidate_sha256": sources.sha256(
                    sources.json_bytes(candidate)
                ),
            },
            "original_candidate": candidate,
            "curve_errors": errors,
            "irregular_errors": future.endpoint(
                candidate["tree"], irregular["time_s"], irregular["truth"]
            ),
            "supplemental": {"curve": grade_curve(errors, source_verified=True)},
        }
        structure.supplement(record, binding)
        remainder.supplement(record, binding, references)
        records.append(record)
    return records


def costs(members):
    fields = (
        "worker_wall_seconds",
        "callback_calls_during_fit",
        "adapter_call_wall_seconds",
    )
    return {
        field: sum(m["costs"][field] for m in members)
        if all(m["costs"][field] is not None for m in members)
        else None
        for field in fields
    }


def comparison(cells):
    blocks = []
    for block in range(1, 5):
        group = [cell for cell in cells if cell["plan"]["block"] == block]
        if len(group) != 5 or any(
            cell["status"] not in ("completed", "worker_failed") for cell in group
        ):
            raise ValueError(
                "All planned calls, including failures, must be accounted for."
            )
        members = sorted(
            [c for c in group if c["plan"]["member"] is not None],
            key=lambda c: c["plan"]["member"],
        )
        chosen = package_selection(members)
        outputs = {}
        for arm, component, selected in (
            (
                "reference",
                [members[0]],
                0 if members[0]["status"] == "completed" else None,
            ),
            ("long", [group[1]], 0 if group[1]["status"] == "completed" else None),
            ("restarts", members, chosen),
        ):
            cell = component[selected] if selected is not None else None
            record = cell["selected_assessment"] if cell else None
            is_a = (
                record is not None and record["supplemental"]["curve"]["grade"] == "A"
            )
            outputs[arm] = {
                "selected_cell": cell["plan"]["number"] if cell else None,
                "status": "completed" if cell else "worker_failed",
                "grade": record["supplemental"]["curve"]["grade"] if record else None,
                "original_family": record["supplemental"]["original_family"]
                if record
                else None,
                "A": is_a,
                "A_and_original_family": bool(
                    is_a
                    and record["supplemental"]["original_family"]["status"]
                    == "proven_member"
                ),
                "costs": costs(component),
                "members": [c["plan"]["number"] for c in component],
                "failed_members": sum(c["status"] != "completed" for c in component),
                "any_front_A": any(c.get("any_front_A", False) for c in component),
                "any_front_A_and_original_family": any(
                    c.get("any_front_A_and_original_family", False) for c in component
                ),
            }
        blocks.append({"block": block, "outputs": outputs})
    totals = {
        arm: {
            "planned": 4,
            "A": sum(block["outputs"][arm]["A"] for block in blocks),
            "A_and_original_family": sum(
                block["outputs"][arm]["A_and_original_family"] for block in blocks
            ),
            "costs": costs(
                [{"costs": block["outputs"][arm]["costs"]} for block in blocks]
            ),
        }
        for arm in ARMS
    }
    contrasts = {}
    for left, right in (
        ("long", "reference"),
        ("restarts", "reference"),
        ("restarts", "long"),
    ):
        pairs = [
            {
                "block": b["block"],
                "left_A": b["outputs"][left]["A"],
                "right_A": b["outputs"][right]["A"],
                "left_A_and_original_family": b["outputs"][left][
                    "A_and_original_family"
                ],
                "right_A_and_original_family": b["outputs"][right][
                    "A_and_original_family"
                ],
            }
            for b in blocks
        ]
        contrasts[left + "_minus_" + right] = {
            "pairs": pairs,
            **{
                endpoint: totals[left][endpoint] - totals[right][endpoint]
                for endpoint in ("A", "A_and_original_family")
            },
        }
    improved = [
        arm
        for arm in ("long", "restarts")
        if totals[arm]["A"] > totals["reference"]["A"]
    ]
    preferred = None
    if improved:
        best = max(totals[arm]["A"] for arm in improved)
        tied = [arm for arm in improved if totals[arm]["A"] == best]
        if len(tied) == 1:
            preferred = tied[0]
        elif all(
            totals[a]["costs"][k] is not None
            for a in tied
            for k in ("callback_calls_during_fit", "worker_wall_seconds")
        ):
            ordered = sorted(
                tied,
                key=lambda a: (
                    totals[a]["costs"]["callback_calls_during_fit"],
                    totals[a]["costs"]["worker_wall_seconds"],
                ),
            )
            if any(
                totals[ordered[0]]["costs"][key] != totals[ordered[1]]["costs"][key]
                for key in ("callback_calls_during_fit", "worker_wall_seconds")
            ):
                preferred = ordered[0]
    next_step = (
        "consider_profile_adoption_then_independent_confirmation"
        if preferred and totals[preferred]["A"] == 4
        else "profile_decision_open"
        if improved and preferred is None
        else "consider_time_normalization_as_second_intervention"
    )
    return {
        "blocks": blocks,
        "totals": totals,
        "contrasts": contrasts,
        "preferred_development_arm": preferred,
        "next_step": next_step,
        "general_success_probability": "not_assessed",
        "automatic_execution": False,
    }


def assemble(root, plans, arrays, irregular):
    cells = []
    for plan in plans:
        directory = root / f"cell-{plan['number']:02d}"
        outcome = sources.read_json((directory / "outcome.json").read_bytes())
        timing = sources.read_json((directory / "timing.json").read_bytes())
        cell = {
            "plan": plan,
            "status": outcome["status"],
            "outcome": outcome,
            "costs": {
                "worker_wall_seconds": None,
                "callback_calls_during_fit": None,
                "adapter_call_wall_seconds": timing["run_seconds"],
            },
        }
        if outcome["status"] == "completed":
            verified = sources.read_json((directory / "verified.json").read_bytes())
            front = sources.read_json((directory / "worker/result.json").read_bytes())
            records = assess_front(front, arrays, irregular)
            index = front["selected_index"]
            cell.update(
                selected=front["candidates"][index],
                selected_assessment=records[index],
                front_assessments=records,
                source_result_sha256=sources.sha256(
                    (directory / "worker/result.json").read_bytes()
                ),
            )
            cell["costs"].update(
                {
                    k: verified[k]
                    for k in ("worker_wall_seconds", "callback_calls_during_fit")
                }
            )
            cell["any_front_A"] = any(
                r["supplemental"]["curve"]["grade"] == "A" for r in records
            )
            cell["any_front_A_and_original_family"] = any(
                r["supplemental"]["curve"]["grade"] == "A"
                and r["supplemental"]["original_family"]["status"] == "proven_member"
                for r in records
            )
        elif outcome["status"] == "worker_failed":
            # Preserve measured attempt time separately from unavailable fit
            # counters and worker-only timing; never substitute a zero cost.
            cell["failed_attempt_wall_seconds"] = outcome["adapter_run_wall_seconds"]
        else:
            raise ValueError("Unfinished planned cell.")
        cells.append(cell)
    return cells


def summary(report):
    lines = [
        "# Vergleich globaler Neustarts",
        "",
        f"Umfang: `{report['scope']}`.",
        "",
        "Originalauswahlen und Kosten in assessment_report.json; kein allgemeiner Erfolgsnachweis.",
        "",
    ]
    if report["comparison"] is not None:
        lines += [
            "| Arm | A / geplant | A und Originalfamilie |",
            "| --- | --- | --- |",
        ]
        for name, value in report["comparison"]["totals"].items():
            lines.append(
                f"| {name} | {value['A']}/4 | {value['A_and_original_family']}/4 |"
            )
        lines += [
            "",
            "Anschlussvorschlag: `" + report["comparison"]["next_step"] + "`.",
        ]
    return "\n".join(lines) + "\n"


def run(output, *, technical=False):
    if not technical:
        cross.scientific_platform()
    output = publication.validate_output(output)
    output.mkdir(parents=True)
    plans = bridge.cells(technical)
    state = {
        "format": FORMAT,
        "scope": "technical" if technical else "scientific",
        "status": "preparing",
        "cells": [{"plan": plan, "status": "planned"} for plan in plans],
    }
    _write_json(output / "run_state.json", state)

    def build(consumed):
        software = freeze_software(consumed)
        arrays = (
            load_module(ROOT / cross.BRIDGE, "restart_input_bridge").technical_arrays()
            if technical
            else cross.anchor_arrays()
        )
        irregular = grid(technical)
        np.savez(output / "anchor.npz", **arrays)
        np.savez(output / "irregular.npz", **irregular)
        _write_json(
            output / "preparation.json",
            {
                "format": FORMAT,
                "scope": state["scope"],
                "software": software,
                "provenance": _provenance(),
                "plans": plans,
                "started_at_utc": _utc_now(),
                "protocol_commit": bridge.PLAN_COMMIT,
                "protocol": bridge.PLAN_HASHES,
                "historical_reference_reuse": False,
                "search_profiles": [
                    ladder.profile_parameters(
                        SearchBudget(seed=p["seed"], niterations=p["niterations"]),
                        "local_300_5",
                    )
                    for p in plans
                ],
            },
        )
        freeze_files(
            consumed,
            output,
            {n: r for n, r in raw_files(output).items() if n != "run_state.json"},
        )
        with historical_checkout(output.parent) as checkout:
            environment = None
            for plan in plans:
                number = plan["number"]
                request = output / f"request-{number:02d}.json"
                _write_json(
                    request, bridge.request_for(plan, output / "anchor.npz", technical)
                )
                destination = output / f"cell-{number:02d}"
                call_bridge(
                    checkout,
                    "prepare",
                    destination,
                    request,
                    output / "anchor.npz",
                    consumed,
                    output / f"cell-{number:02d}-prepare.log",
                )
                options = sources.read_json((destination / "options.json").read_bytes())
                current = cross.environment_key(options["initial"]["environment"])
                if environment is not None and environment != current:
                    raise ValueError(
                        "Numerical environments differ before the first search."
                    )
                environment = current
                freeze_files(
                    consumed,
                    output,
                    {
                        n: r
                        for n, r in raw_files(output).items()
                        if n != "run_state.json"
                    },
                )
            bound = {
                n: sources.sha256(r)
                for n, r in raw_files(output).items()
                if n != "run_state.json"
            }
            _write_json(output / "prepared_bindings.json", bound)
            consumed.add(
                output / "prepared_bindings.json",
                (output / "prepared_bindings.json").read_bytes(),
            )
            for slot in state["cells"]:
                plan = slot["plan"]
                number = plan["number"]
                destination = output / f"cell-{number:02d}"
                slot["status"] = "running"
                _write_json(output / "run_state.json", state)
                elapsed = call_bridge(
                    checkout,
                    "run",
                    destination,
                    output / f"request-{number:02d}.json",
                    output / "anchor.npz",
                    consumed,
                    output / f"cell-{number:02d}-run.log",
                )
                _write_json(destination / "timing.json", {"run_seconds": elapsed})
                outcome = sources.read_json((destination / "outcome.json").read_bytes())
                slot["status"] = outcome["status"]
                if outcome["status"] == "completed":
                    evidence = sources.read_json(
                        (destination / "verified.json").read_bytes()
                    )
                    if any(
                        cross.environment_key(evidence[k]) != environment
                        for k in ("environment", "environment_after_search")
                    ):
                        raise ValueError("Numerical environment changed during search.")
                consumed.check()
                freeze_files(
                    consumed,
                    output,
                    {
                        n: r
                        for n, r in raw_files(output).items()
                        if n != "run_state.json"
                    },
                )
        cells = assemble(output, plans, arrays, irregular)
        if technical:
            first, last = [
                sources.read_json((output / f"cell-{n:02d}/verified.json").read_bytes())
                for n in (1, 3)
            ]
            if not cross.comparison(first, last)["all_search_features_equal"]:
                raise ValueError("Repeated technical front differs.")
        state["status"] = "completed"
        _write_json(output / "run_state.json", state)
        files = raw_files(output)
        freeze_files(consumed, output, files)
        expected = {n: sources.sha256(r) for n, r in files.items()}

        def unchanged_inventory():
            if {n: sources.sha256(r) for n, r in raw_files(output).items()} != expected:
                raise ValueError("Restart artifact inventory changed.")

        consumed.callbacks.append(unchanged_inventory)
        report = {
            "format": FORMAT,
            "scope": state["scope"],
            "software": software,
            "cells": cells,
            "comparison": None if technical else comparison(cells),
            "real_new_search_calls": len(plans),
            "historical_costs": 0,
            "actual_costs": costs(cells),
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
            output / "completion",
            build,
            seconds=3600 if technical else bridge.configuration()["total_seconds"],
        )
    except BaseException as error:
        state.update(status="aborted", error=f"{type(error).__name__}: {error}")
        for slot in state["cells"]:
            if slot["status"] == "running":
                slot["status"] = "aborted"
        _write_json(output / "run_state.json", state)
        raise


def verify(source, output):
    """Read every original byte and rerun native replays, with no fitting call."""
    source = Path(source).absolute()
    output = Path(output).absolute()
    if (
        source == output
        or output.is_relative_to(source)
        or source.is_relative_to(output)
    ):
        raise ValueError("Verification must use a separate output directory.")

    def build(consumed):
        software = freeze_software(consumed)
        if (source / "completion" / publication.LOCK).exists():
            raise ValueError("Source completion is locked.")
        completion = source / "completion"
        manifest = sources.read_json((completion / publication.MANIFEST).read_bytes())
        for name, digest in manifest.items():
            if len(sources.safe_name(name).parts) != 1:
                raise ValueError("Invalid completion manifest name.")
            raw = (completion / name).read_bytes()
            if sources.sha256(raw) != digest:
                raise ValueError("Source completion checksum differs.")
            consumed.add(completion / name, raw)
        consumed.add(
            completion / publication.MANIFEST,
            (completion / publication.MANIFEST).read_bytes(),
        )
        original = sources.read_json((completion / publication.REPORT).read_bytes())
        if (
            original["format"] != FORMAT
            or original["status"] != "completed"
            or original["scope"] not in ("technical", "scientific")
        ):
            raise ValueError("No completed comparison source.")
        expected = sources.read_json((completion / "raw_checksums.json").read_bytes())
        files = raw_files(source)
        if {n: sources.sha256(r) for n, r in files.items()} != expected:
            raise ValueError("Original raw evidence inventory or checksums differ.")
        freeze_files(consumed, source, files)

        def unchanged():
            if (completion / publication.LOCK).exists() or {
                n: sources.sha256(r) for n, r in raw_files(source).items()
            } != expected:
                raise ValueError("Original comparison changed during verification.")

        consumed.callbacks.append(unchanged)
        prepared = sources.read_json(files["preparation.json"])
        if (
            prepared["software"]["source_sha256"] != software["source_sha256"]
            or original["software"] != prepared["software"]
        ):
            raise ValueError("Executed and verifying sources differ.")
        for name, digest in prepared["software"]["source_sha256"].items():
            if (
                sources.sha256(
                    consumed.git_file(prepared["software"]["software_commit"], name)
                )
                != digest
            ):
                raise ValueError("Missing original execution source binding.")
        technical = original["scope"] == "technical"
        plans = bridge.cells(technical)
        if (
            prepared["plans"] != plans
            or prepared["protocol"] != bridge.PLAN_HASHES
            or prepared["protocol_commit"] != bridge.PLAN_COMMIT
        ):
            raise ValueError("Executed protocol differs.")
        bound = sources.read_json(files["prepared_bindings.json"])
        if any(expected.get(n) != digest for n, digest in bound.items()):
            raise ValueError("Pre-search bindings differ.")
        with np.load(io.BytesIO(files["anchor.npz"]), allow_pickle=False) as saved:
            arrays = {key: saved[key].copy() for key in saved.files}
        with np.load(io.BytesIO(files["irregular.npz"]), allow_pickle=False) as saved:
            irregular = {key: saved[key].copy() for key in saved.files}
        if {k: sources.fingerprint(v) for k, v in irregular.items()} != {
            k: sources.fingerprint(v) for k, v in grid(technical).items()
        }:
            raise ValueError(
                "Stored diagnostic grid differs from its frozen generator."
            )
        with (
            historical_checkout(output.parent) as checkout,
            tempfile.TemporaryDirectory(
                prefix=".restart-replay-", dir=output.parent
            ) as temporary,
        ):
            replay = Path(temporary)
            for plan in plans:
                number = plan["number"]
                request = sources.read_json(files[f"request-{number:02d}.json"])
                if request["cell"] != plan:
                    raise ValueError("Cell request assigned to the wrong slot.")
                call_bridge(
                    checkout,
                    "verify",
                    source / f"cell-{number:02d}",
                    source / f"request-{number:02d}.json",
                    source / "anchor.npz",
                    consumed,
                    replay / f"{number}.log",
                    replay / f"{number}.json",
                )
        actual = assemble(source, plans, arrays, irregular)
        if sources.json_bytes(actual) != sources.json_bytes(original["cells"]):
            raise ValueError("Independent assessments or cost totals differ.")
        if not technical and comparison(actual) != original["comparison"]:
            raise ValueError("Original restart comparison differs.")
        result = {
            "format": FORMAT + "-verification",
            "scope": original["scope"],
            "source_report_sha256": sources.sha256(
                (completion / publication.REPORT).read_bytes()
            ),
            "software": software,
            "verified_cells": len(actual),
            "search_calls": 0,
        }
        return (
            result,
            "# Lesende Verifikation\n\nAlle geplanten Zellen und Nachweise geprüft; keine Suche.\n",
            {},
        )

    return publication.export_transaction(output, build, seconds=3600)
