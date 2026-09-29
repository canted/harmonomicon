# Assignment-policy portability findings

**Result:** `python3 experiments/policy-portability/check.py` passes five policy fixtures in JavaScript, Python, and Ruby. The three implementations agree on full outputs. For three checkpoint fixtures, every producer runtime resumes in every consumer runtime and reaches the same result as uninterrupted execution: 27 cross-runtime continuations.

## What the evidence supports

| Probe | Result | Interpretation |
|---|---|---|
| Small IDs, forward and reverse request order | Ordered offers match the earlier [forward-order fixture](../offer-flows/cases/11-cover-allocation-stability.json) and [reverse-order fixture](../offer-flows/cases/13-cover-allocation-reverse-order.json). | A separately specified policy can preserve the existing bounded example while leaving its surrounding stage plan unchanged. Request order is a behavioral input. |
| Large IDs and a score tie | Decimal-string IDs above `2^53` retain their values in all three runtimes. IDs `1` and `9007199254740993` have the same 32-bit score for one recipient, so numeric ID order decides their offer order. The `2^64−1` boundary is accepted; overflow and leading-zero IDs reject. | The tie and integer representation have to be normative. The previous small-ID Python/JavaScript agreement did not establish this. |
| Duplicate delivery | An exact request-ID retry returns the saved offer without changing exposure counts. A new ID for the same recipient returns the saved offer; reuse of an ID for another recipient rejects. A request ID named `__proto__` survives JavaScript/Ruby/Python round trips. | Serial replay semantics can be made portable. This does not prove atomic database behavior under simultaneous requests. |
| Capability negotiation | A host advertising version `@2` but not `@1` returns `unsupported` and names the missing `@1` token. | A package can fail explicitly when the host does not implement the required algorithm version. A token alone cannot certify an implementation. |
| Process restart | Each runtime's JSON checkpoint resumes in each runtime, including after a saved offer and after an exposure count has changed. | These snapshots carry enough state for the fixtures. No real crash, transaction, or durable log was exercised. |

The [policy contract](contract.md) takes 27 physical lines and the three example implementations take 103, 109, and 111 lines. Those counts are only a rough cost signal: they include fixture loading, validation, checkpoint handling, and CLI output. They do show that a compact *definition* still obliges every conforming host to implement and maintain the algorithm.

The exact32 policy is an experimental successor to the earlier `cover_offer_score_v1` tie-breaker. It matches the small-ID fixtures. The earlier JavaScript interpreter uses `number` multiplication before bitwise conversion; this contract instead performs exact integer arithmetic and uses decimal-string IDs. The two definitions may differ for large IDs.

## Architectural consequence and limit

A versioned named policy plus fixtures is a workable portability boundary for this one algorithm: the activity plan names the decision point; the policy specification supplies its exact meaning; the host declares support for that version. No portable callback or general expression language was needed for these cases. This does not establish that every novel assignment, scoring, or moderation rule should become a named policy. Proliferating specialized policies could make host implementation impractical.

The experiment isolates one decision. It does not make the composed plan a complete portable package, test actual simultaneous writes, enforce private views in a server, or transfer a running activity between apps. The [contract synthesis](../../research/contract-synthesis.md) records what can now be drafted and what still needs a host-level trial.
