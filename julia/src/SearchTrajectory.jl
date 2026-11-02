module SearchTrajectory

using SymbolicRegression
using Random
using Serialization
using ..RingdownSRSearch
using ..RingdownSRLoss
using ..RepresentationProfiles
using ..FreeOptimizerBudget

const EVENT_FORMAT = "ringdown-sr-search-trajectory-event-1"
const MAX_BYTES = 256 * 1024 * 1024
const REQUEST = Ref{Any}(nothing)
const VERIFIED_OPTIONS = Ref{Any}(nothing)
const OBSERVATION = Ref{Any}(nothing)
const UNARY = ("exp", "sin", "cos")
const BINARY = ("+", "-", "*", "/")

"Immutable plugin configuration; file handles and counters never enter search state."
struct SearchTrajectoryObserver <: SymbolicRegression.AbstractPlugin end

mutable struct ObservationWriter
    io::IO
    expected_events::Int
    max_bytes::Int
    event_count::Int
    member_count::Int
    bytes_written::Int
    hook_nanoseconds::UInt64
    failed::Bool
    closed::Bool
end

ObservationWriter(io, expected_events; max_bytes=MAX_BYTES) =
    ObservationWriter(io, expected_events, max_bytes, 0, 0, 0, UInt64(0), false, false)

float_bits(value::Float64) = string(reinterpret(UInt64, value); base=16, pad=16)
from_bits(bits::AbstractString) = reinterpret(Float64, parse(UInt64, bits; base=16))

function raw_tree(tree, options)
    root = tree isa SymbolicRegression.AbstractExpression ?
        SymbolicRegression.get_tree(tree) : tree
    root isa SymbolicRegression.AbstractExpressionNode{Float64} ||
        error("The observer only supports the pinned Float64 node type.")
    degree = Int(root.degree)
    if degree == 0
        return root.constant ?
            (; kind="constant", value_bits=float_bits(root.val)) :
            (; kind="variable", index=Int(root.feature))
    end
    degree in (1, 2) || error("Unexpected observed operator arity.")
    names = degree == 1 ? UNARY : BINARY
    index = Int(root.op)
    1 <= index <= length(names) || error("Unexpected observed operator index.")
    string(options.operators.ops[degree][index]) == names[index] ||
        error("The actual observed operator mapping changed.")
    children = degree == 1 ? [raw_tree(root.l, options)] :
        [raw_tree(root.l, options), raw_tree(root.r, options)]
    return (; kind="operator", arity=degree, operator_index=index,
        operator=names[index], children)
end

function restore_tree(record)
    record.kind == "constant" && return RingdownSRSearch.constant(from_bits(record.value_bits))
    record.kind == "variable" && return RingdownSRSearch.variable(record.index)
    children = map(restore_tree, record.children)
    return record.arity == 1 ?
        RingdownSRSearch.unary(record.operator_index, children[1]) :
        RingdownSRSearch.binary(record.operator_index, children[1], children[2])
end

function raw_member(member, options)
    return (;
        tree=raw_tree(getfield(member, :tree), options),
        loss_bits=float_bits(getfield(member, :loss)),
        cost_bits=float_bits(getfield(member, :cost)),
        complexity_cache=getfield(member, :complexity),
        birth=getfield(member, :birth), ref=getfield(member, :ref),
        parent=getfield(member, :parent),
    )
end

function event_record(index, population, hof, options)
    length(population.members) == 32 || error("Unexpected returned population size.")
    length(hof.members) == length(hof.exists) == 20 ||
        error("Unexpected global Hall-of-Fame slots.")
    return (; format=EVENT_FORMAT, event_index=index,
        returned_population=[raw_member(member, options) for member in population.members],
        hall_of_fame=[(; slot=i, member=raw_member(hof.members[i], options))
            for i in eachindex(hof.exists) if hof.exists[i]])
end

# Restrict the wire format to JSON primitives without lossy floating-point printing.
function write_json(io, value::AbstractString)
    write(io, '"')
    for character in value
        if character == '"' || character == '\\'
            write(io, '\\', character)
        elseif character == '\n'
            write(io, "\\n")
        elseif character == '\r'
            write(io, "\\r")
        elseif character == '\t'
            write(io, "\\t")
        elseif Int(character) < 0x20
            write(io, "\\u", string(Int(character); base=16, pad=4))
        else
            print(io, character)
        end
    end
    write(io, '"')
