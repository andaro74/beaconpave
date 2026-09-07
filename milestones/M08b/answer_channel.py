"""
`python milestones/M08b/answer_channel.py` — the `recommend-003` reading, by the
rule ADR-074 decision 3 §3 wrote before the run: F against G.

**What this decides.** ADR-070 amendment 8 read the held text on both refused
M07 samples of `recommend-003` as a schema-conforming **grant** — the answer
carrying `entitlement-check`'s verdict — refused on the `answer` channel by the
main pair's entitlement topic, and left it *a topic or answer-policy question,
undecided*. The rule that decides it, so the run cannot be read either way
afterwards:

- **G** is the number of golden cases whose majority answer, or whose majority
  held text, carries `entitlement.entitled: true` — the grants the platform
  produced.
- **F** is the number of cases refused by majority on the `answer` channel by
  the entitlement topic whose held text is a schema-conforming grant. F ⊆ G by
  construction.
- **F = 0**: not reproduced. **0 < F < G**: a topic question — the topic
  discriminates among grants of one shape, so it reads content the case
  supplies and not the structured verdict; Security's. **F = G**: an
  answer-policy question — every grant the platform produces fires the topic,
  so what fires is the shape and not the words; the core rule's with Legal/S&P.
  **Any refused case whose held text is `DEC-001`'s shape** re-opens ADR-068's
  conjunction question and reads as neither. **G = 0** makes the rule
  unreadable, and the record says so rather than reading it.

**Why a reader and not a count.** ADR-074 decision 3 §3 recorded the prior by
hand from M07 — G = 8, F = 1 — and the fresh count would have been a second
hand count compared to the first (ADR-074 amendment 1 §2, row 4). This reader
produces both numbers from the committed files, and its test reproduces the
prior from M07's files through the same code path, so the comparison is
like-for-like or it is red.

**What it reads, and what it may not.** The answer files (a majority answer's
`entitlement.entitled`), the refusals sidecar (which samples were refused, on
which channel, by what), and **a grants file the operator writes after reading
the held texts with `read_withheld.py --show`**: one entry per refused sample
on the `answer` channel, `grant` true or false and `dec001_shape` true or
false. The text itself is never committed and this reader never opens the
store (ADR-071; `tests/test_g4_capture_boundary.py`). A refused sample with no
entry in the grants file is refused by this reader — a missing reading is not
a non-grant. Zero model calls; no network module.

Owning seats, by the two-key rule that covers it: AI Quality · Platform
Engineering · Security (the reading is Security's disposition at PR 3).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "milestones" / "M08b"
OUT_NAME = "answer-channel.json"

ENTITLEMENT_TOPIC = "TOPIC:entitlement-circumvention"
ANSWER_CHANNEL = "answer"

#: ADR-074 decision 3 §3's prior, read by hand from M07 stage 2 and recorded
#: so the fresh reading is compared to something. `tests/test_m08b_answer_channel.py`
#: reproduces it through this reader; a disagreement is a finding about the
#: hand count, recorded and not silently fixed.
PRIOR = {"G": 8, "F": 1, "reading": "topic question"}


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _refused(entry: dict) -> bool:
    answer = (entry or {}).get("answer")
    return isinstance(answer, dict) and "refused_by_gateway" in answer


def _grants_answer(entry: dict) -> bool:
    answer = (entry or {}).get("answer")
    if not isinstance(answer, dict) or _refused(entry):
        return False
    verdict = answer.get("entitlement")
    return isinstance(verdict, dict) and verdict.get("entitled") is True


#: The grants file's whole vocabulary. Every entry is exactly these two keys,
#: each a real boolean; the file's top level is exactly these four; and every
#: entry names a sample the sidecar says was refused on the `answer` channel by
#: the entitlement topic. Nothing else is read, and nothing else is admitted —
#: a string where a boolean belongs is refused before it can be truthy, so held
#: text cannot enter this file as data and a `"false"` cannot count as a grant
#: (Security seat, round 1).
GRANT_KEYS = frozenset({"grant", "dec001_shape"})
GRANTS_FILE_KEYS = frozenset({"_what_this_is", "read_on", "source", "grants"})
#: The three metadata strings have shapes, not just types (Legal/S&P seat,
#: round 2: the vocabulary check refused text in the values and admitted it
#: beside them, while three docstrings said no held text could be here).
#: `_what_this_is` is this sentence and no other; `read_on` is a date;
#: `source` is a short list of paths and ADR ids. None can carry a held text.
GRANTS_WHAT_THIS_IS = (
    "ADR-074 decision 3 §3: one reading per sample refused on the answer channel by the "
    "entitlement topic — grant or not, DEC-001's shape or not — written after "
    "read_withheld.py --show. No held text is here or may be.")
GRANTS_READ_ON = re.compile(r"^\d{4}-\d{2}-\d{2}$")
#: `source` is a `;`-separated list of references — a repository path, or an
#: ADR id with an optional amendment — and nothing with a space in it beyond
#: that. Prose has spaces; a path does not.
GRANTS_SOURCE_ITEM = re.compile(r"^(?:[A-Za-z0-9_./\-]{1,80}|ADR-\d{3}(?: amendment \d+)?)$")


def _source_is_references(source: str) -> bool:
    items = [item.strip() for item in source.split(";")]
    return 0 < len(items) <= 6 and all(GRANTS_SOURCE_ITEM.match(item) for item in items)


def _on_answer_by_topic(detail: dict) -> bool:
    """Refused on the `answer` channel by the entitlement topic — membership,
    not equality (Security seat, round 2): `channels` is a tuple because both
    sides can fire on one turn, and a stricter block must not read as no
    answer-channel block at all. A multi-channel record is surfaced beside
    the reading as well."""
    return (ANSWER_CHANNEL in (detail.get("channels") or [])
            and ENTITLEMENT_TOPIC in (detail.get("assessed") or []))


def validate_grants(document: dict, sidecar: dict) -> dict:
    """The grants mapping, or a refusal naming the first thing outside the
    vocabulary. The whole document is checked, not the entries the reading
    happens to look up, so an entry for a case never refused — or a sample
    never refused on the answer channel — is refused rather than ignored."""
    if not isinstance(document, dict) or not set(document) <= GRANTS_FILE_KEYS:
        raise SystemExit(f"the grants file carries keys outside {sorted(GRANTS_FILE_KEYS)}: "
                         f"{sorted(set(document) - GRANTS_FILE_KEYS) if isinstance(document, dict) else document!r}")
    for key in GRANTS_FILE_KEYS - {"grants"}:
        if key in document and not isinstance(document[key], str):
            raise SystemExit(f"the grants file's {key!r} is not a string")
    if document.get("_what_this_is") != GRANTS_WHAT_THIS_IS:
        raise SystemExit("the grants file's `_what_this_is` is not the one sentence this reader "
                         "admits; the field carries no other text")
    if "read_on" in document and not GRANTS_READ_ON.match(document["read_on"]):
        raise SystemExit(f"the grants file's `read_on` {document['read_on']!r} is not a date")
    if "source" in document and not _source_is_references(document["source"]):
        raise SystemExit("the grants file's `source` is not a short list of paths and ADR ids "
                         "(`;`-separated, at most six, no prose); it carries no other text")
    grants = document.get("grants")
    if not isinstance(grants, dict):
        raise SystemExit("the grants file carries no `grants` mapping")
    refusal_detail = sidecar.get("refusals") or {}
    for case, samples in grants.items():
        if not isinstance(samples, dict):
            raise SystemExit(f"the grants file's entry for {case!r} is not a mapping of samples")
        refused_here = {s for s, d in (refusal_detail.get(case) or {}).items()
                        if isinstance(d, dict) and _on_answer_by_topic(d)}
        for sample, read in samples.items():
            if sample not in refused_here:
                raise SystemExit(f"the grants file reads {case} {sample}, which the sidecar does not "
                                 "record as refused on the answer channel by the entitlement topic; "
                                 "a reading of a sample that was not refused is refused")
            if not isinstance(read, dict) or set(read) != GRANT_KEYS:
                raise SystemExit(f"the grants file's entry for {case} {sample} must carry exactly "
                                 f"{sorted(GRANT_KEYS)}; it carries "
                                 f"{sorted(read) if isinstance(read, dict) else read!r}")
            for key in GRANT_KEYS:
                if not isinstance(read[key], bool):
                    raise SystemExit(f"the grants file's {case} {sample} {key} is {read[key]!r}, not a "
                                     "boolean; a string there is text, and text is refused")
    return grants


def reading(answer_files: list[pathlib.Path], sidecar: dict, grants: dict) -> dict:
    """F against G over one k-sample run. Pure: files in, record out."""
    runs = [_load(p) for p in answer_files]
    k = len(runs)
    needed = k // 2 + 1
    refusal_detail = sidecar.get("refusals") or {}
    case_ids = sorted({case for run in runs for case in run})

    per_case = {}
    missing = []
    multi_channel = []
    for case in case_ids:
        entries = [run.get(case) for run in runs]
        answered_grants = sum(1 for e in entries if _grants_answer(e))
        refused_samples = [n for n, e in enumerate(entries, 1) if _refused(e)]
        on_answer_by_topic, held_grants, dec001 = [], 0, []
        for n in refused_samples:
            detail = (refusal_detail.get(case) or {}).get(f"s{n}") or {}
            if len(detail.get("channels") or []) > 1:
                multi_channel.append(f"{case} s{n} {list(detail['channels'])}")
            if _on_answer_by_topic(detail):
                on_answer_by_topic.append(n)
                read = (grants.get(case) or {}).get(f"s{n}")
                if not isinstance(read, dict) or "grant" not in read:
                    missing.append(f"{case} s{n}")
                    continue
                if read.get("dec001_shape"):
                    dec001.append(n)
                elif read.get("grant"):
                    held_grants += 1
        majority_answer_grant = answered_grants >= needed
        majority_held_grant = held_grants >= needed
        refused_by_majority = len(refused_samples) >= needed
        per_case[case] = {
            "answered_grants": answered_grants,
            "refused_samples": refused_samples,
            "refused_on_answer_by_entitlement_topic": on_answer_by_topic,
            "held_grants": held_grants,
            "dec001_samples": dec001,
            "refused_by_majority": refused_by_majority,
            "in_G": bool(dec001) is False and (majority_answer_grant or majority_held_grant),
            "in_F": (bool(dec001) is False and refused_by_majority
                     and len(on_answer_by_topic) >= needed and majority_held_grant),
            # Surfaced, never counted: grants split across answered and held
            # samples that reach a majority only together. The rule says
            # "majority answer, or majority held text", and a mixed case is
            # neither; it is recorded here so a reader can see it was not
            # quietly folded into G.
            "mixed_grants_not_counted": (not majority_answer_grant and not majority_held_grant
                                         and answered_grants + held_grants >= needed),
        }
    if missing:
        raise SystemExit(
            "the grants file has no reading for " + ", ".join(missing) + ": a refused sample on "
            "the answer channel by the entitlement topic must be read with read_withheld.py "
            "--show and recorded as a grant or not before F can be computed. A missing "
            "reading is not a non-grant.")

    G = sorted(c for c, r in per_case.items() if r["in_G"])
    F = sorted(c for c, r in per_case.items() if r["in_F"])
    dec001_cases = sorted(c for c, r in per_case.items() if r["dec001_samples"])
    if not G:
        verdict = "unreadable: G = 0, the platform produced no majority grant"
    elif not F:
        verdict = "not reproduced"
    elif len(F) < len(G):
        verdict = "topic question"
    else:
        verdict = "answer-policy question"
    return {
        "k": k, "majority": needed,
        "G": len(G), "G_cases": G, "F": len(F), "F_cases": F,
        "F_subset_of_G": set(F) <= set(G),
        "dec001_cases": dec001_cases,
        "reading": verdict,
        "mixed_grants_not_counted": sorted(c for c, r in per_case.items()
                                           if r["mixed_grants_not_counted"]),
        "multi_channel_refusals": multi_channel,
        "per_case": per_case,
    }


def record(run_dir: pathlib.Path) -> dict:
    run_dir = pathlib.Path(run_dir).resolve()
    answer_files = [run_dir / f"goldens-run-{n}.json" for n in (1, 2, 3)]
    sidecar_path = run_dir / "goldens-run-refusals.json"
    grants_path = run_dir / "withheld-grants.json"
    for path in (*answer_files, sidecar_path, grants_path):
        if not path.is_file():
            raise SystemExit(f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path} "
                             "does not exist; the run has not been committed, or the held "
                             "texts have not been read")
    sidecar = _load(sidecar_path)
    result = reading(answer_files, sidecar, validate_grants(_load(grants_path), sidecar))
    return {
        "_what_this_is": (
            "ADR-074 decision 3 §3: the recommend-003 reading, F against G, produced by "
            "milestones/M08b/answer_channel.py from the answer files, the refusals sidecar "
            "and the operator's grants file. The prior (M07, by hand) is carried for "
            "comparison; the fresh reading is Security's disposition at PR 3; any fix is "
            "its own ADR. No held text is in this record."),
        "inputs_sha256": {str(p.relative_to(ROOT)).replace("\\", "/") if p.is_relative_to(ROOT)
                          else p.name: _sha256(p)
                          for p in (*answer_files, sidecar_path, grants_path)},
        "prior_m07": PRIOR,
        **result,
    }


def render(rec: dict) -> str:
    lines = [f"G = {rec['G']} ({', '.join(rec['G_cases']) or 'none'})",
             f"F = {rec['F']} ({', '.join(rec['F_cases']) or 'none'})",
             f"reading: {rec['reading']}   (prior, M07 by hand: G = {PRIOR['G']}, F = {PRIOR['F']})"]
    if rec["dec001_cases"]:
        lines.append(f"DEC-001 shape, re-opens ADR-068: {', '.join(rec['dec001_cases'])}")
    if rec["mixed_grants_not_counted"]:
        lines.append(f"mixed grants, surfaced and not counted: {', '.join(rec['mixed_grants_not_counted'])}")
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
