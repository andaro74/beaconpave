"""
M09b's admission test, as far as ADR-077 amendment 1 lets it run before the deploy.

**What this file executes, and what it does not.** ADR-077 decision 3 has seven gates.
Amendment 1 reads gates 1 and 2 before the deploy, because they read no guardrail. It
reads gates 3 to 7 after the deploy, on the pinned guardrail. This file executes
gates 1 and 2 over `milestones/M09b/candidates.json`. It also checks what makes that file a
record: one candidate per topic, its digest pinned here in a later commit than the
record, and every citation it carries found at its lines. **It admits nothing past
gate 2. A green run here is not admission**, and no candidate has been swept against any
guardrail.

**Gate 2's limit, stated.** ADR-024:84-88 presumes a term drawn from a prohibited file
when it appears there *"and nowhere else in the repository"*. That is read at the parent
of the commit that first adds the record, because a document written afterwards quoting
the candidates would otherwise make every term appear elsewhere. A term an earlier
document already quoted from a corpus is not presumed drawn, which is ADR-024's test
as written and weaker than the hazard it names.

Hermetic (G8): committed files and this repository's git objects. Owning seats: AI
Quality · Platform Engineering · Security.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess

import pytest

from tests.test_iam_assertions import GATEWAY_SNAPSHOT, MAX_TOPIC_DEFINITION, load

ROOT = pathlib.Path(__file__).resolve().parents[1]
CANDIDATES = "milestones/M09b/candidates.json"
RECORD = json.loads((ROOT / CANDIDATES).read_text(encoding="utf-8"))

#: The record's digest, pinned in a later commit than the record. Editing a candidate
#: means editing this line too, in a diff that shows both.
SET_SHA256 = "e14ab3546e368e475e5a45235307ee922e82d0cddd835093ad09140825906baf"

#: ADR-024's four prohibited sources, as its amendment names them (:84-88).
ADR_024 = "docs/adr/ADR-024-a-refusal-is-not-an-evasion.md"
ADR_024_FOUR = (
    "quality/adversarial/probes.yaml",
    "services/highlights-agent/evals/golden/cases.yaml",
    "quality/adversarial/phrasings.yaml",
    "quality/adversarial/topic-attacks.yaml",
)
#: The fifth, which postdates ADR-024 and which ADR-076 amendment 2 found no rule names.
DISCLOSURE_SHAPES = "quality/adversarial/disclosure-shapes.yaml"

#: ADR-077 decision 2's axis letters, per topic kind.
AXES = {"recalibration": "ABCDE", "additive": "FGHIJ"}

WORD = re.compile(r"[a-z]+")


def set_digest(candidates: list) -> str:
    return hashlib.sha256(json.dumps(candidates, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def _git(*args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True,
                          input=data).stdout


def at_lines(path: str, first: int, last: int) -> str:
    """The cited lines, each stripped of surrounding space and a leading `>`, joined
    and whitespace-collapsed — the normalisation the record's `_citations` declares."""
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()[first - 1:last]
    return " ".join(" ".join(line.strip().lstrip(">").strip() for line in lines).split())


def words_at(commit: str) -> dict[str, set[str]]:
    """Every tracked text file at `commit`, as its set of lower-cased words."""
    paths = _git("ls-tree", "-r", "--name-only", commit).decode("utf-8").splitlines()
    raw = _git("cat-file", "--batch", data="".join(f"{commit}:{p}\n" for p in paths).encode())
    words, pos = {}, 0
    for path in paths:
        end = raw.index(b"\n", pos)
        size = int(raw[pos:end].split(b" ")[2])
        body = raw[end + 1:end + 1 + size]
        pos = end + 1 + size + 1
        try:
            words[path] = set(WORD.findall(body.decode("utf-8").lower()))
        except UnicodeDecodeError:
            continue
    return words


def presumed_drawn(terms: set[str], words: dict[str, set[str]],
                   prohibited: tuple[str, ...]) -> list[str]:
    """ADR-024:84-88: in a prohibited file, and in no other file."""
    return sorted(t for t in terms
                  if any(t in words.get(p, ()) for p in prohibited)
                  and not any(t in w for p, w in words.items() if p not in prohibited))


def gate_1(candidate: dict, cap: int = MAX_TOPIC_DEFINITION) -> list[str]:
    """ADR-077 decision 3 §1: at most the service's cap, and the recorded count honest."""
    problems = []
    if len(candidate["text"]) > cap:
        problems.append(f"{candidate['topic']}: {len(candidate['text'])} characters, over {cap}")
    if candidate.get("characters") != len(candidate["text"]):
        problems.append(f"{candidate['topic']}: records {candidate.get('characters')} characters "
                        f"and its text has {len(candidate['text'])}")
    return problems


