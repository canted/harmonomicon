# Offer-flow contract 0.1

**Experimental.** Definitions use `activity-offer-flows/0.1`, an activity `kind`, actors and roles, required capability names, content, and kind-specific configuration. Events have `type`, `actor`, integer `at`, and object `payload`. The event list is processed in authoritative order. A missing capability yields `unsupported`; a rejected event does not perform its requested action. This experiment has two built-in flow kinds, not an executable rule language.

## Competitive relay

`initial` is the first chain entry. `mediaByStep` lists each next contribution's required media, and `routes[step][attempt]` contains exactly two distinct offered participants. The package fixes these pairs for this test. Selection of eligible people is therefore an organizer choice made before the run, not an algorithm inferred from Eat Poop You Cat.

The flow starts `ready` at step zero. A `system` `open` event with `deadline > at` activates the current pair. An offered participant can `submit` a nonempty artifact with the current `step`, `attempt`, required `media`, and a nonempty `requestId` at or before the deadline. The first valid submission **processed by the host** appends one chain entry and closes that attempt; a second submission is rejected. An exact retry of an accepted request ID yields `replayed` with no second append. Reusing that ID with a changed actor or payload rejects. This models an atomic single-winner decision, but the interpreters only process a serial event list; they do not prove database atomicity under real concurrency.

A `system` `timeout` at or after the deadline closes an open attempt. If a further pair is configured for that step, the flow returns to `ready`; otherwise it becomes `stalled`. A later `open` activates the next pair. At the exact deadline, `submit` and `timeout` can each win if processed first; their order, not a client-supplied timestamp, is authoritative in these fixtures. Accepted submissions complete one step and move to the next `ready` step, or to `done` after the last. Only offered participants see the current input before completion; all named participants see the chain at `done`.

The host must supply trusted identity, time, media storage, delivery, and an atomic commitment of each decision. `atomic_step_commit` in `requires` is an assertion to check, not proof that a host has those properties.

## Cover and Response

[Cover and Response](../../research/activities/cover-and-response.md) is a constructed digital group activity. The fixture uses numeric-string participant IDs and small numeric cover IDs. It models these operations:

1. Participants `submit_cover` while covers are still being collected. One active cover per person is represented. The host can `remove_cover` before the cover deadline.
2. `tick` advances the effective phase. At or after `coverDeadline`, responses open only if at least `minimumCovers` remain active. While below the minimum, later covers can still arrive. At `responseDeadline`, the activity becomes `complete`.
3. A cover contributor can `request_offer` after responses open. The two candidate covers exclude their own. Previously created offers count toward each cover's exposure. Candidates sort by the fewest existing offers, then by a deterministic `assignmentScore(roundId, userId, coverId)`; the two selected IDs are saved. A repeated request returns that saved offer.
4. The participant can `choose_cover` from their offered pair, then `submit_response` in an allowed medium. The response references the chosen cover. On completion, response-cover pairs become visible to participants.

For the small IDs in these fixtures, the score starts with the bitwise XOR of `roundId × 73856093`, `userId × 19349663`, and `coverId × 83492791`, then XORs that 32-bit value with its zero-filled right shift by 16. Exposure count sorts first; score sorts second. [Cases 11 and 13](cases/) fix the resulting offer IDs for opposite request orders. Equal-score ordering and large-ID arithmetic are not specified by this first contract; the later [exact-integer policy](../policy-portability/contract.md) defines both explicitly.

This contract intentionally omits SQL transactions, notification delivery, publication controls, richer views, and cancellation. It requires a person's own cover before `request_offer`, stores opaque artifacts, and permits one active cover and one current response per participant. The fixtures use small integer IDs and do not probe JavaScript number precision for very large IDs. Passing fixtures establish only the listed behavior of this constructed case.

## Checkpoint and replay meaning

Each fixture runs from initial state in both interpreters. At `checkpointAt`, a runner emits a JSON snapshot containing state, prior outcomes, and the next event index. A new process in either language reads that snapshot and processes the remaining events. Equality with uninterrupted replay shows the snapshot carries enough information for these traces and is portable between these two implementations. The experiment does not simulate a real process crash, database transaction, outbox, concurrent requests, or exactly-once message delivery. Event IDs and ordered durable logs are not specified here.
