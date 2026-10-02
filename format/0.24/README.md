# Candidate 0.24: first valid contribution and rolling invitations

**Status:** isolated local pre-1 candidate from completed 0.23 `ba0530038747f5ed0ee5570d232e2ec72db64a40`, implemented for validation and independent review. No merge, publication, deployment or 1.0 decision.

Authors can invite two people from a saved shuffled queue, accept the first finished valid text/image/audio contribution atomically, preserve the losing person's next opportunity and move on with a fresh shared deadline. If both expire, rotate them against unchanged canonical material. Full failed passes stop with a declared retry delay. The host launches bounded successor instances and delivers invitations.

- [Exact relay contract](relay-notes.md), [schema](package.schema.json), [operation catalog](operations.md), [authoring](authoring.md)
- Independent [Python](relay.py)/[JavaScript](relay.mjs) relay modules, retained independent runtimes
- [Creative relay start](examples/creative-relay-start.json), [continuation](examples/creative-relay-continue.json), [empty retry](examples/creative-relay-retry-empty.json)
- [Different private-pair reflection composition](examples/relay-paired-reflection.json)
- [Design checkpoint](DESIGN-CHECKPOINT.md), [decisions](DECISIONS.md), [supported profile](readiness-assessment.md)
- [Host review packet](HOST-REVIEW.md), [short review summary](HOST-REVIEW-SUMMARY.md), [conformance](conformance/README.md), [validation evidence](../../validation/0.24/EVIDENCE.md)
- [User-facing rules](CREATIVE-RELAY-RULES.md), [compatibility](COMPATIBILITY.md), [migration accounting](MIGRATION.md)

```sh
PYTHONDONTWRITEBYTECODE=1 python3 format/0.24/relay_check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 format/0.24/check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 format/0.24/compatibility_check.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.24/relay_trial.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.24/run.py
```

JSON Schema validation needs the optional pinned dependency in requirements-validation.txt; neither runtime depends on it. Hosts use Python 3 and Node with `node:sqlite`. The inspector remains pinned to retained 0.20. Historical operation semantics and files are preserved. Carry-over preserves opportunities rather than guaranteeing wins; an inactive invitee may remain while others contribute quickly. Notification delivery, accounts, calendars, media processing and long-running product lifecycle remain host work.
