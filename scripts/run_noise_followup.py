"""Prepare, execute and read-verify the duration and sampling follow-up study."""

import argparse
import hashlib
import io
import json
import os
import tarfile
from pathlib import Path


def positive_integer(value):
    """Accept a positive limit for deliberately stopping at a case boundary."""
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Expected a positive integer.") from error
    if number <= 0:
        raise argparse.ArgumentTypeError("Expected a positive integer.")
    return number


def archive(root, part):
    """Archive one explicit partition, binding predecessors and every file byte.

    This is an integrity check, not a replacement for scientific verification.
    Files in the source tree are never changed. A partial failed archive is
    retained under its new name and cannot be silently overwritten.
    """
    root = Path(root).absolute()
    if (
        not root.is_dir()
        or root.is_symlink()
        or any(parent.is_symlink() for parent in root.parents)
        or root.name in {"", ".", ".."}
        or any(not character.isprintable() for character in root.name)
    ):
        raise ValueError("Expected an existing run directory without symlinks.")
    partitions = {
        "shared": ("inputs", "technical", "estimators", "technical-plots"),
        "duration": ("duration", "verification-duration", "plots-duration"),
        "sampling": ("sampling", "verification-sampling", "plots-sampling"),
    }
    if part not in partitions:
        raise ValueError("Unknown archive partition.")
    output = root / "archives"
    if output.is_symlink():
        raise ValueError("Archive directory cannot be a symlink.")
    output.mkdir(exist_ok=True)
    destination = output / f"{root.name}-{part}.tar.gz"
    checksum_path = destination.with_name(destination.name + ".sha256")
    if any(path.exists() or path.is_symlink() for path in (destination, checksum_path)):
        raise ValueError("Archive or checksum already exists; nothing overwritten.")

    def digest(path):
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()

    dependencies = {}
    for previous in (() if part == "shared" else ("shared",)) + (
        ("duration",) if part == "sampling" else ()
    ):
        dependency = output / f"{root.name}-{previous}.tar.gz"
        checksum = dependency.with_name(dependency.name + ".sha256")
        if any(
            path.is_symlink() or not path.is_file() for path in (dependency, checksum)
        ):
            raise ValueError(
                "A complete predecessor archive and checksum are required."
            )
        actual = digest(dependency)
        if checksum.read_text() != f"{actual}  {dependency.name}\n":
            raise ValueError("Predecessor archive checksum changed.")
        dependencies[dependency.name] = actual

    def source_files():
        found = []
        for name in partitions[part]:
            directory = root / name
            if not directory.is_dir() or directory.is_symlink():
                raise ValueError(f"Missing archive input directory: {name}")
            for path in sorted(directory.rglob("*")):
                if path.is_symlink() or (not path.is_file() and not path.is_dir()):
                    raise ValueError(
                        "Only regular files and directories can be archived."
                    )
                if path.is_file():
                    found.append(path)
            for suffix in ("-call.json", "_call.json"):
                call = root / (name + suffix)
                if call.is_symlink():
                    raise ValueError("Call records cannot be symlinks.")
                if call.is_file():
                    found.append(call)
        return found

    files = source_files()
    inventory = {path.relative_to(root).as_posix(): digest(path) for path in files}
    if not inventory:
        raise ValueError("Cannot archive an empty partition.")
    receipt = {
        "format": "ringdown-sr-noise-followup-archive-1",
        "part": part,
        "run_directory_name": root.name,
        "required_archives_sha256": dependencies,
        "files_sha256": inventory,
        "scope": "File integrity only; scientific verification is a separate step.",
    }
    raw_receipt = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
    receipt_name = f"{root.name}/ARCHIVE-{part}.json"
    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with (
        os.fdopen(descriptor, "wb") as stream,
        tarfile.open(fileobj=stream, mode="w:gz", compresslevel=6) as packed,
    ):
        for path in files:
            packed.add(path, arcname=f"{root.name}/{path.relative_to(root).as_posix()}")
        entry = tarfile.TarInfo(receipt_name)
        entry.size = len(raw_receipt)
        entry.mode = 0o600
        packed.addfile(entry, io.BytesIO(raw_receipt))
    expected = {f"{root.name}/{name}": value for name, value in inventory.items()}
    expected[receipt_name] = hashlib.sha256(raw_receipt).hexdigest()
    seen = set()
    with tarfile.open(destination, mode="r:gz") as packed:
        for entry in packed:
            if not entry.isfile() or entry.name not in expected or entry.name in seen:
                raise ValueError("Unexpected or duplicate archive member.")
            with packed.extractfile(entry) as stream:
                if (
                    hashlib.file_digest(stream, "sha256").hexdigest()
                    != expected[entry.name]
                ):
                    raise ValueError("Archived file hash mismatch.")
            seen.add(entry.name)
    if (
        source_files() != files
        or seen != set(expected)
        or any(digest(root / name) != value for name, value in inventory.items())
    ):
        raise ValueError("Source inventory changed during archiving.")
    archive_hash = digest(destination)
    with checksum_path.open("x", encoding="utf-8") as stream:
        stream.write(f"{archive_hash}  {destination.name}\n")
    return destination


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="action", required=True)
    prepare = commands.add_parser("prepare", help="Bind all scientific inputs")
    prepare.add_argument("--output", type=Path, required=True)
    verify_inputs = commands.add_parser(
        "verify-inputs", help="Read-only input verification, without searches"
    )
    verify_inputs.add_argument("--inputs", type=Path, required=True)
    verify_inputs.add_argument("--regenerate", action="store_true")
    estimator_check = commands.add_parser(
        "estimator-check", help="Run the separate noise-only estimator diagnosis"
    )
    estimator_check.add_argument("--output", type=Path, required=True)
    estimator_verify = commands.add_parser(
        "estimator-verify", help="Read-only estimator-diagnosis verification"
    )
    estimator_verify.add_argument("--output", type=Path, required=True)
    estimator_verify.add_argument("--export", type=Path)
    for action in ("run", "verify", "plots"):
        command = commands.add_parser(action)
        command.add_argument("--inputs", type=Path, required=True)
        command.add_argument("--technical", type=Path, required=True)
        command.add_argument("--estimators", type=Path, required=True)
        command.add_argument("--block", choices=("duration", "sampling"), required=True)
        command.add_argument(
            "--output", type=Path, required=True, help="Scientific block directory"
        )
        command.add_argument(
            "--duration", type=Path, help="Completed duration block for shared controls"
        )
        if action == "run":
            command.add_argument("--max-cases", type=positive_integer)
        else:
            command.add_argument("--export", type=Path, required=action == "plots")
    technical_plots = commands.add_parser("technical-plots")
    technical_plots.add_argument("--technical", type=Path, required=True)
    technical_plots.add_argument("--export", type=Path, required=True)
    plot_verify = commands.add_parser("verify-plots")
    plot_verify.add_argument("--export", type=Path, required=True)
    pack = commands.add_parser("archive", help="Create one new hash-bound archive part")
    pack.add_argument("--root", type=Path, required=True)
    pack.add_argument(
        "--part", choices=("shared", "duration", "sampling"), required=True
    )
    return result


