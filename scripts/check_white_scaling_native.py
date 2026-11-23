"""Check scaling arithmetic and 300/5 observer neutrality on technical inputs."""

import math
import os

from ringdown_sr.symbolic import ROOT


def main():
    if os.environ.get("PYTHON_JULIACALL_PROJECT") != str(ROOT / "julia"):
        raise RuntimeError("Use scripts/run_python.py.")
    import pysr
    from juliacall import Main as jl

    if (
        pysr.__version__,
        str(jl.VERSION),
        str(jl.seval("Base.pkgversion(SymbolicRegression)")),
    ) != ("2.6.0", "1.13.1", "2.5.1"):
        raise ValueError("Unexpected pinned runtime.")
    jl.include(str(ROOT / "julia/test/white_loss_scaling.jl"))
    records = jl.WhiteLossScalingChecks.REPLAY_CASES
    if len(records) != 9:
        raise ValueError("Missing native arithmetic references.")
    for record in records:
        residual = [
            float(y) - float(p)
            for y, p in zip(record.observed, record.prediction, strict=True)
        ]
        expected = math.fsum(x * x for x in residual) / len(residual)
        if str(record.arm) != "ordinary":
            expected /= float(record.sigma) ** 2
        if not math.isclose(float(record.loss), expected, rel_tol=32 * 2**-52):
            raise ValueError("Independent arithmetic reference disagrees.")
    print("White scaling native arithmetic, guards and observer checks passed.")


if __name__ == "__main__":
    main()
