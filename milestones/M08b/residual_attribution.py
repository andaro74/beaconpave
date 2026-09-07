"""
`python milestones/M08b/residual_attribution.py` — the residual, attributed by
two exact numbers (ADR-074 decision 3 §4).

**What this attributes.** ADR-073 amendment 2 §2 bounded the tools arm's
per-call input base at 1859–1974 tokens with ≈1437 explained by committed text
and **422–537 unattributed** — the same size with one tool offered as with two
— and named the measurement that separates provider-side framing from content
the agent sends: per-call `inputTokens` and one calibration call. Both exist
after PR 3, and the reading was written before either did:

- **A** — the fresh run's round-1 `tokens_in` on the calibration case
  (`blackout-008`, the census's mandated-shape maximum), read from each answer
  file's `usage.calls[0]`. The three samples must agree, because the round-1
  request is deterministic; a disagreement is itself a finding and the reading
  stops.
- **B** — one gateway turn on the same viewer turn with `tools` absent and the
  same `system` (`run_with_tools.py --calibrate`, `calibration.json`). Its
  round-1 `tokens_in` is the committed text as the model counts it.
- **E** — the census's estimate of that text: `system_prompt.tokens_est` plus
  the viewer turn at the census's chars-per-token, read by key from
  `milestones/M08/context-census.json` and the case's own turn, never
  re-estimated.
- **S** — the census's `tool_specs_total.tokens_est`.

Then **D = B − E** is tokeniser density (the estimate undercounting the
committed text), **F = A − B − S** is provider-side framing (what `toolConfig`
costs beyond the specs' own text), and **A − E − S = D + F** by identity. The
reading names whichever of |D| and |F| is 70% or more of |D| + |F|, or both
with their shares, **each with its sign** — D is negative when the estimate
over-counts, and a share of a signed sum is undefined (ADR-074 amendment 1
§2, row 5). Neither is content the agent can stop sending. ADR-014 amendment
2's downward re-derivation trigger arms only if the round-1 pin fails, and
that pin is a test, not a number here.

**Rounds two and three are recorded, not ruled on.** From the join's per-round
columns: each round's growth in `tokens_in` against the replayed transcript's
growth in characters at the density B measures. A growth more than a quarter
unexplained is a dated finding for Platform Engineering, never a trigger.

**The fallback, pre-registered (SPEC/08b).** If the calibration turn was
refused on the `answer` channel the runner writes `tokens_in: 0` in `usage`,
and B is read from the audit record's per-call usage; if the calibration was
re-issued on `entitlement-010`, A is read from the same case and the
substitution is recorded. Zero model calls; no network module; no ceiling.

Owning seats, by the two-key rule that covers it: AI Quality · Platform
Engineering · Security.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "milestones" / "M08b"
OUT_NAME = "residual-attribution.json"
CENSUS = ROOT / "milestones" / "M08" / "context-census.json"
CENSUS_READER = ROOT / "milestones" / "M08" / "context_census.py"
CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"

COMPONENTS = "4_by_component (estimated)"
DEFAULT_CASE = "blackout-008"
FALLBACK_CASE = "entitlement-010"
SHARE_NAMES = 0.70
UNEXPLAINED_QUARTER = 0.25


def _census_module():
    spec = importlib.util.spec_from_file_location("context_census", CENSUS_READER)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("context_census", module)
    spec.loader.exec_module(module)
    return module


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _round1(usage: dict | None) -> int | None:
    calls = (usage or {}).get("calls")
    if isinstance(calls, list) and calls and isinstance(calls[0], dict):
        return calls[0].get("tokens_in")
    return None


def read_b(calibration: dict) -> tuple[int | None, str]:
    """B and where it was read from. The response's usage first; the record's
    copy when the turn was refused and the runner wrote zeros."""
    if calibration.get("tools") != "absent":
        raise SystemExit("calibration.json does not say tools were absent; a calibration "
                         "turn that offered tools measured A twice and called it B")
    b = _round1(calibration.get("usage"))
    from_record = _round1(calibration.get("record_usage"))
    # The producer writes that the response's usage and the record's must
    # agree; this is where that sentence is a check rather than a comment
    # (Platform Engineering seat, round 1). The record is the independent
    # witness that the turn happened as described, so a disagreement is not a
    # number to pick between — it is a B nobody can read.
    if b and from_record and b != from_record:
        raise SystemExit(f"calibration.json's response usage says round 1 cost {b} and its audit "
                         f"record says {from_record}; the two must agree before B is readable")
    if b:
        return b, "usage.calls[0].tokens_in"
    b = _round1(calibration.get("record_usage"))
    if b:
        return b, "record_usage.calls[0].tokens_in (the response's usage carried no round; the fallback)"
    raise SystemExit("calibration.json carries no round-1 tokens_in in either the response's usage "
                     "or the record's; B is unreadable and the call must be re-issued")


def estimate(census: dict, cases: dict, case_id: str) -> dict:
    """E and S by key from the census record, the viewer turn by the census
    reader's own estimator over the case's own text."""
    reader = _census_module()
    components = census[COMPONENTS]
    system = components["per_call_text"]["system_prompt"]
    specs = components["per_call_text"]["tool_specs_total"]
    constants = reader.client_constants()
    viewer_text = reader.user_turn(constants, cases[case_id])
    viewer = reader._est(len(viewer_text), components["calibration"])
    return {
        "system_prompt_tokens_est": system["tokens_est"],
        "system_prompt_band": system["tokens_est_band"],
        "viewer_turn_chars": viewer["chars"],
        "viewer_turn_tokens_est": viewer["tokens_est"],
        "viewer_turn_band": viewer["tokens_est_band"],
        "E": system["tokens_est"] + viewer["tokens_est"],
        "E_band": [system["tokens_est_band"][0] + viewer["tokens_est_band"][0],
                   system["tokens_est_band"][1] + viewer["tokens_est_band"][1]],
        "S": specs["tokens_est"],
        "S_band": specs["tokens_est_band"],
        "committed_text_chars": len(reader.tool_prompt(constants)) + viewer["chars"],
    }


def attribute(a_values: list[int | None], b: int, est: dict) -> dict:
    seen = [v for v in a_values if v is not None]
    if len(seen) != len(a_values) or not seen:
        return {"A": None, "A_values": a_values, "reading": "unreadable: a sample carries no round-1 tokens_in",
                "finding": "round-1 usage absent on a sample"}
    if len(set(seen)) != 1:
        return {"A": None, "A_values": a_values,
                "reading": "unreadable: the round-1 tokens_in disagree across samples",
                "finding": "the round-1 request is deterministic and the samples disagree; a finding "
                           "for Platform Engineering before any attribution is read"}
    a = seen[0]
    e, s = est["E"], est["S"]
    d, f = b - e, a - b - s
    residual = a - e - s
    assert d + f == residual, "the identity A - E - S = D + F failed; the arithmetic is wrong"
    magnitude = abs(d) + abs(f)
    shares = {"D": (abs(d) / magnitude) if magnitude else None,
              "F": (abs(f) / magnitude) if magnitude else None}
    if magnitude == 0:
        reading = "no residual: A = E + S exactly"
    elif shares["D"] >= SHARE_NAMES:
        reading = "tokeniser density: the estimate mis-counts the committed text"
    elif shares["F"] >= SHARE_NAMES:
        reading = "provider-side framing: what toolConfig costs beyond the specs' own text"
    else:
        reading = "both, with their shares"
    return {
        "A": a, "A_values": a_values, "B": b,
        "D": d, "D_sign": "negative (the estimate over-counts)" if d < 0 else "non-negative",
        "F": f, "F_sign": "negative" if f < 0 else "non-negative",
        "residual_A_minus_E_minus_S": residual,
        "identity_holds": True,
        "shares_of_abs": {k: (round(v, 3) if v is not None else None) for k, v in shares.items()},
        "reading": reading,
        "removable_by_the_agent": "neither D nor F is content the agent can stop sending",
        "downward_trigger": {
            "armed": False,
            "arms_only_if": "the round-1 pin fails: tests/test_tool_loop.py "
                            "(the first transcript is the caller's messages verbatim) and "
                            "tests/test_handler_wiring.py (the model call is modelId, the "
                            "transcript, inferenceConfig, system and toolConfig, nothing else)",
        },
    }


def growth(join: dict | None, b: int, est: dict) -> dict:
    """Rounds two and three against the replayed transcript at the measured
    density. Recorded, not ruled on; a growth more than a quarter unexplained
    is listed as a dated finding."""
    if not join:
        return {"available": False, "note": "fresh-join.json not present; per-round growth not read"}
    density = est["committed_text_chars"] / b if b else None
    rows, unexplained = [], []
    for sample in join.get("per_sample") or []:
        for step in sample.get("per_round_growth") or []:
            if step.get("delta_tokens") is None:
                continue
            explained = (step.get("replayed_chars_added") or 0) / density if density else None
            share = (1 - explained / step["delta_tokens"]) if explained is not None and step["delta_tokens"] else None
            row = {"case": sample["case"], "sample": sample["sample"], "round": step["round"],
                   "delta_tokens": step["delta_tokens"],
                   "replayed_chars_added": step.get("replayed_chars_added"),
                   "explained_tokens_at_density": round(explained) if explained is not None else None,
                   "unexplained_share": round(share, 3) if share is not None else None}
            rows.append(row)
            if share is not None and share > UNEXPLAINED_QUARTER:
                unexplained.append(row)
    return {"available": True, "chars_per_token_measured": round(density, 3) if density else None,
            "rows": rows,
            "more_than_a_quarter_unexplained": unexplained,
            "finding": ("dated finding for Platform Engineering, not a trigger" if unexplained
                        else "none")}


def record(run_dir: pathlib.Path) -> dict:
    run_dir = pathlib.Path(run_dir).resolve()
    calibration_path = run_dir / "calibration.json"
    if not calibration_path.is_file():
        raise SystemExit(f"{calibration_path} does not exist; the calibration call has not been made")
    calibration = _load(calibration_path)
    case_id = calibration.get("case") or DEFAULT_CASE
    if case_id not in (DEFAULT_CASE, FALLBACK_CASE):
        raise SystemExit(f"calibration.json is on {case_id!r}; the reading is pre-registered on "
                         f"{DEFAULT_CASE} with {FALLBACK_CASE} as the one fallback")
    b, b_source = read_b(calibration)
    import yaml  # noqa: PLC0415 — the census reader's own dependency
    cases = {c["id"]: c for c in yaml.safe_load(CASES.read_text(encoding="utf-8"))}
    est = estimate(_load(CENSUS), cases, case_id)
    answer_files = [run_dir / f"goldens-run-{n}.json" for n in (1, 2, 3)]
    a_values = [_round1((_load(p).get(case_id) or {}).get("usage")) if p.is_file() else None
                for p in answer_files]
    join_path = run_dir / "fresh-join.json"
    join = _load(join_path) if join_path.is_file() else None
    inputs = [calibration_path, CENSUS, CASES, *[p for p in answer_files if p.is_file()]]
    if join is not None:
        inputs.append(join_path)
    return {
        "_what_this_is": (
            "ADR-074 decision 3 §4: the residual attributed by two exact numbers, produced by "
            "milestones/M08b/residual_attribution.py. A is the fresh run's round-1 tokens_in on "
            "the calibration case, B the calibration call's, E and S the census's estimates by "
            "key; D = B - E, F = A - B - S, A - E - S = D + F. Rounds two and three are recorded "
            "against the replayed transcript at the measured density, not ruled on."),
        "inputs_sha256": {str(p.relative_to(ROOT)).replace("\\", "/") if p.is_relative_to(ROOT)
                          else p.name: _sha256(p) for p in inputs},
        "case": case_id,
        "fallback_taken": case_id != DEFAULT_CASE,
        "B_read_from": b_source,
        "calibration_decision": calibration.get("decision"),
        "estimates": est,
        "attribution": attribute(a_values, b, est),
        "per_round_growth": growth(join, b, est),
    }


def render(rec: dict) -> str:
    att, est = rec["attribution"], rec["estimates"]
    lines = [f"case {rec['case']}{' (fallback)' if rec['fallback_taken'] else ''}; B from {rec['B_read_from']}",
             f"A = {att.get('A')} ({att.get('A_values')})   B = {att.get('B')}   "
             f"E = {est['E']} {est['E_band']}   S = {est['S']} {est['S_band']}"]
    if att.get("A") is not None:
        lines.append(f"D = B - E = {att['D']} ({att['D_sign']});  F = A - B - S = {att['F']} ({att['F_sign']});  "
                     f"A - E - S = {att['residual_A_minus_E_minus_S']}; shares of |D|+|F|: {att['shares_of_abs']}")
    lines.append(f"reading: {att['reading']}")
    g = rec["per_round_growth"]
    if g.get("available"):
        lines.append(f"per-round growth: {len(g['rows'])} row(s) at {g['chars_per_token_measured']} chars/token; "
                     f"{len(g['more_than_a_quarter_unexplained'])} more than a quarter unexplained ({g['finding']})")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--dir", default=str(HERE), help="the run directory (default: milestones/M08b)")
    parser.add_argument("--check", action="store_true",
                        help="recompute and compare with the committed record; write nothing; exit 1 on drift")
    args = parser.parse_args(argv)
    run_dir = pathlib.Path(args.dir)
    rec = record(run_dir)
    text = json.dumps(rec, indent=2, ensure_ascii=False) + "\n"
    out = run_dir / OUT_NAME
    if args.check:
        committed = out.read_text(encoding="utf-8") if out.exists() else ""
        if committed != text:
            print(f"DRIFT: {out} differs from what the committed inputs produce")
            return 1
        print(f"OK: {out} is what the committed inputs produce")
        return 0
    out.write_text(text, encoding="utf-8", newline="\n")
    print(render(rec))
    print(f"\nwritten: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
