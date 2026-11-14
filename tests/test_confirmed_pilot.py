"""Exercise real shared inputs and reference fits with synthetic native workers."""

import json
import signal
from pathlib import Path

import numpy as np
import pytest
from test_confirmed_search import fake_native

from ringdown_sr import confirmed_pilot as pilot
from ringdown_sr import confirmed_search as search
from ringdown_sr import covariance_pilot
from ringdown_sr.cli import main
from ringdown_sr.config import parse_config
from ringdown_sr.losses import CovarianceLoss, mean_squared_error
from ringdown_sr.pilot import _write_json, run_pilot

ROOT = Path(__file__).resolve().parents[1]


def content(kind="ar1"):
    raw = (ROOT / "configs/pilot_confirmed_ar1.toml").read_text()
    raw = raw.replace("n_samples = 128", "n_samples = 16")
    raw = raw.replace("n_train = 64", "n_train = 12")
    raw = raw.replace("n_validation = 128", "n_validation = 16")
    raw = raw.replace("n_check = 256", "n_check = 16")
    if kind == "white":
        raw = raw.replace('kind = "gaussian_ar1"', 'kind = "gaussian_white"').replace(
            "correlation = 0.65\n", ""
        )
    return raw.encode()


def read(path):
    return json.loads(Path(path).read_bytes())


@pytest.fixture
def native_boundary(monkeypatch):
    """Retain real packages, publications, references and read verification."""
    events = fake_native(monkeypatch)
    monkeypatch.setattr(pilot, "_provenance", search._provenance)
    monkeypatch.setattr(covariance_pilot, "_provenance", search._provenance)
    original = search.profile.run_member

    def run(directory, **kwargs):
        record = original(directory, **kwargs)
        arrays = search._input_arrays((directory / "inputs.npz").read_bytes())
        value = 0.125 * (int(directory.name[-2:]))
        prediction = np.full_like(arrays["time_s"], value)
        residual = arrays["observed"] - prediction
        loss = (
            mean_squared_error(residual)
            if "covariance" not in arrays
            else CovarianceLoss(arrays["covariance"]).mean_squared(residual)
        )
        candidate = {
            "tree": {"kind": "constant", "value_hex": value.hex()},
            "prediction": prediction.tolist(),
            "residual": residual.tolist(),
            "loss": loss,
            "complexity": 1,
            "display_equation": str(value),
        }
        record.update(selected=candidate, candidates=[candidate])
        _write_json(directory / "verified.json", record)
        return record

    monkeypatch.setattr(search.profile, "run_member", run)
    return events


def execute(tmp_path, *, kind="ar1"):
    path = tmp_path / "config.toml"
    path.write_bytes(content(kind))
    return run_pilot(path, tmp_path / "pilot")


@pytest.mark.parametrize("kind", ["white", "ar1"])
def test_general_route_reuses_reference_data_and_four_seeds_per_arm(
    tmp_path, native_boundary, kind
):
    outcome = execute(tmp_path, kind=kind)
    assert outcome.status == "success"
    report = pilot.verify_confirmed_pilot(outcome.output_directory)
    run_events = [event for event in native_boundary if event[0] == "run"]
    assert len(run_events) == 12
    config = parse_config(content(kind))
    assert [event[1] for event in run_events] == list(config.confirmed_search.seeds) * 3
    assert report["schema_version"] == 4 and report["planned_search_calls"] == 12
    assert report["algorithm_outputs"] == 3
    assert report["selection_across_weighting_arms"] == "forbidden"
    assert report["physical_parameter_match"] == "not_assessed"
    assert (
        read(outcome.output_directory / "reference/result.json")["schema_version"] == 2
    )
    with np.load(
        outcome.output_directory / "reference/comparison_inputs.npz", allow_pickle=False
    ) as data:
        for name in pilot.ARM_LABELS:
            package = outcome.output_directory / "symbolic" / name
            with np.load(package / "inputs.npz", allow_pickle=False) as inputs:
                np.testing.assert_array_equal(inputs["time_s"], data["time_s"])
                np.testing.assert_array_equal(inputs["observed"], data["observed"])
                covariance = (
                    None
                    if name == "ordinary"
                    else data[
                        "covariance_true"
                        if name == "known_covariance"
                        else "covariance_estimated"
                    ]
                )
                if covariance is None:
                    assert "covariance" not in inputs.files
                else:
                    np.testing.assert_array_equal(inputs["covariance"], covariance)
            selected = read(package / "completion/assessment_report.json")[
                "selected_candidate"
            ]
            residual = data["observed"] - selected["prediction"]
            metrics = report["symbolic_arms"][name]["metrics"]
            expected = (
                residual
                @ np.linalg.solve(data["covariance_true"], residual)
                / len(residual)
            )
            np.testing.assert_allclose(
                metrics["q_true_per_sample"], expected, rtol=1e-12
            )
            if covariance is not None:
                expected_used = (
                    residual @ np.linalg.solve(covariance, residual) / len(residual)
                )
                np.testing.assert_allclose(
                    metrics["q_used_per_sample"], expected_used, rtol=1e-12
                )


