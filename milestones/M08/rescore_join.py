"""
M08 PR 4: the re-score joined to the census, per sample, at the signed ceiling.

SPEC/08's one claim is a per-sample statement — every committed stage-2 answered
sample at three model calls or fewer passes `tokens_in` at the re-derived
ceiling and every sample at four or more fails it — and the k=3 transcript
cannot show it: `run_evals` prints one representative sample's failures per
case. This reader joins the three single-file transcripts at the live ceiling
(`per-sample-at-7700.txt`) to the census's per-sample `calls` column
(`context-census.json`) and writes the join as a record, one row per sample,
with the claim's two halves and the side-prediction's falsifiers computed from
the rows rather than asserted.

Inputs, every one committed: the two transcripts PR 4 ran once, PR 2's
transcript at 6000 (for what each flipped sample failed on before), the census
record, M07's history row (the FAIL each flip is read against), and the cases
file (the ceiling the transcripts were scored at, read so the record names it
and the budget lines are checked against it). Zero model calls; no network
module; the `usage` fields are read from a transcript, never written.

The count on the k=3 transcript is carried into the record because it is PR 4's
number — the first pass count at the new ceiling (SPEC/08 constraint 2) — and
because the flip set is read from it. The reader takes no ceiling argument and
computes no count at any other.

Owning seats, by the two-key rule that covers it: AI Quality (the ceiling this
join measures), Platform Engineering (the loop whose call counts it reads),
Security (what "catches a runaway loop" means).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "milestones" / "M08"
OUT = HERE / "rescore-join.json"

PER_SAMPLE_NEW = HERE / "per-sample-at-7700.txt"
PER_SAMPLE_OLD = HERE / "per-sample-at-6000.txt"
K3 = HERE / "goldens-rescore.txt"
CENSUS = HERE / "context-census.json"
M07_ROW = ROOT / "evals" / "history" / "m07-tools-goldens.json"
CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"

INPUTS = (PER_SAMPLE_NEW, PER_SAMPLE_OLD, K3, CENSUS, M07_ROW, CASES)

#: SPEC/08 amendment 1 / ADR-073 amendment 2 §1, verbatim: the ten that flip,
#: the five that cannot, the two that pass already, the bound and the point.
PREDICTED_FLIPS = (
    "entitlement-002", "entitlement-010", "entitlement-011", "recommend-015",
    "grounded-017", "grounded-019", "brand-020", "edge-024", "headroom-005",
    "headroom-026",
)
PREDICTED_HELD = ("blackout-001", "blackout-007", "blackout-008", "blackout-009", "concise-022")
PASSING_AT_M07 = ("grounded-016", "brand-021")
BOUND = (2, 12)
PREDICTED_N = 12

HEADER_RE = re.compile(r"^=== (?P<cmd>.*)$")
ANSWERS_RE = re.compile(r"--answers milestones/M07/goldens-run-(?P<sample>\d)\.json")
CASE_RE = re.compile(r"^(?P<case>[a-z]+-\d{3})\s+(?P<result>PASS|FAIL)(?:\s+\[(?P<samples>[A-Z ]+)\])?\s*$")
ASSERT_RE = re.compile(r"^\s+- (?P<kind>[a-z_]+): (?P<detail>.*)$")
BUDGET_RE = re.compile(r"(?P<axis>tokens_in|tokens_out)=(?P<value>\d+) over (?P<ceiling>\d+)")
COUNT_RE = re.compile(r"^(?P<passed>\d+)/(?P<total>\d+) passed \((?P<failed>\d+) failed, (?P<infra>\d+) infra\)")


def _sha256(path: pathlib.Path) -> str:
    """LF-normalised, as `context_census.py` digests its inputs: the committed
    text, not the checkout (`hash-the-blob-not-the-checkout`)."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_transcript(text: str) -> list[dict]:
    """Every `=== command` block: the sample it scored (from `--answers`, one per
    block for a per-sample file, None for the k=3 block), each case's result, its
    per-sample bracket when printed, and its failing asserts by kind."""
    blocks: list[dict] = []
    block: dict | None = None
    case: dict | None = None
    for line in text.splitlines():
        header = HEADER_RE.match(line)
        if header:
            found = ANSWERS_RE.findall(header.group("cmd"))
            block = {"command": header.group("cmd"),
                     "sample": int(found[0]) if len(found) == 1 else None,
                     "cases": {}, "count": None}
            blocks.append(block)
            case = None
            continue
        if block is None:
            continue
        m = CASE_RE.match(line)
        if m:
            case = {"result": m.group("result"), "asserts": {},
                    "samples": m.group("samples").split() if m.group("samples") else None}
            block["cases"][m.group("case")] = case
            continue
        m = ASSERT_RE.match(line)
        if m and case is not None:
            case["asserts"][m.group("kind")] = m.group("detail")
            continue
        m = COUNT_RE.match(line)
        if m:
            block["count"] = {k: int(v) for k, v in m.groupdict().items()}
    return blocks


