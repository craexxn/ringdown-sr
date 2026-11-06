module SearchTimeBudget

using SymbolicRegression
using ..RingdownSRSearch
using ..RepresentationProfiles
using ..LocalOptimizerBudget

const REQUEST = Ref{Any}(nothing)
const VERIFIED_OPTIONS = Ref{Any}(nothing)
const LIMITS = Dict("iterations" => nothing, "time" => 400.0,
    "technical_timeout" => 0.01, "technical_reserve" => 400.0)

optimizer_settings(options) = LocalOptimizerBudget.optimizer_settings(options)

function changed(options; fields...)
    all(key in fieldnames(typeof(options)) for key in keys(fields)) ||
        error("Unknown native option field.")
    return typeof(options)((get(fields, key, getfield(options, key))
        for key in fieldnames(typeof(options)))...)
end

function limit(condition)
    haskey(LIMITS, condition) || error("Unknown time-budget profile.")
    return LIMITS[condition]
end

function reference_options(condition, seed; should_simplify::Bool=false)
    baseline = LocalOptimizerBudget.reference_options("local_300_5", seed; should_simplify)
    return changed(baseline; loss_function=objective, timeout_in_seconds=limit(condition))
end

function verify_options(options, condition, seed; should_simplify::Bool=false)
    options.loss_function === objective || error("Wrong time-budget objective.")
    isequal(options.timeout_in_seconds, limit(condition)) || error("Wrong native search timer.")
    options.warmup_maxsize_by == 0.0 || error("Iteration-dependent size warmup is forbidden.")
    # Restore only the two intentionally different fields for the unchanged
    # exhaustive 300/5 native guard. No defaults or unrelated options are waived.
    baseline = changed(options; loss_function=LocalOptimizerBudget.objective,
        timeout_in_seconds=nothing)
    LocalOptimizerBudget.verify_options(baseline, "local_300_5", seed; should_simplify)
    return nothing
end

function configure(condition, seed; should_simplify::Bool=false)
    REQUEST[] === nothing || error("A fresh process is required per budget cell.")
    options = reference_options(condition, seed; should_simplify)
    verify_options(options, condition, seed; should_simplify)
    REQUEST[] = (; condition=String(condition), seed=Int(seed))
    return nothing
end

function objective(tree, dataset, options, idx=nothing)
    request = REQUEST[]
    request !== nothing || error("Time-budget profile is not configured.")
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
