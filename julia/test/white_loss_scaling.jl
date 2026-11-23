module WhiteLossScalingChecks

using Test
using LinearAlgebra: Diagonal
using SymbolicRegression

const SOURCES = ("RingdownSRLoss.jl", "RingdownSRSearch.jl", "RepresentationProfiles.jl",
    "FreeOptimizerBudget.jl", "TrigonometricGrammar.jl", "LocalOptimizerBudget.jl",
    "SearchTimeBudget.jl", "WhiteLossScaling.jl")

function isolated(name)
    namespace = Module(name)
    for source in SOURCES
        Base.include(namespace, joinpath(@__DIR__, "..", "src", source))
    end
    return namespace
end

const REPLAY_CASES = NamedTuple[]
const NAMESPACES = [isolated(Symbol("ScalingArm", index)) for index in 1:4]

@testset "White loss scaling: exact profile, arithmetic and observation" begin
    time = collect(0.0:0.125:0.875)
    observed = 1.0 .+ time
    sigma, seed = 0.25, 173
    ordinary_losses = Float64[]
    ordinary_baseline = Ref(0.0)
    ordinary_cost = Ref(0.0)
    for (index, arm) in enumerate(("ordinary", "scaled", "covariance"))
        namespace = NAMESPACES[index]
        backend = namespace.RingdownSRSearch
        module_ = namespace.WhiteLossScaling
        covariance = arm == "covariance" ? Matrix(Diagonal(fill(sigma^2, 8))) : nothing
        backend.bind_context(time, observed, covariance)
        module_.configure(arm, sigma, seed)
        options = module_.reference_options(seed)
        @test isnothing(module_.verify_options(options))
        @test options.optimizer_options.iterations == 300
        @test options.optimizer_nrestarts == 5
        @test options.optimizer_options.g_abstol == 1e-8
        @test options.optimizer_options.f_calls_limit == 10000
        @test options.should_simplify === false
        @test options.maxsize == 20
        dataset = backend.CONTEXT[]._dataset
        wrong = (
            namespace.SearchTimeBudget.changed(options; seed=seed + 1),
            namespace.SearchTimeBudget.changed(options; optimizer_nrestarts=2),
            namespace.SearchTimeBudget.changed(options; should_simplify=true),
            namespace.SearchTimeBudget.changed(options; loss_function=backend.objective),
            namespace.SearchTimeBudget.changed(options;
                optimizer_options=module_.Optim.Options(options.optimizer_options; g_abstol=1e-7)),
        )
        for changed in wrong
            before = backend.CALLS[]
            @test_throws ErrorException module_.objective(backend.constant(0.0), dataset, changed)
            @test backend.CALLS[] == before
        end
        trees = [backend.constant(0.25),
            backend.binary(1, backend.constant(1.0),
                backend.binary(3, backend.constant(2.0), backend.variable(1))),
            module_.ringdown([1.0, -1.0, 1.0, 0.1])]
        for (i, tree) in enumerate(trees)
            loss = SymbolicRegression.eval_loss(tree, dataset, options)
            prediction, complete = eval_tree_array(tree, dataset.X, options)
            @test complete
            reference = sum(abs2, observed - prediction) / length(time)
            scale = arm == "ordinary" ? 1.0 : 16.0
            @test isapprox(loss, scale * reference; rtol=32eps(Float64), atol=0)
            if arm == "ordinary"
                push!(ordinary_losses, loss)
            elseif arm == "scaled"
                @test isequal(loss, 16.0 * ordinary_losses[i])
            else
                @test isapprox(loss, 16.0 * ordinary_losses[i]; rtol=32eps(Float64), atol=0)
            end
            push!(REPLAY_CASES, (; arm, time, observed, prediction, loss, sigma))
        end
        @test module_.objective(backend.variable(1), dataset, options) == Inf
        @test_throws ArgumentError module_.objective(trees[1], dataset, options, 1:8)
        changed_data = deepcopy(dataset)
        changed_data.y[1] += 0.125
        @test_throws ArgumentError module_.objective(trees[1], changed_data, options)
        SymbolicRegression.LossFunctionsModule.update_baseline_loss!(dataset, options)
        @test dataset.use_baseline
        @test dataset.baseline_loss > 0.01
        member = PopMember(dataset, trees[1], options; deterministic=true, ref=1)
        if arm == "ordinary"
            ordinary_baseline[] = dataset.baseline_loss
            ordinary_cost[] = member.cost
        else
            @test isapprox(dataset.baseline_loss, 16ordinary_baseline[]; rtol=32eps(Float64), atol=0)
            @test isapprox(member.cost, ordinary_cost[]; rtol=32eps(Float64), atol=0)
        end
        record = module_.verification_record(options)
        @test record.status == "verified"
        @test record.scale == 16.0
        @test_throws ErrorException module_.configure(arm, sigma, seed)
        # A separate technical eight-point family fit proves that the observer
        # preserves returned bits, callback count and actual RNG consumption.
        parameters = [1.0, -1.0, 1.0, 0.1]
        observed_fit = module_.run_fixed(parameters, seed)
        plain_fit = module_.run_fixed(parameters, seed; instrument=false)
        @test isequal(observed_fit.parameters, plain_fit.parameters)
        @test isequal(observed_fit.loss, plain_fit.loss)
        @test isequal(observed_fit.prediction, plain_fit.prediction)
        @test observed_fit.fit_calls == plain_fit.fit_calls
        @test observed_fit.rng_before == plain_fit.rng_before
        @test observed_fit.rng_after == plain_fit.rng_after
        reference = module_.rng_reference(seed)
        @test observed_fit.rng_before == reference.before
        @test observed_fit.rng_after == reference.after
        @test observed_fit.draws == reference.draws
        @test length(observed_fit.draws) == 5
        @test all(s -> s.kind == "BFGSState", observed_fit.states)
        @test sort(unique(s.local_index for s in observed_fit.states)) == collect(1:6)
        @test !observed_fit.termination_available
    end
    namespace = NAMESPACES[4]
    namespace.RingdownSRSearch.bind_context(time, observed, Matrix(Diagonal(fill(1.0, 8))))
    @test_throws ErrorException namespace.WhiteLossScaling.configure("covariance", sigma, seed)
    @test_throws ErrorException namespace.WhiteLossScaling.configure("ordinary", sigma, seed)
    @test_throws ArgumentError namespace.WhiteLossScaling.configure("unknown", sigma, seed)
    @test_throws ArgumentError namespace.WhiteLossScaling.configure("scaled", 0.0, seed)
end

end
