# Behavior contracts for format 0.12

This document defines the ten exact behavior tokens accepted by the [0.12 package format](README.md). A package selects exactly one contract. Shared event, time, replay, capability, and exchange rules are in the format document. The [schema](package.schema.json) validates structure; these rules define what a host must do. All actor and media views described here are access-control requirements at read, cache, notification, and byte-read boundaries, not only screen suggestions.

References to example packages point to [this release](examples/). A narrower statement in a contract overrides a shared rule for that contract; otherwise the [shared 0.12 rules](README.md) apply.


## `timed_collection@1`

The package's `behavior` is `{ "contract": "timed_collection@1", "medium": "text" | "image_ref", "allowPromptOverride": boolean }`. The host supplies `opensAt` and `closesAt` at instance creation, with `opensAt < closesAt`; both are trusted integer Unix milliseconds. Creation must occur no later than `opensAt`. If `allowPromptOverride` is true, the organizer may set a nonempty prompt at creation; otherwise the package's `content.prompt` is used.

The phases are `waiting` before `opensAt`, `open` in `[opensAt, closesAt)`, and `closed` at or after `closesAt`. A participant's first valid `submit` during `open` stores `{actor, value}`. Its payload is `{ "value": ... }`, with the value matching `medium`. A second submission by the same participant is rejected unless it is a replay of the first accepted event ID. `tick` from `system` has an empty payload, may advance the phase, and is accepted even if it changes nothing. The collection closes at `closesAt` regardless of missing submissions. Missing participants contribute no entry.

Before close, every participant and the organizer may see the phase and submission count. A participant may also see their own entry. No one receives another person's entry through the activity view, including the organizer. After close, all bound participants and the organizer may see the ordered entries; their order is the order of accepted submissions. The host may store private data internally but must enforce this projection at its read boundaries.

## `sequential_handoff@1`

The package's `behavior` is `{ "contract": "sequential_handoff@1", "medium": "text" | "image_ref", "steps": integer, "allowPromptOverride": boolean }`. `steps` is at least two and equals both `participants.min` and `participants.max`. At instance creation the host supplies `route`: every participant ID exactly once, in a chosen order, with length `steps`. The first route member is current. The prompt override rule is the same as above.

The phase starts `active`. A valid `submit` from the current participant stores their `{actor, value}` and advances to the next route member. Its payload is `{ "value": ... }`, matching `medium`. Other actors' submissions are rejected. After the final accepted submission, the phase is `complete`, the current actor is null, and no further contribution is accepted.

Before completion, everyone may see the phase, current actor, and one-based step number. A participant may see their own accepted entry. Only the current actor sees the immediate predecessor's value as input; the first actor instead sees the prompt. The organizer sees no entry content before completion. The package prompt is public content, so this contract does not claim that the first input is secret. On completion, all bound participants and the organizer may see the full ordered chain. This contract has no timeout, skip, replacement, or reassignment rule: an unfinished handoff waits for its current actor. A package needing recovery must use a later contract with defined recovery semantics.

## `repeated_collection@1`

This contract defines a finite series of collection windows on a fixed millisecond interval. It supports a private group practice, immediate group sharing, or reveal after each window. Its `behavior` is `{ "contract": "repeated_collection@1", "medium": "text" | "image_ref", "allowPromptOverride": boolean, "intervalMs": integer, "windowMs": integer, "occurrences": integer, "visibility": "private" | "group_after_close" | "group_immediate" }`. `intervalMs` is positive; `windowMs` is positive and no greater than `intervalMs`; `occurrences` is from 2 through 366. These fields are fixed by the package. The organizer supplies `startsAt` when creating an instance. Creation time must be no later than `startsAt`. The final closing time must fit the safe integer time range. The same prompt applies to every occurrence unless the organizer sets a permitted prompt override at instance creation.

Occurrence numbers are one-based. Occurrence `n` opens at `startsAt + (n − 1) × intervalMs` and closes at its opening plus `windowMs`. Its window is half-open: submission is allowed at opening and rejected at closing. Windows do not overlap. The overall phase is `waiting` before the first opening, `open` during a window, `between` in a gap, and `complete` at or after the final closing. `currentOccurrence` is the open occurrence number, or null in any other phase. Time advances before every event and view, including when a worker tick is late or absent. A worker should wake at each opening and closing to make transitions visible promptly. If time jumps across several windows, the host closes all elapsed windows and retains their histories.

