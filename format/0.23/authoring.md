# Writing a candidate 0.23 activity

Describe what people will contribute, who may act/see it, when collection closes and what happens next. Keep those meaningful choices in package data; hosts implement storage, accounts, media and interface details.

## One pool, separate kinds and limits

Use `pool@2` for new typed pooling. “Accept text and audio” and “allow up to two contributions per person” are independent settings:

```json
{"id":"pieces","op":"pool@2","prompt":"Offer up to two pieces.","kinds":["text","audio"],"perActor":2,"visibility":"private"}
```

Each person can contribute zero, one or two items total across both kinds. Each item has its own stable ID. A filled limit does not close the host-scheduled window early. Optional named `round` and qualified `input` support continuation; ordinary pooling needs neither. A host must support the operation, declared media capabilities and trusted controls before starting it.

The [written-idea poll](examples/text-pool-vote.json) allows three text contributions, the [image poll](examples/image-pool-vote.json) one image, and [audio sharing](examples/audio-pool-sharing.json) two recordings. No separate type-specific pool is needed to change the limit.

## Read/play and share every accepted item

The [mixed sharing activity](examples/typed-sharing.json) follows collection with `for_items@2`. The body says: let a non-author claim this contribution, wait for acknowledgment, then share it with attribution. Accepted eligible items run in acceptance order; missing slots do not appear. Apart from its author, only the assigned reader sees the private piece before successful acknowledgment publishes it. A timeout skips publication; an assigned reader keeps their saved access. A group without any possible non-author reader skips that item immediately.

Only frozen source-effective actors may claim, including those who contributed nothing. Organizers have no role bypass; a participating organizer follows the same membership rule. These new typed operations deliberately preserve attribution. Use the retained anonymous text [gratitude example](examples/gratitude-pool.json) when that older author-concealment/closing contract is intended.

Ordinary item-body collect/reveal/tally/pause instructions remain available under their existing rules. For example, after sharing, ask people for a written continuation. That body collection still runs when a reveal was skipped; phrase the prompt to handle that path. Outputs stay within their iteration; there is no hidden workflow or general exported body result.

## Choose one outcome

The new qualified voting chain votes on every actual item, not a copied label or one slot per author. Choose whether people may change their one current vote and whether ballots stay private. Count, apply most-votes and a tie/no-vote policy, then present the structured output. Public counts never silently reveal private individual ballots.

[Typed continuation](examples/typed-continuation.json) starts from a declared actual contribution, accepts up to two possible continuations per person, selects and presents material, then supplies that actual selection to a written next round. Wrong/stale references reject. An empty candidate pool remains no_candidates; unresolved results block only dependent collection, not later instructions. Explicit random/no-vote fallback and retention keep their precise 0.22 boundaries.

Predefined options still use the retained [poll](examples/predefined-vote.json). Old operation versions keep their source types; do not merely point an old text consumer at a new pool. Use the compatible new versions and validate the complete source graph before execution.

## Assign one source and respond

The [workshop](examples/typed-response-workshop.json) collects up to two mixed pieces, assigns one non-self source to each effective person, accepts one independent response, reveals used source/response pairs, then forms private pairs. Several source items do not create duplicate recipients or extra responses. New deterministic policy chooses the next eligible author and their first accepted item. Random item sampling is another explicit policy; more submitted items may mean more exposure, with no balancing claim.

Assignments preserve real source identity, author and value. Responses must reference the actual saved qualified source. Seeing media grants viewing access, not ownership for submission. Unused private pieces remain private even after linked reveal. Use an even roster for the example's exact pairs; pair notes remain with their recorded membership.

## Keep the host boundary visible

The host resolves dates, eligible actors, authoritative starting material, immutable media and access for every viewer. It renders/plays results and decides whether to start another instance. Input origin and the decision handing material onward remain distinct. Notifications do not guarantee attention, acknowledgment does not prove listening, and package transfer does not move live state/blobs.

See [pooling rules](pooling-notes.md), [retained operation reference](operations.md), [input contract](input-notes.md), [supported profile](readiness-assessment.md), [compatibility](COMPATIBILITY.md) and [migration accounting](MIGRATION.md). Existing collection, hidden-answer, groups, scheduling, scoring, recurrence and linked-response examples remain executable with their retained versions; their detailed authoring history is documented in [0.22](../0.22/authoring.md).
