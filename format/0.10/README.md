# Activity package format 0.10 candidate

**Status:** Candidate validated in two independent local hosts for text and the specified PNG image subset. It is not yet a published standard.

A Harmonomicon package is data describing a digitally mediated group activity: human directions, participation bounds, provenance, host requirements, and one exact behavior contract. Candidate 0.10 retains the [eight 0.9 contracts and image-reference rules](../0.9/README.md) and the [package exchange rules](../0.4/README.md). Its `format` is exactly `harmonomicon.activity-package/0.10`. Carried examples have new package versions because their format field changed. Hosts report missing contracts or capabilities as `unsupported`.

Candidate 0.10 adds `offered_response_vote@1`. The [image-caption vote](examples/image-caption-vote.json) collects uploaded PNG images, gives each source contributor two saved offers under `policy:balanced_artifacts_exact32@1`, accepts one linked text caption, reveals the images and captions at the response deadline, then accepts votes until a separate vote deadline. The [text response vote](examples/text-caption-vote.json) uses the same stages with text sources. The prior `offered_response@1` contract is unchanged; packages that do not need voting keep its original result rule.

## Package and setup

The behavior object is exactly `{ "contract": "offered_response_vote@1", "sourceMedium": "text" | "image_ref", "allowPromptOverride": boolean, "assignmentPolicy": "policy:balanced_artifacts_exact32@1" }`. It requires `identity@1`, `serial_events@1`, `durable_state@1`, `private_views@1`, `clock@1`, `text@1`, and the named policy. An image-source package additionally requires `image_ref@1` as [defined in 0.9](../0.9/README.md#image-reference-contract).

The organizer supplies the same source setup as `offered_response@1`: canonical unsigned 64-bit participant and round IDs, `opensAt`, `sourceDeadline`, and `responseDeadline`, plus `voteDeadline`. Trusted creation time must be no later than `opensAt`; the four stage times must be strictly increasing and within the safe integer Unix-millisecond range. The organizer may override the initial prompt only if the package permits it. The host validates setup before creating the instance. It does not choose a winner by assessing caption quality.

## Phases and votes

The phases are `waiting`, `sources_open`, `responses_open`, `voting`, and `complete`. Source and response windows are half-open. If fewer than three sources exist at `sourceDeadline`, the phase becomes terminal `insufficient_sources`; offers, voting, and group reveal do not occur. Otherwise source offers and linked responses follow the unchanged `offered_response@1` assignment, submission, and retry rules. At `responseDeadline`, the host reveals accepted sources and captions and opens voting. Missing captions do not delay the phase.

During `[responseDeadline, voteDeadline)`, any bound participant may submit one `submit_vote` with exact payload `{ "responseActor": participant ID }`. The target must be the actor of an accepted caption and cannot be the voter. Participants do not have to submit an image or caption to vote. The first valid vote from an actor wins in the host's authoritative commit order. A second vote is rejected. Exact retries of accepted events return `replayed`, including after the deadline; changed reuse is rejected. At `voteDeadline`, new votes are rejected. The host's `system` actor may record `tick` events at stage boundaries, including after a worker time jump.

All bound actors see `phase`, `sourceCount`, `responseCount`, and `voteCount`. During voting and after completion they see the accepted `sources` and `responses` in accepted order. A participant sees their own vote as `ownVote`; neither the organizer nor other participants see individual ballots. At completion, everyone also sees `scores`: one `{responseActor, votes}` item for every accepted caption, sorted by numeric participant ID. `winners` contains every response actor tied for the largest positive total in that order. If there are no votes, `winners` is empty and scores are zero; if there are no captions, scores and winners are empty. The host never silently breaks a tie. Media byte reads follow the participant views and [0.9 access rule](../0.9/README.md#image-reference-contract).

## Evidence and boundary

The [schema](package.schema.json), [examples](examples/), and [38 conformance cases](conformance/README.md) define nine behavior contracts. Run `python3 format/0.10/check.py` for the reference model. The [two-host trial](../../validation/0.10/README.md) imports the same packages into separate Python and Node.js SQLite services, checks voting traces, concurrent ballots, worker boundaries, private views, restart, stored images, and package transfer.

This is one exact selection policy. It does not define multi-criterion ratings, a reviewer queue, weighted grading, moderator overrides, or the source-specific ranking rules of [ranked game jams](../../research/activities/itch-ranked-game-jam.md) or [Moodle Workshop](../../research/activities/moodle-workshop.md). Those need separate contracts or policies. Offline judging and caption quality remain human matters.
