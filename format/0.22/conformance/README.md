# Candidate 0.22 conformance

The corpus contains **73 engine traces** (57 retained from 0.21 plus 16 qualified-input/fallback traces), **231 invalid definitions** (175 retained plus 56 new), and **34 schema-valid examples** (30 retained plus four supplied-material examples). New supplemental checks include **56 setup/authority negatives**, **29 package schema negatives**, and **nine qualified-binding schema negatives**. These are supported-profile witnesses, not a claim that a prospective host's full product has migrated.

[Retained cases](cases.json), [image checks](../image_check.py), and [typed-artifact checks](../artifact_check.py) preserve earlier operation behavior. Their historical development and migration evidence remain documented in [candidate 0.20](../../0.20/conformance/README.md). The [checker](../check.py) compares independent Python and JavaScript outcomes, full actor projections, and resulting state. Compatibility checks execute all 57 retained traces through both historical 0.21 engines in separate processes and require exact outcomes, every actor view, and full state under the translated 0.22 envelope.

## Retained voting and finite-round witnesses

[Voting cases](voting-cases.json) contain explicit expected action outcomes and expected or forbidden view fields. [Voting checks](../voting_check.py) execute them and add malformed-definition, setup, serialized race, capability-negotiation, and random-result property checks.

| Trace | Meaning checked |
|---|---|
| Predefined identity, forbidden changes, retries | Distinct candidate IDs even when labels coincide; labels/indices/wrong source are rejected; one-submission behavior; accepted retry after settlement. |
| Current ballots, private ballots, public totals | Replacement counts one current slot; replay of the old accepted ballot does not undo the change; peer and organizer ballots remain private after totals/outcome appear. |
| Totals and explicit ballot reveal | Generic totals presentation is independent of the explicitly requested release of current ballots and voter attribution. |
| Group ballot visibility | Individual ballots are public immediately only when the definition chooses that behavior. |
| Source and voter eligibility | A withdrawn author is excluded at source closure; candidates then remain fixed. Final effective voters determine counted current ballots. |
| Unresolved tie | Exact top tied set; continuation is blocked with explicit status and predecessor round; a subsequent empty vote is presented honestly. |
| No votes | Candidate zero counts produce `no_votes`; no arbitrary candidate becomes next-round source. |
| No candidates | Empty counts and `no_candidates`; no fabricated ballot can be accepted. |
| Random tie and next-round input | Injected tie choice is durable; selected contribution/author/value/round becomes the saved next input; identical item IDs across rounds are distinct; stale first-round references reject. |
| Typed candidate values | Ready owned text/image/audio material remains typed and attributed; foreign or unready uploads reject before voting. |
| Retained typed pool version | `artifact_pool@1` can feed new voting without changing its contract; its candidate round is explicitly null. |
| Held-out proposal planning and pair exercise | The new selected outcome feeds first-step planning, followed by the existing pair/group collection family; no activity-name dispatch. |
| Empty proposal workshop | Planning is blocked without an invented source or plans; the pair discussion still opens with a useful empty-result prompt and retains pair privacy. |

Every new trace is resumed from serialized state at **every event boundary**, including rejected and replayed actions. Deterministic rules and injected ties compare exact expected results and full independent-engine states. Independent default host randomness is checked separately for selection from the highest tied set, one durable draw, stable read/retry/restart behavior, and transfer of a committed choice between engines. These checks do not require identical random algorithms or streams. Equal chances are a host policy guarantee; the reference hosts use their standard uniform random-integer primitives.

The 46 new invalid-definition cases include missing operation/policy/media capabilities, wrong and forward references, duplicate option IDs or round names, incorrect source types, nested new operations, malformed literal inputs, unsupported tie/eligibility/media/announcement settings, and executable-template-shaped content. Of these, 23 structural negatives also reject under JSON Schema; cross-step typing, identity uniqueness, and capability accounting additionally require semantic validation before execution.

Additional workshop probes check that an unresolved tie also blocks planning while the pair discussion still runs, survives restart, and retains pair privacy; an odd roster rejects rather than promising exact pairs. Additional ordered-action checks cover the exclusive closing boundary, same-timestamp change and close races, trusted configuration authority, newly bound effective voters, immutable setup on restore, and explicit unsupported-capability rejection before state creation. Actual concurrent requests, SQLite persistence, worker progression, media bytes/grants, restart, and recovery are exercised by the separate [durable host suite](../../../validation/0.22/README.md).

## Qualified contribution inputs and fallback outcomes

[Input cases](input-cases.json) and [input checks](../input_check.py) exercise the new typed chain independently of example names. Every declarative trace specifies action outcomes, full qualified candidate/result/input snapshots, expected or forbidden viewer fields, and saved instance/binding identity. Every event boundary is recovered and compared against uninterrupted execution in both engines.

