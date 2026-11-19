"""Render the verified bd42634 study with a separately bound plotting correction."""

import argparse
import hashlib
import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
EXECUTION_COMMIT = "bd42634b888c2dbaa5a92726b9a1f9851c766a48"
RENDERER = "src/ringdown_sr/noise_background_plots.py"
LAUNCHER = "scripts/recover_noise_background_plots.py"
MODULE = "ringdown_sr._recovery_noise_background_plots"


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def _directory(path):
    path = Path(path).absolute()
    if path != path.resolve() or not path.is_dir():
        raise ValueError("Expected an existing checkout without symlinks.")
    return path


def _clean_commit(root, expected=None):
    if _git(root, "status", "--porcelain", "--untracked-files=all").strip():
        raise ValueError("Recovery requires clean, committed checkouts.")
    commit = _git(root, "rev-parse", "HEAD").decode().strip()
    if expected is not None and commit != expected:
        raise ValueError("Recovery checkout changed or has the wrong commit.")
    return commit


class RendererBinding:
    """Hold the exact new code while the original verifier guards its own code."""

    def __init__(self, root):
        self.root = _directory(root)
        self.commit = _clean_commit(self.root)
        self.files = {}
        for name in (LAUNCHER, RENDERER):
            path = self.root / name
            if path != path.resolve() or not path.is_file():
                raise ValueError("Recovery sources must be regular committed files.")
            raw = path.read_bytes()
            if raw != _git(self.root, "show", f"{self.commit}:{name}"):
                raise ValueError("Recovery source differs from its Git commit.")
            self.files[name] = raw
        self.check()

    def check(self):
        _clean_commit(self.root, self.commit)
        for name, raw in self.files.items():
            path = self.root / name
            if path != path.resolve() or path.read_bytes() != raw:
                raise ValueError("Recovery source changed after loading.")

    def bind(self, consumed):
        self.check()
        for name, raw in self.files.items():
            consumed.add(self.root / name, raw)
        consumed.callbacks.append(self.check)
        return {
            "software_commit": self.commit,
            "source_sha256": {
                name: hashlib.sha256(raw).hexdigest()
                for name, raw in sorted(self.files.items())
            },
            "mode": "separate_renderer_with_unchanged_execution_verifier",
            "execution_commit": EXECUTION_COMMIT,
        }


def _check_package_origins(execution):
    package = execution / "src/ringdown_sr"
    for name, module in tuple(sys.modules.items()):
        if name != "ringdown_sr" and not name.startswith("ringdown_sr."):
            continue
        if name == MODULE:
            continue
        source = getattr(module, "__file__", None)
        if source is None or not Path(source).resolve().is_relative_to(package):
            raise ValueError(
                "Recovery imported a dependency outside the execution checkout."
            )


def _load_renderer(execution):
    execution = _directory(execution)
    _clean_commit(execution, EXECUTION_COMMIT)
    if execution == _directory(ROOT):
        raise ValueError("Use separate execution and rendering checkouts.")
    if any(
        name == "ringdown_sr" or name.startswith("ringdown_sr.") for name in sys.modules
    ):
        raise ValueError("Start recovery in a fresh Python process.")
    binding = RendererBinding(ROOT)
    sys.path.insert(0, str(execution / "src"))
    importlib.import_module("ringdown_sr")
    _check_package_origins(execution)
    path = ROOT / RENDERER
    spec = importlib.util.spec_from_file_location(MODULE, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE] = module
    # Execute precisely the captured Git bytes, never a cached bytecode file.
    exec(compile(binding.files[RENDERER], str(path), "exec"), module.__dict__)  # noqa: S102 -- Execute only the captured, committed renderer.
    _check_package_origins(execution)
    binding.check()

    def bind(consumed):
        def check_execution():
            _clean_commit(execution, EXECUTION_COMMIT)
            _check_package_origins(execution)

        check_execution()
        consumed.callbacks.append(check_execution)
        return binding.bind(consumed)

    return module, bind


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-checkout", required=True)
    parser.add_argument("--inputs", required=True)
    parser.add_argument("--technical", required=True)
    parser.add_argument("--series", required=True)
    parser.add_argument("--export", required=True)
    args = parser.parse_args()
    execution = _directory(args.execution_checkout)
    if Path(sys.prefix).resolve() != (execution / ".venv").resolve():
        raise ValueError(
            "Run recovery with the unchanged execution checkout's Python environment."
        )
    renderer, binding = _load_renderer(execution)
    report = renderer.export(
        args.inputs,
        args.technical,
        args.series,
        args.export,
        _renderer_binding=binding,
    )
    verified = renderer.verify_export(args.export)
    if json.dumps(verified, sort_keys=True) != json.dumps(report, sort_keys=True):
        raise ValueError("Saved recovery export differs from its completed report.")
    print(
        "All 130 original outputs exported and checked; no fits or searches executed."
    )


if __name__ == "__main__":
    main()
