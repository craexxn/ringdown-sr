"""Synthetic archive fixtures test bindings, never stand in for historical results."""

import copy
import importlib
import io
import subprocess
import tarfile

import numpy as np
import pytest

from ringdown_sr import assessment_sources as sources


def npz(**arrays):
    stream = io.BytesIO()
    np.savez(stream, **arrays)
    return stream.getvalue()


def pack(files, prefix="synthetic-series", extra=None):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for name, raw in files.items():
            member = tarfile.TarInfo(prefix + "/" + name)
            member.size = len(raw)
            archive.addfile(member, io.BytesIO(raw))
        if extra is not None:
            archive.addfile(extra, io.BytesIO(b"x") if extra.isfile() else None)
    return stream.getvalue()


def seal(files):
    report = sources.read_json(files["report.json"])
    report["frozen_file_sha256"] = {
        name: sources.sha256(raw)
        for name, raw in files.items()
        if name not in {"report.json", "summary.md", "checksums.json"}
    }
    files["report.json"] = sources.json_bytes(report)
    files["checksums.json"] = sources.json_bytes(
        {
            name: sources.sha256(raw)
            for name, raw in files.items()
            if name != "checksums.json"
        }
    )


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    blobs = {
        name: ("Synthetic nonexecutable source: " + name).encode()
        for name in (
            "src/ringdown_sr/synthetic.py",
            "plan.md",
            ".python-version",
            "pyproject.toml",
            "uv.lock",
            "src/ringdown_sr/juliapkg.json",
            "julia/Project.toml",
            "julia/Manifest.toml",
        )
    }
    hashes = {name: sources.sha256(raw) for name, raw in blobs.items()}
    python = {"ringdown_sr/synthetic.py": hashes["src/ringdown_sr/synthetic.py"]}
    provenance = {
        "git": {"available": True, "commit": "1" * 40, "dirty": False, "changes": []},
        "python_source_sha256": python,
        "python_source_set_sha256": sources.sha256(sources.json_bytes(python)),
        "project_file_sha256": {
            name: value
            for name, value in hashes.items()
            if name not in {"src/ringdown_sr/synthetic.py", "plan.md"}
        },
    }
    arrays = {
        "time_s": np.arange(4, dtype=float),
        "observed": np.arange(1, 5, dtype=float),
        "diagnostic_time_s": np.linspace(0.25, 2.75, 5),
        "diagnostic_truth": np.linspace(1.25, 3.75, 5),
    }
    spec = {
        "execution_commit": "1" * 40,
        "format": "synthetic-series-1",
        "profile_format": "synthetic-profile-1",
        "plan": {"commit": "2" * 40, "sha256": hashes["plan.md"]},
        "plan_path": "plan.md",
        "source_count": len(hashes),
        "source_set_sha256": sources.sha256(sources.json_bytes(hashes)),
        "runtime_sources": {"worker.py": "src/ringdown_sr/synthetic.py"},
        "signal_order": ["anchor"],
        "data_shape": {"training": 4, "diagnostic": 5},
        "local_profiles": {
            "synthetic": {
                "optimizer_iterations": 100,
                "optimizer_nrestarts": 2,
                "should_simplify": False,
                "use_frequency": True,
                "use_frequency_in_tournament": True,
            }
        },
        "cells": [
            {
                "number": n,
                "directory": f"cell-{n:02d}",
                "condition": "synthetic",
                "arm": "synthetic",
                "budget": {"seed": seed, "niterations": 2},
            }
            for n, seed in enumerate((101, 102), 1)
        ],
    }
    files = {
        "training.npz": npz(time_s=arrays["time_s"], observed=arrays["observed"]),
        "diagnostic.npz": npz(
            diagnostic_time_s=arrays["diagnostic_time_s"],
            diagnostic_truth=arrays["diagnostic_truth"],
        ),
        "runtime/worker.py": blobs["src/ringdown_sr/synthetic.py"],
        "summary.md": b"Synthetic only.\n",
    }
    report = {
        "format": spec["format"],
        "status": "completed",
        "final_verification": "passed",
        "plan": spec["plan"],
        "source_sha256": hashes,
        "control_initial": {"provenance": provenance},
        "control_final": {"provenance": provenance},
        "input_fingerprints": {
            name: sources.fingerprint(value) for name, value in arrays.items()
        },
        "cells": [],
    }
    tree = {"kind": "constant", "value_hex": float(1).hex()}
    for expected in spec["cells"]:
        params = {**spec["local_profiles"]["synthetic"], "niterations": 2}
        native = {
            "format": spec["format"],
            "status": "verified",
            "backend_options": {"synthetic": True},
        }
        front = {
            "format": "ringdown-sr-search-arm-1",
            "selected_index": 1,
            "selection": "minimum_training_loss_then_complexity",
            "evaluation_scope": "fitted_samples_only",
            "rng": {"python_seed": expected["budget"]["seed"], "backend_seed": 123},
            "candidates": [],
        }
        diagnoses = []
        for index in (0, 1):
            candidate = {
                "tree": tree,
                "complexity": 1,
                "display_equation": "1.0",
                "loss": 2.0 - index,
                "prediction_replay": {
                    "status": "passed",
                    "times": sources.fingerprint(arrays["time_s"]),
                    "tree_sha256": sources.sha256(sources.json_bytes(tree)),
                },
                "loss_replay": {"status": "passed"},
            }
            front["candidates"].append(candidate)
            diagnoses.append(
                {
                    "source_index": index,
                    "is_selected": index == 1,
                    "source_candidate_sha256": sources.sha256(
                        sources.json_bytes(candidate)
                    ),
                    "complexity": 1,
                    "display_equation": "1.0",
                    "training_loss": candidate["loss"],
                    "training_verification": {"status": "passed"},
                    "curve_errors": {
                        grid: {
                            "status": "available",
                            "reason": None,
                            "relative_rms": 0.5 * index,
                            "relative_max": 0.5 * index,
                        }
                        for grid in ("training", "diagnostic")
                    },
                    "curve_marker": "outside_tolerance"
                    if index
                    else "within_tolerance",
                    "search_analysis": {
                        "structure": {"structure_status": "not_supported"}
                    },
                    "physical_analysis": {"alias": {"status": "not_attempted"}},
                    "parameter_match": {"status": "not_assessed"},
                }
            )
        cellfiles = {
            "inputs.npz": files["training.npz"],
            "result.json": sources.json_bytes(front),
            "request.json": sources.json_bytes(
                {"format": "ringdown-sr-search-arm-1", "budget": expected["budget"]}
            ),
            "profile.json": sources.json_bytes(
                {"format": spec["profile_format"], "condition": "synthetic"}
            ),
            "metadata_initial.json": sources.json_bytes({"provenance": provenance}),
            "metadata.json": sources.json_bytes(
                {
                    "phase": "success",
                    "provenance": provenance,
                    "worker_provenance": provenance,
                }
            ),
            "status.json": sources.json_bytes({"status": "success"}),
            "verification.json": sources.json_bytes(native),
            "backend_options.json": sources.json_bytes(native["backend_options"]),
            "pysr_parameters.json": sources.json_bytes(params),
        }
        cellfiles["manifest.json"] = sources.json_bytes(
            {
                "format": spec["format"],
                "sources": hashes,
                "inputs": {
                    name: sources.sha256(cellfiles[name])
                    for name in ("inputs.npz", "request.json", "profile.json")
                },
                "runtime": {"worker.py": hashes["src/ringdown_sr/synthetic.py"]},
            }
        )
        cellfiles["checksums.json"] = sources.json_bytes(
            {name: sources.sha256(raw) for name, raw in cellfiles.items()}
        )
        report["cells"].append(
            {
                **expected,
                "status": "completed",
                "diagnostics": {
                    "selected_index": 1,
                    "candidate_count": 2,
                    "candidates": diagnoses,
                    "source_file_sha256": {
                        name: sources.sha256(raw) for name, raw in cellfiles.items()
                    },
                    "native_verification": native,
                    "effective_parameters": params,
                    "effective_backend_options": native["backend_options"],
                    "rng": front["rng"],
                },
            }
        )
        files.update(
            {expected["directory"] + "/" + name: raw for name, raw in cellfiles.items()}
        )
    files["report.json"] = sources.json_bytes(report)
    path = tmp_path / "synthetic-series.tar.gz"
    monkeypatch.setattr(sources, "_git_file", lambda commit, name: blobs[name])
    monkeypatch.setattr(sources, "contracts", lambda: {"synthetic-series": spec})

    def write(mutate=None, extra=None, manifest_mutation=None):
        modified = copy.deepcopy(files)
        if mutate:
            mutate(modified)
        seal(modified)
        if manifest_mutation:
            manifest_mutation(modified)
        raw = pack(modified, extra=extra)
        path.write_bytes(raw)
        spec["archive_sha256"] = sources.sha256(raw)
        return path

    return write, path, spec, report


