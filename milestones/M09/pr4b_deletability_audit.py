#!/usr/bin/env python
"""PR 4b's deletability audit: every check this PR adds, deleted in turn.

SPEC/09 constraint 10, the standing step. Each mutation below **deletes or
disables one check** (or, where the check is a pin, moves the thing it pins), the
named tests are re-run, and the result is recorded RED or SILENT. A silent check
gets a test before merge or comes out.

**Working copies are backed up to a temp directory and restored from it —
never with `git checkout`**, which would delete the uncommitted change the audit
exists to test (M08b's own finding; ADR-075 amendment 3 §8). Every file this
script writes is written back byte for byte from its backup, and the script
verifies that at the end.

Run from the repository root:

    python milestones/M09/pr4b_deletability_audit.py

Zero model calls. Output committed beside it as `pr4b-deletability-audit.txt`.
"""
from __future__ import annotations

import dataclasses
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]


@dataclasses.dataclass
class Mutation:
    name: str
    path: str
    old: str
    new: str
    tests: list[str]
    #: What the mutation is meant to be caught by, for the report's third column.
    caught_by: str


M = Mutation
MUTATIONS = [
    M("f4: clause 1 (a <=3-call sample over 7700 that was under it at M08b) returns []",
      "milestones/M09/f4.py",
      '    m08b_over = set(m08b_join["claim"]["3_call_or_fewer_samples_over"])\n'
      '    return [s for s in join["claim"]["3_call_or_fewer_samples_over"] if s not in m08b_over]',
      "    return []",
      ["tests/test_m09_f4.py"],
      "test_every_clause_is_reachable_and_none_is_decorative"),
    M("f4: clause 2 (a 3-of-3 M08b pass failing by majority) returns [] -- the clause that FIRED",
      "milestones/M09/f4.py",
      '    return [c for c in base\n'
      '            if all(s == "PASS" for s in base[c]) and now[c]["result"] != "PASS"]',
      "    return []",
      ["tests/test_m09_f4.py"],
      "test_clause_2_fired_on_grounded_017"),
    M("f4: clause 3 (a 0-of-3 M08b fail passing by majority) returns []",
      "milestones/M09/f4.py",
      '    return [c for c in base\n'
      '            if all(s == "FAIL" for s in base[c]) and now[c]["result"] == "PASS"]',
      "    return []",
      ["tests/test_m09_f4.py"],
      "test_every_clause_is_reachable_and_none_is_decorative"),
    M("f4: the case-set guard stops refusing a baseline that is missing a case",
      "milestones/M09/f4.py",
      '    if set(base) != set(now):\n'
      '        raise SystemExit(f"the baseline names {len(base)} cases and the control run "\n'
      '                         f"{len(now)}; F4 compares case for case and cannot compare these")',
      "    return None",
      ["tests/test_m09_f4.py"],
      "test_the_reader_refuses_a_baseline_and_a_run_with_different_case_sets"),
    M("f4: the count loses its SIDE-PREDICTION label and reads as a falsifier",
      "milestones/M09/f4.py",
      'f"SIDE-PREDICTION (not F4, not the claim)  count N = {n}/{k3[\'count\'][\'total\']} "',
      'f"count N = {n}/{k3[\'count\'][\'total\']} "',
      ["tests/test_m09_f4.py"],
      "test_the_count_is_printed_after_the_falsifier_and_labelled"),
    M("f4: the reading stops saying the claim was already FAILED on F1",
      "milestones/M09/f4.py",
      '    print("THE CLAIM IS FAILED. F1 fired on disclosure-103 at PR 4 (ADR-075 amendment 5) "',
      '    print("F4 has been read. "',
      ["tests/test_m09_f4.py"],
      "test_the_count_is_printed_after_the_falsifier_and_labelled"),
    M("f4: a case id typed in beside the baseline instead of read from the entry",
      "milestones/M09/f4.py",
      'COUNT_BAND = (8, 12)',
      'COUNT_BAND = (8, 12)\n_PLANTED = "entitlement-010"',
      ["tests/test_m09_f4.py"],
      "test_the_baseline_is_the_published_entry_and_not_a_list_in_the_reader"),
    M("f4: the browse-gap seven quietly become six",
      "milestones/M09/f4.py",
      'BROWSE_GAP_SEVEN = ("recommend-003", "recommend-013", "recommend-014",\n'
      '                    "grounded-018", "grounded-019", "multi-023", "edge-025")',
      'BROWSE_GAP_SEVEN = ("recommend-003", "recommend-013", "recommend-014",\n'
      '                    "grounded-018", "grounded-019", "multi-023")',
      ["tests/test_m09_f4.py"],
      "test_the_seven_browse_gap_cases_are_seven_real_cases"),
    M("fresh_join: the cp1252 fallback removed -- emit() becomes print()",
      "milestones/M08b/fresh_join.py",
      "    stream = sys.stdout if stream is None else stream\n    try:\n        print(text, file=stream)\n        return\n    except UnicodeEncodeError:\n        pass",
      "    print(text, file=sys.stdout if stream is None else stream)\n    return\n    if False:\n        pass",
      ["tests/test_m08b_fresh_join.py"],
      "test_the_render_path_survives_a_cp1252_console"),
    M("fresh_join: the fallback keeps the exception away but loses the relation (errors='replace')",
      "milestones/M08b/fresh_join.py",
      "    for char, ascii_form in ASCII_FALLBACK.items():\n        text = text.replace(char, ascii_form)",
      "    pass",
      ["tests/test_m08b_fresh_join.py"],
      "test_the_fallback_keeps_the_relation_rather_than_replacing_it"),
    M("fresh_join: the fallback runs on EVERY stream, not only the one that refused",
      "milestones/M08b/fresh_join.py",
      "    try:\n        print(text, file=stream)\n        return\n    except UnicodeEncodeError:\n        pass",
      "    if False:\n        print(text, file=stream)",
      ["tests/test_m08b_fresh_join.py"],
      "test_a_stream_that_can_carry_the_report_is_written_once_and_unchanged"),
    M("history: README_GOLDENS stops pinning m09, so the published 10/25 backs onto no entry",
      "pave/history.py",
      '    "m09": "m09-tools-goldens.json",\n}',
      "}",
      ["tests/test_history_checks.py", "tests/test_m09_f4.py"],
      "check_readme's exact-set, both directions"),
    M("README: row 09's bold 10/25 removed while the entry stays on disk",
      "README.md",
      "| `m09` | **10/25** ❉ |",
      "| `m09` | –/25 ❉ |",
      ["tests/test_history_checks.py"],
      "check_readme: a goldens entry whose row is pinned to none"),
    M("M08b README: the era line beside the published 92.9% removed",
      "milestones/M08b/README.md",
      "> **That 92.9% is era-pinned to M08b's prompt, and the number is not a standing",
      "> **That 92.9% is a standing property of the system, and the number is not",
      ["tests/test_m08b_residual.py"],
      "test_the_published_figure_names_its_era"),
    M("the era-debt trigger: a prompt constant moves (the event the trigger exists for)",
      "services/highlights-agent/gateway_client.py",
      "TOOL_SYSTEM = ",
      "_AUDIT_PLANT = 1\nTOOL_SYSTEM = ",
      ["tests/test_m08b_residual.py"],
      "test_a_prompt_constant_may_not_move_before_this_records_era_debt_is_paid"),
    M("the cascade: a record outside the governed directories digests the prompt",
      "milestones/M09/f4.py",
      "#!/usr/bin/env python",
      "#!/usr/bin/env python",
      ["tests/test_m09_goldens_denominator.py"],
      "test_the_records_the_fix_moves_are_derived_and_not_listed (the `rest` clause)"),
    M("ADR-075 stops naming milestones/M09/fresh-join.json, the record this PR adds to the cascade",
      "docs/adr/ADR-075-m09-is-two-milestones-and-the-disposition-ships-without-a-deploy.md",
      "`milestones/M09/fresh-join.json` (written by M08b's own `fresh_join.py`),",
      "the goldens control run's join record,",
      ["tests/test_m09_goldens_denominator.py"],
      "test_the_spec_names_every_record_the_cascade_moves (the ADR branch)"),
]

