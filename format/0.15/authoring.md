# Writing a candidate 0.15 package

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
