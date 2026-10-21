module RingdownSRSearch

using SymbolicRegression
using ..RingdownSRLoss

# A worker binds exactly one context. A second arm requires a fresh process.
const CONTEXT = Ref{Any}(nothing)
const LAST_DATASET = Ref{Any}(nothing)
const LAST_OPTIONS = Ref{Any}(nothing)
const CALLS = Ref(0)

function bind_context(time, observed, covariance)
    CONTEXT[] === nothing || throw(ArgumentError("A search context is already bound."))
    CONTEXT[] = FixedWindowLoss(time, observed; covariance=covariance)
    return nothing
end

function objective(tree, dataset, options, idx=nothing)
    CONTEXT[] === nothing && throw(ArgumentError("No search context is bound."))
    value = CONTEXT[](tree, dataset, options, idx)
    LAST_DATASET[] = dataset
    LAST_OPTIONS[] = options
    CALLS[] += 1
    return value
end

constant(value) = Node{Float64}(; val=value)
variable(index) = Node{Float64}(; feature=index)
unary(index, child) = Node{Float64}(; op=index, l=child)
binary(index, left, right) = Node{Float64}(; op=index, l=left, r=right)

function replay(tree, options)
    loss = candidate_loss(CONTEXT[], tree, options)
    isfinite(loss) || throw(ArgumentError("Exported expression is not admissible."))
    prediction, complete = eval_tree_array(tree, CONTEXT[]._dataset.X, options)
    complete || throw(ArgumentError("Exported expression cannot be evaluated."))
    return prediction, loss
end

# No abbreviated show output: record every effective backend field separately.
option_fields(options) = [
    (name=string(name), type=string(typeof(getfield(options, name))),
     value=repr(getfield(options, name); context=:limit => false))
    for name in fieldnames(typeof(options))
]

end
