# Candidate 0.23: generic typed pooling

**Status:** local incremental candidate based on completed independently reviewed [0.22](../0.22/README.md), implemented and validated locally, cleared by fresh independent runtime and authoring reviews at `68d3f8322bee337a27ea52c9af94d330ff8116e8`, merged into local main. Ongoing development follows real-world activity needs and the explicit limits below.

Authors can configure one typed pool independently for accepted text/image/audio kinds and up to eight contributions per person. The same actual items can feed compatible iteration, qualified voting or one-source assignment/response. Shared quotas, accepted order, attribution, privacy and media authority stay explicit; existing operation versions retain their exact meanings.

- [Typed pooling/consumer contract](pooling-notes.md), [schema](package.schema.json), [all retained operations](operations.md), [authoring](authoring.md)
- Independent [Python](runtime.py)/[JavaScript](runtime.mjs) engines and [Python](pooling.py)/[JavaScript](pooling.mjs) typed-pool modules
- [Mixed typed sharing](examples/typed-sharing.json), [three written ideas](examples/text-pool-vote.json), [one image](examples/image-pool-vote.json), [two recordings](examples/audio-pool-sharing.json)
- [Different source-response/private-pairs workshop](examples/typed-response-workshop.json), [supplied typed continuation](examples/typed-continuation.json)
- [Conformance](conformance/README.md), [durable evidence](../../validation/0.23/EVIDENCE.md), [supported profile](readiness-assessment.md)
- [Concise host review packet](HOST-REVIEW-SUMMARY.md), [full executable packet](HOST-REVIEW.md), [independent review](../../validation/0.23/INDEPENDENT-REVIEW.md)
- [Compatibility](COMPATIBILITY.md), [migration accounting](MIGRATION.md), [decision record](DECISIONS.md), [design checkpoint](DESIGN-CHECKPOINT.md)

```sh
PYTHONDONTWRITEBYTECODE=1 python3 format/0.23/check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.23/run.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.23/pooling_trial.py
```

Schema checking uses the existing optional validation dependency. Six new compositions supplement 34 retained examples. 108 engine traces, 324 invalid definitions and all 40 schema-valid examples pass; exact compatibility covers all 73 retained traces. Durable validation and material limits are recorded in the evidence. Earlier text item loops and source/response instructions already reused saved material; this candidate removes the configurable-text versus single-entry-typed pool split while preserving historical contracts. Six complete historical migrations remain six, fourteen incomplete. Clocks/accounts/calendars, media infrastructure, interface design, source registries and successor launching remain host responsibilities.
