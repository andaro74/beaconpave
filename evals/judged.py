"""
Turning a directory of raw judge output into the parts of a judged history entry.

Hermetic, and that is the point. The model call is the only thing nobody can
regenerate; everything after it — majority band, veto, the axes table, the refusal
census — is a pure function of committed files, so a stranger with no AWS account
can re-derive a judged row from the tree (ADR-025).

**What a judged entry is, per ADR-027.** The same answers, read by a different
instrument. Not `supersedes`, which means the earlier row was wrong. Not `arm`,
which means a different system produced the answers. A judged and an unjudged
`m00b` are the same service, the same prompt, the same 25 answers, the same bytes.

**Two of the three fields describe different objects, and conflating them is the
trap this module exists to avoid.**

- `guardrail_refusals` is a property of **this run**: how many of its own judge
  calls each control refused.
- `judge_axes` is a property of **the judge**: the calibration measured on the
  held-out split, which decides whether any band is allowed to veto anything.

They can come from different instruments, and at M03 they do. The anchor runs
under instrument B; the published calibration was measured under instrument A,
and instrument B was measured only on the single held-out item A's defect
touched. `instrument.calibrated_by` records which instrument produced the
calibration, because a reader who assumes it is the same one as `instrument`
would be wrong here and would have no way to find out.

Owning seat: AI Quality.
"""
from __future__ import annotations

import pathlib

from evals import judge, run_calibration

ROOT = pathlib.Path(__file__).resolve().parents[1]


def calibrated_axes(calibration: dict) -> set:
    """Axes a judge is allowed to veto with.

    Read from a published calibration report rather than recomputed, so a judged
    entry and the agreement number that licenses it cannot disagree. At M03 this
    is empty: every axis demoted, so `veto` consults nothing and a judged score is
    identical to its deterministic score for every case."""
    return {axis for axis, row in (calibration.get("axes") or {}).items()
            if row.get("status") == "calibrated"}


def bands_by_case(samples: dict, k: int) -> dict:
    """`{case_id: {axis: majority band}}` for one run's judge output.

    `samples` is keyed by `(label, case_id)` and one directory holds one run, so
    the label is dropped here rather than threaded through. A directory holding
    two labels is a caller error and `run_calibration.instruments` already refuses
    the shape it produces."""
    out: dict = {}
    for (_, case_id), by_sample in samples.items():
        axes: dict = {}
        for sample in range(1, k + 1):
            for axis, band in (by_sample.get(sample, {}).get("axes") or {}).items():
                axes.setdefault(axis, []).append(band)
        out[case_id] = {axis: judge.majority_band(bands) for axis, bands in axes.items()}
    return out


def vetoes(bands: dict, calibrated: set) -> dict:
    """`{case_id: [axis, ...]}` for every case a calibrated axis subtracts.

    Only `0.0` vetoes and only on a calibrated axis; an undecided band never
    does. With `calibrated` empty this is empty by construction, which is what
    "advisory in full" means expressed as arithmetic rather than as a claim."""
    out = {}
    for case_id, axes in bands.items():
        hit, which = judge.veto(axes, calibrated)
        if hit:
            out[case_id] = which
    return out


def entry_parts(judged_dir: pathlib.Path, calibration: dict, k: int) -> dict:
    """The judged half of a history entry, derived from committed files alone.

    Raises rather than degrades on every shape that would quietly flatter the
    result: a directory spanning two instruments, an instrument no
    `frozen.json` entry records, or a calibration report whose own instrument is
    unnamed. A judged row naming an instrument nobody can look up is a
    fingerprint of an object that does not exist (ADR-027, rule 4)."""
    samples = run_calibration.load_samples(judged_dir)
    marks = run_calibration.instruments(judged_dir)
    if len(marks) != 1:
        raise SystemExit(
            f"error: {len(marks)} distinct instrument blocks in {judged_dir}. The judge moved "
            "mid-run; no judged score computed across it means anything."
        )
    instrument = dict(marks[0])
    named = judge.matching_instrument(instrument)
    if named is None:
        raise SystemExit(
            f"error: the judge output in {judged_dir} was produced by an instrument no entry "
            "in quality/judge/frozen.json records. A judged history row is append-only and "
            "names its instrument; naming one nobody can look up is worse than not recording "
            "it (ADR-027)."
        )
    instrument["name"] = named
    instrument["k_judge"] = k

    calibrated_by = calibration.get("instrument_name")
    if not calibrated_by:
        raise SystemExit(
            "error: the calibration report does not name the instrument that produced it. "
            "The axes table decides whether any band may veto, so an unnamed one leaves a "
            "reader unable to tell which instrument licensed the veto."
        )
    # Recorded even when it equals `instrument`, because its absence would then be
    # the only way to say "the same one" and absence already means "not recorded".
    instrument["calibrated_by"] = calibrated_by

    calibrated = calibrated_axes(calibration)
    bands = bands_by_case(samples, k)
    return {
        "instrument": instrument,
        "judge_axes": calibration.get("axes") or {},
        "guardrail_refusals": run_calibration.refusal_census(samples),
        "calibrated": sorted(calibrated),
        "vetoes": vetoes(bands, calibrated),
        "bands": bands,
    }
