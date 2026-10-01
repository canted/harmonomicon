# Candidate 0.21: votes, outcomes and linked rounds

**Status:** local incremental pre-1 candidate from [0.20](../0.20/README.md). No release, deployment or 1.0 decision.

Authors can collect typed contributions, vote on their stable identities, allow vote changes with one setting, compute exact totals without revealing individual ballots, select a structured most-votes outcome, present it and use selected material in a later explicitly linked round. Random tie policy promises equal chances and durable selection without mandating a generator. Existing operation versions and historical candidate files remain unchanged.

57 engine traces, 175 invalid definitions and all 30 examples pass schema checks; all 44 prior traces preserve outcomes, views and full state. Both durable hosts validate the retained profile and new consequential boundaries.

Four new witnesses supplement the retained 26 examples: [predefined poll](examples/predefined-vote.json), [contribution contest](examples/contribution-contest.json), [creative continuation](examples/creative-continuation.json) and [proposal workshop](examples/proposal-workshop.json). They demonstrate activity-data reuse across the new and retained families, not faithful prospective host app product migration. prospective host app is another prospective host app evaluating support.

- [Normative voting/continuation contract](voting-notes.md), [all retained operations](operations.md), [schema](package.schema.json)
- [Python](runtime.py), [JavaScript](runtime.mjs), independent [Python voting module](voting.py)/[JS voting module](voting.mjs)
- [Conformance](conformance/README.md), [durable evidence](../../validation/0.21/EVIDENCE.md), [supported profile](readiness-assessment.md)
- [Authoring](authoring.md), [compatibility/migration](COMPATIBILITY.md), [decision record](DECISIONS.md), [design checkpoint](DESIGN-CHECKPOINT.md)
- [prospective host app review packet prepared for submission](HOST-REVIEW.md)

```sh
PYTHONDONTWRITEBYTECODE=1 python3 format/0.21/check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.21/run.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.21/voting_trial.py
```

Schema uses the existing optional validation dependency. Hosts own accounts, dates/calendars, durable ordering, media infrastructure, rendering and notification delivery. Designated-person tie decisions and previous-winner eligibility are deferred explicitly. Finite continuation is supported; unlimited streams and general workflow programming are absent. Legacy migration accounting remains six complete/fourteen incomplete.
