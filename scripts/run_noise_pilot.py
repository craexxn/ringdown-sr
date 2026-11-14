"""Prepare, execute or read-verify the separately frozen noise-pilot series."""

import argparse

from ringdown_sr import noise_pilot, noise_pilot_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    prepare = commands.add_parser(
        "prepare", help="Bind all inputs without searches or fits"
    )
    prepare.add_argument("--output", required=True)
    for action in ("run", "verify"):
        command = commands.add_parser(action)
        command.add_argument("--inputs", required=True)
        command.add_argument("--technical", required=True)
        command.add_argument(
            "--output", required=True, help="Scientific series directory"
        )
        if action == "verify":
            command.add_argument(
                "--export", help="New directory for a read-only replay export"
            )
    args = parser.parse_args()
    if args.action == "prepare":
        noise_pilot_inputs.prepare_inputs(args.output)
        print("All twelve noise-pilot inputs bound; no fits or searches executed.")
    elif args.action == "run":
        noise_pilot.run(args.inputs, args.technical, args.output)
        print(
            "Noise pilot completed: all 144 planned searches accounted for in 36 package outputs."
        )
    else:
        noise_pilot.verify(args.inputs, args.technical, args.output, export=args.export)
        print(
            "Noise-pilot series read-only verification passed; no fits or searches executed."
        )


if __name__ == "__main__":
    main()