def gate_2(candidate: dict, words: dict[str, set[str]], prohibited: tuple[str, ...]) -> list[str]:
    """ADR-077 decision 2 §3: every presumed-drawn term declared, each with a policy
    justification, and nothing declared that is not presumed drawn."""
    terms = set(WORD.findall(candidate["text"].lower())) | set(WORD.findall(candidate["topic"].lower()))
    computed = presumed_drawn(terms, words, prohibited)
    declared = (candidate.get("prohibited_source_declaration") or {}).get("presumed_drawn")
    if not isinstance(declared, list):
        return [f"{candidate['topic']}: no prohibited-source declaration"]
    problems = []
    names = sorted(entry.get("term") for entry in declared)
    if names != computed:
        problems.append(f"{candidate['topic']}: declares {names}, and ADR-024's test finds {computed}")
    for entry in declared:
        if not str(entry.get("justification") or "").strip():
            problems.append(f"{candidate['topic']}: {entry.get('term')!r} has no justification")
    return problems


@pytest.fixture(scope="module")
def words_at_the_records_parent() -> dict[str, set[str]]:
    added = _git("log", "--diff-filter=A", "--format=%H", "--", CANDIDATES).decode().split()
    assert added, f"{CANDIDATES} has no commit reachable from HEAD; gate 2 reads its parent"
    return words_at(f"{added[-1]}^")


# --- the record ---------------------------------------------------------------

def test_the_record_carries_the_digest_it_was_committed_with():
    assert set_digest(RECORD["candidates"]) == RECORD["set_sha256"] == SET_SHA256


def test_one_candidate_per_topic():
    """ADR-077 amendment 1. Two topics, one candidate each: the recalibration of the
    deployed topic by its own name, and the additive topic."""
    kinds = sorted(c["kind"] for c in RECORD["candidates"])
    assert kinds == ["additive", "recalibration"]
    topics = [c["topic"] for c in RECORD["candidates"]]
    assert len(set(topics)) == len(topics)
    assert next(c for c in RECORD["candidates"]
                if c["kind"] == "recalibration")["topic"] == "entitlement-circumvention"


def test_the_prohibited_sources_are_adr_024s_four_and_the_corpus_that_postdates_it():
    declared = RECORD["prohibited_sources"]
    assert tuple(declared["files"]) == (*ADR_024_FOUR, DISCLOSURE_SHAPES)
    clause = at_lines(ADR_024, 84, 88)
    for path in ADR_024_FOUR:
        if path.startswith("quality/"):
            assert path in clause, f"ADR-024:84-88 no longer names {path}"
    assert "the golden set" in clause
    assert set(declared["added_to_adr_024s_four"]) == {DISCLOSURE_SHAPES}


def _citations():
    for c in RECORD["candidates"]:
        yield f"{c['topic']}:listed_at", c["axis"]["listed_at"]
        yield f"{c['topic']}:licence", c["axis"]["licence"]
        if "subject" in c:
            yield f"{c['topic']}:subject", c["subject"]
    yield "prohibited_sources:rule", RECORD["prohibited_sources"]["rule"]
    for path, ref in RECORD["prohibited_sources"]["added_to_adr_024s_four"].items():
        yield f"prohibited_sources:{path}", ref


@pytest.mark.parametrize("label,ref", list(_citations()), ids=[k for k, _ in _citations()])
def test_every_citation_is_found_at_its_lines(label, ref):
    first, last = ref["lines"]
    assert ref["quote"] in at_lines(ref["path"], first, last), (
        f"{label}: {ref['path']}:{first}-{last} does not say {ref['quote']!r}. An axis that "
        f"cannot be cited to an owning line refuses the candidate (ADR-077 decision 2).")


@pytest.mark.parametrize("candidate", RECORD["candidates"], ids=lambda c: c["topic"])
def test_each_axis_is_one_decision_2_names_for_its_topic(candidate):
    axis = candidate["axis"]
    assert len(axis["id"]) == 1 and axis["id"] in AXES[candidate["kind"]]
    assert axis["listed_at"]["path"].startswith("docs/adr/ADR-077-")
    assert axis["listed_at"]["quote"].startswith(f"| {axis['id']} |")