A participant may make one accepted `submit` in each window, with payload `{ "occurrence": n, "value": ... }`. The occurrence number is mandatory so a delayed request cannot silently become a submission for the next window. It must identify the currently open occurrence. `value` matches `medium` and follows the shared contribution rules above. A rejected, late, or duplicate submission does not replace an entry. An accepted event ID can be replayed across later windows under the shared replay rule. A `tick` from `system` has empty payload and is accepted even when it changes no phase; it cannot add an entry. `submit` and `tick` are the only event types in this contract.

Every bound participant and the organizer sees the overall `phase`, `currentOccurrence`, and an `occurrences` array covering every occurrence that has opened so far, ordered by number. Each occurrence view contains `number`, `phase` (`open` or `closed`), `submissionCount`, and `statuses` in enrollment order. Each status is `{ "actor": participantId, "status": "pending" | "complete" | "missed" }`. A submitted participant is `complete`; an absent participant is `pending` while the window is open and `missed` after it closes. The status is visible to the whole group even when entries are private. Each participant also sees their own accepted entry for each occurrence as `own`; the organizer never receives `own`.

With `private`, no occurrence view has an `entries` field, including after close. With `group_after_close`, `entries` appears only after that occurrence closes. With `group_immediate`, `entries` appears as soon as the occurrence opens. It contains accepted `{actor, value}` records in authoritative submission order. These audience rules apply to reads, cached views, and notifications. The host may retain private entries internally but must not expose them through another actor's view. An old occurrence keeps its visibility rule and entries when later occurrences begin. There is no removal, edit, skip, or penalty beyond `missed` status.

This is an elapsed-time schedule, not a local-calendar rule. A 86,400,000 ms interval means consecutive windows begin 24 hours apart; it does not promise the same local wall-clock time across daylight-saving changes. Notifications, reminders, timezones, open-ended recurrence, changing membership, and per-occurrence prompts require later contracts or host behavior outside this package.

## `offered_response@1`

This contract has two timed submission stages and a final reveal. Its `behavior` is `{ "contract": "offered_response@1", "sourceMedium": "text" | "image_ref", "allowPromptOverride": boolean, "assignmentPolicy": "policy:balanced_artifacts_exact32@1" }`. Responses are nonempty text. The organizer supplies `opensAt`, `sourceDeadline`, `responseDeadline`, and `roundId` at instance creation. The trusted times satisfy `createdAt ≤ opensAt < sourceDeadline < responseDeadline` and fit the safe integer range. `roundId` and every participant ID for this contract are canonical unsigned decimal strings from `0` through `18446744073709551615`, with no leading zero except `0`. They are activity-local aliases that a host binds to real authenticated accounts. The organizer ID remains an opaque nonempty string, distinct from participants and `system`.

The phases are `waiting` before `opensAt`, `sources_open` in `[opensAt, sourceDeadline)`, then either `responses_open` in `[sourceDeadline, responseDeadline)` if at least three sources were accepted or terminal `insufficient_sources` otherwise. At or after `responseDeadline`, a successful response stage becomes `complete`. All transitions are based on trusted time before processing an event or read. A worker should wake at the named boundaries; a delayed worker cannot extend a stage. An insufficient-source activity never enters the response stage or reveals its sources to the group.

During `sources_open`, each participant may make one accepted `submit_source` with payload `{ "value": ... }` matching `sourceMedium`. The actor's canonical participant ID also identifies that source for assignment; no separate artifact ID is supplied. The source pool is fixed at `sourceDeadline`. There is no edit, removal, or late source. Only a source contributor may request an offer or submit a response.

During `responses_open`, `request_offer` has empty payload. Its first accepted event saves an ordered pair of other contributors' source IDs for that requester. The requester sees those two source values in the same order. A later request with a new event ID returns `existing`, records that ID for replay, and returns the saved pair; an exact retry of either recorded ID returns `replayed`. The offer is not recalculated after a refresh or restart. Requests from different people use the host's authoritative event order, so an earlier saved offer can affect a later one. An invalid request changes neither offers nor the event-ID ledger.

The required `policy:balanced_artifacts_exact32@1` ranks every other contributor's source by `(exposure count, score, numeric source ID)` ascending and selects the first two. Exposure count is the number of saved offers that already contain that source ID. Let `M = 2^32`, `r` be the numeric `roundId`, `u` the numeric requester ID, and `a` the numeric source ID. All arithmetic is exact unsigned integer arithmetic:

