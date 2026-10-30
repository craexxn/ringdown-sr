"""Restricted search-profile changes; no truth, data generation or free overrides."""

import copy
from pathlib import Path

from .pilot import _sha256
from .symbolic import ROOT
from .symbolic import search_parameters as _ordinary_parameters

PROFILE_FORMAT = "ringdown-sr-representation-profile-1"
OBJECTIVE = "Main.RepresentationProfiles.objective"
CONDITIONS = ("baseline", "time_stretch", "complexity_frequency")
RUNTIME_FILES = {
    "driver.py": "scripts/repeat_symbolic_arm.py",
    "probe_symbolic_numerics.py": "scripts/probe_symbolic_numerics.py",
    "run_representation_worker.py": "scripts/run_representation_worker.py",
    "check_representation_backend.py": "scripts/check_representation_backend.py",
    "check_representation_references.py": "scripts/check_representation_references.py",
    "orchestrator.py": "scripts/run_representation_control.py",
}


def source_hashes():
    """Cover every consumed module, runtime copy, native source and frozen pin."""
    names = {
        *RUNTIME_FILES.values(),
        "scripts/run_noiseless_control.py",
        "scripts/check_representation_integration.py",
        "scripts/run_python.py",
        "scripts/run_symbolic_worker.py",
        "docs/search_representation_plan.md",
        "docs/noiseless_control_plan.md",
        "pyproject.toml",
        "uv.lock",
        ".python-version",
        "src/ringdown_sr/juliapkg.json",
        "julia/Project.toml",
        "julia/Manifest.toml",
    }
    names.update(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src/ringdown_sr").glob("*.py")
    )
    names.update(
        path.relative_to(ROOT).as_posix() for path in (ROOT / "julia/src").glob("*.jl")
    )
    return {name: _sha256((ROOT / name).read_bytes()) for name in sorted(names)}


def verify_manifest(manifest, directory, runtime):
    """Check source and input bytes before consumption and again after the worker."""
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"format", "sources", "runtime", "inputs"}
        or manifest["format"] != "ringdown-sr-representation-manifest-1"
        or manifest["sources"] != source_hashes()
        or set(manifest["runtime"]) != set(RUNTIME_FILES)
        or set(manifest["inputs"])
        != {"request.json", "inputs.npz", "representation_profile.json"}
    ):
        raise ValueError("Invalid or changed representation worker manifest.")
    for name, source in RUNTIME_FILES.items():
        if manifest["runtime"][name] != manifest["sources"][source]:
            raise ValueError("Runtime copy does not match its source manifest.")
    for root, hashes in (
        (Path(runtime), manifest["runtime"]),
        (Path(directory), manifest["inputs"]),
    ):
        for name, digest in hashes.items():
            path = root / name
            if path.is_symlink() or _sha256(path.read_bytes()) != digest:
                raise ValueError(f"Changed representation consumed file: {name}")


def plugin_field_record(record):
    return {"type": str(record.type), "value": str(record.value)}


def plugin_records(records):
    return [
        {
            "type": str(plugin.type),
            "fields": [
                {
                    "name": str(field.name),
                    "type": str(field.type),
                    "value": str(field.value),
                }
                for field in plugin.fields
            ],
        }
        for plugin in records
    ]


def checked_profile(document):
    if (
        not isinstance(document, dict)
        or set(document) != {"format", "condition"}
        or document["format"] != PROFILE_FORMAT
        or document["condition"] not in CONDITIONS
    ):
        raise ValueError("Invalid restricted representation profile.")
    return document["condition"]


def profile_parameters(budget, condition):
    """Use the same verification wrapper for all three fresh-search conditions."""
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    parameters = _ordinary_parameters(budget)
    parameters.update(
        loss_function=OBJECTIVE,
        use_frequency=condition == "complexity_frequency",
        use_frequency_in_tournament=condition == "complexity_frequency",
    )
    return parameters


def validate_plugin_records(records, condition):
    """Check structured plugin configuration against the pinned source contract."""
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    specs = [
        ("SimulatedAnnealingPlugin", {"alpha": ("Float64", 3.17)}),
        (
            "AdaptiveMutationWeightsPlugin",
            {
                "smoothing": ("Float64", 0.02),
                "floor": ("Float64", 0.05),
                "reward": ("Symbol", ":cost"),
                "adaptation_strength": ("Float64", 0.5),
            },
        ),
    ]
    if condition == "complexity_frequency":
        specs.insert(
            1,
            (
                "AdaptiveParsimonyPlugin",
                {
                    "tournament": ("Bool", "true"),
                    "mutation_acceptance": ("Bool", "true"),
                },
            ),
        )
    if not isinstance(records, list) or len(records) != len(specs):
        raise ValueError("Unexpected actual plugin count.")
    for record, (name, expected) in zip(records, specs, strict=True):
        if (
            not isinstance(record, dict)
            or set(record) != {"type", "fields"}
            or not isinstance(record["type"], str)
            or not isinstance(record["fields"], list)
            or any(
                not isinstance(field, dict)
                or set(field) != {"name", "type", "value"}
                or any(not isinstance(value, str) for value in field.values())
                for field in record["fields"]
            )
        ):
            raise ValueError("Invalid actual plugin record schema.")
        if record["type"].split("{", 1)[0].rsplit(".", 1)[-1] != name:
            raise ValueError("Unexpected actual plugin type/order.")
        fields = {field["name"]: field for field in record["fields"]}
        if len(fields) != len(record["fields"]) or set(fields) != set(expected):
            raise ValueError("Unexpected actual plugin fields.")
        for key, (kind, value) in expected.items():
            field = fields[key]
            if field["type"] != kind:
                raise ValueError("Unexpected actual plugin field type.")
            try:
                actual = float(field["value"]) if kind == "Float64" else field["value"]
            except (TypeError, ValueError) as error:
                raise ValueError("Invalid actual plugin field value.") from error
            if actual != value:
                raise ValueError("Unexpected actual plugin field value.")
    return {"status": "passed", "plugin_count": len(specs)}


def normalized_backend_fields(fields, condition, expected_plugins):
    """Normalize only individually verified planned differences for old contracts.

    Original fields are never changed. The full plugin field must match the
    genuine preflight object for this condition; it is not simply discarded.
    """
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    by_name = {field["name"]: field for field in fields}
    if len(by_name) != len(fields):
        raise ValueError("Duplicate backend option name.")
    enabled = str(condition == "complexity_frequency").lower()
    for name in ("use_frequency", "use_frequency_in_tournament"):
        if by_name.get(name) != {"name": name, "type": "Bool", "value": enabled}:
            raise ValueError(f"Representation backend mismatch: {name}")
    objective = by_name.get("loss_function")
    if objective != {
        "name": "loss_function",
        "type": f"typeof({OBJECTIVE})",
        "value": OBJECTIVE,
    }:
        short = OBJECTIVE.removeprefix("Main.")
        if objective != {
            "name": "loss_function",
            "type": f"typeof({short})",
            "value": short,
        }:
            raise ValueError("Representation backend mismatch: loss_function")
    plugins = by_name.get("plugins")
    if (
        plugins is None
        or {key: plugins[key] for key in ("type", "value")} != expected_plugins
    ):
        raise ValueError("Representation backend mismatch: actual plugin configuration")
    normalized = copy.deepcopy(fields)
    for field in normalized:
        if field["name"] in ("use_frequency", "use_frequency_in_tournament"):
            field["value"] = "false"
        elif field["name"] == "loss_function":
            field.update(
                type="typeof(Main.RingdownSRSearch.objective)",
                value="Main.RingdownSRSearch.objective",
            )
    return normalized
