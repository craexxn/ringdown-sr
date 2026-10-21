module ConstantOptimizationChecks

using Test
using Random: Xoshiro
using LinearAlgebra: Diagonal, diag, norm
using SymbolicRegression
using SymbolicRegression: get_scalar_constants
using ..RingdownSRLoss: FixedWindowLoss, candidate_loss

# Access the already locked backend dependencies without adding project packages.
const Backend = SymbolicRegression.ConstantOptimizationModule
const Optim = Backend.Optim
const PARAMETER_ATOL = 1e-6
const LOSS_ATOL = 1e-11
const GRADIENT_ATOL = 1e-8
const REPLAY_CASES = NamedTuple[]

constant(value) = Node(Float64; val=Float64(value))
time_node() = Node(Float64; feature=1)
binary(op, left, right) = Node(Float64; op, children=(left, right))
linear(a, b) = binary(1, constant(a), binary(3, constant(b), time_node()))

function backend_options(objective, callback; kwargs...)
    return Options(;
        binary_operators=[+, -, *, /], unary_operators=[exp, sin, cos],
        loss_function=objective, batching=false, turbo=false, bumper=false,
        dimensionless_constants_only=false, autodiff_backend=nothing,
        optimizer_algorithm=Optim.BFGS(; linesearch=Backend.LineSearches.BackTracking()),
        optimizer_nrestarts=0, optimizer_iterations=100,
        optimizer_options=(; g_abstol=GRADIENT_ATOL, callback),
        deterministic=true, parsimony=0.0,
        use_frequency=false, use_frequency_in_tournament=false,
        kwargs...,
    )
end

function dataset_for(time, observed)
    return Dataset(
        reshape(copy(time), 1, length(time)), copy(observed), Float64;
        variable_names=["t"], X_units=["s"], y_units="1",
    )
end

function run_backend(objective, time, observed, tree)
    states = NamedTuple[]
    # Optim 2.2.2 supplies its actual mutable optimizer state, not a trace wrapper.
    function observe(state)
        push!(states, (;
            kind=string(nameof(typeof(state))), parameters=copy(state.x),
            gradient_norm=norm(state.g_x, Inf),
        ))
        return false
    end
    options = backend_options(objective, observe)
    dataset = dataset_for(time, observed)
    initial_parameters = copy(get_scalar_constants(tree)[1])
    member = PopMember(dataset, copy(tree), options; deterministic=true, ref=1)
    initial_loss = member.loss
    member, reported_evaluations = SymbolicRegression.optimize_constants(
        dataset, member, options; rng=Xoshiro(20261021),
    )
    parameters = copy(SymbolicRegression.get_optimizable_parameters(member.tree, options)[1])
    prediction, complete = eval_tree_array(member.tree, dataset.X, options)
    return (;
        parameters, prediction=copy(prediction), complete, loss=member.loss,
        recomputed_loss=candidate_loss(objective, member.tree, options),
        initial_parameters, initial_loss, states, reported_evaluations, options,
    )
end

function check_reference(result, expected_parameters, expected_loss, expected_kind)
    @test result.complete
    @test result.parameters ≈ expected_parameters atol=PARAMETER_ATOL rtol=0
    @test result.loss ≈ expected_loss atol=LOSS_ATOL rtol=0
    @test result.recomputed_loss ≈ result.loss rtol=64eps(Float64) atol=0
    @test result.loss < result.initial_loss
    @test result.reported_evaluations > 0
    @test length(result.states) > 1
    @test all(state -> state.kind == expected_kind, result.states)
    @test result.states[end].gradient_norm <= GRADIENT_ATOL
    @test result.options.autodiff_backend === nothing
    @test result.options.batching === false
    # The one-constant Newton case must override this configured BFGS algorithm.
    @test result.options.optimizer_algorithm isa Optim.BFGS
end

