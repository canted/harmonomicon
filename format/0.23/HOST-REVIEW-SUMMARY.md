# Harmonomicon 0.23 — host review packet

Candidate 0.23 is implemented and independently reviewed locally. Reviewed implementation: `68d3f8322bee337a27ea52c9af94d330ff8116e8`. This packet is prepared for user submission; no prospective host was contacted and nothing was merged, published or deployed.

## What authors can express

One typed pool independently chooses accepted text/image/audio kinds and a shared limit of one to eight contributions per person. Each actual item retains identity, attribution and accepted order. The same pool can feed typed item sharing, a contribution vote or one-source assignment and linked response. Existing versioned operations keep their exact meanings.

The earlier concerns about contribution-derived choices, optional current-vote changes, private ballots with public totals, structured most-votes/tie/empty outcomes and general result presentation are supported. Selected typed material can feed an explicit later round or a separately host-launched instance through an authorized declared input. Input origin and the decision handing it onward remain distinct. Earlier text loops and linked responses already reused material; this candidate adds consistent typed quotas and compatible consumers.

## Representative executable example

The companion `typed-sharing.json` is unchanged from the reviewed candidate. Its instructions read: collect up to two text, image or audio pieces per person; for each eligible accepted piece, let a non-author claim it; wait for acknowledgment; then share that actual piece with attribution. The author retains access. Apart from the author, only the reader sees it before explicit sharing. Timeout skips publication; an assigned reader keeps saved access. An empty pool creates no sharing rounds.

This definition is package data, not app-name dispatch. The host supplies actor/date bindings and closes the collection. It renders/plays material, authenticates users, stores media and state, serializes actions and retains access rules across restart. Read access never gives submission ownership.

The full repository packet `format/0.23/HOST-REVIEW.md` includes the executable creative-continuation definition and a separate privileged host-binding request. The creative flow collects up to two continuations, privately votes for one current choice, counts/selects/presents and feeds the selected piece into a named written next round. Random positive ties and nonempty zero-count fallback are explicit; an empty candidate set remains `no_candidates`.

## Evidence and limits

Fresh runtime and authoring reviews cleared the exact implementation pin: both complete durable hosts, 108 traces, 324 invalid definitions, all 40 examples, all 73 actual historical comparisons per language, 860 independent observable assertions and 14 inspector tests. Actual PNG/WAV, private grants, mixed quotas, ordering/identity, races, retries, restart, stable randomness and cross-instance handoffs passed. A different source-response/private-pairs workshop demonstrated reuse. Evidence is in `validation/0.23/EVIDENCE.md` and `INDEPENDENT-REVIEW.md`.

Deferred rules include designated-person ties with timeout/fallback, previous-winner-derived eligibility, video, balanced/two-offer distribution, self fallbacks, unassigned responses, preparation offers, unlimited streams and product thread lifecycle. Provider SMS, calendars/accounts/media infrastructure, successor scheduling and interface design remain host responsibilities. Settled deadlines do not silently admit later processing. Local SQLite evidence does not certify distributed/production/load behavior. Six complete historical migrations remain six; fourteen remain incomplete. No faithful product-parity or 1.0 claim follows.

Please distinguish a remaining failure of the core activity from a request for faithful product parity. For a core failure, identify the instruction, participant-visible result or supported reference that prevents the activity. For parity, identify the product rule and whether it is essential to adoption or an optional refinement.
