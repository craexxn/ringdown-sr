module WhiteLossScaling

using LinearAlgebra: Diagonal
using Random: AbstractRNG, Xoshiro
import Random
using SymbolicRegression
using SymbolicRegression: get_scalar_constants
using ..RingdownSRLoss
using ..RingdownSRSearch
using ..RepresentationProfiles
using ..SearchTimeBudget

const Backend = SymbolicRegression.ConstantOptimizationModule
const Optim = Backend.Optim
const REQUEST = Ref{Any}(nothing)
const VERIFIED_OPTIONS = Ref{Any}(nothing)
const ARMS = ("ordinary", "scaled", "covariance")

"""Bind exactly one explicitly checked white-noise loss arm per process."""
function configure(arm, sigma, seed)
    REQUEST[] === nothing || error("A fresh process is required per scaling arm.")
    arm in ARMS || throw(ArgumentError("Unknown white-noise loss arm."))
    sigma isa Float64 && isfinite(sigma) && sigma > 0 ||
        throw(ArgumentError("Sigma must be a positive finite Float64."))
    variance = sigma * sigma
    factor = 1.0 / variance
    isfinite(factor) && factor > 0 || throw(ArgumentError("Unrepresentable loss scale."))
    context = RingdownSRSearch.CONTEXT[]
    context !== nothing || error("Bind the original input context first.")
    if arm == "covariance"
        context._factor !== nothing || error("The covariance arm needs a covariance.")
        expected = Matrix(Diagonal(fill(sqrt(variance), context._dataset.n)))
        isequal(Matrix(context._factor), expected) ||
            error("The covariance arm requires exactly sigma squared times identity.")
    else
        context._factor === nothing || error("MSE arms must not carry a covariance.")
    end
    REQUEST[] = (; arm=String(arm), sigma, variance, factor, seed=Int(seed))
    verify_options(reference_options(seed))
    return nothing
end

function request()
    value = REQUEST[]
    value !== nothing || error("White-noise scaling is not configured.")
    return value
end

function reference_options(seed)
    seed == request().seed || error("Changed scaling seed.")
    baseline = SearchTimeBudget.reference_options("iterations", seed; should_simplify=false)
    return SearchTimeBudget.changed(baseline; loss_function=objective)
end

function verify_profile(options, seed, expected_objective, callback)
    options.loss_function === expected_objective || error("Wrong scaling objective.")
    options.optimizer_options.callback === callback || error("Wrong optimizer observer.")
    # Restore only the two declared wrappers. All effective optimizer tolerances,
    # plugins, grammar and search options remain under the existing native guard.
    optim = Optim.Options(options.optimizer_options; callback=nothing)
    baseline = SearchTimeBudget.changed(options;
        loss_function=SearchTimeBudget.objective, optimizer_options=optim)
    SearchTimeBudget.verify_options(baseline, "iterations", seed; should_simplify=false)
    return nothing
end

verify_options(options) = verify_profile(options, request().seed, objective, nothing)

function scaled_value(value)
    info = request()
    # Multiplication follows the identical MSE kernel; this is the sole O/S
    # arithmetic difference. Invalid candidates remain invalid after scaling.
    return info.arm == "scaled" ? info.factor * value : value
end

function objective(tree, dataset, options, idx=nothing)
    if VERIFIED_OPTIONS[] !== options
        verify_options(options)
        VERIFIED_OPTIONS[] = options
    end
    return scaled_value(RingdownSRSearch.objective(tree, dataset, options, idx))
end

function verification_record(options)
    info = request()
    VERIFIED_OPTIONS[] === options || error("No verified scaling callback observed.")
    verify_options(options)
    return (; status="verified", arm=info.arm, sigma=info.sigma,
        variance=info.variance, scale=info.factor, backend_seed=info.seed,
        callback_calls=RingdownSRSearch.CALLS[],
        plugins_field=RepresentationProfiles.plugin_field(options),
        plugins=RepresentationProfiles.plugin_records(options),
        optimizer_settings=SearchTimeBudget.optimizer_settings(options))
end

const c = RingdownSRSearch.constant
const t = RingdownSRSearch.variable
const u = RingdownSRSearch.unary
const b = RingdownSRSearch.binary

