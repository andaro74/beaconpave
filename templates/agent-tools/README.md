# agent-tools — the template `pave new` renders

Five files, and the list is in `pave/scaffold.py`'s `RENDERED`. Every one is a
`.tmpl`: two of them were specified as rendered *verbatim* and both carried the
reference service's identity — the answer schema's `$id` (two scaffolded services
would collide on the field a JSON-Schema resolver keys on) and the golden README's
heading.

```
python -m pave.cli new <service> [--brand meridian-sports] [--team T] [--oncall O]
```

## What this directory is a copy OF

`services/highlights-agent/`. A template is a copy, and a copy of a living file is
wrong the moment the original moves — so `tests/test_scaffold.py` compares every
one of the five against the service it was cut from. Two round-trip **byte
identically**: render the template with the reference service's own values and you
get the reference file back. Change either side and that test is red.

Nothing compared these two trees before ADR-047, because this directory held one
README. A template could have drifted for four milestones unnoticed.

## What it deliberately does not render

**No `run_probes*.py`.** That path is on a `(security, platform-eng)` rule, so
emitting one would hand every team a file it could never edit alone. Per-service
adversarial lanes arrive at M08.

**No `gate.yml`, no CODEOWNERS entry.** M05 builds no per-service lane, and
ADR-013 records that CODEOWNERS collects nothing on a one-operator repository.
Writing to `.github/CODEOWNERS` would also contradict creates-only.

**Nine of the reference service's fourteen files.** They are M01–M04 measurement
harnesses (`inspect_context.py`, `run_judge.py`, `run_phrasings.py`, `run_split.py`,
`run_via_gateway.py`, `run_with_tools.py`, `topic_baseline.py`,
`verify_guardrail_pin.py`, and the probe runner above). A new service needs none of
them.

## The scaffold does not pass its own gate

`pave verify <service>` refuses a fresh scaffold with exactly two findings, and each
one is a step `pave new` may not take: the registry grant, and twenty golden cases
nobody has written. That is by design — see ADR-047.

**Owning seats:** Platform Engineering, AI Quality, Tool Owner, Security. Four keys,
because a template edit sets the default tool set, case floor, headroom expectation
and wire text for every service that does not exist yet, and none of those services
can review the diff.
