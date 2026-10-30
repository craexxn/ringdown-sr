using Test
using LinearAlgebra: I
using SymbolicRegression
using SymbolicRegression.CoreModule: batch

include(joinpath(@__DIR__, "..", "src", "RingdownSRLoss.jl"))
using .RingdownSRLoss

const_node(value) = Node(Float64; val=Float64(value))
time_node() = Node(Float64; feature=1)
bin_node(op, left, right) = Node(Float64; op=op, children=(left, right))
un_node(op, child) = Node(Float64; op=op, children=(child,))

function loss_options(; dimensionless_constants_only=false, kwargs...)
    return Options(;
        binary_operators=[+, -, *, /],
        unary_operators=[exp, sin, cos],
        batching=false, turbo=false, bumper=false,
        dimensionless_constants_only,
        kwargs...,
    )
end

function full_dataset(time, observed; X_units=["s"], y_units="1", weights=nothing)
    return Dataset(
        reshape(Float64.(time), 1, length(time)), Float64.(observed), Float64;
        X_units, y_units, weights,
    )
end

@testset "Fixed-window Julia loss" begin
    options = loss_options()

    @testset "Independent numeric references" begin
        context = FixedWindowLoss(
            [0.0, 1.0], [1.0, 0.0]; covariance=[2.5 1.5; 1.5 4.5],
        )
        @test n_samples(context) == 2
        @test residual_loss(context, [1.0, 0.0]) ≈ 1/4 rtol=32eps(Float64)
        @test candidate_loss(context, const_node(0), options) ≈ 1/4 rtol=32eps(Float64)
        # The transposed triangular solve would give 1/5 instead of 1/4.
        @test !isapprox(residual_loss(context, [1.0, 0.0]), 1/5; rtol=1e-3)

        same = FixedWindowLoss([0.0, 1.0], [1.0, 1.0]; covariance=[2.0 1.0; 1.0 2.0])
        opposite = FixedWindowLoss(
            [0.0, 1.0], [1.0, -1.0]; covariance=[2.0 1.0; 1.0 2.0],
        )
        @test candidate_loss(same, const_node(0), options) ≈ 1/3 rtol=32eps(Float64)
        @test candidate_loss(opposite, const_node(0), options) ≈ 1.0 rtol=32eps(Float64)

        ordinary = FixedWindowLoss([0.0, 1.0], [2.0, 4.0])
        identity = FixedWindowLoss(
            [0.0, 1.0], [2.0, 4.0]; covariance=Matrix{Float64}(I, 2, 2),
        )
        @test residual_loss(ordinary, [2.0, 4.0]) ≈ 10.0 rtol=32eps(Float64)
        @test residual_loss(identity, [2.0, 4.0]) ≈ 10.0 rtol=32eps(Float64)
        @test candidate_loss(ordinary, const_node(0), options) ≈ 10.0 rtol=32eps(Float64)
        @test residual_loss(ordinary, 2.0:2.0:4.0) ≈ 10.0 rtol=32eps(Float64)
        ranged = FixedWindowLoss(0.0:1.0, 2.0:2.0:4.0)
        @test candidate_loss(ranged, const_node(0), options) ≈ 10.0 rtol=32eps(Float64)

        for scale in (1e-21, 1.0, 1e21)
            scaled = FixedWindowLoss(
                [0.0, 1.0], scale .* [1.0, 0.0];
                covariance=scale^2 .* [2.5 1.5; 1.5 4.5],
            )
            @test residual_loss(scaled, scale .* [1.0, 0.0]) ≈ 1/4 rtol=64eps(Float64)
        end

        large = FixedWindowLoss([0.0, 1.0], zeros(2))
        @test isfinite(residual_loss(large, [1e154, 1e154]))
        @test residual_loss(large, [1e154, 1e154]) ≈ 1e308 rtol=32eps(Float64)
        @test residual_loss(large, [0.0, 0.0]) === 0.0

        # Evaluate the hand-derived multi-constant optimum; do not optimize it.
        linear = FixedWindowLoss(
            [0.0, 1.0, 2.0], [0.0, 1.0, 0.0];
            covariance=[2.0 1.0 0.0; 1.0 2.0 0.0; 0.0 0.0 1.0],
        )
        tree = bin_node(1, const_node(0), bin_node(3, const_node(1/7), time_node()))
        @test candidate_loss(linear, tree, options) ≈ 4/21 rtol=64eps(Float64)

        rho = 0.999
        correlated = FixedWindowLoss(
            [0.0, 1.0], zeros(2); covariance=[1.0 rho; rho 1.0],
        )
        tolerance = 10eps(Float64) * (1+rho)/(1-rho)
        @test residual_loss(correlated, [1.0, -1.0]) ≈ 1/(1-rho) rtol=tolerance
    end

    @testset "Original times and explicit dimensions" begin
        time = [0.0, 0.25, 0.5]
        prediction = exp.(-2 .* time)
        context = FixedWindowLoss(time, prediction)
        valid = un_node(1, bin_node(3, const_node(-2), time_node()))
        @test candidate_loss(context, valid, options) < 1e-28
        @test candidate_loss(
            context, Expression(valid; operators=options.operators), options,
        ) < 1e-28

        # Numerically perfect predictions with wrong units remain inadmissible.
        dimensioned = FixedWindowLoss(time, time)
        @test candidate_loss(dimensioned, time_node(), options) == Inf
        bad_exp = FixedWindowLoss(time, exp.(time))
        @test candidate_loss(bad_exp, un_node(1, time_node()), options) == Inf
        strict = loss_options(dimensionless_constants_only=true)
        @test candidate_loss(context, valid, strict) == Inf

        exact = FixedWindowLoss(time, fill(2.0, length(time)))
        @test candidate_loss(exact, const_node(2), options) === 0.0

        covariance = [1.0 1.0; 1.0 2.0]
        original = FixedWindowLoss([0.0, 1.0], zeros(2); covariance)
        exponential = un_node(1, bin_node(3, const_node(1), time_node()))
        expected = (1 + (exp(1)-1)^2)/2
        @test candidate_loss(original, exponential, options) ≈ expected rtol=64eps(Float64)
        @test !isapprox(expected, (1 + exp(1)^2)/2; rtol=1e-3)

        # A finite-loss damped sinusoid is representable without a template.
        signal = exp.(-2 .* time) .* cos.(3 .* time .+ 0.3)
        ringdown = bin_node(
            3,
            un_node(1, bin_node(3, const_node(-2), time_node())),
            un_node(3, bin_node(1, bin_node(3, const_node(3), time_node()), const_node(0.3))),
        )
        @test candidate_loss(FixedWindowLoss(time, signal), ringdown, options) < 1e-28
    end

    @testset "Full callback and backend loss dispatch" begin
        time, observed = [0.0, 1.0], [1.0, 0.0]
        objective = FixedWindowLoss(time, observed; covariance=[2.5 1.5; 1.5 4.5])
        dataset = full_dataset(time, observed)
        zero = const_node(0)
        @test objective(zero, dataset, options) ≈ 1/4 rtol=32eps(Float64)
        callback_options = loss_options(loss_function=objective)
        @test SymbolicRegression.eval_loss(zero, dataset, callback_options) ≈ 1/4 rtol=32eps(Float64)
        @test SymbolicRegression.eval_loss(
            zero, dataset, callback_options; idx=nothing,
        ) ≈ 1/4 rtol=32eps(Float64)

        # Explicit indices must not be silently ignored, even for the full window.
        for idx in ([1], [1, 2], [2, 1], Int[], 1:2)
            @test_throws ArgumentError SymbolicRegression.eval_loss(
                zero, dataset, callback_options; idx,
            )
        end
        # The four-argument dispatcher also forwards indices from SubDataset.
        for idx in ([1], [1, 2])
            @test_throws ArgumentError SymbolicRegression.eval_loss(
                zero, batch(dataset, idx), callback_options,
            )
        end

        # The custom-loss route must perform units analysis even with penalty 0.
        units_objective = FixedWindowLoss(time, time)
        units_dataset = full_dataset(time, time)
        units_options = loss_options(
            loss_function=units_objective, dimensional_constraint_penalty=0.0,
        )
        @test SymbolicRegression.eval_loss(
            time_node(), units_dataset, units_options,
        ) == Inf

        @test_throws ArgumentError objective(zero, batch(dataset, [1, 2]), options)
        @test_throws ArgumentError objective(zero, batch(dataset, [1]), options)
        @test_throws ArgumentError objective(
            zero, full_dataset(reverse(time), reverse(observed)), options,
        )
        @test_throws ArgumentError objective(
            zero, full_dataset(time, observed .+ 0.01), options,
        )
        @test_throws ArgumentError objective(
            zero, full_dataset(time, observed; weights=ones(2)), options,
        )
        for (xunits, yunits) in ((nothing, nothing), (["ms"], "1"), (["s"], "m"))
            @test_throws ArgumentError objective(
                zero, full_dataset(time, observed; X_units=xunits, y_units=yunits), options,
            )
        end
        float32 = Dataset(
            reshape(Float32.(time), 1, 2), Float32.(observed);
            X_units=["s"], y_units="1",
        )
        @test_throws ArgumentError objective(zero, float32, options)
        @test_throws ArgumentError objective(zero, full_dataset([0.0], [1.0]), options)
        @test_throws ArgumentError objective(zero, nothing, options)
    end

    @testset "Candidate failures and programmer errors" begin
        context = FixedWindowLoss([0.0, 1.0], zeros(2))
        for value in (NaN, Inf, -Inf)
            @test candidate_loss(context, const_node(value), options) == Inf
        end
        @test candidate_loss(
            context, bin_node(4, const_node(1), const_node(0)), options,
        ) == Inf
        @test candidate_loss(context, un_node(1, const_node(1000)), options) == Inf
        @test_throws ArgumentError candidate_loss(
            context, Node(Float32; val=0f0), options,
        )
        @test_throws ArgumentError candidate_loss(
            context, Node(Float64; feature=2), options,
        )
        @test_throws ArgumentError candidate_loss(
            context, un_node(99, const_node(1)), options,
        )
        @test_throws ArgumentError candidate_loss(context, "not a tree", options)

        overflow = FixedWindowLoss([0.0], [floatmax(Float64)])
        @test candidate_loss(overflow, const_node(-floatmax(Float64)), options) == Inf
        tiny = FixedWindowLoss([0.0], [1e150]; covariance=reshape([1e-300], 1, 1))
        @test_throws OverflowError residual_loss(tiny, [1e150])
        @test candidate_loss(tiny, const_node(0), options) == Inf
        @test_throws OverflowError residual_loss(context, [floatmax(Float64), 0.0])

        # A bad callback dataset is never hidden by a bad candidate.
        @test_throws ArgumentError context(const_node(NaN), nothing, options)
    end

    @testset "Input validation" begin
        for (time, observed) in (
            (Float64[], Float64[]),
            ([0.0], [0.0, 1.0]),
            ([-1.0], [0.0]),
            ([NaN], [0.0]),
            ([0.0], [Inf]),
            ([true], [0.0]),
            ([0.0], [false]),
            (["0"], [0.0]),
            ([0.0], [0.0 + 0.0im]),
            (reshape([0.0], 1, 1), [0.0]),
        )
            @test_throws ArgumentError FixedWindowLoss(time, observed)
        end
        for covariance in (
            zeros(0, 0), ones(1, 2), ones(3, 3), [1.0 2.0; 0.0 1.0],
            [1.0 1.0; 1.0 1.0], [1.0 2.0; 2.0 1.0], [Inf 0.0; 0.0 1.0],
            fill(true, 2, 2), fill("1", 2, 2), [1.0+0im 0.0; 0.0 1.0],
            1e-42 .* [2.0 1.0; 0.0 2.0],
        )
            @test_throws ArgumentError FixedWindowLoss([0.0, 1.0], zeros(2); covariance)
        end
        context = FixedWindowLoss([0.0, 1.0], zeros(2))
        for residual in (Float64[], [1.0], [NaN, 0.0], [true, false], ["1", "2"])
            @test_throws ArgumentError residual_loss(context, residual)
        end
    end

    @testset "Owned data, fixed factor and independent instances" begin
        time, observed = [0.0, 1.0], [1.0, 0.0]
        covariance = [2.5 1.5; 1.5 4.5]
        context = FixedWindowLoss(time, observed; covariance)
        snapshot = full_dataset(copy(time), copy(observed))
        factor = context._factor
        factor_values = Matrix(factor)
        time[1] = 99.0
        observed[1] = -99.0
        covariance .= 0.0
        @test context(const_node(0), snapshot, options) ≈ 1/4 rtol=32eps(Float64)
        @test context._factor === factor
        @test Matrix(context._factor) == factor_values

        other = FixedWindowLoss([0.0, 1.0], [1.0, 0.0])
        first = candidate_loss(context, const_node(0), options)
        @test candidate_loss(other, const_node(0), options) ≈ 1/2 rtol=32eps(Float64)
        @test candidate_loss(context, const_node(0), options) == first
        @test Matrix(context._factor) == factor_values
    end
