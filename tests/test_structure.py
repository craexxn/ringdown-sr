"""Independent exact references and input contracts for structural recognition."""

import copy
import itertools
import json
import math
import subprocess
import sys
from dataclasses import FrozenInstanceError
from fractions import Fraction

import pytest

from ringdown_sr import structure, symbolic
from ringdown_sr.structure import InvalidTreeError, recognize_ringdown


def constant(value):
    return {"kind": "constant", "value_hex": float(value).hex()}


def time_node():
    return {"kind": "variable", "index": 1}


def operator(name, *children):
    names = ("exp", "sin", "cos") if len(children) == 1 else ("+", "-", "*", "/")
    return {
        "kind": "operator",
        "operator": name,
        "arity": len(children),
        "operator_index": names.index(name) + 1,
        "children": list(children),
    }


def product(*factors):
    result = factors[0]
    for factor in factors[1:]:
        result = operator("*", result, factor)
    return result


def model(*, amplitude=2, exponential=None, oscillation=None):
    exponential = (
        operator("*", constant(-125), time_node())
        if exponential is None
        else exponential
    )
    oscillation = (
        operator("+", operator("*", constant(512), time_node()), constant(0.25))
        if oscillation is None
        else oscillation
    )
    factors = [operator("exp", exponential), operator("cos", oscillation)]
    if amplitude is not None:
        factors.insert(
            0, amplitude if isinstance(amplitude, dict) else constant(amplitude)
        )
    return product(*factors)


def coefficients(result):
    raw = result.coefficients
    assert raw is not None
    return (
        raw.amplitude,
        raw.exponential_rate_per_s,
        raw.angular_frequency_per_s,
        raw.phase_rad,
    )


def test_grammar_contract_matches_the_pinned_search_export():
    assert structure._BINARY == symbolic.BINARY
    assert structure._UNARY == symbolic.UNARY
    assert (
        structure.MAX_TREE_NODES
        == symbolic.search_parameters(symbolic.SearchBudget())["maxsize"]
    )


def test_basic_reference_and_strict_json_do_not_derive_parameters():
    result = recognize_ringdown(model())
    assert result.structure_status == "recognized" and result.reason is None
    assert coefficients(result) == (
        Fraction(2),
        Fraction(-125),
        Fraction(512),
        Fraction(1, 4),
    )
    report = result.to_dict()
    assert report["raw_coefficients"] == {
        "A": {"numerator": "2", "denominator": "1"},
        "b": {"numerator": "-125", "denominator": "1"},
        "c": {"numerator": "512", "denominator": "1"},
        "d": {"numerator": "1", "denominator": "4"},
    }
    assert (
        report["exponential_status"] == "decaying"
        and report["amplitude_status"] == "nonzero"
    )
    assert report["phase_kind"] == "radian_rational"
    assert (
        report["replay_status"]
        == report["alias_status"]
        == report["parameter_interpretation"]
        == "not_attempted"
    )
    assert report["physical_identification"] == "not_assessed"
    assert "frequency_hz" not in report and "decay_time_s" not in report
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize("permutation", list(itertools.permutations(range(3))))
@pytest.mark.parametrize("right_grouped", [False, True])
def test_factor_order_and_grouping_have_the_same_exact_coefficients(
    permutation, right_grouped
):
    base = model()
    factors = [constant(2), base["children"][0]["children"][1], base["children"][1]]
    first, second, third = [factors[i] for i in permutation]
    tree = (
        operator("*", first, operator("*", second, third))
        if right_grouped
        else product(first, second, third)
    )
    assert coefficients(recognize_ringdown(tree)) == (2, -125, 512, Fraction(1, 4))


def test_affine_reference_without_prefactor_fits_the_search_size_contract():
    exponential = operator(
        "-",
        operator("*", constant(-100), time_node()),
        operator("*", constant(25), time_node()),
    )
    oscillation = operator(
        "+",
        operator(
            "+",
            operator("*", constant(256), time_node()),
            operator("*", constant(256), time_node()),
        ),
        constant(0.25),
    )
    result = recognize_ringdown(
        model(amplitude=None, exponential=exponential, oscillation=oscillation)
    )
    assert coefficients(result) == (1, -125, 512, Fraction(1, 4))


def test_affine_division_and_shifted_argument_have_hand_derived_coefficients():
    exponential = operator(
        "/",
        operator("*", constant(-250), time_node()),
        operator("-", constant(3), constant(1)),
    )
    oscillation = operator("*", operator("+", time_node(), constant(1)), constant(-512))
    assert coefficients(
        recognize_ringdown(model(exponential=exponential, oscillation=oscillation))
    ) == (2, -125, -512, -512)


def test_affine_denominator_can_be_exactly_constant_after_linear_cancellation():
    denominator = operator("+", operator("-", time_node(), time_node()), constant(2))
    result = recognize_ringdown(
        model(exponential=operator("/", time_node(), denominator))
    )
    assert coefficients(result) == (2, Fraction(1, 2), 512, Fraction(1, 4))
    assert result.to_dict()["exponential_status"] == "growing"


