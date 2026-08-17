"""
The gateway's pure half: classify -> decide -> meter -> build the audit record.

**Nothing in this package imports an SDK**, and `tests/test_hermeticity.py` scans
it to keep that true. The split is the same one `evals/` already makes and for
the same reason: the decisions that G1, G4, and G5 rest on are provable against
committed fixtures, offline, on a fresh clone, before anything reaches AWS.

`platform/gateway/handler.py` is the other half — boto3, Bedrock, S3 — and is
deliberately outside the hermetic surface, exactly as the M00b control is.

Owning seat: Platform Engineering (pipeline) · Data Governance (classification)
· Security (guardrail interpretation).
"""