end
write_json(io, value::Integer) = print(io, value)
write_json(io, value::Bool) = print(io, value ? "true" : "false")
write_json(io, ::Nothing) = print(io, "null")
function write_json(io, value::NamedTuple)
    write(io, '{')
    for (i, name) in enumerate(keys(value))
        i == 1 || write(io, ',')
        write_json(io, string(name))
        write(io, ':')
        write_json(io, getfield(value, name))
    end
    write(io, '}')
end
function write_json(io, value::AbstractVector)
    write(io, '[')
    for (i, item) in enumerate(value)
        i == 1 || write(io, ',')
        write_json(io, item)
    end
    write(io, ']')
end
function json_line(record)
    io = IOBuffer()
    write_json(io, record)
    write(io, '\n')
    return take!(io)
end

function append_event!(writer, population, hof, options)
    try
        writer.closed && error("Observation stream is already closed.")
        writer.failed && error("Observation stream has already failed.")
        writer.event_count < writer.expected_events || error("Unexpected extra observer event.")
        record = event_record(writer.event_count + 1, population, hof, options)
        bytes = json_line(record)
        writer.bytes_written + length(bytes) <= writer.max_bytes ||
            error("Observation byte limit exceeded; no event is truncated.")
        written = write(writer.io, bytes)
        written == length(bytes) || error("Incomplete observation write.")
        flush(writer.io)
        writer.event_count += 1
        writer.member_count += length(record.returned_population) + length(record.hall_of_fame)
        writer.bytes_written += written
    catch
        writer.failed = true
        rethrow()
    end
    return nothing
end

function SymbolicRegression.on_generation_end!(
    _, ::SearchTrajectoryObserver, search_state, dataset, options, ropt, returned_pop,
)
    writer = OBSERVATION[]
    writer === nothing && error("The observation stream is not configured.")
    # This series has one output. Do not invent a population/iteration identity.
    length(search_state.halls_of_fame) == 1 || error("Unexpected observer output count.")
    started = time_ns()
    try
        append_event!(writer, returned_pop, only(search_state.halls_of_fame), options)
    finally
        writer.hook_nanoseconds += time_ns() - started
    end
    return nothing
end

function baseline_plugin(index::Integer)
    index isa Bool && error("The baseline plugin position must be an integer.")
    baseline = FreeOptimizerBudget.reference_options(100, 42)
    length(baseline.plugins) == 3 && 1 <= index <= 3 ||
        error("Unexpected baseline plugin position or count.")
    return baseline.plugins[index]
end

function reference_options(observed::Bool, seed)
    backend = SymbolicRegression.ConstantOptimizationModule
    baseline = FreeOptimizerBudget.reference_options(100, seed)
    if observed
        canonical = FreeOptimizerBudget.reference_options(100, 42)
        RepresentationProfiles.plugin_records(baseline) ==
            RepresentationProfiles.plugin_records(canonical) ||
            error("The baseline plugin configuration unexpectedly depends on the seed.")
    end
    # Backend Options puts explicit plugins first and only appends novel defaults.
    # Supply the original plugins explicitly to keep their order before the observer.
    plugins = observed ? (baseline.plugins..., SearchTrajectoryObserver()) : ()
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
        optimizer_algorithm=backend.Optim.BFGS(; linesearch=backend.LineSearches.BackTracking()),
        optimizer_options=(; iterations=100), optimizer_nrestarts=2,
        plugins,
    )
end

function expected_options(observed, seed)
    prototype = reference_options(observed, seed)
    baseline = FreeOptimizerBudget.reference_options(100, seed)
    actual = RepresentationProfiles.plugin_records(prototype)
    base_plugins = RepresentationProfiles.plugin_records(baseline)
    length(actual) == length(base_plugins) + Int(observed) ||
        error("Unexpected plugin count in the reference profile.")
    actual[1:length(base_plugins)] == base_plugins ||
        error("Existing plugins changed in the observer profile.")
    if observed
        last(prototype.plugins) isa SearchTrajectoryObserver ||
            error("The observer must follow every existing plugin.")
        isempty(fieldnames(typeof(last(prototype.plugins)))) ||
            error("Unexpected observer configuration fields.")
    end
    return prototype
end

