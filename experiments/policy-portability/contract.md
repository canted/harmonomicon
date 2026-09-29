# Balanced artifact assignment: exact32 version 1

**Experimental policy token:** `policy:balanced_artifacts_exact32@1`. This is a language-neutral specification of one assignment decision, not a general activity format. The experiment reads `count: 2`, `excludeSelf: true`, and `roundId: 42` from the unchanged [composed Cover and Response slice](../composition/definitions/cover-response.json). The new token is declared separately in [policy.json](policy.json); it does not rename the earlier plan's `balanced_artifacts` policy.

## Inputs and result

- Every round, recipient, owner, and artifact ID in policy input is a canonical unsigned decimal string in `[0, 2^64−1]`: `0` or a nonzero digit followed by digits, with no leading zero. The round ID read from the base plan is converted to that representation. JSON numbers are not used for policy IDs.
- The cover pool is an immutable list of unique artifact IDs with one active cover per owner. A requester must own one active cover. Each event is `{requestId, recipient}` with a nonempty, case-sensitive request ID.
- Each accepted first request returns an ordered list of two **other owners'** artifact IDs and saves that list for the recipient. A repeated request with the same ID and recipient returns `replayed` with the saved list. Reusing the request ID for another recipient returns `rejected`. A new request ID for a recipient who already has an offer returns `existing` with the saved list and records the new ID. Rejected requests change no offer or request ledger.
- If fewer than two eligible artifacts exist, the request is rejected. Input order does not affect sorting. The host supplies an authoritative serial order for requests; requests from different recipients can affect later exposure counts.

## Ranking

For each eligible artifact, compute its **exposure count** as the number of saved offers containing its ID. Sort ascending by `(exposure count, score, numeric artifact ID)` and select the first two. All three components have explicit tie behavior.

Let `M = 2^32`, `r` be the round ID, `u` the requesting recipient ID, and `a` an artifact ID. Arithmetic is exact on unsigned integers. Define:

```text
x = ((r × 73856093) mod M) XOR ((u × 19349663) mod M) XOR ((a × 83492791) mod M)
score = x XOR (x >> 16)
```

`XOR` is a bitwise operation on unsigned 32-bit words and `>>` is a zero-filling right shift. The score is an unsigned 32-bit integer. This preserves the earlier experiment’s ranking for the small IDs in its fixtures; for large IDs it defines exact arithmetic instead of the earlier JavaScript `number` multiplication. IDs differing by `2^32` can have the same score, so the final numeric-ID tie-breaker is required.

## Capability and checkpoint contract

The host must advertise the exact policy token. If it does not, the package returns `unsupported` before processing requests, reporting that token as missing. A JSON checkpoint includes the saved offers, request-ID ledger, outcomes, next request index, and policy token. A receiving interpreter checks the token and resumes the same input sequence. The checkpoint test proves representation compatibility for the fixtures; it does not prove atomic database writes, durable storage, or exactly-once delivery.