#: The one mutation that is not a text edit: a stray record under a directory the
#: Definition of done does not govern, digesting a model-facing file.
STRAY_RECORD = ROOT / "milestones" / "M07" / "audit-plant-record.json"
STRAY_BODY = ('{"inputs_sha256": {"services/highlights-agent/evals/golden/'
              'cases.yaml": "0000"}}\n')


def run(tests: list[str]) -> bool:
    """True if the suite went RED."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *tests, "-q", "--no-header", "-x"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.returncode != 0


def main() -> int:
    backup = pathlib.Path(tempfile.mkdtemp(prefix="m09-pr4b-audit-"))
    touched = sorted({m.path for m in MUTATIONS})
    for rel in touched:
        dest = backup / rel.replace("/", "__")
        shutil.copy2(ROOT / rel, dest)
    print(f"working copies backed up to {backup}\n")

    rows = []
    try:
        for i, mut in enumerate(MUTATIONS, 1):
            target = ROOT / mut.path
            original = target.read_text(encoding="utf-8")
            stray = "a record outside the governed directories" in mut.name
            if stray:
                STRAY_RECORD.write_text(STRAY_BODY, encoding="utf-8", newline="\n")
            else:
                if original.count(mut.old) != 1:
                    raise SystemExit(
                        f"[{i}] {mut.name}: the text to mutate appears "
                        f"{original.count(mut.old)} times in {mut.path}. An audit that "
                        "silently mutates nothing reports every check RED for free "
                        "(the 'verify the plant before the count' finding).")
                target.write_text(original.replace(mut.old, mut.new),
                                  encoding="utf-8", newline="")
            try:
                red = run(mut.tests)
            finally:
                if stray:
                    STRAY_RECORD.unlink()
                else:
                    target.write_text(original, encoding="utf-8", newline="")
            rows.append((i, mut.name, mut.caught_by, "RED" if red else "SILENT"))
            print(f"  [{i:>2}] {'RED   ' if red else 'SILENT'}  {mut.name}")
    finally:
        for rel in touched:
            restored = (backup / rel.replace("/", "__")).read_bytes()
            assert (ROOT / rel).read_bytes() == restored, (
                f"{rel} was not restored byte for byte; restore it from {backup}")
        if STRAY_RECORD.exists():
            STRAY_RECORD.unlink()

    print()
    print("| # | mutation | caught by | result |")
    print("|---|---|---|---|")
    for i, name, caught, result in rows:
        mark = f"**{result}**" if result == "RED" else f"**{result}**"
        print(f"| {i} | {name} | {caught} | {mark} |")
    silent = [r for r in rows if r[3] == "SILENT"]
    print()
    print(f"{len(rows)} mutations, {len(rows) - len(silent)} RED, {len(silent)} SILENT")
    for row in silent:
        print(f"  SILENT: {row[1]}")
    print(f"\nevery working copy restored from {backup} byte for byte (no `git checkout`)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