def test_the_recalibration_changes_the_carve_out_and_not_the_deny_clause():
    """The candidate record's own claim about itself, held: everything before the
    carve-out is byte-identical to the deployed definition in the committed snapshot."""
    deployed = {topic["Name"]: topic["Definition"]
                for resource in load(GATEWAY_SNAPSHOT)["Resources"].values()
                if resource.get("Type") == "AWS::Bedrock::Guardrail"
                for topic in resource["Properties"].get("TopicPolicyConfig", {}).get("TopicsConfig", [])}
    candidate = next(c for c in RECORD["candidates"] if c["kind"] == "recalibration")
    assert candidate["text"].split(" Saying ")[0] == deployed[candidate["topic"]].split(" Saying ")[0]


# --- gate 1 -------------------------------------------------------------------

@pytest.mark.parametrize("candidate", RECORD["candidates"], ids=lambda c: c["topic"])
def test_gate_1_every_candidate_fits_the_service_cap(candidate):
    assert MAX_TOPIC_DEFINITION == 200
    assert gate_1(candidate) == []


def test_gate_1_refuses_a_candidate_at_201_characters():
    """The seat plant SPEC/09b names."""
    assert gate_1({"topic": "t", "text": "x" * 201, "characters": 201})
    assert gate_1({"topic": "t", "text": "x" * 200, "characters": 200}) == []


def test_gate_1_refuses_a_recorded_count_that_is_not_the_texts():
    assert gate_1({"topic": "t", "text": "x" * 150, "characters": 149})


# --- gate 2 -------------------------------------------------------------------

@pytest.mark.parametrize("candidate", RECORD["candidates"], ids=lambda c: c["topic"])
def test_gate_2_every_declaration_is_what_adr_024s_test_finds(candidate, words_at_the_records_parent):
    prohibited = tuple(RECORD["prohibited_sources"]["files"])
    assert gate_2(candidate, words_at_the_records_parent, prohibited) == []


def test_gate_2_reads_a_tree_that_holds_the_prohibited_files(words_at_the_records_parent):
    """Anti-vacuity: a parent missing the corpora finds no term drawn from any of them."""
    for path in (*ADR_024_FOUR, DISCLOSURE_SHAPES):
        assert words_at_the_records_parent.get(path), f"{path} is not in the tree gate 2 reads"


def test_gate_2_reads_a_tree_from_before_the_record(words_at_the_records_parent):
    """Anti-vacuity, the other way. Read at a tree holding the record, every
    candidate term appears in the record itself, so every term appears "elsewhere"
    and nothing can be presumed drawn."""
    assert CANDIDATES not in words_at_the_records_parent, (
        "gate 2 is reading a tree that already holds the candidate record")


WORDS = {"quality/adversarial/phrasings.yaml": {"vpn", "watch", "regional"},
         "README.md": {"watch"}}
PROHIBITED = ("quality/adversarial/phrasings.yaml",)


def test_gate_2_refuses_an_undeclared_presumed_drawn_term():
    """`gateway-stack.ts:292-298`'s real draft, reaching for `PHR-002`'s noun."""
    candidate = {"topic": "t", "text": "Giving a VPN to watch it.",
                 "prohibited_source_declaration": {"presumed_drawn": []}}
    assert presumed_drawn({"vpn", "watch"}, WORDS, PROHIBITED) == ["vpn"]
    assert gate_2(candidate, WORDS, PROHIBITED)


def test_gate_2_refuses_a_declared_term_with_no_justification():
    """The seat plant SPEC/09b names."""
    candidate = {"topic": "t", "text": "Giving a VPN to watch it.",
                 "prohibited_source_declaration": {"presumed_drawn": [{"term": "vpn",
                                                                       "justification": " "}]}}
    assert gate_2(candidate, WORDS, PROHIBITED)
    candidate["prohibited_source_declaration"]["presumed_drawn"][0]["justification"] = "policy"
    assert gate_2(candidate, WORDS, PROHIBITED) == []


def test_gate_2_refuses_a_declaration_of_a_term_that_is_not_presumed_drawn():
    candidate = {"topic": "t", "text": "Giving a way to watch it.",
                 "prohibited_source_declaration": {"presumed_drawn": [{"term": "watch",
                                                                       "justification": "x"}]}}
    assert gate_2(candidate, WORDS, PROHIBITED)


def test_gate_2_refuses_a_candidate_with_no_declaration():
    assert gate_2({"topic": "t", "text": "x"}, WORDS, PROHIBITED)


def test_gate_2_reads_the_topic_name_as_well_as_the_text():
    candidate = {"topic": "regional-feed", "text": "Giving a way.",
                 "prohibited_source_declaration": {"presumed_drawn": []}}
    assert gate_2(candidate, WORDS, PROHIBITED)
