# Single-source distribution: scope and evidence

**Status:** Retained text-source/linked-text-response design and validation notes in candidate 0.20. New typed operations are specified in [artifact notes](artifact-notes.md). It does not certify production app integration or define 1.0.

The latest project scope clarification prioritizes explicit useful distribution algorithms over faithful reproduction of every activity detail. A simplified creative-response activity can give each person one non-self source rather than two alternatives. The Chorus comparison, pinned to 0.16, identifies authoritative source links and independent participant progress as useful core witnesses; it also identifies many additional product rules. Those rules are not all readiness prerequisites.

The selected policy set has two members: next contributing person in roster order, and seeded non-self sampling. Both use a closed one-item-per-author pool, an explicit participant/contributor recipient set, one source per matched person, permitted reuse and explicit unmatched skip. This avoids pretending roster offsets handle partial pools, and avoids a combinatorial set of cardinality, fairness and allocation settings. Randomized outcomes are saved once and survive reads, retries, process restart and changed process seed configuration. The sampler is exact and reproducible, with no cryptographic or exposure-fairness claim.

The [creative-response package](examples/single-source-creative-response.json) uses one randomized source per contributor and a deadline-only response window. The [idea exchange package](examples/idea-response-and-pairs.json) uses deterministic assignment, all-matched-response close and a pair-private continuation. A held-out authored arrangement combines random assignment with that continuation and executes in both durable hosts without a new activity-specific implementation.

Seven explicit traces cover full/partial/empty/one-source pools, both recipient sets, self-exclusion, repeated use of a source, independent responses, source-ID validation, private source/response views and attributed reveal. Twenty-five invalid-definition witnesses and additional seed, rejection-sampling, immutable restore, deadline, no-publication, overflow and sequential-distribution probes supplement them. Durable probes cover concurrent materialization reads, response races, accepted replay after closing/restart, changed process seed, worker-only progression, absent capability/no state, host-generated seed persistence and transfer with opaque IDs.

## Simplification versus exact parity

| Witness | 0.20 support | Explicitly deferred |
|---|---|---|
| Retained text-only creative response | One assigned non-self text source; a response bound to its saved source; independent response progress; deadline and linked-result reveal. | Authorized images/audio/video, two offered choices, balanced exposure, late third-source threshold, mutable contributions, moderation, organizer participation/inspection, active date changes and app publication. |
| Legacy paired story response | Reusable text source pool and authoritative response relation. | Exact two-source balanced offers, contributor selection, phase time bindings and the legacy insufficient-source terminal branch. Its migration remains incomplete. |
| Unrelated idea assessment/reflection | Deterministic source assignment and text response followed by private pair reflection. | Numeric grading of those links, representative synthesis and reviewer balancing are not inferred. |

Uploads, drafts, notification delivery, chat cards and board publication remain host integration work. Candidate 0.20 additionally provides typed image/audio pools and linked responses, organizer participation and effective actor/date controls via separate operations. Retained text operation contracts remain unchanged; their text-only witnesses are distinct from the new simplified image-source Chorus. See [typed rules](artifact-notes.md). Richer offer choice and exact app parity remain optional. No 1.0 promotion follows automatically from this candidate.
