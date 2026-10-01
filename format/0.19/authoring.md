# Writing a candidate 0.19 package

Start with what the app should record, who may act, who may read it, and how each step ends. Directions explain the activity to people; `runbook.steps` defines the app's actions. Use the [schema](package.schema.json) and [operation rules](operations.md) together.

## Collect and reveal

The [check-in](examples/check-in.json) collects private text from each participant, then reveals it. The [poll](examples/choice-poll.json) adds a tally. The [Two Truths](examples/two-truths.json) and [List Game](examples/list-game.json) repeat collection and reveal for every participant. These retain the five operations introduced in 0.13.

## Two items from each person

The [gratitude pool](examples/gratitude-pool.json) uses this sequence:

1. Collect two independent text items per person, with stable item IDs.
2. Repeat over the accepted items in their accepted order.
3. Let someone other than the author claim the item as its reader.
4. Wait for that reader's acknowledgment.
5. Reveal that item's text without identifying its author.

The repetition body is package data:

```json
{
  "id": "reading",
  "op": "for_items@1",
  "source": "slips",
  "policy": "policy:pool_order@1",
  "steps": [
    {"id":"claim","op":"assign_item@1","policy":"policy:claim_reader@1","prompt":"Claim the next item.","afterMs":30000},
    {"id":"read","op":"acknowledge@1","source":"claim","prompt":"Acknowledge your item.","afterMs":30000},
    {"id":"share","op":"reveal_item@1","source":"read"}
  ]
}
```

This fragment follows a pool named `slips` and belongs inside a full package envelope. Include every operation and policy used in `requires`. A timed-out claim or acknowledgment skips publication of that item. The app records acknowledgment, not whether anyone actually read aloud. Reader claims are not two-source offers and do not ensure balanced exposure.

## Group rounds

A `partition@1` step defines a group's membership; `collect_group@1` refers to it. Choose either consecutive roster chunks of an exact size or a map supplied by the organizer while the activity runs. The [partner rounds](examples/partner-rounds.json) use organizer maps; [1-2-4-All](examples/one-two-four-all.json) uses fixed roster groups and exact durations. Each submission stays visible only to its recorded group, including after regrouping. The organizer cannot read those notes.

Declare the digital choice explicitly: roster chunks are not a universal pairing algorithm. A fixed-size group policy may reject some roster sizes even within the envelope's bounds. Check setup before enrolling people. Group collection is one individual response each; it is not a shared editable document or a synthesized group response.

## Combine operations

[Pooled ideas and pairs](examples/pooled-ideas-and-pairs.json) follows item reveal with a private paired reflection. Both app hosts run this new arrangement without a new complete-activity implementation. This is the authoring goal: change package order and configuration, while apps reuse the operations.

The [migration checklist](MIGRATION.md) separates supported pieces from missing requirements in every older example. Do not approximate a missing rule with prose or count a similar activity as an exact migration. See the [roadmap](../../ROADMAP.md#path-from-013-to-10) for the next work.

## Choose times when starting an instance

The [scheduled check-in](examples/scheduled-check-in.json) declares `opens_at`, `closes_at`, and `question` settings. It waits until opening, collects private answers until closing, then reveals them. A question default is supplied by the package; the times are required. For example, an organizer can select tomorrow's opening and closing and their own question. The app validates the choices before creating the instance and saves them across restart.

A step uses `{"setting":"question"}` as its whole prompt value, or `{"setting":"closes_at"}` as its whole deadline value. This is a typed reference, not executable code or a template language. All declared times must increase in scheduled step order, starting no earlier than creation.

Choose `collect_until@1` when everyone must wait for a fixed closing time. Use `collect@1` when collection should end as soon as everyone answers, or when an authorized person advances. Those are different rules. The [scheduled check-in and pairs](examples/scheduled-check-in-pairs.json) combines the new schedule with existing private group steps; no complete-activity token is needed.

## Route and assess items

The [peer proposal assessment](examples/proposal-assessment.json) has an ordinary text pool, then two route/rate pairs, then aggregation, publication, and private reflection. Each route names its source pool, a unique round ID, and a roster offset. Each rating step names that route, a numeric range, and its close rule. Aggregation explicitly lists the rating step IDs to include. Publication states a rank cutoff and the tie policy.

Repeat a round by adding another route/rate pair with new step and round IDs and a different offset. The package contains this sequence directly; the app does not infer five rounds from an activity name. Numeric scores stay private until totals are published, and individual score records remain private afterward. Use sum or exact scaled-mean policy deliberately: they treat missing ratings differently. Consult the [operation rules](operations.md) for all limits and [example notes](scoring-notes.md) for the digital choices in 25/10.

An `integer` field can also be used in `collect@1` or `collect_until@1`, with declared inclusive `min`/`max` and private or group visibility. Add `integer_values@1` to the package requirements. That does not automatically turn a collection into a scoring or ranking activity.

## Repeat a bounded schedule

Use `for_windows@1` with a declared first opening, fixed interval and window duration, and a count up to 366. Begin its body with one `collect_window@1`, followed by explicit reveal and optional choice tally. Change package data to adjust timing, fields, visibility or the later continuation. A host that lacks either operation reports `unsupported`.

The three daily-practice examples preserve the earlier fixed prompts and day-sized intervals; their `starts_at` setting is chosen at instance creation. Public completion status is explicit via `completion: "group"` and `completion_status@1`. The repeated-poll-and-pairs example chooses `none`, uses private choices and per-window reveal/tally, then continues into pair-private reflection.

Each submission uses a key such as `entry:0`, not an unbound current-day action. Gaps reject new submissions; retries retain the original key and payload. Waiting until the app is next opened does not extend these windows. This schedule does not promise reminders, delivery acknowledgment, local-calendar days, editable running dates, or observation of offline practice.

## Distribute one source and respond

Collect one text source per contributor in a pool, then use `assign_sources@1` with an explicit recipient set and named policy. Choose deterministic `policy:next_nonself_source@1` or randomized `policy:seeded_nonself_source@1`; the latter requires a host supporting `seeded_assignment@1`. Both exclude self, assign one source, allow reuse and skip unmatched recipients. Those are stated rules, not inferred from human instructions.

Follow with `respond@1` and optional `reveal_responses@1`. Recipients respond independently within the same step. Use `deadline` to retain the full response window or `all` to advance after every matched recipient responds. Each submission includes its assigned item ID. A later paired reflection or other supported top-level continuation is package data.

The creative-response example is a text-only simplified source/response activity. It does not reproduce image/audio media, two offered covers, participant choice, late threshold collection, replacement, moderation, host participation or mutable dates. These omissions remain visible in [distribution notes](distribution-notes.md) and the coverage inventory. A simplified useful activity is separate from exact legacy migration or product parity.

## Images in forms

Require `image_contributions@1`, then declare an `image_ref` field in an ordinary, scheduled or recurring form. Use the host's supported upload/processing path and ready receipt; submit `{ref}` after success. Image encoding choices come from the host profile, not the language field. Never place bytes, URLs, readiness/ownership assertions or MIME metadata in the event value. Preserve the upload receipt and event identity for partial-success retries. `private` and explicit reveal work as for other fields; group-immediate recurrence is a distinct deliberate choice. Image-source distribution is not supported by these forms. See [image boundary](image-notes.md), [scheduled image check-in](examples/image-check-in.json) and [image daily prompt](examples/image-daily-prompt.json).
