"""Archive original main-study files without overwrites or execution claims."""

import hashlib
import io
import json
import os
import tarfile
from pathlib import Path


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
        "shared": ("inputs", "technical", "technical-plots"),
        "signal_200_4ms": ("signal_200_4ms", "verification-200", "plots-200"),
        "signal_250_6ms": ("signal_250_6ms", "verification-250", "plots-all"),
    }
    if part == "partial":
        partitions[part] = tuple(
            child.name
            for child in sorted(root.iterdir())
            if child.name != "archives" and child.is_dir()
        )
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
    for previous in (() if part in {"shared", "partial"} else ("shared",)) + (
        ("signal_200_4ms",) if part == "signal_250_6ms" else ()
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
        if part == "partial":
            for path in sorted(root.iterdir()):
                if path.name == "archives":
                    continue
                if path.is_symlink() or not (path.is_file() or path.is_dir()):
                    raise ValueError("Only regular partial artifacts may be archived.")
                if path.is_file() and path not in found:
                    found.append(path)
        return found

    files = source_files()
    inventory = {path.relative_to(root).as_posix(): digest(path) for path in files}
    if not inventory:
        raise ValueError("Cannot archive an empty partition.")
    receipt = {
        "format": "ringdown-sr-main-study-archive-1",
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
