# Activity package format 0.6 candidate

**Status:** Candidate validated in two independent local hosts for text packages and package transfer. It is not a published standard.

A Harmonomicon package contains human directions, participation bounds, provenance, exact host requirements, and one behavior contract for a digitally mediated group activity. Candidate 0.6 retains the [0.5 behavior contracts](../0.5/README.md) and [0.4 exchange rules](../0.4/README.md) unchanged. Its `format` value is exactly `harmonomicon.activity-package/0.6`; copied examples have new package versions because their format field changed. Hosts must report an unknown behavior or missing capability as `unsupported`, not reinterpret it.

0.6 adds `ongoing_space@1`: an activity with retained text entries, per-entry privacy, comments on shared entries, and either an unscheduled open period or a finite prompt series. This defined digital behavior responds to the [shared-journal and creative-practice cases](../../research/creative-jams-and-shared-practice.md) and the [coverage audit](../../COVERAGE.md). It does not assert that Waffle, Day One, Jamuary, or another named service uses this exact contract.

## Package and schedule

The behavior is `{ "contract": "ongoing_space@1", "allowPromptOverride": boolean, "schedule": ... }`. It requires `identity@1`, `serial_events@1`, `durable_state@1`, `private_views@1`, `clock@1`, and `text@1`.

- `{"kind":"open"}` lets participants post during one `[startsAt, endsAt)` period. The organizer supplies both trusted times at instance creation, with `createdAt ≤ startsAt < endsAt`. It can be a long period, but the end must be within the safe integer millisecond range.
- `{"kind":"fixed_prompt_series","intervalMs":n,"windowMs":n,"prompts":[...],"statusVisibility":"none"|"group"}` defines 2–366 nonempty text prompts. `intervalMs` is positive; `windowMs` is positive and no greater than `intervalMs`. The organizer supplies `startsAt` no earlier than creation. Occurrence `k` opens at `startsAt + (k − 1) × intervalMs` and closes `windowMs` later; the final close must fit the safe integer range. Windows do not overlap. The prompt at array index `k − 1` belongs to occurrence `k`.

A prompt override at creation is permitted only if `allowPromptOverride` is true. It changes the package's general `content.prompt`, not the fixed series array. Prompts are package data and may be visible to someone who can export the package; this contract does not promise surprise or secrecy for later prompts.

The `open` schedule has phases `waiting`, `open`, and `complete`. The fixed series has `waiting`, `open` during a window, `between` in a gap, and `complete` at or after the final close. `currentOccurrence` is the one-based open number or null. The host advances phases before every event and view; delayed workers cannot extend a window. Workers should wake at each opening and closing, including boundaries crossed in one delayed jump. Fixed intervals measure elapsed milliseconds, not local-calendar days across daylight-saving changes.

## Entries and comments

A participant can make any number of accepted `post_entry` events during `open`. The event ID becomes the entry ID. For the open schedule, the exact payload is `{ "audience": "private" | "group", "value": text }`. For a fixed series it is `{ "occurrence": current number, "audience": "private" | "group", "value": text }`. The occurrence number is mandatory so a delayed request cannot silently post to a later prompt. A text value is nonempty; there is no word-count or quality test. An entry stores `{id, actor, occurrence, audience, value, comments}` in authoritative acceptance order. `occurrence` is null for an open schedule, and `comments` begins empty.

A participant can `comment` with `{ "entryId": accepted entry ID, "value": text }` on a `group` entry while the activity is `open` or `between`. Comments are accepted in a gap so conversation can continue between prompts. They are rejected before opening, at or after completion, and on private or unknown entries. Each accepted comment is appended as `{actor, value}` to its entry. The organizer can read shared entries but is not a participant and cannot post or comment.

`tick` with empty payload is accepted only from the host's reserved `system` actor. These three event types—`post_entry`, `comment`, and `tick`—are the only ones for this contract. Actors and time are trusted host inputs, not client assertions. All accepted event IDs are durable: an exact retry returns `replayed` without another entry or comment, even after the window closes; changed reuse returns `rejected`. A rejected action changes no contribution, though its trusted time can still advance the phase.

## Audience views and status

Every bound actor sees `phase` and an `entries` array in accepted order. It contains all group entries and, for a participant, that participant's own private entries. The organizer sees group entries only. Comments on a group entry appear with that entry as soon as accepted. Private content must not leak through activity views, caches, or notifications.

For a fixed series, every view also contains `currentOccurrence` and an `occurrences` array for every occurrence that has opened, in number order. Each item includes `{number, prompt, phase}`; item phase is `open` until its close and `closed` afterward. When `statusVisibility` is `group`, each item also includes `statuses` in participant enrollment order. A status is `complete` after that participant makes at least one accepted entry in the occurrence, even if the entry is private; otherwise it is `pending` while open and `missed` after close. This deliberately reveals completion without revealing the entry. With `statusVisibility: "none"`, no status or missed-day signal is emitted. A soft prompt invitation should use `none` rather than silently imposing a penalty.

Membership is fixed for the instance. Entries and comments remain in history across occurrences. The contract has no edit, deletion, moderation, reactions, nested threads, attachment storage, local-calendar schedule, notifications, or host verification of work done away from the app. Hosts may provide these separately only with clear capability and audience rules; they are not implied by `ongoing_space@1`.

## Evidence

The [0.6 schema](package.schema.json), [examples](examples/), and [22 conformance cases](conformance/README.md) cover the six behavior contracts. Run `python3 format/0.6/check.py` for the reference model. The [two-host local trial](../../validation/0.6/README.md) imports the same packages into independent Python and Node.js SQLite-backed hosts, runs all 22 cases, and probes time jumps, concurrent entries, private reads, restart, and package transfer. The result supports the checked-in text packages and local operations; it does not establish media storage, calendar scheduling, public deployment, or every researched activity.
