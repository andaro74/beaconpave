"""
`python milestones/M08/residual_differential.py` — does the unattributed residual
grow with the added tool spec? The M02-to-stage-2 differential, zero calls.

**What this is.** The census (`context_census.py`) bounded the tools arm's
per-call input at M07 stage 2 from its seven 2-call samples — 1859–1974 tokens
per call — and explained ≈1437 of it from committed text; the remaining 422–537
is *"not in any committed text the client or gateway sends"*, recorded and not
attributed. ADR-073 amendment 1 (question 3) named three explanations the census
cannot separate — estimation error, provider-side tool-use framing, content the
agent sends that no committed text shows — and one zero-call measurement that
narrows them: M02's tools arm offered ONE tool and stage 2 offered TWO, on the
same client, the same answer schema and the same `catalog-search` contract, so
the per-call difference between the two runs is one added tool spec
(`entitlement-check`, ≈282 tokens as sent) and nothing else the repository
controls. A residual that grows with the spec points at the explanations that
scale with text; one that does not points at a fixed cost.

**What it reads.** The same committed runs the census reads (`milestones/M02/
runs/`, `milestones/M07/`), through the census's own reader, so the rows here
are the census's rows; and the same committed text, rebuilt the way the client
and gateway send it. Every input's sha256 is in the record.

**What it does not do.** It calls nothing, takes no ceiling, prints no pass
count at any ceiling, and moves no number in the census. It narrows the
question; it does not pay the debt. The measurement that settles the residual
is per-call `inputTokens` in the answer file plus one calibration call with
tools offered — a `run_with_tools.py` change and a model call, both M09 PR 1's
(SPEC/08 amendment 1).

**The M02-era text.** The subtraction below uses HEAD's committed text for
M02's explained half. That is valid because at M02's run commit (`4eda0d0`,
2026-08-19, the commit that committed `milestones/M02/runs/`) `gateway_client.py`
and `answer.schema.json` were the same blobs HEAD has, and the `catalog-search`
contract as sent digests the same. Those digests are constants here, verified
against `git show` when the record was produced (`--verify-history`, which
needs the local history and nothing else) and pinned on HEAD's side by
`tests/test_m08_residual_differential.py`, so a client or contract change turns
the record red rather than quietly invalidating the subtraction.

Owning seats: Platform Engineering (the loop's shape; the residual debt) · AI
Quality (the ceiling the residual may move).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "residual-differential.json"

M02_RUN = "m02-tools"
SUBJECT = "m07-stage2"
ADDED_SPEC = "entitlement-check"

#: The commit that committed `milestones/M02/runs/` (`git log -- milestones/M02/runs/`),
#: and what the three files the subtraction depends on were at it. Blob ids are
#: `git rev-parse <commit>:<path>`; the rebuilt-text digests are sha256 over the
#: text exactly as `context_census.tool_prompt` and `tool_config` rebuild it.
M02_ERA = {
    "commit": "4eda0d036884a2d536d757b60b78ff10ac7d91e8",
    "committed": "2026-08-19",
    "what": "the commit that committed milestones/M02/runs/",
    "blobs": {
        "services/highlights-agent/gateway_client.py": "8351db7a64ef27600b4002541b99d648bb91d275",
        "services/highlights-agent/evals/answer.schema.json": "3c81d9e89e75ab00bcf3617f7b2d76c43c8eed4d",
        # differs from HEAD's blob: two descriptions changed since (entitlement-check's,
        # publish-highlight's); the catalog-search contract, the one M02 sent, did not
        "platform/gateway/policy/tools.contracts.json": "eb49fe418bc7373cdadb3fe68085e974088626f1",
    },
    "rebuilt_text_sha256_at_m02": {
        "tool_system_prompt": "9ebd6e0725e914e492592c0f178dc09d97449c59d2072d618897dae43da238a4",
        "catalog_search_toolspec": "c8c3bddb71174ae73e4de6d15fd1db7ed536ab75175770e6a3329b292db53986",
    },
    "clock_at_m02": "2026-09-13T18:00:00Z",
}


def _census():
    if "context_census" in sys.modules:
        return sys.modules["context_census"]
    spec = importlib.util.spec_from_file_location("context_census", HERE / "context_census.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["context_census"] = module
    spec.loader.exec_module(module)
    return module


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _toolspec_text(cc, tool_id: str) -> str:
    config = cc.tool_config([tool_id])
    return json.dumps(config["tools"][0]["toolSpec"], ensure_ascii=False)


def head_text_digests() -> dict:
    """HEAD's side of the identity the subtraction rests on."""
    cc = _census()
    constants = cc.client_constants()
    return {
        "tool_system_prompt": _sha256_text(cc.tool_prompt(constants)),
        "catalog_search_toolspec": _sha256_text(_toolspec_text(cc, "catalog-search")),
    }


