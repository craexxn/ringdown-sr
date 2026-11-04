"""Run twenty fresh unrestricted searches across two local optimizer factors."""

from ringdown_sr import local_optimizer as control
from ringdown_sr.pilot import _write_json


def load_driver():
    factory = control.load_module(
        control.ROOT / "scripts/run_search_duration.py", "local_duration_factory"
    )
    driver = factory.load_driver(control=control)
    driver.EXTRA_FILES += ("LocalOptimizerBudget.jl",)
    driver.expected_grammar_cases = control.expected_grammar_cases
    driver.save_report = save_report
    return driver


def save_report(output, report):
    report["configuration"].update(
        grammar="unrestricted",
        niterations=200,
        optimizer_iterations=[100, 300],
        optimizer_nrestarts=[2, 5],
        should_simplify=False,
        profiles={
            k: {"optimizer_iterations": i, "optimizer_nrestarts": r}
            for k, (i, r) in control.PROFILES.items()
        },
    )
    report.update(
        control.comparison(
            report["cells"],
            final_verified=report["final_verification"] == "passed"
            and report["status"] == "completed",
        )
    )
    lines = [
        "# Lokales Optimiererbudget: unrestricted bei 200 Suchiterationen",
        "",
        f"Serienstatus: `{report['status']}`, Abschlussverifikation: `{report['final_verification']}`.",
        "",
        "Adaptiver Entwicklungsvergleich; physikalische Identifikation `not_assessed`.",
        "",
        "| Zelle | Seed | Profil | Status | Auswahlindex | Kurve | Struktur | Parameter |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for cell in report["cells"]:
        diagnosis = cell.get("diagnostics")
        chosen = control.selected(cell) if diagnosis else None
        values = [
            cell["number"],
            cell["budget"]["seed"],
            cell["condition"],
            cell["status"],
            diagnosis["selected_index"] if diagnosis else "nicht verfügbar",
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
            "| Kontrast | C links | C rechts | Differenz | Einordnung |",
            "| --- | --- | --- | --- | --- |",
        ]
        for name, value in report["comparison"]["contrasts"].items():
            lines.append(
                f"| {name} | {value['C_first']} | {value['C_second']} | {value['difference']} | {value['development_signal']} |"
            )
        lines += [
            "",
            f"Zählinteraktion: {report['comparison']['count_interaction']}. Kein automatisch gewähltes Gewinnerprofil.",
        ]
    lines += [
        "",
        "Sämtliche Fronten, Fehler, Status, endlichen Nenner und Kosten stehen in report.json. Der Alias-Blindfleck bei 8·fs = 32768 Hz bleibt bestehen.",
        "",
    ]
    temporary = output / "summary.md.tmp"
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(output / "summary.md")
    _write_json(output / "report.json", report)


if __name__ == "__main__":
    load_driver().main()
