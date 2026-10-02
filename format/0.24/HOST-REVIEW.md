# Candidate 0.24 executable host review packet

Base: completed 0.23 `ba0530038747f5ed0ee5570d232e2ec72db64a40`. Review current implementation pin separately. New neutral Creative relay examples express first-valid typed completion and saved rolling invitation order; no host dispatch on package identity/title.

## Run

```sh
PYTHONDONTWRITEBYTECODE=1 python3 format/0.24/relay_check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 format/0.24/check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 format/0.24/compatibility_check.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.24/relay_trial.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.24/run.py
```

Install the optional requirements-validation.txt dependency for schema checks. Python 3 and Node with `node:sqlite` are needed; durable trials bind loopback services to ephemeral ports and use temporary databases, trusted test clocks and authenticated actor tokens. No real messages or calendars are sent. Exact fixtures live in conformance/relay-cases.json.

## Acceptance gates

1. Both engines validate exact shape, declared capabilities, queue bindings and canonical matching before setup; all examples pass schema; invalid package/setup witnesses reject. Retained 0.23 operations preserve full state/views/outcomes under envelope-only translation.
2. Two simultaneous valid invitee submissions commit one entry, canonical output, queue, closure and accepted ID. Invalid owner/unready/wrong-kind/boolean-ticket attempts do not win; stale predecessor/ticket/actor/path reject. First means authoritative transaction order.
3. Accepted retries replay after closure/deadline/restart; changed retries reject. Saved shuffle/queue and output identity survive recovery at every event boundary. Historical operations retain their semantics and media/private grants.
4. Loser is explicitly first next time. Prior author stays excluded even after all offers expire. After success, carried invitee and next partner receive a fresh shared configurable deadline. Expiry opens the next pair against unchanged canonical at observed clock time.
5. Decline retains the other invitation ticket/deadline; both decline-before-partner and partner-before-decline orderings behave exactly. Membership removes stale tickets, retains survivor identity/order, appends authorized members and preserves failed identities. Insufficient roster pauses; odd tails and full pass are explicit.
6. Full eligible pass and 100 failure-transition budget are distinct exhausted reasons. Clock limits terminate non-resumably with notBefore:null, never clamped delays. Null-canonical retries use input:null; cooldown boundary rejects early and accepts at notBefore.
7. Queue authority attests immutable whole source output and destination viewers. Aliases of the same qualified source reject; competing destination IDs yield only one successor. Failed setup leaves source unclaimed and no target/grants. Source claim, successor identity/state/grants/tokens/receipt commit together. Exact creation retry returns the original after offers expire; changed request conflicts.
8. Canonical origin material binds directly to successor without election/copy. Actual PNG owner/readiness, publication and cross-instance grants survive restart; unbound viewers cannot read. Demonstrate preauthorized membership separately from denied wholly new origin viewers. Queue membership alone gives no bytes.
9. A first-valid piece followed by private pair reflection is data-only and executes in both engines with privacy intact. Hosts import/export identical immutable packages/digests. Keep source scheduling/delivery/media infrastructure outside language claims.

See [contract](relay-notes.md), [design checkpoint](DESIGN-CHECKPOINT.md), [supported profile](readiness-assessment.md) and [evidence](../../validation/0.24/EVIDENCE.md). Six faithful 0.12 migrations remain six. The candidate adds a changed relay pattern, not an unconditional legacy migration. Independent review, production host integration and 1.0 acceptance are separate gates; no merge/deployment is performed here.
