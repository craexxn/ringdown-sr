"""Check command boundaries and lossless, nonoverwriting archive partitions."""

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def command():
    return load_script("run_noise_followup")


@pytest.fixture
def fake_modules(monkeypatch):
    import ringdown_sr

    calls = []

    def install(name, functions):
        module = types.ModuleType(name)
        for function in functions:

            def called(*args, _function=function, **kwargs):
                calls.append((name, _function, args, kwargs))
                return {"status": "completed"}

            setattr(module, function, called)
        monkeypatch.setitem(sys.modules, "ringdown_sr." + name, module)
        monkeypatch.setattr(ringdown_sr, name, module, raising=False)
        return module

    install("noise_followup_inputs", ["prepare_inputs", "verify_inputs"])
    install("noise_followup_diagnostics", ["run", "verify"])
    install("noise_followup", ["run", "verify"])
    install("noise_followup_plots", ["export", "export_technical", "verify_export"])
    install("noise_followup_technical", ["run", "verify"])
    return calls, install


@pytest.mark.parametrize("action", ["run", "verify", "plots"])
def test_sampling_commands_bind_all_gates_and_shared_controls(
    command, fake_modules, action
):
    calls, _ = fake_modules
    arguments = [
        action,
        "--block",
        "sampling",
        "--inputs",
        "inputs",
        "--technical",
        "technical",
        "--estimators",
        "estimators",
        "--duration",
        "duration",
        "--output",
        "sampling",
    ]
    if action == "run":
        arguments += ["--max-cases", "2"]
    else:
        arguments += ["--export", "new-export"]
    assert command.main(arguments) == 0
    assert len(calls) == 1
    _, function, args, kwargs = calls[0]
    assert function == ("export" if action == "plots" else action)
    assert args[:3] == tuple(map(Path, ("inputs", "technical", "sampling")))
    assert kwargs["block"] == "sampling"
    assert kwargs["uniform"] == Path("duration")
    assert kwargs["diagnostics"] == Path("estimators")
    if action == "run":
        assert kwargs["max_cases"] == 2
    elif action == "verify":
        assert kwargs["export"] == Path("new-export")
    else:
        assert args[3] == Path("new-export")


@pytest.mark.parametrize("action", ["run", "verify", "plots"])
def test_sampling_without_duration_fails_before_dispatch(command, fake_modules, action):
    calls, _ = fake_modules
    arguments = [
        action,
        "--block",
        "sampling",
        "--inputs",
        "inputs",
        "--technical",
        "technical",
        "--estimators",
        "estimators",
        "--output",
        "sampling",
    ]
    if action == "plots":
        arguments += ["--export", "plots"]
    with pytest.raises(SystemExit) as error:
        command.main(arguments)
    assert error.value.code == 2
    assert not calls


def test_duration_rejects_control_path(command, fake_modules):
    calls, _ = fake_modules
    with pytest.raises(SystemExit):
        command.main(
            [
                "run",
                "--block",
                "duration",
                "--inputs",
                "i",
                "--technical",
                "t",
                "--estimators",
                "e",
                "--output",
                "o",
                "--duration",
                "wrong",
            ]
        )
    assert not calls


def test_paused_run_never_announces_completed_block(command, fake_modules, capsys):
    _, install = fake_modules
    module = install("noise_followup", [])
    module.run = lambda *args, **kwargs: {"status": "paused"}
    command.main(
        [
            "run",
            "--block",
            "duration",
            "--inputs",
            "i",
            "--technical",
            "t",
            "--estimators",
            "e",
            "--output",
            "o",
            "--max-cases",
            "1",
        ]
    )
    output = capsys.readouterr().out
    assert "paused" in output
    assert "block completed" not in output


def test_unknown_run_result_has_no_success_message(command, fake_modules, capsys):
    _, install = fake_modules
    module = install("noise_followup", [])
    module.run = lambda *args, **kwargs: {"status": "aborted"}
    with pytest.raises(ValueError, match="Unexpected follow-up"):
        command.main(
            [
                "run",
                "--block",
                "duration",
                "--inputs",
                "i",
                "--technical",
                "t",
                "--estimators",
                "e",
                "--output",
                "o",
            ]
        )
    assert not capsys.readouterr().out


@pytest.mark.parametrize("value", ["0", "-1", "1.5", "bad"])
def test_case_limit_is_positive_integer(command, value):
    with pytest.raises(SystemExit):
        command.parser().parse_args(
            [
                "run",
                "--block",
                "duration",
                "--inputs",
                "i",
                "--technical",
                "t",
                "--estimators",
                "e",
                "--output",
                "o",
                "--max-cases",
                value,
            ]
        )


