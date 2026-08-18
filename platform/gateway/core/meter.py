"""
The meter: what a call spent, in the denomination the budgets are written in.

ADR-014 fixed budgets in tokens and moved dollars to report time, because a
dollar ceiling tracks a price list that moves without a commit — two runs would
score differently with no code change between them. So this module records
tokens and **refuses to store a currency figure at all**, rather than storing one
and trusting every future reader not to compare it.

Owning seat: Platform Engineering (meter) · AI Quality (budgets, two-key).
"""
from __future__ import annotations

#: Rejected outright rather than dropped, so an attempt to widen the record
#: surfaces in a test rather than in a dashboard six milestones later.
CURRENCY_MARKERS = ("usd", "cost", "price", "dollar", "cents")


def usage_from_response(response: dict, latency_ms: int) -> dict:
    """Extract the token counts a Bedrock `converse` response reports.

    Raises when usage is absent. A call that reached the model but reported no
    usage is a metering failure, and defaulting it to zero would quietly credit
    the service with a free request — the budget axis would then pass for the one
    call it should most want to see."""
    usage = response.get("usage")
    if not usage:
        raise ValueError("response carries no usage — a metered call must report what it spent")
    return {
        "tokens_in": usage["inputTokens"],
        "tokens_out": usage["outputTokens"],
        "latency_ms": latency_ms,
    }


def assert_token_denominated(usage: dict) -> dict:
    """Reject a usage object carrying money (ADR-014).

    The mirror of `test_no_budget_is_denominated_in_currency` on the golden set:
    that test guards what the budgets *ask for*, this guards what the platform
    *records*. Both are needed, because a currency field could arrive from either
    end and would look plausible from either."""
    priced = sorted(k for k in usage if any(marker in k.lower() for marker in CURRENCY_MARKERS))
    if priced:
        raise ValueError(
            f"usage carries currency field(s) {priced}. Budgets are token-denominated; "
            "dollars are rendered at report time and never stored (ADR-014)."
        )
    return usage
