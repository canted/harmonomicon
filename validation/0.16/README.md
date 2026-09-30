# Candidate 0.16 validation in two app hosts

Run from the repository root:

```sh
python3 format/0.16/check.py
python3 validation/0.16/run.py
```

Python 3 and Node.js with `node:sqlite` are required. The validation trial launches separate [Python](python_host.py) and [Node.js](node_host.mjs) HTTP services on loopback. Each uses its independently written 0.16 interpreter, its own SQLite database, persisted package versions, actor token hashes, contribution state, and accepted-event ledger. Instance effects and ledger writes are committed in one database transaction. Temporary databases and services are cleaned up after the trial.

## Checked evidence

- All twenty-two [conformance traces](../../format/0.16/conformance/README.md) pass through both authenticated HTTP interfaces, with every actor view matching the reference result.
- Both processes restart during each trace; tokens, private fields, current execution keys, and accepted IDs survive.
- Two simultaneous submissions from the same actor to one collection yield exactly one accepted contribution and one rejected contribution. The winner replays after restart. This checks transactional event ordering and per-actor limits.
- Unbound tokens cannot read a view. A participant cannot override `actor` or `at`; forged envelopes are rejected. Other participants see no private field before reveal.
- A worker closes all three timed story turns from one trusted clock jump without a participant read or action. Status polling reads persisted state without reconciling to the new time, so the worker is what performs the progression.
- Import is idempotent. Changed content under the same `(id, version)` conflicts; a different version can coexist while an existing instance keeps its original definition.
- An app with `append@1` disabled imports a valid package but returns `unsupported` with that missing operation before creating state. Its support discovery omits the disabled operation.
- A newly authored check-in-then-story package transfers from Python to Node with the same canonical digest, runs in both, and preserves its result after restart. Neither interpreter changes to support that arrangement.

Additional probes race different authors for the same item ID and different readers for the same item. Each race has exactly one accepted winner. The author cannot claim their own item; the losing claimant cannot read or acknowledge it. Restart preserves the dynamic item-loop expansion, assignment, and replay ledger. A worker skips an unclaimed item without a participant read. Group traces check that regrouping does not expose previous notes.

A pooled-ideas-then-pairs package also transfers with the same digest, runs in both apps, and survives restart during its item loop and after completion. Missing `policy:claim_reader@1` produces `unsupported` before instance creation. A roster that cannot form the declared groups produces `invalid_setup` without creating state. Client action types include `claim` and organizer-only `partition`, subject to the operation rules.

## Scheduled collection and migration evidence

The scheduled probes check saved questions across restart, invalid settings without created state, concurrent submissions with one winner, no early reveal after all answers, forbidden organizer advance, deadline exclusion, and replay after close. Disabling `instance_settings@1` returns `unsupported` before creation and removes it from support discovery.

The [migration trial](migration_trial.py) launches the actual retained 0.12 Python and Node implementations alongside their 0.16 counterparts. Each language compares six [check-in scenarios](../../format/0.16/conformance/check-in-migration.json), including the two original fixtures, early/late actions, empty/partial collection, read-driven deadlines, prompt override, replay, maximum time, and restart. A separate comparison verifies worker-only completion without participant reads. A [small adapter](../../format/0.16/migration_check.py) compares the same user-visible facts across their different view shapes; it does not imply API or running-instance compatibility.

A scheduled-check-in-to-pairs package transfers with the same canonical digest and runs with the same chosen settings in both apps. Both restart before opening, after reveal, and after private paired reflection. The previous pool and group transfer/race probes remain included.

## Routed numeric assessment

All six new scoring/form traces run through both app interfaces. Probes race two scores from the same assigned reviewer: exactly one is accepted, the other is rejected, and the winner replays after restart. Self/wrong-item and stale-round submissions are rejected. Other actors and the organizer see no private rating entries. A worker closes all remaining rating rounds from one clock jump without a participant read, and exact normalized results survive restart.

Disabling `integer_values@1`, `rate@1`, or `policy:mean_scaled_scores@1` separately removes that token from discovery and causes `unsupported` before state creation. An offset that cannot fit the actual roster causes `invalid_setup` without creating an instance.

A proposal-assessment package transfers with the same digest and runs with opaque Unicode, prototype-like, and large-decimal actor IDs. Both apps restart during scoring and after completion. Final ranks, raw-score privacy, and pair-only reflection match the reference and each other. The previous transfer/race/worker/migration checks remain included.

## Local transport

The transport exists for validation; the specification does not mandate these URLs. Bearer tokens authenticate requests. An admin token permits definition import, export, instance creation, and controlled clock advancement. Creation returns distinct participant and organizer tokens. Private instance views are never available through the admin token alone.

| Request | Result |
|---|---|
| `GET /support` | Exact format, sorted supported operations and capabilities and policies. |
| `POST /packages` with `{package}` | `imported`, `existing`, `package_conflict`, or `invalid_package`; successful results include digest. |
| `GET /packages/{id}/{version}` | Stored package definition and digest, or `not_found`. |
| `POST /instances` with `{id, packageId, version, participants, organizer}` and optional `settings` | Bind the roster and organizer at the current trusted clock; return `created` and actor tokens, or an explicit failure including `unsupported`. |
| `POST /instances/{id}/events` with `{eventId, type, step, payload}` | Authenticate the token's actor, supply trusted time, and return the event outcome. Client `tick`, `actor`, and `at` are rejected. |
| `GET /instances/{id}/view` | Reconcile deadlines and return the authenticated actor view. |
| `POST /clock` with `{at}` | Admin-only nondecreasing trusted test-clock advancement. |
| `GET /instances/{id}/status` | Admin-only persisted progress metadata for worker verification; no contributions and no reconciliation against the new clock. |

The local clock is a deterministic admin-controlled test clock, polled by deadline workers. Public deployments must supply an appropriate trusted clock and actor enrollment. These services are validation tools, not production apps. This trial does not establish public transport security, notification delivery, browser UI, media support, running-instance migration, or the remaining operations needed for 1.0.