def budget_axes(detail: str | None) -> dict[str, dict]:
    """`tokens_in=8302 over 7700; tokens_out=411 over 400` -> per axis."""
    if not detail:
        return {}
    return {m.group("axis"): {"value": int(m.group("value")), "over": int(m.group("ceiling"))}
            for m in BUDGET_RE.finditer(detail)}


def live_ceiling() -> int:
    """The one `tokens_in` value every case carries. Read as text — one regex
    over the file — so this reader adds no dependency the census does not have."""
    values = {int(v) for v in re.findall(r"budget:\s*\{[^}]*\btokens_in:\s*(\d+)", _read(CASES))}
    if len(values) != 1:
        raise SystemExit(f"cases.yaml carries {len(values)} distinct tokens_in ceilings: {sorted(values)}")
    return values.pop()


def per_sample_rows(census: dict, new_blocks: list[dict], old_blocks: list[dict], ceiling: int) -> list[dict]:
    """One row per stage-2 sample, in the census's order: the call count and
    tokens from the record, the verdicts from the transcript at the live
    ceiling, and what the same sample failed on at 6000."""
    by_sample_new = {b["sample"]: b for b in new_blocks if b["sample"] is not None}
    by_sample_old = {b["sample"]: b for b in old_blocks if b["sample"] is not None}
    if sorted(by_sample_new) != [1, 2, 3] or sorted(by_sample_old) != [1, 2, 3]:
        raise SystemExit("each per-sample transcript must hold exactly the three single-file runs")
    rows = []
    for r in census["2_stage2_per_sample (exact + replayed)"]:
        scored = by_sample_new[r["sample"]]["cases"][r["case"]]
        before = by_sample_old[r["sample"]]["cases"][r["case"]]
        axes = budget_axes(scored["asserts"].get("budget"))
        axes_before = budget_axes(before["asserts"].get("budget"))
        row = {
            "case": r["case"], "sample": r["sample"], "answered": r["answered"],
            "calls": r["calls"], "mandated_calls": r["mandated_calls"],
            "tokens_in": r["tokens_in"], "tokens_out": r["tokens_out"],
            "sample_result": scored["result"],
            "tokens_in_verdict": None, "tokens_out_verdict": None,
            "other_failing_asserts": sorted(k for k in scored["asserts"] if k != "budget"),
            "failed_on_at_6000": sorted(
                [k for k in before["asserts"] if k != "budget"]
                + [f"budget.{axis}" for axis in axes_before]),
        }
        if r["answered"]:
            row["tokens_in_verdict"] = "FAIL" if "tokens_in" in axes else "PASS"
            row["tokens_out_verdict"] = "FAIL" if "tokens_out" in axes else "PASS"
            # The transcript and the record describe one sample: a `tokens_in`
            # line that names a different ceiling or a different token count is
            # a transcript scored against something other than this record.
            # (`tokens_out` is tiered per case and is not checked here.)
            if "tokens_in" in axes:
                if axes["tokens_in"]["over"] != ceiling:
                    raise SystemExit(f"{r['case']} s{r['sample']}: budget line says tokens_in over "
                                     f"{axes['tokens_in']['over']}, cases.yaml says {ceiling}")
                if axes["tokens_in"]["value"] != r["tokens_in"]:
                    raise SystemExit(f"{r['case']} s{r['sample']}: transcript tokens_in "
                                     f"{axes['tokens_in']['value']} != census {r['tokens_in']}")
        elif "budget" in scored["asserts"]:
            raise SystemExit(f"{r['case']} s{r['sample']}: refused in the census, budget-scored in the transcript")
        rows.append(row)
    return rows