def change_report(files, mutate):
    report = sources.read_json(files["report.json"])
    mutate(report)
    files["report.json"] = sources.json_bytes(report)


def test_original_selection_and_historical_values_survive_without_reranking(synthetic):
    write, _, _, report = synthetic
    verified = sources.read_verified_series(write(), "synthetic-series")
    assert len(verified.records) == 2
    for raw, cell in zip(verified.records, report["cells"], strict=True):
        record = sources.read_json(raw)
        assert record["original_selected_index"] == 1
        assert record["unchanged_historical"] == cell["diagnostics"]["candidates"][1]
        assert record["candidate"]["display_equation"] == "1.0"
    assert (
        sources.read_json(verified.records[0])["cell"]["budget"]["seed"]
        != sources.read_json(verified.records[1])["cell"]["budget"]["seed"]
    )
    with pytest.raises(TypeError):
        verified.files["report.json"] = b"changed"


def reanchor_cell(files):
    """Rebind synthetic consumption files, leaving candidate identity independent."""
    report = sources.read_json(files["report.json"])
    cell = report["cells"][0]
    prefix = cell["directory"] + "/"
    manifest = sources.read_json(files[prefix + "manifest.json"])
    manifest["inputs"] = {
        name: sources.sha256(files[prefix + name]) for name in manifest["inputs"]
    }
    files[prefix + "manifest.json"] = sources.json_bytes(manifest)
    checksums = sources.read_json(files[prefix + "checksums.json"])
    files[prefix + "checksums.json"] = sources.json_bytes(
        {name: sources.sha256(files[prefix + name]) for name in checksums}
    )
    cell["diagnostics"]["source_file_sha256"] = {
        name: sources.sha256(files[prefix + name])
        for name in cell["diagnostics"]["source_file_sha256"]
    }
    files["report.json"] = sources.json_bytes(report)


