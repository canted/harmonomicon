# Candidate 0.24 conformance

The corpus contains **108 retained engine traces** (73 retained from 0.22 plus 35 typed-pooling traces), **324 retained invalid definitions** (231 retained plus 93 pooling negatives), and **44 schema-valid examples** (40 retained plus four relay compositions). Supplemental relay checks add 18 traces and 26 invalid package/setup witnesses. Retained pooling checks include **32 setup, seed and clock-budget negatives**, **49 package schema negatives**, an exact 800-item expansion/recovery probe, ordered-action races and durable random-selection properties. Retained qualified-input checks additionally preserve their 56 authority/setup negatives, 29 package schema negatives and nine qualified-binding schema negatives. These are supported-profile witnesses, not faithful product-migration credit.

[Retained cases](cases.json), [image checks](../image_check.py), and [typed-artifact checks](../artifact_check.py) preserve earlier operation behavior. Their historical development and migration evidence remain documented in [candidate 0.20](../../0.20/conformance/README.md). The [checker](../check.py) compares independent Python and JavaScript outcomes, full actor projections, and resulting state. Compatibility checks execute all 73 retained traces through both actual historical 0.22 engines in separate processes and require exact outcomes, every actor view, and full state under the translated 0.24 envelope. No newly introduced iterator cache or qualified state is added to retained definitions.

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

Additional workshop probes check that an unresolved tie also blocks planning while the pair discussion still runs, survives restart, and retains pair privacy; an odd roster rejects rather than promising exact pairs. Additional ordered-action checks cover the exclusive closing boundary, same-timestamp change and close races, trusted configuration authority, newly bound effective voters, immutable setup on restore, and explicit unsupported-capability rejection before state creation. Actual concurrent requests, SQLite persistence, worker progression, media bytes/grants, restart, and recovery are exercised by the separate [durable host suite](../../../validation/0.24/README.md).

## Retained qualified contribution inputs and fallback outcomes

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

The 56 retained input-contract definition negatives cover required capabilities, declaration type/kind/name/count and consumption, new versus retained source versions, input/result typing, forward/nested references, static retention eligibility, unsupported fallback/media/permission/workflow/announcement shapes, and undeclared binding references. All 44 examples satisfy Draft 2020-12 Schema; semantic validation additionally enforces cross-step typing, declared-input consumption, direct pointer/origin consistency and capability accounting.

The 56 setup negatives require exact bindings and canonical lowercase UUID URNs, full author/value/kind/round/origin/handoff authority, ready origin media, and every destination viewer. The initial audience includes the organizer, original roster and all supplied future-phase actors. Direct Python and JavaScript constructor probes require an explicit attestation callback for fresh bindings and reject missing, false, non-boolean-success or exceptional authority; callback mutation cannot change saved snapshots or reader sets. Trusted restore preserves prior attestation without silently substituting a fresh source.

Ordered configuration probes deny a new viewer unless **every** retained input is authorized, including future-used inputs and input history reached through an unchanged window operation. Denial preserves actor bindings/controls and grants no projection. Successful authorization exposes the same immutable starting snapshot. Actor actions cannot inject bindings/instance identity or configuration authority. Eight declared inputs are demonstrably consumed and retained; nine validly named declarations reject.

Fallback checks compare exact deterministic/injected outputs, candidate identities, all zero counts, selection bases, and round/pointer lineage. Default randomness is checked independently for eligible-set membership, stable read/retry/restart results, and transfer of the committed selection between engines. No identical cross-host random stream is required. Same-timestamp close/submission ordering, exclusive deadlines, final source-author withdrawal independent of voter eligibility, final voter withdrawal, accepted retry, and unsupported negotiation also have explicit outcomes. [Durable host trials](../../../validation/0.24/README.md) add authoritative source lookup, actual byte/read grants, concurrency, transactions, worker/restart behavior and multi-instance handoff.

## Typed pooling and qualified consumers

[Pooling cases](pooling-cases.json) and [pooling checks](../pooling_check.py) contain 35 self-contained definitions with explicit expected action outcomes, qualified snapshots, private/public projections and saved state assertions. Every trace resumes at every event boundary and requires the same complete final state in the independent engines.