def main(arguments=None):
    command_parser = parser()
    args = command_parser.parse_args(arguments)
    if args.action in {"run", "verify", "plots"}:
        if args.block == "sampling" and args.duration is None:
            command_parser.error("--block sampling requires --duration.")
        if args.block == "duration" and args.duration is not None:
            command_parser.error("--duration is only valid for --block sampling.")

    if args.action == "archive":
        destination = archive(args.root, args.part)
        print(f"Archive bytes and file hashes verified: {destination}")
    elif args.action in {"prepare", "verify-inputs"}:
        from ringdown_sr import noise_followup_inputs as inputs

        if args.action == "prepare":
            inputs.prepare_inputs(args.output, purpose="scientific")
            print("All follow-up inputs bound; no fits or searches executed.")
        else:
            inputs.verify_inputs(args.inputs, regenerate=args.regenerate)
            print("Follow-up input verification passed; no searches executed.")
    elif args.action in {"estimator-check", "estimator-verify"}:
        from ringdown_sr import noise_followup_diagnostics as diagnostics

        if args.action == "estimator-check":
            diagnostics.run(args.output)
        else:
            diagnostics.verify(args.output, export=args.export)
        print("Noise-only estimator diagnosis verified; no SR searches executed.")
    elif args.action in {"run", "verify"}:
        from ringdown_sr import noise_followup

        options = {
            "block": args.block,
            "uniform": args.duration,
            "diagnostics": args.estimators,
        }
        if args.action == "run":
            report = noise_followup.run(
                args.inputs,
                args.technical,
                args.output,
                max_cases=args.max_cases,
                **options,
            )
            if report.get("status") == "paused":
                print(
                    "Follow-up block paused after a complete case; "
                    "the whole block is not yet complete."
                )
            elif report.get("status") == "completed":
                print(f"Follow-up {args.block} block completed and accounted for.")
            else:
                raise ValueError("Unexpected follow-up run state; no success declared.")
        else:
            noise_followup.verify(
                args.inputs,
                args.technical,
                args.output,
                export=args.export,
                **options,
            )
            print("Follow-up read-only verification passed; no searches executed.")
    else:
        from ringdown_sr import noise_followup_plots as plots

        if args.action == "technical-plots":
            plots.export_technical(args.technical, args.export)
        elif args.action == "verify-plots":
            plots.verify_export(args.export)
        else:
            plots.export(
                args.inputs,
                args.technical,
                args.output,
                args.export,
                block=args.block,
                uniform=args.duration,
                diagnostics=args.estimators,
            )
        print("Bound plots, original formulas and point data verified; no searches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
