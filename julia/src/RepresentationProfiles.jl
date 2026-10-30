module RepresentationProfiles

using SymbolicRegression
using ..RingdownSRSearch

const Backend = SymbolicRegression.ConstantOptimizationModule
const Optim = Backend.Optim
const REQUEST = Ref{Any}(nothing)
const VERIFIED_OPTIONS = Ref{Any}(nothing)

function enabled(condition)
    condition in ("baseline", "time_stretch", "complexity_frequency") ||
        throw(ArgumentError("Unknown representation condition."))
    return condition == "complexity_frequency"
end

function plugin_field(options)
    return (;
        type=string(typeof(options.plugins)),
        value=repr(options.plugins; context=:limit => false),
    )
end

function plugin_records(options)
    return [
        (;
            type=string(typeof(plugin)),
            fields=[
                (;
                    name=string(name),
                    type=string(typeof(getfield(plugin, name))),
                    value=repr(getfield(plugin, name); context=:limit => false),
                ) for name in fieldnames(typeof(plugin))
            ],
        ) for plugin in options.plugins
    ]
end

function reference_options(condition, seed)
    active = enabled(condition)
    return Options(;
        binary_operators=[+, -, *, /], unary_operators=[exp, sin, cos],
        loss_function=objective, loss_scale=:log,
        complexity_of_operators=Dict(op => 1 for op in (+, -, *, /, exp, sin, cos)),
        complexity_of_constants=1, complexity_of_variables=1,
        maxsize=20, maxdepth=20, populations=2, population_size=32,
        ncycles_per_iteration=50, seed=Int(seed),
        parsimony=0.0, use_frequency=active, use_frequency_in_tournament=active,
        dimensionless_constants_only=false, deterministic=true, batching=false,
        turbo=false, bumper=false, autodiff_backend=nothing,
        optimizer_algorithm=Optim.BFGS(; linesearch=Backend.LineSearches.BackTracking()),
        optimizer_options=(; iterations=20), optimizer_nrestarts=2,
    )
end

function verify_options(options, condition, seed, expected)
    active = enabled(condition)
    options.loss_function === objective ||
        throw(ArgumentError("Unexpected representation loss wrapper."))
    options.use_frequency === active && options.use_frequency_in_tournament === active ||
        throw(ArgumentError("Wrong representation frequency flags."))
    options.seed == seed && options.maxsize == 20 && options.maxdepth == 20 &&
        options.populations == 2 && options.population_size == 32 &&
        options.ncycles_per_iteration == 50 && options.parsimony == 0.0 &&
        options.adaptive_parsimony_scaling == 1040.0 ||
        throw(ArgumentError("Wrong reviewed representation backend settings."))
    plugin_field(options) == expected.field && plugin_records(options) == expected.records ||
        throw(ArgumentError("Unexpected actual representation plugins."))
    return nothing
end

function expected_plugins(condition, seed)
    prototype = reference_options(condition, seed)
    names = [string(nameof(typeof(plugin))) for plugin in prototype.plugins]
    expected = enabled(condition) ?
        ["SimulatedAnnealingPlugin", "AdaptiveParsimonyPlugin", "AdaptiveMutationWeightsPlugin"] :
        ["SimulatedAnnealingPlugin", "AdaptiveMutationWeightsPlugin"]
    names == expected || throw(ArgumentError("Pinned default plugin layout changed."))
    if enabled(condition)
        plugin = prototype.plugins[2]
        plugin.tournament === true && plugin.mutation_acceptance === true ||
            throw(ArgumentError("Adaptive parsimony controls are not enabled."))
    end
    return (; field=plugin_field(prototype), records=plugin_records(prototype))
end

function configure(condition, seed)
    REQUEST[] === nothing || throw(ArgumentError("A fresh process is required per profile."))
    REQUEST[] = (; condition=String(condition), seed=Int(seed), expected=expected_plugins(condition, seed))
    return nothing
end

function objective(tree, dataset, options, idx=nothing)
    request = REQUEST[]
    request === nothing && throw(ArgumentError("Representation profile is not configured."))
    if VERIFIED_OPTIONS[] !== options
        # Construct prototypes before fit; never consume RNG in this guard.
        # Recheck backend-specialized copies instead of requiring one identity.
        verify_options(options, request.condition, request.seed, request.expected)
        VERIFIED_OPTIONS[] = options
    end
    return RingdownSRSearch.objective(tree, dataset, options, idx)
end

function verification_record(options)
    request = REQUEST[]
    request !== nothing && VERIFIED_OPTIONS[] === options ||
        throw(ArgumentError("No verified search callback was observed."))
    verify_options(options, request.condition, request.seed, request.expected)
    return (;
        condition=request.condition, backend_seed=request.seed,
        plugins_field=plugin_field(options), plugins=plugin_records(options),
        callback_calls=RingdownSRSearch.CALLS[], status="verified",
    )
end

end
