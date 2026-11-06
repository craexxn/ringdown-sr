"""Read a bounded PR76 archive and assess whole-arm technical eligibility."""

import io
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from . import assessment_publication as publication
from . import assessment_sources as sources
from . import seed_driver_crosscheck as cross
from . import time_budget_profile as profile
from .symbolic import _stop_worker

REVIEWED_COMMIT = "66ec4238f39edbbc2a71bb4e984571e41531e7ab"


def archive_files(raw):
    """Accept regular bounded members; never load archived pickle/Julia state."""
    files, total, names = {}, 0, set()
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for index, member in enumerate(archive):
            if index >= sources.MAX_MEMBERS:
                raise ValueError("Too many control archive members.")
            name = sources.safe_name(member.name).as_posix()
            if name in names:
                raise ValueError("Duplicate control archive member.")
            names.add(name)
            if member.isdir():
                continue
            if not member.isfile() or not 0 <= member.size <= sources.MAX_MEMBER:
                raise ValueError("Unsafe control archive member.")
            total += member.size
            if total > sources.MAX_TOTAL:
                raise ValueError("Control archive expansion exceeds its bound.")
            with archive.extractfile(member) as stream:
                value = stream.read(member.size + 1)
            if len(value) != member.size:
                raise ValueError("Incomplete control archive member.")
            files[name] = value
    suffix = "/completion/" + publication.REPORT
    roots = [name[: -len(suffix)] for name in files if name.endswith(suffix)]
    if len(roots) != 1 or len(sources.safe_name(roots[0]).parts) != 1:
        raise ValueError("Archive must contain exactly one top-level PR76 run.")
    root = roots[0]
    # The documented archive may also contain the separate read verification.
    allowed = {root, root + "-verification"}
    if any(sources.safe_name(name).parts[0] not in allowed for name in files):
        raise ValueError("Unexpected control archive root.")
    return root, files


def checked_sources(files, root, consumed):
    prepared = sources.read_json(files[root + "/preparation.json"])
    actual = prepared["software"]["software_commit"]
    if not isinstance(actual, str) or re.fullmatch("[0-9a-f]{40}", actual) is None:
        raise ValueError("Invalid original execution commit.")
    # Execute only the reviewed verifier, never code supplied by an archive.
    # The PR76 merge has the reviewed tree; arbitrary later implementations
    # require an explicit new review instead of silent historical substitution.
    if cross.git("rev-parse", actual + "^{tree}") != cross.git(
        "rev-parse", REVIEWED_COMMIT + "^{tree}"
    ):
        raise ValueError("PR76 execution tree is not the reviewed corrected tree.")
    for name, digest in prepared["software"]["source_sha256"].items():
        if sources.sha256(consumed.git_file(actual, name)) != digest:
            raise ValueError("Original PR76 source binding differs: " + name)
    return actual