function verify_options(options, observed::Bool, seed, expected=expected_options(observed, seed))
    fieldnames(typeof(options)) == fieldnames(typeof(expected)) ||
        error("Changed backend option field coverage.")
    for key in fieldnames(typeof(expected))
        key == :output_directory && continue
        repr(getfield(options, key); context=:limit => false) ==
            repr(getfield(expected, key); context=:limit => false) ||
            error("Changed trajectory backend option: $key")
    end
    options.loss_function === objective || error("Wrong common trajectory loss wrapper.")
    RepresentationProfiles.plugin_records(options) ==
        RepresentationProfiles.plugin_records(expected) || error("Changed actual plugins.")
    return nothing
end

function configure(observed::Bool, seed, path::AbstractString, expected_events::Integer)
    REQUEST[] === nothing || error("A fresh process is required for every trajectory cell.")
    expected_events in (4, 400) || error("Unexpected trajectory event budget.")
    prototype = expected_options(observed, seed)
    REQUEST[] = (; observed, seed=Int(seed), expected=prototype, expected_events=Int(expected_events))
    if observed
        (ispath(path) || islink(path)) && error("Observation output already exists.")
        OBSERVATION[] = ObservationWriter(open(path, "w"), expected_events)
    end
    return nothing
end

function objective(tree, dataset, options, idx=nothing)
    request = REQUEST[]
    request === nothing && error("Trajectory profile is not configured.")
    if VERIFIED_OPTIONS[] !== options
        verify_options(options, request.observed, request.seed, request.expected)
        VERIFIED_OPTIONS[] = options
    end
    return RingdownSRSearch.objective(tree, dataset, options, idx)
end

function finish_observation()
    request = REQUEST[]
    request === nothing && error("Trajectory profile is not configured.")
    if !request.observed
        return (; status="disabled", event_count=0, member_count=0, bytes_written=0,
            max_bytes=MAX_BYTES, expected_events=request.expected_events, hook_seconds=0.0)
    end
    writer = OBSERVATION[]
    writer.failed && error("Observation failed during search.")
    writer.event_count == writer.expected_events || error("Incomplete observer event sequence.")
    if !writer.closed
        flush(writer.io)
        close(writer.io)
        writer.closed = true
    end
    return (; status="completed", event_count=writer.event_count,
        member_count=writer.member_count, bytes_written=writer.bytes_written,
        max_bytes=writer.max_bytes, expected_events=writer.expected_events,
        hook_seconds=Float64(writer.hook_nanoseconds) / 1e9)
end

function abort_observation()
    writer = OBSERVATION[]
    if writer !== nothing && !writer.closed
        writer.failed = true
        close(writer.io)
        writer.closed = true
    end
    return nothing
end

function verification_record(options)
    request = REQUEST[]
    request !== nothing && VERIFIED_OPTIONS[] === options ||
        error("No verified trajectory callback observed.")
    verify_options(options, request.observed, request.seed, request.expected)
    baseline = FreeOptimizerBudget.reference_options(100, request.seed)
    return (; status="verified", observed=request.observed, iterations=100,
        backend_seed=request.seed, callback_calls=RingdownSRSearch.CALLS[],
        plugins_field=RepresentationProfiles.plugin_field(options),
        plugins=RepresentationProfiles.plugin_records(options),
        baseline_plugins_field=RepresentationProfiles.plugin_field(baseline),
        baseline_plugins=RepresentationProfiles.plugin_records(baseline),
        expected_plugins_field=RepresentationProfiles.plugin_field(request.expected),
        optimizer_settings=FreeOptimizerBudget.optimizer_settings(options))
end

"After fit only: classify dimensions without evaluating the objective or touching members."
function units_status(root, options)
    checked, finite = RingdownSRLoss._checked_tree(root, options)
    finite || return (; status="not_assessed", reason="nonfinite_constant")
    context = RingdownSRSearch.CONTEXT[]
    context === nothing && error("Missing fixed training context.")
    try
        invalid = SymbolicRegression.DimensionalAnalysisModule.violates_dimensional_constraints(
            checked, context._dataset, options)
        return invalid ? (; status="invalid", reason="dimensional_violation") :
            (; status="valid", reason=nothing)
    catch error
        if error isa DomainError || error isa OverflowError
            return (; status="not_assessed", reason="numerical_unresolved")
        end
        rethrow()
    end
end

serialized(value) = (io = IOBuffer(); serialize(io, value); take!(io))

