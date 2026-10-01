# Candidate 0.21 local verification record

October 1, 2026, connected Mac; Python 3.14.7 and Node 25.5.0 with `node:sqlite`. Base `c7b3fb9`. Existing optional JSON Schema dependency at `/private/tmp/harmonomicon-schema-deps` was reused; nothing installed. All services bound loopback and all test databases were temporary. No user journal state or running product server was accessed or changed.

## Commands

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/private/tmp/harmonomicon-schema-deps python3 format/0.21/check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.21/run.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.21/voting_trial.py
git diff --check
```

`run.py` includes the new voting trial after the retained suites; standalone invocation is useful during iteration. The final runs followed the authoring-review corrections below. Schema is an optional validation dependency, not a runtime dependency. Local loopback server permission was obtained through the execution environment's approval review.

## Results

- **57 engine traces**: 44 retained plus 13 voting/linked-round witnesses, with exact full state/views for deterministic and injected cases and serialized recovery at every event boundary. **175 invalid definitions**, including 46 new semantic-invalid definitions and 23 new structural schema negatives. **30 schema-valid examples**. Independent Python and JavaScript implementations agree on deterministic rules. All **44 prior 0.20 traces preserve exact outcomes, actor views and full state** when run through the actual historical interpreter in a separate process.
- **Four new activities:** predefined options; accepted text/image/audio contributions with private ballots/public totals; two explicit creative rounds with selected-source continuation; proposal selection feeding shared planning and retained pair-private exercise. Empty/tied proposals explicitly block planning yet permit useful pair reflection. The held-out composition transfers identical definition bytes/digest and executes in both hosts without activity-name dispatch.
- **New durable host evidence:** both authenticated SQLite hosts pass exact predefined/linked traces with every-event restart, actual PNG/WAV candidate publication and read grants, ownership rejection, selected-media next-round input, one-current-vote counting, replay of an old accepted ballot without undoing a later change, enabled/disabled replacement races, duplicate candidate-ID races, close/action serialization, exclusive deadline rejection, aggregate-only presentation and explicit current-ballot reveal. Effective-source withdrawal freezes candidate eligibility; final-voter withdrawal removes that vote from counting without erasing its private history.
- **Random rules:** injected tied indices cover every tied member with exact expected selection. Unique/no-vote/no-candidate results consume no draw. Default host randomness is independently checked for tied-set membership and stable worker/read/retry/restart results, including actual unseeded durable hosts. Standard platform uniform random-integer APIs supply equal chances; no cross-host random sequence is mandated or compared. The retained seeded assignment algorithm and its exact vectors are unchanged.
- **Unsupported behavior:** each of the six new operations and both policies can be disabled separately; discovery omits it and setup returns `unsupported` before creating state. Invalid reference types, duplicate/forward rounds, wrong candidate sources, stale actions, unsupported tie/visibility/template/quota/video/eligibility settings reject. Participant HTTP requests cannot inject trusted time, actors, controls or tie fixtures.
- **Retained durable suites:** both hosts pass 34 retained HTTP traces, six scheduled check-in legacy scenarios, nine recurrence legacy scenarios and four image comparisons per language; workers, races, historical private views, package immutability, restart and all retained transfers. Six typed artifact witnesses pass with every-event restart and actual media. **29 PNG** and **32 WAV** validator fixtures remain passing. Six exact historical migrations remain complete; fourteen incomplete.
- **Documentation/repository:** local link targets in new candidate/validation Markdown resolve; prospective host app packet's executable code block exactly matches the creative example. New files are isolated to `format/0.21` and `validation/0.21`, with current-candidate accounting in root README/ROADMAP/COVERAGE. Previous candidates, inspector code/catalog, journal adapter and other user work are untouched.

## Independent authoring review and corrections

A separate read-only reviewer confirmed the six required capabilities and instruction-level abstractions, and found three example clarity issues: candidate material was disclosed at voting entry earlier than access text said; the exact-pair workshop needed an even-roster setup instruction; and empty/tied proposal outcomes reached an exercise whose prompt assumed existing plans. All three were corrected. Engine fixtures and both durable hosts now verify the empty/tied reflection path, blocked planning, no fabricated source/plans, pair privacy and restart. Odd workshop rosters reject at setup.

A temporary new-test assertion expected an earlier wording of the revised workshop prompt; it was corrected to the actual reviewed prompt without changing runtime behavior or weakening the behavioral assertions. The complete final host suite verifies the corrected fixture.

## Review boundary

The pinned candidate is prepared for independent runtime review and user review. Local evidence does not certify production auth/transport, distributed ordering, performance/load, arbitrary storage failures, media rendering safety, prospective host app integration or nontechnical authoring usability. [Supported profile](../../format/0.21/readiness-assessment.md) and [decision record](../../format/0.21/DECISIONS.md) distinguish required core capability from deferred designated-person ties/result-derived eligibility and product parity. No merge, push, publication, deployment, prospective host app contact or 1.0 claim occurred.
