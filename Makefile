# Beaconpave developer entrypoints.
# `make check` is hermetic (G8): unit + contract + rules validation.
# No AWS account, no network, no excuses.

.PHONY: check bootstrap core evals adversarial drill up down clean

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

evals:
	python -m evals.run_evals --answers $(ANSWERS) --record

adversarial:
	python evals/run_adversarial.py --record

drill:
	python -m pave.cli drill --event jefferson-derby --tier 3

up:
	@echo "(ephemeral demo resources — nothing bills while idle, G10)"

down:
	cd platform/infra && cdk destroy --all

clean:
	rm -f verdict-*.json
