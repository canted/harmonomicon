# Activity package format 0.11 candidate

**Status:** Candidate validated in two independent local hosts for text and the specified PNG image subset. It is not yet a published standard.

A Harmonomicon package is data describing a digitally mediated group activity: human directions, participation bounds, provenance, host requirements, and one exact behavior contract. Candidate 0.11 retains the [nine 0.10 contracts and image-reference rules](../0.10/README.md) and the [package exchange rules](../0.4/README.md). Its `format` is exactly `harmonomicon.activity-package/0.11`; carried examples have new package versions because their format field changed. A host reports missing contracts or capabilities as `unsupported`.

Candidate 0.11 adds `permissioned_dialogue@1`. The [feedback circle](examples/feedback-circle.json) is a digital text activity with a facilitator, a maker, and responders. The facilitator advances four phases manually. In the last phase, the maker grants or denies each request before the requester may submit an opinion. The [Critical Response Process card](../../research/activities/critical-response-process.md) identifies phase authority and per-opinion permission as app-enforceable mechanisms. This contract is a separate digital adaptation; it does not claim to implement that practice's human judgment of neutrality or constructive feedback.

## Package and setup

The behavior object is exactly `{ "contract": "permissioned_dialogue@1", "allowPromptOverride": boolean, "phasePrompts": { ... } }`. `phasePrompts` has exactly four nonempty text fields: `meaning`, `maker_questions`, `neutral_questions`, and `permissioned_opinions`. It requires `identity@1`, `serial_events@1`, `durable_state@1`, `private_views@1`, `clock@1`, and `text@1`.

At instance creation the organizer is the facilitator and supplies `maker`, one of the bound participants. All other participants are responders. The organizer is distinct from every participant. The trusted creation time must fit the safe integer Unix-millisecond range. The initial general prompt may be overridden only when `allowPromptOverride` is true; the four phase prompts stay fixed from the package. The instance begins in `meaning`; no clock or participant submission advances a phase automatically.

## Events and phase authority

Every accepted event is committed in one authoritative order. A facilitator-only `advance` with empty payload moves exactly one step from `meaning` to `maker_questions`, then `neutral_questions`, then `permissioned_opinions`, then `complete`. It can occur with no contributions. A participant cannot advance, and the facilitator cannot backtrack or advance after completion.

The other event types are allowed only in their named phase:

| Phase | Actor and event | Exact payload | Rule |
|---|---|---|---|
| `meaning` | Responder `post_meaning` | `{ "value": nonempty text }` | Adds a visible statement. |
| `maker_questions` | Maker `ask_question` | `{ "value": nonempty text }` | Creates a question identified by its accepted event ID. |
| `maker_questions` | Responder `answer_question` | `{ "questionId": ID, "value": nonempty text }` | Question ID must name an accepted maker question; each responder may answer that question once. |
| `neutral_questions` | Responder `ask_neutral` | `{ "value": nonempty text }` | Creates a question identified by its accepted event ID. The host does not judge neutrality. |
| `neutral_questions` | Maker `answer_neutral` | `{ "questionId": ID, "value": nonempty text }` | Question ID must name an accepted neutral question; the maker may answer it once. |
| `permissioned_opinions` | Responder `request_permission` | `{ "topic": nonempty text }` | Creates a request identified by its accepted event ID. |
| `permissioned_opinions` | Maker `decide_permission` | `{ "requestId": ID, "grant": boolean }` | The request must exist and be undecided. One decision per request. |
| `permissioned_opinions` | Requesting responder `post_opinion` | `{ "requestId": ID, "value": nonempty text }` | Requires that specific request's grant; one opinion per granted request. A denial cannot be bypassed by a grant for another request. |

Accepted contributions, decisions, and phase advances appear in `transcript` in commit order. An unanswered or undecided request may remain when the facilitator completes the activity; it grants no permission. Events for a closed phase are rejected. Every event uses an authenticated actor and trusted host time. Accepted event IDs persist: an exact retry returns `replayed`, including after completion; changed reuse returns `rejected`. Rejected requests do not reserve IDs.

Every bound actor sees `{phase, phaseNumber, facilitator, maker, prompts, transcript}`. `phaseNumber` is 1–4 while open and null at completion. The prompts are the package's four phase prompts. Transcript entries contain the accepted event ID, kind, actor, and the event-specific value, link, or decision. The transcript is group-visible immediately. An opinion is absent until a grant and a subsequent accepted `post_opinion`; a pending or denied request contains no opinion text. The host enforces permission at event commit, not merely in the interface.

## Evidence and boundary

The [schema](package.schema.json), [examples](examples/), and [41 conformance cases](conformance/README.md) cover ten exact behavior contracts. Run `python3 format/0.11/check.py` for the reference model. The [two-host trial](../../validation/0.11/README.md) checks the same traces through separate Python and Node.js SQLite services, including role and phase gates, simultaneous maker decisions, restart, authenticated views, and package exchange.

This contract does not classify the meaning of a question, judge feedback tone, guarantee that anyone speaks, provide live audio or video, let a facilitator reorder or reopen phases, or define Moodle's grading and reviewer-allocation policies. Those require human judgment or separately specified behavior.
