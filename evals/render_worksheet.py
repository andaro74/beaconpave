"""Regenerates the calibration review worksheet from the committed corpus.

Its own module so that `python -m evals.render_worksheet` is the whole command a
reviewer needs, and so the worksheet is never produced by an ad-hoc script whose
output nobody can reproduce. Hermetic: committed answers, no model.
"""
from __future__ import annotations

import json

import yaml

from evals.calibration import ROOT, worksheet

CASES = ROOT / "services" / "highlights-agent" / "evals" / "golden" / "cases.yaml"
LABELS = ROOT / "quality" / "judge" / "calibration" / "labels.json"
OUT = ROOT / "quality" / "judge" / "calibration" / "WORKSHEET.md"


def render() -> str:
    return worksheet(
        yaml.safe_load(CASES.read_text(encoding="utf-8")),
        json.loads(LABELS.read_text(encoding="utf-8")),
    )


if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
