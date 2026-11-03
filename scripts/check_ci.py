"""Select conservative CI coverage and check local Markdown without dependencies."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DOCUMENTS = {
    "docs/constant_diagnostic_plan.md",
    "docs/free_optimizer_budget_plan.md",
    "docs/noiseless_control_plan.md",
    "docs/search_representation_plan.md",
    "docs/search_trajectory_plan.md",
    "docs/search_trajectory_replay_policy.md",
    "docs/trigonometric_grammar_plan.md",
    "docs/search_duration_plan.md",
    "docs/search_duration_verification_plan.md",
    "docs/search_duration_table_loss_note.md",
    "docs/search_duration_simplification_plan.md",
}
SHA = re.compile(r"[0-9a-f]{40}\Z")
LINK = re.compile(
    r"!?\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s)\n]+))(?:\s+[\"'][^\n]*?[\"'])?\s*\)"
)
REFERENCE = re.compile(r"^\s{0,3}\[([^\]]+)\]:\s*(?:<([^>\n]+)>|(\S+))")


def documentation_only(paths):
    """Require a nonempty diff containing only explicitly allowed prose files."""
    return bool(paths) and all(
        path not in RUNTIME_DOCUMENTS
        and (
            path in {"README.md", "AGENTS.md"}
            or (path.startswith("docs/") and path.endswith(".md"))
        )
        for path in paths
    )


def changed_paths(event_name, event, root):
    """Use all Git paths, with both sides of renames and no API page limits."""
    if event_name == "pull_request":
        base = event["pull_request"]["base"]["sha"]
        head = event["pull_request"]["head"]["sha"]
        separator = "..."
    elif event_name == "push" and not event.get("forced", False):
        base, head, separator = event["before"], event["after"], ".."
    else:
        raise ValueError("Manual, forced or unknown event requires full CI.")
    if any(
        not isinstance(sha, str) or not SHA.fullmatch(sha) or set(sha) == {"0"}
        for sha in (base, head)
    ):
        raise ValueError("Missing or invalid comparison commits.")
    result = subprocess.run(
        [
            "git",
            "diff",
            "--no-renames",
            "--name-only",
            "-z",
            f"{base}{separator}{head}",
            "--",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [os.fsdecode(path) for path in result.stdout.split(b"\0") if path]


def full_check_required(event_name, event, root):
    """Uncertainty always selects the full existing technical suite."""
    try:
        paths = changed_paths(event_name, event, root)
    except (
        KeyError,
        TypeError,
        ValueError,
        OSError,
        subprocess.CalledProcessError,
    ) as error:
        return True, f"Comparison unavailable ({type(error).__name__})."
    full = not documentation_only(paths)
    reason = (
        "Code, runtime input, other path or empty diff."
        if full
        else "Documentation-only diff."
    )
    return full, reason


def check_document(path, root):
    """Check UTF-8, basic whitespace and local file targets, without HTTP requests."""
    errors = []
    if path.is_symlink():
        return [f"{path.relative_to(root)}: Markdown must be a regular file."]
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as error:
        return [f"{path.relative_to(root)}: {type(error).__name__}."]
    label = path.relative_to(root)
    if text and not text.endswith("\n"):
        errors.append(f"{label}: Missing final newline.")
    if "\0" in text:
        errors.append(f"{label}: Unexpected NUL character.")
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        whitespace = line[len(line.rstrip(" \t")) :]
        if whitespace and whitespace != "  ":
            errors.append(
                f"{label}:{number}: Trailing whitespace (two-space Markdown breaks are allowed)."
            )
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is not None or line.startswith(("    ", "\t")):
            continue
        visible = re.sub(r"(`+).*?\1", "", line)
        targets = [first or second for first, second in LINK.findall(visible)]
        reference = REFERENCE.match(visible)
        if reference and not reference.group(1).startswith("^"):
            targets.append(reference.group(2) or reference.group(3))
        for target in targets:
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            name = unquote(parts.path)
            destination = (
                root / name.lstrip("/") if name.startswith("/") else path.parent / name
            ).resolve()
            if (
                not destination.is_relative_to(root.resolve())
                or not destination.exists()
            ):
                errors.append(
                    f"{label}:{number}: Missing or external local target {target!r}."
                )
    if fence is not None:
        errors.append(f"{label}: Unclosed fenced code block.")
    return errors


def check_documentation(root):
    tracked = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True
    ).stdout
    paths = [
        os.fsdecode(path) for path in tracked.split(b"\0") if path.endswith(b".md")
    ]
    errors = [error for name in paths for error in check_document(root / name, root)]
    if errors:
        raise ValueError("\n".join(errors))
    print(
        f"Documentation checks passed: {len(paths)} Markdown files; local file targets only."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("scope", "docs"))
    args = parser.parse_args()
    if args.mode == "docs":
        check_documentation(ROOT)
        return
    try:
        event = json.loads(
            Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8")
        )
    except (KeyError, OSError, ValueError) as error:
        full, reason = True, f"Event unavailable ({type(error).__name__})."
    else:
        full, reason = full_check_required(
            os.environ.get("GITHUB_EVENT_NAME"), event, ROOT
        )
    print(f"Full technical CI: {str(full).lower()}. {reason}")
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        output.write(f"full={str(full).lower()}\n")


if __name__ == "__main__":
    main()
