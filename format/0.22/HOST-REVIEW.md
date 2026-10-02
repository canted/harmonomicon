# Candidate 0.22 host review packet

Prepared for user submission; no external contact or publication. Candidate 0.22 is local and pre-1. This packet asks about a bounded creative core, not complete product parity.

## Executable core definition

The package declares an actual starting contribution, collects possible text/image/audio continuations, lets each participant privately change their current vote until closing, selects a most-votes result with random positive ties/random no-vote fallback, and presents counts and the selected material.

```json
{
  "format": "harmonomicon.activity-package/0.22",
  "id": "org.harmonomicon.example.creative-continuation-input",
  "version": "0.1.1",
  "content": {
    "language": "en",
    "title": "Creative continuation",
    "summary": "Propose continuations of a supplied starting piece, vote privately, and select material that the host can supply to a later instance.",
    "setup": "The host supplies the declared starting contribution with its real author and origin, eligible participants, and resolved collection/voting windows.",
    "prompt": "Continue the shared piece.",
    "participant": "Read or play the starting piece. Submit one text, image, or audio continuation, then choose one accepted continuation before voting closes. You may change your vote until closing.",
    "completion": "Show the counts and selected contribution. With candidates but no counted votes, choose one candidate randomly. With no candidates, show the empty result. The host may start another instance using an actual selected contribution.",
    "access": "The supplied starting contribution and attribution are visible to all bound viewers. Accepted eligible continuations and their authors appear when voting is entered, even before a later configured opening. Ballots remain private after public totals and outcome presentation. Voting waits for its closing time or trusted host close even if everyone has voted."
  },
  "provenance": {
    "kind": "original",
    "credit": "Original Harmonomicon candidate 0.22 activity example.",
    "rights": "Authors retain rights to their contributions. This package grants no media rights."
  },
  "participants": {
    "min": 1,
    "max": 100
  },
  "requires": [
    "artifact_pool@3",
    "audio_contributions@1",
    "clock@1",
    "contribution_inputs@1",
    "durable_state@1",
    "host_controls@1",
    "identity@1",
    "image_contributions@1",
    "policy:most_votes@1",
    "policy:random_candidate@1",
    "policy:random_tie@1",
    "present@2",
    "private_views@1",
    "select@2",
    "serial_events@1",
    "tally@3",
    "text@1",
    "vote@2"
  ],
  "settings": {},
  "inputs": {
    "starting_piece": {
      "type": "contribution",
      "kinds": [
        "text",
        "image",
        "audio"
      ]
    }
  },
  "runbook": {
    "steps": [
      {
        "id": "continuations",
        "op": "artifact_pool@3",
        "round": "continuation",
        "prompt": "Propose one continuation of the supplied starting piece.",
        "input": {
          "binding": "starting_piece"
        },
        "kinds": [
          "text",
          "image",
          "audio"
        ],
        "visibility": "private"
      },
      {
        "id": "vote",
        "op": "vote@2",
        "prompt": "Choose the continuation that should become our next starting piece.",
        "candidates": {
          "source": "continuations"
        },
        "changes": "allowed",
        "ballots": "private"
      },
      {
        "id": "counts",
        "op": "tally@3",
        "source": "vote"
      },
      {
        "id": "selected",
        "op": "select@2",
        "source": "counts",
        "policy": "policy:most_votes@1",
        "ties": "random",
        "noVotes": "random"
      },
      {
        "id": "result",
        "op": "present@2",
        "source": "selected",
        "prompt": "Here is the outcome and the selected starting material, if any.",
        "audience": "group"
      }
    ]
  }
}
```

This is package data; operation implementations are reusable host code. The selected value is a real candidate snapshot with author, UUID origin, source/item identity and round, rather than a copied title. Its media remains owned by its origin author.

## Host binding and next-instance handoff

The following is a separate privileged host instance-creation example, not part of the package or a participant request. The source instance must actually exist, and `selected` must be settled and publicly presented to every destination viewer. The numeric dates 100/200/300 are controlled test-clock fixtures; real hosts must supply actual resolved windows.

