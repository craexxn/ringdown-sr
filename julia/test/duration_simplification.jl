module DurationSimplificationTests

using Test
using SymbolicRegression
using ..TrigonometricGrammar

function check()
    @testset "Finite-precision simplification and the shared duration profile" begin
        for condition in ("unrestricted", "no_nested_trig")
            old = TrigonometricGrammar.reference_options(condition, 583244435)
            new = TrigonometricGrammar.reference_options(condition, 583244435; should_simplify=false)
            @test old.should_simplify === true
            @test new.should_simplify === false
            for key in fieldnames(typeof(old))
                key == :should_simplify && continue
                @test repr(getfield(old, key); context=:limit => false) ==
                    repr(getfield(new, key); context=:limit => false)
            end
            @test isnothing(TrigonometricGrammar.verify_options(new, condition, 583244435; should_simplify=false))
            @test_throws ErrorException TrigonometricGrammar.verify_options(old, condition, 583244435; should_simplify=false)
            @test_throws ErrorException TrigonometricGrammar.verify_options(new, condition, 583244435)

            for simplify in (true, false)
                # Independent exact binary inputs; no fit, search or optimizer.
                options = Options(; binary_operators=(+, -, *, /), unary_operators=(exp, sin, cos),
                    nested_constraints=condition == "unrestricted" ? nothing :
                        Dict(a => Dict(b => 0 for b in (sin, cos)) for a in (sin, cos)),
                    should_simplify=simplify, should_optimize_constants=false,
                    parsimony=0.0, deterministic=true)
                X = reshape(collect(0.0:0.125:0.875), 1, :)
                dataset = Dataset(X, vec(X) .+ 1)
                t = Node{Float64}(; feature=1)
                c(x) = Node{Float64}(; val=x)
                b(op, l, r) = Node{Float64}(; op, l, r)
                root = b(1, b(2, b(2, t, c(1e16)), c(-1e16)), c(1.0))
                member = PopMember(dataset, root, options; deterministic=true)
                prediction, complete = eval_tree_array(member.tree, X, options)
                @test complete && prediction == ones(8)
                @test member.loss == 35 / 128 # sum((j/8)^2 for j=0:7)/8
                weights = copy(options.mutations)
                SymbolicRegression.MutateModule.condition_mutation_weights!(weights, member, options, 20, 1)
                weight = only(last(p) for p in weights if first(p) isa SimplifyMutation)
                @test simplify ? weight > 0 : weight == 0
                pop = SymbolicRegression.Population([copy(member)])
                pop, evaluations = SymbolicRegression.SingleIterationModule.optimize_and_simplify_population(
                    dataset, pop, options, 20, nothing)
                after = only(pop.members)
                @test evaluations == 0
                @test after.loss == member.loss
                actual = SymbolicRegression.eval_loss(after.tree, dataset, options)
                if simplify
                    @test actual == 0
                    @test actual != after.loss
                    result = SymbolicRegression.MutateModule.mutate!(copy(member.tree), member,
                        SimplifyMutation(), options; trace=nothing, dataset, parent_ref=1)
                    @test result.return_immediately
                    @test result.member.loss == 35 / 128
                    @test SymbolicRegression.eval_loss(result.member.tree, dataset, options) == 0
                else
                    @test actual == 35 / 128
                    @test SymbolicRegression.get_tree(after.tree) == SymbolicRegression.get_tree(member.tree)
                    @test_throws AssertionError SymbolicRegression.MutateModule.mutate!(
                        copy(member.tree), member, SimplifyMutation(), options;
                        trace=nothing, dataset, parent_ref=1)
                end
            end
        end
    end
    # The worker guard rejects the old option before touching the loss callback.
    backend = parentmodule(@__MODULE__).RingdownSRSearch
    request = TrigonometricGrammar.REQUEST[]
    old = TrigonometricGrammar.reference_options(request.condition, request.seed)
    calls = backend.CALLS[]
    @test_throws r"Wrong simplification policy" TrigonometricGrammar.objective(
        backend.constant(0.0), backend.CONTEXT[]._dataset, old)
    @test backend.CALLS[] == calls
    return nothing
end

end
