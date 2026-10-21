module RingdownSRLoss

using LinearAlgebra: LowerTriangular, PosDefException, Symmetric, cholesky, issymmetric, norm
using SymbolicRegression:
    AbstractExpression, AbstractExpressionNode, Dataset, eval_tree_array, get_tree, tree_mapreduce
using SymbolicRegression.CoreModule: get_indices
using SymbolicRegression.DimensionalAnalysisModule: violates_dimensional_constraints

export FixedWindowLoss, candidate_loss, residual_loss, n_samples

function _real_array(values, name::String, dimensions::Int)
    values isa AbstractArray && ndims(values) == dimensions ||
        throw(ArgumentError("$name must be a $dimensions-dimensional real array."))
    Base.require_one_based_indexing(values)
    all(x -> x isa Real && !(x isa Bool), values) ||
        throw(ArgumentError("$name must contain real numbers, excluding booleans."))
    # Materialize ranges and views into owned dense arrays too.
    converted = try
        collect(Float64, values)
    catch error
        if error isa InexactError || error isa OverflowError || error isa ArgumentError
            throw(ArgumentError("$name cannot be represented as finite Float64 values."))
        end
        rethrow()
    end
    all(isfinite, converted) ||
        throw(ArgumentError("$name must contain finite Float64 values."))
    return converted
end

function _factor(covariance, n::Int)
    covariance === nothing && return nothing
    matrix = _real_array(covariance, "covariance", 2)
    size(matrix) == (n, n) ||
        throw(ArgumentError("covariance dimensions must match the full window."))
    issymmetric(matrix) ||
        throw(ArgumentError("covariance must be exactly symmetric."))
    factor = try
        cholesky(Symmetric(matrix); check=true)
    catch error
        error isa PosDefException || rethrow()
        throw(ArgumentError("covariance must be positive definite."))
    end
    lower = LowerTriangular(Matrix(factor.L))
    all(isfinite, lower) ||
        throw(ArgumentError("The covariance factor must be finite."))
    return lower
end

"""
    FixedWindowLoss(time_s, observed; covariance=nothing)

Copy one finite, nonempty window into a Float64 dataset with time in seconds
and dimensionless output. Cache a lower Cholesky factor when covariance is
supplied. No centering, normalization, regularization or resampling is done.

The dataset and factor fields are internal implementation details. Public
operations do not mutate them. Use a separate instance for each weighting.
"""
struct FixedWindowLoss{D,F} <: Function
    _dataset::D
    _factor::F

    function FixedWindowLoss(time_s, observed; covariance=nothing)
        time = _real_array(time_s, "time_s", 1)
        target = _real_array(observed, "observed", 1)
        !isempty(time) && length(time) == length(target) ||
            throw(ArgumentError("time_s and observed must have the same nonzero length."))
        all(x -> x >= 0, time) ||
            throw(ArgumentError("time_s must be nonnegative."))
        factor = _factor(covariance, length(time))
        dataset = Dataset(
            reshape(time, 1, length(time)), target, Float64;
            variable_names=["t"], X_units=["s"], y_units="1",
        )
        return new{typeof(dataset),typeof(factor)}(dataset, factor)
    end
end

n_samples(objective::FixedWindowLoss) = objective._dataset.n

function _mean_squared(objective::FixedWindowLoss, residual::Vector{Float64})
    transformed = if objective._factor === nothing
        residual
    else
        objective._factor \ residual
    end
    all(isfinite, transformed) ||
        throw(OverflowError("The whitened residual exceeds the Float64 range."))
    scaled_norm = norm(transformed) / sqrt(n_samples(objective))
    value = scaled_norm * scaled_norm
    isfinite(value) ||
        throw(OverflowError("The mean-squared loss exceeds the Float64 range."))
    return value
end

"""
    residual_loss(objective, residual)

Return ordinary MSE or Q/N for a supplied residual in the fixed sample order.
Invalid residual inputs raise ArgumentError; numerical range failures raise
OverflowError. This numeric reference path does not perform expression units
analysis. Candidate evaluation uses candidate_loss instead.
"""
function residual_loss(objective::FixedWindowLoss, residual)
    values = _real_array(residual, "residual", 1)
    length(values) == n_samples(objective) ||
        throw(ArgumentError("residual length must match the full window."))
    return _mean_squared(objective, values)