@pytest.mark.parametrize(
    "name,mutate",
    [
        (
            "result.json",
            lambda r: r["candidates"][1].update(
                tree={"kind": "constant", "value_hex": float(2).hex()}
            ),
        ),
        ("result.json", lambda r: r.update(selected_index=0)),
        ("result.json", lambda r: r["candidates"].reverse()),
        ("result.json", lambda r: r["rng"].update(python_seed=999)),
        ("metadata.json", lambda r: r.update(phase="failed")),
        ("manifest.json", lambda r: r["runtime"].update(**{"worker.py": "0" * 64})),
        ("pysr_parameters.json", lambda r: r.update(optimizer_iterations=300)),
        ("verification.json", lambda r: r.update(status="failed")),
    ],
)
def test_resealed_consumption_still_rejects_independent_binding_contradictions(
    synthetic, name, mutate
):
    write, _, _, _ = synthetic

    def alter(files):
        path = "cell-01/" + name
        document = sources.read_json(files[path])
        mutate(document)
        files[path] = sources.json_bytes(document)
        reanchor_cell(files)

    with pytest.raises(ValueError):
        sources.read_verified_series(write(alter), "synthetic-series")


@pytest.mark.parametrize(
    "kind", ["swapped", "bit", "signal", "missing", "zero_reference", "object"]
)
def test_grid_roles_and_exact_input_bits(synthetic, kind):
    write, _, _, _ = synthetic

    def alter(files):
        if kind == "swapped":
            files["training.npz"], files["diagnostic.npz"] = (
                files["diagnostic.npz"],
                files["training.npz"],
            )
        elif kind == "missing":
            del files["diagnostic.npz"]
        elif kind == "signal":
            files["cell-01/inputs.npz"] = npz(
                time_s=np.arange(4, dtype=float), observed=np.arange(2, 6, dtype=float)
            )
            reanchor_cell(files)
        else:
            values = np.arange(1, 5, dtype=float)
            if kind == "bit":
                values[0] = np.nextafter(values[0], np.inf)
            elif kind == "zero_reference":
                values[:] = 0
            else:
                values = values.astype(object)
            files["training.npz"] = npz(
                time_s=np.arange(4, dtype=float), observed=values
            )

    with pytest.raises((ValueError, KeyError)):
        sources.read_verified_series(write(alter), "synthetic-series")


