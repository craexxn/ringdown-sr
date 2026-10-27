"""Verify recorded candidate mapping, evidence integrity and read-only diagnosis."""

import hashlib
import importlib.util
import json
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from ringdown_sr import parameter_export as export
from ringdown_sr.structure import InvalidTreeError

ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False), encoding="utf-8")


def read(path):
    return json.loads(path.read_bytes())


def hashes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def constant(value):
    return {"kind": "constant", "value_hex": float(value).hex()}


def operator(name, *children):
    names = ("exp", "sin", "cos") if len(children) == 1 else ("+", "-", "*", "/")
    return {
        "kind": "operator",
        "operator": name,
        "arity": len(children),
        "operator_index": names.index(name) + 1,
        "children": list(children),
    }


def reseal(root, *, workers=True):
    if workers:
        for name in export.ARMS:
            directory = root / "symbolic" / name
            write(
                directory / "checksums.json",
                {
                    key: value
                    for key, value in hashes(directory).items()
                    if key != "checksums.json"
                },
            )
    metadata = read(root / "metadata.json")
    metadata["artifact_sha256"] = {
        key: value for key, value in hashes(root).items() if key != "metadata.json"
    }
    write(root / "metadata.json", metadata)


@pytest.fixture
def stored(tmp_path):
    """Write independently prescribed artifacts; never fit or generate noise."""
    root = tmp_path / "stored"
    provenance = {"git": {"commit": "recorded-commit", "dirty": False}}
    environment = {"platform": "recorded-search-platform"}
    time = np.arange(8, dtype=np.float64) / 1024
    variable = {"kind": "variable", "index": 1}
    tree = operator(
        "*",
        constant(2),
        operator(
            "*",
            operator("exp", operator("*", constant(-125), variable)),
            operator(
                "cos",
                operator("+", operator("*", constant(512), variable), constant(0.25)),
            ),
        ),
    )
    predictions = (
        np.full(8, 3.0),
        2 * np.exp(-125 * time) * np.cos(512 * time + 0.25),
        np.sin(time),
    )
    candidates = [
        {
            "tree": expression,
            "complexity": size,
            "loss": loss,
            "display_equation": label,
            "prediction": prediction.tolist(),
            "residual": (-prediction).tolist(),
            "extra_recorded_field": "retained",
        }
        for expression, size, loss, label, prediction in zip(
            (constant(3), tree, operator("sin", variable)),
            (1, 13, 2),
            (3.0, 1.0, 2.0),
            ("constant", "ringdown", "sin(t)"),
            predictions,
            strict=True,
        )
    ]
    reference = root / "reference"
    reference.mkdir(parents=True)
    np.savez(reference / "comparison_inputs.npz", time_s=time, signal=np.ones(8))
    for filename in ("metadata.json", "result.json"):
        write(
            reference / filename,
            {
                "schema_version": 2,
                "status": "success",
                "provenance": provenance,
                "environment": environment,
            },
        )
    budget = {"seed": 42, "niterations": 1}
    write(
        root / "resolved_config.json",
        {
            "schema_version": 3,
            "sampling": {"n_samples": 8, "sample_rate_hz": 1024},
            "signal": {"amplitude": 999.0},
            "symbolic_search": budget,
        },
    )
    result = {
        "schema_version": 3,
        "status": "success",
        "stage": "complete",
        "evaluation_scope": "fitted_samples_only",
        "shared_inputs_file": "reference/comparison_inputs.npz",
        "reference": {"status": "success", "result_file": "reference/result.json"},
        "symbolic_arms": {},
    }
    for name in export.ARMS:
        directory = root / "symbolic" / name
        directory.mkdir(parents=True)
        inputs = {"time_s": time, "observed": np.zeros(8)}
        if name != "ordinary":
            inputs["covariance"] = np.eye(8)
        np.savez(directory / "inputs.npz", **inputs)
        write(directory / "metadata_initial.json", {"provenance": provenance})
        write(
            directory / "metadata.json",
            {
                "phase": "success",
                "provenance": provenance,
                "worker_provenance": {"worker": name},
                "environment": environment,
            },
        )
        write(
            directory / "request.json", {"format": export.ARM_FORMAT, "budget": budget}
        )
        write(
            directory / "result.json",
            {
                "format": export.ARM_FORMAT,
                "evaluation_scope": "fitted_samples_only",
                "selected_index": 1,
                "candidates": candidates,
            },
        )
        result["symbolic_arms"][name] = {
            "status": "success",
            "result_file": f"symbolic/{name}/result.json",
            "selected": {
                "index": 1,
                "complexity": 13,
                "training_loss": 1.0,
                "display_equation": "ringdown",
                "parameter_interpretation": "not_attempted",
            },
        }
    write(root / "result.json", result)
    write(
        root / "metadata_initial.json",
        {"provenance": provenance, "environment": environment},
    )
    write(
        root / "metadata.json",
        {
            "schema_version": 3,
            "status": "success",
            "provenance": provenance,
            "environment": environment,
        },
    )
    reseal(root)
    return root


