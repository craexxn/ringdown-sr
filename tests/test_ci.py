"""Guard the cheap CI path against skipped runtime changes and broken prose links."""

import base64
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
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
        return {
            "action": "synchronize",
            "pull_request": {
                "base": {"sha": base},
                "head": {"sha": head},
                "draft": False,
                "state": "open",
                "merged": False,
            },
        }
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
    assert output.read_text() == "full=true\ncomparison_known=false\nmode=full\n"
    assert "Event unavailable" in capsys.readouterr().out


def scope_output(root, data, monkeypatch, name="pull_request"):
    source, output = root / "event.json", root / "scope.txt"
    source.write_text(json.dumps(data))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(source))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_EVENT_NAME", name)
    monkeypatch.setattr(CI, "ROOT", root)
    monkeypatch.setattr("sys.argv", [str(SCRIPT), "scope"])
    CI.main()
    return dict(line.split("=", 1) for line in output.read_text().splitlines())


@pytest.mark.parametrize(
    "action,draft,code_mode",
    [
        ("opened", True, "development"),
        ("reopened", True, "development"),
        ("synchronize", True, "development"),
        ("converted_to_draft", True, "development"),
        ("ready_for_review", False, "full"),
        ("synchronize", False, "full"),
    ],
)
@pytest.mark.parametrize(
    "path", ["README.md", "source.py", "docs/supplemental_assessment.md"]
)
def test_actual_pr_scope_cli_separates_prose_development_and_ready(
    repository, monkeypatch, action, draft, code_mode, path
):
    root, base = repository
    target = root / path
    target.parent.mkdir(exist_ok=True)
    target.write_text("Changed input.\n")
    head = commit(root)
    data = event(base, head)
    data["action"] = action
    data["pull_request"]["draft"] = draft
    prose = path == "README.md"
    assert scope_output(root, data, monkeypatch) == {
        "full": "false" if prose else "true",
        "comparison_known": "true",
        "mode": "docs" if prose else code_mode,
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("draft", None),
        ("draft", "true"),
        ("draft", 1),
        ("draft", 0),
        ("draft", []),
        ("draft", {}),
        ("draft", "false"),
        ("state", "closed"),
        ("state", None),
        ("merged", True),
        ("merged", None),
        ("action", "edited"),
        ("action", None),
        ("action", []),
        ("action", "ready_for_review"),
    ],
)
@pytest.mark.parametrize("path", ["README.md", "source.py"])
def test_invalid_or_contradictory_event_metadata_cannot_save_work(
    repository, monkeypatch, field, value, path
):
    root, base = repository
    (root / path).write_text("Changed input.\n")
    data = event(base, commit(root))
    data["pull_request"]["draft"] = True
    target = data if field == "action" else data["pull_request"]
    if value is None:
        del target[field]
    else:
        target[field] = value
    assert scope_output(root, data, monkeypatch) == {
        "full": "true",
        "comparison_known": "true",
        "mode": "full",
    }


def test_converted_to_draft_with_false_draft_cannot_save_work(repository, monkeypatch):
    root, base = repository
    (root / "README.md").write_text("Changed prose.\n")
    data = event(base, commit(root))
    data["action"] = "converted_to_draft"
    assert scope_output(root, data, monkeypatch)["mode"] == "full"


@pytest.mark.parametrize("unknown", ["missing_commit", "empty_diff"])
def test_unknown_or_empty_draft_comparison_never_defers_native_work(
    repository, monkeypatch, unknown
):
    root, base = repository
    data = event(base, "a" * 40 if unknown == "missing_commit" else base)
    data["pull_request"]["draft"] = True
    assert scope_output(root, data, monkeypatch) == {
        "full": "true",
        "comparison_known": "false",
        "mode": "full",
    }


@pytest.mark.parametrize("name", ["push", "workflow_dispatch", "unknown"])
@pytest.mark.parametrize("path", ["README.md", "source.py"])
def test_main_preserves_scope_and_manual_unknown_always_run_full(
    repository, monkeypatch, name, path
):
    root, base = repository
    (root / path).write_text("Changed input.\n")
    data = event(base, commit(root), "push")
    output = scope_output(root, data, monkeypatch, name)
    assert output["mode"] == (
        "docs" if name == "push" and path == "README.md" else "full"
    )
    assert output["comparison_known"] == ("true" if name == "push" else "false")


def test_unexpected_scope_process_failure_stops_instead_of_deferring(
    repository, monkeypatch
):
    root, base = repository

    def fail(*args):
        raise RuntimeError("synthetic process error")

    monkeypatch.setattr(CI, "full_check_required", fail)
    with pytest.raises(RuntimeError, match="process error"):
        scope_output(root, event(base, base), monkeypatch)
    assert not (root / "scope.txt").exists()


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


