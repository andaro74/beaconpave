"""
L0 unit tests: a governance check must be able to say why it blocked, on the
console the operator actually uses.

`pave gate two-key` renders its blocking path with U+2717. A Windows console
running cp1252 cannot encode that character, so `print` raised
UnicodeEncodeError and the command died *before* emitting the reason — the
operator got a traceback and exit 1, with the blocking reason nowhere on screen.
Exit 1 is coincidentally the right code, which is what made it survive: the
check looked like it worked.

CI never caught it. GitHub runners are UTF-8, so the glyph encodes fine there,
and M00a's Windows-parity DoD was written about `pave check` rather than the
gate commands.

These tests run identically on every platform: they pass an explicit encoding
rather than depending on whatever codepage the host happens to use, so the
Windows bug stays covered when the suite runs on a Linux runner.

Hermetic (G8). Owning seat: Platform Engineering.
"""
import pytest

from pave import cli, twokey

#: The character that actually broke, named rather than pasted so this file
#: stays readable in an editor that cannot render it.
BALLOT_X = "✗"


def test_a_console_that_can_show_the_glyph_gets_it_unchanged():
    """The fix must not degrade UTF-8 terminals or CI logs. Swapping the glyph
    for ASCII at the source would have — this is why the fix is at the output
    boundary and `twokey.render` still emits the real character."""
    text = f"two-key: BLOCKED (G9)\n  {BALLOT_X} missing disposition"
    assert cli._console_safe(text, "utf-8") == text
    assert BALLOT_X in cli._console_safe(text, "utf-8")


def test_a_cp1252_console_degrades_instead_of_raising():
    """The regression. Before the fix this path raised UnicodeEncodeError."""
    text = f"two-key: BLOCKED (G9)\n  {BALLOT_X} missing disposition from ai-quality"
    safe = cli._console_safe(text, "cp1252")
    safe.encode("cp1252")  # must not raise — this is the whole point
    assert "missing disposition from ai-quality" in safe, "the reason must survive the rewrite"


@pytest.mark.parametrize("encoding", ["cp1252", "cp437", "ascii", "utf-8"])
def test_the_real_blocking_message_is_emittable_on_any_console(encoding):
    """End-to-end against the actual renderer rather than a handcrafted string,
    so a future glyph added to `twokey.render` is covered by this test without
    anyone remembering to update it.

    `cp437` and `ascii` are here because cp1252 is not the only codepage a
    Windows console can be in, and under those even the em dashes this repo uses
    everywhere stop being representable."""
    changed = ["services/highlights-agent/evals/golden/cases.yaml"]
    problems = twokey.evaluate(changed, "", repo_root=cli.ROOT)
    assert problems, "expected an undisposed two-key path to produce a problem"

    rendered = twokey.render(changed, problems)
    cli._console_safe(rendered, encoding).encode(encoding)


def test_emit_survives_a_stdout_that_cannot_encode_the_glyph(monkeypatch, capsys):
    """Guards the wiring, not just the helper: `_emit` must read the *stream's*
    encoding. An earlier shape of this fix cached the encoding at import time,
    which is wrong — stdout differs between a console, a pipe, and a redirect."""

    class Cp1252Stdout:
        encoding = "cp1252"

        def write(self, _):
            pass

        def flush(self):
            pass

    monkeypatch.setattr("sys.stdout", Cp1252Stdout())
    cli._emit(f"blocked {BALLOT_X} for a reason")  # must not raise