@contextmanager
def verified_archive(path, digest, consumed, parent):
    """Keep original bytes under the caller's final publication rechecks."""
    path = Path(path).absolute()
    raw = sources.bounded_read(path)
    if not isinstance(digest, str) or sources.sha256(raw) != digest:
        raise ValueError("Original PR76 archive SHA-256 differs.")
    consumed.add_archive(path, raw)
    root, files = archive_files(raw)
    actual = checked_sources(files, root, consumed)
    with tempfile.TemporaryDirectory(prefix=".time-control-", dir=parent) as temporary:
        temporary = Path(temporary)
        checkout = temporary / "checkout"
        owned = False
        try:
            for name, value in files.items():
                target = temporary / "archive" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(value)
            source = temporary / "archive" / root
            cross.git("worktree", "add", "--detach", str(checkout), REVIEWED_COMMIT)
            owned = True
            environment = {
                **os.environ,
                "PYTHONPATH": str(checkout / "src"),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            command = [
                sys.executable,
                str(checkout / "scripts/run_global_restarts.py"),
                "verify",
                str(source),
                "--output",
                str(temporary / "verification"),
            ]
            with (temporary / "verify.log").open("wb") as log:
                child = subprocess.Popen(
                    command,
                    cwd=checkout,
                    env=environment,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                try:
                    left = consumed.clock.seconds - (
                        time.monotonic() - consumed.clock.started
                    )
                    code = child.wait(timeout=max(0.01, left))
                    if code:
                        detail = (temporary / "verify.log").read_text()[-4000:]
                        raise ValueError(
                            "Original PR76 read verification failed:\n" + detail
                        )
                except BaseException:
                    _stop_worker(child)
                    raise
            consumed.check()
            yield (
                source,
                {
                    "archive_sha256": digest,
                    "execution_commit": actual,
                    "reviewed_verifier_commit": REVIEWED_COMMIT,
                    "original_read_verification": "passed",
                },
            )
        finally:
            if owned:
                cross.git("worktree", "remove", str(checkout))


def eligibility(source, identity, technical=False):
    """Use only technical evidence; curve quality cannot affect eligibility."""
    prepared = sources.read_json((source / "preparation.json").read_bytes())
    expected_scope = "technical" if technical else "scientific"
    if prepared["scope"] != expected_scope:
        raise ValueError("Control scope differs from the planned comparison.")
    slots = [1] if technical else profile.configuration()["reuse_cells"]
    expected_seeds = [73] if technical else list(profile.SEEDS)
    expected_iterations = 2 if technical else 2000
    reasons, controls = [], []
    for number, seed in zip(slots, expected_seeds, strict=True):
        directory = source / f"cell-{number:02d}"
        request = sources.read_json(
            (source / f"request-{number:02d}.json").read_bytes()
        )
        plan = request["cell"]
        if plan["seed"] != seed or plan["niterations"] != expected_iterations:
            raise ValueError("Wrong fixed PR76 control slot, seed or budget.")
        options = sources.read_json((directory / "options.json").read_bytes())
        outcome = sources.read_json((directory / "outcome.json").read_bytes())
        if outcome["status"] not in {"completed", "worker_failed"}:
            raise ValueError("Incomplete original control.")
        runtime = options.get("budget_runtime")
        if runtime is None:
            reasons.append(
                f"cell-{number:02d}: actual CPU/Julia/GC thread evidence absent"
            )
        else:
            try:
                profile.validate_runtime(runtime)
            except (ValueError, KeyError, TypeError):
                reasons.append(
                    f"cell-{number:02d}: incompatible native runtime evidence"
                )
            worker_runtime = directory / "worker/time_budget_runtime.json"
            if (
                not worker_runtime.is_file()
                or sources.read_json(worker_runtime.read_bytes()) != runtime
            ):
                reasons.append(f"cell-{number:02d}: actual worker runtime is not bound")
        controls.append(
            {
                "number": number,
                "seed": seed,
                "status": outcome["status"],
                "environment": cross.environment_key(options["initial"]["environment"]),
                "budget_runtime": runtime,
            }
        )
    return {
        **identity,
        "eligible": not reasons,
        "reasons": reasons,
        "controls": controls,
        "whole_arm_only": True,
        "quality_used_for_eligibility": False,
        "automatic_fallback": False,
    }


def audit(path, digest, output):
    """Publish a read-only eligibility finding, not a scientific comparison."""
    from .iteration_time import freeze_software

    def build(consumed):
        profile.configuration()
        software = freeze_software(consumed)
        with verified_archive(
            path, digest, consumed, Path(output).absolute().parent
        ) as (source, identity):
            result = eligibility(source, identity)
        return (
            {
                "format": "ringdown-sr-time-control-eligibility-1",
                "software": software,
                "eligibility": result,
                "search_calls": 0,
            },
            "# Eignung des PR76-Kontrollarms\n\n"
            + (
                "Technische Belege vorhanden; Abgleich mit neuer Vorbereitung bleibt erforderlich.\n"
                if result["eligible"]
                else "Wiederverwendung nicht freigegeben. Gründe stehen im JSON-Bericht; kein automatischer Ersatzlauf.\n"
            ),
            {},
        )

    return publication.export_transaction(output, build, seconds=1800)
