"""Guard the cheap CI path against skipped runtime changes and broken prose links."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_ci.py"
SPEC = importlib.util.spec_from_file_location("check_ci", SCRIPT)
CI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CI)


@pytest.mark.parametrize("paths", [["README.md"], ["AGENTS.md", "docs/nested/plan.md"]])
def test_only_allowed_prose_can_skip_the_technical_suite(paths):
    assert CI.documentation_only(paths)


@pytest.mark.parametrize(
    "path",
    [
        "src/ringdown_sr/signals.py",
        "tests/test_signals.py",
        "scripts/check_ci.py",
        "pyproject.toml",
        "uv.lock",
        ".python-version",
        "configs/pilot_white.toml",
        "julia/Manifest.toml",
        ".github/workflows/technical-checks.yml",
        "docs/noiseless_control_plan.md",
        "docs/search_representation_plan.md",
        "docs/constant_diagnostic_plan.md",
        "docs/free_optimizer_budget_plan.md",
        "docs/search_trajectory_plan.md",
        "docs/search_trajectory_replay_policy.md",
        "docs/trigonometric_grammar_plan.md",
        "docs/search_duration_plan.md",
        "docs/search_duration_simplification_plan.md",
        "docs/search_duration_prediction_plan.md",
        "docs/local_optimizer_plan.md",
        "docs/outer_search_ladder_plan.md",
        "docs/transfer_check_plan.md",
        "docs/seed_driver_crosscheck_plan.md",
        "data/transfer_check_inputs.npz",
        "data/transfer_check_inputs.json",
        "docs/reference.npz",
        "other.md",
    ],
)
def test_runtime_dependencies_workflows_and_unknown_paths_always_run_full(path):
    assert not CI.documentation_only(["README.md", path])


def test_empty_diff_cannot_bypass_the_suite():
    assert not CI.documentation_only([])


def git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repository(tmp_path):
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "core.autocrlf", "false")
    git(tmp_path, "config", "user.name", "CI test")
    git(tmp_path, "config", "user.email", "ci-test@example.invalid")
    (tmp_path / "README.md").write_text("Initial prose.\n")
    (tmp_path / "source.py").write_text("value = 1\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "Initial fixture")
    return tmp_path, git(tmp_path, "rev-parse", "HEAD")


def event(base, head, name="pull_request"):
    if name == "pull_request":
        return {"pull_request": {"base": {"sha": base}, "head": {"sha": head}}}
    return {"before": base, "after": head, "forced": False}


def commit(root):
    git(root, "add", ".")
    git(root, "commit", "-m", "Change fixture")
    return git(root, "rev-parse", "HEAD")


@pytest.mark.parametrize("name", ["pull_request", "push"])
def test_real_git_prose_diff_uses_the_cheap_path(repository, name):
    root, base = repository
    (root / "README.md").write_text("Updated prose.\n")
    head = commit(root)
    assert CI.full_check_required(name, event(base, head, name), root)[0] is False


@pytest.mark.parametrize("direction", ["code_to_docs", "docs_to_code"])
def test_both_sides_of_a_real_rename_are_considered(repository, direction):
    root, base = repository
    if direction == "code_to_docs":
        (root / "docs").mkdir()
        git(root, "mv", "source.py", "docs/renamed.md")
    else:
        git(root, "mv", "README.md", "renamed.py")
    head = commit(root)
    paths = CI.changed_paths("pull_request", event(base, head), root)
    assert len(paths) == 2
    assert CI.full_check_required("pull_request", event(base, head), root)[0] is True


def test_code_after_hundreds_of_docs_is_not_lost_to_a_diff_page_limit(repository):
    root, base = repository
    docs = root / "docs"
    docs.mkdir()
    for index in range(305):
        (docs / f"page-{index:03d}.md").write_text("Prose.\n")
    (root / "source.py").write_text("value = 2\n")
    head = commit(root)
    paths = CI.changed_paths("pull_request", event(base, head), root)
    assert len(paths) == 306
    assert CI.full_check_required("pull_request", event(base, head), root)[0] is True


def test_pr_diff_excludes_changes_only_on_the_base_branch(repository):
    root, base = repository
    git(root, "switch", "-c", "prose")
    (root / "README.md").write_text("Updated prose.\n")
    head = commit(root)
    git(root, "switch", "main")
    (root / "source.py").write_text("value = 2\n")
    advanced = commit(root)
    assert CI.changed_paths("pull_request", event(advanced, head), root) == [
        "README.md"
    ]
    assert base != advanced


@pytest.mark.parametrize(
    "name, data",
    [
        ("workflow_dispatch", {}),
        ("unknown", {}),
        ("pull_request", {}),
        ("pull_request", {"pull_request": None}),
        ("push", {"forced": True}),
        ("push", {"before": "0" * 40, "after": "a" * 40}),
        ("push", {"before": "--help", "after": "a" * 40}),
        ("push", {"before": "a" * 40, "after": "b" * 40}),
    ],
)
def test_manual_missing_invalid_or_unavailable_comparisons_fall_back_to_full(
    tmp_path, name, data
):
    assert CI.full_check_required(name, data, tmp_path)[0] is True


def test_missing_event_file_writes_full_output(tmp_path, monkeypatch, capsys):
    output = tmp_path / "output.txt"
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setattr("sys.argv", [str(SCRIPT), "scope"])
    CI.main()
    assert output.read_text() == "full=true\n"
    assert "Event unavailable" in capsys.readouterr().out


def test_existing_file_targets_external_links_and_fragments(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (tmp_path / "source.py").write_text("value = 1\n")
    (docs / "with space.md").write_text("Target.\n")
    page = docs / "page.md"
    page.write_text(
        "[source](../source.py#L1) [root](/source.py) [space](<with space.md>)\n"
        "[encoded](with%20space.md) [section](#section) [site](https://example.invalid/x)\n"
        "[reference]: ../source.py\n",
        encoding="utf-8",
    )
    assert CI.check_document(page, tmp_path) == []


def test_missing_targets_are_checked_for_inline_and_reference_links(tmp_path):
    page = tmp_path / "README.md"
    page.write_text("[broken](absent.md)\n[target]: missing.py\n")
    errors = CI.check_document(page, tmp_path)
    assert len(errors) == 2
    assert "absent.md" in errors[0] and "missing.py" in errors[1]


def test_examples_inside_code_and_footnotes_are_not_file_links(tmp_path):
    page = tmp_path / "README.md"
    page.write_text(
        "`[sample](missing.md)`\n```markdown\n[example](absent.md)\n```\n"
        "~~~text\n[example](absent.md)\n~~~\n    [code](absent.md)\n[^1]: Note text.\n"
    )
    assert CI.check_document(page, tmp_path) == []


def test_crlf_and_markdown_hard_breaks_are_accepted(tmp_path):
    page = tmp_path / "README.md"
    page.write_bytes(b"First line.  \r\nNext line.\r\n")
    assert CI.check_document(page, tmp_path) == []


@pytest.mark.parametrize(
    "data", [b"No final newline", b"Trailing \n", b"Bad\xff\n", b"```\nunclosed\n"]
)
def test_format_and_encoding_errors_fail_the_cheap_check(tmp_path, data):
    page = tmp_path / "README.md"
    page.write_bytes(data)
    assert CI.check_document(page, tmp_path)


def test_links_cannot_escape_the_repository(tmp_path):
    page = tmp_path / "README.md"
    page.write_text("[outside](../outside.md)\n")
    assert CI.check_document(page, tmp_path)


def test_documentation_command_checks_all_tracked_markdown(repository, capsys):
    root, _ = repository
    CI.check_documentation(root)
    assert "1 Markdown files" in capsys.readouterr().out
    (root / "README.md").write_text("[broken](absent.md)\n")
    with pytest.raises(ValueError, match="absent.md"):
        CI.check_documentation(root)
