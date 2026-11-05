"""Exercise distinct signal inputs through the actual lifecycle and numerical gates."""

import json

import numpy as np
import pytest
from test_noiseless_control import BACKEND_SEEDS, fake_runtime  # noqa: F401
from test_transfer_check import NATIVE_SEEDS, option_fixture

from ringdown_sr import transfer_check as control
from ringdown_sr.pilot import _sha256

DRIVER = control.load_module(
    control.ROOT / "scripts/run_transfer_check.py", "transfer_factory"
).load_driver()
CONTRACTS = control.load_module(
    control.ROOT / "tests/test_search_duration_driver.py",
    "transfer_lifecycle_contracts",
)
CONTRACTS.control = control
CONTRACTS.DRIVER = DRIVER
CONTRACTS.option_fixture = option_fixture
CONTRACTS.frozen_data = lambda: control.read_inputs(control.ROOT / control.INPUT)[1]


@pytest.fixture
def runtime(request, monkeypatch, tmp_path):
    for seed, native in NATIVE_SEEDS.items():
        monkeypatch.setitem(BACKEND_SEEDS, seed, native)
    return CONTRACTS.runtime.__wrapped__(request, monkeypatch, tmp_path)


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


def test_all_eighteen_cells_consume_only_their_training_rows_and_preserve_selection(
    runtime, tmp_path
):
    output = tmp_path / "full"
    result = DRIVER.run(runtime.archive, output, label="fixture")
    assert result["status"] == "completed" and result["final_verification"] == "passed"
    assert len(runtime.calls) == 18 and len(result["pair_differences"]) == 15
    config = result["configuration"]
    assert (
        config["niterations"],
        config["optimizer_iterations"],
        config["optimizer_nrestarts"],
    ) == (500, 300, 5)
    assert (config["limit_seconds"], config["worker_limit_seconds"]) == (7200, 900)
    assert config["grammar"] == "unrestricted" and config["should_simplify"] is False
    assert config["truth"] == {s: control.reference_truth(s) for s in control.SIGNALS}
    _, roots = control.read_inputs(control.ROOT / control.INPUT)
    for cell, (times, observed, budget, directory) in zip(
        result["cells"], runtime.calls, strict=True
    ):
        expected = control.arrays_for_cell(roots, cell)
        assert len(times) == len(observed) == 128
        np.testing.assert_array_equal(times, expected["time_s"])
        np.testing.assert_array_equal(observed, expected["observed"])
        with np.load(directory / "inputs.npz", allow_pickle=False) as data:
            assert set(data.files) == {"time_s", "observed"}
            np.testing.assert_array_equal(data["observed"], expected["observed"])
        assert (
            budget.niterations
            == cell["diagnostics"]["search_invocation"]["niterations"]
            == 500
        )
        assert cell["diagnostics"]["selected_index"] == 0
        assert [c["source_index"] for c in cell["diagnostics"]["candidates"]] == [0, 1]
    for name, digest in json.loads((output / "checksums.json").read_bytes()).items():
        assert _sha256((output / name).read_bytes()) == digest
    with np.load(output / "training.npz", allow_pickle=False) as data:
        np.testing.assert_array_equal(data["observed"], roots["observed"])
    with np.load(output / "diagnostic.npz", allow_pickle=False) as data:
        np.testing.assert_array_equal(
            data["diagnostic_truth"], roots["diagnostic_truth"]
        )


@pytest.mark.parametrize("number", [1, 5])
@pytest.mark.parametrize(
    "fault", ["wrong_signal", "diagnostic_leak", "iterations", "restarts", "truth"]
)
def test_first_and_later_cell_data_or_profile_faults_fail_closed(
    runtime, tmp_path, number, fault
):
    def alter(index, directory, docs):
        if index != number:
            return
        if fault in ("wrong_signal", "diagnostic_leak", "truth"):
            with np.load(directory / "inputs.npz", allow_pickle=False) as bundle:
                arrays = {k: bundle[k] for k in bundle.files}
            if fault == "wrong_signal":
                _, root = control.read_inputs(control.ROOT / control.INPUT)
                arrays["observed"] = root["observed"][3]
            else:
                arrays[
                    "diagnostic_truth" if fault == "diagnostic_leak" else "signal_truth"
                ] = np.ones(889 if fault == "diagnostic_leak" else 4)
            np.savez(directory / "inputs.npz", **arrays)
            docs["manifest.json"]["inputs"]["inputs.npz"] = _sha256(
                (directory / "inputs.npz").read_bytes()
            )
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
                            "Options(iterations = 100,)"
                            if fault == "iterations"
                            else "2"
                        )

    runtime.alter = alter
    output = tmp_path / "wrong-cell"
    with pytest.raises(ValueError):
        DRIVER.run(runtime.archive, output, label="fixture")
    assert len(runtime.calls) == number
    CONTRACTS.assert_locked(output)


def test_parent_uses_case_specific_truth_after_original_selection(
    runtime, tmp_path, monkeypatch
):
    factory = control.load_module(
        control.ROOT / "scripts/run_transfer_check.py", "transfer_truth_spy"
    )
    original = factory.diagnose_candidate
    recorded = []

    def spy(candidate, index, selected, arrays, condition, **kwargs):
        recorded.append((kwargs["truth"], index, selected))
        return original(candidate, index, selected, arrays, condition, **kwargs)

    monkeypatch.setattr(factory, "diagnose_candidate", spy)
    monkeypatch.setattr(
        DRIVER, "diagnose_cell_candidate", factory.diagnose_cell_candidate
    )
    DRIVER.run(runtime.archive, tmp_path / "truth", label="fixture")
    assert recorded == [
        (control.reference_truth(c["signal"]), index, 0)
        for c in control.planned_cells()
        for index in (0, 1)
    ]
