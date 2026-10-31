module FreeOptimizerBudget

using SymbolicRegression
using ..RingdownSRSearch
using ..RepresentationProfiles

const Backend = SymbolicRegression.ConstantOptimizationModule
const Optim = Backend.Optim
const REQUEST = Ref{Any}(nothing)
const VERIFIED_OPTIONS = Ref{Any}(nothing)

optimizer_settings(options) = [(; name=string(k),
    value=repr(getfield(options.optimizer_options, k); context=:limit => false))
    for k in fieldnames(typeof(options.optimizer_options))]

function reference_options(iterations, seed)
    iterations in (20, 100) || throw(ArgumentError("Unsupported free optimizer budget."))
    return Options(;
        binary_operators=[+, -, *, /], unary_operators=[exp, sin, cos],
        loss_function=objective, loss_scale=:log,
        complexity_of_operators=Dict(op => 1 for op in (+, -, *, /, exp, sin, cos)),
        complexity_of_constants=1, complexity_of_variables=1,
        maxsize=20, maxdepth=20, populations=2, population_size=32,
        ncycles_per_iteration=50, seed=Int(seed),
        parsimony=0.0, use_frequency=true, use_frequency_in_tournament=true,
        dimensionless_constants_only=false, deterministic=true, batching=false,
        turbo=false, bumper=false, autodiff_backend=nothing,
        should_simplify=true, define_helper_functions=false, input_stream=devnull,
        optimizer_algorithm=Optim.BFGS(; linesearch=Backend.LineSearches.BackTracking()),
        optimizer_options=(; iterations), optimizer_nrestarts=2,
    )
end

function verify_options(options, iterations, seed)
    baseline = RepresentationProfiles.reference_options("complexity_frequency", seed)
    fieldnames(typeof(options)) == fieldnames(typeof(baseline)) ||
        error("Changed backend option field coverage.")
    for key in fieldnames(typeof(baseline))
        key in (:loss_function, :optimizer_options, :output_directory) && continue
        repr(getfield(options, key); context=:limit => false) ==
            repr(getfield(baseline, key); context=:limit => false) ||
            error("Changed frequency-profile option: $key")
    end
    options.loss_function === objective || error("Wrong common free-budget loss wrapper.")
    fieldnames(typeof(options.optimizer_options)) == fieldnames(typeof(baseline.optimizer_options)) ||
        error("Changed optimizer setting coverage.")
    for key in fieldnames(typeof(baseline.optimizer_options))
        actual = getfield(options.optimizer_options, key)
        expected = key == :iterations ? iterations : getfield(baseline.optimizer_options, key)
        isequal(actual, expected) || error("Changed optimizer setting: $key")
    end
    return nothing
end

function configure(iterations, seed)
    REQUEST[] === nothing || throw(ArgumentError("A fresh process is required per budget cell."))
    prototype = reference_options(iterations, seed)
    verify_options(prototype, iterations, seed)
    REQUEST[] = (; iterations=Int(iterations), seed=Int(seed))
    return nothing
end

function objective(tree, dataset, options, idx=nothing)
    request = REQUEST[]
    request === nothing && throw(ArgumentError("Free budget profile is not configured."))
    if VERIFIED_OPTIONS[] !== options
        verify_options(options, request.iterations, request.seed)
        VERIFIED_OPTIONS[] = options
    end
    return RingdownSRSearch.objective(tree, dataset, options, idx)
end

function verification_record(options)
    request = REQUEST[]
    request !== nothing && VERIFIED_OPTIONS[] === options || error("No verified callback observed.")
    verify_options(options, request.iterations, request.seed)
    return (; status="verified", iterations=request.iterations,
        backend_seed=request.seed, callback_calls=RingdownSRSearch.CALLS[],
        plugins_field=RepresentationProfiles.plugin_field(options),
        plugins=RepresentationProfiles.plugin_records(options),
        optimizer_settings=optimizer_settings(options))
end

end