def claim(rows: list[dict], ceiling: int) -> dict:
    """The claim's two halves, from the rows and nothing else."""
    answered = [r for r in rows if r["answered"]]
    low = [r for r in answered if r["calls"] <= 3]
    high = [r for r in answered if r["calls"] >= 4]
    low_over = [f"{r['case']} s{r['sample']}" for r in low if r["tokens_in_verdict"] != "PASS"]
    high_under = [f"{r['case']} s{r['sample']}" for r in high if r["tokens_in_verdict"] != "FAIL"]
    return {
        "ceiling": ceiling,
        "answered_samples": len(answered),
        "samples_at_3_calls_or_fewer": len(low),
        "samples_at_4_calls_or_more": len(high),
        "every_3_call_or_fewer_sample_passes_tokens_in": not low_over,
        "every_4_call_or_more_sample_fails_tokens_in": not high_under,
        "3_call_or_fewer_samples_over": low_over,
        "4_call_or_more_samples_under": high_under,
        "largest_3_call_or_fewer_tokens_in": max(r["tokens_in"] for r in low),
        "smallest_4_call_or_more_tokens_in": min(r["tokens_in"] for r in high),
        "cases_with_a_4_call_or_more_sample": sorted({r["case"] for r in high}),
        "holds": not low_over and not high_under,
    }


def per_case(k3: dict, m07: dict, rows: list[dict]) -> list[dict]:
    """M07's recorded result beside the re-score's, per case, with the sample
    brackets from both and the call count of each sample."""
    old = {c["id"]: c for c in m07["cases"]}
    calls = {(r["case"], r["sample"]): r["calls"] for r in rows}
    out = []
    for case_id, scored in k3["cases"].items():
        out.append({
            "case": case_id,
            "m07_result": old[case_id]["result"],
            "m07_samples": old[case_id].get("samples"),
            "rescore_result": scored["result"],
            "rescore_samples": scored["samples"],
            "calls_by_sample": [calls[(case_id, s)] for s in (1, 2, 3)],
            "flipped": old[case_id]["result"] == "FAIL" and scored["result"] == "PASS",
            "regressed": old[case_id]["result"] == "PASS" and scored["result"] == "FAIL",
            "representative_failures": sorted(scored["asserts"]),
        })
    return out


def side_prediction(cases: list[dict], rows: list[dict], count: dict) -> dict:
    """SPEC/08's falsifiers of the side-prediction, each a boolean read from the
    rows, with the evidence beside it. A True here is a finding about the
    side-prediction and not a failure of the claim (SPEC/08 amendment 1)."""
    flipped = [c["case"] for c in cases if c["flipped"]]
    regressed = [c["case"] for c in cases if c["regressed"]]
    by_key = {(r["case"], r["sample"]): r for r in rows}

    def majority_calls_ge4(case_id: str) -> bool:
        return sum(1 for s in (1, 2, 3) if (by_key[(case_id, s)]["calls"] or 0) >= 4) >= 2

    def flipped_on_more_than_tokens_in(case_id: str) -> list[str]:
        # The samples that pass now are the majority that flipped it; at 6000
        # each must have failed on `budget.tokens_in` and nothing else.
        offenders = []
        for s in (1, 2, 3):
            r = by_key[(case_id, s)]
            if r["sample_result"] == "PASS" and r["failed_on_at_6000"] not in ([], ["budget.tokens_in"]):
                offenders.append(f"s{s}: {r['failed_on_at_6000']}")
        return offenders

    n = count["passed"]
    return {
        "N": n,
        "total": count["total"],
        "predicted_N": PREDICTED_N,
        "bound": list(BOUND),
        "N_in_bound": BOUND[0] <= n <= BOUND[1],
        "N_is_predicted": n == PREDICTED_N,
        "flipped": flipped,
        "regressed": regressed,
        "predicted_flips": list(PREDICTED_FLIPS),
        "predicted_held": list(PREDICTED_HELD),
        "passing_at_m07": list(PASSING_AT_M07),
        "flipped_set_is_exactly_the_ten": sorted(flipped) == sorted(PREDICTED_FLIPS),
        "falsifiers": {
            "a_case_flipped_on_a_4_call_majority": [c for c in flipped if majority_calls_ge4(c)],
            "a_flipped_case_failed_another_assert_at_m07": {
                c: offenders for c in flipped if (offenders := flipped_on_more_than_tokens_in(c))},
            "one_of_the_five_flipped": [c for c in PREDICTED_HELD if c in flipped],
            "one_of_the_ten_did_not_flip": [c for c in PREDICTED_FLIPS if c not in flipped],
        },
        "held": (n == PREDICTED_N and sorted(flipped) == sorted(PREDICTED_FLIPS)
                 and not regressed),
    }


