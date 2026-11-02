"""Regressions from five audited Manjaro records, without a new search or fit.

The captured NumPy predictions are replay inputs here, not transcendental-value
references for the executing platform. Native integration is tested separately.
"""

import copy
import hashlib
import json
import math
import struct
from pathlib import Path

import numpy as np
import pytest

from ringdown_sr import search_trajectory as control
from ringdown_sr.noiseless_control import frozen_data

FIXTURE = Path(__file__).with_name("fixtures") / "search_trajectory_replay_cases.json"
CAPTURE = json.loads(FIXTURE.read_bytes())


def number(bits):
    return struct.unpack(">d", bytes.fromhex(bits))[0]


def bits(value):
    return struct.pack(">d", float(value)).hex()


def vector(values):
    return np.array([number(value) for value in values], dtype=np.float64)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_key(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def exported(raw):
    if raw["kind"] == "constant":
        return {"kind": "constant", "value_hex": number(raw["value_bits"]).hex()}
    if raw["kind"] == "variable":
        return dict(raw)
    return {**raw, "children": [exported(child) for child in raw["children"]]}


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def write_bundle(tmp_path, arrays, members, replays):
    """Embed original members in one explicitly reduced technical test event."""
    path = tmp_path / "observations.jsonl"
    event = {
        "format": control.EVENT_FORMAT,
        "event_index": 1,
        "returned_population": [
            copy.deepcopy(members[i % len(members)]) for i in range(32)
        ],
        "hall_of_fame": [],
    }
    path.write_bytes(json.dumps(event).encode() + b"\n")
    units_path = tmp_path / "observation_units.json"
    write_json(
        units_path,
        {
            "format": control.UNITS_FORMAT,
            "trees": {key: {"status": "valid", "reason": None} for key in replays},
        },
    )
    np.savez(
        tmp_path / "inputs.npz", time_s=arrays["time_s"], observed=arrays["observed"]
    )
    document = {
        "format": control.REPLAY_FORMAT,
        "inputs_sha256": digest(tmp_path / "inputs.npz"),
        "raw_sha256": digest(path),
        "units_sha256": digest(units_path),
        "trees": copy.deepcopy(replays),
    }
    write_json(tmp_path / "observation_replays.json", document)
    return path, document


def verify(path, arrays, **overrides):
    arguments = {
        "expected_events": 1,
        "arrays": arrays,
        "front": {"candidates": []},
        "expected_inputs_sha256": digest(path.with_name("inputs.npz")),
        "expected_sha256": digest(path),
        "expected_units_sha256": digest(path.with_name("observation_units.json")),
        "expected_replay_sha256": digest(path.with_name("observation_replays.json")),
    }
    return control.verify_observations(path, **(arguments | overrides))


@pytest.fixture
def captured_bundle(tmp_path, monkeypatch):
    arrays = frozen_data()
    for name in ("time_s", "observed"):
        arrays[name] = vector(CAPTURE["training"][name + "_bits"])
    predictions = {
        json_key(exported(case["member"]["tree"])): vector(
            case["numpy_replay"]["prediction_bits"]
        )
        for case in CAPTURE["cases"]
    }

    def captured_numpy_replay(tree, times):
        np.testing.assert_array_equal(
            times.view(np.uint64), arrays["time_s"].view(np.uint64)
        )
        return predictions[json_key(tree)].copy()

    monkeypatch.setattr(control, "evaluate_tree", captured_numpy_replay)
    replays = {
        case["tree_sha256"]: {
            "status": "available",
            "reason": None,
            **case["native_replay"],
        }
        for case in CAPTURE["cases"]
    }
    path, document = write_bundle(
        tmp_path, arrays, [case["member"] for case in CAPTURE["cases"]], replays
    )
    return path, arrays, document


def test_fixture_preserves_audited_inputs_members_and_provenance():
    assert (
        digest(FIXTURE)
        == "0545d02156c56a83750b60bea87699e3637d973cb8791355f802a29f4523f759"
    )
    assert (
        CAPTURE["provenance"]["execution_commit"]
        == "41ccdd27aaa4ade56b509493089241d6695b9757"
    )
    assert CAPTURE["provenance"]["original_archive_sha256"] == (
        "08676ddc21c1820110ae425a68de3c5b954c8bef2022b816ca274c307041c873"
    )
    assert CAPTURE["provenance"]["replay_script_sha256"] == (
        "fa6eaa23de632fd4fa0e1fb84159e7996af52ed69cec93d2ee4ca156c3b99a61"
    )
    np.testing.assert_array_equal(
        vector(CAPTURE["training"]["time_s_bits"]), np.arange(128) / 4096
    )
    assert len(CAPTURE["training"]["observed_bits"]) == 128
    assert [(case["event_index"], case["position"]) for case in CAPTURE["cases"]] == [
        (16, 21),
        (16, 24),
        (51, 19),
        (245, 4),
        (247, 15),
    ]
    # These exact Int64 values would be corrupted by a JavaScript JSON roundtrip.
    assert [case["member"]["ref"] for case in CAPTURE["cases"]] == [
        6996717237634345370,
        3920939788815893906,
        2838068409013589290,
        3566295308476460385,
        8427256569363001243,
    ]
    for case in CAPTURE["cases"]:
        assert (
            hashlib.sha256(json_key(case["member"]["tree"]).encode()).hexdigest()
            == case["tree_sha256"]
        )
        assert case["source"] == "returned_population"


@pytest.mark.parametrize(
    "case",
    CAPTURE["cases"],
    ids=lambda case: f"event-{case['event_index']}-position-{case['position']}",
)
def test_captured_numeric_evidence_retains_three_saved_and_two_numpy_loss_mismatches(
    case,
):
    observed = vector(CAPTURE["training"]["observed_bits"])
    for name in ("native_replay", "numpy_replay"):
        predictions = vector(case[name]["prediction_bits"])
        assert predictions.shape == observed.shape == (128,)
        assert np.all(np.isfinite(predictions))
        # Independent scalar summation checks the saved replay evidence. It does
        # not use the implementation's BLAS norm or current transcendental code.
        mse = (
            math.fsum(
                (float(y) - float(q)) ** 2
                for y, q in zip(observed, predictions, strict=True)
            )
            / 128
        )
        assert math.isclose(
            number(case[name]["loss_bits"]), mse, rel_tol=1e-10, abs_tol=0
        )
    saved = number(case["member"]["loss_bits"])
    native = number(case["native_replay"]["loss_bits"])
    numpy_loss = number(case["numpy_replay"]["loss_bits"])
    assert (
        math.isclose(saved, native, rel_tol=1e-10, abs_tol=0)
        is case["expected_saved_native_mse_match"]
    )
    assert (
        math.isclose(native, numpy_loss, rel_tol=1e-10, abs_tol=0)
        is case["expected_native_numpy_mse_match"]
    )


def test_all_five_original_cases_are_unresolved_without_positive_markers(
    captured_bundle,
):
    path, arrays, _ = captured_bundle
    original = {file.name: file.read_bytes() for file in path.parent.iterdir()}
    result = verify(path, arrays)
    expected = {case["tree_sha256"]: case for case in CAPTURE["cases"]}
    assert result["counts"]["numerical_unresolved"] == 32
    assert result["counts"]["verified"] == result["counts"]["not_assessed"] == 0
    assert result["unique_tree_count"] == 5
    assert (
        sum(not case["expected_saved_native_mse_match"] for case in expected.values())
        == 3
    )
    assert (
        sum(not case["expected_native_numpy_mse_match"] for case in expected.values())
        == 2
    )
    for occurrence in result["occurrences"]:
        case = expected[occurrence["tree_sha256"]]
        assert occurrence["status"] == "numerical_unresolved"
        assert (
            occurrence["curve_marker"]
            == occurrence["parameter_marker"]
            == "not_assessed"
        )
        assert occurrence["loss_bits"] == case["member"]["loss_bits"]
        comparisons = occurrence["comparisons"]
        assert comparisons["native_loss_vs_native_prediction_mse"]["status"] == "passed"
        assert (comparisons["saved_vs_native_loss"]["status"] == "passed") is case[
            "expected_saved_native_mse_match"
        ]
        assert (comparisons["native_vs_python_tree_mse"]["status"] == "passed") is case[
            "expected_native_numpy_mse_match"
        ]
        if not case["expected_saved_native_mse_match"]:
            assert "saved_native_loss_mismatch" in occurrence["reasons"]
        if not case["expected_native_numpy_mse_match"]:
            assert "native_python_loss_mismatch" in occurrence["reasons"]
    for tree in result["trees"]:
        assert tree["status"] == "numerical_unresolved"
        if tree["diagnostics"] is not None:
            assert tree["diagnostics"]["curve_marker"] == "not_assessed"
            assert tree["diagnostics"]["parameter_match"]["status"] == "not_assessed"
        assert tree["sources"]["returned_population"]["curve_success_occurrences"] == 0
    assert {file.name: file.read_bytes() for file in path.parent.iterdir()} == original


@pytest.mark.parametrize(
    "change",
    [
        "native_loss",
        "native_prediction",
        "negative_loss",
        "truncated_prediction",
        "malformed_bits",
        "missing_tree",
        "extra_field",
    ],
)
def test_manipulated_real_replay_fails_even_with_updated_file_checksum(
    captured_bundle, change
):
    path, arrays, document = captured_bundle
    entry = document["trees"][CAPTURE["cases"][0]["tree_sha256"]]
    if change == "native_loss":
        entry["loss_bits"] = bits(number(entry["loss_bits"]) * 2)
    elif change == "native_prediction":
        entry["prediction_bits"][0] = bits(number(entry["prediction_bits"][0]) + 0.1)
    elif change == "negative_loss":
        entry["loss_bits"] = bits(-1)
    elif change == "truncated_prediction":
        entry["prediction_bits"].pop()
    elif change == "malformed_bits":
        entry["prediction_bits"][0] = "0000"
    elif change == "missing_tree":
        document["trees"].pop(CAPTURE["cases"][0]["tree_sha256"])
    else:
        entry["unapproved"] = True
    write_json(path.with_name("observation_replays.json"), document)
    with pytest.raises(ValueError):
        verify(path, arrays)


@pytest.mark.parametrize("field", ["inputs_sha256", "raw_sha256", "units_sha256"])
def test_real_replays_cannot_be_bound_to_different_artifacts(captured_bundle, field):
    path, arrays, document = captured_bundle
    document[field] = "0" * 64
    write_json(path.with_name("observation_replays.json"), document)
    with pytest.raises(ValueError):
        verify(path, arrays)


def test_changed_training_bits_invalidate_the_saved_replay_binding(captured_bundle):
    path, arrays, _ = captured_bundle
    changed = arrays["observed"].copy()
    changed[0] = np.nextafter(changed[0], math.inf)
    np.savez(path.with_name("inputs.npz"), time_s=arrays["time_s"], observed=changed)
    with pytest.raises(ValueError, match="source binding"):
        verify(path, arrays | {"observed": changed})


def test_changed_replay_checksum_is_fatal(captured_bundle):
    path, arrays, _ = captured_bundle
    with pytest.raises(ValueError, match="Changed native replay artifact"):
        verify(path, arrays, expected_replay_sha256="0" * 64)


@pytest.mark.parametrize(
    "saved_loss", [0.0, 1.0], ids=["consistent", "saved-loss-manipulated"]
)
def test_analytic_linear_control_requires_consistent_saved_loss(tmp_path, saved_loss):
    times = np.arange(128, dtype=np.float64) / 4096
    diagnostic_times = times[:-1] + 1 / 8192
    arrays = {
        "time_s": times,
        "observed": 1 + times,
        "diagnostic_time_s": diagnostic_times,
        "diagnostic_truth": 1 + diagnostic_times,
    }
    raw = {
        "kind": "operator",
        "arity": 2,
        "operator_index": 1,
        "operator": "+",
        "children": [
            {"kind": "constant", "value_bits": bits(1)},
            {"kind": "variable", "index": 1},
        ],
    }
    key = hashlib.sha256(json_key(raw).encode()).hexdigest()
    member = {
        "tree": raw,
        "loss_bits": bits(saved_loss),
        "cost_bits": bits(saved_loss),
        "complexity_cache": 3,
        "birth": 1,
        "ref": 1,
        "parent": -1,
    }
    replays = {
        key: {
            "status": "available",
            "reason": None,
            "loss_bits": bits(0),
            "prediction_bits": [bits(value) for value in arrays["observed"]],
        }
    }
    path, _ = write_bundle(tmp_path, arrays, [member], replays)
    result = verify(path, arrays)
    verified = saved_loss == 0
    assert result["counts"]["verified"] == (32 if verified else 0)
    assert result["counts"]["numerical_unresolved"] == (0 if verified else 32)
    assert result["counts"]["not_assessed"] == 0
    for occurrence in result["occurrences"]:
        assert occurrence["curve_marker"] == (
            "within_tolerance" if verified else "not_assessed"
        )
        assert occurrence["parameter_marker"] == "not_assessed"
        assert occurrence["loss_bits"] == bits(saved_loss)
        assert occurrence["comparisons"]["saved_vs_native_loss"]["status"] == (
            "passed" if verified else "failed"
        )
        assert all(
            value["status"] == "passed"
            for name, value in occurrence["comparisons"].items()
            if name != "saved_vs_native_loss"
        )
    assert result["trees"][0]["sources"]["returned_population"][
        "curve_success_occurrences"
    ] == (32 if verified else 0)
    assert json.loads(path.read_bytes())["returned_population"][0]["loss_bits"] == bits(
        saved_loss
    )
