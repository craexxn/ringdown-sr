"""Apply the existing fail-closed driver contracts to every local budget profile."""

import json

import pytest
from test_local_optimizer import NATIVE_SEEDS, option_fixture
from test_noiseless_control import (
    BACKEND_SEEDS,
    fake_runtime,  # noqa: F401 -- Shared non-search fixture.
)

from ringdown_sr import local_optimizer as control
from ringdown_sr.pilot import _sha256

DRIVER = control.load_module(
    control.ROOT / "scripts/run_local_optimizer.py", "local_factory"
).load_driver()
CONTRACTS = control.load_module(
    control.ROOT / "tests/test_search_duration_driver.py", "local_lifecycle_contracts"
)
CONTRACTS.control = control
CONTRACTS.DRIVER = DRIVER
CONTRACTS.option_fixture = option_fixture


@pytest.fixture
def runtime(request, monkeypatch, tmp_path):
    for seed, native in NATIVE_SEEDS.items():
        monkeypatch.setitem(BACKEND_SEEDS, seed, native)
    return CONTRACTS.runtime.__wrapped__(request, monkeypatch, tmp_path)


# Exercise the same real publication, timeout, source-consumption and numerical
# evidence failure paths with the new driver, profile matrix and native module.
for _name in (
    "test_parent_recomputes_unselected_prediction_evidence",
    "test_actual_reference_work_is_interrupted_by_parent_deadline",
    "test_rehashed_candidate_evidence_is_independently_checked",
    "test_consistently_rehashed_wrong_actual_budget_or_worker_fails",
    "test_real_timer_interrupts_parent_verification_and_restores_handler",
    "test_preflight_rejects_incomplete_or_wrong_profiles_before_search",
    "test_partial_series_retained_without_retry_or_subgroup_release",
    "test_late_consumed_cell_mutation_revokes_entire_comparison",
    "test_final_publication_failure_revokes_even_after_rename",
):
    globals()[_name] = getattr(CONTRACTS, _name)


def test_twenty_cells_preserve_training_roles_fronts_selection_and_configuration(
    runtime, tmp_path
):
    output = tmp_path / "full"
    result = DRIVER.run(runtime.archive, output, label="fixture")
    assert result["status"] == "completed" and result["final_verification"] == "passed"
    assert len(runtime.calls) == 20 and len(result["pair_differences"]) == 25
    config = result["configuration"]
    assert config["optimizer_iterations"] == [100, 300]
    assert config["optimizer_nrestarts"] == [2, 5]
    assert config["grammar"] == "unrestricted" and config["niterations"] == 200
    assert config["should_simplify"] is False
    for cell, (times, observed, budget, _) in zip(
        result["cells"], runtime.calls, strict=True
    ):
        assert len(times) == len(observed) == 128
        assert (
            budget.niterations
            == cell["diagnostics"]["search_invocation"]["niterations"]
            == 200
        )
        assert cell["diagnostics"]["selected_index"] == 0
        assert [c["source_index"] for c in cell["diagnostics"]["candidates"]] == [0, 1]
    for name, digest in json.loads((output / "checksums.json").read_bytes()).items():
        assert _sha256((output / name).read_bytes()) == digest


@pytest.mark.parametrize("number", [1, 3])
@pytest.mark.parametrize(
    "fault",
    ["iterations", "restarts", "snapshot", "python_iterations", "python_restarts"],
)
def test_wrong_local_fields_in_first_or_later_worker_are_rejected(
    runtime, tmp_path, number, fault
):
    def alter(index, directory, docs):
        if index != number:
            return
        if fault.startswith("python_"):
            docs["pysr_parameters.json"][
                "optimizer_"
                + ("iterations" if fault.endswith("iterations") else "nrestarts")
            ] = 99
        elif fault == "snapshot":
            docs["verification.json"]["optimizer_settings"]["iterations"] = "99"
        else:
            for record in (
                docs["backend_options.json"],
                docs["verification.json"]["backend_options"],
            ):
                for field in record:
                    if field["name"] == (
                        "optimizer_options"
                        if fault == "iterations"
                        else "optimizer_nrestarts"
                    ):
                        field["value"] = (
                            "Options(iterations = 99,)"
                            if fault == "iterations"
                            else "99"
                        )

    runtime.alter = alter
    output = tmp_path / "wrong-profile"
    with pytest.raises(ValueError):
        DRIVER.run(runtime.archive, output, label="fixture")
    assert len(runtime.calls) == number
    CONTRACTS.assert_locked(output)
