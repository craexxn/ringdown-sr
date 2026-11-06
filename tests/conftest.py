"""Reusable valid sources for rejection tests; integration fixtures remain fresh."""

import pytest


@pytest.fixture(scope="session")
def assessment_replay_template(tmp_path_factory):
    import test_future_assessment as fixtures
    from test_symbolic_pilot import small_config

    from ringdown_sr.pilot import run_pilot

    root = tmp_path_factory.mktemp("assessment-replay-template")
    config = root / "input.toml"
    config.write_text(small_config())
    with pytest.MonkeyPatch.context() as patch:
        fixtures.bind_software(patch)
        calls = fixtures.bind_worker(patch)
        assert (
            run_pilot(
                config, root / "run", assessment_output=root / "assessment"
            ).status
            == "success"
        )
        assert len(calls) == 3

    def snapshot():
        return {
            p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()
        }

    original = snapshot()
    yield root
    assert snapshot() == original, "A rejection test modified the shared template."
