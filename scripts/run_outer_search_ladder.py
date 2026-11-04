"""Run the bound four-budget comparison with a fixed local 300/5 profile."""

from ringdown_sr import outer_search_ladder as control
from ringdown_sr.pilot import _write_json


def load_driver():
    factory = control.load_module(
        control.ROOT / "scripts/run_search_duration.py", "ladder_duration_factory"
    )
    driver = factory.load_driver(control=control)
    driver.EXTRA_FILES += ("LocalOptimizerBudget.jl",)
    driver.expected_grammar_cases = control.expected_grammar_cases
    driver.save_report = save_report
    return driver


def save_report(output, report):
    report["configuration"].update(
        grammar="unrestricted",
        niterations=list(control.ITERATIONS),
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
        "# Äußere Suchbudgets bei festem lokalem Profil 300/5",
        "",
        f"Serienstatus: `{report['status']}`, Abschlussverifikation: `{report['final_verification']}`.",
        "",
        "Bekannter Entwicklungsfall; physikalische Identifikation `not_assessed`.",
        "",
        "| Zelle | Seed | Iterationen | Status | Auswahlindex | Kurve | Struktur | Parameter |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for cell in report["cells"]:
        d = cell.get("diagnostics")
        chosen = control.selected(cell) if d else None
        values = [
            cell["number"],
            cell["budget"]["seed"],
            cell["budget"]["niterations"],
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
                f"Zelle {cell['number']}, Komplexität {chosen['complexity']}:",
                "",
                "```text",
                chosen["display_equation"],
                "```",
                "",
            ]
    if report["comparison"] is None:
        lines += [
            "Alle Gruppenaggregate, Paardifferenzen und Entscheidungen sind gesperrt."
        ]
    else:
        lines += [
            "| Iterationen | Kurvenerfolge C | Unterstützte Auswahlen S |",
            "| --- | --- | --- |",
        ]
        for name, summary in report["summaries"].items():
            lines.append(
                f"| {name} | {summary['curve_successes']}/5 | {summary['supported_reconstructions']}/5 |"
            )
        lines += [
            "",
            "| Kontrast | Delta C | Delta S | Einordnung |",
            "| --- | --- | --- | --- |",
        ]
        for name, value in report["comparison"]["contrasts"].items():
            lines.append(
                f"| {name} | {value['curve_difference']} | {value['supported_difference']} | {value['count_outcome']} |"
            )
    lines += [
        "",
        "Alle Originalfronten, Fehler, Status, endlichen Nenner und Kosten stehen in report.json. Kein automatisch gewähltes Gewinnerprofil; der Blindfleck bei 8·fs bleibt bestehen.",
        "",
    ]
    temporary = output / "summary.md.tmp"
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(output / "summary.md")
    _write_json(output / "report.json", report)


if __name__ == "__main__":
    load_driver().main()
