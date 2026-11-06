module SearchBudgetClock

using SymbolicRegression
const SR = SymbolicRegression
const OBSERVATION = Ref{Any}(nothing)

mutable struct Observation
    state::Any
    iterations::Int
    populations::Int
    checks::Int
    native_start::Float64
    first_elapsed::Float64
    last_elapsed::Float64
    first_tick::UInt64
    last_tick::UInt64
    loop_start::UInt64
    loop_end::UInt64
    timeout_reached::Bool
    finished::Bool
    technical_checks::Union{Int,Nothing}
    observer::Any
end

function configure(; technical_checks=nothing, observer=nothing)
    OBSERVATION[] === nothing || error("Search clock requires a fresh process.")
    technical_checks === nothing ||
        (technical_checks isa Int && technical_checks > 0) || error("Invalid technical stop.")
    OBSERVATION[] = Observation(nothing, 0, 0, 0, NaN, NaN, NaN,
        UInt64(0), UInt64(0), UInt64(0), UInt64(0), false, false, technical_checks, observer)
    return nothing
end

# More specific methods instrument only this fresh worker process. Original
# dependency files are never rewritten. The original loop is invoked unchanged.
function SR._main_search_loop!(state::SR.SearchState, datasets,
    ropt::SR.AbstractRuntimeOptions, options::SR.Options)
    observation = OBSERVATION[]
    observation !== nothing && observation.state === nothing || error("Unexpected search loop.")
    ropt.parallelism === :serial && length(datasets) == 1 || error("Expected one serial output.")
    options.warmup_maxsize_by == 0.0 || error("Unexpected size warmup.")
    observation.state = state
    observation.iterations = ropt.niterations
    observation.populations = options.populations
    observation.loop_start = time_ns()
    result = invoke(SR._main_search_loop!,
        Tuple{SR.AbstractSearchState, Any, SR.AbstractRuntimeOptions, SR.AbstractOptions},
        state, datasets, ropt, options)
    observation.loop_end = time_ns()
    observation.finished = true
    return result
end

function SR.check_for_timeout(start_time::Float64, options::SR.Options)
    observation = OBSERVATION[]
    observation !== nothing && observation.state !== nothing || error("Unbound search clock.")
    elapsed, tick = time() - start_time, time_ns()
    # Exactly the pinned backend's strict comparison, without changing its
    # placement, drawing randomness, or interrupting any population cycle.
    reached = options.timeout_in_seconds !== nothing && elapsed > options.timeout_in_seconds
    if observation.checks == 0
        observation.native_start = start_time
        observation.first_elapsed = elapsed
        observation.first_tick = tick
    end
    observation.native_start == start_time || error("Backend timer origin changed.")
    observation.checks += 1
    observation.last_elapsed = elapsed
    observation.last_tick = tick
    observation.timeout_reached = reached
    if observation.observer !== nothing
        observation.observer(observation.state, options)
    end
    return reached || (observation.technical_checks !== nothing &&
        observation.checks >= observation.technical_checks)
end

function record()
    o = OBSERVATION[]
    o !== nothing && o.finished && o.checks > 0 || error("Search clock did not finish.")
    remaining = only(o.state.cycles_remaining)
    total = o.iterations * o.populations
    0 <= remaining < total || error("Invalid native cycle counter.")
    elapsed_monotonic = Float64(o.last_tick - o.first_tick) / 1e9
    clock_difference = (o.last_elapsed - o.first_elapsed) - elapsed_monotonic
    isfinite(o.last_elapsed) && o.last_elapsed >= 0 && abs(clock_difference) <= 1.0 ||
        error("Native wall clock changed relative to the monotonic clock.")
    # These count population outputs consumed by the main loop. A completed
    # but not consumed next population can exist; it is not counted as exported.
    return (; native_start_unix_seconds=o.native_start,
        elapsed_at_last_check_seconds=o.last_elapsed,
        main_loop_call_wall_seconds=Float64(o.loop_end - o.loop_start) / 1e9,
        clock_difference_seconds=clock_difference, checks=o.checks,
        timeout_reached=o.timeout_reached, iteration_limit_reached=remaining == 0,
        requested_iterations=o.iterations, populations=o.populations,
        processed_population_cycles=total - remaining,
        completed_outer_rounds=(total - remaining) ÷ o.populations,
        residual_population_cycles=(total - remaining) % o.populations,
        technical_counter_stop=o.technical_checks !== nothing,
        pending_population_cycles="not_observed",
        scope="consumed_population_outputs; warmup and pending work also contribute to callback cost")
end

end
