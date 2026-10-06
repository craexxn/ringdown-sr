"""Run Python with the project's locked Julia environment."""

import json
import os
import subprocess
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path

import juliapkg


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    project = root / "julia"
    with (project / "Manifest.toml").open("rb") as file:
        manifest = tomllib.load(file)
    expected = manifest["julia_version"]

    pin_path = root / "src" / "ringdown_sr" / "juliapkg.json"
    pin = json.loads(pin_path.read_text(encoding="utf-8"))
    if pin.get("julia") != f"={expected}":
        raise SystemExit("Julia pin and manifest disagree.")

    pythoncall = manifest["deps"]["PythonCall"][0]["version"]
    if version("juliacall") != pythoncall:
        raise SystemExit("JuliaCall and PythonCall versions must match.")

    julia = juliapkg.executable()
    actual = subprocess.check_output(
        [julia, "--startup-file=no", "-e", "print(VERSION)"], text=True
    ).strip()
    if actual != expected:
        raise SystemExit(f"Expected Julia {expected}, found {actual}.")

    subprocess.run(
        [
            julia,
            "--startup-file=no",
            f"--project={project}",
            "-e",
            "using Pkg; Pkg.instantiate()",
        ],
        check=True,
    )

    environment = os.environ.copy()
    environment["PYTHON_JULIACALL_EXE"] = julia
    environment["PYTHON_JULIACALL_PROJECT"] = str(project)
    environment["PYTHON_JULIACALL_STARTUP_FILE"] = "no"
    return subprocess.call([sys.executable, *sys.argv[1:]], env=environment)


if __name__ == "__main__":
    raise SystemExit(main())
