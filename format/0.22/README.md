# Candidate 0.22: typed starting material and cross-instance continuation

**Status:** local incremental pre-1 candidate from [0.21](../0.21/README.md), prepared for independent review. No 0.22 merge, publication, deployment or 1.0 decision.

An activity can declare an actual text/image/audio starting contribution, collect continuations, privately vote, select and present an outcome, then let the host supply that real selected contribution to a separate instance. Stable UUID-qualified material identity, author/round provenance and a separate handoff pointer survive that transfer. Hosts attest the entire input and every viewer's access; input bytes never confer submission ownership.

Optional no-vote policies choose among eligible candidates randomly or retain the real starting source. Omission preserves the unresolved stop. Zero candidates always remains empty, including under retention. Random rules specify equal chances and durable selection, not a generator or identical cross-host sequence.

Earlier versions already reuse saved contributions through item loops and linked source/response instructions. This candidate adds qualified selected material and explicit cross-instance input authority, not ordinary output-to-next-step reuse.

- [Normative input/fallback contract](input-notes.md), [retained voting](voting-notes.md), [all operations](operations.md), [schema](package.schema.json)
- Independent [Python](runtime.py)/[JavaScript](runtime.mjs) interpreters and [Python](continuation.py)/[JavaScript](continuation.mjs) input modules
- Actual [creative package](examples/creative-continuation-input.json), [walkthrough](CREATIVE-CONTINUATION.md), separate [host request](creative-continuation-host-binding.json)
- [Source seed](examples/starting-contribution.json), [explicit source retention](examples/creative-retained-source.json), [different supplied-brief workshop](examples/supplied-brief-workshop.json)
- [Conformance](conformance/README.md), [durable evidence](../../validation/0.22/EVIDENCE.md), [supported profile](readiness-assessment.md)
- [Compatibility](COMPATIBILITY.md), [migration accounting](MIGRATION.md), [decision record](DECISIONS.md), [design checkpoint](DESIGN-CHECKPOINT.md), [neutral host review packet](HOST-REVIEW.md), [next-candidate pooling assessment](POOLING-ASSESSMENT.md)

```sh
PYTHONDONTWRITEBYTECODE=1 python3 format/0.22/check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.22/run.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.22/input_trial.py
```

Schema checking uses the existing optional validation dependency. Previous operation versions and historical files remain unchanged. Six exact historical migrations remain complete and fourteen incomplete. Dates/calendars, accounts, source registries, media processing/storage/rendering, successor launching and notification delivery remain host responsibilities.
