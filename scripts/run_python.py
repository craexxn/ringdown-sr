"""Run Python with the project's locked Julia environment."""

import json
import os
import platform
import subprocess
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path

from filelock import FileLock, Timeout
from juliapkg.compat import Compat
from juliapkg.find_julia import find_julia

ROOT = Path(__file__).resolve().parents[1]
LOCK_TIMEOUT_SECONDS = 30
INSTALL_TIMEOUT_SECONDS = 600


class StartupError(RuntimeError):
    """The pinned runtime could not be prepared safely."""


def check_pins(root: Path) -> str:
    expected_python = (root / ".python-version").read_text().strip()
    if platform.python_version() != expected_python:
        raise StartupError(f"Run this project with Python {expected_python}.")
    project = root / "julia"
    with (project / "Manifest.toml").open("rb") as file:
        manifest = tomllib.load(file)
    expected = manifest["julia_version"]
    pin_path = root / "src" / "ringdown_sr" / "juliapkg.json"
    pin = json.loads(pin_path.read_text(encoding="utf-8"))
    if pin.get("julia") != f"={expected}":
        raise StartupError("Julia pin and manifest disagree.")
    pythoncall = manifest["deps"]["PythonCall"][0]["version"]
    if version("juliacall") != pythoncall:
        raise StartupError("JuliaCall and PythonCall versions must match.")
    return expected


def runtime_environment(project: Path, julia: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        PYTHON_JULIACALL_EXE=julia,
        PYTHON_JULIACALL_PROJECT=str(project),
        PYTHON_JULIACALL_STARTUP_FILE="no",
        JULIA_PYTHONCALL_EXE=sys.executable,
        JULIA_CONDAPKG_BACKEND="Null",
        JULIA_PKG_PRECOMPILE_AUTO="0",
    )
    return environment


def prepare_runtime(root: Path) -> dict[str, str]:
    expected = check_pins(root)
    project = root / "julia"
    prefix = Path(sys.prefix)
    lock_path = prefix / ".ringdown-sr-julia.lock"
    print("Preparing the pinned Julia runtime...", file=sys.stderr, flush=True)
    try:
        # Only installation is serialized; the actual Python run is outside the lock.
        with FileLock(lock_path, timeout=LOCK_TIMEOUT_SECONDS, fallback_to_soft=False):
            # Locate/install Julia only. juliapkg.executable() would also resolve
            # another Julia package environment and precompile it independently.
            julia, actual = find_julia(
                compat=Compat.parse(f"={expected}"),
                prefix=str(prefix / "julia_env" / "pyjuliapkg" / "install"),
                install=True,
                upgrade=False,
            )
            if str(actual) != expected:
                raise StartupError(f"Expected Julia {expected}, found {actual}.")
            environment = runtime_environment(project, julia)
            snapshots = {
                path: path.read_bytes()
                for path in (project / "Project.toml", project / "Manifest.toml")
            }
            subprocess.run(
                [
                    julia,
                    "--startup-file=no",
                    f"--project={project}",
                    "-e",
                    (
                        "using Pkg; Pkg.instantiate(; allow_autoprecomp=false, "
                        "julia_version_strict=true)"
                    ),
                ],
                check=True,
                env=environment,
                timeout=INSTALL_TIMEOUT_SECONDS,
            )
            for path, original in snapshots.items():
                if path.read_bytes() != original:
                    raise StartupError(
                        f"Julia changed {path.name}; inspect the Git diff before retrying."
                    )
    except Timeout as error:
        raise StartupError(
            f"Another launcher is preparing Julia ({lock_path}). "
            f"The {LOCK_TIMEOUT_SECONDS:g} s lock wait expired; retry after it finishes. "
            "Do not delete an active lock."
        ) from error
    except subprocess.TimeoutExpired as error:
        raise StartupError(
            f"Julia package installation exceeded {INSTALL_TIMEOUT_SECONDS:g} s. "
            "Check the installation output and network, then retry."
        ) from error
    return environment


def main(arguments: list[str] | None = None) -> int:
    environment = prepare_runtime(ROOT)
    arguments = sys.argv[1:] if arguments is None else arguments
    return subprocess.call([sys.executable, *arguments], env=environment)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StartupError as error:
        print(f"Julia startup failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
