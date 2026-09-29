# Digital activity stress cases

**Status:** Focused research extension after Pass 4. Observed product behavior is separated from a proposed relay variant; this is not a plugin schema.


## Why these cases

The first eleven [activity cards](mechanism-survey.md) covered scheduled posting and possible digital adaptations, but only one card documented a native digital product in detail. The [named-mechanism experiment](../experiments/named-mechanisms/comparison.md) explicitly lacks multiple recipients, optional turns, and simultaneous submissions. These three new cards probe distinct digital advantages and failure points:

| Observed case | Source-backed algorithm | Digital-specific issue exposed |
|---|---|---|
| [Drawception picture telephone](activities/drawception-picture-telephone.md) | Alternate drawing and caption panels across people; skipped or exited panels return to a shared queue; repeatedly skipped descriptions can be removed. | An asynchronous chain needs a way to release work without ending the chain. |
| [Moodle Workshop](activities/moodle-workshop.md) | Gate submissions and reviews by phase and time; allocate peer reviews; evaluate grades; teacher can intervene and close. | Missed work, late submissions, allocations, and automatic transitions require distinct policies and authorities. |
| [Board Game Arena Gaia Project faction auction](activities/bga-gaia-project-faction-auction.md) | Collect maximum bids from everyone, run many automatic bids, assign factions, and adjust scores. | Software can carry out a long rule sequence from compact participant inputs; its exact game logic remains specific to the activity. |

These are examples of implemented behavior, not evidence that every activity host should copy their rules. Drawception's [FAQ](https://drawception.com/faq/) states the skip/requeue behavior; Moodle's [settings](https://docs.moodle.org/502/en/Workshop_settings) state late-work and phase-switch conditions; Board Game Arena's [game help](https://en.doc.boardgamearena.com/Gamehelpgaiaproject) describes the auction and its generated log.

## Proposed asynchronous Eat Poop You Cat variant

The physical game alternates a written phrase and a drawing, passes the sheet to the next person, hides earlier contributions, and reveals the chain at the end. A [participant account of the game](https://xolotl.org/epyc-2021/) supports that baseline. Drawception is an observed digital relative, but its published rules describe a queue and skips, **not** the simultaneous two-recipient rule below. Everything in this section is a **proposed digital variant for testing the protocol**.

### Candidate procedure: two open offers, first valid completion

1. Start a chain with a phrase. Determine whether the next contribution must be a drawing or a phrase, how many accepted steps complete the chain, and which participants are eligible.
2. For a pending step, select two eligible participants. Give each an offer showing only the prior accepted contribution and the requested media type. Record the offer's deadline and send invitations through the host's available channels.
3. Either person may work. A submitted contribution must satisfy the declared input conditions (for example, correct media type and a valid still-open offer). The first valid submission **committed by the authoritative host** becomes the step's single accepted contribution.
4. Close both offers as part of that decision. A later attempt gets a clear closed-step response and does not advance the chain. Decide separately whether an unaccepted draft is retained privately, discarded, or returned to its creator; this variant does not silently publish it.
5. If no valid contribution arrives by the deadline, use an explicit recovery policy: offer the step to another person, extend the deadline, allow a host to intervene, or end the chain as incomplete. The choice is part of the activity rules.
6. Continue with the next media type. Reveal the complete chain only after the chosen completion condition is met.

“First valid completion” differs from “first claim.” Claiming would grant one person an exclusive, possibly expiring reservation before they produce anything. The proposed procedure leaves two offers open until an accepted submission or timeout. It reduces dependence on one person but may cause a participant to work on a contribution that is not used. That cost needs to be visible in the invitation and closure message.

### Traces that distinguish the policies

| Trace | State and response required by this proposed variant |
|---|---|
| A submits a valid drawing; B has not submitted. | Accept A once, close both offers, create one next phrase step, notify B that the step has closed. |
| A and B submit near-simultaneously. | The host commits one accepted contribution for the step. The other receives a closed-step result; arrival times at different devices do not decide the winner. |
| A's submission is invalid; B submits valid work. | Reject A without closing the step; accept B. “Valid” must be defined before this can be portable. |
| A retries after a lost network response. | Return the original result for the same submission attempt; do not create a second step. |
| Neither person responds before the deadline. | Apply the declared recovery branch; a timeout alone must not leave the chain pending forever. |
| The deadline job and A's submission race. | The authoritative host chooses exactly one transition: accept the submission under the deadline rule or close/reassign the step. A job retry must not perform a second transition. |
| B opens an old invitation after A wins. | Show that the offer is closed. Do not expose any next-step private context through the stale invitation. |

The single accepted contribution and single next step are **proposed invariants**, not observed Eat Poop You Cat rules. They would require atomic state change and duplicate-request handling by a host. The activity definition would need to state the deadline boundary, eligibility, winner policy, lost-work treatment, and recovery branch; a host capability declaration would need to establish that it can enforce those semantics. The later [offer-flow experiment](../experiments/offer-flows/README.md) tests a fixed-policy slice in two interpreters; it does not establish real concurrent database behavior.

## Cross-case findings for package research

1. **Assignment, offer, reservation, and acceptance are separate events.** Drawception documents requeue after skip; Moodle documents reviewer allocation; the proposed relay makes two offers and accepts only one result. Treating all of these as a single `nextParticipant` operation would erase important behavior.
2. **A deadline does not specify recovery.** Moodle can accept late submissions but needs subsequent allocation; Drawception returns skipped work to a queue; the proposed relay still needs a chosen timeout branch. BeReal's late flag is yet another policy, not a default for the others.
3. **Automatic rules have different portability costs.** The Gaia Project auction is a compact input followed by extensive game-specific calculation. Moodle's grading likewise has a deterministic method, configurable strategies, and teacher overrides. Declaring generic “scoring” or “auction” support would not establish that two hosts produce the same result; either the precise algorithm or a named, versioned capability must be shared.
4. **Participant-facing explanations matter when software does hidden work.** Board Game Arena exposes an auction log and [advises developers](https://en.doc.boardgamearena.com/images/7/76/5-guidelines.pdf) to make automatic actions legible. The proposed relay likewise needs an explicit response to a contributor whose offer closes while they work.
5. **Liveness and concurrency need separate evidence.** The later [offer-flow experiment](../experiments/offer-flows/findings.md) covers same-time serial ordering, duplicate retry, timeout/submission order, fallback, and full-chain reveal under one fixed relay policy. It does not simulate truly concurrent writes or delivery failures. A further experiment must test those host guarantees before a public contract claims them.

## Evidence limits

The product help pages describe public behavior, not their entire server implementation. Drawception does not publish its queue fairness or exact collision rules in the consulted pages. Moodle's user documentation describes the grading method but says it has no single simple formula. Board Game Arena's Gaia Project help illustrates the auction but does not fully formalize every tie and invalid-input case. The proposed two-offer relay is a design hypothesis and has no claim of deployment or measured improvement in completion rate.
