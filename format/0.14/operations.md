# Candidate 0.14 runbook operations

These rules define how an app executes package data. Operation implementations are reusable app code; the activity's order and configuration are supplied by the package. All shared [event, time, identity, and privacy rules](README.md) apply.

## Sequence, scope, and references

A sequence contains 1–32 ordered steps. A package contains at most 64 declared step IDs, globally unique, each matching `[a-z][a-z0-9_]{0,47}`. Every step has `id` and `op`, with exactly the additional fields below. `for_each@1` and `for_items@1` may occur only at the top level. Neither can contain any repetition. Multiple top-level repetitions are allowed.

A reference names a preceding step of the required type in the same sequence or an earlier top-level step inherited by a repetition body. It resolves to the current iteration's record for a body step, or the single record for a top-level step. A reference cannot point forward, select a previous iteration, or escape a repetition body into a later top-level step. These constraints prevent ambiguous references when a collection is repeated. References and type compatibility are validated before execution; they are not arbitrary JSON paths or expressions.

## `for_each@1`

Fields: `id`, `op`, `over`, `steps`.

`over` is exactly `participants`. `steps` is the body sequence. The app expands it once per participant in immutable roster order. Within the body, `turn` means that participant and `others` means every other participant. Each iteration completes before the next begins. No event is needed for the repetition itself.

## `collect@1`

Fields: `id`, `op`, `actors`, `prompt`, `fields`, `close`, `afterMs`.

`actors` is `participants`, or within a repetition body `turn` or `others`. `prompt` is nonempty text. `fields` defines 1–8 named fields. Field names use the step-ID syntax. Every field has `visibility`, either `group` or `private`, plus exactly the type-specific fields:

| Type | Additional configuration | Accepted value |
|---|---|---|
| `text` | None | Nonempty Unicode scalar string. |
| `text_list` | `count`, an integer from 1 through 32 | Exactly that many nonempty text strings, in order. |
| `choice` | `options`, 2–32 distinct nonempty strings | One exact option string; no trimming or case folding. |
| `index` | `indexOf` | Zero-based integer index into the referenced text list. |

`indexOf` is either a field name in the same submitted form, or `stepId.fieldName` referring to a preceding collection. A local source must have type `text_list`. A preceding source must collect from `turn`, have a `group` text-list field, and satisfy the scope rules above. This makes its list unambiguous and visible to the people choosing an index. If a preceding source timed out with no contribution, no index guess is valid; the collection may still close manually or on its own deadline.

A `submit` payload is an object with exactly the declared field names. The app validates all fields before storing any of them. Thus visible statements and their private answer are committed together. Each eligible actor may submit once in this invocation. Edits and replacement submissions are rejected. Accepted entries retain their actor identity and accepted order. Every actor can read the collection's accepted-entry count.

`close` is one of:

- `all`: close immediately after every eligible actor has submitted.
- `organizer`: remain open until the organizer sends `advance` with an empty payload, even if everyone has submitted.
- `turn`: within a repetition body, remain open until the current turn actor sends `advance` with an empty payload.

Manual advance may close an empty collection. `advance` is rejected for `close: all`. Closing omits missing entries and keeps accepted ones. Closing does not itself reveal private fields.

`afterMs` is `null` or an integer from 1 through 86,400,000. A non-null duration supplies an additional close trigger regardless of `close`. A deadline closes with the entries accepted before it. A null duration has no timeout: a collection can remain open indefinitely if its completion condition never occurs. After closing, execution advances to the next declared step.

## `reveal@1`

Fields: `id`, `op`, `sources`.

`sources` is a unique list of 1–32 preceding collection IDs in scope. This automatic step makes every accepted field and actor identity in those source records readable by all bound actors, permanently. It does not collect an event, score an answer, or verify real-world truth. Revealing an empty collection is valid. Repeating a reveal of an already revealed collection has no additional effect. Execution advances immediately.

A package chooses when reveal occurs by placing this step after the appropriate waiting step. For example, placing it after a speaker-controlled guess collection makes the speaker's `advance` trigger reveal and then the next turn.

## `append@1`

Fields: `id`, `op`, `prompt`, `afterMs`.

This waiting step is allowed only within a participant repetition. The current turn actor may submit exactly `{"text": "nonempty text"}`. An accepted submission appends a group-visible entry to the instance's cumulative story and closes the step. Earlier story entries remain visible to every bound actor; the app does not replace the story or ask the actor to resubmit its prior text.

`afterMs` follows the collection duration bounds. A timeout closes the step without an entry and advances to the next step. With `null`, the turn waits indefinitely. There is no manual skip event in this candidate. The story is the ordered list of accepted append entries across all append invocations in the package, with their actor identities. Joining entries into displayed prose is an app presentation choice.

## `tally@1`

Fields: `id`, `op`, `source`, `field`.

`source` names a preceding collection in scope. `field` must name one of its `choice` fields. The same sequence must contain an earlier `reveal@1` for that source. This prevents an implicit reveal through aggregate output: the package must publish the source before tallying it.

The step automatically creates group-visible `counts`, one `{value, count}` per option, in the package's option order. Count each accepted entry once; omit missing entries. Counts are exact nonnegative integers. An empty collection produces a zero for every option. Ties remain visible in the counts; this operation does not select a winner. Execution advances immediately.

## `pool@1`

Fields: `id`, `op`, `prompt`, `perActor`, `close`, `afterMs`. Top-level only.