def test_export_preserves_every_candidate_and_source_bytes(stored, tmp_path):
    before = hashes(stored)
    random_before, numpy_before = random.getstate(), np.random.get_state()
    output = export.export_parameter_diagnostics(stored, tmp_path / "diagnostics")
    report = read(output / "diagnostics.json")
    assert hashes(stored) == before
    assert random.getstate() == random_before
    after = np.random.get_state()
    assert numpy_before[0] == after[0] and numpy_before[2:] == after[2:]
    np.testing.assert_array_equal(numpy_before[1], after[1])
    assert report["format"] == "ringdown-sr-parameter-diagnostics-1"
    assert report["physical_identification"] == "not_assessed"
    assert report["source"]["recorded_metadata"] == read(stored / "metadata.json")
    assert report["source"]["recorded_initial_metadata"] == read(
        stored / "metadata_initial.json"
    )
    assert report["exporter"]["environment"]["julia_used"] is False
    assert report["exporter"]["environment"]["platform"] != "recorded-search-platform"
    assert (
        report["exporter"]["environment"]["numerical_libraries"]["snapshot"]
        == "parameter_diagnostics_export"
    )
    assert report["exporter"]["provenance"]["python_source_sha256"][
        "ringdown_sr/parameter_export.py"
    ]
    for name in export.ARMS:
        front = read(stored / f"symbolic/{name}/result.json")
        arm = report["arms"][name]
        assert arm["selected_index"] == 1 and arm["candidate_count"] == 3
        assert [c["source_candidate"] for c in arm["candidates"]] == front["candidates"]
        assert [c["source_index"] for c in arm["candidates"]] == [0, 1, 2]
        assert [c["is_selected"] for c in arm["candidates"]] == [False, True, False]
        assert [
            c["analysis"]["structure"]["structure_status"] for c in arm["candidates"]
        ] == [
            "not_supported",
            "recognized",
            "not_supported",
        ]
        analysis = arm["candidates"][1]["analysis"]
        assert analysis["raw_parameters"]["decay_time_s"]["value"] == 0.008
        assert analysis["raw_parameters"]["frequency_raw_hz"]["value"] == 256 / np.pi
        assert analysis["raw_replay"]["status"] == "passed"
        assert arm["source_selection"]["parameter_interpretation"] == "not_attempted"
        assert all(
            c["saved_prediction_replay"]["status"] == "passed"
            for c in arm["candidates"]
        )
    for filename, digest in report["source"]["file_sha256"].items():
        assert before[filename] == digest
    manifest = read(output / "metadata.json")
    assert manifest["status"] == "success"
    assert manifest["artifact_sha256"] == {
        "diagnostics.json": hashes(output)["diagnostics.json"]
    }


