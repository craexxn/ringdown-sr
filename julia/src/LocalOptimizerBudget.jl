module LocalOptimizerBudget

using SymbolicRegression
using ..RingdownSRSearch
using ..RepresentationProfiles
using ..TrigonometricGrammar

const Backend = SymbolicRegression.ConstantOptimizationModule
const Optim = Backend.Optim
const REQUEST = Ref{Any}(nothing)
const VERIFIED_OPTIONS = Ref{Any}(nothing)
const PROFILES = Dict("local_100_2" => (100, 2), "local_300_2" => (300, 2),
    "local_100_5" => (100, 5), "local_300_5" => (300, 5))

optimizer_settings(options) = TrigonometricGrammar.optimizer_settings(options)

function profile(condition)
    haskey(PROFILES, condition) || throw(ArgumentError("Unsupported local optimizer profile."))
    return PROFILES[condition]
end

function reference_options(condition, seed; should_simplify::Bool=false)
    iterations, restarts = profile(condition)
    should_simplify === false || error("Local comparison must disable simplification.")
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
        should_simplify=false, define_helper_functions=false, input_stream=devnull,
        optimizer_algorithm=Optim.BFGS(; linesearch=Backend.LineSearches.BackTracking()),
        optimizer_options=(; iterations), optimizer_nrestarts=restarts,
        nested_constraints=nothing,
    )
end

function verify_options(options, condition, seed; should_simplify::Bool=false)
    iterations, restarts = profile(condition)
    should_simplify === false || error("Wrong requested simplification policy.")
    baseline = TrigonometricGrammar.reference_options("unrestricted", seed; should_simplify=false)
    fieldnames(typeof(options)) == fieldnames(typeof(baseline)) || error("Changed native field coverage.")
    for key in fieldnames(typeof(baseline))
        key in (:loss_function, :optimizer_options, :optimizer_nrestarts, :output_directory) && continue
        repr(getfield(options, key); context=:limit => false) ==
            repr(getfield(baseline, key); context=:limit => false) || error("Changed common option: $key")
    end
    options.loss_function === objective || error("Wrong shared local optimizer objective.")
    options.optimizer_nrestarts == restarts || error("Wrong local restart budget.")
    fieldnames(typeof(options.optimizer_options)) == fieldnames(typeof(baseline.optimizer_options)) ||
        error("Changed optimizer field coverage.")
    for key in fieldnames(typeof(baseline.optimizer_options))
        expected = key == :iterations ? iterations : getfield(baseline.optimizer_options, key)
        isequal(getfield(options.optimizer_options, key), expected) || error("Changed optimizer option: $key")
    end
    return nothing
end

function configure(condition, seed; should_simplify::Bool=false)
    REQUEST[] === nothing || error("A fresh process is required per local optimizer cell.")
    verify_options(reference_options(condition, seed; should_simplify), condition, seed; should_simplify)
    REQUEST[] = (; condition=String(condition), seed=Int(seed))
    return nothing
end

function objective(tree, dataset, options, idx=nothing)
    request = REQUEST[]
    request !== nothing || error("Local optimizer profile is not configured.")
    if VERIFIED_OPTIONS[] !== options
        verify_options(options, request.condition, request.seed)
        VERIFIED_OPTIONS[] = options
    end
    return RingdownSRSearch.objective(tree, dataset, options, idx)
end

function verification_record(options)
    request = REQUEST[]
    request !== nothing && VERIFIED_OPTIONS[] === options || error("No verified callback observed.")
    verify_options(options, request.condition, request.seed)
    return (; status="verified", condition=request.condition,
        backend_seed=request.seed, callback_calls=RingdownSRSearch.CALLS[],
        plugins_field=RepresentationProfiles.plugin_field(options),
        plugins=RepresentationProfiles.plugin_records(options),
        optimizer_settings=optimizer_settings(options))
end

end
