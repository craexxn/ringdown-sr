"""Versioned stopping-rule profile built on the unchanged native 300/5 guard."""

import copy
import json
import os
from pathlib import Path

from . import outer_search_ladder as prior
from .pilot import _sha256
from .symbolic import ROOT

FORMAT = "ringdown-sr-iteration-time-worker-1"
PROFILE_FORMAT = "ringdown-sr-iteration-time-profile-1"
PLAN = "docs/iteration_time_budget_plan.md"
PLAN_COMMIT = "1aeedcce6a0f6c5683b2c4176161e14ed83ffa6d"
PLAN_SHA256 = "24d7486cf097fc89a329fbae452f132ca5f661f49a969830e62b79f88edaedab"
CONFIGURATION = "data/iteration_time_protocol.json"
CONFIGURATION_SHA256 = (
    "a7081e34a317c8ac4c839b4671e6e00a11f012682ed6d4d710f5a09edf879396"
)
NATIVE_MODULE = "SearchTimeBudget"
OBJECTIVE = "Main.SearchTimeBudget.objective"
LIMIT_SECONDS, WORKER_LIMIT_SECONDS = 7200, 1800
LIMITS = {
    "iterations": None,
    "time": 400.0,
    "technical_timeout": 0.01,
    "technical_reserve": 400.0,
}
JULIA_THREADS = {
    "JULIA_NUM_THREADS": "1,0",
    "PYTHON_JULIACALL_THREADS": "1,0",
    "JULIA_NUM_GC_THREADS": "1",
}
CONDITIONS = ("iterations", "time")
SEEDS = (20261201, 20261210, 20261211, 20261212)
RUNTIME = {
    **prior.RUNTIME,
    "worker.py": "scripts/time_budget_worker.py",
    "backend.py": "scripts/time_budget_backend.py",
    "SearchTimeBudget.jl": "julia/src/SearchTimeBudget.jl",
    "SearchBudgetClock.jl": "julia/src/SearchBudgetClock.jl",
}
load_module = prior.load_module


def configuration():
    for name, digest in ((PLAN, PLAN_SHA256), (CONFIGURATION, CONFIGURATION_SHA256)):
        if _sha256((ROOT / name).read_bytes()) != digest:
            raise ValueError("Changed frozen iteration/time protocol.")
    return json.loads((ROOT / CONFIGURATION).read_bytes())


def checked_backend_sources(jl):
    import pysr.sr

    native = Path(str(jl.seval("dirname(pathof(SymbolicRegression))")))
    paths = {
        "pysr/sr.py": Path(pysr.sr.__file__),
        **{
            "SymbolicRegression/src/" + name: native / name
            for name in ("SymbolicRegression.jl", "SearchUtils.jl", "Options.jl")
        },
    }
    hashes = {name: _sha256(path.read_bytes()) for name, path in paths.items()}
    if hashes != configuration()["reviewed_backend_sources"]:
        raise ValueError("Pinned timer/backend source differs from the reviewed bytes.")
    return hashes


def checked_runtime(jl):
    # PySR otherwise defaults Julia to auto and enables concurrent GC. Serial
    # equation_search and BLAS limits alone do not bind these runtime threads.
    if any(os.environ.get(key) != value for key, value in JULIA_THREADS.items()):
        raise ValueError("Explicit Julia and GC thread limits must precede import.")
    jl.seval("using LinearAlgebra")
    native = jl.seval("""(;
        cpu_name=string(Sys.CPU_NAME), cpu_threads=Sys.CPU_THREADS,
        word_size=Sys.WORD_SIZE, julia_threads=Threads.nthreads(:default),
        interactive_threads=Threads.nthreads(:interactive), gc_threads=Threads.ngcthreads(),
        blas_threads=LinearAlgebra.BLAS.get_num_threads())""")
    record = {str(key): getattr(native, str(key)) for key in jl.keys(native)}
    record.update(
        affinity=sorted(os.sched_getaffinity(0)), thread_environment=dict(JULIA_THREADS)
    )
    validate_runtime(record)
    return record


def validate_runtime(record):
    if (
        not isinstance(record, dict)
        or set(record)
        != {
            "cpu_name",
            "cpu_threads",
            "word_size",
            "julia_threads",
            "interactive_threads",
            "gc_threads",
            "blas_threads",
            "affinity",
            "thread_environment",
        }
        or not isinstance(record["cpu_name"], str)
        or not record["cpu_name"]
        or type(record["cpu_threads"]) is not int
        or record["cpu_threads"] < 1
        or record["word_size"] != 64
        or record["thread_environment"] != JULIA_THREADS
    ):
        raise ValueError("Incomplete native hardware/thread evidence.")
    if (
        record["julia_threads"] != 1
        or record["interactive_threads"] != 0
        or record["gc_threads"] != 1
        or record["blas_threads"] != 1
        or len(record["affinity"]) != 1
    ):
        raise ValueError(
            "Effective native threads or CPU affinity violate the budget profile."
        )