Each participant may submit `perActor` independent items, an integer from 1 through 8. A payload is exactly `{itemId, text}`, both nonempty Unicode scalar strings. An item ID is unique across the entire invocation, not just its author. One accepted submission stores one immutable item; replacement and quota overflow are rejected. Entries retain authoritative accepted-event order. All bound actors see the total count. An actor sees their own item IDs and text; author identities are never included in projected pool entries.

`close` is `all`, `organizer`, or `deadline`. `all` closes when every participant fills their quota. `organizer` waits for organizer `advance` with `{}`. A non-null `afterMs` also closes either mode on timeout. `deadline` closes only on timeout and requires a non-null duration. Duration bounds are 1–86,400,000 ms or `null`. Empty or partial pools close without invented items.

## `for_items@1`

Fields: `id`, `op`, `source`, `policy`, `steps`. Top-level only; `source` is an earlier `pool@1`.

`policy` is exactly `policy:pool_order@1`. Its input is the closed pool's accepted items. Its output is that same list in accepted commit order, with no shuffle or sort by ID. Expand the body once per item when this step executes. Persist that ordered snapshot and each item's source/ID binding. The body has keys `id:iteration`; item identity itself is not an execution key. Missing quota slots create no iteration, and an empty pool immediately continues. No participant action selects the next item. The policy token must appear in `requires`.

## `assign_item@1`

Fields: `id`, `op`, `policy`, `prompt`, `afterMs`. Item-loop body only.

`policy` is exactly `policy:claim_reader@1`, required in `requires`. Its inputs are the current item author, bound participant roster, and ordered authenticated requests. Eligible readers are all participants except the author. The first accepted `claim` with `{}` sets the one reader and closes the step atomically. The organizer and author cannot claim. A competing new request to the old execution key is rejected; an exact accepted retry replays. All views expose the reader ID and current eligibility through `canClaim`. Only the assigned reader's assignment record includes the item's ID and text. This is reader assignment, not a transfer that erases the author's knowledge.

`afterMs` uses the shared nullable duration bounds. A timeout records no reader and proceeds; `null` may wait indefinitely. There is no substitute-reader routing policy in this version.

## `acknowledge@1`

Fields: `id`, `op`, `source`, `prompt`, `afterMs`. Item-loop body only; `source` is an earlier `assign_item@1` in scope.

Only that assignment's reader may send `advance` with `{}`. Acceptance records `acknowledged: true` and closes. A timeout closes with false. If assignment produced no reader, the step immediately skips with false. Duration bounds are shared and nullable. The view exposes reader and acknowledgment status to all bound actors, but no additional item text. An acknowledgment is an app action, not proof of speech or any physical action.

## `reveal_item@1`

Fields: `id`, `op`, `source`. Item-loop body only; `source` is an earlier `acknowledge@1` in scope.

If the referenced acknowledgment is true, automatically publish that assigned item's ID and text in its source pool for all bound actors, permanently. Otherwise publish nothing and continue. Author metadata remains concealed. An already-published item remains published. This permits staged reveal without exposing the entire pool or revealing skipped items.

## `partition@1`

Fields: `id`, `op`, `policy`, `minSize`, `maxSize`, `prompt`, `afterMs`. Top-level only.

Group sizes are inclusive integers from 1 through 100; `maxSize` cannot exceed the package's maximum roster. Each invocation produces an immutable ordered list of groups. Each policy must be in `requires`:

- `policy:roster_chunks@1`: `minSize` must equal `maxSize`; `afterMs` must be `null`. Automatically divide immutable roster order into consecutive groups of that size. At least one roster size within package bounds must divide evenly. Actual instance setup must divide evenly; there is no leftover group or implicit reassignment.
- `policy:organizer_groups@1`: wait for organizer `partition` with exactly `{groups: [[actorId, ...], ...]}`. The groups must cover every bound participant exactly once, contain no outsiders or empty groups, and meet the size limits. Preserve declared group and member order. Invalid submissions do not change the map. The first accepted map closes the step. `afterMs` may be null or a shared bounded duration; timeout produces an empty map.

Setup rejects any roster size that cannot be covered by groups within the declared bounds. Automatic grouping is a digital choice, not a claim that a source activity prescribes that algorithm. Organizer maps allow explicit human regrouping; the package does not enforce diversity or prohibit repeated partners. Only the organizer sees the full map. Participants see their own group. Later partitions do not mutate earlier maps.

## `collect_group@1`

Fields: `id`, `op`, `source`, `prompt`, `close`, `afterMs`. Top-level only; `source` is an earlier `partition@1`.

Snapshot that partition's groups. Each participant in a group may submit exactly `{text}` with nonempty Unicode scalar text once. A contributor's entries, actor identities, and accepted count are visible only within their captured group. The organizer is separate from all groups: the collection projects empty members and entries and a count of zero to the organizer. Historical access retains that snapshot after later regrouping. `reveal@1` cannot refer to this operation.

`close` and `afterMs` follow the pool's `all`, `organizer`, and `deadline` rules, except `all` requires one response per grouped participant. An empty partition immediately skips. A deadline closes with optional partial notes and preserves within-group privacy. There is no representative selection, group-owned response, or synthesis inferred from these individual notes.

## `pause@1`

Fields: `id`, `op`, `prompt`, `afterMs`.

Display the prompt until the shared relative deadline; `afterMs` must be a non-null duration from 1 through 86,400,000 ms. No participant or organizer event closes this step. At timeout continue at the original deadline. This can precede the first collection or separate rounds. It neither observes offline work nor guarantees presence.
