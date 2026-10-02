# Voting, structured results and finite continuation

Candidate 0.23 retains these versioned rules. [Generic typed pooling](pooling-notes.md) adds compatible new consumer versions without widening the old contracts.
Retained normative additions from candidate 0.21 to candidate 0.20. The new 0.22 typed input/version chain is defined separately in [input-notes.md](input-notes.md). Historical contracts remain unchanged. All operations below are top-level, with ordinary globally unique step IDs and preceding typed references. Require each used operation and policy. Pools/votes require `host_controls@1`; typed kinds require their existing media capabilities. Structural schema and semantic reference validation both apply.

## Contribution material and round input: `artifact_pool@2`

Exactly `id`, `op`, `prompt`, `kinds`, `visibility`, `round`, `input`. Prompt, kinds and visibility follow `artifact_pool@1`. Each effective actor may submit one immutable `{itemId,value}` under its existing text/image/audio shape and ready-owned-media authority. Dates and effective actors use the existing trusted input/control boundary. `round` is a name matching the step-ID syntax, unique across typed rounds and retained route-round identifiers in this package.

`input` is exactly one of:

- `null`: collect standalone material.
- `{value:{kind:"text",text:<nonempty scalar string>}}`: the initial shared piece.
- `{result:<preceding select@1 ID>}`: consume that selection's typed contribution.

The referenced selection must derive from a preceding `tally@2` over a `vote@1` whose candidates come from a typed pool. Literal option selections cannot serve as typed contribution input. Wrong types, forward/out-of-scope references, unknown results and duplicate round names invalidate the package before instance creation. This is a whole typed result reference, not a JSON path, expression, executable template or activity-name convention.

At collection entry save `input:{status,predecessorRound,candidate}`. Status is `none` for null, `initial` for a literal (candidate `{value:...}`), or the predecessor's `selected`, `tie`, `no_votes` or `no_candidates` status. A selected candidate preserves its complete immutable reference/value/author/round snapshot; predecessorRound is the originating pool's round even for an unresolved or empty result (null for a retained pool without a round). The input is visible to bound actors even if no separate presentation step was used; it exposes the selected candidate/status, not counts or ballots. Unresolved or empty predecessor results close the collection immediately with `blocked:true`, no contributions and no invented source. An ordinary usable input has `blocked:false`. The history explains why continuation stopped. Later instructions still execute normally, so authors can present the empty outcome explicitly.

A finite list of uniquely named rounds, connected by these references, is the supported model. Each submission is addressed to its actual pool step within its authenticated instance. The same item ID in another pool, a past round's execution key or another instance's state is not interchangeable. No host starts hidden successor instances for this capability. Hosts own enrollment, date selection, rendering and any schedule launching the finite activity. Unlimited streams, restart/thread-ending rules and result-driven calendars are absent.

## Voting: `vote@1`

Exactly `id`, `op`, `prompt`, `candidates`, `changes`, `ballots`. `changes` is `allowed` or `forbidden`; `ballots` is `private` or `group`. Candidates are exactly:

- `{options:[{id,label},...]}`: 2–32 options with distinct nonempty scalar IDs and nonempty scalar labels. Duplicate labels are allowed; identity is the ID.
- `{source:<preceding artifact_pool@1 or artifact_pool@2 ID>}`: accepted text/image/audio contributions whose authors are in that pool's final effective actor set.

Freeze the candidate snapshot when execution enters voting, after source closure, even if the configured voting opening is later. Candidate identity is `{source:<pool step ID>,itemId:<accepted ID>}`. Each typed candidate snapshot contains `ref`, `actor`, `value`, `round` (null for pool@1). Literal candidates use source equal to the vote step ID and contain `ref` and `label`. Their configured order is retained; typed candidates retain acceptance order. Source edits cannot reroll or replace candidates. Withdrawal before source closure excludes a candidate without erasing its accepted history.

Voting publishes the eligible candidate snapshots, including contribution attribution/value, to bound viewers. This explicit use as voting material can publish candidates from a private source pool. It does not reveal unrelated or withdrawn pool entries. Hosts authorize media reads through these projections; a viewing grant never confers submission ownership. The package's content/access description should tell participants that their accepted candidate material will be shown for voting.

Voting dates/actors use the retained `{actors,opensAt,closesAt}` host input and trusted current-phase configure/close rules. Null closing waits for trusted close. It never closes simply because everyone voted. Opening is inclusive; closing exclusive. Only an effective voter during the open phase can submit exactly `{candidate:{source,itemId}}`. Labels, indices, copied values, extra fields, unknown/withdrawn candidate IDs, wrong source IDs and stale step keys reject without counting. An empty candidate set closes voting immediately; no fabricated choice or ballot is allowed.

Each actor has one current ballot. With changes allowed, a new accepted event replaces that actor's current candidate in place. With changes forbidden, a second submission rejects even when it repeats the same candidate under a new event ID. Exact accepted-event retries replay by the retained actor/type/step/payload identity: retrying an earlier accepted vote after a later change does not restore the earlier selection. Changed reuse rejects. Rejection does not reserve an event ID. After settlement new votes and changes reject; an exact earlier accepted retry remains replayable.

