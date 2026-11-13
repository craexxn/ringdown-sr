"""Exercise two tiny signals and twelve workers, never restart-budget-confirmation science."""

import argparse
from pathlib import Path

from ringdown_sr.restart_budget_confirmation import run, verify
from ringdown_sr.restart_budget_confirmation_profile import names

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    roots = []
    for name in names(technical=True):
        root = args.output.with_name(args.output.name + "-" + name)
        run(root, name, technical=True)
        verify([root], root.with_name(root.name + "-verification"))
        roots.append(root)
    report = verify(roots, args.output, complete=True)
    if (
        report["verified_cells"] != 12
        or report["algorithm_outputs"] != 4
        or report["transition_criterion_met"] is not None
        or report["L_control_criterion_met"] is not None
    ):
        raise ValueError("Technical restart-budget-confirmation scope changed.")
    if any(
        cell["status"] != "completed"
        or cell["stop"] != "iteration_limit"
        or cell["completed_outer_rounds"] != cell["plan"]["niterations"]
        or not cell["costs"]["callback_calls_during_fit"]
        for section in report["sections"]
        for cell in section["cells"]
    ):
        raise ValueError("Every tiny worker must complete its actual iteration budget.")
    for comparison in report["comparisons"]:
        if (
            len(comparison["pairs"]) != 1
            or comparison["R_meets_signal_threshold"] is not None
            or comparison["L_meets_signal_threshold"] is not None
            or any(
                totals["uncertainty"] is not None
                for totals in comparison["totals"].values()
            )
        ):
            raise ValueError("Each technical signal needs exactly one package pair.")
        for arm, member_count in (("R", 4), ("L", 2)):
            output = comparison["pairs"][0]["outputs"][arm]
            if (
                len(output["members"]) != member_count
                or output["status"] != "completed"
                or output["selected_cell"] not in output["members"]
                or any(value is None for value in output["costs"].values())
            ):
                raise ValueError(
                    "Every tiny package must retain its members and costs."
                )
    print(
        "Twelve tiny workers, both package arms and read-only series verification passed."
    )