def test_rational_scalar_arithmetic_and_phase_are_not_rounded():
    amplitude = operator(
        "/",
        operator("-", constant(9), constant(3)),
        operator("+", constant(2), constant(1)),
    )
    assert coefficients(recognize_ringdown(model(amplitude=amplitude))) == (
        2,
        -125,
        512,
        Fraction(1, 4),
    )
    phase = operator(
        "+",
        operator("*", constant(512), time_node()),
        operator("/", constant(1), constant(3)),
    )
    assert coefficients(recognize_ringdown(model(oscillation=phase)))[3] == Fraction(
        1, 3
    )


def test_decimal_constant_retains_its_binary_value_instead_of_becoming_one_tenth():
    actual = recognize_ringdown(model(amplitude=0.1))
    expected = Fraction(3602879701896397, 36028797018963968)
    assert coefficients(actual)[0] == expected and expected != Fraction(1, 10)


def test_float_pi_phase_is_never_promoted_to_an_exact_pi_multiple():
    phase = operator("+", operator("*", constant(512), time_node()), constant(math.pi))
    result = recognize_ringdown(model(oscillation=phase))
    assert coefficients(result)[3] == Fraction(*math.pi.as_integer_ratio())
    assert result.to_dict()["phase_kind"] == "radian_rational"
    assert result.to_dict()["alias_status"] == "not_attempted"


@pytest.mark.parametrize(
    "rate,status", [(-125, "decaying"), (0, "undamped"), (125, "growing")]
)
@pytest.mark.parametrize(
    "amplitude,amplitude_status", [(-2, "nonzero"), (0, "zero"), (1e-21, "nonzero")]
)
def test_form_and_amplitude_states_use_exact_signs(
    rate, status, amplitude, amplitude_status
):
    result = recognize_ringdown(
        model(
            amplitude=amplitude, exponential=operator("*", constant(rate), time_node())
        )
    )
    assert coefficients(result)[0] == Fraction.from_float(float(amplitude))
    assert coefficients(result)[1] == rate
    assert result.to_dict()["exponential_status"] == status
    assert result.to_dict()["amplitude_status"] == amplitude_status
    assert result.to_dict()["physical_identification"] == "not_assessed"


def test_zero_frequency_and_missing_phase_remain_raw_coefficients():
    result = recognize_ringdown(model(exponential=constant(0), oscillation=constant(0)))
    assert coefficients(result) == (2, 0, 0, 0)
    assert result.to_dict()["alias_status"] == "not_attempted"


@pytest.mark.parametrize("factor", [1e-300, 1e300])
def test_exact_amplitude_products_can_exceed_float64_range_without_conversion(factor):
    amplitude = operator("*", constant(factor), constant(factor))
    result = recognize_ringdown(model(amplitude=amplitude))
    expected = Fraction.from_float(factor) ** 2
    assert coefficients(result)[0] == expected and expected > 0
    assert result.to_dict()["amplitude_status"] == "nonzero"
    if factor < 1:
        assert float(expected) == 0
    else:
        assert expected > Fraction.from_float(sys.float_info.max)
    json.dumps(result.to_dict(), allow_nan=False)


@pytest.mark.parametrize("association", ["left", "right"])
def test_real_coefficient_extraction_does_not_claim_float64_replay(association):
    first, second, third = constant(1e16), constant(-1e16), constant(1)
    coefficient = (
        operator("+", operator("+", first, second), third)
        if association == "left"
        else operator("+", first, operator("+", second, third))
    )
    tree = model(exponential=operator("*", coefficient, time_node()))
    result = recognize_ringdown(tree)
    assert coefficients(result)[1] == 1
    prediction = symbolic.evaluate_tree(tree, [0.001])
    expected_rate = 1 if association == "left" else 0
    expected = 2 * math.exp(expected_rate * 0.001) * math.cos(512 * 0.001 + 0.25)
    assert math.isclose(float(prediction[0]), expected, rel_tol=1e-14, abs_tol=0)
    assert result.to_dict()["replay_status"] == "not_attempted"


