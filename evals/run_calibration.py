"""
`python -m evals.run_calibration` — publish the judge's agreement, per axis.

**Hermetic.** It reads committed judge output and committed labels and computes;
it never calls a model. `services/highlights-agent/run_judge.py` is the half that
spends calls, and its raw output is committed precisely so this half can be
re-run by a stranger with no AWS account and reach the same numbers.

The arithmetic lives in `evals/judge.py` — `majority_band`, `agreement`,
`demotion` — and is tested there. This module only assembles the inputs, which is
the part that is easy to get quietly wrong:

- **A judge refusal is not a missing item.** The answer exists and the judge was
  asked; the gateway would not carry the call. That yields no band, no majority,
  and `agreement` scores it as a disagreement. Dropping those items instead would
  compute agreement over exactly the answers the guardrail found unobjectionable,
  which is a different and much more flattering question.
- **A harness-decided not-applicable IS dropped**, because judge and label agree
  on it by construction. Those items pin the harness rather than the judge, and
  this module asserts that the two agree on *which* items they are — if the
  harness starts calling something not-applicable that the seat labelled
  applicable, that is a defect and it would otherwise vanish into a silent drop.

Owning seat: AI Quality.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

from evals import judge

ROOT = pathlib.Path(__file__).resolve().parents[1]
ITEMS = ROOT / "quality" / "judge" / "calibration" / "items.json"
LABELS = ROOT / "quality" / "judge" / "calibration" / "labels.json"


def load_samples(directory: pathlib.Path) -> dict:
    """`{(run, case_id): {sample: case_record}}` from a directory of judge output."""
    out: dict = collections.defaultdict(dict)
    seen: dict = {}
    for path in sorted(directory.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if "cases" not in doc:
            raise SystemExit(
                f"error: {path.name} carries no `cases`. A truncated or half-written judge "
                "output must not be skipped — skipping it removes samples from the majority "
                "and refusals from the census with nothing to show for it."
            )
        if doc.get("harness_failures"):
            raise SystemExit(
                f"error: {path.name} records harness failures on "
                f"{', '.join(doc['harness_failures'])}. Those cases produced no band because "
                "the harness broke, not because a control refused or the judge disagreed. "
                "Scoring them would demote an axis for the harness's fault. Re-run the sample."
            )
        key = (doc["label"], doc["sample"])
        if key in seen:
            raise SystemExit(
                f"error: {path.name} and {seen[key]} both carry label {doc['label']!r} "
                f"sample {doc['sample']}. Last-one-wins would let a re-rolled call replace a "
                "refusal in both the majority and the refusal census, with nothing in the diff "
                "to show it. Remove one or relabel it."
            )
        seen[key] = path.name
        for case_id, record in doc["cases"].items():
            out[(doc["label"], case_id)][doc["sample"]] = record
    return out


def instruments(directory: pathlib.Path) -> list[dict]:
    """Every distinct instrument block in a run. More than one means the judge
    moved mid-run, and no number computed across it means anything."""
    seen = []
    for path in sorted(directory.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if "instrument" not in doc:
            raise SystemExit(
                f"error: {path.name} carries no `instrument`. Skipping it would let the "
                "moved-instrument guard report one distinct block about a run it never read."
            )
        if doc["instrument"] not in seen:
            seen.append(doc["instrument"])
    return seen


def refusal_census(samples: dict) -> dict:
    """How many judge calls each control refused, by mechanism.

    Split by mechanism deliberately. A guardrail refusal and a classification
    denial are different controls with different owners, and a single "refused"
    count would let one hide inside the other.
    """
    census: collections.Counter = collections.Counter()
    calls = 0
    for by_sample in samples.values():
        for record in by_sample.values():
            if record.get("not_applicable"):
                continue
            calls += 1
            mechanism = record.get("refused_by_gateway")
            census[mechanism or "served"] += 1
    # Every known mechanism, explicitly, including the ones that fired zero times.
    # An absent `classification` key is indistinguishable from "not measured", and
    # SPEC/03 amendment 8 pre-registered "classification refusals: 0 of 75" with the
    # falsifier "any" - a record that cannot resolve the prediction it was written
    # to test is not a record of it.
    zeros = {m: 0 for m in ("served", "guardrail", "classification")}
    return {"model_eligible_calls": calls, **zeros, **dict(sorted(census.items()))}


def assemble(split: str, samples: dict, k: int, only: tuple = ()) -> tuple[list, list]:
    """`(scorable, dropped)` — one entry per calibration item in `split`.

    `only` restricts to named item ids. A **scoped** measurement is the honest
    shape when an instrument change can reach some items and provably not others:
    re-rolling the untouched ones produces differences indistinguishable from
    run-to-run variance, and a reader shown two full tables reads those as
    instrument effects. Every report says whether it was scoped, and a scoped one
    is never a split result."""
    items = {i["id"]: i for i in json.loads(ITEMS.read_text(encoding="utf-8"))["items"]}
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    labels = labels["labels"] if isinstance(labels, dict) else labels

    scorable, dropped = [], []
    for label in labels:
        item = items[label["item"]]
        if item["split"] != split:
            continue
        if only and label["item"] not in only:
            continue
        key = (item["run"], item["case_id"])
        by_sample = samples.get(key, {})
        if not by_sample:
            raise SystemExit(f"error: no judge output for {key} (item {label['item']})")

        missing = [s for s in range(1, k + 1) if s not in by_sample]
        if missing:
            raise SystemExit(
                f"error: {key[0]} {key[1]} has no judge output for sample(s) "
                f"{', '.join(map(str, missing))} at k={k}. If this directory holds a run at a "
                f"different k, pass --k {len(by_sample)}. Read as a disagreement instead, a "
                "missing sample would accuse the calibration labels of a defect they do not have."
            )
        harness_na = all(by_sample.get(s, {}).get("not_applicable") for s in range(1, k + 1))
        seat_na = not label.get("applicable", True)
        if harness_na != seat_na:
            raise SystemExit(
                f"error: {label['item']} ({key[0]} {key[1]} {label['axis']}) — the harness "
                f"calls it {'not-' if harness_na else ''}applicable and the seat labelled it "
                f"{'not-' if seat_na else ''}applicable. Agreement is not computable over an "
                "item the two halves disagree about the existence of."
            )
        if seat_na:
            dropped.append({**label, "reason": by_sample.get(1, {}).get("not_applicable")})
            continue

        bands = [by_sample.get(s, {}).get("axes", {}).get(label["axis"]) for s in range(1, k + 1)]
        # No `if majority_band(...) is None: continue` here, and it is worth saying
        # why in the code rather than only in the docstring. Skipping undecided
        # items would drop exactly the ones a control refused, compute agreement
        # over the answers the guardrail permitted, and delete a fully-blocked axis
        # from the published table instead of demoting it. It fails silently and in
        # the flattering direction.
        scorable.append({
            "item": label["item"],
            "axis": label["axis"],
            "run": item["run"],
            "case_id": item["case_id"],
            "label": label["final"],
            "band": judge.majority_band(bands),
            "samples": bands,
        })
    return scorable, dropped


def correction_rate(split: str) -> dict:
    """How often the seat's disposition moved a drafted label.

    Published beside every agreement figure, in the same sentence, because a
    label the seat agreed with 30 times out of 30 is a weaker reference than one
    it corrected — and the reader cannot tell which they are looking at otherwise.
    """
    items = {i["id"]: i for i in json.loads(ITEMS.read_text(encoding="utf-8"))["items"]}
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    labels = labels["labels"] if isinstance(labels, dict) else labels
    rows = [x for x in labels if items[x["item"]]["split"] == split]
    moved = [x for x in rows if x.get("drafted") != x.get("final")]
    return {"n": len(rows), "corrected": len(moved),
            "rate": round(len(moved) / len(rows), 4) if rows else 0.0}


def diagnostics(rows: list) -> dict:
    """Two things the published table cannot show, and both change how it reads.

    **Decided-only agreement.** The published figure counts an undecided item as a
    disagreement, which is right: a judge that would not answer is not calibrated
    by the answers where it did. But it means a fully blocked axis and a fully
    wrong axis both read `0.00`, and those call for different work by different
    seats. This is the number over the items the judge actually answered. It is a
    diagnostic and is never the published figure — quoting it as agreement would be
    computing agreement over exactly the answers the guardrail permitted.

    **What made each item undecided.** No majority can mean the controls refused
    the call, or it can mean the judge returned three different bands. The first is
    a finding about the gateway; the second is a finding about the judge. A single
    `undecided` count cannot tell a reader which platform they have.
    """
    decided = [r for r in rows if r["band"] is not None]
    agree = sum(1 for r in decided if r["band"] == r["label"])
    def usable(row):
        return sum(1 for s in row["samples"] if s in judge.BANDS)

    undecided = [r for r in rows if r["band"] is None]
    blocked = sum(1 for r in undecided if usable(r) < 2)
    # Only a row where every sample came back counts as the judge splitting bands.
    # A row with two usable samples that disagree is NOT that: a control removed the
    # tiebreak, so the split is as much the gateway's doing as the judge's, and
    # filing it under "the judge disagreed with itself" would attribute a gateway
    # finding to the instrument under test.
    split_bands = sum(1 for r in undecided if usable(r) == len(r["samples"]))
    ambiguous = len(undecided) - blocked - split_bands
    return {
        "decided_only": {
            "n": len(decided),
            "exact": agree,
            "raw": round(agree / len(decided), 4) if decided else None,
        },
        "undecided_because_controls_refused": blocked,
        "undecided_because_judge_split_bands": split_bands,
        "undecided_with_a_refused_tiebreak": ambiguous,
    }


def report(split: str, directory: pathlib.Path, k: int, only: tuple = ()) -> dict:
    if split == "held-out":
        # Enforced, not promised. `held_out_guard` had zero callers when it landed,
        # while its own docstring claimed to be "the one place the spec's central
        # discipline is enforced rather than promised". This is that place.
        judge.held_out_guard()
    samples = load_samples(directory)
    marks = instruments(directory)
    if len(marks) != 1:
        raise SystemExit(
            f"error: {len(marks)} distinct instrument blocks in {directory}. The judge moved "
            "mid-run; no agreement number computed across it means anything."
        )
    # Which RECORDED instrument produced this directory. Not "does it match the
    # current freeze": a directory legitimately measured under a retired instrument
    # keeps its published number (ADR-025), and refusing to re-score it would make
    # the instrument-A figure un-re-derivable by the stranger the whole hermetic
    # half exists for. What must never happen is scoring output from an instrument
    # nobody recorded.
    #
    # Enumerated from `judge.freeze_keys()` rather than re-listed here. This check
    # named four digests while `instrument()` recorded five, so instrument-A output
    # scored cleanly under the instrument-B freeze -- A and B are byte-identical on
    # the four it looked at and differ only on the one it did not. The guard whose
    # own message says "checking that the run used ONE instrument is not the same as
    # checking it used the FROZEN one" could not see the half of the instrument that
    # was refusing the calls.
    named = judge.matching_instrument(marks[0])
    if named is None:
        pinned = judge.frozen()
        drifted = sorted(k for k in judge.freeze_keys()
                         if pinned.get(k) != marks[0].get(k))
        raise SystemExit(
            f"error: the committed judge output in {directory} was produced by an instrument "
            f"no entry in quality/judge/frozen.json records (differs from the current pin on "
            f"{', '.join(drifted) or 'nothing listed'}). Checking that the run used ONE "
            "instrument is not the same as checking it used a RECORDED one. Freeze the "
            "instrument that produced it, or re-run under one that is recorded."
        )

    scorable, dropped = assemble(split, samples, k, only)
    by_axis = collections.defaultdict(list)
    for row in scorable:
        by_axis[row["axis"]].append(row)

    axes = {}
    for axis, rows in sorted(by_axis.items()):
        stats = judge.agreement([{"axis": axis, "label": r["label"], "band": r["band"]}
                                 for r in rows])
        axes[axis] = judge.demotion(axis, stats)

    return {
        "split": split,
        # A scoped report is not a split result and must never be read as one. The
        # key is always present so its absence cannot be mistaken for "not scoped"
        # in a file written before the field existed.
        "scope": {"items": sorted(only), "of_split": split} if only else None,
        "k_judge": k,
        "instrument": marks[0],
        # Which recorded instrument, by name. A report that shows two tables without
        # saying which instrument produced each invites a reader to read run-to-run
        # variance as an instrument effect.
        "instrument_name": named,
        "refusals": refusal_census(samples),
        "correction_rate": correction_rate(split),
        "dropped_not_applicable": [{"item": d["item"], "axis": d["axis"], "reason": d["reason"]}
                                   for d in dropped],
        "diagnostics": diagnostics(scorable),
        "axes": axes,
        "rows": scorable,
    }


def render(result: dict) -> str:
    lines = []
    ref = result["refusals"]
    served = ref.get("served", 0)
    calls = ref["model_eligible_calls"]
    lines.append(f"split: {result['split']}   k_judge: {result['k_judge']}")
    if result.get("scope"):
        lines.append(f"SCOPED to {len(result['scope']['items'])} item(s): "
                     f"{', '.join(result['scope']['items'])}. This is NOT a "
                     f"{result['split']} split result and its axis rows are not the split's.")
    # Named, not only fingerprinted. Two reports shown side by side without the name
    # invite a reader to read run-to-run variance as an instrument effect.
    lines.append(f"instrument: {result.get('instrument_name', '?')} - "
                 f"prompt {result['instrument']['prompt_sha256'][:12]} "
                 f"rubric-axes {result['instrument']['rubric_axes_sha256'][:12]}")
    lines.append("")
    lines.append(f"model-eligible judge calls: {calls}   served: {served}")
    for mechanism, count in ref.items():
        if mechanism in ("model_eligible_calls", "served"):
            continue
        lines.append(f"  refused by {mechanism}: {count} ({count / calls:.0%})")
    cr = result["correction_rate"]
    lines.append(f"seat correction rate on this split: {cr['corrected']}/{cr['n']} = {cr['rate']:.0%}")
    lines.append("")

    head = f"{'axis':<30}{'n':>3}{'exact':>7}{'raw':>7}{'kappa':>8}{'undec':>7}  status"
    lines.append(head)
    lines.append("-" * len(head))
    for axis, d in result["axes"].items():
        kappa = "n/a" if d["kappa"] is None else f"{d['kappa']:.2f}"
        lines.append(f"{axis:<30}{d['n']:>3}{d['exact']:>7}{d['raw']:>7.2f}{kappa:>8}"
                     f"{d['undecided']:>7}  {d['status'].upper()}")
    lines.append("")
    for axis, d in result["axes"].items():
        if d["status"] == "demoted":
            lines.append(f"{axis} — DEMOTED, so it cannot veto and cannot enter a verdict:")
            for reason in d["reasons"]:
                lines.append(f"  - {reason}")
            lines.append(f"  label distribution: {d['label_distribution']}")
    diag = result["diagnostics"]
    dec = diag["decided_only"]
    lines.append("diagnostics — NOT the published agreement figure:")
    raw = "n/a" if dec["raw"] is None else f"{dec['raw']:.2f}"
    lines.append(f"  agreement over items the judge actually answered: "
                 f"{dec['exact']}/{dec['n']} = {raw}")
    lines.append(f"  undecided because the controls refused the call: "
                 f"{diag['undecided_because_controls_refused']}")
    lines.append(f"  undecided because the judge returned different bands: "
                 f"{diag['undecided_because_judge_split_bands']}")
    calibrated = [a for a, d in result["axes"].items() if d["status"] == "calibrated"]
    lines.append("")
    lines.append(f"calibrated axes: {calibrated or 'none — the judge is advisory in full'}")
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="run_calibration")
    p.add_argument("--judged", required=True, help="directory of committed judge output")
    p.add_argument("--split", default="held-out", choices=("held-out", "dev"))
    p.add_argument("--k", type=int, default=3)
    p.add_argument("--out", help="write the full result as JSON")
    p.add_argument("--items", help="comma-separated calibration item ids: score only these. "
                                   "Produces a SCOPED report, which is not a split result")
    args = p.parse_args(argv)

    if args.k % 2 == 0:
        print(f"error: k_judge={args.k} is even, so a strict majority is not always "
              "reachable and 'undecided' would mean two different things.", file=sys.stderr)
        return 2

    only = tuple(i.strip() for i in args.items.split(",") if i.strip()) if args.items else ()
    result = report(args.split, pathlib.Path(args.judged), args.k, only)
    print(render(result))
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