```json
{
  "id": "creative_two",
  "packageId": "org.harmonomicon.example.creative-continuation-input",
  "version": "0.1.1",
  "participants": [
    "Alice",
    "Bob",
    "Carol"
  ],
  "organizer": "Organizer",
  "hostBindings": {
    "starting_piece": {
      "instance": "creative_one",
      "result": "selected"
    }
  },
  "hostInputs": {
    "continuations": {
      "actors": [
        "Alice",
        "Bob",
        "Carol"
      ],
      "opensAt": 100,
      "closesAt": 200
    },
    "vote": {
      "actors": [
        "Alice",
        "Bob",
        "Carol"
      ],
      "opensAt": 200,
      "closesAt": 300
    }
  }
}
```

The host resolves the actual selection and saves `{candidate,via}`. Candidate origin remains where that contribution was accepted; `via` records which instance/decision handed it onward. For a first piece, a host can bind a real closed/publicly projected contribution with `{instance:"opening_material",source:"piece",itemId:"opening"}`. A [seed definition](examples/starting-contribution.json) supplies that source using retained typed collection. No caller-provided author/value/round claim substitutes for durable authority.

The same declared input handles text, ready image and ready audio. Both local hosts verify actual origin-owned PNG/WAV bytes, all destination viewers and durable grants without copying ownership. A later actor addition must have source access to every input; failure rejects before bindings/projections/grants expand. Host calendars, successor launching and other source registries remain external.

## Fallbacks and authoring boundaries

Omitted noVotes preserves the unresolved stop. With candidates and no votes, the example selects among frozen eligible candidates with equal chances; [the retention variant](examples/creative-retained-source.json) keeps the real starting piece instead. Both outputs retain zero counts and use a truthful fallback basis. Zero candidates always remains no_candidates, selected null and no draw, even when a usable source exists. Retention addresses proposed continuations without a decision; it is not a universal empty-activity fallback.

Candidates and authors publish at voting entry, including before a future opening. Voting waits for the deadline or trusted host close even when everyone voted. Ballots remain private after presentation unless the package explicitly reveals them. Public totals/attribution do not promise universal anonymity. Notifications do not guarantee delivery or attention.

## What this addresses

Typed accepted candidates, stable qualified identity/attribution, current-vote replacement, ballot/aggregate separation, structured most-votes outcomes and durable random policies, generic presentation, finite linked rounds and an explicit generic host-supplied cross-instance input are supported. Ordinary reuse already existed through text item loops and source-linked responses; this candidate closes the narrower selected typed origin/authority boundary.

## What remains outside scope

Designated-person tie decisions with timeout/fallback, previous-winner submission exclusion, multiple typed contributions, video, exposure/offer policies, participant-specific preparation, unassigned responses, unlimited streams, thread-ending/restart lifecycle, provider SMS rules, calendars/roles/general workflows and acceptance after settled closing remain outside this profile. Reference cross-instance bindings resolve inside one host; cross-provider transfer/retention/grant infrastructure is host-owned. Six exact legacy migrations remain six, not a faithful product migration claim.

## Review questions

- Does the executable creative core preserve the useful participation experience? Identify a concrete failure of that core separately from a faithful product-parity request.
- Are actual source identity/author/round and separate decision handoff sufficient for your host's starting-material UI?
- Which explicit no-vote policy fits the activity? Is the distinction between unvoted candidates and an empty candidate pool understandable?
- Can your host attest full snapshot/source-media authority for organizer, roster, future actors and later actor additions without a private-content bypass?

[Walkthrough](CREATIVE-CONTINUATION.md), [normative contract](input-notes.md), [supported limits](readiness-assessment.md), [compatibility](COMPATIBILITY.md), [conformance](conformance/README.md) and [durable evidence](../../validation/0.22/EVIDENCE.md) provide review entry points.
