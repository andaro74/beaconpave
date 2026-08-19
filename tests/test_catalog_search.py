"""
L1 tests for catalog-search — the tool that ends the control's prompt shape.

Three properties carry weight here, and the rest of the file exists to stop each
of them being reached around.

**It cannot serve the blackout table.** That is not a behaviour to be checked on
the paths we thought of; it is checked as a projection onto an allowlist, so a
field added to the fixture is invisible until somebody adds it here and to the
schema.

**It is deterministic.** Two runs of the golden set must differ by the model's
sampling and nothing else. A tool whose row order moved would put a second
non-deterministic component inside a measurement built to isolate one.

**A degenerate query returns nothing.** The input schema says it "deliberately
cannot express 'give me everything'", and the query most likely to be degenerate
is the one a model sends when it does not know what to ask for.

Hermetic (G8). Owning seat: Tool Owner.
"""
import json
import pathlib

import jsonschema
import pytest
from search import DEFAULT_LIMIT, MAX_LIMIT, load_catalog, search

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "catalog-search"
CATALOG = load_catalog(ROOT / "data" / "catalog.json")
POISONED = load_catalog(ROOT / "data" / "catalog_poisoned.json")
OUT_SCHEMA = json.loads((TOOL / "schema.out.json").read_text(encoding="utf-8"))
IN_SCHEMA = json.loads((TOOL / "schema.in.json").read_text(encoding="utf-8"))

#: Queries spanning what the golden set actually asks. Used to check the contract
#: holds across the corpus rather than on one happy path.
QUERIES = [
    {"query": "derby"},
    {"query": "rowing finals"},
    {"query": "granite falls classic replay"},
    {"query": "sports live event"},
    {"query": "harbor bay invitational"},
    {"query": "nightly news", "brand": "meridian-news"},
    {"query": "derby", "type": "live-event", "limit": 1},
]


@pytest.mark.parametrize("args", QUERIES, ids=lambda a: a["query"][:20])
def test_every_result_conforms_to_the_committed_output_schema(args):
    jsonschema.validate(search(args, CATALOG), OUT_SCHEMA)


@pytest.mark.parametrize("args", QUERIES, ids=lambda a: a["query"][:20])
def test_every_query_the_tests_use_is_a_legal_input(args):
    """The fixtures must exercise the contract, not a superset of it. A test
    querying something the input schema forbids would prove the tool handles
    requests the tool plane will reject before they arrive."""
    jsonschema.validate(args, IN_SCHEMA)


# --- it cannot serve the blackout table ---------------------------------------

def test_no_result_can_carry_blackout_or_market_data():
    """The load-bearing one. `data/catalog.json` holds `blackouts` and `dmas`
    beside `titles`, and entitlement geography is entitlement-check's at M06.

    Checked as a projection rather than as a behaviour: `_row` allowlists fields,
    so this fails the moment a field starts reaching the model, including one
    nobody thought to write a case for."""
    allowed = set(OUT_SCHEMA["properties"]["results"]["items"]["properties"])
    for args in QUERIES:
        for row in search(args, CATALOG)["results"]:
            assert set(row) <= allowed, f"{args}: row carries {sorted(set(row) - allowed)}"
            assert "blackout" not in json.dumps(row).lower()
            assert "dma" not in json.dumps(row).lower()


def test_the_fixture_really_does_contain_what_the_tool_must_not_serve():
    """The positive control for the test above. Without it, that test would pass
    just as happily against a fixture with no blackout table in it — proving the
    fixture rather than the projection (PR #13's lesson)."""
    assert CATALOG["blackouts"], "the fixture no longer carries a blackout table"
    assert CATALOG["dmas"]


def test_a_field_added_to_the_fixture_does_not_reach_the_model():
    """The mechanism behind the projection, exercised directly. A catalog that
    grows a field — a licensing note, an internal flag, a blackout list per
    title — must not start feeding it to a model because the schema happened not
    to forbid it yet."""
    grown = {"titles": [dict(t, blackout_dmas=["jefferson-city"], internal_note="x")
                        for t in CATALOG["titles"]]}
    rows = search({"query": "derby"}, grown)["results"]
    assert rows
    for row in rows:
        assert "blackout_dmas" not in row
        assert "internal_note" not in row
    jsonschema.validate({"results": rows}, OUT_SCHEMA)


# --- it cannot express "give me everything" -----------------------------------

def test_a_query_with_no_usable_terms_returns_nothing_rather_than_everything():
    """The input schema's stated design: an unbounded query is how the whole
    catalog ends up back in the model's context, which is the failure mode M02
    exists to remove.

    Returning everything here would be the quiet version of that, on exactly the
    request a model sends when it has no idea what to ask for."""
    for query in ["", "  ", "on", "a b c"]:
        assert search({"query": query}, CATALOG)["results"] == []


def test_the_limit_is_honoured_and_capped():
    """The query names titles rather than leaning on the brand prefix, which is no
    longer free text — see `test_the_brand_name_is_not_a_wildcard`."""
    broad = "derby report nightly classic rowing"
    assert len(search({"query": broad, "limit": 2}, CATALOG)["results"]) == 2
    everything = search({"query": broad, "limit": MAX_LIMIT * 5}, CATALOG)["results"]
    assert len(everything) <= MAX_LIMIT
    assert len(everything) <= len(CATALOG["titles"])


def test_the_default_limit_applies_when_none_is_given():
    assert len(search({"query": "meridian"}, CATALOG)["results"]) <= DEFAULT_LIMIT


