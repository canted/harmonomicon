# Candidate 0.23 decision record

The language arranges activity instructions. Authors configure participation, accepted material, audiences and outcome policies; hosts provide clocks, identities, durable authority and presentation. This candidate consolidates a concrete author-facing split: text pools allowed several items while typed pools allowed one.

1. **Types and limits are independent settings.** `pool@2` accepts a declared subset of text/image/audio and one shared `perActor` maximum of 1–8. No empty quota slot is a contribution. Accepted immutable entries continue consuming quota after withdrawal/readdition; moderation/replacement is not inferred.
2. **Items carry identity, not positions or copies.** Each actual accepted item has a UUID/source/item reference and real author/value/round. Equal values and multiple contributions by one author remain independent candidates. Typed inputs/results reuse the 0.22 snapshot and authority contract.
3. **Three different activity instructions remain useful.** Iterate every accepted item, assign one source and select a voted outcome express different rules. Old text loops and linked response instructions already reused saved material. Typed iteration and independent typed cardinality are the new capabilities; ordinary output reuse is not claimed as new.
4. **Version consumer contracts coherently.** Compatible new iteration/voting/assignment consumers accept typed pools without repeating producer kinds or building one operation per medium. Old versions retain exact source/output/privacy rules. Additional version tokens protect compatibility; reducing operation count is not an acceptance target.
5. **Sharing is explicit and attributed.** A frozen final-source actor list controls non-self readers, including eligible noncontributors. Internal snapshots remain private. Claim grants one reader the actual contribution; acknowledgment can produce an explicit public reveal. Timeout does not publish. Old anonymous text sharing stays unchanged.
6. **Assignment policy states the meaningful choice.** `next_nonself_item@1` chooses the next eligible author cyclically and that author's earliest accepted item. Seeded random assignment samples items, so more entries can mean more exposure. Reuse is allowed and unmatched actors skip. Neither policy promises balanced exposure or two offers; the host does not dispatch on activity names.
7. **Do not turn cardinality into a workflow engine.** One assigned immutable response per matched actor remains one. Item body outputs remain local; new voting/pooling/repetition stays top-level. Up to 800 eligible items, bounded identities/step IDs and conservative time budgets bound expansion. Late null-date close retains established capped timeout semantics.
8. **Authority is part of the observable contract.** Ready immutable owner-controlled media, qualified origins, all-viewer attestation, projection-based read grants and stable recovery are required. Storage/processing/player UI, calendars/accounts/notifications and launch of later instances remain host engineering.

## Deferred requests and reuse assessment

| Request | Potential reuse | Boundary in this profile |
|---|---|---|
| Designated-person tie choice with timeout/random fallback | Facilitated voting and judging | Deferred; needs a pending result and authority/timeout contract. Current random/unresolved tie policies suffice for the examples. |
| Exclude previous selected author from submitting but permit voting | Continuing contests | Deferred; needs result-derived eligibility. Hosts cannot claim this rule is language-defined when implementing it externally. |
| Video or new contribution kinds | Broader creative media | Deferred; no unrestricted type registry. Host encodings are separate from the three language kinds. |
| Exposure-balanced or two-offer assignments and self fallbacks | Peer review, creative exchange | Deferred; different saved choice/fairness semantics. More items do not imply these policies. |
| Responses without assignment, participant preparation offers | Flexible workshops | Deferred; separate participation/source rules, no dependency in the implemented examples. |
| Ongoing streams, thread endings/restarts, product schedules | Journals and long-running products | Host instance scheduling or future explicit contracts; this is a finite instruction sequence. |
| Provider SMS/deadline grace rules, late processed messages | Delivery integration | Host responsibility; settled exclusive deadlines do not accept later processing as earlier actions. |
| Calendar/role/workflow administration or executable templates | General automation | Outside bounded candidate direction; package data contains supported typed references and instructions only. |

The [checkpoint](DESIGN-CHECKPOINT.md) was sent before implementation. Its read-only critique settled shared quota accounting, frozen readers, private caches, exact multi-item policy and bounds. Independent implementations and [evidence](../../validation/0.23/EVIDENCE.md) validate these rules. Fresh independent runtime and authoring reviews cleared implementation `68d3f8322bee337a27ea52c9af94d330ff8116e8`; the [review record](../../validation/0.23/INDEPENDENT-REVIEW.md) is separate from completed 0.22 reviews and does not establish product parity.