def complete_needs(full="true", mode=None, known="true"):
    mode = mode or ("full" if full == "true" else "docs")
    return {
        "prepare": {
            "result": "success",
            "outputs": {
                "full": full,
                "mode": mode,
                "comparison_known": known,
            },
        },
        **{
            name: {"result": "success" if mode == "full" else "skipped", "outputs": {}}
            for name in CI.NATIVE_JOBS
        },
    }


@pytest.mark.parametrize("full", ["true", "false"])
def test_gate_accepts_only_complete_technical_or_prose_paths(full):
    CI.check_completion(complete_needs(full))


def test_development_gate_explicitly_withholds_full_clearance(capsys):
    with pytest.raises(
        ValueError, match="Schnelle Prüfungen bestanden.*keine vollständige CI-Freigabe"
    ):
        CI.check_completion(complete_needs(mode="development"))
    assert "passed" not in capsys.readouterr().out


def test_development_prepare_failure_is_not_reported_as_deferred_success():
    needs = complete_needs(mode="development")
    needs["prepare"]["result"] = "failure"
    with pytest.raises(ValueError, match="Early checks did not succeed"):
        CI.check_completion(needs)


@pytest.mark.parametrize("mode", [None, "", "FULL", "reuse", True, [], {}])
def test_invalid_mode_never_gives_clearance(mode):
    needs = complete_needs()
    needs["prepare"]["outputs"]["mode"] = mode
    with pytest.raises(ValueError, match="mode"):
        CI.check_completion(needs)


@pytest.mark.parametrize("known", [None, "", "TRUE", True, False, 1, []])
def test_invalid_comparison_marker_never_gives_clearance(known):
    with pytest.raises(ValueError, match="comparison"):
        CI.check_completion(complete_needs(known=known))


@pytest.mark.parametrize(
    "full,mode,known",
    [
        ("false", "full", "true"),
        ("true", "docs", "true"),
        ("false", "development", "true"),
        ("true", "development", "false"),
        ("false", "docs", "false"),
    ],
)
def test_contradictory_scope_mode_comparison_blocks_gate(full, mode, known):
    with pytest.raises(ValueError, match="contradictory"):
        CI.check_completion(complete_needs(full, mode, known))


def test_conservative_full_scope_can_complete_when_comparison_unknown():
    CI.check_completion(complete_needs(known="false"))


@pytest.mark.parametrize("job", CI.NATIVE_JOBS)
@pytest.mark.parametrize("result", ["success", "failure", "cancelled", None])
def test_development_cannot_hide_unexpected_native_results(job, result):
    needs = complete_needs(mode="development")
    needs[job]["result"] = result
    with pytest.raises(ValueError, match=f"{job}: expected skipped"):
        CI.check_completion(needs)


@pytest.mark.parametrize("job", ["prepare", *CI.NATIVE_JOBS])
@pytest.mark.parametrize("result", ["failure", "cancelled", "skipped", None, ""])
def test_gate_blocks_every_failed_cancelled_skipped_or_missing_required_result(
    job, result
):
    needs = complete_needs()
    needs[job]["result"] = result
    with pytest.raises(ValueError):
        CI.check_completion(needs)


@pytest.mark.parametrize("job", CI.NATIVE_JOBS)
@pytest.mark.parametrize("result", ["success", "failure", "cancelled", None])
def test_prose_gate_requires_all_three_explicit_skips(job, result):
    needs = complete_needs("false")
    needs[job]["result"] = result
    with pytest.raises(ValueError):
        CI.check_completion(needs)


@pytest.mark.parametrize("scope", [None, "", "TRUE", "False", " true", True, False, 0])
def test_successful_native_jobs_cannot_mask_invalid_scope(scope):
    needs = complete_needs()
    needs["prepare"]["outputs"]["full"] = scope
    with pytest.raises(ValueError, match="scope"):
        CI.check_completion(needs)


@pytest.mark.parametrize("field", ["outputs", "result"])
@pytest.mark.parametrize("job", ["prepare", *CI.NATIVE_JOBS])
def test_missing_job_or_required_field_blocks_gate(job, field):
    needs = complete_needs()
    del needs[job]
    with pytest.raises(ValueError):
        CI.check_completion(needs)
    needs = complete_needs()
    if field == "outputs" and job != "prepare":
        needs[job] = None
    else:
        del needs[job][field]
    with pytest.raises(ValueError):
        CI.check_completion(needs)


@pytest.mark.parametrize("needs", [None, [], {}, {**complete_needs(), "extra": {}}])
def test_gate_requires_exact_job_set(needs):
    with pytest.raises(ValueError):
        CI.check_completion(needs)


