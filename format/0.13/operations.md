# Candidate 0.13 runbook operations

These rules define how an app executes package data. Operation implementations are reusable app code; the activity's order and configuration are supplied by the package. All shared [event, time, identity, and privacy rules](README.md) apply.

## Sequence, scope, and references

A sequence contains 1–32 ordered steps. A package contains at most 64 declared step IDs, globally unique, each matching `[a-z][a-z0-9_]{0,47}`. Every step has `id` and `op`, with exactly the additional fields below. `for_each@1` may occur at the top level and cannot contain another `for_each@1`. Multiple top-level repetitions are allowed.

A reference names a preceding collection step in the same sequence or an earlier top-level collection inherited by a repetition body. It resolves to the current iteration's record for a body step, or the single record for a top-level step. A reference cannot point forward, select a previous iteration, or escape a repetition body into a later top-level step. These constraints prevent ambiguous references when a collection is repeated. References and type compatibility are validated before execution; they are not arbitrary JSON paths or expressions.

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
