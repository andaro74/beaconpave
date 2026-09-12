"""
`python milestones/M09b/fg.py` — F against G on one goldens run, on both
estimators, from two independent grant readings, against a baseline the caller
names.

    python milestones/M09b/fg.py --run milestones/M09 \
        --grants milestones/M09b/withheld-grants-security.json \
        --grants milestones/M09b/withheld-grants-legal-sp.json \
        --baseline milestones/M08b/answer-channel.json \
        --out milestones/M09b/fg-pre.json

**What it inherits and does not re-decide.** G and the majority F are
`milestones/M08b/answer_channel.py`'s: ADR-074 decision 3 §3's rule, which
ADR-075 decision 5 §5 pre-registered as `F = 0 with G ≥ 8` and SPEC/09b's F1
inherits unchanged. This file imports `validate_grants` and `reading` from that
module and computes neither number a second time. A second copy of that
arithmetic would be the one-rule-two-expressions shape `evals/refusals.py`'s
two-key rule was written about.

**What it adds, each for a dated reason.**

1. **The baseline is an argument** (ADR-076 decision 6; SPEC/09b's debt whose
   trigger is *the next milestone that re-runs the goldens as a control*).
   `answer_channel.py` carries its prior as the module constant `PRIOR`, M07's,
   and M09's own direction block read against M08 the same way and reported both
   falsifier lists empty on the run where F4.2 fired. There is no default: a
   reading compared to nothing named on the command line is refused.
2. **Two readings, and where they disagree the disagreement is the reading**
   (ADR-076 amendment 1, *F1 is a one-key control over the claim's outcome*).
   Exactly two grants files, each read on its own. Where any boolean differs, F
   and G are published per reading and no single number is.
3. **The at-least-once companion** (ADR-076 decision 6). Defined here before
   this file first ran: `F_at_least_once` is the cases with at least one sample
   refused on the `answer` channel by the entitlement topic whose held text the
   reading records as a grant, in a case with no sample read as DEC-001's shape
   (the case-level exclusion `answer_channel.py` applies to F). It is not
   restricted to G; the cases outside G
   are published beside it rather than dropped.
4. **The refusal reading on both estimators**, per topic and per channel, from
   the run's sidecar, through `evals.refusals.census_from_samples`, the
   estimator every sidecar's census is computed by.

**What nobody outside the operator can check.** A grants file is booleans over
text the control withheld and the repository may not hold (ADR-071). F and G are
checkable against those booleans and never outsider-verifiable (SPEC/09b:109-122).
Two readers taken by one operator make F *checkable*; they do not make it two
humans' reading, and a record of this file does not say otherwise.

Zero model calls; no network module. Scores nothing and enters no history entry.
Owning seats, by the two-key rule that covers it: AI Quality · Platform
Engineering · Security.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.refusals import census_from_samples  # noqa: E402

READER = ROOT / "milestones" / "M08b" / "answer_channel.py"
READINGS = 2
GRANTS_PREFIX = "withheld-grants-"
CANONICAL_CASE = "blackout-009"
TOPIC_PREFIX = "TOPIC:"
ESTIMATOR_FIELDS = ("refused_by_majority", "refused_at_least_once", "cases_by_majority",
                    "cases_at_least_once", "cases_separating_the_estimators")


def _load_answer_channel():
    spec = importlib.util.spec_from_file_location("m08b_answer_channel", READER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AC = _load_answer_channel()


def _rel(path: pathlib.Path) -> str:
    path = pathlib.Path(path).resolve()
    return str(path.relative_to(ROOT)).replace("\\", "/") if path.is_relative_to(ROOT) else path.name


def _label(path: pathlib.Path) -> str:
    stem = pathlib.Path(path).stem
    return stem[len(GRANTS_PREFIX):] if stem.startswith(GRANTS_PREFIX) and stem != GRANTS_PREFIX else stem


def f_at_least_once(per_case: dict, grants: dict) -> list[str]:
    """Item 3 of the docstring, and nothing else."""
    out = []
    for case, row in per_case.items():
        if row["dec001_samples"]:
            continue
        read = grants.get(case) or {}
        if any((read.get(f"s{n}") or {}).get("grant") is True
               for n in row["refused_on_answer_by_entitlement_topic"]):
            out.append(case)
    return sorted(out)


def read_one(answer_files: list[pathlib.Path], sidecar: dict, grants_path: pathlib.Path):
    grants = AC.validate_grants(AC._load(grants_path), sidecar)
    result = AC.reading(answer_files, sidecar, grants)
    alo = f_at_least_once(result["per_case"], grants)
    return grants, {
        "G": result["G"], "G_cases": result["G_cases"],
        "F_majority": result["F"], "F_majority_cases": result["F_cases"],
        "F_at_least_once": len(alo), "F_at_least_once_cases": alo,
        "F_at_least_once_outside_G": sorted(set(alo) - set(result["G_cases"])),
        "dec001_cases": result["dec001_cases"],
        "answer_channel_reading": result["reading"],
        "mixed_grants_not_counted": result["mixed_grants_not_counted"],
        "multi_channel_refusals": result["multi_channel_refusals"],
    }


def disagreements(a: dict, b: dict) -> list[str]:
    """Every boolean the two readings do not share, named. Never resolved."""
    out = []
    for case in sorted(set(a) | set(b)):
        samples_a, samples_b = a.get(case) or {}, b.get(case) or {}
        for sample in sorted(set(samples_a) | set(samples_b)):
            read_a, read_b = samples_a.get(sample) or {}, samples_b.get(sample) or {}
            for key in sorted(AC.GRANT_KEYS):
                if read_a.get(key) != read_b.get(key):
                    out.append(f"{case} {sample} {key}: {read_a.get(key)} / {read_b.get(key)}")
    return out


def baseline_numbers(document) -> dict:
    """The numbers a baseline record carries, from either reader's record shape.

    An `answer_channel.py` record carries `G` and `F` (majority) and no
    at-least-once figure, which is published as absent rather than as zero. A
    record of this file carries its agreed reading; one whose readings disagree
    has no single number to compare against and is refused."""
    if isinstance(document, dict) and isinstance(document.get("reading"), dict):
        agreed = document["reading"]
        if agreed.get("agree") is not True:
            raise SystemExit("the baseline's two readings disagree, so it has no single F or G to "
                             "compare against; name a baseline whose readings agree")
        return {"G": agreed["G"], "F_majority": agreed["F_majority"],
                "F_at_least_once": agreed["F_at_least_once"]}
    if (isinstance(document, dict) and isinstance(document.get("G"), int)
            and isinstance(document.get("F"), int)):
        return {"G": document["G"], "F_majority": document["F"], "F_at_least_once": None}
    raise SystemExit("the baseline is neither an answer_channel.py record nor a record of this "
                     "file; a reading compared to an unreadable baseline is compared to nothing")


def _census(sidecar: dict, predicate) -> dict:
    """Both estimators over the samples `predicate` counts as refused.

    A sample the run marks refused and the sidecar does not describe is refused
    here, never counted as a refusal by nobody: an unattributed refusal read as
    no topic's refusal is the flattering direction. A lost sample stays `None`."""
    k = sidecar["_k"]
    detail = sidecar.get("refusals") or {}
    per_sample = {}
    for case, refused in sorted(sidecar["per_sample_refused"].items()):
        row = []
        for n, was_refused in enumerate(refused, 1):
            if was_refused is None:
                row.append(None)
                continue
            described = (detail.get(case) or {}).get(f"s{n}")
            if was_refused and not isinstance(described, dict):
                raise SystemExit(f"{case} s{n} is refused and the sidecar does not describe it; an "
                                 "unattributed refusal cannot be assigned to a topic or a channel")
            row.append(bool(was_refused) and predicate(described))
        per_sample[case] = row
    census = census_from_samples(per_sample, k)
    return {field: census[field] for field in ESTIMATOR_FIELDS}