@pytest.mark.parametrize(
    ("arguments", "module", "function", "kwargs"),
    [
        (
            ["prepare", "--output", "new"],
            "noise_followup_inputs",
            "prepare_inputs",
            {"purpose": "scientific"},
        ),
        (
            ["verify-inputs", "--inputs", "old", "--regenerate"],
            "noise_followup_inputs",
            "verify_inputs",
            {"regenerate": True},
        ),
        (
            ["estimator-check", "--output", "new"],
            "noise_followup_diagnostics",
            "run",
            {},
        ),
        (
            ["estimator-verify", "--output", "old"],
            "noise_followup_diagnostics",
            "verify",
            {"export": None},
        ),
        (
            ["technical-plots", "--technical", "old", "--export", "new"],
            "noise_followup_plots",
            "export_technical",
            {},
        ),
        (
            ["verify-plots", "--export", "old"],
            "noise_followup_plots",
            "verify_export",
            {},
        ),
    ],
)
def test_nonsearch_commands_dispatch_only_requested_operation(
    command, fake_modules, arguments, module, function, kwargs
):
    calls, _ = fake_modules
    command.main(arguments)
    assert len(calls) == 1
    assert calls[0][0:2] == (module, function)
    assert calls[0][3] == kwargs


def test_technical_verification_never_starts_workers(fake_modules):
    calls, _ = fake_modules
    load_script("check_noise_followup").main(["--verify", "existing"])
    assert calls == [("noise_followup_technical", "verify", (Path("existing"),), {})]


def archive_fixture(tmp_path):
    root = tmp_path / "run-001"
    for directory in (
        "inputs",
        "technical",
        "estimators",
        "technical-plots",
        "duration",
        "verification-duration",
        "plots-duration",
        "sampling",
        "verification-sampling",
        "plots-sampling",
    ):
        path = root / directory
        path.mkdir(parents=True)
        (path / "record.json").write_text(json.dumps({"role": directory}))
    (root / "inputs" / "large-background.npy").write_bytes(b"background" * 100)
    (root / "inputs-call.json").write_text('{"status":"completed"}\n')
    return root


def unpack_receipt(archive):
    with tarfile.open(archive) as packed:
        receipts = [item for item in packed if "/ARCHIVE-" in item.name]
        assert len(receipts) == 1
        return json.load(packed.extractfile(receipts[0]))


def test_archives_bind_predecessors_without_duplicating_inputs(command, tmp_path):
    root = archive_fixture(tmp_path)
    before = {
        p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    shared = command.archive(root, "shared")
    duration = command.archive(root, "duration")
    sampling = command.archive(root, "sampling")
    receipts = {
        part: unpack_receipt(path)
        for part, path in (
            ("shared", shared),
            ("duration", duration),
            ("sampling", sampling),
        )
    }
    assert "inputs/large-background.npy" in receipts["shared"]["files_sha256"]
    assert "inputs-call.json" in receipts["shared"]["files_sha256"]
    assert not any(
        name.startswith("inputs/")
        for part in ("duration", "sampling")
        for name in receipts[part]["files_sha256"]
    )
    assert receipts["duration"]["required_archives_sha256"] == {
        shared.name: hashlib.sha256(shared.read_bytes()).hexdigest()
    }
    assert receipts["sampling"]["required_archives_sha256"] == {
        shared.name: hashlib.sha256(shared.read_bytes()).hexdigest(),
        duration.name: hashlib.sha256(duration.read_bytes()).hexdigest(),
    }
    for path, raw in before.items():
        assert (root / path).read_bytes() == raw
    for path in (shared, duration, sampling):
        assert (
            path.with_name(path.name + ".sha256").read_text()
            == f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
        )


def test_archive_refuses_overwrite(command, tmp_path):
    root = archive_fixture(tmp_path)
    path = command.archive(root, "shared")
    original = path.read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        command.archive(root, "shared")
    assert path.read_bytes() == original


def test_archive_rejects_changed_dependency(command, tmp_path):
    root = archive_fixture(tmp_path)
    path = command.archive(root, "shared")
    with path.open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="checksum changed"):
        command.archive(root, "duration")
    assert not (root / "archives" / "run-001-duration.tar.gz").exists()


def test_archive_refuses_symlinks_and_missing_partitions(command, tmp_path):
    root = archive_fixture(tmp_path)
    (root / "inputs" / "link").symlink_to(root / "inputs-call.json")
    with pytest.raises(ValueError, match="regular files"):
        command.archive(root, "shared")
    (root / "inputs" / "link").unlink()
    (root / "technical-plots" / "record.json").unlink()
    (root / "technical-plots").rmdir()
    with pytest.raises(ValueError, match="Missing archive input"):
        command.archive(root, "shared")