def test_stored_selection_is_referenced_without_reranking(stored, tmp_path):
    result = read(stored / "result.json")
    for name in export.ARMS:
        path = stored / f"symbolic/{name}/result.json"
        front = read(path)
        front["selected_index"] = 0
        write(path, front)
        result["symbolic_arms"][name]["selected"].update(
            index=0, complexity=1, training_loss=3.0, display_equation="constant"
        )
    write(stored / "result.json", result)
    reseal(stored)
    output = export.export_parameter_diagnostics(stored, tmp_path / "out")
    for arm in read(output / "diagnostics.json")["arms"].values():
        assert arm["selected_index"] == 0
        assert (
            arm["candidates"][0]["analysis"]["structure"]["structure_status"]
            == "not_supported"
        )
        assert (
            arm["candidates"][1]["source_candidate"]["loss"]
            < arm["candidates"][0]["source_candidate"]["loss"]
        )


@pytest.mark.parametrize(
    "filename",
    [
        "result.json",
        "resolved_config.json",
        "reference/comparison_inputs.npz",
        "symbolic/ordinary/result.json",
        "symbolic/ordinary/metadata_initial.json",
        "symbolic/ordinary/checksums.json",
    ],
)
def test_unsealed_source_corruption_fails_before_output(stored, tmp_path, filename):
    with (stored / filename).open("ab") as file:
        file.write(b" ")
    before = hashes(stored)
    with pytest.raises(ValueError, match="checksum"):
        export.export_parameter_diagnostics(stored, tmp_path / "absent")
    assert not (tmp_path / "absent").exists() and hashes(stored) == before


@pytest.mark.parametrize(
    "corruption",
    [
        "index_bool",
        "index_float",
        "index_negative",
        "index_large",
        "selection_mismatch",
        "arm_path",
        "worker_phase",
        "worker_provenance",
        "pilot_provenance",
        "request",
        "empty_front",
        "tree",
        "complexity",
        "prediction",
        "sampling",
        "time",
        "time_zero_sign",
        "failed_run",
        "failed_reference",
    ],
)
def test_invalid_recorded_contract_is_rejected(stored, tmp_path, corruption):
    path = stored / "symbolic/ordinary/result.json"
    front, result = read(path), read(stored / "result.json")
    if corruption.startswith("index_"):
        front["selected_index"] = {
            "index_bool": True,
            "index_float": 1.0,
            "index_negative": -1,
            "index_large": 3,
        }[corruption]
    elif corruption == "selection_mismatch":
        result["symbolic_arms"]["ordinary"]["selected"]["index"] = 2
    elif corruption == "arm_path":
        result["symbolic_arms"]["ordinary"]["result_file"] = (
            "symbolic/known_covariance/result.json"
        )
    elif corruption in ("worker_phase", "worker_provenance"):
        target = stored / "symbolic/ordinary/metadata.json"
        meta = read(target)
        meta["phase" if corruption == "worker_phase" else "provenance"] = "changed"
        write(target, meta)
    elif corruption == "pilot_provenance":
        write(stored / "metadata_initial.json", {"provenance": "changed"})
    elif corruption == "request":
        write(
            stored / "symbolic/ordinary/request.json",
            {"format": export.ARM_FORMAT, "budget": {}},
        )
    elif corruption == "empty_front":
        front["candidates"] = []
    elif corruption == "tree":
        front["candidates"][1]["tree"]["operator_index"] = 2
    elif corruption == "complexity":
        front["candidates"][0]["complexity"] = 2
    elif corruption == "prediction":
        front["candidates"][0]["prediction"][0] *= -1
    elif corruption == "sampling":
        target = stored / "resolved_config.json"
        config = read(target)
        config["sampling"]["sample_rate_hz"] = True
        write(target, config)
    elif corruption in ("time", "time_zero_sign"):
        time = np.arange(8) / 1024
        time[0] = 0.01 if corruption == "time" else -0.0
        np.savez(
            stored / "symbolic/ordinary/inputs.npz", time_s=time, observed=np.zeros(8)
        )
    elif corruption == "failed_run":
        result["status"] = "comparison_failed"
    elif corruption == "failed_reference":
        target = stored / "reference/result.json"
        record = read(target)
        record["status"] = "failed"
        write(target, record)
    write(path, front)
    write(stored / "result.json", result)
    reseal(stored)
    with pytest.raises((ValueError, TypeError, AssertionError)):
        export.export_parameter_diagnostics(stored, tmp_path / "absent")
    assert not (tmp_path / "absent").exists()


