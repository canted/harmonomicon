# Offer-flow findings

**Result:** [14 explicit cases](cases/) pass in both independent interpreters, including cross-language continuation from snapshots emitted by separate processes. Run `python3 experiments/offer-flows/check.py`.

## What the traces establish

| Trace group | Observed result within this contract | Limit |
|---|---|---|
| Relay competing submissions | The first valid event in the authoritative sequence fills one step; reversed same-time order reverses the winner. A loser cannot advance that step. | Events were serially processed; this does not exercise concurrent database writes. |
| Relay retry and invalid input | An exact retry of an accepted request ID returns `replayed`; changing its payload rejects. An invalid media type does not consume the step. A request ID that is a special JavaScript object key survives JSON restart. | No durable request ledger or external artifact validation exists. |
| Relay timeout and fallback | A timed-out first pair is replaced by the configured second pair. If all pairs time out, the chain enters `stalled`; it does not reveal an incomplete chain. | A real worker must deliver timeout events reliably. The pairs and recovery limit were experiment choices. |
| Relay views | An open step exposes its input only to offered participants; the full chain appears to everyone at `done`. | View shaping is not a storage or API access-control proof. |
| Cover and Response minimum-cover barrier | Two covers at the scheduled switch keep the modeled activity collecting. A third late cover opens responses; a chosen offered cover can receive a linked response. | This is a constructed activity with limited participant-facing views. |
| Cover and Response allocation | Saved offers exclude the requester's own cover and prefer less-offered covers. Reversing offer-request order changes the pairs while leaving the submitted covers identical. | Host event order and the assignment algorithm are part of reproducible behavior. |
| Cover and Response recovery and reveal | Host removal before the cover deadline can drop the count below the minimum. Responses stop at the due time and become visible at completion. | Publication controls, notifications, and reassessment are outside the model. |
| Process restart and replay | For every supported fixture, either language can resume a JSON snapshot emitted by a separate process in either language and reach the uninterrupted result. | Real crash recovery, persistence, and message redelivery remain untested. |

## Architectural consequence

The two flows require **different named semantics** even though both present “two offers.” The competitive relay needs a single-winner commit for one pending contribution, retries, and timeout reassignment. Cover and Response needs a saved pair of source artifacts, exposure balancing, a participant choice, a response linked to the chosen artifact, and a minimum-count phase barrier. The existing `handoff` and `collection` mechanisms cannot express either flow faithfully by parameter changes alone. This experiment added two hard-coded interpreter branches; it did **not** demonstrate that a small composable mechanism set can express them.

The Cover and Response case exposes a portability requirement beyond the shape of a JSON definition. Its `assignmentScore` and offer-count ordering affect who sees which covers. A second host could read the same config yet allocate differently unless that algorithm, its inputs, and event ordering are specified and versioned. The [contract](contract.md) defines the bounded procedure; the [policy experiment](../policy-portability/README.md) later defines a versioned, exact-integer successor for the assignment decision.

## Next boundary test

Before choosing a public schema, test whether a small set of independently specified operations can compose these two flows **without** one bespoke branch per activity. The operations would have to cover offers to people, offers of artifacts, one-winner acceptance, contribution linkage, barriers, reveal, and replayable side effects. Compare definition size and interpreter complexity against the current hard-coded flows; an increase that simply recreates a general programming language would not answer the portability question.

This follow-up is now recorded in the [composition experiment](../composition/README.md). Its [findings](../composition/findings.md) show reuse of operation names while identifying distinct assignment policies and higher definition cost.

The later [creative-practice revisit](../creative-practice-revisit/README.md) distinguishes the proposed two-recipient picture-telephone relay here from the published Relay Jam's sequential A-to-B project handoff. The newer game-jam examples do not change the outcomes of these 14 traces.
