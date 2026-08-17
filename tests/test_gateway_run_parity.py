"""
The M01 run and the m00b run must differ by the gateway and nothing else.

M01's golden number is only interpretable if the prompt, the evaluation clock,
and the transport decoding are identical to the control's. If any of them drifted
by a word, the delta would be shared between the gateway and the drift, and the
milestone could not say which part was which. That is the ADR-016 hazard —
comparing two numbers produced by different instruments — arriving somewhere new.

Both files are read **as source text and parsed with `ast`**, never imported.
`run_baseline.py` and `gateway_client.py` both import boto3, and the hermetic
suite must not pull an AWS SDK into `sys.modules` (G8). This is the same
technique `tests/test_hermeticity.py` uses to scan for imports without running
anything.

Hermetic. Owning seat: AI Quality (comparability) · Platform Engineering.
"""
import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASELINE = ROOT / "services" / "highlights-agent-baseline" / "run_baseline.py"
GOVERNED = ROOT / "services" / "highlights-agent" / "gateway_client.py"


def module_constants(path):
    """Every module-level `NAME = <literal>` assignment, without importing."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node.value.value
    return found


BASELINE_CONSTANTS = module_constants(BASELINE)
GOVERNED_CONSTANTS = module_constants(GOVERNED)


@pytest.mark.parametrize("name", ["SYSTEM", "CLOCK"])
def test_the_governed_run_uses_the_controls_prompt(name):
    """Byte-identical, not merely equivalent.

    If you are here because you changed the prompt: that is allowed, but it ends
    the comparison. Either change both and footnote the progression row that the
    instrument moved again, or leave the control alone — which is almost always
    the right answer, since the control's numbers are recorded against a commit
    and cannot be re-run to match."""
    assert name in BASELINE_CONSTANTS, f"{BASELINE.name} no longer defines {name}"
    assert name in GOVERNED_CONSTANTS, f"{GOVERNED.name} no longer defines {name}"
    assert GOVERNED_CONSTANTS[name] == BASELINE_CONSTANTS[name], (
        f"{name} differs between the control and the governed caller. The M01 golden score "
        "is only comparable to m00b if the gateway is the only difference between the two runs."
    )


def test_the_model_id_is_the_same_pinned_profile():
    """ADR-015. A run against a different profile is a different measurement, and
    the regional pin is a recorded decision rather than an accident."""
    baseline_model = BASELINE_CONSTANTS["MODEL_ID"]
    stack = (ROOT / "platform" / "infra" / "lib" / "gateway-stack.ts").read_text(encoding="utf-8")
    assert f"'{baseline_model}'" in stack, (
        f"the gateway stack does not pin {baseline_model!r} — the M01 run would measure a "
        "different model from the one m00b measured"
    )


def test_transport_decoding_matches_the_control():
    """The fence-unwrapping is `parse` in the control and `parse_answer` here.
    Comparing the function bodies structurally catches a repair being added on one
    side — a retry, a schema coercion, a missing-field fill — which would repair
    the content the goldens measure rather than decode the transport."""
    def body_of(path, name):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                # Docstrings differ by design; the logic must not.
                body = node.body[1:] if ast.get_docstring(node) else node.body
                return ast.dump(ast.Module(body=body, type_ignores=[]))
        raise AssertionError(f"{name} not found in {path.name}")

    assert body_of(GOVERNED, "parse_answer") == body_of(BASELINE, "parse"), (
        "the governed caller decodes the model's reply differently from the control. "
        "Unwrapping a code fence is decoding transport; anything more repairs the answer, "
        "which is the behaviour the golden set is measuring."
    )