def simulated_shell(tmp_path, *, fail=None, existing=False):
    """Exercise the real Bash orchestration with explicitly fake scientific tools."""
    project = tmp_path / "project"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    shutil.copyfile(
        ROOT / "scripts/run_noise_followup_manjaro.sh",
        scripts / "run_noise_followup_manjaro.sh",
    )
    for name in ("run_noise_followup.py", "check_noise_followup.py"):
        (scripts / name).touch()
    (project / ".venv/bin").mkdir(parents=True)
    (project / ".venv/bin/python").touch()
    binaries = tmp_path / "bin"
    binaries.mkdir()
    (binaries / "git").write_text(
        "#!/bin/sh\nif [ \"$1\" = rev-parse ]; then printf '%040d\\n' 1; fi\n"
    )
    (binaries / "systemd-inhibit").write_text(
        '#!/bin/sh\nprintf "INHIBIT\\n" >> "$TASK_TEST_LOG"\n'
        'while [ "$1" != bash ]; do shift; done\nexec "$@"\n'
    )
    fake_uv = r"""
import importlib.util
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
assert args[:4] == ['run', '--locked', '--no-sync', 'python']
args = args[4:]
with open(os.environ['TASK_TEST_LOG'], 'a') as stream:
    stream.write(json.dumps(args) + '\n')
if args[0] == '-':
    os.execv(os.environ['TASK_TEST_PYTHON'], [os.environ['TASK_TEST_PYTHON'], *args])
script = Path(args.pop(0)).name
action = 'technical' if script == 'check_noise_followup.py' else args.pop(0)
if action == os.environ.get('TASK_TEST_FAIL'):
    raise SystemExit(31)
def option(name):
    return Path(args[args.index(name)+1]) if name in args else None
if action == 'archive':
    spec = importlib.util.spec_from_file_location('real_archive', os.environ['TASK_TEST_ARCHIVE_SCRIPT'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.archive(option('--root'), str(option('--part')))
elif action in {'run', 'verify', 'plots'}:
    assert option('--inputs').is_dir()
    assert option('--technical').is_dir()
    assert option('--estimators').is_dir()
    if str(option('--block')) == 'sampling':
        assert option('--duration').is_dir()
        assert any(option('--duration').parent.joinpath('archives').glob('*-duration.tar.gz'))
    output = option('--export') if action in {'verify', 'plots'} else option('--output')
    output.mkdir()
    (output/'report.json').write_text(json.dumps({'action': action}))
elif action in {'prepare', 'estimator-check'} or (action == 'technical' and option('--output')):
    output = option('--output')
    output.mkdir()
    (output/'report.json').write_text(json.dumps({'action': action}))
    if action == 'prepare':
        output.with_name(output.name+'-call.json').write_text('{}\n')
elif action == 'technical-plots':
    output = option('--export')
    output.mkdir()
    (output/'report.json').write_text('{}\n')
elif action in {'verify-inputs', 'estimator-verify', 'verify-plots'}:
    pass
elif action == 'technical' and option('--verify'):
    assert option('--verify').is_dir()
else:
    raise AssertionError((action,args))
"""
    (binaries / "uv").write_text(f"#!{sys.executable}\n" + fake_uv)
    for path in binaries.iterdir():
        path.chmod(0o755)
    log = tmp_path / "calls.log"
    environment = dict(os.environ)
    environment.update(
        PATH=str(binaries) + os.pathsep + os.environ["PATH"],
        TASK_TEST_LOG=str(log),
        TASK_TEST_PYTHON=sys.executable,
        TASK_TEST_ARCHIVE_SCRIPT=str(ROOT / "scripts/run_noise_followup.py"),
    )
    if fail:
        environment["TASK_TEST_FAIL"] = fail
    if existing:
        (project / "results/run-001").mkdir(parents=True)
    result = subprocess.run(
        ["bash", "scripts/run_noise_followup_manjaro.sh", "results/run-001"],
        cwd=project,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    entries = log.read_text().splitlines() if log.exists() else []
    return result, project, entries


def test_complete_shell_sequence_uses_inhibitor_and_archives_before_sampling(tmp_path):
    result, project, entries = simulated_shell(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert entries[0] == "INHIBIT"
    scientific = [
        json.loads(line) for line in entries[1:] if json.loads(line)[0] != "-"
    ]
    runs = [
        row
        for row in scientific
        if row[0].endswith("run_noise_followup.py") and row[1] == "run"
    ]
    assert len(runs) == 2
    assert [row[row.index("--block") + 1] for row in runs] == ["duration", "sampling"]
    root = project / "results/run-001"
    assert len(list((root / "archives").glob("*.tar.gz"))) == 3
    assert (
        json.loads((root / "workflow_state.json").read_text())["status"] == "completed"
    )


def test_shell_failure_stops_before_scientific_search_and_keeps_files(tmp_path):
    result, project, entries = simulated_shell(tmp_path, fail="estimator-verify")
    assert result.returncode != 0
    assert "Abbruch" in result.stderr
    assert (project / "results/run-001/technical/report.json").is_file()
    assert not (project / "results/run-001/inputs").exists()
    assert not any('"run"' in line for line in entries)
    state = json.loads((project / "results/run-001/workflow_state.json").read_text())
    assert state["status"] == "aborted"


def test_shell_existing_run_is_never_overwritten(tmp_path):
    result, project, entries = simulated_shell(tmp_path, existing=True)
    assert result.returncode != 0
    assert "bereits vorhanden" in result.stderr
    assert list((project / "results/run-001").iterdir()) == []
    assert entries == ["INHIBIT"]