end

function _checked_tree(tree, options)
    root = tree isa AbstractExpression ? get_tree(tree) : tree
    root isa AbstractExpressionNode{Float64} ||
        throw(ArgumentError("The expression must use Float64 nodes."))

    # Validate indices before backend routines that use unchecked array access.
    leaf(node) = if node.constant
        isfinite(node.val)
    else
        node.feature == 1 ||
            throw(ArgumentError("The expression may only use the time feature."))
        true
    end
    function branch(node)
        degree = Int(node.degree)
        1 <= degree <= length(options.operators.ops) ||
            throw(ArgumentError("The expression has an unsupported operator arity."))
        1 <= Int(node.op) <= length(options.operators.ops[degree]) ||
            throw(ArgumentError("The expression has an invalid operator index."))
        return true
    end
    finite = tree_mapreduce(
        leaf, branch, (valid, children...) -> valid && all(children), root;
        break_sharing=Val(true),
    )
    return root, finite
end

"""
    candidate_loss(objective, tree, options)

Check expression dimensions explicitly, evaluate all original time points,
and return ordinary MSE or Q/N of observed minus prediction. Invalid
dimensions, nonfinite candidates and numerical range failures return Inf.
Malformed trees and programming errors propagate instead of becoming Inf.
"""
function candidate_loss(objective::FixedWindowLoss, tree, options)
    root, finite = _checked_tree(tree, options)
    finite || return Inf
    dataset = objective._dataset
    try
        violates_dimensional_constraints(root, dataset, options) && return Inf
        prediction, complete = eval_tree_array(root, dataset.X, options)
        (!complete || prediction === nothing) && return Inf
        prediction isa AbstractVector ||
            throw(ArgumentError("The expression must return a prediction vector."))
        length(prediction) == dataset.n ||
            throw(ArgumentError("The prediction must cover the full window."))
        all(x -> x isa Real && isfinite(x), prediction) || return Inf
        residual = dataset.y - prediction
        all(isfinite, residual) || return Inf
        return _mean_squared(objective, residual)
    catch error
        # Only numeric candidate failures are converted to an infinite loss.
        if error isa DomainError || error isa OverflowError
            return Inf
        end
        rethrow()
    end
end

function _check_dataset(objective::FixedWindowLoss, dataset)
    dataset isa Dataset{Float64,Float64} ||
        throw(ArgumentError("The callback requires a Float64 regression dataset."))
    get_indices(dataset) === nothing ||
        throw(ArgumentError("Batched datasets are not supported by the full covariance."))
    expected = objective._dataset
    dataset.weights === nothing ||
        throw(ArgumentError("Per-sample weights must not be combined with this objective."))
    dataset.n == expected.n && dataset.nfeatures == 1 ||
        throw(ArgumentError("The callback requires the complete single-feature window."))
    isequal(dataset.X, expected.X) && isequal(dataset.y, expected.y) ||
        throw(ArgumentError("The callback dataset or its sample order has changed."))
    isequal(dataset.X_units, expected.X_units) &&
        isequal(dataset.y_units, expected.y_units) ||
        throw(ArgumentError("The callback requires seconds and dimensionless output."))
    return nothing
end

"""
    objective(tree, dataset, options)
    objective(tree, dataset, options, idx)

Full-loss callback. Reject changed, weighted or batched datasets before
evaluating any candidate. The four-argument backend interface rejects every
idx other than nothing, including indices covering the complete window.
With idx=nothing it delegates to the three-argument callback. The future
PySR adapter must bind this instance in its isolated process and explicitly
disable batching.
"""
function (objective::FixedWindowLoss)(tree, dataset, options)
    _check_dataset(objective, dataset)
    return candidate_loss(objective, tree, options)
end

function (objective::FixedWindowLoss)(tree, dataset, options, idx)
    idx === nothing ||
        throw(ArgumentError("Explicit batch indices are not supported by the full covariance."))
    return objective(tree, dataset, options)
end

end
