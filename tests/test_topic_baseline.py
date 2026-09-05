"""The output-side producer's arm table, asserted without importing it.

**Why this file exists.** `services/highlights-agent/topic_baseline.py` produced
every output-side measurement in M06b — three corpora, three derived artifacts,
three ADRs — and the seat round found it had **no test of any kind**. Platform
Engineering planted, and all four were green against the full suite:

- `--output-attacks` re-wired to `source="INPUT"` and `CHANNEL_QUESTION`, so an
  arm whose corpus exists to be scored on the OUTPUT channel would have been
  scored on the other one, under a correct-looking name;
- `--refusal-shapes` reading the decomposition corpus;
- an arm dropped from the expectation lookup, silently scoring nothing;
- an arm added to the summary list and not to the lookup, printing
  **"17/17 met their expectation"** having compared nothing, because `met` absent
  defaulted to a pass.

None of that is currently true of the file. **Nothing held it there**, which is
the whole argument: `test_the_probes_yaml_arm_still_offers_no_tools` parses a
producer with `ast` for exactly this reason and `test_handler_wiring.py` does it
for `handler.py`, and neither technique was applied to the producer the milestone
grew from three arms to six.

**Parse, do not import** (G8): the module holds boto3 clients at call time and
importing it would put credentials inside `make check`. `ast` reads it as text.

What this proves and what it does not: it proves the file *says* the right things
— that each arm names the channel its own corpus declares, and that every arm with
expectations is wired to supply them. It cannot prove a run behaves; only a run
can. That is the same trade `test_handler_wiring.py` states about itself.

Hermetic (G8): reads source and committed YAML, imports nothing under test.
Owning seat: Security (the corpora and what a verdict on them means) · Platform
Engineering (the producer).
"""
from __future__ import annotations

import ast
import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "services" / "highlights-agent" / "topic_baseline.py"
CORPORA = ROOT / "quality" / "adversarial"

#: Arm name -> the corpus file whose rows it scores, for the arms that read one.
#:
#: `questions`, `answers`, `probes` and `controls` are deliberately absent: they
#: are built from the golden cases, a committed run, and two corpora that declare
#: no `source` of their own. The arms that a corpus file declares a channel for
#: are the ones a channel can be checked against.
ARM_CORPORA = {
    "attacks": "topic-attacks.yaml",
    "heldout": "topic-attacks-heldout.yaml",
    "output-attacks": "topic-attacks-output.yaml",
    "refusal-shapes": "refusal-shapes.yaml",
    "decomposition": "answer-decomposition.yaml",
}

#: Arm name -> the function that supplies its rows.
#:
#: **This is which corpus the arm actually reads**, and it was the gap that let a
#: plant swap `--refusal-shapes` onto the decomposition corpus with the channel,
#: the source and the arm's recorded name all still correct. A name checked
#: against a channel says nothing about the text underneath it.
ARM_READERS = {
    "questions": "questions", "answers": "answers", "attacks": "attacks",
    "heldout": "heldout", "probes": "probes", "controls": "controls",
    "output-attacks": "output_attacks", "refusal-shapes": "refusal_shapes",
    "decomposition": "decomposition",
}

#: The arms whose corpora declare `expect` on their rows, so a verdict on them is
#: comparable to something. Pinned as a closed set: an arm that scores
#: expectations and is missing from `EXPECTATION_SOURCES` scores them against
#: nothing, and an arm listed there with no expectations to supply fails its own
#: coverage check at runtime.
ARMS_WITH_EXPECTATIONS = frozenset({
    "heldout", "controls", "output-attacks", "refusal-shapes", "decomposition",
})


@pytest.fixture(scope="module")
def tree() -> ast.Module:
    return ast.parse(PRODUCER.read_text(encoding="utf-8"))