"""The unchanged thirteen-node damped cosine, with four ordered constants."""
ringdown(p) = b(3, c(p[1]), b(3, u(1, b(3, c(p[2]), t(1))),
    u(3, b(1, b(3, c(p[3]), t(1)), c(p[4])))))

rng_state(rng) = [string(getfield(rng, key)) for key in fieldnames(typeof(rng))]

function rng_reference(seed)
    rng = Xoshiro(seed)
    before = rng_state(rng)
    draws = [randn(rng, Float64, 4) for _ in 1:5]
    return (; before, after=rng_state(rng), draws)
end

struct RestartObserver <: AbstractRNG
    inner::Xoshiro
    draws::Vector{Vector{Float64}}
    local_number::Base.RefValue{Int}
end

function Random.randn(rng::RestartObserver, ::Type{Float64}, dims::Int...)
    values = randn(rng.inner, Float64, dims...)
    push!(rng.draws, copy(vec(values)))
    rng.local_number[] += 1
    return values
end

"""Observe the actual 300/5 backend optimizer without replacing its algorithm.

The backend returns the winning member and evaluation count, but discards the
six local Optim results. Consequently callback states are observations and do
not certify a termination reason. No inferred stop reason is returned here.
"""
function run_fixed(parameters, seed; instrument=true)
    seed == request().seed || error("Changed fixed-structure seed.")
    p = collect(Float64, parameters)
    length(p) == 4 && all(isfinite, p) || error("Expected four finite constants.")
    states = NamedTuple[]
    local_number = Ref(1)
    steps = zeros(Int, 6)
    calls = Ref(0)
    observe(state) = begin
        i = local_number[]
        push!(states, (; local_index=i, step=steps[i],
            kind=string(nameof(typeof(state))), parameters=copy(state.x),
            loss=Float64(state.f_x), gradient=copy(state.g_x)))
        steps[i] += 1
        false
    end
    callback = instrument ? observe : nothing
    checked = Ref{Any}(nothing)
    fixed_objective(tree, dataset, options, idx=nothing) = begin
        if checked[] !== options
            verify_profile(options, seed, fixed_objective, callback)
            checked[] = options
        end
        calls[] += 1
        scaled_value(RingdownSRSearch.CONTEXT[](tree, dataset, options, idx))
    end
    baseline = reference_options(seed)
    options = SearchTimeBudget.changed(baseline; loss_function=fixed_objective,
        optimizer_options=Optim.Options(baseline.optimizer_options; callback))
    verify_profile(options, seed, fixed_objective, callback)
    dataset = RingdownSRSearch.CONTEXT[]._dataset
    tree = ringdown(p)
    SymbolicRegression.compute_complexity(tree, options) == 13 || error("Wrong structure.")
    isequal(get_scalar_constants(tree)[1], p) || error("Wrong constant order.")
    member = PopMember(dataset, copy(tree), options; deterministic=true, ref=1)
    initial_loss = member.loss
    before_calls = calls[]
    inner = Xoshiro(seed)
    before_rng = rng_state(inner)
    draws = Vector{Float64}[]
    rng = instrument ? RestartObserver(inner, draws, local_number) : inner
    started = time_ns()
    member, evaluations = SymbolicRegression.optimize_constants(dataset, member, options; rng)
    elapsed = (time_ns() - started) / 1e9
    fit_calls = calls[] - before_calls
    isequal(get_scalar_constants(tree)[1], p) || error("Start tree mutated.")
    prediction, complete = eval_tree_array(member.tree, dataset.X, options)
    complete || error("Incomplete returned tree.")
    loss = SymbolicRegression.eval_loss(member.tree, dataset, options)
    isequal(loss, member.loss) || error("Returned loss disagrees with callback.")
    verify_profile(options, seed, fixed_objective, callback)
    return (; tree=SymbolicRegression.get_tree(member.tree),
        initial_parameters=p, parameters=copy(get_scalar_constants(member.tree)[1]),
        prediction=copy(prediction), residual=dataset.y - prediction,
        initial_loss, loss, fit_calls, total_calls=calls[], evaluations, elapsed,
        states, draws, rng_before=before_rng, rng_after=rng_state(inner),
        local_steps=steps, termination_available=false, options)
end

end