@pytest.mark.parametrize("change", ["manifest", "fingerprints", "order", "truth"])
def test_frozen_multi_signal_manifest_binding(synthetic, monkeypatch, change):
    write, _, spec, _ = synthetic
    files = sources.archive_files(write().read_bytes(), "synthetic-series")
    report = sources.read_json(files["report.json"])
    manifest = {
        "arrays": copy.deepcopy(report["input_fingerprints"]),
        "cases": [{"name": "anchor", "truth": {"amplitude": 1.0}}],
    }
    report["input_manifest"] = copy.deepcopy(manifest)
    report["configuration"] = {"truth": {"anchor": {"amplitude": 1.0}}}
    spec["input_manifest_path"] = "synthetic-inputs.json"
    monkeypatch.setattr(
        sources, "_git_file", lambda *args: sources.json_bytes(manifest)
    )
    sources._arrays(files, report, spec)
    if change == "manifest":
        report["input_manifest"]["cases"][0]["truth"]["amplitude"] = 2.0
    elif change == "fingerprints":
        manifest["arrays"]["observed"]["sha256"] = "0" * 64
        report["input_manifest"] = copy.deepcopy(manifest)
    elif change == "order":
        spec["signal_order"] = ["wrong"]
    else:
        report["configuration"]["truth"]["anchor"]["amplitude"] = 2.0
    with pytest.raises(ValueError):
        sources._arrays(files, report, spec)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.update(status="failed"),
        lambda r: r.update(final_verification="pending"),
        lambda r: r["cells"].pop(),
        lambda r: r["cells"][0].update(status="running"),
        lambda r: r["cells"][0].update(directory="cell-02"),
        lambda r: r["cells"][0]["budget"].update(seed=999),
        lambda r: r["cells"][0].update(condition="other"),
        lambda r: r["control_initial"]["provenance"]["git"].update(commit="3" * 40),
        lambda r: r["source_sha256"].pop("plan.md"),
        lambda r: r["cells"][0]["diagnostics"].update(selected_index=0),
        lambda r: r["cells"][0]["diagnostics"].update(selected_index=True),
        lambda r: r["cells"][0]["diagnostics"]["candidates"][1].update(source_index=0),
        lambda r: r["cells"][0]["diagnostics"]["candidates"][1].update(is_selected=1),
        lambda r: r["cells"][0]["diagnostics"]["candidates"][1].update(
            source_candidate_sha256="0" * 64
        ),
        lambda r: r["cells"][0]["diagnostics"]["candidates"][1][
            "training_verification"
        ].update(status="failed"),
        lambda r: r["cells"][0]["diagnostics"]["source_file_sha256"].pop("result.json"),
        lambda r: r["cells"][0]["diagnostics"]["source_file_sha256"].update(
            **{"result.json": "0" * 64}
        ),
        lambda r: r["input_fingerprints"]["observed"].update(sha256="0" * 64),
    ],
)
def test_inconsistent_bound_series_never_imports(synthetic, mutate):
    write, _, _, _ = synthetic
    with pytest.raises(ValueError):
        sources.read_verified_series(
            write(lambda files: change_report(files, mutate)), "synthetic-series"
        )


def test_external_hash_is_required_before_archive_parsing(synthetic, monkeypatch):
    write, path, _, _ = synthetic
    write()
    path.write_bytes(b"not the original archive")
    monkeypatch.setattr(
        sources, "archive_files", lambda *a: pytest.fail("parsed unanchored archive")
    )
    with pytest.raises(ValueError, match="externally anchored"):
        sources.read_verified_series(path, "synthetic-series")


@pytest.mark.parametrize(
    "raw",
    [
        b'{"a":1,"a":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":1e999}',
        b'{"x":-1e999}',
    ],
)
def test_strict_json_including_unselected_documents(synthetic, raw):
    write, _, _, _ = synthetic
    with pytest.raises(ValueError):
        sources.read_verified_series(
            write(lambda files: files.update({"unused.json": raw})), "synthetic-series"
        )


@pytest.mark.parametrize(
    "name,kind",
    [
        ("/absolute", tarfile.REGTYPE),
        ("synthetic-series/../outside", tarfile.REGTYPE),
        ("synthetic-series/symlink", tarfile.SYMTYPE),
        ("synthetic-series/hardlink", tarfile.LNKTYPE),
        ("synthetic-series/device", tarfile.CHRTYPE),
        ("synthetic-series/report.json", tarfile.REGTYPE),
        ("synthetic-series\\outside", tarfile.REGTYPE),
    ],
)
def test_unsafe_archive_members_are_rejected(synthetic, name, kind):
    write, _, _, _ = synthetic
    member = tarfile.TarInfo(name)
    member.type, member.size = kind, 1 if kind == tarfile.REGTYPE else 0
    member.linkname = (
        "report.json" if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE) else ""
    )
    with pytest.raises(ValueError):
        sources.read_verified_series(write(extra=member), "synthetic-series")


