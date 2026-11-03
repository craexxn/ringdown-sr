"""Run the frozen twenty-cell search-budget comparison using the audited lifecycle."""

from ringdown_sr import search_duration as control
from ringdown_sr import symbolic
from ringdown_sr.pilot import _sha256, _write_json


def load_driver():
    driver = control.load_module(
        symbolic.ROOT / "scripts/run_trigonometric_grammar.py", "duration_driver"
    )
    for name in (
        "FORMAT",
        "PROFILE_FORMAT",
        "PLAN",
        "PLAN_COMMIT",
        "PLAN_SHA256",
        "LIMIT_SECONDS",
        "WORKER_LIMIT_SECONDS",
        "RUNTIME",
        "source_hashes",
        "planned_cells",
        "profile_parameters",
        "verify_manifest",
        "comparison",
        "common_parameters",
    ):
        setattr(driver, name, getattr(control, name))
    driver.EXTRA_FILES += ("search_invocation.json",)

    def verify_preflight(record, initial, sources, support, probe):
        if (
            record["format"] != control.FORMAT
            or record["status"] != "verified"
            or record["mode"] != "options"
            or record["callback_calls"] != 0
            or record["source_sha256"] != sources
            or len(record["profiles"]) != 10
            or record["search_profiles"] != control.search_profiles()
        ):
            raise ValueError("Invalid search-duration preflight.")
        driver.verify_snapshots(record, initial, probe)
        expected = {(g, s) for g in control.CONDITIONS for s in control.SEEDS}
        seen, first = set(), None
        for profile in record["profiles"]:
            key = profile["condition"], profile["python_seed"]
            if key not in expected or key in seen:
                raise ValueError("Missing or duplicate search-duration native profile.")
            seen.add(key)
            control.verify_options(profile, key[1], key[0], driver.BASE, support)
            current = control.common_options(profile, support)
            if first is not None and current != first:
                raise ValueError("Unplanned native cross-profile difference.")
            first = current

    original_verify = driver.verify_cell

    def verify_cell(directory, cell, *args):
        diagnosis = original_verify(directory, cell, *args)
        contents = (directory / "search_invocation.json").read_bytes()
        if _sha256(contents) != diagnosis["source_file_sha256"][
            "search_invocation.json"
        ] or driver.BASE.load_support().read_json(
            contents
        ) != control.invocation_record(cell["budget"]["niterations"]):
            raise ValueError("Wrong or changed actual equation_search budget.")
        diagnosis["search_invocation"] = control.invocation_record(
            cell["budget"]["niterations"]
        )
        return diagnosis

    driver.verify_preflight = verify_preflight
    driver.verify_cell = verify_cell
    driver.save_report = save_report
    return driver


def save_report(output, report):
    report.update(
        control.comparison(
            report["cells"],
            final_verified=report["final_verification"] == "passed"
            and report["status"] == "completed",
        )
    )
    lines = [
        "# Suchbudgetvergleich",
        "",
        f"Serienstatus: `{report['status']}`, Abschlussverifikation: `{report['final_verification']}`.",
        "",
        "Bekannter Entwicklungsfall; physikalische Identifikation `not_assessed`.",
        "",
        "| Zelle | Seed | Grammatik | Iterationen | Status | Auswahlindex | Kurve | Struktur | Parameter |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for cell in report["cells"]:
        diagnosis = cell.get("diagnostics")
        chosen = control.selected(cell) if diagnosis else None
        values = [
            cell["number"],
            cell["budget"]["seed"],
            cell["condition"],
            cell["budget"]["niterations"],
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
    if report["comparison"] is not None:
        lines += [
            "| Grammatik | C₂₀₀ | C₂₀₀₀ | Differenz | Einordnung |",
            "| --- | --- | --- | --- | --- |",
        ]
        for grammar, values in report["comparison"]["by_grammar"].items():
            lines.append(
                f"| {grammar} | {values['C_200']} | {values['C_2000']} | {values['difference']} | {values['development_signal']} |"
            )
    else:
        lines += [
            "Alle Gruppenaggregate, Paardifferenzen und Gesamtentscheidungen sind gesperrt."
        ]
    lines += [
        "",
        "Alle Fronten, Kosten, Fehler, Status und endlichen Nenner stehen in report.json. Der Alias-Blindfleck bei 8·fs = 32768 Hz bleibt bestehen.",
        "",
    ]
    temporary = output / "summary.md.tmp"
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(output / "summary.md")
    _write_json(output / "report.json", report)


if __name__ == "__main__":
    load_driver().main()
