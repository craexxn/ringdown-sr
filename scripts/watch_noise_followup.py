"""Show saved follow-up progress without changing files or launching searches."""

import argparse
import json
import math
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

CONDITIONS = {
    "duration": (
        "ordinary",
        "known_covariance",
        "estimated_64s",
        "estimated_4096s",
    ),
    "sampling": ("jitter_ordinary", "jitter_known_covariance"),
}
LABELS = {
    "ordinary": "O",
    "known_covariance": "K",
    "estimated_64s": "64 s",
    "estimated_4096s": "4096 s",
    "jitter_ordinary": "Jitter O",
    "jitter_known_covariance": "Jitter K",
}
CASE_IDS = tuple(
    name
    for block in range(1, 21)
    for name in (
        (f"ar1-{block:02d}", f"white-{block:02d}")
        if block <= 6
        else (f"ar1-{block:02d}",)
    )
)
TERMINAL = {"completed", "fit_error", "timeout"}


def clean_text(value, limit=180):
    text = str(value)
    return "".join(character if character.isprintable() else " " for character in text)[
        :limit
    ]


def read_json(path, warnings):
    """Tolerate a concurrent status write, but never turn it into success."""
    try:
        if not path.exists():
            return {}
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError("symbolischer Link")
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("Statusdatei über 2 MiB")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise TypeError("kein JSON-Objekt")
        return value
    except (OSError, ValueError, TypeError) as error:
        warnings.append(f"Nicht lesbar: {clean_text(path)} ({clean_text(error)})")
        return {}


def seconds(value):
    if type(value) in (int, float) and math.isfinite(value) and value >= 0:
        return float(value)
    return None


def worker_state(directory, saved, now, warnings):
    outcome = read_json(directory / "outcome.json", warnings)
    state = clean_text(outcome.get("status", saved))
    elapsed = seconds(outcome.get("worker_wall_seconds"))
    timing_kind = "gemessen" if elapsed is not None else "—"
    metadata = {}
    if not outcome or state != "completed":
        metadata = read_json(directory / "metadata.json", warnings)
    error = metadata.get("error")
    if error is not None:
        state = state if state in TERMINAL else "Fehler gespeichert"
    if elapsed is None:
        fit = seconds(metadata.get("fit_wall_seconds"))
        if fit is not None:
            elapsed, timing_kind = fit, "nur Fit"
        elif metadata.get("worker_started_at"):
            try:
                started = datetime.fromisoformat(metadata["worker_started_at"])
                if started.tzinfo is None:
                    raise ValueError("timezone missing")
                elapsed = seconds((now - started).total_seconds())
                timing_kind = "seit Start*" if elapsed is not None else "—"
            except (TypeError, ValueError):
                warnings.append(f"Ungültige Startzeit: {clean_text(directory)}")
    phase = metadata.get("failed_during", metadata.get("phase"))
    return {
        "state": state,
        "phase": None if phase is None else clean_text(phase),
        "seconds": elapsed,
        "timing_kind": timing_kind,
        "error": None if error is None else clean_text(error),
        "process_finished": outcome.get("status") in TERMINAL,
        "recorded_failure": outcome.get("status") in {"fit_error", "timeout"}
        or error is not None,
    }


def invocation_costs(directory, warnings):
    """Summarize saved inclusive calls separately from worker measurements."""
    records = []
    calls = directory / "calls"
    try:
        if calls.is_symlink() or any(parent.is_symlink() for parent in calls.parents):
            raise ValueError("symbolischer Link")
        paths = sorted(calls.iterdir()) if calls.exists() else []
        for path in paths:
            if path.suffix != ".json" or not path.stem.isdecimal():
                warnings.append(f"Unbekannte Aufrufdatei: {clean_text(path)}")
                continue
            record = read_json(path, warnings)
            numbers = [
                seconds(record.get(key))
                for key in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds")
            ]
            if any(value is None for value in numbers):
                warnings.append(f"Ungültige Aufrufkosten: {clean_text(path)}")
                continue
            records.append((record, numbers))
    except (OSError, ValueError) as error:
        warnings.append(f"Aufrufkosten nicht lesbar: {clean_text(error)}")
    return {
        "saved_calls": len(records),
        "wall_seconds": sum(values[0] for _, values in records),
        "cpu_seconds": sum(values[1] + values[2] for _, values in records),
        "cpu_measurement_complete": bool(records)
        and all(
            record.get("cpu_measurement_complete") is True for record, _ in records
        ),
    }


