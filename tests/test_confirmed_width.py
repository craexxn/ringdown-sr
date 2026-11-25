"""Adversarial full-front withholding with an analytically zero wide expression."""

import csv
import math
import subprocess
import time
from types import SimpleNamespace

import numpy as np
import pytest

from ringdown_sr import confirmed_profile as profile
from ringdown_sr import prediction_reference as reference
from ringdown_sr import symbolic
from ringdown_sr.constant_diagnostic import backend_seed
from ringdown_sr.losses import CovarianceLoss
from ringdown_sr.pilot import _write_json

WIDE = "exp(1.0) - exp(1.0)"


@pytest.mark.parametrize("technical, iterations", [(True, 10), (False, 1000)])
def test_width_member_requires_new_format_and_pinned_n103_grid(
    tmp_path, technical, iterations
):
    times = np.arange(103) / 4096
    directory = tmp_path / "member"
    profile.prepare_main_width_member(
        directory, times, np.ones(103), seed=5, technical=technical
    )
    request, _, _ = profile.verify_prepared(directory)
    assert request["format"] == profile.MAIN_WIDTH_FORMAT
    assert request["budget"]["niterations"] == iterations
    with pytest.raises(ValueError, match="N103 grid"):
        profile.prepare_main_width_member(
            tmp_path / "wrong", times + 1, np.ones(103), seed=5
        )


def test_unbounded_or_contradicted_predictions_remain_hard():
    t = np.arange(3) / 4096
    zero = np.zeros_like(t)
    tree = profile.equation_tree(WIDE)
    with pytest.raises(reference.PredictionVerificationError):
        profile.verify_prediction(tree, t, zero, zero)
    wide = profile.width_prediction(tree, t, zero, zero)
    assert wide["status"] == "indeterminate"
    assert wide["membership"] == {"status": "not_attempted"}
    assert list(map(float.fromhex, wide["observed_python_hex"])) == zero.tolist()
    assert [a["reason"] for a in wide["attempts"]] == [profile.WIDTH_REASON] * 4
    with pytest.raises(ValueError, match="wide enclosure"):
        profile.width_prediction(tree, t, zero, [0, 1, 0])
    with pytest.raises(
        reference.PredictionVerificationError, match="possible_zero_denominator"
    ):
        profile.width_prediction(profile.equation_tree("1.0 / t"), t, zero, zero)
    with pytest.raises(
        reference.PredictionVerificationError, match="prediction_outside_reference"
    ):
        profile.width_prediction(profile.equation_tree("t"), t, t, t + 1)


def test_width_diagnostic_still_requires_both_weighted_losses_and_whitening():
    t = np.arange(3) / 4096
    y = np.ones(3)
    covariance = np.eye(3) * 4
    candidate = {
        "tree": profile.equation_tree(WIDE),
        "prediction": [0.0] * 3,
        "native_whitened_residual": [0.5] * 3,
        **dict.fromkeys(
            ("loss", "julia_reimport_loss", "table_loss", "python_loss"), 0.25
        ),
    }

    def replay():
        return profile._width_candidate_evidence(
            candidate,
            t,
            y,
            covariance,
            native_factor=np.eye(3) * 2,
            loss_object=CovarianceLoss(covariance),
        )

    assert replay()["status"] == "scalar_checks_passed_prediction_indeterminate"
    candidate["native_whitened_residual"][0] = 1.0
    with pytest.raises(ValueError, match="backward-error bound"):
        replay()


def test_terminal_status_requires_only_width_at_every_precision(monkeypatch):
    t = np.array([0.0])
    tree = profile.equation_tree(WIDE)
    proof = reference.membership(reference.reference(tree, t), t, t)
    proof["attempts"][0]["reason"] = "possible_zero_denominator"

    def fail(*args):
        raise reference.PredictionVerificationError(proof)

    monkeypatch.setattr(profile, "verify_prediction", fail)
    with pytest.raises(reference.PredictionVerificationError):
        profile.width_prediction(tree, t, t, t)


def test_worker_persists_width_before_checking_observed_vectors(tmp_path):
    t = np.arange(103) / 4096
    out = tmp_path / "member"
    profile.prepare_main_width_member(out, t, np.ones(103), seed=5)
    hooks = profile.WorkerHooks(out)
    tree, zero = profile.equation_tree(WIDE), np.zeros_like(t)
    with pytest.raises(ValueError, match="contradicts"):
        hooks.prediction_replay(tree, t, zero, zero + 1)
    assert (out / profile.WIDTH_MARKER).read_bytes() == b""
    assert hooks.prediction_replay(tree, t, zero, zero)["status"] == "indeterminate"


