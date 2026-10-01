# Candidate 0.21 validation in two app hosts

Run from the repository root:

```sh
python3 format/0.21/check.py
python3 validation/0.21/run.py
```

Python 3 and Node.js with `node:sqlite` are required. The validation trial launches separate [Python](python_host.py) and [Node.js](node_host.mjs) HTTP services on loopback. Each uses its independently written 0.21 interpreter, its own SQLite database, persisted package versions, actor token hashes, contribution state, and accepted-event ledger. Instance effects and ledger writes are committed in one database transaction. Temporary databases and services are cleaned up after the trial.

## Checked evidence

- All thirty-four [conformance traces](../../format/0.21/conformance/README.md) pass through both authenticated HTTP interfaces, with every actor view matching the reference result.
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

The [migration trial](migration_trial.py) launches the actual retained 0.12 Python and Node implementations alongside their 0.21 counterparts. Each language compares six [check-in scenarios](../../format/0.21/conformance/check-in-migration.json), including the two original fixtures, early/late actions, empty/partial collection, read-driven deadlines, prompt override, replay, maximum time, and restart. A separate comparison verifies worker-only completion without participant reads. A [small adapter](../../format/0.21/migration_check.py) compares the same user-visible facts across their different view shapes; it does not imply API or running-instance compatibility.

A scheduled-check-in-to-pairs package transfers with the same canonical digest and runs with the same chosen settings in both apps. Both restart before opening, after reveal, and after private paired reflection. The previous pool and group transfer/race probes remain included.

## Routed numeric assessment

All six new scoring/form traces run through both app interfaces. Probes race two scores from the same assigned reviewer: exactly one is accepted, the other is rejected, and the winner replays after restart. Self/wrong-item and stale-round submissions are rejected. Other actors and the organizer see no private rating entries. A worker closes all remaining rating rounds from one clock jump without a participant read, and exact normalized results survive restart.

Disabling `integer_values@1`, `rate@1`, or `policy:mean_scaled_scores@1` separately removes that token from discovery and causes `unsupported` before state creation. An offset that cannot fit the actual roster causes `invalid_setup` without creating an instance.

A proposal-assessment package transfers with the same digest and runs with opaque Unicode, prototype-like, and large-decimal actor IDs. Both apps restart during scoring and after completion. Final ranks, raw-score privacy, and pair-only reflection match the reference and each other. The previous transfer/race/worker/migration checks remain included.

## Local transport

The transport exists for validation; the specification does not mandate these URLs. Bearer tokens authenticate requests. An admin token permits definition import, export, instance creation, and controlled clock advancement. Creation returns tokens per distinct bound identity; host_controls allows organizer participation. Private instance views are never available through the admin token alone.

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

## Bounded recurrence and migration evidence

[Recurrence probes](recurrence_trial.py) compare nine scenarios against actual retained 0.12 hosts in each language, including all three original fixtures, day-sized gaps/history, private/immediate/after-close visibility, maximum closing times, and restart. Separate probes race same-actor submissions, check one accepted winner and replay after restart, reject gap/stale actions, verify private organizer views, and wait for worker-only completion through all remaining windows without participant reads.

Disabling `for_windows@1`, `collect_window@1`, or `completion_status@1` removes that token from discovery and yields `unsupported` before state creation. Invalid or overflowing setup creates no instance. A newly authored three-window choice-and-pairs package transfers with its canonical digest and executes with opaque Unicode/prototype-like actor IDs; settings, polls, and pair-private continuation survive restart. These local services do not establish notification delivery, local-calendar recurrence, mutable schedules or production app integration.

The package immutability probe derives its second revision from the input package revision, rather than a hard-coded number. It still requires changed bytes under either existing identity to conflict, identical reimport to be idempotent, the original exported definition to remain unchanged, and the running instance to remain pinned to its original prompt.

## Single-source distribution and linked response

[Distribution probes](distribution_trial.py) exercise concurrent assignment reads racing deadline workers, exact saved assignment vectors, same-actor response races, private source/response projections, wrong-source and forged-envelope rejection, exclusive deadline/replay behavior, and worker-only progression through distribution and response. Restarts with a different process seed leave the initial instance seed, consumed state and assignments unchanged. A default host-generated seed is also persisted before any distribution occurs.

The local hosts generate a nonzero 32-bit seed at creation; `--assignment-seed` is a trusted validation-only fixture option. Actor events and instance creation bodies cannot supply it. Unsupported operations, randomized policy or seed capability fail before state creation; a zero trusted test seed is invalid setup rather than a silently substituted default. These tests do not claim cryptographic assignment or balanced exposure.

A newly authored random source-response activity with private paired continuation transfers with the same package digest and runs with opaque Unicode/prototype-like actors, restart before distribution and during response, and matching final linked results/private groups. Media, mutable lifecycle rules, two-offer selection and exact Chorus parity remain outside this trial.

## Candidate 0.21 image trial

[image_trial.py](image_trial.py) runs actual PNG uploads in both independently implemented hosts. Host discovery advertises the semantic image capability and the narrower PNG byte profile. Tests cover malformed/truncated/trailing bytes, unsupported MIME, unauthenticated/organizer upload, ready immutable identity, owner/instance/kind/readiness rejection, view-gated reads, organizer reveal access, response races, missing authority, upload-success/submit-failure retries, exact deadline, recurrence history, worker-only completion, restart and unsupported/no-state behavior. A newly authored image/form/reveal/story package transfers and runs without new interpreter code. Definitions transfer; running state and media do not.

