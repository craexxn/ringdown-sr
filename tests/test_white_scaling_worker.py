"""Separate scaling requests and scalar semantics must remain fail closed."""

import copy
import time
from dataclasses import asdict

import numpy as np
import pytest

from ringdown_sr import symbolic
from ringdown_sr import white_scaling_worker as scaling
from ringdown_sr.losses import mean_squared_error
from ringdown_sr.pilot import _write_json
from ringdown_sr.prediction_reference import verify_prediction


def request(arm="ordinary", technical=False):
    sigma = 0.25
    return {
        "format": scaling.FORMAT,
        "profile": scaling.PROFILE,
        "arm": arm,
        "sigma_hex": sigma.hex(),
        "scale_hex": (1.0 / sigma**2).hex(),
        "technical": technical,
        "budget": asdict(
            symbolic.SearchBudget(seed=73, niterations=2 if technical else 100)
        ),
    }


@pytest.mark.parametrize("arm", scaling.ARMS)
def test_only_objective_changes_the_free_search_options(arm):
    budget = scaling.checked_request(request(arm))
    actual = scaling.parameters(budget)
    expected = scaling.confirmed.parameters(budget)
    assert actual.pop("loss_function") == scaling.OBJECTIVE
    expected.pop("loss_function")
    assert actual == expected
    assert actual["maxsize"] == 20
    assert actual["optimizer_iterations"] == 300
    assert actual["optimizer_nrestarts"] == 5


@pytest.mark.parametrize(
    "field,value",
    [
        ("sigma_hex", "nan"),
        ("sigma_hex", "-0x1p-2"),
        ("scale_hex", "0x1p0"),
        ("technical", 1),
        ("format", scaling.symbolic.FORMAT),
        ("arm", "other"),
    ],
)
def test_request_rejects_unbound_or_ambiguous_scales(field, value):
    document = request()
    document[field] = value
    with pytest.raises(ValueError):
        scaling.checked_request(document)


@pytest.mark.parametrize(
    "field,value",
    [
        ("niterations", 1000),
        ("niterations", True),
        ("seed", 0),
        ("population_size", 64),
    ],
)
def test_request_rejects_budget_changes(field, value):
    document = request()
    document["budget"][field] = value
    with pytest.raises(ValueError):
        scaling.checked_request(document)


def test_technical_budget_cannot_be_disguised_as_scientific():
    document = request(technical=True)
    assert scaling.checked_request(document).niterations == 2
    document["technical"] = False
    with pytest.raises(ValueError):
        scaling.checked_request(document)


def test_preparation_binds_exact_diagonal_and_refuses_overwrite(tmp_path):
    path = tmp_path / "member"
    times = np.arange(8, dtype=float)
    observed = times + 1
    scaling.prepare_member(
        path,
        times,
        observed,
        arm="covariance",
        sigma=0.25,
        seed=73,
        technical=True,
        niterations=2,
    )
    document, arrays, manifest = scaling.verify_prepared(path)
    np.testing.assert_array_equal(arrays["covariance"], np.eye(8) / 16)
    assert document["scale_hex"] == (16.0).hex()
    with pytest.raises(FileExistsError):
        scaling.prepare_member(
            path, times, observed, arm="covariance", sigma=0.25, seed=73, technical=True
        )
    observed[0] = 90
    assert scaling.verify_prepared(path)[1]["observed"][0] == 1
    arrays["covariance"][0, 1] = arrays["covariance"][1, 0] = 1e-3
    np.savez(path / "inputs.npz", **arrays)
    # Even a recomputed transport hash cannot authorize a changed covariance.
    manifest["files"]["inputs.npz"] = scaling._sha256(
        (path / "inputs.npz").read_bytes()
    )
    _write_json(path / "prepared.json", manifest)
    with pytest.raises(ValueError, match="exactly"):
        scaling.verify_prepared(path)


def test_scaled_replay_keeps_base_mse_and_checks_exact_multiplication():
    times = np.arange(4, dtype=float)
    tree = {"kind": "constant", "value_hex": (1.0).hex()}
    prediction = np.ones(4)
    observed = np.array([0.0, 1.0, 2.0, 3.0])
    mse = mean_squared_error(observed - prediction)
    proof = verify_prediction(tree, times, prediction, prediction)
    document = request("scaled")
    args = [observed, prediction, prediction, 16 * mse, mse, 16 * mse, mse, None]
    evidence = scaling.loss_evidence(document, *args, prediction_check=proof)
    assert evidence["base_native_mse"] == mse
    assert evidence["raw_objective_loss"] == 16 * mse
    args[3] = float(np.nextafter(args[3], np.inf))
    with pytest.raises(ValueError, match="multiplication"):
        scaling.loss_evidence(document, *args, prediction_check=proof)


def test_wrong_scale_cannot_be_hidden_by_a_new_loss_proof():
    document = request("scaled")
    changed = copy.deepcopy(document)
    changed["scale_hex"] = (32.0).hex()
    with pytest.raises(ValueError):
        scaling.checked_request(changed)


