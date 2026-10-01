# Candidate 0.21 decision record

October 1, 2026; base `c7b3fb9` (0.20). This candidate addresses activity composability raised by prospective host app, a prospective host app evaluating Harmonomicon support. It does not reproduce prospective host app's product or decide 1.0 readiness.

1. **Voting is an instruction.** `vote@1` states candidate material, ballot audience and whether choices can change. Authors do not implement replacement, retry or counting workflows. Predefined IDs and accepted contribution references preserve identity independently of labels and rendering.
2. **Count, select and present are distinct useful abstractions.** `tally@2` creates a private structured count result without requiring individual reveal. `select@1` applies a meaningful most-votes outcome policy. `present@1` publishes a typed result, including selected material. Authors can present totals without selecting, or calculate a selection for a subsequent round without a separate announcement. No special winner operation or general template language is needed.
3. **Random ties name a guarantee.** Equal chances among the highest tied candidates and durable one-time selection are required. Reference hosts use their platform uniform random integer APIs; injected test selections cover every tie member. Equivalent hosts need not use the same generator or produce matching random sequences. The older seeded assignment policy keeps its exact historical algorithm.
4. **Finite linked rounds establish continuation.** `artifact_pool@2` adds a round identity and a typed initial/result input to existing collection rules. References remain explicit, preceding and instance-scoped. Unresolved/empty input records lineage and blocks collection rather than inventing a fallback. This is sufficient for a continuing creative witness without an unlimited orchestration system.
5. **Visibility remains an activity choice.** Private ballots reveal neither peers' current choices nor completion flags. Candidate publication is explicit in voting; aggregates disclose counted totals when presented. An optional ballot reveal remains available. No universal anonymity claim is made. The organizer does not bypass private views.
6. **The host owns execution infrastructure.** Resolved dates/actors, account authentication, ordered durable transactions, media authority/storage/rendering, notifications and interface design stay with the host. Package data selects observable rules; host implementation cannot silently substitute product rules and claim full package support.

## Assessed extensions

| Request | Potential reuse | Candidate relation/decision |
|---|---|---|
| Designated-person tie choice, deadline, random fallback | Committees, judging, facilitated decisions | Deferred. Requires an authority and pending-result race contract; random/unresolved policies satisfy required scope. |
| Exclude previous winner from submitting but allow voting | Rotating authorship and equitable participation | Deferred. Separate effective submitter/voter sets can be supplied by the host, but no result-derived package eligibility exists; faithful prospective host app support remains limited. |
| Video | Creative source/response activities | Deferred media kind/profile; no dependency for current text/image/audio witnesses. |
| Multiple typed contributions per person | Brainstorming and contests | Deferred quota extension; one typed entry per actor remains. Existing text pool quotas are unchanged. |
| Exposure-balanced assignments, self fallback, preparation offers | Peer exchange and large collections | Deferred assignment policies/states; unrelated to highest-vote selection. |
| Responses without assigned input | Open feedback and discussion | Deferred activity response contract; ordinary host conversation remains external. |
| Unlimited streams, thread ending/restart | Ongoing community products | Deferred lifecycle/orchestration; finite explicit rounds suffice here. |
| Provider-specific SMS and attention rules | Product integration | Host transport/preferences, no language guarantee. |
| Messages processed after settled deadline | Offline/queued communication | Unsupported acceptance; trusted exclusive execution deadline remains. |
| Calendars, roles/admin, general workflow code | Application infrastructure | Host-owned. No general permission/calendar/programming language introduced. |

Review packet and executable witnesses establish a bounded supported profile, not a faithful product migration. Legacy migration accounting remains six complete/fourteen incomplete. Missing offer/caption/permission/lifecycle contracts remain recorded even when a simplified voting slice is now expressible.
