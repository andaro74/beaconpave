# Beaconpave developer entrypoints.
# `make check` is hermetic (G8): unit + contract + rules validation.
# No AWS account, no network, no excuses.

.PHONY: check bootstrap core evals adversarial drill up down clean snapshot snapshot-check

# One implementation, in `pave check`. The Makefile used to inline the steps and
# swallow pytest's exit code with `|| echo`, which reported green over zero tests
# for the repo's entire life so far. It also used POSIX-only shell, so it could
# not run on the machine this is developed on.
check:
	python -m pave.cli check

bootstrap:
	pip install -e .
	cd platform/infra && npm install && cdk bootstrap

# **One recipe line, and the `&&` is the guard.** Measured here on GNU Make 4.3
# rather than quoted: with two recipe lines, `make -i core` prints the gate's
# failure and runs the deploy anyway (`DEPLOY-RAN`, exit 0); with `&&` on one line
# the deploy never runs. Under plain `make` the target exits 2 and stops.
#
# **The gate runs BEFORE the `cd`, which is where SPEC/05 put it and it was wrong.**
# The spec's literal is `cd platform/infra && python -m pave.cli verify --all && cdk
# deploy --all`, justified on the `pave` console script existing only after `pip
# install -e .`. Measured, that justification does not hold: from `platform/infra`
# **neither** form works without the install -- `python -m pave.cli` there is
# `ModuleNotFoundError: No module named 'pave'`, exit 1 -- and after `make bootstrap`
# **both** do. So the spec's ordering buys nothing and costs the one case that
# matters: on a tree that has not been bootstrapped it refuses with an import error
# dressed as a gate refusal, which is a silent success's mirror image and just as
# unreadable. Run from the root, the verifier resolves with no install at all
# (exit 0, PASS highlights-agent) and the `&&` still blocks the deploy.
#
# **What this is NOT.** It does not make `attestations.manifest_signature` true.
# Nothing verifies a manifest at deploy; ADR-046 decision 4 records that as a stated
# cut. This is a control on the repository, not on the runtime, and selling it as
# the other thing is the claim ADR-046 exists to refuse. Note also that under
# `make -i` this target exits **0** having run neither the gate nor the deploy: an
# unsupported invocation whose exit code means nothing, written down because a
# silent success is the `|| echo` shape this file's own header records the
# repository shipping for its entire life.
core:
	python -m pave.cli verify --all && cd platform/infra && cdk deploy --all

# The G1 assertions read a committed snapshot so `make check` stays hermetic
# (ADR-017). Re-record it whenever the CDK app changes; `snapshot-check` is what
# CI runs, and it blocks on drift — a stale snapshot asserts against
# infrastructure that no longer exists.
snapshot:
	cd platform/infra && npx cdk synth --quiet
	python -m pave.cli infra snapshot

snapshot-check:
	cd platform/infra && npx cdk synth --quiet
	python -m pave.cli infra snapshot --check

evals:
	python -m evals.run_evals --answers $(ANSWERS) --record

adversarial:
	@test -n "$(OBSERVATIONS)" || { echo "set OBSERVATIONS=milestones/MNN/probes-run.json -- a default would record a second row over another milestone's evidence"; exit 2; }
	python -m evals.run_adversarial --observations $(OBSERVATIONS) --record

drill:
	python -m pave.cli drill --event jefferson-derby --tier 3

up:
	@echo "(ephemeral demo resources — nothing bills while idle, G10)"

down:
	cd platform/infra && cdk destroy --all

clean:
	rm -f verdict-*.json
