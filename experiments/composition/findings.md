# Composition findings

**Result:** `python3 experiments/composition/check.py` passes 14 unchanged offer-flow traces and three new queue traces in independent JavaScript and Python interpreters. The new interpreters agree exactly on JSON output. For the 14 legacy cases, outcomes, selected state fields, and relevant participant/host views also match the earlier interpreter. The new cases cover skip and reassignment, a private active lease, unauthorized submit/skip, and a media mismatch.

## What changed

The [offer-flow experiment](../offer-flows/findings.md) dispatched on two activity-specific `kind` values. These plans dispatch on eight operation names and two stage types. The same `assign` and `commit` operations run the proposed relay, [Cover and Response](../../research/activities/cover-and-response.md), and a held-out picture-telephone queue case. No branch checks an activity ID. A skipped queue lease retains its input, and a later claimant can complete that step.

This is **partial composition**, not evidence of a stable universal core. The assignment policies contain substantial distinct behavior: fixed recipient routes, exposure-balanced artifact offers with a hash tie-breaker, and a queue lease. The held-out case required adding `queue_lease` and `release`. Naming these as policies moves some complexity into reusable host behavior; it does not make the algorithm portable merely because the plan is JSON. A host lacking a policy should reject that plan, but this draft only declares coarse capabilities and does not yet negotiate policy versions.

## Size comparison

Counts are physical lines and UTF-8 bytes from `wc -l -c`; whitespace and formatting affect them. They are a rough authoring/implementation cost signal, not a runtime benchmark.

| Artifact | Earlier two hard-coded flows | Composed experiment |
|---|---:|---:|
| Two matching definitions | 38 lines / 1,486 bytes | 43 lines / 2,613 bytes |
| Both interpreters | 430 lines / 22,110 bytes | 590 lines / 27,453 bytes |
| Added held-out definition | — | 20 lines / 988 bytes |

The composed definitions for the original two flows are about 76% larger in bytes, while the interpreters are about 37% longer in lines. The extra queue plan uses the same interpreter, but the implementation had to add a new policy. The evidence does not yet show that composition reduces total cost as more activities arrive.

## Limits and next boundary

The tests use serial event lists. They do not prove atomicity for simultaneous network submissions, durable recovery, authorization, or delivery. The Cover and Response allocation uses small numeric IDs; large-number precision and tie behavior need a normative rule if this policy becomes portable. The Drawception case deliberately models only the documented skip-and-requeue pattern, leaving its unknown queue algorithm outside the claim.

The next discriminating test is **policy portability**: specify one assignment policy as a versioned, language-neutral algorithm with input/output fixtures and host capability negotiation. Then implement it in a third runtime or an independently structured interpreter, including ties, duplicate delivery, large IDs, and restart. If that specification becomes too burdensome, compare a constrained portable expression/runtime extension for only the assignment decision. That experiment should keep the surrounding activity plan unchanged, so its cost isolates the extension boundary.

The later [creative-practice revisit](../creative-practice-revisit/README.md) shows another independent boundary: a collection pool retains one artifact per actor, and the linear stage plan does not model ongoing progress discussion beside a final-submission deadline. This does not change the 17 passing traces; it limits what they support about long-running activities.

The subsequent [assignment-policy portability experiment](../policy-portability/README.md) implements the isolated algorithm test described above with an exact-integer version, a third runtime, and cross-runtime restart. It does not change the composed stage plan or establish host-level concurrency.