Four scenarios per language compare actual preserved 0.12 image check-in and daily image prompt hosts at every action/read/restart, including full selected timing, empty/partial histories, stale/deadline rejection, accepted replay and byte visibility. Image daily prompt remains group-immediate. See [exact host/runtime attestations and limits](../../format/0.21/image-notes.md) and [remaining readiness assessment](../../format/0.21/readiness-assessment.md). These local tests do not certify general image processing or production embedding.

## PNG validator correction after independent review

Independent review of `8411c02` found two implementation defects in the local upload validators: Python called `decompressobj.flush(length)`, whose argument does not bound decoded output, and both languages concatenated IDAT chunks separated by an ancillary chunk. These were defects against the declared local PNG profile, not optional scope decisions or image-language limitations.

Python now makes one `decompress(..., expected + 1)` call and requires exact expected length, EOF, no unused input and no unconsumed tail; it never flushes a potentially unbounded remainder. Both validators reject an IDAT chunk after the contiguous IDAT sequence has ended. [png_check.py](png_check.py) executes the actual checked-in validator functions: a CRC-valid 8MiB decoded bomb for a 1×1 image returns only five decoded bytes and never calls flush; CRC-valid split-IDAT-with-intervening-text rejects. Fifteen witnesses include valid RGB/RGBA, contiguous split IDAT, ancillary chunks before/after, maximum dimensions, all permitted filters, malformed/trailing/truncated/short/oversized streams. The same fixtures pass or reject through both authenticated upload endpoints, and the full retained durable suite is rerun. Earlier candidate directories are retained unchanged; this retained correction applies to the current local profile.

A subsequent recheck found that Node's `toString('ascii')` clears high bits in chunk names. The current validators check all four raw name bytes are ASCII letters and the reserved third byte is uppercase **before** interpreting any special chunk. Twelve CRC-valid high-bit mutations cover every position of IHDR, IDAT and IEND; an invalid ancillary reserved bit rejects and contiguous empty IDAT remains valid. Together with the preceding fixtures, all 29 direct and authenticated-upload witnesses agree across Python/Node. The image authorization/privacy/retry/recovery/legacy/transfer suite is rerun for this correction. This is another byte-validator defect correction, not a readiness scope exemption.

## Typed contributions and host controls

[Artifact trials](artifact_trial.py) run all six typed normative witnesses through both authenticated hosts with actual PNG/WAV receipts and every-event restart. They check rejected foreign/unready/wrong-kind references, private source read grants, independent replies, attributed reveal without unused-source publication, source-ID and response races, close/submission serialization, accepted retry, partial-success upload retry, long-date worker completion and unsupported/no-state. Thirty-two direct WAV validator fixtures agree; all 29 PNG regressions remain retained. A new immutable typed-exchange package exports/imports with identical digest and continues into retained pair-private reflection in both apps.

Admin-only `POST /instances/:id/control` accepts exact `{eventId,type,step,payload}` for configure/close and injects system actor/trusted clock. Participants cannot invoke this route or forge controls through events. Admin `POST /instances/:id/bindings` accepts `{actor,token}` only for an already bound identity; it is a local fixture for host authentication provisioning, not an activity role operation. Token hashes cannot be rebound to another identity. Creation accepts trusted `hostInputs`; no participant endpoint accepts them. Discovery separately advertises bounded PNG and canonical PCM16 WAV upload choices; language refs remain encoding-independent.

Feedback open replies are demonstrated as an external host-owned table whose after-close insert does not alter activity state, not a production conversation API. Journal 23/25-hour dates are explicit host inputs in separate solo instances, not language calendar/DST recurrence. Exact candidate contracts and limits are in [artifact notes](../../format/0.21/artifact-notes.md).

[Verification commands, results and evidence limits](EVIDENCE.md) record the final local checks for independent review.

## Candidate 0.21 voting and continuation

The [new trial](voting_trial.py) validates predefined and contribution-backed polls, one current vote with changes enabled/disabled, private ballots/public totals, structured selection/presentation, unique/tied/empty outcomes, explicit linked rounds, actual PNG/WAV candidate/source grants, wrong ownership/reference rejection, serialized candidate/vote/close races, exclusive deadlines, accepted replay after replacement, every-event restart and worker-only random resolution. Default random outcomes are checked for tied-set membership and durable retention, not equal cross-host draws. Trusted `--tie-choice` fixtures inject a selected tied index for exact durable cases; participant endpoints cannot supply fixture randomness. Each operation/policy can be disabled independently, yielding unsupported before state creation.

The proposal workshop transfers identical package bytes/digest and executes selected-proposal planning followed by retained private-pair deliberation. Empty or tied selection explicitly blocks planning and still permits a useful pair reflection. This is a genuinely different composition from the creative continuation. The activity title/ID is never a dispatch key. [Normative instruction contracts](../../format/0.21/voting-notes.md) separate ballot disclosure, aggregate presentation, typed source input and host duties.

The complete `run.py` invokes the retained suites and this new trial. Run the new trial alone while iterating with `PYTHONDONTWRITEBYTECODE=1 python3 validation/0.21/voting_trial.py`. Hosts bind only loopback with temporary fixtures; this does not certify public deployments, general blob/rendering security or prospective host app product integration. [Verification record](EVIDENCE.md) records actual commands/results and review corrections.