def test_numerical_package_failure_retains_all_other_calls_and_unknown_costs(
    tmp_path, native_boundary, monkeypatch
):
    original = search.profile.run_member

    def fail_ordinary(directory, **kwargs):
        record = original(directory, **kwargs)
        if directory.parent.name == "ordinary":
            record.update(
                status="fit_error", selected=None, selected_index=None, candidates=[]
            )
            record["costs"]["fit_wall_seconds"] = None
            _write_json(directory / "verified.json", record)
        return record

    monkeypatch.setattr(search.profile, "run_member", fail_ordinary)
    outcome = execute(tmp_path)
    assert outcome.status == "comparison_failed"
    report = pilot.verify_confirmed_pilot(outcome.output_directory)
    assert len([e for e in native_boundary if e[0] == "run"]) == 12
    assert report["symbolic_arms"]["ordinary"]["costs"]["fit_wall_seconds"] is None
    assert report["symbolic_arms"]["known_covariance"]["status"] == "success"
    assert report["symbolic_arms"]["estimated_covariance"]["status"] == "success"
    assert main(["verify-confirmed", str(outcome.output_directory)]) == 0


@pytest.mark.parametrize(
    "error",
    [
        ValueError("worker provenance"),
        RuntimeError("invocation guard"),
        KeyboardInterrupt(),
    ],
)
def test_package_integrity_and_interrupts_abort_without_pilot_release(
    tmp_path, native_boundary, monkeypatch, error
):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(search.profile, "run_member", fail)
    with pytest.raises(type(error)):
        execute(tmp_path)
    assert not (tmp_path / "pilot/completion/assessment_checksums.json").exists()
    assert read(tmp_path / "pilot/run_state.json")["status"] == "aborted"


@pytest.mark.parametrize(
    "mutation", ["seeds", "profile", "scope", "covariance", "input_role", "environment"]
)
def test_mismatched_verified_package_cannot_publish_pilot(
    tmp_path, native_boundary, monkeypatch, mutation
):
    original = pilot.run_confirmed_package

    def run(*args, **kwargs):
        output = Path(kwargs["output"])
        if output.name == "known_covariance":
            if mutation == "seeds":
                kwargs["seeds"] = kwargs["seeds"][::-1]
            elif mutation == "scope":
                kwargs["technical"] = True
            elif mutation == "covariance":
                kwargs["covariance"] = kwargs["covariance"] * 2
        outcome = original(*args, **kwargs)
        if output.name == "known_covariance" and mutation in (
            "profile",
            "input_role",
            "environment",
        ):
            path = output / "completion/assessment_report.json"
            report = read(path)
            if mutation == "profile":
                report["profile"] = "different"
            elif mutation == "environment":
                report["numerical_environment"]["threads"] = 2
            else:
                with np.load(output / "inputs.npz", allow_pickle=False) as stored:
                    arrays = {name: stored[name].copy() for name in stored.files}
                arrays["unexpected"] = arrays["observed"]
                np.savez(output / "inputs.npz", **arrays)
                report["inputs_sha256"] = pilot.sources.sha256(
                    (output / "inputs.npz").read_bytes()
                )
            _write_json(path, report)
        return outcome

    monkeypatch.setattr(pilot, "run_confirmed_package", run)
    with pytest.raises(ValueError):
        execute(tmp_path)
    assert not (tmp_path / "pilot/completion/assessment_checksums.json").exists()


@pytest.mark.parametrize(
    "mutation", ["state", "reference", "config", "summary", "signal"]
)
def test_late_change_after_publication_return_revokes_release(
    tmp_path, native_boundary, monkeypatch, mutation
):
    original = pilot.publication.export_transaction

    def export(output, *args, **kwargs):
        report = original(output, *args, **kwargs)
        root = Path(output).parent
        if root.name != "pilot":
            return report
        if mutation == "state":
            _write_json(root / "run_state.json", {"status": "running"})
        elif mutation == "reference":
            (root / "reference/comparison_inputs.npz").write_bytes(b"changed")
        elif mutation == "config":
            (root / "config.toml").write_bytes(b"changed")
        elif mutation == "summary":
            (Path(output) / "assessment_summary.md").write_text("changed")
        else:
            handler = signal.getsignal(signal.SIGTERM)
            assert callable(handler)
            handler(signal.SIGTERM, None)
        return report

    monkeypatch.setattr(pilot.publication, "export_transaction", export)
    with pytest.raises((ValueError, InterruptedError)):
        execute(tmp_path)
    completion = tmp_path / "pilot/completion"
    assert (completion / "ASSESSMENT_LOCKED").exists()
    assert not (completion / "assessment_checksums.json").exists()