```text
x = ((r × 73856093) mod M) XOR ((u × 19349663) mod M) XOR ((a × 83492791) mod M)
score = x XOR (x >> 16)
```

`XOR` is bitwise XOR on unsigned 32-bit words and `>>` is a zero-filling shift. The score is an unsigned 32-bit integer. JSON numbers must not represent these IDs; implementations need exact handling above `2^53`. This specializes the [experimentally specified policy](../../experiments/policy-portability/contract.md) to one source per contributor, using that contributor's ID as the source ID. A host missing the exact policy token returns `unsupported` before creating the instance.

A contributor with a saved offer may make one accepted `submit_response` with payload `{ "source": sourceId, "value": text }`. `source` must be one of their two saved offer IDs. A response is stored as `{ "actor": contributorId, "source": sourceId, "value": text }`; multiple contributors may choose the same source. A second response from the same contributor is rejected. At the response deadline, the activity completes even if some contributors did not request offers or respond. `tick` from `system` has empty payload and is accepted even if the phase is unchanged. These four event types—`submit_source`, `request_offer`, `submit_response`, and `tick`—are the only ones in this contract.

Every participant and the organizer sees `{ "phase", "sourceCount", "responseCount" }`. A participant also sees their accepted source as `ownSource`, their saved ordered pair as `offer` containing `{actor, value}` records, and their accepted response as `ownResponse`. Before `complete`, no one sees another person's source except through their own two-source offer; no one sees another person's response, including the organizer. At `complete`, everyone additionally sees `sources` in accepted source order and `responses` in accepted response order. In `insufficient_sources`, no group `sources` or `responses` fields appear; contributors retain only their own source. The host must enforce these projections at every read, cached view, and notification boundary.

The package does not define voting, scoring captions, selecting a winner, source moderation, media-file transfer, reminders, or replacement of missing contributors. An `image_ref` host must verify the reference and its access rights; the reference-model examples cannot prove actual image storage.

## `project_cycle@1`

### Package and instance

The behavior configuration is exactly `{ "contract": "project_cycle@1", "allowPromptOverride": boolean }`. It requires `identity@1`, `serial_events@1`, `durable_state@1`, `private_views@1`, `clock@1`, and `text@1`. The [small team jam](examples/small-team-jam.json) is a complete package example. The [JSON Schema](package.schema.json) checks its structure; this document defines its runtime meaning.

At instance creation, the host binds an organizer, distinct participant IDs within the package bounds, and `teams`: an ordered array of at least two `{ "id": string, "members": [participant IDs] }` records. Team IDs are unique nonempty strings other than `system`. Every team has at least one member; every participant belongs to exactly one team. Teams and membership stay fixed for the instance. The organizer is not a team member. The host also binds trusted integer millisecond times `opensAt`, `submissionDeadline`, and `reviewDeadline`, satisfying `createdAt ≤ opensAt < submissionDeadline < reviewDeadline` within the safe integer time range. A prompt override at creation is valid only when `allowPromptOverride` is true.

Phases are `waiting` before `opensAt`, `work` in `[opensAt, submissionDeadline)`, `review` in `[submissionDeadline, reviewDeadline)`, and `complete` at or after `reviewDeadline`. The host advances phases before events and views, even if a scheduled worker runs late. A worker should wake at each boundary. Missing submissions or reviews never delay a boundary. Boundary ticks from `system` have an empty payload and are accepted without adding a human contribution.

### Participant actions

All contribution values below are nonempty text. The actor is authenticated by the host; a client cannot supply another actor or trusted time. An event has a nonempty `eventId`, `type`, actor, trusted `at`, and exact payload. Accepted IDs are durable: retrying the same ID with the same type, actor, and structurally equal payload returns `replayed` without a second effect, including after a deadline. Reusing an ID with changed content returns `rejected`.

