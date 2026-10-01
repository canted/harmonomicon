# Candidate 0.21 supported profile for review

The core activity language now supports a finite collect → vote → select → present → continue procedure using explicit package data. prospective host app is another prospective host application whose adoption feedback motivated this increment. Neither faithful prospective host app product migration nor 1.0 readiness is claimed.

The four new examples demonstrate a predefined poll, a text/image/audio contribution contest, two creative rounds with an explicit selected-contribution input, and proposal selection followed by shared planning and retained private-pair deliberation. Hosts dispatch on operation/policy tokens, never activity IDs. Voting changes are a setting; most-votes and tie resolution are policies; presentation carries a structured result. Authors describe meaningful activity choices, not replacement or random-number machinery.

## Demonstrated behavior and invariants

Stable candidate source/item identity and attribution; final source eligibility; candidate publication; optional one-current-vote replacement; no duplicate counting; private ballots/public totals; optional explicit individual reveal; exact counts; unique/tied/no-vote/no-candidate outcomes; uniformly selected durable random ties; whole typed result presentation; explicit unique rounds and predecessor inputs; rejected stale/wrong references; blocked empty/unresolved continuation; authenticated media grants without ownership transfer; exclusive deadline and serialized races; accepted retries, worker progression and restart.

All retained 0.20 behavior remains within its original contract: form collections, turn-based stories, pools/claims, private groups, fixed recurrence, routed scoring, typed assignment/responses and trusted controls. The candidate keeps the finite runbook bounds (32 steps per sequence, 64 globally unique declared IDs), 100 actors per effective phase and 256 bound identities. A five-instruction full creative round allows six explicit rounds within one 32-step top-level sequence; no arbitrary looping or indefinitely running orchestration is added.

Evidence entry points: [engine conformance](conformance/README.md), [new voting checker](voting_check.py), [durable voting trial](../../validation/0.21/voting_trial.py), and [verification record](../../validation/0.21/EVIDENCE.md). Local independent Python/JavaScript engines and SQLite hosts validate the profile. These are execution/contract witnesses and authoring review inputs, not a nontechnical usability study or production host certification.

## Host duties and remaining limits

Hosts authenticate/enroll actors, resolve dates/timezones, retain ordered durable state, progress deadlines, provide unbiased tie selection, attest immutable ready owned media, grant bytes from projected views and render typed results. Account roles, date calendars, notification channels/attention, interface design, blobs/transcoding, publication and ordinary discussion remain host responsibilities. The organizer has no private-content bypass. Private ballots are an access guarantee, not universal anonymity; aggregate totals and candidate attribution can reveal information in small groups.

The following remain outside the supported contract:

- Designated-person tie policy with timeout/random fallback, and package-enforced result-derived eligibility such as previous-winner exclusion. Hosts may explicitly select effective submitters/voters, but must label any result-dependent product rule they enforce outside the package.
- Unlimited activity streams, thread-ending/restart product lifecycle, video, multiple typed entries per actor, exposure-balanced/two-offer assignments, self fallback, unassigned responses and participant-specific preparation offers.
- Replacement/moderation of contributions, nested typed/voting operations, arbitrary expressions/templates, a universal role/permission/calendar language, provider SMS rules and acceptance after a settled deadline.
- Direct voting on arbitrary structured forms or linked-response records; new voting sources are typed pools. Initial literal round material is text; selected image/audio material can feed subsequent rounds. No external cross-instance result-import or running-instance migration contract is supplied.

[Decision record](DECISIONS.md) assesses reuse and dependencies for deferred requests. None is necessary for the required four witnesses. Six exact historical migrations remain complete and fourteen remain incomplete. The simplified witnesses must not be counted as faithful Daily/Chorus or complete prospective host app support.

The local serial SQLite profile does not establish distributed ordering, performance/load, storage-failure robustness, general rendering safety or production integration. PNG/WAV are reference upload profiles, not language encoding restrictions. Independent review and user decisions about this supported profile precede any later version or release.
