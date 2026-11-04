"""Check actual local-profile callback rejection on fixed eight-point data."""

from ringdown_sr import local_optimizer as control
from ringdown_sr.constant_diagnostic import backend_seed
from ringdown_sr.pilot import _sha256


def check():
    sources = control.source_hashes()
    loader = control.load_module(
        control.ROOT / "scripts/check_trigonometric_grammar_backend.py",
        "local_native_loader",
    )
    jl = loader.native_runtime()
    jl.seval(r"""
        using Test
        function local_optimizer_checks(backend, module_, seed)
            replace_field(object, key, value) = typeof(object)(
                (name == key ? value : getfield(object, name) for name in fieldnames(typeof(object)))...)
            conditions = ("local_100_2", "local_300_2", "local_100_5", "local_300_5")
            expected = ((100, 2), (300, 2), (100, 5), (300, 5))
            @testset "Native local optimizer profile and callback" begin
                for (condition, (iterations, restarts)) in zip(conditions, expected)
                    options = module_.reference_options(condition, seed)
                    @test options.optimizer_options.iterations == iterations
                    @test options.optimizer_nrestarts == restarts
                    @test options.optimizer_options.f_calls_limit == 10000
                    @test isnothing(options.nested_constraints)
                    @test options.should_simplify === false
                    @test isnothing(module_.verify_options(options, condition, seed))
                end
                condition = module_.REQUEST[].condition
                options = module_.reference_options(condition, seed)
                optim = options.optimizer_options
                wrong = [
                    replace_field(options, :seed, seed + 1),
                    replace_field(options, :optimizer_nrestarts, 99),
                    replace_field(options, :optimizer_options, replace_field(optim, :iterations, 99)),
                    replace_field(options, :optimizer_options, replace_field(optim, :f_calls_limit, 9999)),
                    replace_field(options, :optimizer_options, replace_field(optim, :g_abstol, 0.1)),
                    replace_field(options, :should_simplify, true),
                    replace_field(options, :use_frequency, false),
                    replace_field(options, :use_frequency_in_tournament, false),
                    replace_field(options, :loss_function, backend.objective),
                    replace_field(options, :nested_constraints, [(1, 2, [(1, 2, 0)])]),
                ]
                root = backend.constant(1.0)
                dataset = backend.CONTEXT[]._dataset
                # The first attempted callback must already reject a wrong profile.
                for bad in wrong
                    before = backend.CALLS[]
                    @test_throws ErrorException module_.objective(root, dataset, bad)
                    @test backend.CALLS[] == before
                end
                before = backend.CALLS[]
                actual = module_.objective(root, dataset, options)
                @test actual == 35 / 128
                @test backend.CALLS[] == before + 1
                @test module_.verification_record(options).status == "verified"
                @test_throws ErrorException module_.configure(condition, seed)
                for bad in wrong
                    before = backend.CALLS[]
                    @test_throws ErrorException module_.objective(root, dataset, bad)
                    @test backend.CALLS[] == before
                end
            end
        end
    """)
    seed = backend_seed(control.SEEDS[0])
    for index, condition in enumerate(control.CONDITIONS):
        name = f"LocalNativeCheck{index}"
        jl.seval(f"module {name} end")
        namespace = getattr(jl, name)
        for filename in (*loader.NATIVE_FILES, "LocalOptimizerBudget.jl"):
            path = control.ROOT / "julia/src" / filename
            if _sha256(path.read_bytes()) != sources["julia/src/" + filename]:
                raise ValueError("Native check source changed.")
            jl.Base.include(namespace, str(path))
        backend = namespace.RingdownSRSearch
        module = namespace.LocalOptimizerBudget
        time = jl.seval("collect(0.0:0.125:0.875)")
        backend.bind_context(time, jl.seval("1 .+ collect(0.0:0.125:0.875)"), None)
        module.configure(condition, seed)
        jl.local_optimizer_checks(backend, module, seed)
    if control.source_hashes() != sources:
        raise ValueError("Native check sources changed.")
    print("Local optimizer native checks passed; no fit, optimization or search.")


if __name__ == "__main__":
    check()