def width_fixture(directory, monkeypatch):
    """Simulate completed native accounting; actual prediction/loss replay stays live."""
    t, y = np.arange(103) / 4096, np.ones(103)
    profile.prepare_main_width_member(directory, t, y, seed=5)
    hooks = profile.WorkerHooks(directory)
    rows = []
    for formula in ("0.0", WIDE):
        tree = profile.equation_tree(formula)
        predicted = symbolic.evaluate_tree(tree, t)
        assert np.array_equal(predicted, np.zeros(103))
        proof = hooks.prediction_replay(tree, t, predicted, predicted)
        scalar = hooks.loss_replay(
            y, predicted, predicted, 1.0, 1.0, 1.0, 1.0, None, prediction_check=proof
        )
        rows.append(
            {
                "tree": tree,
                "display_equation": formula,
                "complexity": profile._node_count(tree),
                "loss": 1.0,
                "prediction": predicted.tolist(),
                "residual": y.tolist(),
                "julia_reimport_loss": 1.0,
                "python_loss": 1.0,
                "table_loss": 1.0,
                "prediction_replay": proof,
                "loss_replay": scalar,
            }
        )
    assert hooks.withheld_front(rows) == (profile.WIDTH_STATUS, profile.WIDTH_FRONT)
    assert hooks.withheld_front([rows[0]]) is None
    front = directory / "pysr/search"
    front.mkdir(parents=True)
    with (front / "hall_of_fame.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Complexity", "Loss", "Equation"])
        for row in rows:
            writer.writerow([row["complexity"], row["loss"], row["display_equation"]])
    _write_json(
        directory / profile.WIDTH_FRONT,
        {
            "format": symbolic.FORMAT,
            "evaluation_scope": "fitted_samples_only",
            "selection": "withheld",
            "selected_index": None,
            "candidates": rows,
            "rng": {"python_seed": 5, "backend_seed": backend_seed(5)},
            "callback_calls_during_fit": 17,
            "timing_seconds": {
                "worker_setup": 0.5,
                "fit_including_jit_and_python_exports": 10.0,
            },
        },
    )
    initial = profile.read(directory, "metadata_initial.json")
    _write_json(
        directory / "metadata.json",
        {
            **initial,
            "phase": profile.WIDTH_STATUS,
            "worker_provenance": initial["provenance"],
            "worker_adapter_source_sha256": initial["adapter_source_sha256"],
            "fit_wall_seconds": 10.0,
        },
    )
    _write_json(directory / "native_runtime.json", {"fixture": True})
    _write_json(
        directory / "backend_sources.json",
        profile.native.configuration()["reviewed_backend_sources"],
    )
    _write_json(
        directory / "outcome.json",
        {
            "format": profile.MAIN_WIDTH_FORMAT,
            "status": profile.WIDTH_STATUS,
            "returncode": 0,
            "timed_out": False,
            "worker_wall_seconds": 11.0,
            "adapter_call_wall_seconds": 11.0,
            "cpu_user_seconds": 9.0,
            "cpu_system_seconds": 1.0,
        },
    )
    monkeypatch.setattr(profile.native, "validate_runtime", lambda unused: None)
    monkeypatch.setattr(
        profile,
        "numerical_environment",
        lambda *args, completed: {"verified": completed},
    )
    monkeypatch.setattr(
        profile, "_native_completion", lambda *args: {"callback_calls_during_fit": 17}
    )
    _write_json(directory / "member_checksums.json", profile._inventory(directory))


def test_width_member_replays_whole_front_and_preserves_cost(tmp_path, monkeypatch):
    out = tmp_path / "member"
    width_fixture(out, monkeypatch)
    before = profile._inventory(out)
    result = profile.verify_member(out)
    assert profile._inventory(out) == before
    assert result["status"] == profile.WIDTH_STATUS
    assert result["width_evidence"]["candidate_indices"] == [1]
    assert result["width_evidence"]["front_count"] == 2
    assert (
        result["candidates"] == []
        and result["selected"] is result["selected_index"] is None
    )
    assert (
        result["costs"]["callback_calls_during_fit"] == 17
        and result["costs"]["fit_wall_seconds"] == 10.0
        and result["costs"]["worker_wall_seconds"] == 11.0
        and result["costs"]["adapter_call_wall_seconds"] == 11.0
    )