Trusted actor changes can withdraw or restore voters. Aggregate results count current ballots only for actors in the final effective voting set; withdrawn ballots remain retained internally and in accepted-event history. A withdrawn actor cannot change a ballot until restored. Candidate eligibility is independent of voting eligibility and remains frozen. This rule is explicit host execution behavior, not a replacement workflow for authors.

## Ballots and participation disclosure

Private vote projections expose candidates, that viewer's eligibility/submitted state and own current ballot. They do not expose a total participation count or another actor's completion flag. The organizer has the same private-content limits. `ballots:"group"` shows all current accepted ballots with actor attribution immediately, including retained ballots of subsequently withdrawn voters. Their final counting eligibility is governed above. Accepted historical replacement ballots are not individual public records.

`reveal_ballots@1`, exactly `id`, `op`, `source` naming a preceding vote, publishes its current accepted ballots and voter identities permanently. It is separate from aggregate presentation. Omitting it preserves private ballots after totals and outcomes appear. Retained `reveal@1` does not accept vote records, and `tally@1` still requires its original explicit collection reveal.

This is access control, not a universal anonymity guarantee. Public candidates/attribution, small-group totals, outside information and host infrastructure can identify or suggest choices. Hosts still authenticate and retain private execution data. Empty totals disclose zero counted participation; individual nonparticipation identities are not invented.

## Counting: `tally@2`

Exactly `id`, `op`, `source` naming a preceding vote. Automatic after closure; no individual reveal prerequisite. Its internal output is `{counts:[{candidate:<snapshot>,count:<integer>},...],totalVotes:<integer>}`. Include every frozen candidate, including zero counts, in candidate order. Count each current eligible actor once; totalVotes is the sum. No candidates gives empty counts/zero total. No votes gives zero for each candidate. The result stays internal until an explicit presentation instruction; computing it does not itself publish ballots or totals.

## Selecting: `select@1`

Exactly `id`, `op`, `source` naming a preceding tally@2, `policy:"policy:most_votes@1"`, `ties:"unresolved"|"random"`. Random ties also require `policy:random_tie@1`. Its internal typed output retains `counts` and `totalVotes`, plus `status`, nullable `selected` candidate and `tied` candidates:

| Condition | Output |
|---|---|
| No candidates | `no_candidates`, selected null, tied empty |
| Candidates, zero counted votes | `no_votes`, selected null, tied empty; zero counts retained |
| Unique maximum with votes | `selected`, selected highest candidate, tied empty |
| Equal highest positive counts, unresolved policy | `tie`, selected null, tied highest candidates in candidate order |
| Equal highest positive counts, random policy | `selected`, one selected tied candidate, tied highest candidates retained |

Random selection must give each tied candidate an equal chance and select only from that set. No particular generator, seed sequence or cross-host identical draw is specified. No draw is necessary for zero candidates, zero votes or a unique outcome. Reference hosts use a uniform host random integer; trusted injected selections test each member without placing random machinery in activity definitions or participant requests.

Resolve once and atomically persist the complete selected snapshot as part of durable progression. Reads, retries and restart retain it. A failed transaction cannot expose an uncommitted selection. This local profile validates serial SQLite commits/recovery; distributed ordering or arbitrary storage failure needs host engineering and evidence.

A designated decision-maker with a timeout and random fallback is deferred. It needs specified authority, pending-result states and a deadline race contract. Authors cannot claim that policy using prose around the supported random/unresolved choices.

## Presentation: `present@1`

Exactly `id`, `op`, `source` naming a preceding tally@2 or select@1, `prompt` nonempty plain text, `audience:"group"`. Automatically save a permanent group-visible presentation record containing that output, including its selected contribution or unresolved/empty status. Calculation and presentation remain separate. This general facility shows counts or a structured decision, rather than a special winner declaration. It does not require reconstructing an outcome in message text or grant access to individual ballots.

The host renders the prompt and typed output for all bound activity viewers, including organizer and any participating organizer. It may offer notifications as its own product feature. SMS, push, proof of delivery or attention are not guaranteed. Automatic advancement retains the presentation in activity history, so a later active prompt cannot erase the result.

## Compatibility and unsupported choices

Candidate format negotiation remains exact; a 0.20 host rejects a 0.22 envelope. Hosts advertise these operations/policies independently and reject missing requirements before state creation. Existing operation versions keep their contracts. Definitions using new behavior need a new activity revision; running instances are not upgraded or transferred. A typed @2 pool is not silently accepted by assignment @1 operations; votes are its supported new consumer.

Result-derived submitter exclusion is deferred. A host can explicitly supply effective actors, including excluding someone, but no supported package policy calculates eligibility from a previous winner. Voting eligibility can be a different supplied set. This remains a limitation of faithful prospective host app support. No universal role/permission language is added.
