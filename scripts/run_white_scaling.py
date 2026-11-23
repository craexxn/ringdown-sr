"""Run or read-only verify the frozen small white-noise scaling experiment."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "verify", "export", "status"))
    parser.add_argument("directory")
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.action == "status":
        path = Path(args.directory) / "status.json"
        if not path.is_file():
            print("Noch kein gespeicherter Laufstand.")
            return
        status = json.loads(path.read_bytes())
        state = (
            status["status"]
            if "finished_at" in status
            else "gestartet; Prozessstatus unbekannt"
        )
        print(f"Status: {state}")
        print(f"Feste Worker: {status['completed_fixed']}/18 (je 4 Starts)")
        print(f"Freie Suchen: {status['completed_search']}/21")
        print(f"Zuletzt: {status.get('stage', '')} {status.get('current_cell', '')}")
        if status.get("error"):
            print(status["error"])
        print(
            "Nur gespeicherter Stand; Prozessabschluss ist kein Verifikationsnachweis."
        )
        return
    from ringdown_sr import white_scaling

    if args.action == "run":
        white_scaling.run(args.directory)
    elif args.action == "verify":
        white_scaling.verify(args.directory)
    elif args.output:
        white_scaling.export(args.directory, args.output)
    else:
        parser.error("export requires --output")
    print(f"White scaling {args.action} passed.", flush=True)


if __name__ == "__main__":
    main()
