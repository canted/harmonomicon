# Independent review of candidate 0.23

Reviewed implementation: `68d3f8322bee337a27ea52c9af94d330ff8116e8`, branch `codex/candidate-0-23`. Fresh parent-coordinated runtime and authoring reviews cleared this exact pin. This record adds documentation/evidence only; it does not change the reviewed schema, examples, engines or hosts.

## Runtime evidence

The independently supplied [review receipt](independent-review.json) records successful full durable-host and schema/engine commands, 108 traces, 324 invalid definitions, 40 examples, 73 actual historical 0.22 comparisons per language and 14 inspector tests. All four recorded log byte lengths/SHA-256 values were verified against the original reviewer outputs before retaining this receipt.

The independent probe suite passed 860 observable assertions covering mixed-kind shared quotas, concurrent acceptance/reader/close races, retries, frozen rosters, non-self assignment, exact item sampling, qualified identity, claim/acknowledgment/reveal, real media privacy, restart and cross-engine recovery, plus authoritative handoffs. The reviewer reported no material runtime findings. Historical format/validation and inspector files were unchanged at the reviewed pin; the checkout was clean. Both harnesses stopped/waited hosts and cleaned temporary directories. Process-list inspection was unavailable in the filesystem sandbox.

Original review outputs are retained in the review task workspace `/Users/will/Documents/Codex/2026-10-01/task-5`: `independent_probes.py`, `review-evidence.json`, `full-hosts.log`, `schema-engine.log`, `independent-probes.log` and `inspector.log`. The receipt preserves hashes and counts; the original probe is independent evidence, not a new normative implementation.

## Contract and authoring review

The parent reported a separate authoring review clearing the same pin: all 40 examples passed schema and both semantic validators; 35 new pooling traces, 93 definition negatives, 49 schema negatives and 32 setup/seed/budget negatives passed. All 73 retained comparisons preserved complete state/results/views, and the packet's executable JSON matched its source files. No material authoring/contract issue remained.

## Scope

These reviews cover local authenticated SQLite reference hosts and the supported 0.23 contract. They do not certify production/distributed/load behavior or faithful product migration. [Supported limits](../../format/0.23/readiness-assessment.md), [compatibility](../../format/0.23/COMPATIBILITY.md) and [decision record](../../format/0.23/DECISIONS.md) remain binding. No merge, push, deployment, publication, outside contact, 0.24 development or 1.0 decision is authorized.
