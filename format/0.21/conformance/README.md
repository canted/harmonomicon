# Candidate 0.21 conformance

The corpus contains **44 retained engine traces plus 13 new voting and linked-round traces**, **175 invalid definitions** (129 retained plus 46 new), and **30 schema-valid examples** (26 retained plus four new). These are witnesses for the supported profile, not a claim that prospective host app's whole product has migrated.

[Retained cases](cases.json), [image checks](../image_check.py), and [typed-artifact checks](../artifact_check.py) preserve earlier operation behavior. Their historical development and migration evidence remain documented in [candidate 0.20](../../0.20/conformance/README.md). The [checker](../check.py) compares independent Python and JavaScript outcomes, full actor projections, and resulting state. Compatibility checks compare all 44 retained traces against candidate 0.20.

## New executable witnesses

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

Additional workshop probes check that an unresolved tie also blocks planning while the pair discussion still runs, survives restart, and retains pair privacy; an odd roster rejects rather than promising exact pairs. Additional ordered-action checks cover the exclusive closing boundary, same-timestamp change and close races, trusted configuration authority, newly bound effective voters, immutable setup on restore, and explicit unsupported-capability rejection before state creation. Actual concurrent requests, SQLite persistence, worker progression, media bytes/grants, restart, and recovery are exercised by the separate [durable host suite](../../../validation/0.21/README.md).

## Four author-facing examples

- [Predefined poll](../examples/predefined-vote.json): fixed named options, private ballots, forbidden changes, an unresolved-tie outcome.
- [Contribution contest](../examples/contribution-contest.json): accepted text/image/audio choices, changes until closing, private ballots, public totals and selection.
- [Creative continuation](../examples/creative-continuation.json): two finite named rounds, explicit seed, selection and presentation, then selected material supplied as the next source.
- [Proposal workshop](../examples/proposal-workshop.json): use an even roster of 4–12 to select a proposal, create first steps from it, and develop an experiment in pairs; if no proposal is selected, discuss what is needed before choosing.

The contribution examples explicitly disclose that eligible material and attribution become public on entering voting, even before the configured voting opening. Empty or unresolved outcomes block only dependent collections; later instructions still run. The instructions remain collect, vote, count, select, show, and continue. Host actor sets and resolved dates are instance inputs; ballots use stable references. Authors do not write a vote-replacement procedure, random algorithm, expression, hidden successor dispatch, or executable template.

Run `PYTHONDONTWRITEBYTECODE=1 python3 format/0.21/check.py`. Install [validation requirements](../requirements-validation.txt) in a Python environment and add `--schema` for schema verification. `python3 format/0.21/voting_check.py` runs the new suite with schema checking directly. See [voting contracts](../voting-notes.md), [design checkpoint](../DESIGN-CHECKPOINT.md), and [durable host evidence](../../../validation/0.21/README.md) for the execution boundary and remaining limits.

## Explicit solo-schema regression

The reviewed 0.21 schema accepts `participants:{min:1,max:1}`, matching both semantic validators under host controls. `voting_check.solo_profile` validates the exact solo envelope through schema and both validators, then executes a solo ballot/close/selection in both engines with identical state and one counted vote. Previous candidate schemas remain historical and unchanged.
