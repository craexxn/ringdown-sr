"""Run the bound eighteen-cell signal transfer check on frozen inputs."""

import argparse
from pathlib import Path

from ringdown_sr import transfer_check as control
from ringdown_sr.pilot import _write_json
from ringdown_sr.representation_control import diagnose_candidate


def diagnose_cell_candidate(candidate, index, selected, arrays, cell):
    return diagnose_candidate(
        candidate,
        index,
        selected,
        arrays,
        "complexity_frequency",
        extended_structure=True,
        truth=control.reference_truth(cell["signal"]),
    )


def load_driver():
    factory = control.load_module(
        control.ROOT / "scripts/run_search_duration.py", "transfer_duration_factory"
    )
    driver = factory.load_driver(control=control)
    driver.EXTRA_FILES += ("LocalOptimizerBudget.jl",)
    driver.expected_grammar_cases = control.expected_grammar_cases
    driver.read_archive = control.read_inputs
    driver.arrays_for_cell = control.arrays_for_cell
    driver.diagnose_cell_candidate = diagnose_cell_candidate
    driver.TRUTH = {name: control.reference_truth(name) for name in control.SIGNALS}
    driver.save_report = save_report
    return driver


def save_report(output, report):
    report["scope"] = (
        "bounded noiseless signal transfer; three fresh paired seeds; no general validation"
    )
    report["input_manifest"] = control.input_manifest()
    report["configuration"].update(
        grammar="unrestricted",
        niterations=500,
        optimizer_iterations=300,
        optimizer_nrestarts=5,
        should_simplify=False,
    )
    report.update(
        control.comparison(
            report["cells"],
            final_verified=report["final_verification"] == "passed"
            and report["status"] == "completed",
        )
    )
    lines = [
        "# Begrenzter Signaltransfer bei 500/300/5",
        "",
        f"Serienstatus: `{report['status']}`, Abschlussverifikation: `{report['final_verification']}`.",
        "",
        "Kurve, unterstützte Struktur und Parameter bleiben getrennt; physikalische Identifikation `not_assessed`.",
        "",
        "| Zelle | Signal | Seed | Status | Auswahlindex | Kurve | Struktur | Parameter |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for cell in report["cells"]:
        d = cell.get("diagnostics")
        chosen = control.selected(cell) if d else None
        values = [
            cell["number"],
            cell["signal"],
            cell["budget"]["seed"],
            cell["status"],
            d["selected_index"] if d else "nicht verfügbar",
            chosen["curve_marker"] if chosen else "nicht verfügbar",
            chosen["search_analysis"]["structure"]["structure_status"]
            if chosen
            else "nicht verfügbar",
            chosen["parameter_match"]["status"] if chosen else "nicht verfügbar",
        ]
        lines.append("| " + " | ".join(map(str, values)) + " |")
    lines += ["", "## Originalauswahlen", ""]
    for cell in report["cells"]:
        if cell.get("diagnostics"):
            chosen = control.selected(cell)
            lines += [
                f"Zelle {cell['number']} ({cell['signal']}), Komplexität {chosen['complexity']}:",
                "",
                "```text",
                chosen["display_equation"],
                "```",
                "",
            ]
    if report["comparison"] is None:
        lines += ["Alle Gruppenaggregate und Paardifferenzen sind gesperrt."]
    else:
        lines += [
            "| Signal | Kurvenerfolge C | Unterstützte Auswahlen S |",
            "| --- | --- | --- |",
        ]
        for name, summary in report["summaries"].items():
            lines.append(
                f"| {name} | {summary['curve_successes']}/3 | {summary['supported_reconstructions']}/3 |"
            )
        lines += ["", "| Kontrast | Delta C | Delta S |", "| --- | --- | --- |"]
        for name, value in report["comparison"]["contrasts"].items():
            lines.append(
                f"| {name} | {value['curve_difference']} | {value['supported_difference']} |"
            )
    lines += [
        "",
        "Alle Originalfronten, Fehler, Status, endlichen Nenner und Kosten stehen in report.json. Begrenzter Strukturerkenner und Blindfleck bei 8·fs; keine gemeinsame Erfolgsquote oder automatische Budgeterhöhung.",
        "",
    ]
    temporary = output / "summary.md.tmp"
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(output / "summary.md")
    _write_json(output / "report.json", report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(control.ROOT / "data"):
        raise ValueError("Use a new output outside frozen inputs.")
    load_driver().run(control.ROOT / control.INPUT, args.output, label=args.label)


if __name__ == "__main__":
    main()