| Event type | Allowed time and actor | Payload and effect |
|---|---|---|
| `post_progress` | A participant during `work`. | `{ "audience": "team" | "group", "value": text }`. Appends a post identified by its accepted `eventId`, with author, team, audience, value, and an initially empty comment list. Any number of distinct posts may be made. |
| `comment` | A participant during `work`. | `{ "postId": accepted post event ID, "value": text }`. Appends one comment. A team post can be commented on only by that team's members; a group post by any participant. Unknown or inaccessible posts reject. |
| `submit_final` | A participant during `work`. | `{ "value": text }`. The first accepted final from a team is that team's only final. Another member's competing submission rejects. Other teams' final content stays concealed until `review`. |
| `submit_review` | A participant during `review`. | `{ "team": other team ID, "value": text }`. The target must have an accepted final. Each participant may review each other team at most once. Self-team and absent-final reviews reject. Reviews stay concealed from other people until `complete`. |
| `tick` | Host `system` actor. | `{}`. Advances scheduled phases without making a contribution; no other actor may send it. |

The five event types above are the only ones in this contract. A rejected action does not add a post, comment, final, or review. The host's authoritative commit order resolves competing team finals and comment order. Accepted events and phase transitions survive restart. The [0.12 package exchange rules](README.md#package-exchange-and-identity) apply before instance creation.

### Views

All bound actors see `phase`, `finalCount`, `reviewCount`, and `finalStatuses` in team enrollment order. Each status is `{ "team": id, "status": "pending" | "submitted" | "missed" }`: absent finals are `pending` through `work` and `missed` after the submission deadline. Counts and statuses may reveal participation progress, not content.

The `progress` array preserves accepted post order and includes all `group` posts plus the viewer's own team's `team` posts. The organizer sees group posts only. Each visible post includes its accepted event ID, team, author, audience, value, and comments in accepted order. A person cannot obtain another team's private post or comment through an activity view.

A participant sees their team's accepted final as `ownFinal` as soon as it exists, and an `ownReviews` array containing only reviews they wrote. The organizer receives neither field. During `review` and `complete`, everyone additionally sees `finals` in accepted order. Only at `complete` does everyone see `reviews` in accepted order. These projections also apply to cached views and notifications. The package prompt is public directions; the host does not claim to verify work done away from the app.

## `ongoing_space@1`

### Package and schedule

The behavior is `{ "contract": "ongoing_space@1", "allowPromptOverride": boolean, "schedule": ... }`. It requires `identity@1`, `serial_events@1`, `durable_state@1`, `private_views@1`, `clock@1`, and `text@1`.

- `{"kind":"open"}` lets participants post during one `[startsAt, endsAt)` period. The organizer supplies both trusted times at instance creation, with `createdAt ≤ startsAt < endsAt`. It can be a long period, but the end must be within the safe integer millisecond range.
- `{"kind":"fixed_prompt_series","intervalMs":n,"windowMs":n,"prompts":[...],"statusVisibility":"none"|"group"}` defines 2–366 nonempty text prompts. `intervalMs` is positive; `windowMs` is positive and no greater than `intervalMs`. The organizer supplies `startsAt` no earlier than creation. Occurrence `k` opens at `startsAt + (k − 1) × intervalMs` and closes `windowMs` later; the final close must fit the safe integer range. Windows do not overlap. The prompt at array index `k − 1` belongs to occurrence `k`.

A prompt override at creation is permitted only if `allowPromptOverride` is true. It changes the package's general `content.prompt`, not the fixed series array. Prompts are package data and may be visible to someone who can export the package; this contract does not promise surprise or secrecy for later prompts.

The `open` schedule has phases `waiting`, `open`, and `complete`. The fixed series has `waiting`, `open` during a window, `between` in a gap, and `complete` at or after the final close. `currentOccurrence` is the one-based open number or null. The host advances phases before every event and view; delayed workers cannot extend a window. Workers should wake at each opening and closing, including boundaries crossed in one delayed jump. Fixed intervals measure elapsed milliseconds, not local-calendar days across daylight-saving changes.

### Entries and comments

A participant can make any number of accepted `post_entry` events during `open`. The event ID becomes the entry ID. For the open schedule, the exact payload is `{ "audience": "private" | "group", "value": text }`. For a fixed series it is `{ "occurrence": current number, "audience": "private" | "group", "value": text }`. The occurrence number is mandatory so a delayed request cannot silently post to a later prompt. A text value is nonempty; there is no word-count or quality test. An entry stores `{id, actor, occurrence, audience, value, comments}` in authoritative acceptance order. `occurrence` is null for an open schedule, and `comments` begins empty.

A participant can `comment` with `{ "entryId": accepted entry ID, "value": text }` on a `group` entry while the activity is `open` or `between`. Comments are accepted in a gap so conversation can continue between prompts. They are rejected before opening, at or after completion, and on private or unknown entries. Each accepted comment is appended as `{actor, value}` to its entry. The organizer can read shared entries but is not a participant and cannot post or comment.