def source_hashes():
    configuration()
    return {
        **prior.source_hashes(),
        **{
            name: _sha256((ROOT / name).read_bytes())
            for name in (
                PLAN,
                CONFIGURATION,
                *RUNTIME.values(),
                "src/ringdown_sr/time_budget_profile.py",
            )
        },
    }


def checked_profile(document):
    if (
        not isinstance(document, dict)
        or set(document) != {"format", "condition"}
        or document["format"] != PROFILE_FORMAT
        or document["condition"] not in LIMITS
    ):
        raise ValueError("Invalid iteration/time profile.")
    return document["condition"]


def profile_parameters(budget, condition):
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    return {
        **prior.profile_parameters(budget, "local_300_5"),
        "loss_function": OBJECTIVE,
        "timeout_in_seconds": LIMITS[condition],
        "warmup_maxsize_by": 0.0,
    }


def normalized_options(record, condition, support):
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    fields = support.backend_without_output(record["backend_options"])
    limit = LIMITS[condition]
    names = (OBJECTIVE, OBJECTIVE.removeprefix("Main."))
    if (
        record["condition"] != condition
        or fields.get("loss_function")
        not in [{"type": f"typeof({name})", "value": name} for name in names]
        or fields.get("timeout_in_seconds")
        != {
            "type": "Nothing" if limit is None else "Float64",
            "value": "nothing" if limit is None else str(limit),
        }
        or fields.get("warmup_maxsize_by") != {"type": "Float64", "value": "0.0"}
    ):
        raise ValueError("Wrong effective time-budget options or objective.")
    normalized = copy.deepcopy(record)
    normalized["condition"] = "local_300_5"
    for field in normalized["backend_options"]:
        if field["name"] == "loss_function":
            field.update(type=f"typeof({prior.OBJECTIVE})", value=prior.OBJECTIVE)
        elif field["name"] == "timeout_in_seconds":
            field.update(type="Nothing", value="nothing")
    return normalized


def verify_options(record, seed, condition, base, support):
    return prior.verify_options(
        normalized_options(record, condition, support),
        seed,
        "local_300_5",
        base,
        support,
    )


def common_options(record, support):
    return prior.common_options(
        normalized_options(record, record["condition"], support), support
    )


def common_parameters(parameters):
    return {
        k: v
        for k, v in parameters.items()
        if k not in {"random_state", "niterations", "timeout_in_seconds"}
    }


def verify_tree_grammar(tree, condition):
    checked_profile({"format": PROFILE_FORMAT, "condition": condition})
    return prior.verify_tree_grammar(tree, "local_300_5")


def expected_grammar_cases():
    return [
        {**case, "condition": condition}
        for condition in CONDITIONS
        for case in prior.expected_grammar_cases()
    ]


def verify_manifest(directory, runtime):
    module = load_module(
        ROOT / "src/ringdown_sr/trigonometric_grammar.py", "ringdown_sr._time_manifest"
    )
    module.FORMAT, module.source_hashes, module.RUNTIME = FORMAT, source_hashes, RUNTIME
    return module.verify_manifest(directory, runtime)


def invocation_record(iterations):
    return {**prior.invocation_record(iterations), "format": FORMAT}


class SearchInvocationGuard(prior.SearchInvocationGuard):
    def record(self):
        return {**super().record(), "format": FORMAT}


def load_driver():
    import sys

    factory = load_module(
        ROOT / "scripts/run_search_duration.py", "time_duration_factory"
    )
    driver = factory.load_driver(control=sys.modules[__name__])
    driver.EXTRA_FILES += (
        "LocalOptimizerBudget.jl",
        "SearchTimeBudget.jl",
        "SearchBudgetClock.jl",
        "time_budget_clock.json",
        "time_budget_runtime.json",
    )
    driver.expected_grammar_cases = expected_grammar_cases
    return driver


# The single-cell bridge owns the frozen schedule and report, not the historical
# twenty-cell CLI. These are required only by the reused driver factory.
def planned_cells():
    raise ValueError("Use the bound iteration/time bridge schedule.")


def comparison(*args, **kwargs):
    raise ValueError("Use the bound iteration/time paired comparison.")
