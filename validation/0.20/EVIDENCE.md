# Candidate 0.20 local verification record

Run on the connected Mac, Python 3.14 / Node with `node:sqlite`, October 1, 2026. Existing optional schema dependency was reused; nothing was installed. Hosts/database fixtures were temporary and cleaned up. This is local conformance/recovery evidence, not production certification or 1.0 readiness.

## Commands and results

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/private/tmp/harmonomicon-schema-deps python3 format/0.20/check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.20/run.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.20/artifact_trial.py
node --test docs/viewer.test.mjs
git diff --check
```

- Engine/schema: **44 traces, 129 invalid definitions, 26 examples**. Both languages compare full state and actor projections, with restore at every event boundary. All **38 previous traces** retain outcomes/views. Six new normative traces plus boundary probes cover typed media authority, independent responses, initial/control setup, source withdrawal, source-ID identity, self-exclusion, unmatched/reuse, privacy, accepted retries and exclusive multi-day deadlines. Additional probes cover effective noncontributor recipients, audio source/image response, opaque actor identities and safe integer timing budget.
- Full app suite: both Python/SQLite and Node/SQLite pass the retained 34 HTTP traces, text/image legacy comparisons, pool/reader/rating/response races, unsupported/no-state, workers, immutable package versions, private history, restarts and all retained transfers. Original **29 PNG validator fixtures** pass, including bounded bomb decoding, raw chunk names and IDAT ordering; authenticated PNG upload regression probes remain included.
- Final typed trial: all six normative witnesses pass through **both actual authenticated hosts with every-event restart**; **32 direct PCM WAV fixtures** agree. Actual-byte tests verify own/private/assigned/published grants, foreign/unready/wrong-kind rejection and unused-source concealment. Pool-ID and linked-response races each have one winner; close/submission race preserves serialized order. Partial-success upload retry, accepted replay after closing/restart, effective actor additions/withdrawal, multi-day worker-only close and no reopening pass. Admin-only controls/binding provisioning and unsupported capability/operation setup preserve no-created-state guarantees.
- Typed transfer: a separately authored image exchange exports/imports with an identical digest, runs in both hosts and continues into retained pair-private reflection without interpreter changes. Intermediate and final recovery/projections match; separate group notes stay private.
- Three witness boundaries are explicit: Feedback replies are an external host table after primary closing, not an activity discussion operation; solo daily journal uses separate resolved 23/25-hour instance dates, not language calendar recurrence; simplified Chorus does not claim offers/choice/fairness/full product parity.
- Inspector: **14 tests pass**, catalog and previews match all 26 examples. Typed cards show kinds/visibility/source policies and the host-input boundary without invented roles/dates/encoding/outcomes.
- Documentation: local link targets checked for current root/candidate/validation documents; none missing. Whitespace check passes. No previous candidate implementation was edited.

The full app run passed before the final additional typed race/transfer assertions were added; the separate final artifact-trial run verifies those additions. Only documentation/inspection evidence changed afterward. Fixture corrections retained strict identity checks: the deterministic trace's response now has its own event ID rather than colliding with an accepted source event; the new pause fixture supplies its required prompt; pair expectations use the retained `{actor,value:{text}}` shape; sampler state is asserted through the actual `randomState` field. Runtime acceptance was not relaxed to accommodate these tests.

## Independent review checkpoint

Pin the local 0.20 commit and review [exact rules](../../format/0.20/artifact-notes.md), both typed modules, runtime hook points, hosts and `artifact_trial.py`. Focus on effective-actor/date controls, stable identity/assignment, media grants, deadline ordering and durable retries. Named policies make no crypto-randomness or exposure-fairness promise. Local reference profiles do not certify production rendering/storage/security/load, external app integration or nontechnical authoring usability. See the [pre-1 assessment](../../format/0.20/readiness-assessment.md) for exclusions and the next user review; no automatic version transition follows.