| Witness | Observable guarantee |
|---|---|
| Qualified text input and current votes | Real outside-roster author and origin are preserved; candidate references use destination UUID/source/item identity; wrong origin, missing instance, stale source and copied round reject; current votes and private ballots retain their rules. |
| Image input retained into another round | Zero votes retain the actual image starting source with zero counts and `basis:retained_input`; its origin remains unchanged while the next input records the local handing-off selection/round. New audio continuation gets its own origin. |
| Audio handoff and random no-vote result | A settled selection pointer is distinct from immutable material origin. Random choice uses every frozen eligible text/image/audio candidate, leaves all counts zero, and reports `basis:random_no_votes`. |
| Single random candidate | Selection needs no random draw. |
| Omitted and explicit unresolved no-vote policy | `no_votes`, no selected material, and blocked dependent collection; its empty selection cannot invent retained material. |
| Positive unique outcome and ties | `most_votes` and `random_tie` bases remain distinct from no-vote fallbacks; positive-vote tie handling overrides the configured no-vote policy. |
| Zero candidates under every setting | Default, explicit unresolved, random, and retention all yield `no_candidates`, null selected/basis, empty tied set and no draw. |
| Individual disclosure choices | Private qualified ballots remain private after aggregate publication; explicit reveal and group ballots expose only the declared current-ballot behavior. |
| Null-round/opaque origin and standalone chain | Unrounded accepted material and Unicode item IDs retain exact identity; the new qualified chain also works without external input declarations or an attestation callback. |

The 56 new definition negatives cover required capabilities, declaration type/kind/name/count and consumption, new versus retained source versions, input/result typing, forward/nested references, static retention eligibility, unsupported fallback/media/permission/workflow/announcement shapes, and undeclared binding references. All 34 examples satisfy Draft 2020-12 Schema; semantic validation additionally enforces cross-step typing, declared-input consumption, direct pointer/origin consistency and capability accounting.

The 56 setup negatives require exact bindings and canonical lowercase UUID URNs, full author/value/kind/round/origin/handoff authority, ready origin media, and every destination viewer. The initial audience includes the organizer, original roster and all supplied future-phase actors. Direct Python and JavaScript constructor probes require an explicit attestation callback for fresh bindings and reject missing, false, non-boolean-success or exceptional authority; callback mutation cannot change saved snapshots or reader sets. Trusted restore preserves prior attestation without silently substituting a fresh source.

Ordered configuration probes deny a new viewer unless **every** retained input is authorized, including future-used inputs and input history reached through an unchanged window operation. Denial preserves actor bindings/controls and grants no projection. Successful authorization exposes the same immutable starting snapshot. Actor actions cannot inject bindings/instance identity or configuration authority. Eight declared inputs are demonstrably consumed and retained; nine validly named declarations reject.

Fallback checks compare exact deterministic/injected outputs, candidate identities, all zero counts, selection bases, and round/pointer lineage. Default randomness is checked independently for eligible-set membership, stable read/retry/restart results, and transfer of the committed selection between engines. No identical cross-host random stream is required. Same-timestamp close/submission ordering, exclusive deadlines, final source-author withdrawal independent of voter eligibility, final voter withdrawal, accepted retry, and unsupported negotiation also have explicit outcomes. [Durable host trials](../../../validation/0.22/README.md) add authoritative source lookup, actual byte/read grants, concurrency, transactions, worker/restart behavior and multi-instance handoff.

## Retained author-facing examples

- [Predefined poll](../examples/predefined-vote.json): fixed named options, private ballots, forbidden changes, an unresolved-tie outcome.
- [Contribution contest](../examples/contribution-contest.json): accepted text/image/audio choices, changes until closing, private ballots, public totals and selection.
- [Creative continuation](../examples/creative-continuation.json): two finite named rounds, explicit seed, selection and presentation, then selected material supplied as the next source.
- [Proposal workshop](../examples/proposal-workshop.json): use an even roster of 4–12 to select a proposal, create first steps from it, and develop an experiment in pairs; if no proposal is selected, discuss what is needed before choosing.

The contribution examples explicitly disclose that eligible material and attribution become public on entering voting, even before the configured voting opening. Empty or unresolved outcomes block only dependent collections; later instructions still run. The instructions remain collect, vote, count, select, show, and continue. Host actor sets and resolved dates are instance inputs; ballots use stable references. Authors do not write a vote-replacement procedure, random algorithm, expression, hidden successor dispatch, or executable template.

Run `PYTHONDONTWRITEBYTECODE=1 python3 format/0.22/check.py`. Install [validation requirements](../requirements-validation.txt) in a Python environment and add `--schema` for schema verification. `python3 format/0.22/voting_check.py` runs retained voting checks; `python3 format/0.22/input_check.py` runs new input/fallback checks with schema validation. See [voting contracts](../voting-notes.md), [design checkpoint](../DESIGN-CHECKPOINT.md), and [durable host evidence](../../../validation/0.22/README.md) for the execution boundary and remaining limits.

## Explicit solo-schema regression

The reviewed 0.22 schema accepts `participants:{min:1,max:1}`, matching both semantic validators under host controls. `voting_check.solo_profile` validates the exact solo envelope through schema and both validators, then executes a solo ballot/close/selection in both engines with identical state and one counted vote. Previous candidate schemas remain historical and unchanged.
