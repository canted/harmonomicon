# prospective host app review packet: Harmonomicon candidate 0.21

Prepared for the user to submit. prospective host app is another prospective host app considering Harmonomicon support. This packet asks for adoption feedback; it does not claim faithful product parity or a release. Nothing has been sent to prospective host app.

## What this candidate changes

- Accepted contribution identities, attribution and text/image/audio values can become voting candidates. Ballots reference the actual source and item, never copied labels or positions.
- Authors state whether vote changes are allowed. Each eligible voter has one current counted choice; retries, closing and replacement are host execution guarantees.
- Private ballots and published aggregate totals are separate. Presenting totals or a selected result keeps individual ballots private. An explicit ballot-reveal instruction remains available.
- Most-votes selection produces a structured selected/tied/empty result. Random ties promise equal chances among tied leaders and a durably retained choice, without prescribing a generator.
- General presentation shows a preceding typed result, including selected material. No winner-specific announcement or executable template is needed.
- Explicit finite rounds consume a preceding selected contribution as source material. Round and source identities are retained; unresolved or empty choices block the dependent collection explicitly.

[Normative contract](voting-notes.md), [supported profile](readiness-assessment.md), [compatibility](COMPATIBILITY.md), [decision record](DECISIONS.md) and [validation evidence](../../validation/0.21/EVIDENCE.md) describe the guarantees and limits. Existing 0.20 operation versions and historical candidates are preserved.

## Executable creative continuation

The activity is: propose continuations of the opening piece, vote privately, select and show the result, then propose continuations of that selected piece and vote again. The following is the actual executable definition, also saved as [creative-continuation.json](examples/creative-continuation.json).

```json
{
  "format": "harmonomicon.activity-package/0.21",
  "id": "org.harmonomicon.example.creative-continuation",
  "version": "0.1.0",
  "content": {
    "language": "en",
    "title": "Continue the station song",
    "summary": "Write, vote, and select twice; the selected first continuation explicitly supplies the second round.",
    "setup": "Agree on the activity windows; the host supplies resolved dates and eligible participants.",
    "prompt": "Continue the station song",
    "participant": "Follow each instruction; submit or vote before its window closes.",
    "completion": "Finish after showing both round results. An unresolved or empty preceding result blocks only the collection that depends on it; later instructions still run and can show the resulting empty outcome.",
    "access": "Accepted eligible contribution values and their authorship become visible to all bound viewers as soon as voting is entered, even before its configured opening. Ballots remain private after totals and the selected result are shown. Selected source material is visible in the next round."
  },
  "provenance": {
    "kind": "original",
    "credit": "Original Harmonomicon candidate 0.21 activity example.",
    "rights": "Rights to participant contributions remain with their authors; this package grants no media rights."
  },
  "participants": {
    "min": 1,
    "max": 100
  },
  "requires": [
    "artifact_pool@2",
    "clock@1",
    "durable_state@1",
    "host_controls@1",
    "identity@1",
    "policy:most_votes@1",
    "policy:random_tie@1",
    "present@1",
    "private_views@1",
    "select@1",
    "serial_events@1",
    "tally@2",
    "text@1",
    "vote@1"
  ],
  "runbook": {
    "steps": [
      {
        "id": "continuations_one",
        "op": "artifact_pool@2",
        "round": "verse_one",
        "prompt": "Propose one continuation of the opening piece.",
        "input": {
          "value": {
            "kind": "text",
            "text": "At dusk, the old station began to sing."
          }
        },
        "kinds": [
          "text"
        ],
        "visibility": "private"
      },
      {
        "id": "vote_one",
        "op": "vote@1",
        "prompt": "Choose the continuation that should become our next starting piece.",
        "candidates": {
          "source": "continuations_one"
        },
        "changes": "allowed",
        "ballots": "private"
      },
      {
        "id": "one_totals",
        "op": "tally@2",
        "source": "vote_one"
      },
      {
        "id": "one_choice",
        "op": "select@1",
        "source": "one_totals",
        "policy": "policy:most_votes@1",
        "ties": "random"
      },
      {
        "id": "one_result",
        "op": "present@1",
        "source": "one_choice",
        "prompt": "Read the continuation selected for the next round.",
        "audience": "group"
      },
      {
        "id": "continuations_two",
        "op": "artifact_pool@2",
        "round": "verse_two",
        "prompt": "Continue the selected piece from the preceding round.",
        "input": {
          "result": "one_choice"
        },
        "kinds": [
          "text"
        ],
        "visibility": "private"
      },
      {
        "id": "vote_two",
        "op": "vote@1",
        "prompt": "Choose the continuation that should conclude our two-round piece.",
        "candidates": {
          "source": "continuations_two"
        },
        "changes": "allowed",
        "ballots": "private"
      },
      {
        "id": "two_totals",
        "op": "tally@2",
        "source": "vote_two"
      },
      {
        "id": "two_choice",
        "op": "select@1",
        "source": "two_totals",
        "policy": "policy:most_votes@1",
        "ties": "random"
      },
      {
        "id": "two_result",
        "op": "present@1",
        "source": "two_choice",
        "prompt": "Here is the final selected continuation and its vote totals.",
        "audience": "group"
      }
    ]
  },
  "settings": {}
}
```

