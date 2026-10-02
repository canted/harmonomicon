# Typed pooling: bounded direction for candidate 0.23

The user requested a generic typed pool with configurable per-person limits. This is the authorized next-candidate direction after 0.22 review, not behavior implemented or credited in 0.22.

## Existing reuse and the actual gap

| Current instruction | Already supported | Remaining restriction |
|---|---|---|
| `pool@1` | Multiple independent text items per participant with stable item IDs and accepted order. | Text only; its quotas do not apply to typed pools. |
| `for_items@1` | Iterate every item of an earlier closed text pool in commit order; claim/read/reveal can use current-item context. An additional collection inside the body can ask for a continuation of the just-shared slip. | Text-pool source and local body/item binding; body outputs cannot be consumed by later top-level typed/voting steps. |
| `artifact_pool@1/@2/@3` | Author-selected nonempty `kinds` subset of text/image/audio, actual typed identity/authority, one accepted contribution per eligible actor. `@2` adds finite round input; `@3` adds qualified material and declared starting inputs. | Fixed single-entry cardinality. Iteration and downstream consumers retain their declared source restrictions. |
| `assign_sources@1` / `respond@1` and typed equivalents | Saved source identity feeds linked responses; selected typed outcomes can feed another round or, in 0.22, a declared host input. | These relationships do not supply a general typed item loop or change pool cardinality. |

A proposal to remove the text-only/multiple-entry versus typed/single-entry split is justified by these author-facing differences. It should preserve the distinction between iterating all items, assigning one source, and selecting a group outcome. It must not imply that older language versions could not reuse submitted material.

## Smallest coherent direction

Accepted kinds and cardinality should be independent author settings: “accept text and audio” and “allow up to two contributions per person” change different participation rules. A typed pool should not require an author to choose a type-specific operation merely to change that limit. Keep stable independent contribution identity, attribution and accepted order for each entry; host media authority remains per value.

The next design checkpoint should choose a bounded initial quota model consistent with existing pool closing and missing-contribution rules. Validate type restrictions separately from quotas, including actors mixing accepted kinds, duplicate/retried items, multiple accepted IDs from one actor, source-author eligibility, deadlines and races. New operation versions must preserve all old pool meanings; lowering operation count is not a reason to silently broaden old contracts.

Assess compatible typed item iteration and downstream source consumers together. An item loop can expose a real current typed item and still keep author flow as “for each contribution, read/play it, then respond.” Claim/reveal/access behavior, nested output scope and rejection of incompatible sources must remain explicit. Do not promise every arbitrary response/form/result is a generic source. Typed voting/counting should reference each actual candidate independently rather than collapse by actor or rendered value.

## Boundaries and evidence

This direction does not require video, unrestricted multi-entry streams, response without source, exposure balancing, two-offer choices, moderation/replacements, a general role/calendar/workflow language or product-specific lifecycle. A per-person quota is not an invitation to infer any of those rules.

Candidate 0.23 should demonstrate the same typed pool configured for different kinds and limits, a compatible typed iteration composition, and a materially different downstream source/voting composition. Both independent engines and durable hosts must cover actual media/grants, accepted order, identity, quotas, eligibility, closing/retry/races/restart, unsupported negotiation and exact historical compatibility. No implementation starts until 0.22's pinned review has settled. This assessment records direction; it does not claim a completed design or conformance evidence for 0.23.
