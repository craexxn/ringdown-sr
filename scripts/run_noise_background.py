"""Prepare, execute, verify or plot the separately frozen background study."""

import argparse

from ringdown_sr import noise_background, noise_background_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    prepare = commands.add_parser(
        "prepare", help="Bind inputs without fits or searches"
    )
    prepare.add_argument("--output", required=True)
    for action in ("run", "verify", "plots"):
        command = commands.add_parser(action)
        command.add_argument("--inputs", required=True)
        command.add_argument("--technical", required=True)
        command.add_argument(
            "--output", required=True, help="Scientific series directory"
        )
        if action in ("verify", "plots"):
            command.add_argument("--export", required=action == "plots")
    technical = commands.add_parser("technical-plots")
    technical.add_argument("--technical", required=True)
    technical.add_argument("--export", required=True)
    args = parser.parse_args()
    if args.action == "prepare":
        noise_background_inputs.prepare_inputs(args.output)
        print("All 26 background-study inputs bound; no fits or searches executed.")
    elif args.action == "run":
        noise_background.run(args.inputs, args.technical, args.output)
        print(
            "Background study completed: all 520 planned searches accounted for in 130 package outputs."
        )
    elif args.action == "verify":
        noise_background.verify(
            args.inputs, args.technical, args.output, export=args.export
        )
        print(
            "Background-study read-only verification passed; no fits or searches executed."
        )
    else:
        from ringdown_sr import noise_background_plots

        if args.action == "plots":
            noise_background_plots.export(
                args.inputs, args.technical, args.output, args.export
            )
        else:
            noise_background_plots.export_technical(args.technical, args.export)
        print(
            "Bound plots, original formulas and numerical plot data exported without fits or searches."
        )


if __name__ == "__main__":
    main()