The definition contains ten recognizable instructions: collect, vote, count, select, present; repeat once with the selected result as input. There is no dispatch on this activity's name. Authors may use the same instructions for a contribution contest or a workplace proposal; [proposal-workshop](examples/proposal-workshop.json) adds existing private-pair deliberation.

## Host integration boundary

At creation, a host supplies resolved effective actors and phase dates. For example, with actors `a`, `b`, `c`:

```json
{
  "continuations_one": {"actors":["a","b","c"],"opensAt":0,"closesAt":10},
  "vote_one": {"actors":["a","b","c"],"opensAt":10,"closesAt":20},
  "continuations_two": {"actors":["a","b","c"],"opensAt":20,"closesAt":30},
  "vote_two": {"actors":["a","b","c"],"opensAt":30,"closesAt":40}
}
```

These small Unix-millisecond values are validation fixtures, not proposed real product dates. Production dates and accounts come from the host. Hosts authenticate events, serialize and retain state, progress exclusive deadlines, supply unbiased tie randomness and render typed results. Media upload/readiness/ownership/retention/playback remain host duties. Package exchange transfers the definition, not running state, accounts or blobs.

A vote is submitted under the authenticated instance/current step with a payload such as `{"candidate":{"source":"continuations_one","itemId":"a-piece"}}`. The reference cannot accidentally choose the same ID from round two. The second round's saved input retains first-round identity/author/type and predecessor round. This candidate keeps one selected continuation as next source; building a cumulative edited document or thread is a product choice outside this witness.

## Rules still outside this candidate

This is a bounded core activity profile, not faithful reproduction of historical/current Daily. It does not implement designated-person tie decisions with timeout/random fallback or automatic previous-winner submitter exclusion. Hosts can separately supply submitter and voter sets, but must not claim that a result-derived product rule is enforced by this package.

Other excluded product rules: video; multiple typed contributions per participant; balanced/two-offer or participant-specific preparation assignments; self fallback; responses without assigned input; unlimited activity streams; thread-ending/restart lifecycle; provider SMS rules; accepting actions processed after settlement; a general calendar/role-admin/workflow system. Typed contribution replacements/moderation and direct voting on arbitrary form/response records also remain unsupported. Existing text pool quotas are unchanged.

No complete prospective host app migration is counted. Six historical Harmonomicon migrations remain complete; fourteen remain incomplete. Useful simplified witnesses do not increase that tally.

## Review request to distinguish core gaps from product parity

Please evaluate the executable core procedure above in the context of prospective host app adoption:

1. Does collect → vote → select → present → selected-source continuation now express the core creative activity? If it still fails, identify the concrete participation, visibility, identity or outcome rule missing from these instructions and a scenario showing the failure.
2. Which remaining requirements are necessary core activity semantics, and which request faithful prospective host app product behavior or host infrastructure? Label them separately so a narrower useful integration is not confused with full parity.
3. Would designated-person tie choice or previous-winner eligibility be a blocker for a bounded integration, or a later refinement? Explain the user-visible rule, rather than prescribing its implementation.
4. Are any of the settings, policies or references unclear to an activity author? Review the predefined poll, typed contest and proposal exercise too; the language should remain usable beyond one creative product.

Prepared for discussion, with no contact, merge, push, publication, deployment or 1.0 declaration performed.