def _arm_tuples(tree: ast.Module) -> dict:
    """Every `arms.append((name, source, ..., channel))` in the file.

    Located by the call rather than by a constant, because the file appends them
    one `if` at a time and a table would be a second place for them to live."""
    found = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "append"
                and getattr(node.func.value, "id", None) == "arms"):
            continue
        (tup,) = node.args
        assert isinstance(tup, ast.Tuple) and len(tup.elts) == 4, (
            "an arm is appended as something other than a 4-tuple; this file reads "
            "(name, source, items, channel) and cannot check a different shape.")
        name, source, reader, channel = tup.elts
        assert isinstance(name, ast.Constant) and isinstance(source, ast.Constant), (
            "an arm's name or source is not a literal. Both are recorded into the "
            "committed artifact, and a computed one cannot be read here or by anyone "
            "auditing what an arm measured.")
        assert isinstance(channel, ast.Attribute), (
            f"arm {name.value!r} passes a channel that is not a `guardrail.CHANNEL_*` "
            "constant. Two spellings of one channel is how 'the guardrail never saw it' "
            "gets misread as 'the guardrail allowed it'.")
        assert isinstance(reader, ast.Call) and isinstance(reader.func, ast.Name), (
            f"arm {name.value!r} is built by something other than a plain call to its "
            "reader. The reader is which corpus the arm actually scores, and an "
            "expression here cannot be checked against the name the arm records.")
        found[name.value] = (source.value, reader.func.id, channel.attr)
    return found


def _expectation_source_keys(tree: ast.Module) -> set:
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign)
                and any(getattr(t, "id", None) == "EXPECTATION_SOURCES" for t in node.targets)):
            assert isinstance(node.value, ast.Dict), "EXPECTATION_SOURCES is not a dict literal"
            return {k.value for k in node.value.keys if isinstance(k, ast.Constant)}
    raise AssertionError(
        "EXPECTATION_SOURCES is gone. It replaced a four-branch `if arm == ...` chain and "
        "a second, independent tuple of the same names; splitting them again is the "
        "divergence that printed a clean sheet for an arm that compared nothing.")


def test_every_arm_is_still_declared_with_a_literal_name_source_and_channel(tree):
    arms = _arm_tuples(tree)
    assert len(arms) >= 9, (
        f"only {len(arms)} arms found. This file had six at M06b's close and the reader "
        "locates them by the `arms.append` call; if they moved, move this with them.")


def test_every_arm_reads_the_corpus_its_name_says_it_reads(tree):
    """The plant: `--refusal-shapes` built from `decomposition()`, green.

    Source, channel and the recorded arm name were all still correct — only the
    text underneath changed. An artifact would then carry one corpus's rows under
    another corpus's name, and every derived reading of it would be about a file
    it never touched."""
    arms = _arm_tuples(tree)
    readers = {name: reader for name, (_, reader, _) in arms.items()}
    assert readers == ARM_READERS, (
        f"the arms read {readers}; pinned as {ARM_READERS}. An arm built from another "
        "arm's reader records one corpus's rows under a different corpus's name.")


@pytest.mark.parametrize("arm", sorted(ARM_CORPORA))
def test_each_arm_is_scored_on_the_channel_its_own_corpus_declares(arm):
    """The plant: `--output-attacks` re-wired to INPUT/question, green.

    A corpus that says `source: OUTPUT` in its own header and is scored at INPUT
    produces a number about a channel nobody asked about, recorded under the
    arm's correct-looking name. The corpus is the authority here — it is frozen,
    Security-owned, and it is the thing the run claims to measure."""
    tree_arms = _arm_tuples(ast.parse(PRODUCER.read_text(encoding="utf-8")))
    assert arm in tree_arms, f"the {arm!r} arm is gone from the producer"
    source, _reader, channel = tree_arms[arm]

    corpus = yaml.safe_load((CORPORA / ARM_CORPORA[arm]).read_text(encoding="utf-8"))
    declared = corpus.get("source", "INPUT")
    assert source == declared, (
        f"the {arm!r} arm scores at source={source!r} while "
        f"{ARM_CORPORA[arm]} declares source={declared!r}.")
    expected_channel = "CHANNEL_ANSWER" if declared == "OUTPUT" else "CHANNEL_QUESTION"
    assert channel == expected_channel, (
        f"the {arm!r} arm records channel={channel} for source={declared}. The channel a "
        "record names must be the channel the text actually travels on (ADR-040).")