def _run(cc, key: str) -> dict:
    return next(r for r in cc.RUNS if r["key"] == key)


def differential() -> dict:
    cc = _census()
    inputs: dict = {}
    for path in (cc.CATALOG, cc.CASES, cc.CLIENT, cc.ANSWER_SCHEMA, cc.CONTRACTS):
        inputs[str(path.relative_to(ROOT)).replace("\\", "/")] = cc._sha256(path)
    constants = cc.client_constants()
    cases = {c["id"]: c for c in cc.yaml.safe_load(cc.CASES.read_text(encoding="utf-8"))}
    catalog = cc.search.load_catalog(cc.CATALOG)
    cal = cc.calibration(constants, cases)

    runs = {key: _run(cc, key) for key in (M02_RUN, SUBJECT)}
    rows = {key: cc.read_run(run, cases, catalog, constants["CLOCK"], inputs) for key, run in runs.items()}
    tables = {key: cc.by_calls(rows[key]) for key in runs}
    comp = {key: cc.components(run, constants, cases, cal) for key, run in runs.items()}
    base = {key: cc.per_call_base(rows[key], cal, comp[key]) for key in runs}

    head = head_text_digests()
    identical = head == M02_ERA["rebuilt_text_sha256_at_m02"] and constants["CLOCK"] == M02_ERA["clock_at_m02"]

    added = comp[SUBJECT]["tool_specs"][ADDED_SPEC]
    common = sorted(set(tables[M02_RUN]) & set(tables[SUBJECT]), key=int)
    by_calls = {}
    for calls in common:
        a, b = tables[M02_RUN][calls], tables[SUBJECT][calls]
        by_calls[calls] = {
            "m02_one_tool": {"n": a["n"], "per_call_median": a["per_call_median"]},
            "m07_stage2_two_tools": {"n": b["n"], "per_call_median": b["per_call_median"]},
            "delta_per_call": b["per_call_median"] - a["per_call_median"],
            "delta_minus_added_spec_est": b["per_call_median"] - a["per_call_median"] - added["tokens_est"],
        }

    def modal(table):
        return max(table, key=lambda c: table[c]["n"])

    m02_mode, s2_mode = modal(tables[M02_RUN]), modal(tables[SUBJECT])
    modal_pair = {
        "m02_one_tool": {"modal_calls": int(m02_mode),
                         "per_call_median": tables[M02_RUN][m02_mode]["per_call_median"]},
        "m07_stage2_two_tools": {"modal_calls": int(s2_mode),
                                 "per_call_median": tables[SUBJECT][s2_mode]["per_call_median"]},
    }
    modal_pair["delta_per_call"] = (modal_pair["m07_stage2_two_tools"]["per_call_median"]
                                    - modal_pair["m02_one_tool"]["per_call_median"])
    modal_pair["of_which_like_for_like_at_two_calls"] = by_calls["2"]["delta_per_call"] if "2" in by_calls else None
    modal_pair["of_which_stage2s_third_call"] = (tables[SUBJECT][s2_mode]["per_call_median"]
                                                 - tables[SUBJECT]["2"]["per_call_median"]) if "2" in tables[SUBJECT] else None
    modal_pair["note"] = ("the figures SPEC/08 names, 1693 against 2057, compare M02's 2-call mode with "
                          "stage 2's 3-call mode; the third call carries the first tool round's "
                          "output and result, which is call count, not the added spec. The "
                          "like-for-like rows above hold call count fixed.")

    residual = {}
    for key in runs:
        b = base[key]
        residual[key] = {
            "offered": list(runs[key]["offered"]),
            "two_call_samples": b["n"],
            "per_call_base": {"lower": b["lower_median"], "upper": b["upper_median"]},
            "explained_by_committed_text_est": b["explained_by_committed_text_est"],
            "residual_est": {"lower": b["residual_est"]["lower"], "upper": b["residual_est"]["upper"]},
        }
    residual_delta = {
        "lower": residual[SUBJECT]["residual_est"]["lower"] - residual[M02_RUN]["residual_est"]["lower"],
        "upper": residual[SUBJECT]["residual_est"]["upper"] - residual[M02_RUN]["residual_est"]["upper"],
        "added_spec_tokens_est": added["tokens_est"],
        "added_spec_tokens_est_band": added["tokens_est_band"],
    }

    grew = residual_delta["upper"] > added["tokens_est_band"][1] - added["tokens_est_band"][0]
    reading = {
        "question": "does the residual grow with the added tool spec?",
        "answer": ("no" if not grew else "yes"),
        "sentence": (
            f"At two calls the per-call input went from {by_calls['2']['m02_one_tool']['per_call_median']} "
            f"(one tool) to {by_calls['2']['m07_stage2_two_tools']['per_call_median']} (two tools), a difference "
            f"of {by_calls['2']['delta_per_call']} against an added spec estimated at {added['tokens_est']} "
            f"[{added['tokens_est_band'][0]}, {added['tokens_est_band'][1]}]; the residual's upper bound is "
            f"{residual[M02_RUN]['residual_est']['upper']} at M02 and {residual[SUBJECT]['residual_est']['upper']} "
            f"at stage 2. The residual did not grow with the spec: it is a fixed cost that appears with "
            f"toolConfig and does not scale with the number of tools offered."
            if not grew else
            f"The residual grew by {residual_delta['upper']} across an added spec of {added['tokens_est']}."),
        "rules_out": [
            "per_tool_provider_framing",
            "estimation_error_on_tool_spec_json",
        ],
        "rules_out_because": (
            "a cost that scaled with the number of tools, or a tokeniser that counted the spec's JSON "
            "denser than the 3.37 chars/token the prose anchors gave, would each have moved the "
            "per-call figure by more than the spec's estimate; it moved by the estimate"),
        "cannot_separate": [
            "provider_side_tool_use_framing",
            "content_the_agent_sends_no_committed_text_shows",
        ],
        "cannot_separate_because": (
            "both are fixed across the two runs: whatever the provider prepends when toolConfig is "
            "present was present in both, and nothing in the client changed between them, so a "
            "fixed agent-side cost is indistinguishable from a fixed provider-side one here"),
        "not_varied": ["answer_schema_json_tokenisation"],
        "not_varied_because": (
            "the answer schema is the same bytes in both runs; that tool-spec JSON tokenised at the "
            "prose ratio weakens the estimation-error explanation for the schema's JSON too, but does "
            "not test it"),
        "paid_by": {
            "owed_to": ["platform-eng", "ai-quality"],
            "date": "M09 PR 1",
            "by": ["per-call inputTokens in the answer file (a run_with_tools.py / _accumulate change; "
                   "SPEC/08 constraint 5 forbids it in M08)",
                   "one calibration call with tools offered and an empty turn (a model call; SPEC/08 "
                   "constraint 6 forbids it in M08)"],
            "what_each_settles": (
                "per-call usage separates the first call's base from what later calls carry; the "
                "calibration call, against the same text with toolConfig present and absent, is the "
                "residual measured directly"),
        },
    }

    return {
        "_what_this_is": (
            "M08's residual differential: the tools arm's per-call input at M02 (one tool offered) against "
            "M07 stage 2 (two tools), across one added tool spec of known size, read off the same committed "
            "runs the census reads through the census's own reader. Zero model calls. Produced by "
            "milestones/M08/residual_differential.py; tests/test_m08_residual_differential.py re-runs it "
            "and refuses drift. Narrows ADR-073 amendment 1's three explanations; pays nothing. Takes no "
            "ceiling and prints no pass count."),
        "inputs_sha256": dict(sorted(inputs.items())),
        "m02_era_text": dict(M02_ERA, rebuilt_text_sha256_at_head=head, identical_to_head=identical),
        "added_spec": {"tool": ADDED_SPEC, "chars": added["chars"], "tokens_est": added["tokens_est"],
                       "tokens_est_band": added["tokens_est_band"],
                       "as_sent": "the toolSpec the gateway builds from the committed input contract"},
        "per_call_by_call_count (exact medians)": by_calls,
        "modal_pair (exact medians)": modal_pair,
        "per_call_base_and_residual (bounded from two-call samples; explained half estimated)": residual,
        "residual_delta": residual_delta,
        "reading": reading,
    }


