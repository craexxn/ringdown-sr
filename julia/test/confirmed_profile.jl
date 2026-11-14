module ConfirmedProfileChecks

using SymbolicRegression
using Random: Xoshiro
using LinearAlgebra: Diagonal, diag
const SR = SymbolicRegression

function run(root)
    records = NamedTuple[]
    native_files = ("RingdownSRLoss.jl", "RingdownSRSearch.jl", "RepresentationProfiles.jl",
        "FreeOptimizerBudget.jl", "TrigonometricGrammar.jl", "LocalOptimizerBudget.jl",
        "SearchTimeBudget.jl")
    for kind in ("ranking", "constant", "linear"), weighting in ("full", "diagonal", "ordinary")
        scope = Module(Symbol("Confirmed_", kind, "_", weighting))
        for filename in native_files
            Base.include(scope, joinpath(root, "julia", "src", filename))
        end
        # Each private module was loaded after this function was compiled.
        Base.invokelatest() do
        backend, guard = scope.RingdownSRSearch, scope.SearchTimeBudget
        time, observed, full = if kind == "ranking"
            ([0., 1.], [0., 0.], [2. 1.; 1. 2.])
        elseif kind == "constant"
            ([0., 1.], [1., 3.], [4. 2.; 2. 10.])
        else
            ([0., 1., 2.], [0., 1., 0.], [2. 1. 0.; 1. 2. 0.; 0. 0. 1.])
        end
        covariance = weighting == "full" ? full : weighting == "diagonal" ? Matrix(Diagonal(diag(full))) : nothing
        backend.bind_context(time, observed, covariance)
        guard.configure("iterations", 20261401; should_simplify=false)
        options = guard.reference_options("iterations", 20261401; should_simplify=false)
        options.optimizer_options.iterations == 300 && options.optimizer_nrestarts == 5 || error("Wrong local profile.")
        options.should_simplify === false && options.use_frequency === true && options.use_frequency_in_tournament === true || error("Wrong representation policy.")
        dataset = backend.CONTEXT[]._dataset
        c(value) = Node(Float64; val=Float64(value))
        t() = Node(Float64; feature=1)
        op(index, a, b) = Node(Float64; op=index, children=(a,b))
        linear(a,b) = op(1, c(a), op(3,c(b),t()))
        if kind == "ranking"
            trees = (c(-1.), linear(-.75,1.5))
            losses = [SR.PopMember(dataset, tree, options; deterministic=true, ref=1).loss for tree in trees]
            expected = weighting == "full" ? [1/3,9/16] : weighting == "diagonal" ? [1/2,9/32] : [1.,9/16]
            all(isapprox.(losses,expected; atol=1e-14,rtol=0)) || error("Native structural ranking lost weighting.")
            push!(records,(;kind,weighting,losses,parameters=Float64[],calls=backend.CALLS[]))
        else
            tree = kind == "constant" ? c(-1.) : linear(1.,-1.)
            member = SR.PopMember(dataset,tree,options;deterministic=true,ref=1)
            member, evaluations = SR.optimize_constants(dataset,member,options;rng=Xoshiro(20261401))
            parameters = collect(SR.get_optimizable_parameters(member.tree,options)[1])
            expected_parameters, expected_loss = if kind == "constant"
                weighting == "full" ? ([7/5],1/5) : weighting == "diagonal" ? ([11/7],1/7) : ([2.],1.)
            else
                weighting == "full" ? ([0.,1/7],4/21) : weighting == "diagonal" ? ([4/11,-1/11],4/33) : ([1/3,0.],2/9)
            end
            all(isapprox.(parameters,expected_parameters;atol=1e-6,rtol=0)) || error("Native constant optimum lost weighting.")
            isapprox(member.loss,expected_loss;atol=1e-11,rtol=0) || error("Native optimized loss lost weighting.")
            evaluations > 0 || error("No actual constant optimization observed.")
            push!(records,(;kind,weighting,losses=[member.loss],parameters,calls=backend.CALLS[]))
        end
        # Constant optimization may copy its Options object. Verify the actual
        # callback object, including every guarded field, rather than identity
        # with the caller's otherwise equal reference object.
        guard.verification_record(backend.LAST_OPTIONS[]).status == "verified" || error("Native profile guard missing.")
        end
    end
    return records
end

end