@testset "Actual backend constant optimization" begin
    @testset "One constant: observed Newton path" begin
        time, observed = [0.0, 1.0], [1.0, 3.0]
        full = [4.0 2.0; 2.0 10.0]
        cases = (
            ("full", full, [7/5], 1/5),
            ("diagonal", Matrix(Diagonal(diag(full))), [11/7], 1/7),
            ("ordinary", nothing, [2.0], 1.0),
        )
        for (weighting, covariance, expected, expected_loss) in cases
            @testset "$weighting, start=$start" for start in (-1.0, 5.0)
                objective = FixedWindowLoss(time, observed; covariance)
                tree = constant(start)
                result = run_backend(objective, time, observed, tree)
                check_reference(result, expected, expected_loss, "NewtonState")
                @test result.initial_parameters == [start]
                @test get_scalar_constants(tree)[1] == [start]
                push!(REPLAY_CASES, (;
                    model="constant", weighting, time, observed, covariance, result,
                ))
                println("Optimizer constant/$weighting: Newton, theta=", result.parameters[1])
            end
        end
    end

    @testset "Two constants: observed BFGS path" begin
        time, observed = [0.0, 1.0, 2.0], [0.0, 1.0, 0.0]
        full = [2.0 1.0 0.0; 1.0 2.0 0.0; 0.0 0.0 1.0]
        cases = (
            ("full", full, [0.0, 1/7], 4/21),
            ("diagonal", Matrix(Diagonal(diag(full))), [4/11, -1/11], 4/33),
            ("ordinary", nothing, [1/3, 0.0], 2/9),
        )
        for (weighting, covariance, expected, expected_loss) in cases
            @testset "$weighting, start=$start" for start in ((1.0, -1.0), (-1.0, 1.0))
                objective = FixedWindowLoss(time, observed; covariance)
                tree = linear(start...)
                result = run_backend(objective, time, observed, tree)
                check_reference(result, expected, expected_loss, "BFGSState")
                @test result.initial_parameters == collect(start)
                @test get_scalar_constants(tree)[1] == collect(start)
                push!(REPLAY_CASES, (;
                    model="linear", weighting, time, observed, covariance, result,
                ))
                println("Optimizer linear/$weighting: BFGS, (a,b)=", result.parameters)
            end
        end
    end

    @testset "Independent contexts during optimization" begin
        time, observed = [0.0, 1.0, 2.0], [0.0, 1.0, 0.0]
        covariance = [2.0 1.0 0.0; 1.0 2.0 0.0; 0.0 0.0 1.0]
        a = FixedWindowLoss(time, observed; covariance)
        b = FixedWindowLoss(time, observed)
        factor, factor_values = a._factor, Matrix(a._factor)
        original_x, original_y = copy(a._dataset.X), copy(a._dataset.y)
        tree = linear(1.0, -1.0)
        first = run_backend(a, time, observed, tree)
        other = run_backend(b, time, observed, tree)
        again = run_backend(a, time, observed, tree)
        @test first.parameters ≈ [0.0, 1/7] atol=PARAMETER_ATOL rtol=0
        @test other.parameters ≈ [1/3, 0.0] atol=PARAMETER_ATOL rtol=0
        @test again.parameters ≈ first.parameters atol=PARAMETER_ATOL rtol=0
        @test again.loss ≈ first.loss atol=LOSS_ATOL rtol=0
        @test a._factor === factor
        @test Matrix(a._factor) == factor_values
        @test a._dataset.X == original_x
        @test a._dataset.y == original_y
        @test get_scalar_constants(tree)[1] == [1.0, -1.0]
    end

    @testset "Exact zero is retained by the Newton path" begin
        time, observed = [0.0, 1.0], [2.0, 2.0]
        result = run_backend(FixedWindowLoss(time, observed), time, observed, constant(2))
        @test result.initial_loss === 0.0
        @test result.loss === 0.0
        @test result.recomputed_loss === 0.0
        @test result.parameters == [2.0]
        @test !isempty(result.states)
        @test all(state -> state.kind == "NewtonState", result.states)
    end

    @testset "The optimizer evaluator preserves units and input errors" begin
        time, observed = [0.0, 1.0], [0.0, 1.0]
        objective = FixedWindowLoss(time, observed)
        options = backend_options(objective, nothing; dimensional_constraint_penalty=0.0)
        dataset = dataset_for(time, observed)
        # Adding a free constant cannot turn a time-valued sum into unitless output.
        expression = Expression(binary(1, constant(0), time_node()); operators=options.operators)
        _, refs = SymbolicRegression.get_optimizable_parameters(expression, options)
        evaluator = Backend.Evaluator(
            expression, refs, Backend.EvaluatorContext(dataset, options, nothing),
        )
        @test evaluator([0.0]) == Inf
        @test evaluator([3.0]; regularization=true) == Inf
        @test evaluator([NaN]) == Inf

        valid = Expression(linear(1, -1); operators=options.operators)
        _, valid_refs = SymbolicRegression.get_optimizable_parameters(valid, options)
        wrong = dataset_for([0.0], [0.0])
        bad_evaluator = Backend.Evaluator(
            valid, valid_refs, Backend.EvaluatorContext(wrong, options, nothing),
        )
        @test_throws ArgumentError bad_evaluator([1.0, -1.0])
    end
end

end