@pytest.mark.parametrize(
    "limit", ["MAX_ARCHIVE", "MAX_MEMBER", "MAX_TOTAL", "MAX_MEMBERS"]
)
def test_archive_resource_limits(synthetic, monkeypatch, limit):
    write, _, _, _ = synthetic
    path = write()
    monkeypatch.setattr(sources, limit, 1)
    with pytest.raises(ValueError):
        sources.read_verified_series(path, "synthetic-series")


@pytest.mark.parametrize(
    "mutation",
    [
        lambda m: m.pop("summary.md"),
        lambda m: m.update(extra="0" * 64),
        lambda m: m.update(**{"report.json": "0" * 64}),
    ],
)
def test_root_manifest_must_be_complete_and_exact(synthetic, mutation):
    write, _, _, _ = synthetic

    def change(files):
        manifest = sources.read_json(files["checksums.json"])
        mutation(manifest)
        files["checksums.json"] = sources.json_bytes(manifest)

    with pytest.raises(ValueError, match="manifest"):
        sources.read_verified_series(
            write(manifest_mutation=change), "synthetic-series"
        )


def test_archive_change_after_consumption_is_detected(synthetic):
    write, path, _, _ = synthetic
    result = sources.read_verified_series(write(), "synthetic-series")
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="changed"):
        result.unchanged()


def test_source_validation_can_be_interrupted(synthetic):
    write, _, _, _ = synthetic

    def interrupt():
        raise KeyboardInterrupt("injected interruption")

    with pytest.raises(KeyboardInterrupt):
        sources.read_verified_series(write(), "synthetic-series", check=interrupt)


def test_real_catalog_has_four_complete_plan_rosters():
    catalog = sources.contracts()
    assert [
        len(catalog[name]["cells"])
        for name in (
            "duration-manjaro-004",
            "local-optimizer-manjaro-001",
            "outer-ladder-manjaro-001",
            "transfer-manjaro-001",
        )
    ] == [20, 20, 20, 18]
    for spec in catalog.values():
        evidence = sources._git_file(
            spec["evidence_commit"], spec["evidence_document"]
        ).decode()
        assert spec["archive_sha256"] in evidence
        assert spec["execution_commit"] in evidence
        assert len({cell["number"] for cell in spec["cells"]}) == len(spec["cells"])
        assert all(
            cell["directory"] == f"cell-{cell['number']:02d}" for cell in spec["cells"]
        )


@pytest.mark.parametrize(
    "name,module_name",
    [
        ("duration-manjaro-004", "search_duration"),
        ("local-optimizer-manjaro-001", "local_optimizer"),
        ("outer-ladder-manjaro-001", "outer_search_ladder"),
        ("transfer-manjaro-001", "transfer_check"),
    ],
)
def test_catalog_matches_unchanged_original_plan_functions_and_source_set(
    name, module_name
):
    spec = sources.contracts()[name]
    source_name = "src/ringdown_sr/" + module_name + ".py"
    assert (sources.ROOT / source_name).read_bytes() == sources._git_file(
        spec["execution_commit"], source_name
    )
    # These trusted, unchanged metadata functions create no data, worker or search.
    module = importlib.import_module("ringdown_sr." + module_name)
    assert spec["cells"] == [
        {k: v for k, v in cell.items() if k != "status"}
        for cell in module.planned_cells()
    ]
    assert spec["runtime_sources"] == module.RUNTIME
    assert (
        spec["format"] == module.FORMAT
        and spec["profile_format"] == module.PROFILE_FORMAT
    )
    historical_paths = set(
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", spec["execution_commit"]],
            cwd=sources.ROOT,
        )
        .decode()
        .splitlines()
    )
    names = module.source_hashes().keys() & historical_paths
    hashes = {
        path: sources.sha256(sources._git_file(spec["execution_commit"], path))
        for path in names
    }
    assert len(hashes) == spec["source_count"]
    assert sources.sha256(sources.json_bytes(hashes)) == spec["source_set_sha256"]
    assert (
        sources.sha256(sources._git_file(spec["plan"]["commit"], spec["plan_path"]))
        == spec["plan"]["sha256"]
    )
