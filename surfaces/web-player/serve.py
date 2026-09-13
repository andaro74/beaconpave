"""
Serve the static player on 127.0.0.1 for the surface runners. Standard library only.

The player is static files, so the smallest server shaped correctly is the one the
standard library already has. It binds the loopback interface and an ephemeral port, so
a run reaches nothing beyond this machine and two runs cannot collide on a port.

Owning seat: Platform Engineering.
"""
from __future__ import annotations

import contextlib
import functools
import http.server
import pathlib
import threading
from collections.abc import Iterator

SITE = pathlib.Path(__file__).resolve().parent / "site"


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:
        # k6 sends thousands of requests; one log line each would bury the runner's output.
        pass


@contextlib.contextmanager
def serving(site: pathlib.Path = SITE) -> Iterator[str]:
    """Serve `site` for the duration of the block and yield its root URL."""
    handler = functools.partial(_QuietHandler, directory=str(site))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        server.server_close()