def snapshot(root, now=None):
    """Read only fixed, known paths; saved JSON never supplies a filesystem path."""
    now = datetime.now(UTC) if now is None else now
    warnings = []
    if not root.exists():
        warnings.append(f"Laufordner noch nicht vorhanden: {clean_text(root)}")
    workflow = read_json(root / "workflow_state.json", warnings)
    result = {
        "time": now.astimezone().isoformat(timespec="seconds"),
        "workflow": workflow,
        "blocks": {},
        "warnings": warnings,
    }
    for block, conditions in CONDITIONS.items():
        directory = root / block
        state = read_json(directory / "run_state.json", warnings)
        saved_cases = state.get("cases", [])
        if not isinstance(saved_cases, list):
            warnings.append(f"{block}: ungültige Fallliste")
            saved_cases = []
        case_states = {}
        for entry in saved_cases:
            if not isinstance(entry, dict) or entry.get("id") not in CASE_IDS:
                warnings.append(f"{block}: unbekannter oder ungültiger Falleintrag")
                continue
            if entry["id"] in case_states:
                warnings.append(f"{block}: doppelter Falleintrag {entry['id']}")
                continue
            case_states[entry["id"]] = clean_text(entry.get("status", "?"))
        records = []
        finished, failures, measured = 0, 0, 0.0
        for case_id in CASE_IDS:
            case_directory = directory / "cases" / case_id
            detail = read_json(case_directory / "run_state.json", warnings)
            case_state = clean_text(
                detail.get("status", case_states.get(case_id, "planned"))
            )
            rows = []
            for condition in conditions:
                package = case_directory / "symbolic" / condition
                package_state = read_json(package / "run_state.json", warnings)
                members = package_state.get("members", ["planned"] * 4)
                if not isinstance(members, list) or len(members) != 4:
                    warnings.append(
                        f"{block}/{case_id}/{condition}: Mitgliedsliste unklar"
                    )
                    members = ["?"] * 4
                workers = []
                for index, saved in enumerate(members, 1):
                    worker = worker_state(
                        package / f"member-{index:02d}", saved, now, warnings
                    )
                    finished += worker["process_finished"]
                    failures += worker["recorded_failure"]
                    if worker["timing_kind"] == "gemessen":
                        measured += worker["seconds"]
                    workers.append(worker)
                rows.append({"condition": condition, "workers": workers})
            records.append({"id": case_id, "state": case_state, "conditions": rows})
        result["blocks"][block] = {
            "state": clean_text(state.get("status", "noch kein gespeicherter Stand")),
            "error": None if state.get("error") is None else clean_text(state["error"]),
            "finished_cases": sum(item["state"] == "completed" for item in records),
            "finished_processes": finished,
            "recorded_failures": failures,
            "planned_processes": len(CASE_IDS) * len(conditions) * 4,
            "measured_worker_seconds": measured,
            "invocation_costs": invocation_costs(directory, warnings),
            "cases": records,
        }
    return result


def render(data, *, detailed=False):
    lines = [data["time"], "Folgestudie: Hintergrunddauer und Messraster"]
    workflow = data["workflow"]
    if workflow:
        lines.append(
            "Gesamtschritt: "
            + clean_text(workflow.get("phase", "?"))
            + " / "
            + clean_text(workflow.get("status", "?"))
        )
    for block, title in (
        ("duration", "A – Hintergrunddauer"),
        ("sampling", "B – Messraster"),
    ):
        record = data["blocks"][block]
        lines.extend(
            [
                "",
                f"{title}: {record['state']}",
                (
                    f"Fälle: {record['finished_cases']}/26; beendete neue Worker: "
                    f"{record['finished_processes']}/{record['planned_processes']}; "
                    f"gespeicherte Fehler: {record['recorded_failures']}"
                ),
                f"Gemessene Workerzeit: {record['measured_worker_seconds'] / 3600:.2f} h",
            ]
        )
        if block == "sampling":
            lines.append(
                "52 geplante O/K-Kontrollreferenzen aus A; keine neuen Worker."
            )
        costs = record["invocation_costs"]
        if costs["saved_calls"]:
            completeness = (
                "vollständig" if costs["cpu_measurement_complete"] else "unvollständig"
            )
            lines.append(
                f"Gespeicherte Aufrufe: {costs['saved_calls']}; "
                f"inklusive Zeit {costs['wall_seconds'] / 3600:.2f} h, "
                f"CPU {costs['cpu_seconds'] / 3600:.2f} h ({completeness})."
            )
            lines.append("Aufrufzeit enthält Workerzeit; diese Werte nicht addieren.")
        if record["error"]:
            lines.append("BLOCKFEHLER: " + record["error"])
        for case in record["cases"]:
            if not detailed and case["state"] == "planned":
                continue
            lines.append(f"  {case['id']:9}  {case['state']}")
            for condition in case["conditions"]:
                workers = condition["workers"]
                if not detailed and all(
                    worker["state"] == "planned" for worker in workers
                ):
                    continue
                member_text = ", ".join(
                    f"{index}={worker['state']}"
                    for index, worker in enumerate(workers, 1)
                )
                lines.append(f"    {LABELS[condition['condition']]:10} {member_text}")
                for index, worker in enumerate(workers, 1):
                    if worker["state"] not in {"planned", "completed"}:
                        duration = (
                            "—"
                            if worker["seconds"] is None
                            else f"{worker['seconds']:.1f} s"
                        )
                        phase = (
                            ""
                            if worker["phase"] is None
                            else f"; Phase {worker['phase']}"
                        )
                        lines.append(
                            f"      {index}: {duration} ({worker['timing_kind']}){phase}"
                        )
                    if worker["error"]:
                        lines.append(f"      FEHLER {index}: {worker['error']}")
    if data["warnings"]:
        lines.append("")
        lines.extend("HINWEIS: " + warning for warning in data["warnings"][:10])
        if len(data["warnings"]) > 10:
            lines.append(f"Weitere Lesehinweise: {len(data['warnings']) - 10}")
    lines.extend(
        [
            "",
            "Nur lesend. Gespeicherte Zustände können nach einem Abbruch stehen bleiben.",
            "* Seit gespeichertem UTC-Start, keine gemessene Workerzeit.",
            "Prozessabschluss ist kein wissenschaftlicher Erfolgsnachweis.",
            "Strg+C beendet ausschließlich diese Anzeige.",
        ]
    )
    return "\n".join(lines)


def main(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=10.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--all", action="store_true", dest="detailed")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(arguments)
    if not math.isfinite(args.interval) or not 0 < args.interval <= 60:
        parser.error("--interval must be greater than zero and at most 60 seconds.")
    try:
        while True:
            data = snapshot(args.root)
            if sys.stdout.isatty() and not args.once and not args.json:
                print("\033[2J\033[H", end="")
            print(
                json.dumps(data, ensure_ascii=False)
                if args.json
                else render(data, detailed=args.detailed),
                flush=True,
            )
            if args.once:
                return 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
