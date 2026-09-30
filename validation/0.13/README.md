# Candidate 0.13 validation in two app hosts

Run from the repository root:

```sh
python3 format/0.13/check.py
python3 validation/0.13/run.py
```

Python 3 and Node.js with `node:sqlite` are required. The validation trial launches separate [Python](python_host.py) and [Node.js](node_host.mjs) HTTP services on loopback. Each uses its independently written 0.13 interpreter, its own SQLite database, persisted package versions, actor token hashes, contribution state, and accepted-event ledger. Instance effects and ledger writes are committed in one database transaction. Temporary databases and services are cleaned up after the trial.

## Checked evidence

- All seven [conformance traces](../../format/0.13/conformance/README.md) pass through both authenticated HTTP interfaces, with every actor view matching the reference result.
- Both processes restart during each trace; tokens, private fields, current execution keys, and accepted IDs survive.
- Two simultaneous submissions from the same actor to one collection yield exactly one accepted contribution and one rejected contribution. The winner replays after restart. This checks transactional event ordering and per-actor limits.
- Unbound tokens cannot read a view. A participant cannot override `actor` or `at`; forged envelopes are rejected. Other participants see no private field before reveal.
- A worker closes all three timed story turns from one trusted clock jump without a participant read or action. Status polling reads persisted state without reconciling to the new time, so the worker is what performs the progression.
- Import is idempotent. Changed content under the same `(id, version)` conflicts; a different version can coexist while an existing instance keeps its original definition.
- An app with `append@1` disabled imports a valid package but returns `unsupported` with that missing operation before creating state. Its support discovery omits the disabled operation.
- A newly authored check-in-then-story package transfers from Python to Node with the same canonical digest, runs in both, and preserves its result after restart. Neither interpreter changes to support that arrangement.

## Local transport

The transport exists for validation; the specification does not mandate these URLs. Bearer tokens authenticate requests. An admin token permits definition import, export, instance creation, and controlled clock advancement. Creation returns distinct participant and organizer tokens. Private instance views are never available through the admin token alone.

| Request | Result |
|---|---|
| `GET /support` | Exact format, sorted supported operations and capabilities. |
| `POST /packages` with `{package}` | `imported`, `existing`, `package_conflict`, or `invalid_package`; successful results include digest. |
| `GET /packages/{id}/{version}` | Stored package definition and digest, or `not_found`. |
| `POST /instances` with `{id, packageId, version, participants, organizer}` | Bind the roster and organizer at the current trusted clock; return `created` and actor tokens, or an explicit failure including `unsupported`. |
| `POST /instances/{id}/events` with `{eventId, type, step, payload}` | Authenticate the token's actor, supply trusted time, and return the event outcome. Client `tick`, `actor`, and `at` are rejected. |
| `GET /instances/{id}/view` | Reconcile deadlines and return the authenticated actor view. |
| `POST /clock` with `{at}` | Admin-only nondecreasing trusted test-clock advancement. |
| `GET /instances/{id}/status` | Admin-only persisted progress metadata for worker verification; no contributions and no reconciliation against the new clock. |

The local clock is a deterministic admin-controlled test clock, polled by deadline workers. Public deployments must supply an appropriate trusted clock and actor enrollment. These services are validation tools, not production apps. This trial does not establish public transport security, notification delivery, browser UI, media support, running-instance migration, or the remaining operations needed for 1.0.