@pytest.mark.parametrize("raw", ["{}", "{broken", "null", ""])
def test_gate_cli_fails_closed_on_missing_or_malformed_json(raw):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "gate"],
        env={**os.environ, "CI_NEEDS": raw},
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0


def test_scope_write_failure_is_not_swallowed(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path))
    monkeypatch.setattr("sys.argv", [str(SCRIPT), "scope"])
    with pytest.raises(OSError):
        CI.main()


@pytest.mark.parametrize("path", sorted(CI.RUNTIME_DOCUMENTS))
def test_every_runtime_document_selects_full_with_a_real_diff(repository, path):
    root, base = repository
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("Runtime input.\n")
    head = commit(root)
    assert CI.full_check_required("pull_request", event(base, head), root)[0]


@pytest.fixture
def history_repository(repository, tmp_path, monkeypatch):
    remote, initial = repository
    git(remote, "switch", "-c", "frozen-plan")
    plan = remote / "plan.md"
    plan.write_text("Frozen plan.\n")
    frozen = commit(remote)
    git(remote, "update-ref", "refs/pull/7/head", frozen)
    git(remote, "switch", "main")
    root = tmp_path / "checkout"
    git(
        tmp_path,
        "clone",
        "--no-local",
        "--single-branch",
        "--branch",
        "main",
        str(remote),
        str(root),
    )
    git(root, "checkout", "--detach", initial)
    (root / "scripts").mkdir()
    bindings = [
        {
            "required_commit": frozen,
            "durable_remote_ref": "refs/pull/7/head",
            "files_sha256": {"plan.md": hashlib.sha256(b"Frozen plan.\n").hexdigest()},
        }
    ]
    (root / "scripts/ci_historical_refs.json").write_text(json.dumps(bindings))
    real_run = subprocess.run
    calls = []

    def local_transport(args, **kwargs):
        calls.append((args, kwargs))
        if args[:2] == ["git", "fetch"]:
            args = [
                str(remote) if arg == "https://example.invalid/owner/repo.git" else arg
                for arg in args
            ]
        return real_run(args, **kwargs)

    monkeypatch.setattr(CI.subprocess, "run", local_transport)
    return root, remote, initial, frozen, calls


def test_history_fetch_recovers_squashed_plan_without_persisting_credentials(
    history_repository,
):
    root, _, initial, frozen, calls = history_repository
    assert (
        subprocess.run(
            ["git", "cat-file", "-e", frozen],
            cwd=root,
            capture_output=True,
            check=False,
        ).returncode
        != 0
    )
    config = (root / ".git/config").read_bytes()
    CI.prepare_history(
        root, "https://example.invalid", "owner/repo", "test-only-secret"
    )
    assert git(root, "rev-parse", "HEAD") == initial
    assert git(root, "show", f"{frozen}:plan.md") == "Frozen plan."
    assert (root / ".git/config").read_bytes() == config
    fetches = [(args, kw) for args, kw in calls if args[:2] == ["git", "fetch"]]
    assert len(fetches) == 1
    args, kwargs = fetches[0]
    encoded = base64.b64encode(b"x-access-token:test-only-secret").decode()
    assert kwargs["env"]["GIT_CONFIG_VALUE_0"] == f"AUTHORIZATION: basic {encoded}"
    assert "CI_GITHUB_TOKEN" not in kwargs["env"]
    assert all("test-only-secret" not in arg and encoded not in arg for arg in args)
    assert all(
        kw.get("env") is None for args, kw in calls if args[:2] != ["git", "fetch"]
    )


@pytest.mark.parametrize(
    "fault",
    [
        "missing_ref",
        "missing_commit",
        "wrong_ancestry",
        "changed_bytes",
        "missing_file",
    ],
)
def test_history_failures_stop_before_tests(history_repository, fault):
    root, remote, initial, _, _ = history_repository
    path = root / "scripts/ci_historical_refs.json"
    data = json.loads(path.read_text())
    if fault == "missing_ref":
        git(remote, "update-ref", "-d", "refs/pull/7/head")
    elif fault == "missing_commit":
        data[0]["required_commit"] = "a" * 40
    elif fault == "wrong_ancestry":
        git(remote, "update-ref", "refs/pull/7/head", initial)
    elif fault == "changed_bytes":
        data[0]["files_sha256"]["plan.md"] = "0" * 64
    else:
        data[0]["files_sha256"]["missing.md"] = "0" * 64
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        CI.prepare_history(
            root, "https://example.invalid", "owner/repo", "test-only-secret"
        )
    assert git(root, "rev-parse", "HEAD") == initial