end


include(joinpath(@__DIR__, "..", "src", "RingdownSRSearch.jl"))

@testset "Frozen noiseless signal through the search callback" begin
    time = Float64.(0:127) ./ 4096.0
    observed = exp.(-time ./ 0.008) .* cos.(2pi * 250 .* time)
    dataset = full_dataset(time, observed)
    RingdownSRSearch.bind_context(time, observed, nothing)
    options = loss_options(
        loss_function=RingdownSRSearch.objective,
        dimensionless_constants_only=false, maxsize=20,
    )
    reference = bin_node(
        3, const_node(1),
        bin_node(
            3,
            un_node(1, bin_node(3, const_node(-125), time_node())),
            un_node(3, bin_node(3, const_node(2pi * 250), time_node())),
        ),
    )
    @test SymbolicRegression.compute_complexity(reference, options) == 11
    @test SymbolicRegression.compute_complexity(reference, options) <= options.maxsize

    reference_loss = SymbolicRegression.eval_loss(reference, dataset, options)
    @test isfinite(reference_loss)
    @test reference_loss < 1e-24
    @test RingdownSRSearch.CALLS[] == 1

    mean_value = sum(observed) / length(observed)
    expected_constant_loss = sum(abs2, observed .- mean_value) / length(observed)
    constant_loss = SymbolicRegression.eval_loss(const_node(mean_value), dataset, options)
    @test constant_loss ≈ expected_constant_loss rtol=64eps(Float64)
    @test constant_loss ≈ 0.06829567962376913 rtol=64eps(Float64)
    @test reference_loss < constant_loss

    # A numerically evaluable tree still has to obey the original units.
    @test SymbolicRegression.eval_loss(un_node(2, time_node()), dataset, options) == Inf
    @test RingdownSRSearch.CALLS[] == 3
    @test RingdownSRSearch.LAST_OPTIONS[] === options
    @test RingdownSRSearch.LAST_DATASET[] === dataset
    println(
        "Noiseless search-callback control passed: nodes=11, reference_MSE=",
        reference_loss, ", constant_MSE=", constant_loss,
    )
end

include(joinpath(@__DIR__, "constant_optimization.jl"))
