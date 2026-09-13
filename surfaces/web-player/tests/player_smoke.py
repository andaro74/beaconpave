"""
Drive the served static player with Playwright and write what the runner observed.

usage: python surfaces/web-player/tests/player_smoke.py <url> <raw-out.json>

**This decides nothing.** It writes the checks it made and whether each held, and
`surfaces/web-player/emit.py` maps that into the verdict envelope. A navigation that
cannot reach the page is written as `error`, never as a failed check: a page that
answered wrongly and a page that was never reached are different findings, and the
envelope says so as FAIL and INFRA.

Runs under an interpreter with the `surfaces` extra installed (`pyproject.toml`). The
hermetic suite never imports it.

Owning seat: AI Quality (the checks); Platform Engineering (the runner).
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright


def main(url: str, out: str) -> None:
    raw: dict = {"runner": "playwright", "url": url, "checks": [], "error": None}
    start = time.monotonic()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            raw["browser"] = f"chromium {browser.version}"
            page = browser.new_page()
            response = page.goto(url)
            raw["checks"] = [
                {"name": "the page responds 200",
                 "ok": bool(response is not None and response.status == 200)},
                {"name": "the title names the player", "ok": "Beacon player" in page.title()},
                {"name": "the player heading is visible",
                 "ok": page.locator("#player-title").is_visible()},
            ]
            browser.close()
    except PlaywrightError as exc:
        raw["checks"] = []
        raw["error"] = str(exc).splitlines()[0]
    raw["duration_s"] = round(time.monotonic() - start, 3)
    pathlib.Path(out).write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    held = sum(1 for c in raw["checks"] if c["ok"])
    print(f"[playwright] {held}/{len(raw['checks'])} checks held"
          + (f"; error: {raw['error']}" if raw["error"] else ""))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
