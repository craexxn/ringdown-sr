module ConstantDiagnostic

using SymbolicRegression
using SymbolicRegression: get_scalar_constants
using Random
using ..RingdownSRSearch
using ..RepresentationProfiles

const Backend = SymbolicRegression.ConstantOptimizationModule
const Optim = Backend.Optim
const c = RingdownSRSearch.constant
const t = RingdownSRSearch.variable
const u = RingdownSRSearch.unary
const b = RingdownSRSearch.binary

ringdown(p) = b(3, c(p[1]), b(3, u(1, b(3, c(p[2]), t(1))),
                                     u(3, b(1, b(3, c(p[3]), t(1)), c(p[4])))))
rng_state(rng) = [string(getfield(rng, key)) for key in fieldnames(typeof(rng))]

optimizer_settings(options) = [(; name=string(k), value= k == :callback ?
    (options.optimizer_options.callback === nothing ? "nothing" : "observing_callback") :
    repr(getfield(options.optimizer_options, k); context=:limit => false))
    for k in fieldnames(typeof(options.optimizer_options))]


function options_for(iterations, seed, objective, callback)
    iterations in (20, 100) || throw(ArgumentError("Unsupported diagnostic budget."))
    return Options(;
        binary_operators=[+, -, *, /], unary_operators=[exp, sin, cos],
        loss_function=objective, loss_scale=:log,
        complexity_of_operators=Dict(op => 1 for op in (+, -, *, /, exp, sin, cos)),
        complexity_of_constants=1, complexity_of_variables=1,
        maxsize=20, maxdepth=20, populations=2, population_size=32,
        ncycles_per_iteration=50, seed=Int(seed),
        parsimony=0.0, use_frequency=false, use_frequency_in_tournament=false,
        dimensionless_constants_only=false, deterministic=true, batching=false,
        turbo=false, bumper=false, autodiff_backend=nothing,
        should_simplify=true, define_helper_functions=false, input_stream=devnull,
        optimizer_algorithm=Optim.BFGS(; linesearch=Backend.LineSearches.BackTracking()),
        optimizer_options=(; iterations, callback), optimizer_nrestarts=2,
    )
end

function verify_options(options, iterations, seed, objective, callback)
    expected = RepresentationProfiles.reference_options("baseline", seed)
    for key in fieldnames(typeof(expected))
        key in (:loss_function, :optimizer_options) && continue
        repr(getfield(options, key); context=:limit => false) ==
            repr(getfield(expected, key); context=:limit => false) ||
            error("Changed baseline option: $key")
    end
    options.loss_function === objective || error("Wrong full loss wrapper.")
    for key in fieldnames(typeof(expected.optimizer_options))
        actual = getfield(options.optimizer_options, key)
        if key == :iterations
            actual == iterations || error("Wrong optimizer iterations.")
        elseif key == :callback
            actual === callback || error("Wrong observation callback.")
        else
            isequal(actual, getfield(expected.optimizer_options, key)) ||
                error("Changed optimizer tolerance/setting: $key")
        end
    end
    return nothing
end

function run(time, observed, parameters, iterations, seed; instrument=true)
    states = NamedTuple[]
    local_number = Ref(1)
    steps = zeros(Int, 3)
    calls = Ref(0)
    objective(tree, dataset, options, idx=nothing) = begin
        calls[] += 1
        RingdownSRSearch.CONTEXT[](tree, dataset, options, idx)
    end
    observe(state) = begin
        i = local_number[]
        push!(states, (; local_index=i, step=steps[i],
            kind=string(nameof(typeof(state))), parameters=copy(state.x),
            loss=Float64(state.f_x), gradient=copy(state.g_x)))
        steps[i] += 1
        false
    end
    callback = instrument ? observe : nothing
    options = options_for(iterations, seed, objective, callback)
    verify_options(options, iterations, seed, objective, callback)
    dataset = RingdownSRSearch.CONTEXT[]._dataset
    isequal(vec(dataset.X), time) && isequal(dataset.y, observed) || error("Changed inputs.")
    tree = ringdown(parameters)
    SymbolicRegression.compute_complexity(tree, options) == 13 || error("Wrong structure.")
    supplied = copy(get_scalar_constants(tree)[1])
    isequal(supplied, parameters) || error("Wrong constant order.")
    member = PopMember(dataset, copy(tree), options; deterministic=true, ref=1)
    initial_loss = member.loss
    before_calls = calls[]
    inner = Xoshiro(seed)
    before_rng = rng_state(inner)
    draws = Vector{Float64}[]
    # The wrapper delegates each vector draw once, without consuming extra RNG.
    rng = instrument ? RestartObserver(inner, draws, local_number) : inner
    started = time_ns()
    member, evaluations = SymbolicRegression.optimize_constants(dataset, member, options; rng)
    elapsed = (time_ns() - started) / 1e9
    fit_calls = calls[] - before_calls
    isequal(get_scalar_constants(tree)[1], supplied) || error("Start tree mutated.")
    prediction, complete = eval_tree_array(member.tree, dataset.X, options)
    complete || error("Incomplete returned tree.")
    loss = SymbolicRegression.eval_loss(member.tree, dataset, options)
    isequal(loss, member.loss) || error("Returned loss disagrees with callback.")
    verify_options(options, iterations, seed, objective, callback)
    return (; tree=SymbolicRegression.get_tree(member.tree), parameters=copy(get_scalar_constants(member.tree)[1]),
        prediction=copy(prediction), residual=dataset.y - prediction,
        initial_loss, loss, fit_calls, total_calls=calls[], evaluations, elapsed,
        states, draws, rng_before=before_rng, rng_after=rng_state(inner), options)
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

function controls(time, observed, iterations, seed)
    options = options_for(iterations, seed, RingdownSRSearch.objective, nothing)
    verify_options(options, iterations, seed, RingdownSRSearch.objective, nothing)
    dataset = RingdownSRSearch.CONTEXT[]._dataset
    trees = [ringdown([1., -125., 2pi*f, 0.]) for f in (250., 4346., 33018.)]
    push!(trees, c(sum(observed) / length(observed)))
    push!(trees, u(2, t(1)))
    return [(; tree, loss=SymbolicRegression.eval_loss(tree, dataset, options), options)
            for tree in trees]
end

end