def workflow_jobs():
    text = (CI.ROOT / ".github/workflows/technical-checks.yml").read_text()
    sections = re.split(
        r"^  ([a-z-]+):\n", text.split("jobs:\n", 1)[1], flags=re.MULTILINE
    )
    return text, dict(zip(sections[1::2], sections[2::2], strict=True))


def workflow_steps(job):
    return re.findall(
        r"^      - name: .*(?:\n(?!      - name: ).*)*", job, flags=re.MULTILINE
    )


def test_all_original_commands_options_error_wrappers_and_order_are_preserved():
    inventory = json.loads(
        (CI.ROOT / "tests/fixtures/ci_steps_before_parallel.json").read_text()
    )
    _, jobs = workflow_jobs()
    found = {}
    for name, job in jobs.items():
        blocks = workflow_steps(job)
        for raw in blocks:
            label = raw.splitlines()[0].split("- name: ", 1)[1]
            raw = re.sub(
                r"^        if: steps.scope.outputs.full != 'false'\n",
                "",
                raw,
                flags=re.MULTILINE,
            )
            raw = raw.replace("          ref: ${{ github.sha }}\n", "")
            found.setdefault(label, []).append(
                (name, hashlib.sha256(raw.strip().encode()).hexdigest())
            )
    for item in inventory["steps"]:
        matches = found.pop(item["name"])
        expected = [item["group"]]
        if item["name"] == "Check out repository":
            expected = list(jobs)
        elif item["name"] in {"Install uv", "Install locked Python environment"}:
            expected = ["prepare", *CI.NATIVE_JOBS]
        elif item["group"] == "runtime-each-native":
            expected = list(CI.NATIVE_JOBS)
        assert matches == [(job, item["sha256"]) for job in expected]
    assert set(found) == {
        "Record tested commit and tree",
        "Prepare historical Git references",
        "Require complete CI coverage",
        "Reject workflow cancellation",
    }
    for group in CI.NATIVE_JOBS:
        ordered = [
            item["name"] for item in inventory["steps"] if item["group"] == group
        ]
        actual = [
            raw.splitlines()[0].split("- name: ", 1)[1]
            for raw in workflow_steps(jobs[group])
        ]
        assert [name for name in actual if name in ordered] == ordered


def test_workflow_requires_early_success_and_all_native_results_without_bypasses():
    text, jobs = workflow_jobs()
    assert list(jobs) == ["prepare", *CI.NATIVE_JOBS, "technical-checks"]
    assert "continue-on-error" not in text and "matrix:" not in text
    assert "contents: read" in text
    assert (
        "group: technical-checks-${{ github.ref }}\n  cancel-in-progress: true" in text
    )
    assert text.count("ref: ${{ github.sha }}") == 5
    assert text.count("persist-credentials: false") == 5
    assert text.count("fetch-depth: 0") == 5
    assert text.count("timeout-minutes: 75") == 5
    assert "OPENBLAS" not in text.split("jobs:", 1)[0]
    assert "full: ${{ steps.scope.outputs.full }}" in jobs["prepare"]
    assert jobs["prepare"].count("if: steps.scope.outputs.full != 'false'") == 6
    assert jobs["prepare"].index("scripts/check_ci.py history") < jobs["prepare"].index(
        "uv run --locked pytest"
    )
    for job in CI.NATIVE_JOBS:
        assert (
            "needs: prepare\n    if: needs.prepare.outputs.mode == 'full'" in jobs[job]
        )
        assert jobs[job].count("if:") == 1
        assert jobs[job].index("scripts/check_ci.py history") < jobs[job].index(
            "scripts/check_environment.py"
        )
    gate = jobs["technical-checks"]
    assert "needs: [prepare, native-a, native-b, native-c]\n    if: always()" in gate
    assert "CI_NEEDS: ${{ toJSON(needs) }}" in gate
    assert "if: cancelled()\n        run: exit 1" in gate
    assert "if: ${{ !cancelled() }}" in gate
    assert gate.index("Reject workflow cancellation") < gate.index(
        "Require complete CI coverage"
    )
    assert "run: python3 scripts/check_ci.py gate" in gate


def test_workflow_events_outputs_and_manual_gate_name_are_unambiguous():
    text, jobs = workflow_jobs()
    assert (
        "types: [opened, reopened, synchronize, ready_for_review, converted_to_draft]"
        in text
    )
    assert "pull_request_target" not in text
    assert "paths:" not in text and "paths-ignore:" not in text
    for field in ("full", "mode", "comparison_known"):
        assert f"{field}: ${{{{ steps.scope.outputs.{field} }}}}" in jobs["prepare"]
    assert (
        "name: ${{ github.event_name == 'workflow_dispatch' && 'manual-technical-checks' || 'technical-checks' }}"
        in jobs["technical-checks"]
    )
