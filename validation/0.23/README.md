# Candidate 0.23 validation in two durable hosts

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 format/0.23/check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.23/run.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.23/pooling_trial.py
```

Python 3 and Node.js with `node:sqlite` are required. JSON Schema is an optional validation dependency; the runtimes do not require it. The trial starts independent [Python](python_host.py) and [Node](node_host.mjs) services on loopback, with temporary SQLite databases, immutable package digests/revisions, token-hash actor bindings, trusted clock workers, private state and accepted-event ledgers. Effects and accepted IDs commit in one serial transaction. Services/databases are cleaned up.

## New generic pooling trial

[pooling_trial.py](pooling_trial.py) runs actual text/image/audio/mixed pools with limits one and two, shared quotas, filled-window behavior, duplicate/overflow/wrong-kind rejection, withdrawal/readdition accounting, private own projections and exact replay after closure. Actual PNG/WAV bytes test ownership, kind/readiness and view-gated reads; a rejected unready attempt can be retried after readiness without consuming its item ID/quota. Equal bytes under distinct IDs remain distinct items.

Typed iteration tests accepted order, frozen final source readers including a noncontributor outside the original roster, organizer/self/withdrawn rejection, reader-only access, successful attributed publication, acknowledgment timeout without publication, stale/replayed keys, a compatible retained typed source and solo no-reader privacy. Every serial event compares exact independent-engine outcomes/views and restarts the real host.

Qualified multi-item voting tests final source eligibility, distinct equal-valued candidates, wrong-instance refs, current-vote replacement without duplicate counting, immutable old accepted replay, private ballots after aggregate publication and actual selected-result binding into a separately launched instance. Default host random ties and zero-vote selection test eligible membership and persisted outputs, not identical random streams between hosts.

The materially different [typed response workshop](../../format/0.23/examples/typed-response-workshop.json) assigns each unique recipient one saved source from multiple items, rejects wrong refs/extra replies, explicitly reveals used pairs and retains private unused audio and pair-only history. Identical package/digest transfer passes. Generated assignment seeds persist; restarting with different process seed options preserves sampled actual non-self items and media grants. No exposure fairness is inferred.

Concurrent quota-last-slot and item-ID races yield one accepted winner; close/submit races settle according to serial commit order, exclude late actions and retain accepted replay after restart. Exclusive opening/closing boundaries are checked. Every new operation and deterministic policy can be disabled separately: support discovery omits it and setup returns unsupported before target state exists.

## Retained suites

The complete `run.py` includes 34 retained HTTP traces and collection/reader/group/scoring workers and races, six actual 0.12 scheduled check-in comparisons, nine recurrence comparisons, saved random distribution/response, four actual historical image comparisons per language, real image/audio validation and typed source exchange, qualified voting and authoritative input trials. Input trials validate whole normalized origin/provenance, every viewer and denied later additions, actual cross-instance byte grants, ownership, fallback matrix and a different supplied-brief/planning/pair composition. Old anonymous loops, predefined polls and all prior versioned rules remain tested.

Engine/schema [conformance](../../format/0.23/conformance/README.md) covers 108 traces, 324 invalid definitions, 40 examples, every-boundary recovery, full 800-item expansion, conservative safe-clock budgets/MAX clamping, new static consumer restrictions and all 73 actual historical 0.22 comparisons. Seeded assignment retains its sampler contract; outcome randomness uses injected choices or durable membership properties.

## Validation transport and boundary

The HTTP URLs are a validation profile, not mandatory language endpoints. Bearer tokens authenticate actors; admin-only definition import/export, instance creation, clock/control and binding operations supply trusted context. Participant endpoints reject actor/time/control/randomness/binding injection. `GET /support` advertises exact format/tokens; `POST /packages` enforces immutable identity; `POST /instances` accepts supported package/roster and optional settings/hostInputs/hostBindings. Instance events, view/media reads and host controls use their authenticated paths. Status polls inspect persisted progress without advancing time; workers reconcile deadlines independently.

Hosts generate UUID identities, attest durable origins, retain projection-based media read grants and never turn viewing into submission ownership. The test clock is nondecreasing and deterministic; production clocks/accounts, storage/security/distributed ordering, media rendering, cross-provider trust, calendars/successor launch, notifications and interface design remain host responsibilities. Package exchange does not migrate live state or blobs. See [evidence](EVIDENCE.md), [supported limits](../../format/0.23/readiness-assessment.md) and [compatibility](../../format/0.23/COMPATIBILITY.md). Six historical migrations remain complete, fourteen incomplete; product parity remains outside this validation profile.
