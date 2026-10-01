# Candidate 0.20: typed source exchange and host controls

**Status:** incremental local pre-1 candidate. No 1.0 definition, transition or readiness claim.

Candidate 0.20 extends [0.19](../0.19/README.md) with typed text/image/audio pools, saved non-self distribution, independent linked text/audio responses and explicit attributed reveal. Small trusted host controls provide effective actors, resolved multi-day dates and early closing; solo use and organizer participation are explicit opt-ins. Application roles, calendars, administration, discussion, uploads/drafts and publication remain host responsibilities. [Exact semantics](artifact-notes.md) specify the boundary, compatibility, identity, read grants and reference byte profiles.

Twenty-six examples include simplified Chorus, Feedback Round and daily music journal. Forty-four engine traces (34 retained, four image and six typed-artifact), 129 invalid definitions, schema checks and every-event serialized recovery pass in Python and JavaScript. All 38 previous traces preserve outcomes and actor views. [Durable trials](../../validation/0.20/README.md) retain prior migration/worker/race/transfer checks and add actual image/audio source grants, typed response races, host controls, solo use, long deadlines and typed exchange followed by private paired reflection.

The [migration checklist](MIGRATION.md) remains six complete and fourteen incomplete legacy migrations. Simplified examples do not count as exact product migrations. [Readiness assessment](readiness-assessment.md) records essential invariants, supported profile and explicit exclusions for subsequent user review.

## Entry points

- [Typed operations and host/media contract](artifact-notes.md), [all operations](operations.md), [authoring](authoring.md)
- [JSON Schema](package.schema.json), [Python](runtime.py)/[JavaScript](runtime.mjs) engines and independent [typed modules](artifacts.py)
- [Conformance](conformance/README.md), [typed witnesses](artifact_check.py), [examples](examples/)
- [Coverage inventory](../../COVERAGE.md), [roadmap](../../ROADMAP.md)

```sh
PYTHONDONTWRITEBYTECODE=1 python3 format/0.20/check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.20/run.py
node --test docs/viewer.test.mjs
```

Schema checks use the existing optional JSON Schema dependency. Format/capability negotiation is exact. Package exchange transfers definitions, not running instances, identities or blobs. Earlier candidate directories remain unchanged.