def refusal_reading(sidecar: dict) -> dict:
    detail = sidecar.get("refusals") or {}
    topics = sorted({name for per_case in detail.values() for d in (per_case or {}).values()
                     if isinstance(d, dict) for name in (d.get("assessed") or [])
                     if name.startswith(TOPIC_PREFIX)})

    def by(topic, channel):
        return lambda d: (topic in (d.get("assessed") or [])
                          and (channel is None or channel in (d.get("channels") or [])))

    any_refusal = _census(sidecar, lambda d: True)
    committed = sidecar.get("census") or {}
    return {
        "k": sidecar["_k"],
        "n_cases": len(sidecar["per_sample_refused"]),
        "any_refusal": any_refusal,
        # The run wrote its own census before anybody read it. Recomputing it here
        # and publishing whether the two agree is what makes the per-topic rows
        # below comparable to it rather than a second, unreconciled count.
        "any_refusal_matches_the_sidecars_census": all(
            any_refusal[field] == committed.get(field) for field in ESTIMATOR_FIELDS),
        "by_topic": {topic: {"any_channel": _census(sidecar, by(topic, None)),
                             "answer_channel": _census(sidecar, by(topic, AC.ANSWER_CHANNEL))}
                     for topic in topics},
    }


def canonical_case(sidecar: dict, case: str = CANONICAL_CASE) -> dict:
    """F1's third clause reads this case by majority on the answer channel by any
    topic, so each sample's channels and topics are published, not a verdict."""
    k = sidecar["_k"]
    refused = sidecar["per_sample_refused"].get(case) or [None] * k
    detail = (sidecar.get("refusals") or {}).get(case) or {}
    samples = []
    for n in range(1, k + 1):
        described = detail.get(f"s{n}") or {}
        samples.append({"sample": f"s{n}", "refused": refused[n - 1],
                        "channels": list(described.get("channels") or []),
                        "assessed": list(described.get("assessed") or [])})
    on_answer = sum(1 for s in samples if s["refused"] and AC.ANSWER_CHANNEL in s["channels"])
    return {"case": case, "samples": samples,
            "refused_on_answer_channel_by_any_topic": on_answer,
            "refused_on_answer_channel_by_majority": on_answer > k // 2}


def record(run_dir: pathlib.Path, grants_paths: list[pathlib.Path],
           baseline_path: pathlib.Path) -> dict:
    run_dir = pathlib.Path(run_dir).resolve()
    grants_paths = [pathlib.Path(p).resolve() for p in grants_paths]
    baseline_path = pathlib.Path(baseline_path).resolve()
    if len(grants_paths) != READINGS or len(set(grants_paths)) != READINGS:
        raise SystemExit(f"exactly {READINGS} distinct grants files, one per reader; got "
                         f"{[_rel(p) for p in grants_paths]}. One file named twice is one reading.")
    labels = [_label(p) for p in grants_paths]
    if len(set(labels)) != READINGS:
        raise SystemExit(f"the two readings carry one label, {labels}; a disagreement between "
                         "them could not be attributed")
    answer_files = [run_dir / f"goldens-run-{n}.json" for n in (1, 2, 3)]
    sidecar_path = run_dir / "goldens-run-refusals.json"
    for path in (*answer_files, sidecar_path, *grants_paths, baseline_path):
        if not path.is_file():
            raise SystemExit(f"{_rel(path)} does not exist")
    sidecar = AC._load(sidecar_path)

    grants, readings = {}, {}
    for label, path in zip(labels, grants_paths, strict=True):
        grants[label], readings[label] = read_one(answer_files, sidecar, path)
    first, second = labels
    differ = disagreements(grants[first], grants[second])
    numbers = ("G_cases", "F_majority_cases", "F_at_least_once_cases")
    agree = not differ and all(readings[first][n] == readings[second][n] for n in numbers)

    base = baseline_numbers(AC._load(baseline_path))
    if agree:
        this = readings[first]
        reading = {"agree": True, "G": this["G"], "F_majority": this["F_majority"],
                   "F_at_least_once": this["F_at_least_once"]}
        direction = {key: {"baseline": base[key], "this_run": this[key]} for key in base}
    else:
        reading = {"agree": False, "disagreements": differ,
                   "note": "the two readings disagree; F and G are published per reading "
                           "and neither is the reading"}
        direction = {label: {key: {"baseline": base[key], "this_run": readings[label][key]}
                             for key in base} for label in labels}

    return {
        "_what_this_is": (
            "SPEC/09b PR 2: F against G by milestones/M09b/fg.py, both estimators, from two "
            "independently committed grant readings, against the baseline named in `baseline`. "
            "G and F_majority are milestones/M08b/answer_channel.py's. No held text is in "
            "this record."),
        "inputs_sha256": {_rel(p): AC._sha256(p)
                          for p in (*answer_files, sidecar_path, *grants_paths, baseline_path)},
        "run": _rel(run_dir),
        "baseline": _rel(baseline_path),
        "readings": readings,
        "reading": reading,
        "direction_against_baseline": direction,
        "canonical_case": canonical_case(sidecar),
        "refusals": refusal_reading(sidecar),
    }


def render(rec: dict) -> str:
    lines = []
    for label, r in rec["readings"].items():
        lines.append(f"reading {label}: G = {r['G']}   F majority = {r['F_majority']} "
                     f"({', '.join(r['F_majority_cases']) or 'none'})   F at least once = "
                     f"{r['F_at_least_once']} ({', '.join(r['F_at_least_once_cases']) or 'none'})")
    lines.append("the readings agree" if rec["reading"]["agree"]
                 else "the readings DISAGREE: " + "; ".join(rec["reading"]["disagreements"]))
    lines.append(f"baseline: {rec['baseline']}")
    canon = rec["canonical_case"]
    lines.append(f"{canon['case']}: refused on the answer channel by any topic in "
                 f"{canon['refused_on_answer_channel_by_any_topic']} of {len(canon['samples'])}")
    for topic, row in rec["refusals"]["by_topic"].items():
        lines.append(f"{topic}: majority {row['any_channel']['refused_by_majority']}, at least once "
                     f"{row['any_channel']['refused_at_least_once']} of {rec['refusals']['n_cases']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="F against G, both estimators, two readings")
    parser.add_argument("--run", required=True, help="the run directory")
    parser.add_argument("--grants", action="append", required=True,
                        help="a grants file; pass exactly two, one per reader")
    parser.add_argument("--baseline", required=True,
                        help="the record this reading is compared to; there is no default")
    parser.add_argument("--out", required=True)
    parser.add_argument("--check", action="store_true",
                        help="recompute and compare with --out; write nothing; exit 1 on drift")
    args = parser.parse_args(argv)
    rec = record(pathlib.Path(args.run), [pathlib.Path(p) for p in args.grants],
                 pathlib.Path(args.baseline))
    text = json.dumps(rec, indent=2, ensure_ascii=False) + "\n"
    out = pathlib.Path(args.out)
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