def test_the_arms_that_score_expectations_are_exactly_the_ones_wired_to_supply_them(tree):
    """Both directions, because each is a different failure.

    An arm scoring expectations and absent from `EXPECTATION_SOURCES` drops its
    corpus's expectations on the floor and prints the blocked/unstable summary as
    though it never had any. An arm present there with no expectations to supply
    fails its own coverage check at runtime and returns 2 — noisy, but only
    because that check exists."""
    keys = _expectation_source_keys(tree)
    assert keys == set(ARMS_WITH_EXPECTATIONS), (
        f"EXPECTATION_SOURCES covers {sorted(keys)}; the arms whose corpora carry "
        f"expectations are {sorted(ARMS_WITH_EXPECTATIONS)}. An arm on one side and not "
        "the other is the fall-through the seat round measured printing '17/17 met their "
        "expectation' after comparing nothing.")
    assert keys <= set(_arm_tuples(tree)), (
        f"EXPECTATION_SOURCES names arms that do not exist: {sorted(keys - set(_arm_tuples(tree)))}")


@pytest.mark.parametrize("arm", sorted(ARMS_WITH_EXPECTATIONS & set(ARM_CORPORA)))
def test_an_arm_that_scores_expectations_has_a_corpus_that_carries_them(arm):
    """The pin above is a list of names; this is what makes it mean something.

    Without it, `ARMS_WITH_EXPECTATIONS` and `EXPECTATION_SOURCES` could agree
    with each other while both had drifted away from the corpora."""
    corpus = yaml.safe_load((CORPORA / ARM_CORPORA[arm]).read_text(encoding="utf-8"))
    texts = str(corpus)
    assert "'expect'" in texts or '"expect"' in texts or "expect:" in texts, (
        f"{ARM_CORPORA[arm]} no longer carries expectations, but {arm!r} is listed as an "
        "arm that scores them.")


def test_a_missing_expectation_is_not_reported_as_met(tree):
    """`met` absent must be a MISS.

    It defaulted to True, so a row nothing compared was counted as having met an
    expectation it was never given — a fall-through that prints a clean sheet
    rather than printing nothing, which is the worse of the two directions.

    **Read by AST, not by substring.** The first version of this assertion
    searched the source text for `r.get("met", True)` and went red on the comment
    explaining why that default was wrong — the "guard coupled to its own data"
    failure the same seat round found in `test_option_e_is_not_deployed_by_this_evidence`.
    A prose sentence about a defect must not be indistinguishable from the defect."""
    defaults = [call.args[1] for call in ast.walk(tree)
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                and call.func.attr == "get" and len(call.args) == 2
                and isinstance(call.args[0], ast.Constant) and call.args[0].value == "met"]
    assert defaults, (
        "nothing reads `met` with a default any more. The missed-row summary counts rows "
        "that did not meet their expectation, and how an ABSENT `met` is counted is the "
        "whole question.")
    for default in defaults:
        assert isinstance(default, ast.Constant) and default.value is False, (
            "a `met` lookup defaults to something other than False. A row with no "
            "expectation must be a miss: defaulting it to a pass is how an arm that "
            "compared nothing printed '17/17 met their expectation'.")


def test_the_arm_coverage_check_is_still_in_the_path_and_fails_closed(tree):
    """An arm that declares expectations must supply one for every row it scores.

    Scoring the rows that happen to have an expectation and printing the total is
    the survivor-versus-population error this repository has made three times, and
    G2 says an errored control blocks rather than skips.

    **Read as a branch, not as a string.** The first version asserted the error
    text was present and that `main` returned 2 somewhere; disabling the branch
    with `if False and missing:` satisfied both. A guard is what runs, not what
    the file says."""
    (main_fn,) = [n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "main"]
    guards = [n for n in ast.walk(main_fn)
              if isinstance(n, ast.If) and isinstance(n.test, ast.Name)
              and n.test.id == "missing"]
    assert guards, (
        "the arm-coverage branch is gone or is no longer a plain `if missing:`. An arm "
        "declaring expectations that cannot supply one per row would score the remainder "
        "and print the total as though it were the whole.")
    for guard in guards:
        returns = [n for n in ast.walk(guard)
                   if isinstance(n, ast.Return) and isinstance(n.value, ast.Constant)]
        assert any(r.value.value == 2 for r in returns), (
            "the arm-coverage branch no longer returns non-zero. A producer that reports "
            "a partial count as a whole one is the control failing open (G2).")
