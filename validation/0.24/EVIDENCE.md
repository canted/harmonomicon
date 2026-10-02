# Candidate 0.24 local verification evidence

October 2, 2026. Base: completed 0.23 `ba0530038747f5ed0ee5570d232e2ec72db64a40`; isolated `codex/candidate-0-24`. Independent review is separately coordinated at the implementation pin; this record claims local verification only. No merge, push, publication, deployment or 1.0 decision.

## Commands

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/private/tmp/harmonomicon-schema-deps python3 format/0.24/check.py --schema
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/private/tmp/harmonomicon-schema-deps python3 format/0.24/relay_check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 format/0.24/compatibility_check.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.24/relay_trial.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.24/run.py
```

The existing optional jsonschema 4.26.0 installation was reused. The default Python lacked it; no new dependency install was needed. Localhost durable suites required sandbox permission to bind loopback. Validation uses temporary databases and test clocks; services stop after each run. Node supports node:sqlite. No real invitation messages are sent.

## Engine and schema evidence

- All **108 retained engine traces** and **324 retained negative definitions** pass in independent Python/JavaScript engines, including full state/views and every-boundary recovery. All 44 current examples and generated held-out definitions pass Draft 2020-12 schema. The inherited 73-trace comparison against separate 0.22 engines remains passing.
- **108 actual 0.23 retained traces** compare exactly with both separate historical engines under envelope-only translation: outcomes, full state, every actor projection. Prior files remain unchanged.
- **14 new relay traces** agree exactly across engines and recovery at every event boundary: first-valid race ordering and replay, invalid media, exclusive boundary/stale ticket, decline-retained partner, partner-before-decline, explicit loser-front/old-author order, odd tail/full pass with prior-author exclusion, small roster, late worker's full fresh window, non-resumable safe-clock exhaustion, withdrawal ticket retention, denied canonical newcomer, boolean ticket rejection and shared 24-hour expiration.
- **26 relay invalid package/setup witnesses** cover structural values/fields, capability declarations, missing/aliased queue input, wrong canonical, invalid seed/order, missing attestation and notBefore/null exhaustion. Structural schema negatives assert failure; semantic-only cross-reference/capability constraints are checked independently in both validators.
- Separate churn witnesses preserve failed identities and terminate at 100 failed replacement transitions with `failure_budget`, including a 99-transition state followed by one two-person expiry. A held-out first-valid/private-pair reflection composition passes without interpreter changes.

## Durable host evidence

Both independent SQLite hosts pass simultaneous valid invitee submissions with one canonical/closure/queue commit; accepted replay and restart; shared 24-hour fresh windows/carry-over; decline replacement while preserving the partner ticket/deadline; stale declined ticket rejection; expiry rotation with previous author still excluded; exact empty/null-canonical cooldown boundary and exhausted creation retry; canonical material preserved from its true earlier origin across a failed pass/retry; and non-resumable safe-clock closure/restart.

Two simultaneous successor IDs yield one creation and one queue_consumed. Failed invalid setup leaves no source claim, target or grants. Duplicate qualified source aliases reject. Source consumption keys qualified UUID/step, and commits with successor state/identity/grants/tokens/creation receipt. Exact creation retries return original identity after offers expire and restart; changed retries conflict. Initial responses contain credentials; durable receipts return identity/digest and permit trusted re-binding instead of plaintext token retention.

Actual PNG uploads exercise foreign owner, unready image retry, canonical publication and cross-instance byte grants after restart. A withdrawn but prebound origin viewer can join/read in the successor. A wholly new origin-unbound viewer is refused; queue or token copying does not grant material. New operation/policy/queue/seed capabilities negotiate separately before any state, tokens, grants or source claims.

The different first-valid/private-pair composition transfers one exact package/digest between durable hosts, matches full engine projections and preserves pair privacy through restart. The full retained host run passes all prior collection/group/scoring/schedule/image/artifact/vote/input/pooling races, privacy, grants, retries, workers and transfers. A separate retained pooling run also passed.

## Review and scope limits

[Design checkpoint](../../format/0.24/DESIGN-CHECKPOINT.md) preceded major implementation. Parent-coordinated early design critique clarified per-invitee tickets, loser-front order, full-pass versus failure-cap reasons, odd tails, single source consumption, creation retry, null canonical, newcomer authority and non-clamped clock exhaustion. These are implemented and witnessed; early design critique is not a completed implementation review.

Changes are limited to new format/validation 0.24 directories and root candidate accounting. Main, all earlier candidates, docs inspector and separate playground are untouched. Six complete 0.12 migrations remain six, fourteen incomplete. Source copy/queue input does not grant a new reader. Carry-over does not guarantee wins and can keep inactive people invited. Clock/delivery/storage/media/accounts/successor launching remain production host work. Local services do not certify distributed failure ordering, arbitrary storage errors, load/security, media rendering, notification UX, cross-provider trust or production product parity. Independent review and user readiness decision remain separate.

## Independent review corrections

Independent implementation review at `adc4e8bbb37ace209283acd7aa7dde7aed53b3d2` found two JavaScript/Python/schema parity defects: explicit queueInputs:null was treated as omission by JavaScript, and a lone surrogate in an attested queue identity outside the destination roster passed its queue shape validator. The narrow correction uses an own-property check for declarations and scalar-safe text validation. Exact negatives cover explicit null in both semantic validators and schema, high/low lone surrogates in saved order and canonical item metadata, plus a valid supplementary Unicode control. Both durable hosts refuse the malformed package before storing it. The relay/schema suite (14 traces, 26 negative package/setup witnesses) and both relay host suites pass after the correction; the full retained engine/schema suite also passes after the correction (108 traces, 324 negative definitions, all current examples); the separate exact 108-trace comparison with both 0.23 engines passes again. Independent reviewer recheck remains separately coordinated.