function fixture_checks()
    options = expected_options(true, 42)
    dataset = SymbolicRegression.Dataset(
        reshape(collect(0.0:0.125:0.875), 1, 8), collect(1.0:0.125:1.875), Float64;
        variable_names=["t"], X_units=["s"], y_units="1")
    c, v, b, u = RingdownSRSearch.constant, RingdownSRSearch.variable,
        RingdownSRSearch.binary, RingdownSRSearch.unary
    trees = [b(1, c(1.0), v(1)), b(1, v(1), u(1, b(3, c(0.0001), v(1)))),
        c(-0.0), c(Inf), c(-Inf), c(reinterpret(Float64, UInt64(0x7ff8000000000042)))]
    for tree in trees
        original = raw_tree(tree, options)
        raw_tree(restore_tree(original), options) == original || error("Tree roundtrip changed bits.")
    end
    members = map(1:32) do i
        tree = SymbolicRegression.CoreModule.create_expression(trees[mod1(i, length(trees))], options, dataset)
        # Direct field constructor preserves explicit metadata and consumes no RNG.
        SymbolicRegression.PopMember{Float64,Float64,typeof(tree)}(
            tree, i == 3 ? -0.0 : Inf, i == 4 ? NaN : Inf, 100 + i, -1, i, i - 1)
    end
    population = SymbolicRegression.Population(members)
    hof = SymbolicRegression.HallOfFame(options, dataset)
    hof.members[3] = copy(members[1])
    hof.members[6] = copy(members[2])
    hof.exists[3] = hof.exists[6] = true
    hof.members[3].loss = 0.0
    hof.members[6].loss = 3.2171682124236767e-12
    plugin_states = SymbolicRegression.CoreModule.PluginModule.init_plugin_states(options, dataset)
    original = serialized((population, hof, plugin_states, options.plugins))
    before_rng = copy(Random.default_rng())
    callbacks = RingdownSRSearch.CALLS[]
    caches = [getfield(member, :complexity) for member in members]
    writer = ObservationWriter(IOBuffer(), 1)
    previous = OBSERVATION[]
    OBSERVATION[] = writer
    try
        SymbolicRegression.on_generation_end!(nothing, SearchTrajectoryObserver(),
            (; halls_of_fame=[hof], plugin_states), dataset, options, nothing, population)
    finally
        OBSERVATION[] = previous
    end
    rand(copy(Random.default_rng()), UInt64, 16) == rand(before_rng, UInt64, 16) ||
        error("The passive observer changed the default RNG.")
    serialized((population, hof, plugin_states, options.plugins)) == original ||
        error("The passive observer changed original search data.")
    caches == [getfield(member, :complexity) for member in members] ||
        error("The passive observer changed complexity caches.")
    RingdownSRSearch.CALLS[] == callbacks || error("Observer evaluated the objective.")
    records = event_record(1, population, hof, options)
    records.returned_population[3].cost_bits == "8000000000000000" ||
        error("Signed zero metadata was lost.")
    records.returned_population[6].tree.value_bits == "7ff8000000000042" ||
        error("NaN payload was lost.")
    limited = ObservationWriter(IOBuffer(), 1; max_bytes=1)
    rejected = false
    try
        append_event!(limited, population, hof, options)
    catch
        rejected = limited.failed && position(limited.io) == 0 && limited.event_count == 0
    end
    rejected || error("Byte cap did not reject the complete event without truncation.")
    before_bytes = position(writer.io)
    rejected = false
    try
        append_event!(writer, population, hof, options)
    catch
        rejected = writer.failed && position(writer.io) == before_bytes && writer.event_count == 1
    end
    rejected || error("Extra event did not fail closed.")
    frontier = SymbolicRegression.calculate_pareto_frontier(hof)
    length(frontier) == 1 && hof.exists[6] && hof.members[6].loss > 0 ||
        error("Pareto filter fixture failed.")
    checks = [
        "exact_tree_roundtrip", "nonfinite_bits_preserved", "rng_unchanged",
        "population_hof_and_plugin_states_unchanged", "complexity_cache_unchanged",
        "callback_count_unchanged", "byte_cap_rejected_without_truncation",
        "unexpected_event_rejected", "pareto_filter_does_not_remove_hof_member",
    ]
    return (; checks, event_json=String(take!(writer.io)))
end

end
