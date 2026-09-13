"""
Run both surface runners against the served static player and write their verdicts.

usage: python surfaces/web-player/run.py --out-dir DIR
           [--playwright-python PY] [--k6 K6] [--path PATH] [--no-serve]

  --out-dir DIR          where the raw outputs and the two verdict records are written
  --playwright-python PY an interpreter with the `surfaces` extra (default: this one)
  --k6 K6                the k6 binary (default: `k6` on PATH)
  --path PATH            request PATH under the served root instead of the root itself;
                         `missing` is a path the player does not serve, a planted failure
  --no-serve             start no server, so both runners meet a refused connection,
                         a planted harness error

Writes `playwright-raw.json`, `k6-summary.json`, `verdict-playwright.json`,
`verdict-k6.json` and `runner-versions.txt`. It exits 0 once both records are written,
whatever they say: **`python -m pave.cli gate decide --verdicts` is the decider**, never
this script. Reaches nothing beyond 127.0.0.1 and makes no model call.

Owning seat: Platform Engineering.
"""
from __future__ import annotations

import argparse
import contextlib
import pathlib
import socket
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import emit  # noqa: E402
import serve  # noqa: E402

ROOT = HERE.parents[1]


@contextlib.contextmanager
def _nothing_listening():
    """A loopback URL on a port that was free a moment ago and is not served."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    yield f"http://127.0.0.1:{port}/"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--playwright-python", default=sys.executable)
    ap.add_argument("--k6", default="k6")
    ap.add_argument("--path", default="")
    ap.add_argument("--no-serve", action="store_true")
    args = ap.parse_args(argv)

    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_pw, summary = out / "playwright-raw.json", out / "k6-summary.json"
    for stale in (raw_pw, summary):
        stale.unlink(missing_ok=True)

    k6_version = subprocess.run([args.k6, "version"], capture_output=True, text=True).stdout.strip()
    pw_version = subprocess.run(
        [args.playwright_python, "-c", "import importlib.metadata as m; print(m.version('playwright'))"],
        capture_output=True, text=True).stdout.strip()
    (out / "runner-versions.txt").write_text(
        f"playwright {pw_version or 'unavailable'}\n{k6_version or 'k6 unavailable'}\n", encoding="utf-8")

    context = _nothing_listening() if args.no_serve else serve.serving()
    with context as root_url:
        url = root_url + args.path
        subprocess.run([args.playwright_python, str(HERE / "tests" / "player_smoke.py"), url, str(raw_pw)])
        subprocess.run([args.k6, "run", "--quiet", "-e", f"TARGET={url}", "-e", f"SUMMARY_OUT={summary}",
                        str(ROOT / "loadtest" / "smoke.js")], capture_output=True, text=True)

    for kind, raw, name in (("playwright", raw_pw, "verdict-playwright.json"),
                            ("k6", summary, "verdict-k6.json")):
        record = emit.RECORDERS[kind](raw)
        emit.verdict.write(out / name, record)
        print(f"[surfaces] {kind}: {record['verdict']} -> {out / name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
