# Candidate 0.19 runbook operations

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
| `image_ref` | none; requires `image_contributions@1` | Exactly `{ref: string}`; trusted instance/actor image authorization; see [image boundary](image-notes.md). |
|---|---|---|
| `integer` | `min`, `max`, both integers with `0 ≤ min ≤ max ≤ 1,000,000` | Integer-valued number within the inclusive bounds; booleans and fractions are rejected. Requires `integer_values@1`. |
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

`sources` is a unique list of 1–32 preceding `collect@1`, `collect_until@1`, or `collect_window@1` IDs in scope. This automatic step makes every accepted field and actor identity in those source records readable by all bound actors, permanently. It does not collect an event, score an answer, or verify real-world truth. Revealing an empty collection is valid. Repeating a reveal of an already revealed collection has no additional effect. Execution advances immediately.

A package chooses when reveal occurs by placing this step after the appropriate waiting step. For example, placing it after a speaker-controlled guess collection makes the speaker's `advance` trigger reveal and then the next turn.

## `append@1`

Fields: `id`, `op`, `prompt`, `afterMs`.

This waiting step is allowed only within a participant repetition. The current turn actor may submit exactly `{"text": "nonempty text"}`. An accepted submission appends a group-visible entry to the instance's cumulative story and closes the step. Earlier story entries remain visible to every bound actor; the app does not replace the story or ask the actor to resubmit its prior text.

`afterMs` follows the collection duration bounds. A timeout closes the step without an entry and advances to the next step. With `null`, the turn waits indefinitely. There is no manual skip event in this candidate. The story is the ordered list of accepted append entries across all append invocations in the package, with their actor identities. Joining entries into displayed prose is an app presentation choice.

## `tally@1`

Fields: `id`, `op`, `source`, `field`.

`source` names a preceding `collect@1`, `collect_until@1`, or `collect_window@1` in scope. `field` must name one of its `choice` fields. The same sequence must contain an earlier `reveal@1` for that source. This prevents an implicit reveal through aggregate output: the package must publish the source before tallying it.

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

## `wait_until@1`

Fields: `id`, `op`, `until`, `prompt`. Top-level only.

