# Activity package format 0.8 candidate

**Status:** Candidate validated in two independent local hosts for text packages and package transfer. It is not yet a published standard.

A Harmonomicon package is data describing a digitally mediated group activity: human directions, participation bounds, provenance, exact host requirements, and one behavior contract. Candidate 0.8 retains the [seven 0.7 behavior contracts](../0.7/README.md) and the [package exchange rules](../0.4/README.md). Its `format` value is exactly `harmonomicon.activity-package/0.8`. The changed format field requires a new version for each carried example package. A host reports unknown behavior or missing capabilities as `unsupported`; it must not approximate a contract it does not implement.

Candidate 0.8 adds `competitive_handoff@1`. It handles an asynchronous chain in which two people may receive each offer, the first accepted answer advances, and an unanswered offer can fall back once. The [digital stress cases](../../research/digital-activity-stress-cases.md) and [offer-flow experiment](../../experiments/offer-flows/findings.md) identify both the stalled-turn and simultaneous-answer problems. This contract defines a text adaptation, not the rules of a named drawing game.

## Package and setup

The behavior object is exactly `{ "contract": "competitive_handoff@1", "allowPromptOverride": boolean, "steps": integer, "attemptMs": integer }`. `steps` is 2–8 and `attemptMs` is a positive safe integer. The contract requires `identity@1`, `serial_events@1`, `durable_state@1`, `private_views@1`, `clock@1`, and `text@1`.

At creation the organizer supplies `startsAt` and `routes`. `startsAt` is no earlier than trusted creation time. `routes` has exactly one item per step. Each step's item contains one or two ordered attempts; each attempt is a pair of distinct, bound participant IDs. A person may occur in different attempts or steps. The host validates the complete route before starting and does not choose the pairs or claim they are fair. `startsAt + steps × 2 × attemptMs` must fit the safe integer Unix-millisecond range. The initial prompt may be overridden only when `allowPromptOverride` is true.

The [two-offer story chain](examples/two-offer-story-chain.json) is a runnable text example. Its story prompt and the organizer's route are example choices, not constraints on other packages.

## Offers, deadlines, and events

The instance is `waiting` before `startsAt`. Step 1, attempt 1 opens at `startsAt`; its deadline is `startsAt + attemptMs`. Only the two offered participants receive the immediate input. For step 1 that input is the package prompt; for later steps it is the last accepted contribution. An attempt is half-open: a submission at its deadline is too late.

An offered participant can `submit` `{ "step": current one-based step, "attempt": current one-based attempt, "value": nonempty text }` or `decline` `{ "step": current step, "attempt": current attempt }`. The first valid submission in the host's authoritative commit order wins the step. The next step's first attempt opens immediately at that accepted event's trusted time. A final-step submission makes the instance `complete`. A losing simultaneous request is rejected, even if both were sent at the same displayed time. A decline removes that participant from the current offer. If both decline, the next attempt opens at the second decline's trusted time; if there is no next attempt, the chain becomes `stalled`.

At a deadline, the host advances to the next attempt at that exact boundary. A delayed worker must process elapsed attempt deadlines in order; it cannot extend an offer. If every attempt for a step times out or is declined, the instance is `stalled` and cannot accept more contributions. A `tick` with empty payload comes only from the host's `system` actor. These are the only event types. The host supplies trusted time, authenticates actors, commits accepted events atomically, and keeps accepted event IDs. An exact retry of an accepted event returns `replayed` even after the chain moves on; changed reuse returns `rejected`.

## Views and boundary

Every bound actor sees `phase`, the current one-based `step` when applicable, current `attempt` and `deadline` while open, and `acceptedCount`. A participant also sees `ownEntries`. Only an actor still offered on the current attempt sees `offer`, containing the step, attempt, deadline, and immediate input. The organizer sees no offer. Before completion, earlier entries and the full chain are not visible to other participants or the organizer. At `complete`, all bound actors see `entries` in accepted order. A stalled chain does not reveal its partial entries to the group. Hosts must preserve these projections in API reads and any notification or cache.

This contract does not provide an open participation queue, skip/requeue policy, image or drawing media, participant chosen routing, editing of previous entries, or a guarantee that someone will finish. These require different behavior or capabilities. It can accept a participant's text about something done away from the app, but the host only enforces the digital offers, deadlines, and views.

The [schema](package.schema.json), [example packages](examples/), and [30 conformance cases](conformance/README.md) define eight exact behavior contracts. Run `python3 format/0.8/check.py` for the reference model. The [two-host trial](../../validation/0.8/README.md) imports the same packages into separate Python and Node.js SQLite-backed services and checks the cases, worker deadlines, invalid routes, concurrent submissions, private views, restart, and transfer. The evidence is local, for the specified text subset.