def test_changed_plan_is_rejected_before_preparation(monkeypatch):
    monkeypatch.setattr(scaling, "PLAN_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="frozen"):
        scaling.source_hashes()


@pytest.mark.parametrize("arm", scaling.ARMS)
@pytest.mark.parametrize("amplitude", [1.0, 0.001])
@pytest.mark.parametrize("signs", [(1, 1, 1, 1), (1, -1, 0, -1)])
def test_zero_baseline_and_floor_are_independently_checked(arm, amplitude, signs):
    observed = np.array([1.0, 2.0, 3.0, 4.0]) * signs * amplitude
    document = request(arm)
    loss = mean_squared_error(observed)
    factor = None
    if arm != "ordinary":
        loss *= 16
    if arm == "covariance":
        factor = np.eye(4) * 0.25
    result = {
        "baseline_loss": loss,
        "zero_expression_loss": loss,
        "zero_expression_loss_status": "finite",
        "cost_normalization": max(loss, 0.01),
        "use_baseline": True,
    }
    evidence = scaling.verify_normalization(
        document, observed, result, native_factor=factor
    )
    assert evidence["floor_active"] is (loss < 0.01)
    for field, value in (
        ("baseline_loss", loss * 2),
        ("zero_expression_loss", loss * 2),
        ("cost_normalization", 7.0),
        ("use_baseline", False),
    ):
        with pytest.raises(ValueError):
            scaling.verify_normalization(
                document, observed, {**result, field: value}, native_factor=factor
            )
    changed_both = {
        **result,
        "baseline_loss": loss * 2,
        "zero_expression_loss": loss * 2,
        "cost_normalization": max(loss * 2, 0.01),
    }
    with pytest.raises(ValueError, match="independent"):
        scaling.verify_normalization(
            document, observed, changed_both, native_factor=factor
        )


@pytest.mark.parametrize("arm", scaling.ARMS)
@pytest.mark.parametrize("sign", [-1, 1])
@pytest.mark.parametrize("magnitude", [np.nextafter(0.0, 1.0), 1e-160])
def test_signed_subnormal_observations_or_squares_remain_outside_reduction_domain(
    arm, sign, magnitude
):
    observed = np.array([1.0, -2.0, sign * magnitude, 4.0])
    # The unsupported value must fail before a purported baseline is consumed.
    with pytest.raises(ValueError, match="normal Float64 domain"):
        scaling.verify_normalization(request(arm), observed, {})


def test_interrupted_worker_preserves_original_exception_and_known_costs(
    tmp_path, monkeypatch
):
    output = tmp_path / "interrupted"
    times = np.arange(8, dtype=float)
    scaling.prepare_member(
        output,
        times,
        1 + times,
        arm="ordinary",
        sigma=0.25,
        seed=73,
        technical=True,
        niterations=2,
    )
    error = KeyboardInterrupt("technical interruption")

    class Process:
        returncode = None

        def wait(self, *, timeout):
            raise error

    process = Process()
    monkeypatch.setattr(scaling.subprocess, "Popen", lambda *args, **kwargs: process)
    stopped = []

    def stop(child):
        stopped.append(child)
        child.returncode = -15

    monkeypatch.setattr(scaling.symbolic, "_stop_worker", stop)
    with pytest.raises(KeyboardInterrupt) as caught:
        scaling.run_member(output, deadline=time.monotonic() + 10)
    assert caught.value is error
    assert stopped == [process]
    outcome = scaling.confirmed.read(output, "outcome.json")
    assert outcome["status"] == "aborted"
    assert outcome["error"] == "KeyboardInterrupt: technical interruption"
    assert outcome["returncode"] == -15
    assert outcome["worker_wall_seconds"] >= 0
    assert outcome["cpu_measurement_complete"] is False
    assert outcome["cpu_user_seconds"] is outcome["cpu_system_seconds"] is None
    assert scaling.confirmed.read(
        output, "member_checksums.json"
    ) == scaling.confirmed._inventory(output)
    with pytest.raises(ValueError, match="did not complete"):
        scaling.verify_member(output)


def test_failed_process_creation_is_archived_and_reraised(tmp_path, monkeypatch):
    output = tmp_path / "startup-failure"
    times = np.arange(8, dtype=float)
    scaling.prepare_member(
        output,
        times,
        1 + times,
        arm="ordinary",
        sigma=0.25,
        seed=73,
        technical=True,
        niterations=2,
    )
    error = OSError("technical startup failure")

    def popen(*args, **kwargs):
        raise error

    monkeypatch.setattr(scaling.subprocess, "Popen", popen)
    with pytest.raises(OSError) as caught:
        scaling.run_member(output, deadline=time.monotonic() + 10)
    assert caught.value is error
    outcome = scaling.confirmed.read(output, "outcome.json")
    assert outcome["status"] == "aborted"
    assert outcome["returncode"] is None
    assert outcome["cpu_measurement_complete"] is False
    assert outcome["cpu_user_seconds"] is outcome["cpu_system_seconds"] is None
    assert scaling.confirmed.read(
        output, "member_checksums.json"
    ) == scaling.confirmed._inventory(output)