@pytest.mark.parametrize(
    "tree,reason",
    [
        (constant(0), "exponential_factor_count"),
        (operator("+", model(), constant(0)), "exponential_factor_count"),
        (
            product(operator("exp", constant(0)), operator("sin", time_node())),
            "cosine_factor_count",
        ),
        (
            product(
                operator("exp", constant(0)),
                operator("cos", time_node()),
                operator("cos", time_node()),
            ),
            "cosine_factor_count",
        ),
        (
            product(
                operator("exp", constant(0)),
                operator("exp", constant(0)),
                operator("cos", time_node()),
            ),
            "exponential_factor_count",
        ),
        (operator("/", model(), constant(2)), "exponential_factor_count"),
        (
            model(
                exponential=operator(
                    "+", operator("*", constant(-125), time_node()), constant(1)
                )
            ),
            "nonzero_exponential_intercept",
        ),
        (
            model(exponential=operator("*", time_node(), time_node())),
            "non_affine_product",
        ),
        (
            model(oscillation=operator("/", time_node(), time_node())),
            "time_dependent_denominator",
        ),
        (
            model(oscillation=operator("sin", time_node())),
            "unsupported_affine_operator",
        ),
        (model(amplitude=time_node()), "non_scalar_outer_factor"),
        (
            model(
                amplitude=operator(
                    "+", operator("-", time_node(), time_node()), constant(2)
                )
            ),
            "non_scalar_outer_factor",
        ),
        (model(amplitude=operator("/", constant(1), constant(0))), "zero_denominator"),
        (
            model(amplitude=0, exponential=operator("/", time_node(), constant(0))),
            "zero_denominator",
        ),
        (
            model(amplitude=0, exponential=operator("*", time_node(), time_node())),
            "non_affine_product",
        ),
    ],
)
def test_valid_unsupported_structures_have_reasons_without_inferred_coefficients(
    tree, reason
):
    result = recognize_ringdown(tree)
    assert result.structure_status == "not_supported" and result.reason == reason
    assert result.coefficients is None
    report = result.to_dict()
    assert (
        report["raw_coefficients"]
        is report["amplitude_status"]
        is report["exponential_status"]
        is report["phase_kind"]
        is None
    )
    assert report["replay_status"] == "not_attempted"
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize(
    "node",
    [
        None,
        [],
        "expression",
        {},
        {"kind": "other"},
        {"kind": "constant"},
        {"kind": "constant", "value_hex": True},
        {"kind": "constant", "value_hex": "1.0"},
        {"kind": "constant", "value_hex": "nan"},
        {"kind": "constant", "value_hex": "inf"},
        {"kind": "constant", "value_hex": "0x1p+9000"},
        {"kind": "constant", "value_hex": "0x1.00000000000001p+0"},
        constant(1) | {"children": []},
        {"kind": "variable"},
        {"kind": "variable", "index": True},
        {"kind": "variable", "index": 1.0},
        {"kind": "variable", "index": 2},
        time_node() | {"value_hex": "0x0.0p+0"},
        operator("cos", constant(0)) | {"arity": True},
        operator("cos", constant(0)) | {"arity": 1.0},
        operator("cos", constant(0)) | {"arity": 3},
        operator("cos", constant(0)) | {"operator_index": True},
        operator("cos", constant(0)) | {"operator_index": 0},
        operator("cos", constant(0)) | {"operator_index": 4},
        operator("cos", constant(0)) | {"operator_index": 1},
        operator("cos", constant(0)) | {"operator": "unknown"},
        operator("cos", constant(0)) | {"operator": ["cos"]},
        operator("cos", constant(0)) | {"children": []},
        operator("cos", constant(0)) | {"children": [constant(0), constant(1)]},
        operator("cos", constant(0)) | {"children": (constant(0),)},
        operator("cos", constant(0)) | {"extra": 1},
    ],
)
def test_malformed_inputs_raise_instead_of_becoming_unsupported(node):
    with pytest.raises(InvalidTreeError):
        recognize_ringdown(node)


@pytest.mark.parametrize("amplitude", [0, 2])
def test_malformed_children_are_validated_before_any_pattern_or_zero_shortcut(
    amplitude,
):
    tree = operator("+", model(amplitude=amplitude), {"kind": "variable", "index": 2})
    with pytest.raises(InvalidTreeError, match="index 1"):
        recognize_ringdown(tree)


def test_size_limit_counts_occurrences_and_accepts_twenty_before_rejecting_twenty_one():
    tree = product(constant(1), constant(1), constant(1), model())
    # 13 base nodes + 3*(one constant + one product) = 19.
    unsupported_twenty = operator("sin", tree)
    assert recognize_ringdown(unsupported_twenty).structure_status == "not_supported"
    with pytest.raises(InvalidTreeError, match="20-node"):
        recognize_ringdown(operator("sin", unsupported_twenty))


def test_cycle_cannot_cause_unbounded_recursion():
    node = operator("cos", constant(0))
    node["children"][0] = node
    with pytest.raises(InvalidTreeError, match="20-node"):
        recognize_ringdown(node)


def test_input_bits_and_structure_are_unchanged_and_results_are_immutable():
    tree = model(amplitude=-2, oscillation=constant(-0.0))
    before = copy.deepcopy(tree)
    result = recognize_ringdown(tree)
    assert (
        tree == before
        and tree["children"][1]["children"][0]["value_hex"] == "-0x0.0p+0"
    )
    assert coefficients(result) == (-2, -125, 0, 0)
    with pytest.raises(FrozenInstanceError):
        result.coefficients.amplitude = Fraction(99)
    with pytest.raises(FrozenInstanceError):
        result.coefficients = None
    report = result.to_dict()
    report["raw_coefficients"]["A"]["numerator"] = "99"
    tree["children"][0]["children"][0]["value_hex"] = float(99).hex()
    assert coefficients(result)[0] == -2


def test_module_import_needs_no_numerical_or_search_runtime():
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import ringdown_sr.structure; assert not {'pysr', 'juliacall', 'numpy', 'scipy', 'sympy'}.intersection(sys.modules)",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