`until` is an absolute trusted Unix-millisecond integer or a whole-value reference to a declared time setting. `prompt` is nonempty text or a reference to a declared text setting. The [instance-setting and schedule validation rules](README.md#saved-instance-settings) apply. The operation displays its prompt and waits until `until`. It accepts no participant or organizer action. At the boundary it closes and continues; if reached late, it immediately continues without rewinding the step opening time. This does not imply a participant is present or has completed offline work.

## `collect_until@1`

Fields: `id`, `op`, `actors`, `prompt`, `fields`, `until`. Top-level only; `actors` is exactly `participants`.

`prompt` and `until` accept the same literals and typed setting references as `wait_until@1`. Structured fields and their visibility use `collect@1`'s field rules unchanged. Each participant may submit one complete declared form. Entries retain actor identity and accepted order; every bound actor sees the count, but only the contributor sees private fields before an explicit reveal. Replacement and extra submissions are rejected; exact accepted retries replay.

The step closes only at the absolute `until` time, accepting submissions in `[actual opening, until)`. It stays open if everyone submits early. No `advance`, `claim`, or `partition` action closes it. A missing answer neither creates an entry nor delays the deadline. A late worker or read closes elapsed steps before processing an event or returning a view. If this step is reached at or after its deadline, it closes empty and continues immediately at the later of opening and deadline.

`reveal@1` may publish its fields and actor identities; `tally@1` may count a declared choice field after explicit reveal in the same sequence. The new source kind extends this format's typed reference grammar; existing operation meanings stay fixed. Cross-step index fields still require the earlier single-turn `collect@1` text-list source. A scheduled collection is not a recurring window or an ongoing stream.

## `route@1`

Fields: `id`, `op`, `source`, `policy`, `round`, `offset`. Top-level only; `source` is an earlier `pool@1` with exactly one item allowed per participant.

`policy` is exactly `policy:roster_offset@1`, required in `requires`. For every accepted pool item, find its author's index `i` in the immutable participant roster of length `N`. Its recipient is roster index `(i + offset) mod N`. `offset` is an integer at least 1 and less than the actual roster length. It must also be below the package maximum roster. Setup rejects an offset that does not fit the actual roster. No hashing, numeric actor-ID conversion, shuffling, or item-ID sorting is involved.

`round` uses step-ID syntax and is unique across the package's routing steps. Offsets for the same source pool must also be distinct. Thus successive routes from that pool give a card different non-author recipients, independent of how many participants submitted. Noncontributors remain eligible reviewers. Every accepted item gets one recipient; because the pool has one item per author, a recipient gets at most one item in a round.

This automatic step saves ordered assignments in pool acceptance order and closes immediately. Its record exposes the round to every bound actor and the assigned item's ID/text only to that recipient. The organizer sees an empty assignment list. The pool still exposes a contributor's own items under its earlier rules. Later routes do not revoke earlier knowledge or access to an actor's own assignment records. Assignment views omit authorship metadata.

## `rate@1`

Fields: `id`, `op`, `source`, `prompt`, `min`, `max`, `close`, `afterMs`. Top-level only; `source` is an earlier `route@1`.

`prompt` is nonempty literal text. `min` and `max` use the numeric form bounds, `0 ≤ min ≤ max ≤ 1,000,000`. This operation requires `integer_values@1`. The step captures its route's saved assignments and round. Only an assigned recipient may submit exactly `{itemId, round, score}`. The item and round must match the assignment, and score must be an integer-valued number within the inclusive bounds. One accepted score is allowed per actor in this invocation. Wrong-item, wrong-round, stale-key, fractional, Boolean, and replacement submissions are rejected. Accepted retries use the shared ledger rules.

`close` is `all` or `deadline`; `afterMs` must be a non-null integer from 1 through 86,400,000. `all` closes after all assigned recipients score, or at timeout. `deadline` waits until timeout even if all have scored. Missing ratings create no entry and do not extend the deadline. An empty assignment list immediately skips. These rules apply at events, reads, and worker reconciliation.

Views expose the total accepted count, each actor's own score entry, and their own assignment only. The organizer has no private-score access. Raw score entries remain private after aggregation and ranking publication. The app cannot prevent someone remembering or communicating their own score; it does not expose other people's score records through this operation.

## `aggregate@1`

Fields: `id`, `op`, `sources`, `policy`, `targetCount`. Top-level only.

`sources` lists 1–10 unique earlier `rate@1` IDs. Their routes must be distinct, refer to the same pool, and all ratings must have identical numeric bounds. Each accepted score is counted once. Source arrays select the included rounds explicitly; other ratings in the package are not implicitly included. The operation automatically computes one internal row per accepted pool item, in pool acceptance order: `{itemId, text, count, total, score}`. Author and individual reviewer metadata are omitted. A row with no scores has `count: 0`, `total: 0`, and `score: null`; it is unrated, not a zero-rated result.

The exact policy must be in `requires`:

- `policy:sum_scores@1`: `targetCount` must be `null`. Score is the sum of accepted scores.
- `policy:mean_scaled_scores@1`: `targetCount` is an integer from 1 through 100. Score is `total × targetCount / count` when count is nonzero. Missing ratings are excluded from the mean, rather than converted to zero.

Represent every non-null score as reduced `{numerator, denominator}` integers with nonnegative numerator and positive denominator; reduce by their greatest common divisor. Zero reduces to `0/1`. Do not compute or store a rounded floating-point average. At most ten scores of at most one million each contribute to an item, so total is at most ten million, scaled numerator is at most one billion before reduction, and exact ranking cross-products are at most ten billion. These fit the shared safe integer range in both languages.

The record closes automatically but exposes no computed rows to any actor until explicit ranked publication. Directions or calculation alone do not reveal it. `reveal@1` cannot target an aggregate.

## `publish_ranking@1`

Fields: `id`, `op`, `source`, `limit`, `policy`. Top-level only; `source` is an earlier `aggregate@1`. Only one publication for that aggregate is allowed in a package.

`limit` is an integer from 1 through 100. `policy` is exactly `policy:competition_rank_all_ties@1`, required in `requires`. Sort scored rows by descending exact rational value, comparing cross-products. Equal scores retain original pool acceptance order for display. Tied rows have the same competition rank: 1, 2, 2, 4. Publish every row whose rank is at most `limit`, including every tie at the boundary; the number of rows can therefore exceed the limit. This limit is a rank cutoff, not a tie-breaking rule.

Automatically expose `ranking` with each selected row and its rank, plus `unrated` with every no-score row in pool acceptance order. Both are visible to all bound actors, including the organizer. Do not assign unrated rows a rank or an invented average. Lower-ranked scored rows are omitted from this projection. The underlying pool, assignment, and individual rating projections keep their own privacy rules; publication does not expose authorship or raw individual ratings. Empty inputs publish empty arrays. The operation continues immediately.

## `for_windows@1`

Fields: `id`, `op`, `startsAt`, `intervalMs`, `windowMs`, `occurrences`, `prompt`, `steps`. Top-level only.

`startsAt` is an absolute safe integer Unix-millisecond time or a declared time setting reference. `prompt` is nonempty text or a declared text reference, shown while waiting for an opening. `intervalMs` is an integer in `1..9007199254740991`; `windowMs` is an integer in `1..intervalMs`. `occurrences` is an integer in `1..366`. Instance setup validates the exact final close `startsAt + (occurrences - 1) * intervalMs + windowMs` and rejects overflow before creating state. The first opening follows the top-level schedule validation rules in the specification. These are fixed elapsed intervals, not local calendar dates or delivery-triggered timers.

The nonempty body begins with exactly one `collect_window@1`; remaining steps may only be `reveal@1` and `tally@1`. References within the body refer only to earlier steps in that body; they never cross occurrences. Nested repetition and references from outside the container into the body are invalid. Body definitions have globally unique IDs; execution keys append the occurrence index. The container's own waiting frame and body frames carry immutable planned opening/closing metadata.

Wait for each planned opening, then execute its body. Automatic reveal/tally run at collection closing, before the next wait or following top-level step. Contiguous windows accept a new action only under the next occurrence key at the shared boundary. Clock jumps process all elapsed windows, including empty ones. A later top-level step starts after the final body completes. This operation never reschedules missed windows or implies notification delivery.

## `collect_window@1`

Fields: `id`, `op`, `actors`, `prompt`, `fields`, `completion`. Window-body only, first and unique collection in that body.

`actors` is exactly `participants`. `prompt` is nonempty text or a declared text setting reference. `fields` follows the structured field rules of `collect@1`, including private/group visibility and optional bounded integers with `integer_values@1`. Each participant may submit one complete form per occurrence. Acceptance binds to the current execution key; replacement and extra submissions reject. The fixed container closing is the exclusive deadline. Everyone answering early does not close it; organizer `advance` is forbidden.

`completion` is `none` or `group`. `none` omits per-person statuses while retaining the usual collection count. `group` requires `completion_status@1` and publishes roster-ordered `{actor,status}` rows: `complete` after that actor submits, otherwise `pending` while open and `missed` after closing. It exposes no private form value. Counts, own values, and visible group fields retain accepted-event order.

`reveal@1` may publish this occurrence's fields and actor identities. `tally@1` may count a choice field after explicit reveal in the same body, using the existing exact option-order rules. These source-kind extensions change the candidate reference grammar, not the prior operation semantics. Window collection is neither an ongoing multi-entry stream nor independent per-participant stage progression.

## `assign_sources@1`

Fields: `id`, `op`, `source`, `recipients`, `policy`, `cardinality`, `reuse`, `unmatched`. Top-level only.

`source` names an earlier closed `pool@1` with `perActor: 1`. The immutable candidate items are that pool's accepted items in commit order; no absent quota slot becomes a source. `recipients` is `participants` (the full roster) or `contributors` (participants with an accepted source), in immutable roster order. The organizer is never a recipient. Every policy excludes items authored by that recipient.

`cardinality` is exactly `one`: each matched recipient gets one source. `reuse` is exactly `allowed`: the same source may be assigned to different recipients; assignments do not consume it or promise equal exposure. `unmatched` is exactly `skip`: a recipient with no non-self candidate is recorded unmatched and receives no assignment. No own-source fallback is invented. An empty contributor pool has no eligible recipients; an empty participants pool has every participant eligible but unmatched. One source leaves its author unmatched and may serve other eligible participants.

Choose one exact policy and declare it in `requires`:

- `policy:next_nonself_source@1`: select the eligible source whose author has the smallest positive forward distance from the recipient in the immutable roster, wrapping at its end. Missing contributors are skipped. One source per author makes the choice unique. Source commit order does not affect this policy.
- `policy:seeded_nonself_source@1`: use the versioned sampler below to select from the recipient's non-self candidates in pool commit order. Process recipients in roster order. No candidate means no draw; a single candidate is assigned without a draw. This policy also requires `seeded_assignment@1`.

Materialize the full assignment once, persist it, mark the automatic step closed and continue. Source author metadata is stored internally but omitted from private assignment projections. The actor view shows only that actor's `eligible`, `unmatched`, and nullable `{itemId,text}` assignment; it never includes the full map or generator state. Each new assignment operation consumes the continuing instance generator stream, not a reset to the initial seed.

### Exact seeded sampler

The initial trusted integer seed is in `1..4294967295`; it initializes the internal `randomState`. A draw applies unsigned 32-bit xorshift in this order: `x ^= x << 13`, `x ^= x >>> 17`, `x ^= x << 5`, masking to 32 bits after each operation. Save the resulting nonzero `x`. To choose among `n > 1` candidates, set `value = x - 1` and `limit = 4294967295 - (4294967295 % n)`. Accept `value % n` only if `value < limit`; otherwise draw again. Rejected draws also advance saved state. No seed zero coercion or silent default is permitted in the reference runtime.

Seed 1 produces `270369, 67634689, 2647435461, 307599695` for its first four draws. With four sources in roster/commit order A,B,C,D, recipient order a,b,c,d and self-exclusion, the assignments are D,A,D,B. Seed `1584200935` first draws `4294967295`; a two-candidate sample rejects that draw, then draws `253983` and chooses index zero. The [checker](distribution_check.py) tests these vectors and consumed state in both implementations. This is a precise seeded sampling policy, not a claim of cryptographic randomness or exposure fairness.

## `respond@1`

Fields: `id`, `op`, `source`, `prompt`, `close`, `afterMs`. Top-level only. `source` names an earlier `assign_sources@1`. `prompt` is nonempty text; `close` is `all` or `deadline`; `afterMs` is an integer in `1..86400000`.

Snapshot the saved assignments. Each assigned recipient may submit exactly `{itemId,text}` once, with the assigned item ID and nonempty Unicode scalar text. A wrong/unassigned/self-source ID, ineligible actor, extra field, empty text, or replacement rejects. The organizer cannot submit. An accepted response stores the actor and immutable `{actor,itemId,text}` source relation, preventing a client from substituting a different source value or author. Accepted retry identity uses the standard execution key and JSON payload rules.

All recipients act independently in this single shared response step. One actor's response does not wait for another actor to choose or respond; there is no serial `for_each@1` body or new general parallel execution model. `all` closes when every matched recipient has answered; unmatched recipients do not block it. `deadline` remains open until timeout even if all answer early. The trusted exclusive relative deadline and clock-jump rules are unchanged. No assignments means immediate empty completion. Manual organizer advance is forbidden.

Counts are group-visible; before explicit publication, an actor sees only their assigned `{itemId,text}` and own response, with source-author metadata omitted. Missing replies create no result and do not reveal an unanswered source. Retained private responses remain private after completion if no publication step follows.

## `reveal_responses@1`

Fields: `id`, `op`, `source`. Top-level only; `source` names an earlier `respond@1`. Automatically mark that response record revealed and continue.

Publish its accepted entries to all bound participants and the organizer in commit order: `{actor, source:{actor,itemId,text}, text}`. Source author and responder attribution are explicit parts of this reveal. The original source pool is not globally revealed; missing responses and unmatched recipients create no published pair. Previously granted private source knowledge is retained. This operation does not publish posts, media bytes, board squares or chat cards in an app.

## Typed image fields (candidate 0.19)

`collect@1`, `collect_until@1` and `collect_window@1` accept an exact field `{type: "image_ref", visibility: "private"|"group"}` when `image_contributions@1` is required. The value is exactly `{ref: <nonempty scalar string, at most 256 code points>}`. Before a new acceptance the trusted instance-bound host authority must affirm ready immutable image content, submitting actor ownership and this instance. No client readiness/MIME/owner assertion grants authority. Invalid fields reject the entire form, preserving existing quota/deadline/privacy semantics; accepted retries replay their frozen identity before new authority checks. Reads and bytes remain host responsibilities. [The complete boundary](image-notes.md) specifies discovery, partial-success retries, concealment/reveal and local PNG limits. Other media and image pools/routing/group forms remain unsupported.
