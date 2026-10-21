"""Check launcher isolation, pins, failure handling and actual OS locking."""

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from filelock import FileLock, Timeout
from juliapkg.compat import Version


@pytest.fixture
def launcher(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / "scripts" / "run_python.py"
    spec = importlib.util.spec_from_file_location("project_python_launcher", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = tmp_path / "project with spaces"
    project = root / "julia"
    project.mkdir(parents=True)
    (root / ".python-version").write_text("3.12.14\n")
    (project / "Project.toml").write_text("[deps]\n")
    (project / "Manifest.toml").write_text(
        'julia_version="1.13.1"\n[deps]\nPythonCall=[{version="0.9.36"}]\n'
    )
    pin = root / "src" / "ringdown_sr" / "juliapkg.json"
    pin.parent.mkdir(parents=True)
    pin.write_text(json.dumps({"julia": "=1.13.1"}))
    prefix = tmp_path / "venv with spaces"
    prefix.mkdir()
    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module.sys, "prefix", str(prefix))
    monkeypatch.setattr(module.platform, "python_version", lambda: "3.12.14")
    monkeypatch.setattr(module, "version", lambda name: "0.9.36")
    monkeypatch.setattr(
        module, "find_julia", lambda **kwargs: ("/runtime with spaces/julia", "1.13.1")
    )
    return module


def test_exact_runtime_and_only_the_locked_project(launcher, monkeypatch):
    calls = []

    def find(**kwargs):
        assert Version.parse("1.13.1") in kwargs["compat"]
        assert Version.parse("1.13.2") not in kwargs["compat"]
        assert kwargs["install"] and not kwargs["upgrade"]
        assert Path(kwargs["prefix"]).is_relative_to(Path(sys.prefix))
        return "/runtime with spaces/julia", "1.13.1"

    monkeypatch.setattr(launcher, "find_julia", find)
    monkeypatch.setattr(
        launcher.subprocess, "run", lambda args, **kw: calls.append((args, kw))
    )
    environment = launcher.prepare_runtime(launcher.ROOT)
    assert len(calls) == 1
    args, options = calls[0]
    assert args[:2] == ["/runtime with spaces/julia", "--startup-file=no"]
    assert args[2] == f"--project={launcher.ROOT / 'julia'}"
    assert "allow_autoprecomp=false" in args[-1]
    assert "julia_version_strict=true" in args[-1]
    assert "Pkg.add" not in args[-1] and "Pkg.resolve" not in args[-1]
    assert options["check"] and options["timeout"] == 600
    assert options["env"] == environment


def test_environment_is_local_and_uses_the_current_python(launcher, monkeypatch):
    monkeypatch.setenv("JULIA_CONDAPKG_BACKEND", "Pixi")
    monkeypatch.setenv("JULIA_PYTHONCALL_EXE", "/another/python")
    environment = launcher.runtime_environment(launcher.ROOT / "julia", "/our/julia")
    assert environment["JULIA_CONDAPKG_BACKEND"] == "Null"
    assert environment["JULIA_PYTHONCALL_EXE"] == sys.executable
    assert environment["PYTHON_JULIACALL_EXE"] == "/our/julia"
    assert environment["PYTHON_JULIACALL_PROJECT"] == str(launcher.ROOT / "julia")
    assert environment["PYTHON_JULIACALL_STARTUP_FILE"] == "no"
    assert environment["JULIA_PKG_PRECOMPILE_AUTO"] == "0"
    assert os.environ["JULIA_CONDAPKG_BACKEND"] == "Pixi"
    assert os.environ["JULIA_PYTHONCALL_EXE"] == "/another/python"


@pytest.mark.parametrize("mismatch", ["python", "pin", "pythoncall", "julia"])
def test_pin_mismatches_prevent_installation_and_execution(
    launcher, monkeypatch, mismatch
):
    if mismatch == "python":
        monkeypatch.setattr(launcher.platform, "python_version", lambda: "3.13.0")
    elif mismatch == "pin":
        (launcher.ROOT / "src/ringdown_sr/juliapkg.json").write_text(
            '{"julia":"=1.13.0"}'
        )
    elif mismatch == "pythoncall":
        monkeypatch.setattr(launcher, "version", lambda name: "0.9.35")
    else:
        monkeypatch.setattr(launcher, "find_julia", lambda **kw: ("/julia", "1.13.2"))

    def unexpected(*args, **kwargs):
        pytest.fail("A mismatched runtime must not install packages or run user code.")

    monkeypatch.setattr(launcher.subprocess, "run", unexpected)
    monkeypatch.setattr(launcher.subprocess, "call", unexpected)
    with pytest.raises(launcher.StartupError):
        launcher.main(["-c", "raise RuntimeError('must not run')"])


@pytest.mark.parametrize("filename", ["Project.toml", "Manifest.toml"])
def test_changed_metadata_prevents_user_execution(launcher, monkeypatch, filename):
    path = launcher.ROOT / "julia" / filename

    def change_metadata(*args, **kwargs):
        path.write_text(path.read_text() + "# changed by package manager\n")

    monkeypatch.setattr(launcher.subprocess, "run", change_metadata)
    monkeypatch.setattr(
        launcher.subprocess, "call", lambda *a, **k: pytest.fail("User code ran")
    )
    with pytest.raises(launcher.StartupError, match="Julia changed"):
        launcher.main([])
    assert "changed by package manager" in path.read_text()


@pytest.mark.parametrize("failure", ["package_error", "timeout"])
def test_failed_installation_releases_lock_without_running_user_code(
    launcher, monkeypatch, failure
):
    error = (
        subprocess.CalledProcessError(1, ["julia"])
        if failure == "package_error"
        else subprocess.TimeoutExpired(["julia"], 600)
    )

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(launcher.subprocess, "run", fail)
    monkeypatch.setattr(
        launcher.subprocess, "call", lambda *a, **k: pytest.fail("User code ran")
    )
    expected = (
        subprocess.CalledProcessError
        if failure == "package_error"
        else launcher.StartupError
    )
    with pytest.raises(expected):
        launcher.main([])
    with FileLock(Path(sys.prefix) / ".ringdown-sr-julia.lock", timeout=0):
        pass


def test_lock_is_released_before_forwarding_arguments_and_exit_status(
    launcher, monkeypatch
):
    monkeypatch.setattr(launcher.subprocess, "run", lambda *a, **k: None)
    arguments = [
        "-c",
        "print('spaces; $literal `characters`')",
        "an argument with spaces",
    ]

    def child(args, **kwargs):
        assert args == [sys.executable, *arguments]
        assert kwargs["env"]["JULIA_CONDAPKG_BACKEND"] == "Null"
        with FileLock(Path(sys.prefix) / ".ringdown-sr-julia.lock", timeout=0):
            return 7

    monkeypatch.setattr(launcher.subprocess, "call", child)
    assert launcher.main(arguments) == 7


def test_another_process_keeps_its_lock_after_the_bounded_wait(launcher, monkeypatch):
    path = Path(sys.prefix) / ".ringdown-sr-julia.lock"
    code = (
        "import sys; from filelock import FileLock; "
        "lock=FileLock(sys.argv[1]); lock.acquire(); "
        "print('locked', flush=True); sys.stdin.read(); lock.release()"
    )
    child = subprocess.Popen(
        [sys.executable, "-u", "-c", code, str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout.readline().strip() == "locked"
        monkeypatch.setattr(launcher, "LOCK_TIMEOUT_SECONDS", 0.05)
        started = time.monotonic()
        with pytest.raises(launcher.StartupError, match="lock wait expired"):
            launcher.prepare_runtime(launcher.ROOT)
        assert time.monotonic() - started < 2
        assert child.poll() is None
        with pytest.raises(Timeout), FileLock(path, timeout=0):
            pass
    finally:
        child.stdin.close()
        child.wait(timeout=5)
        child.stdout.close()