def render(record: dict) -> str:
    lines = ["M08 residual differential — one tool (M02) against two (M07 stage 2), zero calls", ""]
    added = record["added_spec"]
    lines.append(f"added spec: {added['tool']}  {added['chars']} chars  ~{added['tokens_est']} tokens "
                 f"[{added['tokens_est_band'][0]}, {added['tokens_est_band'][1]}]")
    lines.append("")
    lines.append("per call, by call count (medians):")
    for calls, row in record["per_call_by_call_count (exact medians)"].items():
        lines.append(f"  {calls} calls  M02 {row['m02_one_tool']['per_call_median']:5} (n={row['m02_one_tool']['n']:2})  "
                     f"stage 2 {row['m07_stage2_two_tools']['per_call_median']:5} (n={row['m07_stage2_two_tools']['n']:2})  "
                     f"delta {row['delta_per_call']:+4}  minus spec {row['delta_minus_added_spec_est']:+4}")
    lines.append("")
    for key, r in record["per_call_base_and_residual (bounded from two-call samples; explained half estimated)"].items():
        lines.append(f"  {key:12} offered {r['offered']}: base {r['per_call_base']['lower']}–{r['per_call_base']['upper']}, "
                     f"explained ~{r['explained_by_committed_text_est']}, residual {r['residual_est']['lower']}–{r['residual_est']['upper']}")
    d = record["residual_delta"]
    lines.append(f"  residual delta: lower {d['lower']:+}, upper {d['upper']:+}  (added spec ~{d['added_spec_tokens_est']})")
    lines.append("")
    lines.append(record["reading"]["sentence"])
    lines.append(f"  rules out: {', '.join(record['reading']['rules_out'])}")
    lines.append(f"  cannot separate: {', '.join(record['reading']['cannot_separate'])}")
    lines.append(f"  owed: {record['reading']['paid_by']['owed_to']} at {record['reading']['paid_by']['date']}")
    return "\n".join(lines)


