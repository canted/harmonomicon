# Cover and Response

**Status:** Constructed digital activity used to test portable group-activity contracts. It is not presented as a traditional practice or as an implementation of a named product.

## Activity

A group first contributes cover images. Once enough covers exist and the collection deadline has passed, each cover contributor can receive two other people's covers, choose one, and make a text or audio response to it. Responses remain private until a shared reveal.

## Procedure used by the experiments

1. The host enrolls participants, sets a cover deadline, a response deadline, and a minimum cover count. The fixtures use four participants, a minimum of three covers, and two response options per contributor.
2. Participants submit one active cover image each. Before the cover deadline, the host may remove a cover. The model stores opaque artifact references rather than image data.
3. At or after the cover deadline, the response phase opens only when the minimum number of active covers exists. If the count is still low, another cover can be accepted before the response deadline and open the response phase. At the response deadline, the activity completes even if the minimum was never met.
4. A cover contributor requests an offer. The host excludes that person's own cover, counts how often each remaining cover has already been offered, sorts by the lowest exposure count and then a deterministic score, and saves the first two covers as that person's offer. Repeating the request returns the saved pair.
5. The contributor chooses one of the offered covers and submits a text or audio response linked to it. The model accepts one current response per contributor; a later accepted response replaces that contributor's earlier one.
6. At the response deadline, the activity completes and the response-cover links are revealed to participants. Contributors see their own cover, offer, choice, and response before completion; the host can inspect the full state.

The [offer-flow contract](../../experiments/offer-flows/contract.md) specifies the bounded event and view semantics used in the first experiment. The [composition contract](../../experiments/composition/contract.md) tests the same flow with shared operations. The [policy contract](../../experiments/policy-portability/contract.md) defines an exact-integer successor to the first experiment's score rule for large IDs; it is not a retroactive change to the earlier fixtures.

## What the activity tests

This case combines a collection threshold, scheduled phase change, persistent artifact offers, exposure-balanced assignment, a participant choice, linked responses, and delayed reveal. It differs from a two-recipient relay: here one person chooses between **two source artifacts**; in the relay two people compete to complete **one pending task**.

The experiments do not model artwork quality, moderation decisions beyond early cover removal, message delivery, storage, actual simultaneous writes, or a full participant interface. The numeric deadlines and allowed response media are test parameters, not rules attributed to an outside practice.
