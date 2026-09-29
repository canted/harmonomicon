# Activity package format 0.5 candidate

**Status:** Candidate validated in two independent local hosts for text packages and package transfer. It is not a published standard.

A Harmonomicon package describes a digitally mediated group activity as data: directions, participant bounds, provenance, exact host requirements, and one behavior contract. Candidate 0.5 retains the [0.4 package exchange and runtime rules](../0.4/README.md), including immutable `(id, version)` identity, capability discovery, import, export, canonical digest, authenticated actors, trusted time, durable event IDs, and audience views. The `format` value is exactly `harmonomicon.activity-package/0.5`; changed example packages use new package versions. The four previous behavior tokens retain their exact semantics and the [0.3 runtime definitions](../0.3/README.md). A host must report an unsupported token instead of substituting another contract.

This candidate adds `project_cycle@1` for a fixed set of teams that make progress posts during a work window, submit final work, and review other teams during a later window. It is a defined digital procedure inspired by the [game-jam and shared-practice research](../../research/creative-jams-and-shared-practice.md) and the [ongoing-activity experiment](../../experiments/ongoing-activities/findings.md), not a claim that any named jam uses these exact rules.

## Package and instance

The new behavior configuration is exactly `{ "contract": "project_cycle@1", "allowPromptOverride": boolean }`. It requires `identity@1`, `serial_events@1`, `durable_state@1`, `private_views@1`, `clock@1`, and `text@1`. The [small team jam](examples/small-team-jam.json) is a complete package example. The [JSON Schema](package.schema.json) checks its structure; this document defines its runtime meaning.

At instance creation, the host binds an organizer, distinct participant IDs within the package bounds, and `teams`: an ordered array of at least two `{ "id": string, "members": [participant IDs] }` records. Team IDs are unique nonempty strings other than `system`. Every team has at least one member; every participant belongs to exactly one team. Teams and membership stay fixed for the instance. The organizer is not a team member. The host also binds trusted integer millisecond times `opensAt`, `submissionDeadline`, and `reviewDeadline`, satisfying `createdAt ≤ opensAt < submissionDeadline < reviewDeadline` within the safe integer time range. A prompt override at creation is valid only when `allowPromptOverride` is true.

Phases are `waiting` before `opensAt`, `work` in `[opensAt, submissionDeadline)`, `review` in `[submissionDeadline, reviewDeadline)`, and `complete` at or after `reviewDeadline`. The host advances phases before events and views, even if a scheduled worker runs late. A worker should wake at each boundary. Missing submissions or reviews never delay a boundary. Boundary ticks from `system` have an empty payload and are accepted without adding a human contribution.

## Participant actions

All contribution values below are nonempty text. The actor is authenticated by the host; a client cannot supply another actor or trusted time. An event has a nonempty `eventId`, `type`, actor, trusted `at`, and exact payload. Accepted IDs are durable: retrying the same ID with the same type, actor, and structurally equal payload returns `replayed` without a second effect, including after a deadline. Reusing an ID with changed content returns `rejected`.

| Event type | Allowed time and actor | Payload and effect |
|---|---|---|
| `post_progress` | A participant during `work`. | `{ "audience": "team" | "group", "value": text }`. Appends a post identified by its accepted `eventId`, with author, team, audience, value, and an initially empty comment list. Any number of distinct posts may be made. |
| `comment` | A participant during `work`. | `{ "postId": accepted post event ID, "value": text }`. Appends one comment. A team post can be commented on only by that team's members; a group post by any participant. Unknown or inaccessible posts reject. |
| `submit_final` | A participant during `work`. | `{ "value": text }`. The first accepted final from a team is that team's only final. Another member's competing submission rejects. Other teams' final content stays concealed until `review`. |
| `submit_review` | A participant during `review`. | `{ "team": other team ID, "value": text }`. The target must have an accepted final. Each participant may review each other team at most once. Self-team and absent-final reviews reject. Reviews stay concealed from other people until `complete`. |
| `tick` | Host `system` actor. | `{}`. Advances scheduled phases without making a contribution; no other actor may send it. |

The five event types above are the only ones in this contract. A rejected action does not add a post, comment, final, or review. The host's authoritative commit order resolves competing team finals and comment order. Accepted events and phase transitions survive restart. The 0.4 package exchange rules still apply before instance creation.

## Views

All bound actors see `phase`, `finalCount`, `reviewCount`, and `finalStatuses` in team enrollment order. Each status is `{ "team": id, "status": "pending" | "submitted" | "missed" }`: absent finals are `pending` through `work` and `missed` after the submission deadline. Counts and statuses may reveal participation progress, not content.

The `progress` array preserves accepted post order and includes all `group` posts plus the viewer's own team's `team` posts. The organizer sees group posts only. Each visible post includes its accepted event ID, team, author, audience, value, and comments in accepted order. A person cannot obtain another team's private post or comment through an activity view.

A participant sees their team's accepted final as `ownFinal` as soon as it exists, and an `ownReviews` array containing only reviews they wrote. The organizer receives neither field. During `review` and `complete`, everyone additionally sees `finals` in accepted order. Only at `complete` does everyone see `reviews` in accepted order. These projections also apply to cached views and notifications. The package prompt is public directions; the host does not claim to verify work done away from the app.

## Boundaries and evidence

The contract fixes teams before the activity starts. It does not provide a team-finding process, mutable membership, drafts, edits, deletion, moderation, media files, scoring, winner selection, a general threaded discussion service, or notifications. These may be separate host features or later contracts. A host lacking the exact behavior or a required capability returns `unsupported` with sorted missing tokens before creating the instance.

The [0.5 conformance cases](conformance/README.md) cover all five contracts. Run `python3 format/0.5/check.py` for the reference model. The [two-host local trial](../../validation/0.5/README.md) imports the packages into independent Python and Node.js SQLite-backed services and checks 18 cases, project worker boundaries, team privacy, competing finals, retry after restart, and package exchange. It establishes agreement for these local text examples, not arbitrary activities, image storage, live media delivery, or production deployment.
