module TrigonometricGrammar

using SymbolicRegression
using ..RingdownSRSearch
using ..RepresentationProfiles
using ..FreeOptimizerBudget

const Backend = SymbolicRegression.ConstantOptimizationModule
const Optim = Backend.Optim
const REQUEST = Ref{Any}(nothing)
const VERIFIED_OPTIONS = Ref{Any}(nothing)

optimizer_settings(options) = FreeOptimizerBudget.optimizer_settings(options)

function reference_options(condition, seed)
    condition in ("unrestricted", "no_nested_trig") ||
        throw(ArgumentError("Unsupported trigonometric grammar."))
    nesting = condition == "unrestricted" ? nothing :
        Dict(outer => Dict(inner => 0 for inner in (sin, cos)) for outer in (sin, cos))
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
        optimizer_options=(; iterations=100), optimizer_nrestarts=2,
        nested_constraints=nesting,
    )
end

function verify_nesting(options, condition)
    nesting = options.nested_constraints
    if condition == "unrestricted"
        nesting === nothing || error("Control grammar must be unrestricted.")
    elseif condition == "no_nested_trig"
        nesting !== nothing && length(nesting) == 2 || error("Wrong outer constraints.")
        all(length(row[3]) == 2 for row in nesting) || error("Wrong inner constraints.")
        rows = [(d, op, inner_d, inner_op, limit)
            for (d, op, inners) in nesting for (inner_d, inner_op, limit) in inners]
        sort(rows) == [(1, a, 1, b, 0) for a in (2, 3) for b in (2, 3)] ||
            error("Wrong trig descendant restriction.")
    else
        error("Unsupported trigonometric grammar.")
    end
    return nothing
end

function verify_options(options, condition, seed)
    baseline = FreeOptimizerBudget.reference_options(100, seed)
    fieldnames(typeof(options)) == fieldnames(typeof(baseline)) ||
        error("Changed backend option field coverage.")
    for key in fieldnames(typeof(baseline))
        key in (:loss_function, :nested_constraints, :output_directory) && continue
        repr(getfield(options, key); context=:limit => false) ==
            repr(getfield(baseline, key); context=:limit => false) ||
            error("Changed 100/2 frequency-profile option: $key")
    end
    options.loss_function === objective || error("Wrong shared grammar loss wrapper.")
    verify_nesting(options, condition)
    return nothing
end

function configure(condition, seed)
    REQUEST[] === nothing || throw(ArgumentError("A fresh process is required per grammar cell."))
    prototype = reference_options(condition, seed)
    verify_options(prototype, condition, seed)
    REQUEST[] = (; condition=String(condition), seed=Int(seed))
    return nothing
end

function objective(tree, dataset, options, idx=nothing)
    request = REQUEST[]
    request === nothing && throw(ArgumentError("Grammar profile is not configured."))
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
