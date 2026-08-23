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

core:
	cd platform/infra && cdk deploy --all

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