def test_invalid_tree_is_not_hidden_as_unsupported(stored, tmp_path):
    path = stored / "symbolic/ordinary/result.json"
    front = read(path)
    front["candidates"][0]["tree"]["value_hex"] = "nan"
    write(path, front)
    reseal(stored)
    with pytest.raises(InvalidTreeError):
        export.export_parameter_diagnostics(stored, tmp_path / "absent")


def test_worker_checksums_are_checked_independently(stored, tmp_path):
    path = stored / "symbolic/ordinary/result.json"
    with path.open("ab") as file:
        file.write(b" ")
    reseal(stored, workers=False)
    with pytest.raises(ValueError, match="worker checksum"):
        export.export_parameter_diagnostics(stored, tmp_path / "absent")


@pytest.mark.parametrize(
    "name", ["../outside", "/absolute", "C:/absolute", "a\\b", "a/../b"]
)
def test_unsafe_manifest_paths_are_rejected(stored, tmp_path, name):
    path = stored / "metadata.json"
    metadata = read(path)
    metadata["artifact_sha256"][name] = "0" * 64
    write(path, metadata)
    with pytest.raises(ValueError, match="path|escapes"):
        export.export_parameter_diagnostics(stored, tmp_path / "absent")


@pytest.mark.parametrize("location", ["source", "child", "parent", "existing"])
def test_output_cannot_overwrite_or_overlap_source(stored, tmp_path, location):
    output = {
        "source": stored,
        "child": stored / "new",
        "parent": tmp_path,
        "existing": tmp_path / "exists",
    }[location]
    if location == "existing":
        output.mkdir()
        (output / "sentinel").write_text("keep")
    before = hashes(stored)
    with pytest.raises((ValueError, FileExistsError)):
        export.export_parameter_diagnostics(stored, output)
    assert hashes(stored) == before
    if location == "existing":
        assert (output / "sentinel").read_text() == "keep"


def test_source_changes_during_diagnosis_are_detected(stored, tmp_path, monkeypatch):
    original = export.analyze_tree

    def mutate(*args, **kwargs):
        with (stored / "metadata.json").open("ab") as file:
            file.write(b" ")
        return original(*args, **kwargs)

    monkeypatch.setattr(export, "analyze_tree", mutate)
    with pytest.raises(ValueError, match="changed during"):
        export.export_parameter_diagnostics(stored, tmp_path / "absent")
    assert not (tmp_path / "absent").exists()


def test_truth_and_other_fronts_do_not_change_a_candidate_analysis(stored, tmp_path):
    first = read(
        export.export_parameter_diagnostics(stored, tmp_path / "first")
        / "diagnostics.json"
    )
    config = read(stored / "resolved_config.json")
    config["signal"]["amplitude"] *= 1e20
    write(stored / "resolved_config.json", config)
    np.savez(
        stored / "reference/comparison_inputs.npz",
        time_s=np.arange(8) / 1024,
        signal=np.full(8, np.nan),
    )
    path = stored / "symbolic/known_covariance/result.json"
    front = read(path)
    front["candidates"][0]["display_equation"] = "changed display text only"
    write(path, front)
    reseal(stored)
    second = read(
        export.export_parameter_diagnostics(stored, tmp_path / "second")
        / "diagnostics.json"
    )
    assert (
        first["arms"]["ordinary"]["candidates"]
        == second["arms"]["ordinary"]["candidates"]
    )