def verify_history() -> int:
    """Rebuild the M02-era texts from `git show` at the recorded commit and compare
    with the constants. Needs the local history; never run by the tests."""
    import ast
    import subprocess

    def show(path: str) -> str:
        return subprocess.run(["git", "show", f"{M02_ERA['commit']}:{path}"], capture_output=True,
                              check=True, cwd=ROOT).stdout.decode("utf-8")

    def blob(path: str) -> str:
        return subprocess.run(["git", "rev-parse", f"{M02_ERA['commit']}:{path}"], capture_output=True,
                              check=True, cwd=ROOT).stdout.decode("utf-8").strip()

    def constant(source: str, name: str) -> str:
        for node in ast.parse(source).body:
            if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == name):
                return node.value.value
        raise SystemExit(f"no {name} at {M02_ERA['commit'][:7]}")

    problems = []
    for path, expected in M02_ERA["blobs"].items():
        got = blob(path)
        if got != expected:
            problems.append(f"{path}: blob {got} at {M02_ERA['commit'][:7]}, constant says {expected}")
    client = show("services/highlights-agent/gateway_client.py")
    schema = show("services/highlights-agent/evals/answer.schema.json")
    contracts = json.loads(show("platform/gateway/policy/tools.contracts.json"))
    prompt = constant(client, "TOOL_SYSTEM").format(schema=schema)
    contract = contracts["catalog-search"]["input"]
    spec = json.dumps({"name": "catalog-search", "description": contract.get("description", "catalog-search"),
                       "inputSchema": {"json": contract}}, ensure_ascii=False)
    rebuilt = {"tool_system_prompt": _sha256_text(prompt), "catalog_search_toolspec": _sha256_text(spec)}
    for key, expected in M02_ERA["rebuilt_text_sha256_at_m02"].items():
        if rebuilt[key] != expected:
            problems.append(f"{key}: {rebuilt[key]} rebuilt from history, constant says {expected}")
    if constant(client, "CLOCK") != M02_ERA["clock_at_m02"]:
        problems.append("CLOCK at the M02 commit differs from the constant")
    for p in problems:
        print("MISMATCH:", p)
    if not problems:
        print(f"OK: the M02-era constants are what {M02_ERA['commit'][:7]} holds; HEAD's rebuilt texts "
              f"{'match' if head_text_digests() == M02_ERA['rebuilt_text_sha256_at_m02'] else 'DO NOT match'}")
    return 1 if problems else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--check", action="store_true",
                        help="recompute and compare with the committed record; write nothing; exit 1 on drift")
    parser.add_argument("--verify-history", action="store_true",
                        help="check the M02-era constants against `git show` at the recorded commit")
    args = parser.parse_args(argv)
    if args.verify_history:
        return verify_history()
    record = differential()
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
