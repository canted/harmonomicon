# Activity package format 0.7 candidate

**Status:** Candidate validated in two independent local hosts for text packages and package transfer. It is not a published standard.

A Harmonomicon package is data describing a digitally mediated group activity: human directions, participation bounds, provenance, exact host requirements, and one behavior contract. Candidate 0.7 retains the [six 0.6 behavior contracts](../0.6/README.md) and the [0.4 package exchange rules](../0.4/README.md) unchanged. Its `format` value is exactly `harmonomicon.activity-package/0.7`; examples use new package versions because their format field changed. A host must report unknown behavior or missing capabilities as `unsupported` rather than guessing.

0.7 adds `guided_rounds@1`: a fixed sequence of timed prompts with a participant partition for each round. It represents software-controlled timers, optional text contributions, and audience views for a digital adaptation of simple group sessions. The [mechanism survey](../../research/mechanism-survey.md) identifies timed phases and changing groups in 1-2-4-All and other practices. This contract does not claim to reproduce their whole human-facilitated procedure or judge the quality of a discussion.

## Package and setup

The behavior is `{ "contract": "guided_rounds@1", "allowPromptOverride": boolean, "rounds": [...] }`. It requires `identity@1`, `serial_events@1`, `durable_state@1`, `private_views@1`, `clock@1`, and `text@1`. The `rounds` array contains 2–8 ordered objects, each with exactly:

| Field | Meaning |
|---|---|
| `id` | Unique lowercase round identifier starting with a letter and containing letters, digits, or hyphens. |
| `prompt` | Nonempty text directions for this round. These are package data and are not secret. |
| `durationMs` | Positive safe integer elapsed duration. |
| `groupMin`, `groupMax` | Inclusive size bounds for each group in this round. `1 ≤ groupMin ≤ groupMax ≤ participants.max`. |
| `visibility` | `private`, `group`, or `all_after_round`, defined below. |

At instance creation the organizer supplies `startsAt`, no earlier than trusted creation time, and `groupsByRound`: one ordered array of `{ "id", "members" }` groups per package round. Group IDs are unique within a round and are nonempty strings other than `system`. Each group is nonempty and within that round's size bounds. Every participant belongs to exactly one group in each round. A participant may be assigned to a different group in the next round. The host validates every partition before creating the instance; it does not choose a matching algorithm. These assignments stay fixed after creation. `startsAt` plus all durations must fit the safe integer Unix-millisecond range. The general package prompt may be overridden only if `allowPromptOverride` is true; round prompts remain the package values.

The [small group synthesis](examples/small-group-synthesis.json) and [two-round icebreaker](examples/rounds-icebreaker.json) are digital example packages. Their prompts and timings are example choices, not rules attributed to a named physical activity.

## Time and contribution rules

The phase is `waiting` before `startsAt`, `round` while a round is open, and `complete` at the final closing time. Round 1 opens at `startsAt`; each subsequent round opens exactly when the preceding duration ends. A round window is half-open, so a contribution to an ending round is rejected at its close. `currentRound` is the one-based open number or null. A delayed worker cannot extend a round: the host advances time before every event and view and should record a tick at the opening and each closing boundary. A time jump crosses all elapsed boundaries in order. No submission is required to advance.

A participant may make one accepted `submit` per round, with exact payload `{ "round": current number, "value": nonempty text }`. The mandatory round number prevents a delayed request from landing in the next round. A second submission by that person in the same round rejects, even if the first was made in a different group configuration. `tick` with empty payload is accepted only from the host's `system` actor. These are the only event types in this contract. The host authenticates actors, supplies trusted time, commits accepted events atomically in one order, and retains accepted event IDs. An exact retry returns `replayed` without another contribution, including after the round closes; changed reuse returns `rejected`.

## Views

Every bound actor sees `{phase, currentRound, rounds}`. The `rounds` array contains every round opened so far. Each round view has its one-based `number`, `id`, `prompt`, `phase` (`open` or `closed`), and `groups` in setup order. Each group view has `id`, `members`, `submissionCount`, and `entries` in accepted order. An entry is `{group, actor, value}`. Group membership and submission counts are visible to all bound actors, including the organizer; this can reveal participation progress even when entry content is private.

The entries array is filtered for each viewer:

- `private`: a participant sees only their own entry; the organizer sees no content. Closing the round does not reveal it.
- `group`: members of that group see its entries immediately and afterward. Other groups and the organizer see no content.
- `all_after_round`: before the round closes, a participant sees only their own entry. At or after close, every bound participant and the organizer sees every group's entries for that round.

These audience projections apply to API reads, caches, and notifications. The host may store all content internally but cannot return a broader activity view to an actor. Missing contributors have no entry; the round still ends on time.

## Boundary and evidence

This contract does not let a facilitator advance a round early, change groups during a run, grant permission for an individual opinion, branch based on a human judgment, prove that people talked or performed, or provide low-latency synchronized audio. Those require distinct rules or host capabilities. Text directions can invite offline or live conversation; software can only enforce the digital timers, contributions, and views specified here.

The [0.7 schema](package.schema.json), [examples](examples/), and [26 conformance cases](conformance/README.md) cover seven exact behavior contracts. Run `python3 format/0.7/check.py` for the reference model. The [two-host local trial](../../validation/0.7/README.md) imports the packages into independent Python and Node.js SQLite-backed services and checks the same cases, worker jumps, invalid partitions, concurrent submissions, group privacy, restart, and package transfer. This establishes a local text slice, not every source activity or a public deployment.