@pytest.mark.parametrize(
    "payload", [b'{"x": NaN}', b'{"x": 1e999}', b'{"x": 1, "x": 2}']
)
def test_nonstandard_or_ambiguous_json_is_rejected(stored, tmp_path, payload):
    (stored / "resolved_config.json").write_bytes(payload)
    reseal(stored)
    with pytest.raises(ValueError, match="JSON"):
        export.export_parameter_diagnostics(stored, tmp_path / "absent")


def test_cli_exports_with_julia_and_pysr_imports_forbidden(stored, tmp_path):
    code = """
import importlib.abc, runpy, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in {'pysr', 'juliacall'}:
            raise RuntimeError('Search runtime import is forbidden')
sys.meta_path.insert(0, Block())
sys.argv = [sys.argv[1], *sys.argv[2:]]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(ROOT / "scripts/export_parameter_diagnostics.py"),
            str(stored),
            "--output",
            str(tmp_path / "cli"),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "exported" in result.stdout
    assert read(tmp_path / "cli/metadata.json")["status"] == "success"


def test_cli_requires_explicit_output():
    spec = importlib.util.spec_from_file_location(
        "parameter_export_cli", ROOT / "scripts/export_parameter_diagnostics.py"
    )
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    with pytest.raises(SystemExit) as caught:
        cli.main(["stored"])
    assert caught.value.code == 2


@pytest.mark.parametrize("case", ["nonassociative", "unresolved_alias"])
def test_diagnostic_failure_states_are_exported_without_changing_selection(
    stored, tmp_path, case
):
    path = stored / "symbolic/ordinary/result.json"
    front = read(path)
    candidate = front["candidates"][1]
    time = np.arange(8) / 1024
    if case == "nonassociative":
        # Exact rate is one, while the original Float64 grouping yields zero.
        candidate["tree"]["children"][1]["children"][0]["children"][0]["children"][
            0
        ] = operator("+", constant(1e16), operator("+", constant(-1e16), constant(1)))
        candidate["complexity"] = 17
        candidate["prediction"] = (2 * np.cos(512 * time + 0.25)).tolist()
    else:
        candidate["tree"]["children"][1]["children"][1]["children"][0]["children"][0][
            "children"
        ][0] = constant(1e300)
        candidate["prediction"] = (
            2 * np.exp(-125 * time) * np.cos(1e300 * time + 0.25)
        ).tolist()
    write(path, front)
    result = read(stored / "result.json")
    result["symbolic_arms"]["ordinary"]["selected"]["complexity"] = candidate[
        "complexity"
    ]
    write(stored / "result.json", result)
    reseal(stored)
    before = hashes(stored)
    output = export.export_parameter_diagnostics(stored, tmp_path / "out")
    arm = read(output / "diagnostics.json")["arms"]["ordinary"]
    diagnostic = arm["candidates"][1]
    assert hashes(stored) == before
    assert arm["selected_index"] == 1
    assert diagnostic["saved_prediction_replay"]["status"] == "passed"
    assert diagnostic["analysis"]["structure"]["structure_status"] == "recognized"
    if case == "nonassociative":
        assert diagnostic["analysis"]["raw_replay"]["status"] == "failed"
        assert diagnostic["analysis"]["alias_replay"]["status"] == "failed"
    else:
        assert diagnostic["analysis"]["alias"]["status"] == "numerical_unresolved"
    assert read(output / "metadata.json")["status"] == "success"


def test_write_failure_has_no_success_marker_and_leaves_source_untouched(
    stored, tmp_path, monkeypatch
):
    output = tmp_path / "out"
    original = Path.open
    before = hashes(stored)

    def fail_marker(path, *args, **kwargs):
        if path == output / "metadata.json":
            raise OSError("injected completion marker failure")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_marker)
    with pytest.raises(OSError, match="completion marker"):
        export.export_parameter_diagnostics(stored, output)
    assert (output / "diagnostics.json").is_file()
    assert not (output / "metadata.json").exists()
    assert hashes(stored) == before