`tick` with empty payload is accepted only from the host's reserved `system` actor. These three event types—`post_entry`, `comment`, and `tick`—are the only ones for this contract. Actors and time are trusted host inputs, not client assertions. All accepted event IDs are durable: an exact retry returns `replayed` without another entry or comment, even after the window closes; changed reuse returns `rejected`. A rejected action changes no contribution, though its trusted time can still advance the phase.

### Audience views and status

Every bound actor sees `phase` and an `entries` array in accepted order. It contains all group entries and, for a participant, that participant's own private entries. The organizer sees group entries only. Comments on a group entry appear with that entry as soon as accepted. Private content must not leak through activity views, caches, or notifications.

For a fixed series, every view also contains `currentOccurrence` and an `occurrences` array for every occurrence that has opened, in number order. Each item includes `{number, prompt, phase}`; item phase is `open` until its close and `closed` afterward. When `statusVisibility` is `group`, each item also includes `statuses` in participant enrollment order. A status is `complete` after that participant makes at least one accepted entry in the occurrence, even if the entry is private; otherwise it is `pending` while open and `missed` after close. This deliberately reveals completion without revealing the entry. With `statusVisibility: "none"`, no status or missed-day signal is emitted. A soft prompt invitation should use `none` rather than silently imposing a penalty.

Membership is fixed for the instance. Entries and comments remain in history across occurrences. The contract has no edit, deletion, moderation, reactions, nested threads, attachment storage, local-calendar schedule, notifications, or host verification of work done away from the app. Hosts may provide these separately only with clear capability and audience rules; they are not implied by `ongoing_space@1`.

## `guided_rounds@1`

### Package and setup

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

### Time and contribution rules

The phase is `waiting` before `startsAt`, `round` while a round is open, and `complete` at the final closing time. Round 1 opens at `startsAt`; each subsequent round opens exactly when the preceding duration ends. A round window is half-open, so a contribution to an ending round is rejected at its close. `currentRound` is the one-based open number or null. A delayed worker cannot extend a round: the host advances time before every event and view and should record a tick at the opening and each closing boundary. A time jump crosses all elapsed boundaries in order. No submission is required to advance.

A participant may make one accepted `submit` per round, with exact payload `{ "round": current number, "value": nonempty text }`. The mandatory round number prevents a delayed request from landing in the next round. A second submission by that person in the same round rejects, even if the first was made in a different group configuration. `tick` with empty payload is accepted only from the host's `system` actor. These are the only event types in this contract. The host authenticates actors, supplies trusted time, commits accepted events atomically in one order, and retains accepted event IDs. An exact retry returns `replayed` without another contribution, including after the round closes; changed reuse returns `rejected`.

### Views

Every bound actor sees `{phase, currentRound, rounds}`. The `rounds` array contains every round opened so far. Each round view has its one-based `number`, `id`, `prompt`, `phase` (`open` or `closed`), and `groups` in setup order. Each group view has `id`, `members`, `submissionCount`, and `entries` in accepted order. An entry is `{group, actor, value}`. Group membership and submission counts are visible to all bound actors, including the organizer; this can reveal participation progress even when entry content is private.

The entries array is filtered for each viewer:

- `private`: a participant sees only their own entry; the organizer sees no content. Closing the round does not reveal it.
- `group`: members of that group see its entries immediately and afterward. Other groups and the organizer see no content.
- `all_after_round`: before the round closes, a participant sees only their own entry. At or after close, every bound participant and the organizer sees every group's entries for that round.

These audience projections apply to API reads, caches, and notifications. The host may store all content internally but cannot return a broader activity view to an actor. Missing contributors have no entry; the round still ends on time.

## `competitive_handoff@1`

### Package and setup

The behavior object is exactly `{ "contract": "competitive_handoff@1", "allowPromptOverride": boolean, "steps": integer, "attemptMs": integer }`. `steps` is 2–8 and `attemptMs` is a positive safe integer. The contract requires `identity@1`, `serial_events@1`, `durable_state@1`, `private_views@1`, `clock@1`, and `text@1`.

