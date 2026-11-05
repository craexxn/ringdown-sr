"""Publish separate assessment artifacts, with fail-closed cancellation handling."""

import math
import signal
import time
from contextlib import ExitStack, contextmanager
from pathlib import Path

from .assessment_sources import ROOT, json_bytes, safe_name, sha256

REPORT = "assessment_report.json"
SUMMARY = "assessment_summary.md"
MANIFEST = "assessment_checksums.json"
LOCK = "ASSESSMENT_LOCKED"
PENDING = REPORT + ".tmp"


class Deadline:
    """A cooperative clock and signal deadline for the bounded, read-only import."""

    def __init__(self, seconds):
        if isinstance(seconds, bool) or not math.isfinite(seconds) or seconds <= 0:
            raise ValueError("Deadline must be finite and positive.")
        self.seconds = seconds
        self.started = time.monotonic()

    def check(self):
        if time.monotonic() - self.started >= self.seconds:
            raise TimeoutError("Assessment deadline exceeded.")

    def cancel(self):
        signal.setitimer(signal.ITIMER_REAL, 0)

    @contextmanager
    def active(self):
        if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
            raise RuntimeError("An existing alarm must not be replaced.")

        def interrupt(signum, frame):
            if signum == signal.SIGALRM:
                raise TimeoutError("Assessment deadline exceeded.")
            raise InterruptedError("Assessment interrupted by signal " + str(signum))

        with ExitStack() as stack:
            for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGALRM):
                previous = signal.signal(sig, interrupt)
                stack.callback(signal.signal, sig, previous)
            stack.callback(self.cancel)
            signal.setitimer(signal.ITIMER_REAL, self.seconds)
            yield self


class Consumption:
    """Freeze exact source/input bytes before consuming them, then check again."""

    def __init__(self, clock):
        self.clock = clock
        self.files = {}
        self.callbacks = []

    def add(self, path, contents):
        path = Path(path).absolute()
        if path in self.files and self.files[path] != contents:
            raise ValueError("Conflicting consumption snapshot.")
        self.files[path] = contents

    def check(self):
        self.clock.check()
        for path, raw in self.files.items():
            if path.is_symlink() or path.read_bytes() != raw:
                raise ValueError("Consumed file changed: " + str(path))
        for callback in self.callbacks:
            callback()
        self.clock.check()


def reserve_output(path):
    """Allow new sibling outputs, never write into sources or an original run."""
    path = Path(path).absolute()
    if path != path.resolve() or path.exists() or ROOT.is_relative_to(path):
        raise ValueError("Use a new assessment directory without symlink parents.")
    if any(
        path.is_relative_to(ROOT / n)
        for n in (
            "src",
            "scripts",
            "docs",
            "data",
            "julia",
            "tests",
            ".git",
            ".venv",
        )
    ):
        raise ValueError("Assessment output cannot be inside project sources.")
    for parent in path.parents:
        if any(
            (parent / n).exists()
            for n in (
                "report.json",
                "checksums.json",
                REPORT,
                MANIFEST,
                LOCK,
            )
        ):
            raise ValueError("Assessment output cannot be inside an existing run.")
    path.mkdir(parents=True, exist_ok=False)
    (path / LOCK).write_text("Publication has not completed.\n", encoding="utf-8")
    return path


def verify_bytes(output, expected, *, locked=True):
    names = set(expected) | ({LOCK} if locked else set())
    if {path.name for path in output.iterdir()} != names:
        raise ValueError("Assessment output inventory changed during publication.")
    for name, contents in expected.items():
        path = output / name
        if path.is_symlink() or path.read_bytes() != contents:
            raise ValueError("Assessment artifact changed: " + name)


def publish(output, report, summary, payloads, consumed):
    """Recheck closing documents and input bytes immediately before publication."""
    consumed.check()
    names = {REPORT, SUMMARY, MANIFEST, LOCK, PENDING}
    for name in payloads:
        if len(safe_name(name).parts) != 1 or name in names:
            raise ValueError("Invalid assessment payload name.")
    report = {**report, "status": "completed"}
    documents = {**payloads, SUMMARY: summary.encode(), REPORT: json_bytes(report)}
    manifest = json_bytes({name: sha256(raw) for name, raw in documents.items()})
    expected = {**documents, MANIFEST: manifest}
    for name, contents in expected.items():
        if name != REPORT:
            (output / name).write_bytes(contents)
    consumed.check()
    pending = output / PENDING
    pending.write_bytes(documents[REPORT])
    consumed.check()
    # In particular, a mutation while writing PENDING must not escape this check.
    verify_bytes(
        output,
        {
            **{k: v for k, v in expected.items() if k != REPORT},
            PENDING: documents[REPORT],
        },
    )
    pending.replace(output / REPORT)
    consumed.check()
    verify_bytes(output, expected)
    (output / LOCK).unlink()
    consumed.check()
    verify_bytes(output, expected, locked=False)
    return report


def revoke(output, error, clock):
    """Retain partial evidence but revoke aggregates even during a second signal."""
    clock.cancel()
    failure = {
        "format": "ringdown-sr-assessment-publication-1",
        "status": "failed",
        "release": "locked",
        "series": [],
        "groups": [],
        "error": f"{type(error).__name__}: {error}",
        "cleanup_errors": [],
        "deferred_signals": [],
    }
    mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
    with ExitStack() as stack:
        stack.callback(signal.pthread_sigmask, signal.SIG_SETMASK, mask)

        def defer(signum, frame):
            failure["deferred_signals"].append(signum)

        for sig in (signal.SIGINT, signal.SIGTERM):
            previous = signal.signal(sig, defer)
            stack.callback(signal.signal, sig, previous)
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)

        def attempt(name, action):
            try:
                action()
                return True
            except BaseException as cleanup_error:  # noqa: BLE001 -- Continue every revocation attempt.
                failure["cleanup_errors"].append(
                    {
                        "operation": name,
                        "error": f"{type(cleanup_error).__name__}: {cleanup_error}",
                    }
                )
                return False

        lock = lambda: (output / LOCK).write_text(
            "Assessment release revoked.\n", encoding="utf-8"
        )
        if not attempt("lock publication", lock):
            attempt("retry lock publication", lock)
        for name in (REPORT, SUMMARY, MANIFEST, PENDING):
            remove = lambda n=name: (output / n).unlink(missing_ok=True)
            if not attempt("remove " + name, remove):
                attempt("retry remove " + name, remove)
        write_report = lambda: (output / REPORT).write_bytes(json_bytes(failure))
        if not attempt("write locked report", write_report):
            attempt("retry write locked report", write_report)
        attempt(
            "write failure evidence",
            lambda: (output / "assessment_failure.json").write_bytes(
                json_bytes(failure)
            ),
        )
    return failure


def export_transaction(output, build, *, seconds=300):
    """Build under cancellation handling; only a complete final package is released."""
    clock = Deadline(seconds)
    consumed = Consumption(clock)
    owned, revoked = None, False
    try:
        # Do not reserve an output when an existing alarm prevents cancellation control.
        with clock.active():
            owned = reserve_output(output)
            try:
                report, summary, payloads = build(consumed)
                result = publish(owned, report, summary, payloads, consumed)
            except BaseException as error:
                revoke(owned, error, clock)
                revoked = True
                raise
        return result
    except BaseException as error:
        # Context teardown is still part of publication, even after success was renamed.
        if owned is not None and not revoked:
            revoke(owned, error, clock)
        raise
