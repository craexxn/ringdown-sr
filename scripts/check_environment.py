"""Check imports and the locked Python/Julia environment."""

import importlib
import os
import platform
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    project = root / "julia"
    expected_python = (root / ".python-version").read_text().strip()
    actual_python = platform.python_version()
    if actual_python != expected_python:
        raise SystemExit(f"Expected Python {expected_python}, found {actual_python}.")
    print("Python:", actual_python)

    if os.environ.get("PYTHON_JULIACALL_PROJECT") != str(project):
        raise SystemExit("Run this check through scripts/run_python.py.")
    if os.environ.get("JULIA_CONDAPKG_BACKEND") != "Null":
        raise SystemExit("The project requires the Null CondaPkg backend.")

    for name in ("numpy", "scipy", "matplotlib", "pandas", "sympy"):
        importlib.import_module(name)
        print(f"{name}: {version(name)}")

    import pysr
    from juliacall import Main as jl

    with (project / "Manifest.toml").open("rb") as file:
        manifest = tomllib.load(file)

    active = Path(str(jl.seval("Base.active_project()"))).resolve()
    if active != project / "Project.toml":
        raise SystemExit(f"Unexpected Julia project: {active}")

    actual_julia = str(jl.seval("string(VERSION)"))
    if actual_julia != manifest["julia_version"]:
        raise SystemExit(f"Unexpected Julia version: {actual_julia}")
    print("PySR:", pysr.__version__)
    print("Julia:", actual_julia)

    jl.seval("using SymbolicRegression, PythonCall")
    for name in ("SymbolicRegression", "PythonCall"):
        actual = str(jl.seval(f"string(Base.pkgversion({name}))"))
        expected = manifest["deps"][name][0]["version"]
        if actual != expected:
            raise SystemExit(f"Expected {name} {expected}, found {actual}.")
        print(f"{name}: {actual}")

    embedded_python = str(
        jl.seval('PythonCall.pyconvert(String, PythonCall.pyimport("sys").executable)')
    )
    if Path(embedded_python) != Path(sys.executable):
        raise SystemExit(f"PythonCall uses a different Python: {embedded_python}")
    if jl.seval("isdefined(PythonCall.C, :CondaPkg)"):
        backend = str(jl.seval("PythonCall.C.CondaPkg.backend()"))
        if backend != "Null":
            raise SystemExit(f"Unexpected CondaPkg backend: {backend}")
    if not jl.seval(
        "Base.get_extension(SymbolicRegression, :SymbolicRegressionPythonCallExt) !== nothing"
    ):
        raise SystemExit("The SymbolicRegression/PythonCall extension did not load.")
    print("PythonCall interpreter:", embedded_python)
    print("CondaPkg policy: Null; PythonCall extension loaded.")

    if jl.seval("1 + 1") != 2:
        raise SystemExit("Julia arithmetic check failed.")
    print("Julia project:", active)
    print("Technical environment check passed.")


if __name__ == "__main__":
    main()
