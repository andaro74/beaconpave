# surfaces/web-player/tests

`player_smoke.py` drives the served static player with Playwright and writes what it
observed. `../emit.py` turns that into a verdict record, and `../run.py` runs it beside
`loadtest/smoke.js` (k6) against the same served surface. Neither runner decides
anything: `python -m pave.cli gate decide --verdicts` does (SPEC/10, ADR-079).

Not collected by pytest. It needs a browser, and `make check` is hermetic (G8).
