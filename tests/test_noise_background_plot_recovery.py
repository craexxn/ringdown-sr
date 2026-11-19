"""Keep a corrected renderer separate from the original scientific verifier."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from test_noise_background_plots import _tiny_render
from test_noise_background_plots import (
    artifacts as artifacts,  # noqa: PLC0414 -- Re-export the shared pytest fixture.
)

from ringdown_sr import assessment_publication as publication
from ringdown_sr import noise_background_plots as plots

SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts/recover_noise_background_plots.py"
)
SPEC = importlib.util.spec_from_file_location("recovery_launcher", SCRIPT)
recovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recovery)


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args]).decode().strip()


def _commit(root):
    _git(root, "add", ".")
    _git(
        root,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "Fixture",
    )
    return _git(root, "rev-parse", "HEAD")


@pytest.fixture
def renderer_checkout(tmp_path):
    root = tmp_path / "renderer-checkout"
    root.mkdir()
    _git(root, "init", "-q")
    (root / ".gitignore").write_text("__pycache__/\n")
    for name, raw in {
        recovery.LAUNCHER: SCRIPT.read_bytes(),
        recovery.RENDERER: b"from . import dependency\nvalue = dependency.VALUE\n",
    }.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    _commit(root)
    return root


def test_recovery_loads_new_renderer_bytes_with_only_original_package_dependencies(
    renderer_checkout, tmp_path
):
    execution = tmp_path / "execution-checkout"
    package = execution / "src/ringdown_sr"
    package.mkdir(parents=True)
    _git(execution, "init", "-q")
    (execution / ".gitignore").write_text("__pycache__/\n")
    (package / "__init__.py").write_text("")
    (package / "dependency.py").write_text("VALUE = 'original verifier dependency'\n")
    (package / "noise_background_plots.py").write_text(
        "raise RuntimeError('old renderer must not execute')\n"
    )
    commit = _commit(execution)
    # Deliberately put an incompatible newer package first in PYTHONPATH.
    (renderer_checkout / "src/ringdown_sr/dependency.py").write_text(
        "VALUE = 'wrong new dependency'\n"
    )
    _commit(renderer_checkout)
    driver = """
