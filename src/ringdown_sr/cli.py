"""Expose the configured reference-fit pilot as a small command-line tool."""

import argparse
import json
import sys
from pathlib import Path

from ringdown_sr.pilot import run_pilot


def main(argv: list[str] | None = None) -> int:
    """Return 0 for success, 1 for a persisted failed run, 2 for input/export errors."""
    parser = argparse.ArgumentParser(description="Konfigurierter Ringdown-Pilot")
    subcommands = parser.add_subparsers(dest="command", required=True)
    run = subcommands.add_parser(
        "run", help="Einen Kontrollfall ausführen und speichern"
    )
    run.add_argument("config", type=Path, help="TOML-Konfiguration")
    run.add_argument("--output", type=Path, required=True, help="Neuer Ausgabeordner")
    args = parser.parse_args(argv)
    try:
        outcome = run_pilot(args.config, args.output)
    except (OSError, ValueError, TypeError, OverflowError) as error:
        print(
            f"Pilot konnte nicht vollständig ausgeführt werden: {error}",
            file=sys.stderr,
        )
        return 2
    result = json.loads(
        (outcome.output_directory / "result.json").read_text(encoding="utf-8")
    )
    print(f"Status: {outcome.status}")
    print(f"Ergebnisse: {outcome.output_directory.resolve()}")
    if outcome.status != "success":
        print(f"Fehler: {result['error']['message']}", file=sys.stderr)
        return 1
    if result["schema_version"] == 2:
        print(f"Gewähltes Alpha: {result['covariance_estimation']['alpha_selected']:g}")
        for name, label in (
            ("ordinary", "Gewöhnlicher Fit"),
            ("known_covariance", "Fit mit wahrer Kovarianz"),
            ("estimated_covariance", "Fit mit geschätzter Kovarianz"),
        ):
            record = result["fits"][name]
            parameters = record["fit"]["parameters"]
            print(
                f"{label}: f = {parameters['frequency_hz']:.8g} Hz, "
                f"tau = {parameters['decay_time_s']:.8g} s, "
                f"MSE = {record['metrics']['ordinary_mse']:.8g}, "
                f"Q_true/N = {record['metrics']['q_true_per_sample']:.8g}"
            )
    else:
        parameters = result["fit"]["parameters"]
        print(f"Frequenz: {parameters['frequency_hz']:.8g} Hz")
        print(f"Abklingzeit: {parameters['decay_time_s']:.8g} s")
        print(f"MSE an Messdaten: {result['metrics']['ordinary_mse']:.8g}")
    print("Einzelner Kontrollfall; keine wissenschaftliche Leistungsbewertung.")
    return 0