# --- determinism ---------------------------------------------------------------

def test_identical_arguments_return_identical_rows_in_identical_order():
    """Two runs of the golden set must differ by the model's sampling and nothing
    else. A tool whose ordering moved would add a second non-deterministic
    component to a measurement built to isolate one — and it would look like
    model variance in the paired diff."""
    for args in QUERIES:
        first = search(args, CATALOG)
        assert all(search(args, CATALOG) == first for _ in range(5))


def test_ranking_prefers_more_matching_terms_and_then_catalog_order():
    """Stated as a property rather than as an expected list, so the test does not
    have to be rewritten every time the fixture gains a title."""
    rows = search({"query": "jefferson derby rovers", "limit": MAX_LIMIT}, CATALOG)["results"]
    assert rows[0]["id"] == "t001"


# --- discovery behaviour the golden set depends on ------------------------------

def test_a_title_that_does_not_exist_returns_no_rows():
    """`grounded-019` and `entitlement-012` ask about the Harbor Bay Invitational,
    which is not in the catalog. The groundedness trap only works if the tool says
    so by returning nothing — a tool that fuzzy-matched to the nearest real title
    would hand the model a confabulation to cite."""
    assert search({"query": "harbor bay invitational"}, CATALOG)["results"] == []


def test_filters_narrow_rather_than_reorder():
    """Note the query. `"meridian"` served as the everything-query here, and it
    worked because `brand` was searchable free text — which is what made the input
    schema's "cannot express give me everything" claim false. Both are fixed, and
    the filters do the narrowing, which is what they are for."""
    args = {"query": "report nightly derby", "limit": MAX_LIMIT}
    unfiltered = {r["id"] for r in search(args, CATALOG)["results"]}
    news = {r["id"] for r in search(dict(args, brand="meridian-news"), CATALOG)["results"]}
    assert news < unfiltered
    assert all(r["brand"] == "meridian-news"
               for r in search(dict(args, brand="meridian-news"), CATALOG)["results"])


def test_the_brand_name_is_not_a_wildcard():
    """The claim in `schema.in.json` is the text the model reads when deciding how
    to call this tool, and it was false: `brand` and `type` were searchable free
    text, so `"meridian"` returned all five titles and `"live"` returned three. A
    contract statement that is not true is worse than a narrow tool."""
    for wildcard in ["meridian", "live", "vod", "meridian-sports"]:
        rows = search({"query": wildcard, "limit": MAX_LIMIT}, CATALOG)["results"]
        # `== []`, not `< len(titles)`. The looser form left four-fifths of a
        # five-title catalog as slack, so a regression restoring `brand` to the
        # searchable fields would have passed it on any fixture with six titles.
        # This test stands in for a claim in model-facing contract text; it should
        # assert what was measured.
        assert rows == [], f"{wildcard!r} is searchable free text again"


def test_a_stopword_is_not_a_search_term():
    """`MIN_TERM_LENGTH` was 3 with `>=`, which kept "the" — and the constant's own
    worked example was the counterexample: "is the derby on" matched *The Port
    William Report*, which has nothing to do with the derby, on a stopword."""
    assert [r["id"] for r in search({"query": "is the derby on"}, CATALOG)["results"]] == ["t001"]
    assert search({"query": "the"}, CATALOG)["results"] == []


@pytest.mark.parametrize("limit,expected", [(-1, 1), (0, 1), (1, 1), (99, 5), ("abc", 5), (None, 5)])
def test_the_limit_is_total_and_clamped_at_both_ends(limit, expected):
    """`min(int(limit), MAX_LIMIT)` had no lower bound, so `limit: -1` became a
    negative slice — dropping the last row rather than refusing. It was unreachable
    only because the plane happened to be in front, and a tool that is correct only
    because of what sits ahead of it is a tool with a bug."""
    query = "derby report nightly classic rowing"
    rows = search({"query": query, "limit": limit}, CATALOG)["results"]
    assert len(rows) == expected


def test_the_limit_constants_agree_with_the_committed_schema():
    """Three copies of the same two numbers — here, `schema.in.json`, and
    `schema.out.json`'s `maxItems`. Raising one alone would produce results the
    tool plane then denies at run time: a SCHEMA refusal on a call nothing
    rejected."""
    assert IN_SCHEMA["properties"]["limit"]["default"] == DEFAULT_LIMIT
    assert IN_SCHEMA["properties"]["limit"]["maximum"] == MAX_LIMIT
    assert OUT_SCHEMA["properties"]["results"]["maxItems"] == MAX_LIMIT


# --- the adversarial fixture ----------------------------------------------------

def test_the_poisoned_catalog_is_served_verbatim_and_not_sanitised():
    """ADV-002's fixture, and the tool must not quietly defuse it.

    The injected instruction rides in a title field. Stripping it here would make
    the probe unmeasurable while looking like a security improvement — the tool
    would be repairing data on the model's behalf, and the open path would stop
    being visible without stopping being open. Whether anything assesses tool
    output is the tool plane's question and SPEC/02 defers it to M04, on the
    record, with this observation committed as the evidence."""
    rows = search({"query": "lake adair open"}, POISONED)["results"]
    assert rows, "the poisoned fixture no longer matches — ADV-002 would go untested"
    assert "SYSTEM NOTE" in rows[0]["title"]
    jsonschema.validate({"results": rows}, OUT_SCHEMA)
