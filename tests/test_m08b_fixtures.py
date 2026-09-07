"""
The planted M08b run is what its builder produces (SPEC/08b, PR 2).

`tests/fixtures/m08b/planted/` is the run the three readers under
`milestones/M08b/` are tested on before any real answer file exists. Its
answer files, trajectories, sidecar, calibration record and grants file are
written by `build_planted.py` from the live cases file; its two transcripts are
the real scorer's output over them. A fixture that drifts from its builder —
or a scorer whose output moved — is caught here, not in the readers' tests.

Hermetic (G8): the scorer runs in a subprocess with no model and no network.
Owning seats: AI Quality · Platform Engineering.
"""
from __future__ import annotations

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tests" / "fixtures" / "m08b" / "build_planted.py"
PLANTED = ROOT / "tests" / "fixtures" / "m08b" / "planted"
CANONICAL = "tests/fixtures/m08b/planted"

BUILT = ("goldens-run-1.json", "goldens-run-2.json", "goldens-run-3.json",
         "goldens-run-1-trajectory.json", "goldens-run-2-trajectory.json",
         "goldens-run-3-trajectory.json", "goldens-run-refusals.json",
         "calibration.json", "withheld-grants.json")
TRANSCRIPTS = ("per-sample.txt", "goldens-score.txt")


def _lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def test_the_planted_run_is_what_its_builder_produces(tmp_path):
    spec = importlib.util.spec_from_file_location("build_planted", BUILDER)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    out = tmp_path / "planted"
    builder.build(out)
    for name in BUILT:
        assert _lf((out / name).read_bytes()) == _lf((PLANTED / name).read_bytes()), (
            f"{name} drifted from what build_planted.py produces; re-run the builder and "
            "commit the result, or find which input moved")
    for name in TRANSCRIPTS:
        rebuilt = (out / name).read_text(encoding="utf-8").replace(out.resolve().as_posix(), CANONICAL)
        committed = (PLANTED / name).read_text(encoding="utf-8")
        assert rebuilt.replace("\r\n", "\n") == committed.replace("\r\n", "\n"), (
            f"{name} drifted: the scorer's output over the planted files moved, or the "
            "committed transcript was edited by hand")


def test_the_planted_run_carries_the_shapes_the_readers_are_tested_on():
    """A builder edit that quietly dropped a plant would leave every reader
    test asserting about a run that no longer contains what it names."""
    import json

    runs = [json.loads((PLANTED / f"goldens-run-{n}.json").read_text(encoding="utf-8")) for n in (1, 2, 3)]
    assert all(len(run) == 25 for run in runs)
    assert [len(run["recommend-013"]["usage"]["calls"]) for run in runs] == [4, 4, 4]
    assert runs[2]["grounded-019"]["usage"]["tokens_in"] == 8181
    assert runs[1]["headroom-005"]["usage"]["tokens_in"] == 7690
    assert "refused_by_gateway" in runs[0]["recommend-003"]["answer"]
    assert "refused_by_gateway" in runs[2]["recommend-003"]["answer"]
    assert runs[1]["recommend-003"]["answer"]["entitlement"]["entitled"] is True
    assert [run["blackout-008"]["usage"]["calls"][0]["tokens_in"] for run in runs] == [1980] * 3
    assert all(run["blackout-001"]["usage"]["tokens_out"] == 330 for run in runs)