def join() -> dict:
    ceiling = live_ceiling()
    census = json.loads(_read(CENSUS))
    new_blocks = parse_transcript(_read(PER_SAMPLE_NEW))
    old_blocks = parse_transcript(_read(PER_SAMPLE_OLD))
    k3_blocks = [b for b in parse_transcript(_read(K3)) if b["count"] is not None]
    if len(k3_blocks) != 1:
        raise SystemExit(f"goldens-rescore.txt holds {len(k3_blocks)} scored blocks, expected one")
    k3 = k3_blocks[0]
    m07 = json.loads(_read(M07_ROW))
    rows = per_sample_rows(census, new_blocks, old_blocks, ceiling)
    cases = per_case(k3, m07, rows)
    return {
        "_what_this_is": (
            "M08 PR 4: M07's three committed stage-2 answer files re-scored once at the "
            "ceiling PR 3 signed, joined per sample to the census's call counts. The claim "
            "is read from `claim`; the side-prediction from `side_prediction`; both are "
            "computed from `per_sample` and `per_case`, never written. Zero model calls."
        ),
        "ceiling": ceiling,
        "census_ceiling": census["ceiling"],
        "inputs_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): _sha256(p) for p in INPUTS},
        "count": k3["count"],
        "claim": claim(rows, ceiling),
        "side_prediction": side_prediction(cases, rows, k3["count"]),
        "per_case": cases,
        "per_sample": rows,
    }


def render(record: dict) -> str:
    """The join as a table, one row per sample, and the two verdict blocks."""
    c, s = record["claim"], record["side_prediction"]
    lines = [
        f"M08 PR 4 — the re-score joined to the census at tokens_in {record['ceiling']}",
        "",
        "| case | s | calls | mandate | tokens_in | tokens_in @ceiling | tokens_out | other failing asserts | sample | failed on at 6000 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in record["per_sample"]:
        if not r["answered"]:
            lines.append(f"| {r['case']} | {r['sample']} | – | {r['mandated_calls']} | – | refused | – | "
                         f"{', '.join(r['other_failing_asserts']) or '–'} | {r['sample_result']} | "
                         f"{', '.join(r['failed_on_at_6000']) or '–'} |")
            continue
        lines.append(f"| {r['case']} | {r['sample']} | {r['calls']} | {r['mandated_calls']} | {r['tokens_in']} | "
                     f"{r['tokens_in_verdict']} | {r['tokens_out_verdict']} | "
                     f"{', '.join(r['other_failing_asserts']) or '–'} | {r['sample_result']} | "
                     f"{', '.join(r['failed_on_at_6000']) or '–'} |")
    lines += [
        "",
        f"claim: every ≤3-call sample passes tokens_in: {c['every_3_call_or_fewer_sample_passes_tokens_in']} "
        f"({c['samples_at_3_calls_or_fewer']} samples, max {c['largest_3_call_or_fewer_tokens_in']}); "
        f"every ≥4-call sample fails it: {c['every_4_call_or_more_sample_fails_tokens_in']} "
        f"({c['samples_at_4_calls_or_more']} samples on {len(c['cases_with_a_4_call_or_more_sample'])} cases, "
        f"min {c['smallest_4_call_or_more_tokens_in']}) -> holds: {c['holds']}",
        f"side-prediction: N = {s['N']}/{s['total']}, predicted {s['predicted_N']}, bound {s['bound']}, "
        f"in bound: {s['N_in_bound']}; flipped {len(s['flipped'])}: {', '.join(s['flipped'])}; "
        f"exactly the ten: {s['flipped_set_is_exactly_the_ten']}; regressed: {s['regressed'] or 'none'}",
        "falsifiers: " + "; ".join(f"{k}: {v or 'none'}" for k, v in s["falsifiers"].items()),
        f"-> side-prediction held: {s['held']}",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--check", action="store_true",
                        help="recompute and compare with the committed record; write nothing; exit 1 on drift")
    args = parser.parse_args(argv)
    record = join()
    text = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    out = pathlib.Path(args.out)
    if args.check:
        committed = out.read_text(encoding="utf-8") if out.exists() else ""
        if committed != text:
            print(f"DRIFT: {out} differs from what the committed inputs produce")
            return 1
        print(f"OK: {out} is what the committed inputs produce")
        return 0
    out.write_text(text, encoding="utf-8", newline="\n")
    print(render(record))
    print(f"\nwritten: {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