import importlib.util, json, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('launcher', sys.argv[1])
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
launcher.EXECUTION_COMMIT = sys.argv[3]
module, binding = launcher._load_renderer(Path(sys.argv[2]))
print(json.dumps({'value': module.value, 'module': module.__name__, 'old_plot_loaded': 'ringdown_sr.noise_background_plots' in sys.modules}))
"""
    import os

    result = subprocess.check_output(
        [
            sys.executable,
            "-c",
            driver,
            str(renderer_checkout / recovery.LAUNCHER),
            str(execution),
            commit,
        ],
        env={**os.environ, "PYTHONPATH": str(renderer_checkout / "src")},
        cwd=renderer_checkout,
        text=True,
    )
    assert json.loads(result) == {
        "value": "original verifier dependency",
        "module": recovery.MODULE,
        "old_plot_loaded": False,
    }
    assert _git(execution, "status", "--porcelain") == ""


@pytest.mark.parametrize("change", ["source", "head", "untracked", "symlink"])
def test_renderer_binding_rejects_changed_code_or_checkout(renderer_checkout, change):
    binding = recovery.RendererBinding(renderer_checkout)
    source = renderer_checkout / recovery.RENDERER
    if change == "source":
        source.write_text("changed = True\n")
    elif change == "head":
        _git(
            renderer_checkout,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--allow-empty",
            "-qm",
            "Changed HEAD",
        )
    elif change == "untracked":
        (renderer_checkout / "unexpected.py").write_text("pass\n")
    else:
        target = renderer_checkout.parent / "moved.py"
        source.rename(target)
        source.symlink_to(target)
    with pytest.raises(ValueError):
        binding.check()


def test_historical_rendering_provenance_is_bound_to_all_130_outputs(
    artifacts, monkeypatch, renderer_checkout
):
    _tiny_render(monkeypatch)
    binding = recovery.RendererBinding(renderer_checkout)
    report = plots.export(
        artifacts.preparation,
        artifacts.technical,
        artifacts.series,
        artifacts.output,
        _renderer_binding=binding.bind,
    )
    rendering = report["source"]["renderer_software"]
    assert rendering["software_commit"] == _git(renderer_checkout, "rev-parse", "HEAD")
    assert set(rendering["source_sha256"]) == {recovery.LAUNCHER, recovery.RENDERER}
    assert report["source"]["execution_software"] == artifacts.report["software"]
    assert (
        report["source"]["verification_software"]
        == artifacts.prepared.manifest["software"]
    )
    assert artifacts.calls == ["full_read_only_verify"]
    for stem in report["outputs"]:
        data = json.loads((artifacts.output / f"{stem}.json").read_bytes())
        assert data["series"]["renderer_software"] == rendering
    assert plots.verify_export(artifacts.output) == report


@pytest.mark.parametrize("late", ["during_render", "after_unlock", "after_transaction"])
def test_changed_renderer_revokes_export_including_after_handler_teardown(
    artifacts, monkeypatch, renderer_checkout, late
):
    _tiny_render(monkeypatch)
    binding = recovery.RendererBinding(renderer_checkout)
    target = renderer_checkout / recovery.RENDERER
    if late == "during_render":
        original = plots._curve_plot

        def changed(*args):
            target.write_text("changed = True\n")
            return original(*args)

        monkeypatch.setattr(plots, "_curve_plot", changed)
    elif late == "after_unlock":
        original = Path.unlink

        def changed(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if path == artifacts.output / publication.LOCK:
                _git(
                    renderer_checkout,
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.invalid",
                    "commit",
                    "--allow-empty",
                    "-qm",
                    "Changed HEAD",
                )
            return result

        monkeypatch.setattr(Path, "unlink", changed)
    else:
        original = publication.export_transaction

        def changed(*args, **kwargs):
            report = original(*args, **kwargs)
            target.write_text("changed = True\n")
            return report

        monkeypatch.setattr(publication, "export_transaction", changed)
    with pytest.raises(ValueError):
        plots.export(
            artifacts.preparation,
            artifacts.technical,
            artifacts.series,
            artifacts.output,
            _renderer_binding=binding.bind,
        )
    assert (artifacts.output / publication.LOCK).is_file()
    report = json.loads((artifacts.output / publication.REPORT).read_bytes())
    assert report["status"] != "completed"
    assert not (artifacts.output / publication.MANIFEST).exists()


def test_existing_failed_output_is_preserved(artifacts, monkeypatch, renderer_checkout):
    _tiny_render(monkeypatch)
    artifacts.output.mkdir()
    marker = artifacts.output / "original-failure.json"
    marker.write_bytes(b'{"status": "aborted"}\n')
    binding = recovery.RendererBinding(renderer_checkout)
    with pytest.raises(ValueError, match="new assessment directory"):
        plots.export(
            artifacts.preparation,
            artifacts.technical,
            artifacts.series,
            artifacts.output,
            _renderer_binding=binding.bind,
        )
    assert marker.read_bytes() == b'{"status": "aborted"}\n'
    assert set(artifacts.output.iterdir()) == {marker}
    assert artifacts.calls == []


def test_execution_checkout_requires_the_pinned_commit(renderer_checkout):
    with pytest.raises(ValueError, match="wrong commit"):
        recovery._load_renderer(renderer_checkout)


def test_launcher_refuses_a_different_python_environment(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--execution-checkout",
            str(tmp_path),
            "--inputs",
            "inputs",
            "--technical",
            "technical",
            "--series",
            "series",
            "--export",
            "plots",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "unchanged execution checkout's Python environment" in result.stderr