| Witness family | Observable guarantee |
|---|---|
| Mixed and kind-specific quotas | One shared per-actor maximum across text/image/audio; exact quotas 1, 2, 3 and 8; filling a quota does not close collection. Equal text values and repeated audio refs under distinct IDs remain distinct accepted items. Duplicate IDs, quota overflow, foreign/unready/wrong-kind material and late actions reject atomically. |
| Withdrawal and readdition | Previously accepted entries still consume quota. Only finally eligible source authors and readers enter the frozen iterator/candidate set; historical entries and replay ledgers remain saved. An entirely withdrawn source produces no iteration. |
| Typed item sharing | Text, image and audio iterate in acceptance order. Public record context contains only the qualified ref, never author/value. Only a claimed reader sees the actual attributed assignment. Self, outsider, competing and stale claims/acknowledgments reject; explicit acknowledgment publishes exactly that item. |
| Reader and timeout boundaries | A participating organizer has the same source-effective eligibility as other actors. No non-self reader skips immediately; claim/acknowledgment timeouts publish null. Ordinary local instructions still run after a skipped reveal. Empty/missing quota slots create no item or loop record. |
| Multiple-item source assignment | Effective/contributor recipients occur once, in roster order. The next eligible author policy uses that author’s earliest accepted item; saved assigned sources retain exact origin/value/attribution. Responses remain one immutable entry per actor and private until explicit linked reveal; unused private sources stay private. |
| Retained seeded sampling | An independent oracle checks the retained exact sampler over non-self accepted items, including multiple items by one author. Zero/one eligible item draws no randomness; seed, cursor and saved choices survive every-boundary restart. No exposure balance is claimed. |
| New qualified voting | Equal-value items remain distinct choices. Allowed changes replace one current vote; forbidden changes retain one-submission behavior. Invalid instance/source/shape and settled/stale references reject. Final effective voters determine counts. Ballot privacy survives public totals/selection unless group ballots or explicit release is chosen. |
| Outcomes and linked inputs | Unique, unresolved/random tied, default/explicit unresolved no-vote, random no-vote, retained-input and all zero-candidate policies have exact outputs. A qualified old `select@2` feeds the new pool; new `select@3` feeds later pools, preserving origin separately from handoff lineage. Retained external material creates no fabricated ballot/count row. |
| Compatible typed sources | New item, assignment and vote consumers execute over `artifact_pool@1/@2/@3`, qualifying real source identity and retaining null/named rounds. New consumers reject untyped `pool@1`; retained consumer versions reject the new pool. |
| Maximum bounds and clock | A direct-engine probe submits 800 items from 100 effective actors outside the original roster, processes exactly those 800 iterations, compares complete state and selected projections, then restores across both engines. Setup/configuration reserve the conservative 100×quota body budget for resolved dates. A null-close phase closed at the maximum safe clock retains deadline clamping: no invented reader/acknowledgment/publication. |

The 93 new definition negatives cover every used operation/policy/media token, malformed quotas/kinds/round/input/settings, forward or wrong-version sources, static retention eligibility, typed body restrictions/local output scope, prohibited implicit adapters and unsupported workflow/role/provider/media shapes. Of these, 49 structural negatives also reject under Draft 2020-12 Schema; semantic validation enforces cross-step types, references, scope and required capabilities before execution. Top-level typed consumers cannot nest inside any repetition, and attributed item operations are valid only in the new typed item body.

Supplemental checks deny forged external origin/author/value/round/handoff snapshots and unauthorized future viewers when consumed by the new pool, preserving the full audience authority contract from 0.22. Default random tie/no-vote results are checked separately per host for membership, one durable draw, stable reads/replays/restarts and committed choice transfer; identical random algorithms or sequences are not required. Actual byte/read grants, database transactions, concurrent requests and worker recovery are covered in the [durable host suite](../../../validation/0.24/README.md).

The six new examples use the same reusable contract through activity data: [mixed typed sharing](../examples/typed-sharing.json), [written idea selection](../examples/text-pool-vote.json), [image selection](../examples/image-pool-vote.json), [audio sharing](../examples/audio-pool-sharing.json), [held-out linked response workshop](../examples/typed-response-workshop.json) and [supplied-piece continuation](../examples/typed-continuation.json). Authors configure accepted kinds and a shared maximum, then collect, assign/share or vote, select and present. No activity-name dispatch or executable template is used.

## Retained author-facing examples

- [Predefined poll](../examples/predefined-vote.json): fixed named options, private ballots, forbidden changes, an unresolved-tie outcome.
- [Contribution contest](../examples/contribution-contest.json): accepted text/image/audio choices, changes until closing, private ballots, public totals and selection.
- [Creative continuation](../examples/creative-continuation.json): two finite named rounds, explicit seed, selection and presentation, then selected material supplied as the next source.
- [Proposal workshop](../examples/proposal-workshop.json): use an even roster of 4–12 to select a proposal, create first steps from it, and develop an experiment in pairs; if no proposal is selected, discuss what is needed before choosing.

The contribution examples explicitly disclose that eligible material and attribution become public on entering voting, even before the configured voting opening. Empty or unresolved outcomes block only dependent collections; later instructions still run. The instructions remain collect, vote, count, select, show, and continue. Host actor sets and resolved dates are instance inputs; ballots use stable references. Authors do not write a vote-replacement procedure, random algorithm, expression, hidden successor dispatch, or executable template.

Run `PYTHONDONTWRITEBYTECODE=1 python3 format/0.24/check.py`. Install [validation requirements](../requirements-validation.txt) in a Python environment and add `--schema` for schema verification. `python3 format/0.24/voting_check.py` runs retained voting checks; `python3 format/0.24/input_check.py` runs retained input/fallback checks with schema validation; `python3 format/0.24/pooling_check.py` runs typed-pooling checks with schema validation. See [voting contracts](../voting-notes.md), [design checkpoint](../DESIGN-CHECKPOINT.md), and [durable host evidence](../../../validation/0.24/README.md) for the execution boundary and remaining limits.

## Explicit solo-schema regression

The reviewed 0.22 schema accepts `participants:{min:1,max:1}`, matching both semantic validators under host controls. `voting_check.solo_profile` validates the exact solo envelope through schema and both validators, then executes a solo ballot/close/selection in both engines with identical state and one counted vote. Previous candidate schemas remain historical and unchanged.

## New 0.24 relay conformance

[relay-cases.json](relay-cases.json) and [relay_check.py](../relay_check.py) exercise exact first-valid outcomes, public/private projections, queue/tickets, exclusive deadline, prior-author order, safe-clock non-resumability, roster authority and every-boundary restart. The checker additionally tests invalid definitions/setup, duplicate qualified queue aliases, a 100-transition churn cap and a different private-pair composition. Actual races, media/queue authority and successor retries are in [relay_trial.py](../../../validation/0.24/relay_trial.py).