At creation the organizer supplies `startsAt` and `routes`. `startsAt` is no earlier than trusted creation time. `routes` has exactly one item per step. Each step's item contains one or two ordered attempts; each attempt is a pair of distinct, bound participant IDs. A person may occur in different attempts or steps. The host validates the complete route before starting and does not choose the pairs or claim they are fair. `startsAt + steps × 2 × attemptMs` must fit the safe integer Unix-millisecond range. The initial prompt may be overridden only when `allowPromptOverride` is true.

The [two-offer story chain](examples/two-offer-story-chain.json) is a runnable text example. Its story prompt and the organizer's route are example choices, not constraints on other packages.

### Offers, deadlines, and events

The instance is `waiting` before `startsAt`. Step 1, attempt 1 opens at `startsAt`; its deadline is `startsAt + attemptMs`. Only the two offered participants receive the immediate input. For step 1 that input is the package prompt; for later steps it is the last accepted contribution. An attempt is half-open: a submission at its deadline is too late.

An offered participant can `submit` `{ "step": current one-based step, "attempt": current one-based attempt, "value": nonempty text }` or `decline` `{ "step": current step, "attempt": current attempt }`. The first valid submission in the host's authoritative commit order wins the step. The next step's first attempt opens immediately at that accepted event's trusted time. A final-step submission makes the instance `complete`. A losing simultaneous request is rejected, even if both were sent at the same displayed time. A decline removes that participant from the current offer. If both decline, the next attempt opens at the second decline's trusted time; if there is no next attempt, the chain becomes `stalled`.

At a deadline, the host advances to the next attempt at that exact boundary. A delayed worker must process elapsed attempt deadlines in order; it cannot extend an offer. If every attempt for a step times out or is declined, the instance is `stalled` and cannot accept more contributions. A `tick` with empty payload comes only from the host's `system` actor. These are the only event types. The host supplies trusted time, authenticates actors, commits accepted events atomically, and keeps accepted event IDs. An exact retry of an accepted event returns `replayed` even after the chain moves on; changed reuse returns `rejected`.

### Views and boundary

Every bound actor sees `phase`, the current one-based `step` when applicable, current `attempt` and `deadline` while open, and `acceptedCount`. A participant also sees `ownEntries`. Only an actor still offered on the current attempt sees `offer`, containing the step, attempt, deadline, and immediate input. The organizer sees no offer. Before completion, earlier entries and the full chain are not visible to other participants or the organizer. At `complete`, all bound actors see `entries` in accepted order. A stalled chain does not reveal its partial entries to the group. Hosts must preserve these projections in API reads and any notification or cache.

This contract does not provide an open participation queue, skip/requeue policy, image or drawing media, participant chosen routing, editing of previous entries, or a guarantee that someone will finish. These require different behavior or capabilities. It can accept a participant's text about something done away from the app, but the host only enforces the digital offers, deadlines, and views.

## `offered_response_vote@1`

### Package and setup

The behavior object is exactly `{ "contract": "offered_response_vote@1", "sourceMedium": "text" | "image_ref", "allowPromptOverride": boolean, "assignmentPolicy": "policy:balanced_artifacts_exact32@1" }`. It requires `identity@1`, `serial_events@1`, `durable_state@1`, `private_views@1`, `clock@1`, `text@1`, and the named policy. An image-source package additionally requires `image_ref@1` as [defined here](media.md).

The organizer supplies the same source setup as `offered_response@1`: canonical unsigned 64-bit participant and round IDs, `opensAt`, `sourceDeadline`, and `responseDeadline`, plus `voteDeadline`. Trusted creation time must be no later than `opensAt`; the four stage times must be strictly increasing and within the safe integer Unix-millisecond range. The organizer may override the initial prompt only if the package permits it. The host validates setup before creating the instance. It does not choose a winner by assessing caption quality.

### Phases and votes

The phases are `waiting`, `sources_open`, `responses_open`, `voting`, and `complete`. Source and response windows are half-open. If fewer than three sources exist at `sourceDeadline`, the phase becomes terminal `insufficient_sources`; offers, voting, and group reveal do not occur. Otherwise source offers and linked responses follow the unchanged `offered_response@1` assignment, submission, and retry rules. At `responseDeadline`, the host reveals accepted sources and captions and opens voting. Missing captions do not delay the phase.

