"""Restricted profiles retain ordinary policy and reject forged effective fields."""

import copy

import pytest
from test_noiseless_control import BACKEND_SEEDS, DRIVER, backend_fixture

from ringdown_sr.config import SearchBudget
from ringdown_sr.representation_profiles import (
    CONDITIONS,
    OBJECTIVE,
    PROFILE_FORMAT,
    checked_profile,
    normalized_backend_fields,
    profile_parameters,
)
from ringdown_sr.symbolic import search_parameters

PLUGINS = {
    "baseline": {
        "type": "Tuple{SimulatedAnnealingPlugin,AdaptiveMutationWeightsPlugin}",
        "value": "(annealing,weights)",
    },
    "complexity_frequency": {
        "type": "Tuple{SimulatedAnnealingPlugin,AdaptiveParsimonyPlugin,AdaptiveMutationWeightsPlugin}",
        "value": "(annealing,parsimony(true,true),weights)",
    },
}
PLUGINS["time_stretch"] = copy.deepcopy(PLUGINS["baseline"])


def fields(condition, seed):
    result = backend_fixture(seed)
    for field in result:
        if field["name"] in ("use_frequency", "use_frequency_in_tournament"):
            field["value"] = str(condition == "complexity_frequency").lower()
        elif field["name"] == "loss_function":
            field.update(type=f"typeof({OBJECTIVE})", value=OBJECTIVE)
    result.append({"name": "plugins", **PLUGINS[condition]})
    return result


@pytest.mark.parametrize("condition", CONDITIONS)
def test_profiles_only_change_common_guard_and_two_frequency_flags(condition):
    budget = SearchBudget(seed=20261020, niterations=200)
    before = search_parameters(budget)
    result = profile_parameters(budget, condition)
    changed = {key for key in before if before[key] != result[key]}
    expected = (
        {"loss_function", "use_frequency", "use_frequency_in_tournament"}
        if condition == "complexity_frequency"
        else {"loss_function"}
    )
    assert changed == expected
    assert result["guesses"] is None and result["warm_start"] is False
    assert result["loss_function"] == OBJECTIVE
    assert search_parameters(budget) == before


@pytest.mark.parametrize(
    "document",
    [
        {},
        {"format": PROFILE_FORMAT, "condition": "combined"},
        {"format": PROFILE_FORMAT, "condition": "baseline", "guesses": ["truth"]},
        {"format": PROFILE_FORMAT, "condition": "baseline", "overrides": {}},
        {"format": "other", "condition": "baseline"},
    ],
)
def test_no_free_overrides_or_truth_fields_can_enter_profile(document):
    with pytest.raises(ValueError):
        checked_profile(document)


@pytest.mark.parametrize("condition", CONDITIONS)
@pytest.mark.parametrize("seed", [20261020, 20261021, 20261022])
def test_common_contracts_still_check_all_profile_seeds_without_mutation(
    condition, seed
):
    original = fields(condition, seed)
    before = copy.deepcopy(original)
    normalized = normalized_backend_fields(original, condition, PLUGINS[condition])
    verified = DRIVER.verify_backend_policy(
        normalized,
        {
            "seed": seed,
            "niterations": 200,
            "populations": 2,
            "population_size": 32,
            "ncycles_per_iteration": 50,
        },
        {"python_seed": seed, "backend_seed": BACKEND_SEEDS[seed]},
        DRIVER.load_support(),
    )
    assert verified["status"] == "passed" and len(verified["checked_fields"]) == 29
    assert original == before


@pytest.mark.parametrize(
    "fault", ["flags", "flag_type", "objective", "plugins", "duplicate"]
)
def test_forged_profile_flags_objective_or_plugins_fail_even_with_consistent_fields(
    fault,
):
    values = fields("complexity_frequency", 20261020)
    if fault in ("flags", "flag_type"):
        item = next(x for x in values if x["name"] == "use_frequency")
        item["value" if fault == "flags" else "type"] = (
            "false" if fault == "flags" else "String"
        )
    elif fault == "objective":
        next(x for x in values if x["name"] == "loss_function")["value"] = (
            "Main.RingdownSRSearch.objective"
        )
    elif fault == "plugins":
        next(x for x in values if x["name"] == "plugins").update(PLUGINS["baseline"])
    else:
        values.append(copy.deepcopy(values[0]))
    with pytest.raises(ValueError):
        normalized_backend_fields(
            values, "complexity_frequency", PLUGINS["complexity_frequency"]
        )


def plugin_fixture(condition):
    specs = [
        ("SimulatedAnnealingPlugin{Float64}", [("alpha", "Float64", "3.17")]),
        (
            "AdaptiveMutationWeightsPlugin{Float64}",
            [
                ("smoothing", "Float64", "0.02"),
                ("floor", "Float64", "0.05"),
                ("reward", "Symbol", ":cost"),
                ("adaptation_strength", "Float64", "0.5"),
            ],
        ),
    ]
    if condition == "complexity_frequency":
        specs.insert(
            1,
            (
                "AdaptiveParsimonyPlugin",
                [
                    ("tournament", "Bool", "true"),
                    ("mutation_acceptance", "Bool", "true"),
                ],
            ),
        )
    return [
        {
            "type": name,
            "fields": [
                {"name": key, "type": kind, "value": value}
                for key, kind, value in fields
            ],
        }
        for name, fields in specs
    ]


@pytest.mark.parametrize("condition", CONDITIONS)
def test_absolute_plugin_contracts(condition):
    from ringdown_sr.representation_profiles import validate_plugin_records

    records = plugin_fixture(condition)
    before = copy.deepcopy(records)
    assert validate_plugin_records(records, condition)["status"] == "passed"
    assert records == before


@pytest.mark.parametrize("condition", CONDITIONS)
@pytest.mark.parametrize(
    "fault",
    [
        "missing_plugin",
        "extra_plugin",
        "order",
        "type",
        "missing_field",
        "extra_field",
        "duplicate_field",
        "field_type",
        "field_value",
        "nan",
        "infinity",
        "bad_number",
        "schema",
        "typed_value",
        "flags",
    ],
)
def test_absolute_plugin_validation_rejects_consistent_forgery(condition, fault):
    from ringdown_sr.representation_profiles import validate_plugin_records

    records = plugin_fixture(condition)
    fields = records[0]["fields"]
    if fault == "missing_plugin":
        records.pop()
    elif fault == "extra_plugin":
        records.append(copy.deepcopy(records[0]))
    elif fault == "order":
        records.reverse()
    elif fault == "type":
        records[0]["type"] = "UnreviewedPlugin"
    elif fault == "missing_field":
        fields.clear()
    elif fault == "extra_field":
        fields.append({"name": "secret", "type": "Bool", "value": "true"})
    elif fault == "duplicate_field":
        fields.append(copy.deepcopy(fields[0]))
    elif fault == "field_type":
        fields[0]["type"] = "Float32"
    elif fault in ("field_value", "nan", "infinity", "bad_number", "typed_value"):
        fields[0]["value"] = {
            "field_value": "3.18",
            "nan": "NaN",
            "infinity": "Inf",
            "bad_number": "oops",
            "typed_value": 3.17,
        }[fault]
    elif fault == "schema":
        fields[0].pop("value")
    else:
        if condition == "complexity_frequency":
            records[1]["fields"][0]["value"] = "false"
        else:
            records = plugin_fixture("complexity_frequency")
    with pytest.raises(ValueError):
        validate_plugin_records(records, condition)