@pytest.mark.parametrize(
    "filename, field, value, label",
    [
        ("metadata.json", "fit_wall_seconds", math.nextafter(10.0, math.inf), "fit"),
        (profile.WIDTH_FRONT, "fit_including_jit_and_python_exports", 10, "fit"),
        (profile.WIDTH_FRONT, "fit_including_jit_and_python_exports", None, "fit"),
        (
            "outcome.json",
            "worker_wall_seconds",
            math.nextafter(11.0, math.inf),
            "worker",
        ),
        ("outcome.json", "adapter_call_wall_seconds", 11, "worker"),
    ],
)
def test_rehashed_width_timings_must_match_original_measurements(
    tmp_path, monkeypatch, filename, field, value, label
):
    out = tmp_path / "member"
    width_fixture(out, monkeypatch)
    record = profile.read(out, filename)
    fields = record["timing_seconds"] if filename == profile.WIDTH_FRONT else record
    fields[field] = value
    _write_json(out / filename, record)
    _write_json(out / "member_checksums.json", profile._inventory(out))
    with pytest.raises(
        ValueError, match=f"Inconsistent withheld worker {label} timing"
    ):
        profile.verify_member(out)


@pytest.mark.parametrize("stage", ["before_width", "after_width", "after_front"])
@pytest.mark.parametrize("failure", ["timeout", "fit_error"])
def test_incomplete_width_replay_never_becomes_an_ordinary_failure(
    tmp_path, monkeypatch, stage, failure
):
    out = tmp_path / "member"
    width_fixture(out, monkeypatch)
    (out / "outcome.json").unlink()
    if stage != "after_front":
        (out / profile.WIDTH_FRONT).unlink()
    if stage == "before_width":
        (out / profile.WIDTH_MARKER).unlink()
    metadata = profile.read(out, "metadata.json")
    metadata["phase"] = "replay"
    if failure == "fit_error":
        metadata.update(
            phase="failed",
            failed_during="replay",
            error="ValueError: No admissible candidates were exported.",
        )
    _write_json(out / "metadata.json", metadata)

    class Worker:
        returncode = -9 if failure == "timeout" else 1

        def wait(self, timeout):
            if failure == "timeout":
                raise subprocess.TimeoutExpired("worker", timeout)
            return self.returncode

    monkeypatch.setattr(
        profile,
        "subprocess",
        SimpleNamespace(
            Popen=lambda *args, **kwargs: Worker(),
            TimeoutExpired=subprocess.TimeoutExpired,
            STDOUT=subprocess.STDOUT,
        ),
    )
    monkeypatch.setattr(symbolic, "_stop_worker", lambda process: None)
    deadline = time.monotonic() + 100
    if stage == "before_width":
        assert profile.run_member(out, deadline=deadline)["status"] == failure
    else:
        with pytest.raises(ValueError, match="Incomplete worker replay"):
            profile.run_member(out, deadline=deadline)
        assert not (out / "outcome.json").exists()


@pytest.mark.parametrize(
    "tamper",
    [
        "bounded_prediction",
        "wide_prediction",
        "wide_loss",
        "width_reasons",
        "missing_marker",
        "front_row",
        "success_file",
        "success_outcome",
        "callback_count",
        "withheld_index",
    ],
)
def test_rehashed_width_diagnostics_cannot_hide_other_failures(
    tmp_path, monkeypatch, tamper
):
    out = tmp_path / "member"
    width_fixture(out, monkeypatch)
    raw = profile.read(out, profile.WIDTH_FRONT)
    bounded, wide = raw["candidates"]
    if tamper == "bounded_prediction":
        bounded["prediction"][0] = 1.0
    elif tamper == "wide_prediction":
        wide["prediction"][0] = 1.0
    elif tamper == "wide_loss":
        wide["python_loss"] = 0.5
    elif tamper == "width_reasons":
        wide["prediction_replay"]["attempts"][1]["reason"] = "other"
    elif tamper == "missing_marker":
        (out / profile.WIDTH_MARKER).unlink()
    elif tamper == "front_row":
        wide["display_equation"] = "0.0"
    elif tamper == "success_file":
        _write_json(out / "result.json", raw)
    elif tamper == "success_outcome":
        _write_json(
            out / "outcome.json",
            {**profile.read(out, "outcome.json"), "status": "completed"},
        )
    elif tamper == "callback_count":
        raw["callback_calls_during_fit"] = 99
    elif tamper == "withheld_index":
        raw["selected_index"] = 0
    _write_json(out / profile.WIDTH_FRONT, raw)
    _write_json(out / "member_checksums.json", profile._inventory(out))
    with pytest.raises((AssertionError, ValueError)):
        profile.verify_member(out)
