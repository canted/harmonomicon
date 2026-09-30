# Candidate 0.19: typed image contributions

**Status:** validated local candidate; pre-1.0. No 1.0 identifier, production integration or general completeness claim follows from this milestone.

Candidate 0.19 extends [0.18](../0.18/README.md) with encoding-independent `image_ref` values in ordinary, scheduled and recurring forms. `image_contributions@1` requires trusted host authority; uploads, bytes, processing and authenticated reads stay in the host. The local validation profile accepts bounded PNG uploads and advertises that limit explicitly. [Exact semantics and responsibilities](image-notes.md) distinguish that profile from the language's image type.

Twenty-three examples include scheduled image check-in, group-immediate image daily prompt and an additional private recurring image witness. Thirty-eight engine traces (34 retained plus four image traces), 114 invalid definitions, schema negatives and serialized restart checkpoints pass in independent Python and JavaScript engines. All 34 prior traces preserve outcomes and views. [Durable app trials](../../validation/0.19/README.md) test actual bytes, authority/privacy, races, replay, worker deadlines, partial-success retries, restart, legacy comparisons and authored transfer.

The [migration checklist](MIGRATION.md) records six complete translations and fourteen incomplete legacy examples. This is separate from core experience coverage: richer offers/choice/exposure balancing remain optional parity refinements. [Readiness assessment](readiness-assessment.md) identifies review-essential evidence and unresolved scope choices without defining or declaring 1.0.

## Entry points

- [Operation semantics](operations.md) and [authoring guide](authoring.md)
- [JSON Schema](package.schema.json), [Python runtime](runtime.py), [JavaScript runtime](runtime.mjs)
- [Reference witnesses](conformance/README.md), [image checks](image_check.py), [examples](examples/)
- [Coverage inventory](../../COVERAGE.md), [roadmap](../../ROADMAP.md)

```sh
PYTHONDONTWRITEBYTECODE=1 python3 format/0.19/check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.19/run.py
node --test docs/viewer.test.mjs
```

Schema validation uses the declared optional validation dependency. Existing candidate directories and package identities remain immutable; callers explicitly negotiate the candidate format and required tokens.
