"""Prepare, execute, verify and export the fixed two-signal main study."""

import argparse
from pathlib import Path

SIGNALS = ("signal_200_4ms", "signal_250_6ms")


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="action", required=True)
    prepare = commands.add_parser("prepare", help="Bind all 80 scientific inputs")
    prepare.add_argument("--output", type=Path, required=True)
    verify_inputs = commands.add_parser("verify-inputs", help="Read-only input check")
    verify_inputs.add_argument("--inputs", type=Path, required=True)
    verify_inputs.add_argument("--regenerate", action="store_true")
    for action in ("run", "verify"):
        command = commands.add_parser(action)
        command.add_argument("--inputs", type=Path, required=True)
        command.add_argument("--technical", type=Path, required=True)
        command.add_argument("--signal", choices=SIGNALS, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--previous", type=Path)
        if action == "verify":
            command.add_argument("--export", type=Path, required=True)
    plots = commands.add_parser("plots")
    plots.add_argument("--inputs", type=Path, required=True)
    plots.add_argument("--technical", type=Path, required=True)
    plots.add_argument("--series-200", type=Path, required=True)
    plots.add_argument("--series-250", type=Path)
    plots.add_argument("--export", type=Path, required=True)
    technical_plots = commands.add_parser("technical-plots")
    technical_plots.add_argument("--technical", type=Path, required=True)
    technical_plots.add_argument("--export", type=Path, required=True)
    verify_plots = commands.add_parser("verify-plots")
    verify_plots.add_argument("--export", type=Path, required=True)
    pack = commands.add_parser("archive", help="Archive bytes; no scientific execution")
    pack.add_argument("--root", type=Path, required=True)
    pack.add_argument("--part", choices=("shared", *SIGNALS, "partial"), required=True)
    return result


def main(arguments=None):
    command_parser = parser()
    args = command_parser.parse_args(arguments)
    if args.action in {"run", "verify"} and (args.signal == SIGNALS[1]) != (
        args.previous is not None
    ):
        command_parser.error("Only --signal signal_250_6ms requires --previous.")

    if args.action == "archive":
        from ringdown_sr.main_study_archiving import archive

        destination = archive(args.root, args.part)
        print(f"Archive bytes and source inventory verified: {destination}")
    elif args.action in {"prepare", "verify-inputs"}:
        from ringdown_sr import main_study_inputs as inputs

        if args.action == "prepare":
            inputs.prepare_inputs(args.output, purpose="scientific")
            print("All 80 main-study inputs bound; no fits or searches executed.")
        else:
            inputs.verify_inputs(args.inputs, regenerate=args.regenerate)
            print("Main-study input verification passed; no searches executed.")
    elif args.action in {"run", "verify"}:
        from ringdown_sr import main_study

        options = {"signal_id": args.signal, "previous": args.previous}
        if args.action == "run":
            report = main_study.run(args.inputs, args.technical, args.output, **options)
            if report.get("status") != "completed":
                raise ValueError("Incomplete main-study section; no success declared.")
            print(f"Main-study section {args.signal} completed and accounted for.")
        else:
            main_study.verify(
                args.inputs, args.technical, args.output, export=args.export, **options
            )
            print("Main-study read-only verification passed; no searches executed.")
    else:
        from ringdown_sr import main_study_plots as plots

        if args.action == "technical-plots":
            plots.export_technical(args.technical, args.export)
        elif args.action == "verify-plots":
            plots.verify_export(args.export)
        else:
            series = {SIGNALS[0]: args.series_200}
            if args.series_250 is not None:
                series[SIGNALS[1]] = args.series_250
            plots.export(args.inputs, args.technical, series, args.export)
        print(
            "Original formulas, full point data and bound plots verified; no searches."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