During `[responseDeadline, voteDeadline)`, any bound participant may submit one `submit_vote` with exact payload `{ "responseActor": participant ID }`. The target must be the actor of an accepted caption and cannot be the voter. Participants do not have to submit an image or caption to vote. The first valid vote from an actor wins in the host's authoritative commit order. A second vote is rejected. Exact retries of accepted events return `replayed`, including after the deadline; changed reuse is rejected. At `voteDeadline`, new votes are rejected. The host's `system` actor may record `tick` events at stage boundaries, including after a worker time jump.

All bound actors see `phase`, `sourceCount`, `responseCount`, and `voteCount`. During voting and after completion they see the accepted `sources` and `responses` in accepted order. A participant sees their own vote as `ownVote`; neither the organizer nor other participants see individual ballots. At completion, everyone also sees `scores`: one `{responseActor, votes}` item for every accepted caption, sorted by numeric participant ID. `winners` contains every response actor tied for the largest positive total in that order. If there are no votes, `winners` is empty and scores are zero; if there are no captions, scores and winners are empty. The host never silently breaks a tie. Media byte reads follow the participant views and [image access rule](media.md).

## `permissioned_dialogue@1`

### Package and setup

The behavior object is exactly `{ "contract": "permissioned_dialogue@1", "allowPromptOverride": boolean, "phasePrompts": { ... } }`. `phasePrompts` has exactly four nonempty text fields: `meaning`, `maker_questions`, `neutral_questions`, and `permissioned_opinions`. It requires `identity@1`, `serial_events@1`, `durable_state@1`, `private_views@1`, `clock@1`, and `text@1`.

At instance creation the organizer is the facilitator and supplies `maker`, one of the bound participants. All other participants are responders. The organizer is distinct from every participant. The trusted creation time must fit the safe integer Unix-millisecond range. The initial general prompt may be overridden only when `allowPromptOverride` is true; the four phase prompts stay fixed from the package. The instance begins in `meaning`; no clock or participant submission advances a phase automatically.

### Events and phase authority

Every accepted event is committed in one authoritative order. A facilitator-only `advance` with empty payload moves exactly one step from `meaning` to `maker_questions`, then `neutral_questions`, then `permissioned_opinions`, then `complete`. It can occur with no contributions. A participant cannot advance, and the facilitator cannot backtrack or advance after completion.

The other event types are allowed only in their named phase:

| Phase | Actor and event | Exact payload | Rule |
|---|---|---|---|
| `meaning` | Responder `post_meaning` | `{ "value": nonempty text }` | Adds a visible statement. |
| `maker_questions` | Maker `ask_question` | `{ "value": nonempty text }` | Creates a question identified by its accepted event ID. |
| `maker_questions` | Responder `answer_question` | `{ "questionId": ID, "value": nonempty text }` | Question ID must name an accepted maker question; each responder may answer that question once. |
| `neutral_questions` | Responder `ask_neutral` | `{ "value": nonempty text }` | Creates a question identified by its accepted event ID. The host does not judge neutrality. |
| `neutral_questions` | Maker `answer_neutral` | `{ "questionId": ID, "value": nonempty text }` | Question ID must name an accepted neutral question; the maker may answer it once. |
| `permissioned_opinions` | Responder `request_permission` | `{ "topic": nonempty text }` | Creates a request identified by its accepted event ID. |
| `permissioned_opinions` | Maker `decide_permission` | `{ "requestId": ID, "grant": boolean }` | The request must exist and be undecided. One decision per request. |
| `permissioned_opinions` | Requesting responder `post_opinion` | `{ "requestId": ID, "value": nonempty text }` | Requires that specific request's grant; one opinion per granted request. A denial cannot be bypassed by a grant for another request. |

Accepted contributions, decisions, and phase advances appear in `transcript` in commit order. An unanswered or undecided request may remain when the facilitator completes the activity; it grants no permission. Events for a closed phase are rejected. Every event uses an authenticated actor and trusted host time. Accepted event IDs persist: an exact retry returns `replayed`, including after completion; changed reuse returns `rejected`. Rejected requests do not reserve IDs.

Every bound actor sees `{phase, phaseNumber, facilitator, maker, prompts, transcript}`. `phaseNumber` is 1–4 while open and null at completion. The prompts are the package's four phase prompts. Transcript entries contain the accepted event ID, kind, actor, and the event-specific value, link, or decision. The transcript is group-visible immediately. An opinion is absent until a grant and a subsequent accepted `post_opinion`; a pending or denied request contains no opinion text. The host enforces permission at event commit, not merely in the interface.
