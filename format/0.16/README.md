# Harmonomicon activity package candidate 0.16

**Status:** Candidate specification with composable runbooks. Fourteen example packages, twenty-two conformance traces, sixty-one invalid-definition witnesses, and cross-family combinations pass independent Python and JavaScript interpreters. Two local SQLite app hosts also pass authenticated views, item and reader races, group privacy, workers, restart, and package transfer. This remains below the broader [1.0 gate](../../ROADMAP.md#goal-for-10).

A package describes an activity through an ordered `runbook.steps` array. Each step selects a versioned operation and supplies its configuration. The app executes the array, including repetition declared by the package. The interpreter dispatches on operation names; it does not select an activity algorithm from the package ID, title, or a complete-game token.

Candidate 0.16 extends [0.15](../0.15/README.md) with bounded integer form fields, item routing, private per-round ratings, exact score aggregation, and explicit ranked publication. Existing operation rules remain unchanged for their previously defined fields. Numeric fields extend this format's field grammar and require `integer_values@1`; older formats do not accept that field kind. The [migration checklist](MIGRATION.md) still records one complete 0.12 translation and nineteen remaining. Scoring is not a new complete-activity contract.

## Start with a package

The [authoring guide](authoring.md) explains how to arrange the operations. The examples are:

| Package | Declared operations |
|---|---|
| [Two Truths and a Tall Tale](examples/two-truths.json) | For each participant: collect visible statements and a private answer; collect other participants' private guesses; reveal both collections. |
| [List Game](examples/list-game.json) | The same operations with five visible items, a hidden text category, and text guesses. |
| [Choice poll](examples/choice-poll.json) | Collect one private choice per participant; close when the organizer advances or one minute passes; reveal; count each option. |
| [See, Think, Wonder](examples/see-think-wonder.json) | Three group-visible response collections, each closed by the organizer. |
| [Timed cumulative story](examples/timed-story.json) | For each participant: append text to the group story or skip the turn after one minute. |
| [Check-in](examples/check-in.json) | Collect private answers until everyone answers or one hour passes; reveal. |
| [Gratitude pool](examples/gratitude-pool.json) | Collect two items per person; repeat claim, acknowledgment, and anonymous reveal for each accepted item. |
| [Partner rounds](examples/partner-rounds.json) | Pause; accept organizer-supplied groups and collect within-group notes for three rounds; close with a whole-group collection. |
| [1-2-4-All](examples/one-two-four-all.json) | Fixed timed invitation and solo/pair/quartet/whole-group text windows with deterministic roster groups. |
| [Pooled ideas and pairs](examples/pooled-ideas-and-pairs.json) | Combine item reading/reveal with paired private reflection, using the same operations. |
| [Scheduled check-in](examples/scheduled-check-in.json) | Wait until the chosen opening; collect private answers until the chosen closing; reveal. |
| [Scheduled check-in and pairs](examples/scheduled-check-in-pairs.json) | Follow the scheduled reveal with private paired reflection. |
| [25/10 digital translation](examples/crowd-scoring.json) | Collect one idea each; declare five routing/rating rounds; scale each exact mean to five ratings; publish ranked results with all cutoff ties. |
| [Peer proposal assessment](examples/proposal-assessment.json) | Two routed rounds on a 0–10 scale; sum scores; publish; continue with private paired reflection. |

The source-derived examples state their digital rules explicitly. The app does not verify real-world truth, infer the meaning of an answer, or grade a creative contribution.

## Package envelope

The top-level fields are exactly `format`, `id`, `version`, `content`, `provenance`, `participants`, `requires`, `settings`, and `runbook`. Unknown or missing fields are invalid. The [JSON Schema](package.schema.json) defines structural rules; [operations.md](operations.md) and the rules below add semantic and runtime requirements. Both apply.

- `format` is exactly `harmonomicon.activity-package/0.16`.
- `id` is a dotted lowercase identifier matching `[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+`. Hyphens are permitted in this candidate to retain earlier package IDs. `version` has three decimal components without leading zeroes, such as `0.1.0`. Together they identify immutable package content.
- `content` has the eight nonempty text fields used in 0.12: `language`, `title`, `summary`, `setup`, `prompt`, `participant`, `completion`, and `access`. They are directions for people, not execution rules.
- `provenance` contains `kind`, `credit`, and `rights`. `kind` is `original` or `adaptation`; an adaptation also requires an HTTP(S) `sourceUrl`. The app checks the declaration's shape, not its legal accuracy.
- `participants.min` and `participants.max` are inclusive integers between 2 and 100, with `min ≤ max`. The organizer is separate.
- `requires` is a unique array of 1–64 exact strings. It must include `identity@1`, `serial_events@1`, `durable_state@1`, `private_views@1`, `clock@1`, `text@1`, every operation used anywhere in the runbook, and each declared policy token. `integer_values@1` is additionally required by `rate@1` and any form declaring an `integer` field. Additional requirement strings may be declared; an app missing any required token returns `unsupported` before creating an instance.
- `settings` declares at most sixteen named `time` or `text` values, or is `{}` when none are needed. A nonempty declaration requires `instance_settings@1`. The binding rules below apply.
- `runbook` contains exactly `steps`. The [operation rules](operations.md) specify allowed steps and references.

Every string must contain Unicode scalar values. Every number must have an integer mathematical value in `0..9007199254740991`; booleans are not numbers. Values written as `100` and `100.0` have the same integer value and canonical representation. Canonical JSON follows 0.12's UTF-8, sorted ASCII member names, escaping, and SHA-256 rules, with all integer-valued numbers emitted as base-ten integers. Arrays retain their order. Package size is at most 1,000,000 canonical bytes. Package object member names are fixed ASCII names or ASCII field names.

## Instances and execution

Creation binds an ordered array of distinct participant IDs, a distinct organizer ID, and a trusted `startedAt` integer. Actor IDs are nonempty Unicode scalar strings; `system` is reserved. The roster order is immutable for the instance. Creation rejects an impossible partition or routing offset for the actual roster, even when its size is within package bounds. Creation checks scheduled boundaries and the clock budget as defined below. Times are trusted integer Unix milliseconds; `startedAt` is instance creation time, not necessarily the first contribution opening.

The app expands each `for_each@1` body once for each participant, in enrollment order. A top-level step's execution key is its `id`. A repeated body's execution key is `id:iteration`, where iteration starts at zero. The current participant is called `turn`. An item loop expands only when its source pool closes, over its accepted items in commit order; it uses the same zero-based body-key syntax and persists the expansion across restart. Execution keys identify one specific invocation; a late submission for `guess:0` cannot become a submission to `guess:1`.

Execution begins at the first step at `startedAt`. A waiting step blocks progression until its close rule fires. Automatic steps run immediately in declared order; they do not require participants to send separate reveal or tally events. There is one active waiting step. After the last step, the instance is complete and keeps its contribution history.

## Saved instance settings

A package declares settings such as:

```json
"settings": {
  "opens_at": {"type": "time"},
  "closes_at": {"type": "time"},
  "question": {"type": "text", "default": "What made you smile today?"}
}
```

Names use the same grammar as step IDs. A declaration has exactly `type` and, optionally, `default`. Only text settings may have a default; it must be nonempty Unicode scalar text. A time setting accepts an integer in the shared safe range. A text setting accepts nonempty Unicode scalar text. Settings without defaults are required. Setup rejects missing, unknown, incorrectly typed, or invalid values before creating state. Omitted instance settings mean `{}`; explicit null or arrays are invalid.

A new scheduled step can reference a value with exactly `{"setting":"name"}`. References are allowed only in `until` and `prompt` on `wait_until@1` or `collect_until@1`, with matching `time` and `text` declarations. These are whole-value references, not string interpolation, JSON paths, expressions, or secret settings. They do not change earlier operation configuration grammar.

The app binds supplied values and defaults once at creation, saves them with instance state, and restores them unchanged after restart. A new package revision or later organizer edit cannot change a running instance's values. Explicit different settings on restore are invalid. Package export includes declarations and defaults, never the values selected for an instance.

Resolved scheduled `until` values must increase strictly in top-level runbook order. The first must be at or after creation. This validates `creation ≤ opening < closing` for the migrated check-in without activity-specific app code. New scheduled steps are top-level only. For safe-clock setup validation, add the maximum of creation and all scheduled boundaries to the sum of relative durations, expanded over the roster and maximum pool quotas; reject if the sum exceeds the safe maximum. This conservative budget can reject some arrangements that would finish earlier.

## Events and time

A reference event has exactly `eventId`, `type`, `actor`, `at`, `step`, and `payload`. `eventId` is a nonempty string. `type` is `submit`, `advance`, `claim`, `partition`, or an internal `tick`. Each operation defines which actions it accepts. `step` must be the current execution key for a participant action. The app authenticates the actor and supplies trusted integer time; participants cannot select their own `actor` or `at`. An internal tick has actor `system`, step `null`, and empty payload. Client actions cannot request a system tick.

Time is nondecreasing. Equal-time requests use authoritative commit order. The app reconciles elapsed deadlines before checking a well-formed event from a bound actor and before returning a view. Thus a late or otherwise forbidden request can close a timed step, but cannot add a contribution. Malformed envelopes, invalid times, and unbound actors are rejected without advancing time.

An active step with a non-null `afterMs` has deadline `min(9007199254740991, openedAt + afterMs)`. Its acceptance window includes the opening instant and excludes the deadline. A relative timeout opens the next step at that deadline, not at the delayed worker's wake time. A single clock jump can therefore close several timed turns. Relative deadlines may saturate at the clock maximum following a late manual transition. A scheduled deadline is its resolved `until` value. If prior work finishes after it, the scheduled step immediately skips; the next opening is the later of its deadline and its actual opening, so progression never rewinds time.

An accepted request returns `accepted`; a forbidden action returns `rejected`. Accepted IDs are stored atomically with their effects. Reusing an accepted ID with identical type, actor, execution key, and JSON payload returns `replayed` with no second contribution, including after the step closes. The retry time may differ but must still be valid and nondecreasing; time reconciliation happens first. Changed reuse is rejected. Rejected IDs are not reserved. Object member order is irrelevant to payload equality; array order and scalar types matter.

## Views and privacy

Only the bound participants and organizer may read a view. The organizer has no special access to private fields. A contributor can see every field of their own entry; other actors can see only fields declared `group`, until an explicit `reveal@1` publishes the source collection. Generic collection counts and step status are group-visible. Routing exposes an item only to its assigned reviewer. A rating record exposes each actor’s own entry; other actors, including the organizer, see no raw ratings, even after result publication. Aggregation remains hidden until `publish_ranking@1` exposes the selected ranked rows and unrated items. Individual rating entries and pool authorship are not revealed by that publication. Pool entries hide author metadata; only their contributor, assigned reader, or the explicit item reveal can expose their text. Group collections expose entries and counts only to members of the partition captured for that collection. The organizer sees the partition map, but cannot read group notes. Later regrouping does not change historical access. These additional rules are defined in [operations.md](operations.md).

The [reference view](runtime.py) contains active phase, execution key, turn actor, prompt, opening time, deadline, ordered records, and cumulative story entries. Completed records remain visible under the same privacy rules. Contribution and story entry order follows accepted event order. Empty private entries are omitted from other actors' views; counts still include them. Tally option order follows the package's option array. An app may render these facts differently, but its authenticated data must preserve the exact content and visibility.

Privacy applies to every app read, cache, export of instance data, and notification. Package export contains definitions, never contributions or instance state. The reference engine's internal state is trusted server storage and is not a participant view or a portable running-instance format.

## Exchange and support

An app advertises the exact format, supported operation tokens, and supported capability and policy tokens. Import validates and stores an immutable `(id, version)` and canonical digest. Identical reimport returns `existing`; changed content at the same identity returns `package_conflict`. Export returns the stored package and digest. Create selects an exact stored identity, binds actors, checks every requirement, and returns sorted missing tokens with `unsupported` before creating any state when support is absent. Invalid package or instance setup is reported explicitly.

Instances remain pinned to the imported identity and digest across restart. A new package revision does not alter a running instance. The [local validation API](../../validation/0.16/README.md) is one transport, not a mandatory API shape. Imported packages may require capabilities that an app does not provide. Unknown operations or operation configurations are invalid under this candidate's schema; known operations may be unsupported by a particular app.

Operation tokens select exact semantics within this candidate. Future changes to their meaning need new tokens; changes to the envelope or reference grammar need a new format identifier. Candidate 0.12 and 0.16 identifiers are distinct, with no implicit migration or alias.

## Verification and remaining scope

Run `python3 format/0.16/check.py` and `python3 validation/0.16/run.py` from the repository root. The [conformance cases](conformance/README.md) give exact event outcomes and privacy/transition witnesses. The latter trial uses independent Python and Node.js SQLite services. Schema checks can additionally run with `--schema` after installing the pinned [validation dependency](requirements-validation.txt).

This candidate has no nested repetition, concurrent branches, arbitrary expressions, persistent open queues, media operations, recurrence, or local-calendar scheduling. Routing is limited to one submitted item per author and distinct non-author roster offsets; it does not supply arbitrary reviewer allocation or exposure-balanced offers. Score aggregation accepts up to ten distinct routed rounds with the same bounds and item source; it is not arbitrary weighted or multi-criterion grading.

The [25/10 notes](scoring-notes.md) distinguish the real face-to-face procedure from the declared digital translation. The [migration checklist](MIGRATION.md) lists one complete migration and nineteen remaining 0.12 examples. The [roadmap](../../ROADMAP.md#path-from-013-to-10) next targets fixed recurrence, occurrence identity, and missed-window recovery, followed by ongoing streams, media, and remaining permissions.