@pytest.mark.parametrize(
    "mutation", ["missing_state", "wrong_state", "extra", "config", "changed_reference"]
)
def test_read_verification_rejects_incomplete_or_changed_original(
    tmp_path, native_boundary, mutation
):
    root = execute(tmp_path).output_directory
    if mutation == "missing_state":
        (root / "run_state.json").unlink()
    elif mutation == "wrong_state":
        _write_json(
            root / "run_state.json",
            {
                "format": pilot.FORMAT,
                "status": "completed",
                "pilot_status": "comparison_failed",
            },
        )
    elif mutation == "extra":
        (root / "added.json").write_text("{}")
    elif mutation == "config":
        (root / "config.toml").write_bytes(
            content().replace(b"frequency_hz = 250.0", b"frequency_hz = 251.0")
        )
    else:
        path = root / "reference/comparison_inputs.npz"
        with np.load(path, allow_pickle=False) as stored:
            arrays = {name: stored[name].copy() for name in stored.files}
        arrays["covariance_estimated"] *= 2
        np.savez(path, **arrays)
        meta = read(root / "reference/metadata.json")
        meta["artifact_sha256"]["comparison_inputs.npz"] = pilot.sources.sha256(
            path.read_bytes()
        )
        _write_json(root / "reference/metadata.json", meta)
    with pytest.raises(ValueError):
        pilot.verify_confirmed_pilot(root)
    assert len([e for e in native_boundary if e[0] == "run"]) == 12


def test_schema4_cli_run_and_read_verification(tmp_path, native_boundary, capsys):
    path = tmp_path / "config.toml"
    path.write_bytes(content())
    root = tmp_path / "pilot"
    assert main(["run", str(path), "--output", str(root)]) == 0
    assert main(["verify-confirmed", str(root)]) == 0
    assert "Schema-4-Verifikation: success" in capsys.readouterr().out
    assert len([e for e in native_boundary if e[0] == "run"]) == 12


def test_read_verification_catches_change_during_last_release_check(
    tmp_path, native_boundary, monkeypatch
):
    root = execute(tmp_path).output_directory
    original = pilot.publication.verify_bytes
    count = 0

    def verify(directory, *args, **kwargs):
        nonlocal count
        original(directory, *args, **kwargs)
        if directory == root / "completion":
            count += 1
            if count == 2:
                (root / "config.toml").write_bytes(b"changed after final release check")

    monkeypatch.setattr(pilot.publication, "verify_bytes", verify)
    with pytest.raises(ValueError, match="Consumed file changed"):
        pilot.verify_confirmed_pilot(root)


@pytest.mark.parametrize(
    "artifact", ["config.toml", "completion/assessment_summary.md"]
)
def test_outer_handler_teardown_mutation_revokes_pilot(
    tmp_path, native_boundary, monkeypatch, artifact
):
    original = signal.signal
    caller_handler = signal.getsignal(signal.SIGTERM)
    mutated = []

    def restore(sig, handler):
        current = signal.getsignal(sig)
        previous = original(sig, handler)
        if (
            sig == signal.SIGTERM
            and handler == caller_handler
            and getattr(current, "__qualname__", "")
            == "run_confirmed_pilot.<locals>.interrupted"
            and not mutated
        ):
            root = tmp_path / "pilot"
            assert (root / "completion/assessment_checksums.json").exists()
            assert not (root / "completion/ASSESSMENT_LOCKED").exists()
            (root / artifact).write_bytes(b"changed while restoring outer handlers")
            mutated.append(artifact)
        return previous

    monkeypatch.setattr(signal, "signal", restore)
    with pytest.raises(ValueError):
        execute(tmp_path)
    assert mutated == [artifact]
    completion = tmp_path / "pilot/completion"
    assert (completion / "ASSESSMENT_LOCKED").exists()
    assert not (completion / "assessment_checksums.json").exists()
    assert read(tmp_path / "pilot/run_state.json")["status"] == "aborted"
