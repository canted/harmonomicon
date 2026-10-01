# Host review packet — candidate 0.23

Prepared for user submission; not sent. Candidate 0.23 is an incremental local candidate based on completed independently reviewed 0.22. [Evidence](../../validation/0.23/EVIDENCE.md), [profile](readiness-assessment.md), [compatibility](COMPATIBILITY.md) and [decision record](DECISIONS.md) state the demonstrated boundary. The final 0.23 implementation pin still needs fresh independent runtime review.

## Activity to try

Give the group a real starting piece with its author and origin. Each person may offer up to two text/image/audio continuations in total. They privately vote for one actual contribution and may change that current choice until closing. Count, select the highest count with random positive-tie resolution, and present the counts and selection. If candidates exist but no votes are counted, choose a candidate randomly; if there are no candidates, present that empty outcome. The selected contribution becomes the actual source for one private written continuation per person in the explicitly named next round.

The executable [typed continuation](examples/typed-continuation.json) follows six recognizable instructions. Hosts supply authorized starting material and actor/date bindings; storage, clocks, media players and successor launching remain host duties. The [retained five-step walkthrough](CREATIVE-CONTINUATION.md) also demonstrates the simpler single-entry 0.22 composition without changing its semantics.

```json
{
  "format": "harmonomicon.activity-package/0.23",
  "id": "org.harmonomicon.example.typed-continuation",
  "version": "0.1.0",
  "content": {
    "language": "en",
    "title": "Choose and continue a supplied piece",
    "summary": "Propose up to two typed continuations, select one, then use the actual selected contribution for a written next round.",
    "setup": "The host supplies an authorized starting_piece binding, eligible actors and contribution/voting windows. Filling limits or receiving every vote does not close a window early.",
    "prompt": "Choose and continue a supplied piece",
    "participant": "Read/play the actual supplied piece. Offer up to two text/image/audio continuations in total. Vote privately, then write one continuation of the selected piece in the next round.",
    "completion": "Present counts and selection; positive ties and nonempty zero-count outcomes choose randomly. No candidates gives no_candidates and blocks the next collection without fabricating source material.",
    "access": "The actual supplied starting contribution and its author/origin are visible to every bound viewer when collection begins. Continuations remain author-private until eligible candidates and attribution appear at voting entry. Ballots stay private after counts and selection appear. The selected piece is visible as input to the next round; new written submissions remain private."
  },
  "provenance": {
    "kind": "original",
    "credit": "Original Harmonomicon candidate 0.23 composition.",
    "rights": "Authors retain rights to their contributions; this definition grants no media rights."
  },
  "participants": {
    "min": 1,
    "max": 100
  },
  "requires": [
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
    "pool@2",
    "present@3",
    "private_views@1",
    "select@3",
    "serial_events@1",
    "tally@4",
    "text@1",
    "vote@3"
  ],
  "settings": {},
  "runbook": {
    "steps": [
      {
        "id": "continuations",
        "op": "pool@2",
        "prompt": "Offer up to two text, image or audio continuations of the supplied starting piece.",
        "kinds": [
          "text",
          "image",
          "audio"
        ],
        "perActor": 2,
        "visibility": "private",
        "round": "one",
        "input": {
          "binding": "starting_piece"
        }
      },
      {
        "id": "vote",
        "op": "vote@3",
        "prompt": "Choose one actual contribution.",
        "candidates": {
          "source": "continuations"
        },
        "changes": "allowed",
        "ballots": "private"
      },
      {
        "id": "counts",
        "op": "tally@4",
        "source": "vote"
      },
      {
        "id": "selected",
        "op": "select@3",
        "source": "counts",
        "policy": "policy:most_votes@1",
        "ties": "random",
        "noVotes": "random"
      },
      {
        "id": "result",
        "op": "present@3",
        "source": "selected",
        "prompt": "Here are the counts, outcome and selected contribution, if any.",
        "audience": "group"
      },
      {
        "id": "next",
        "op": "pool@2",
        "prompt": "Write one continuation of the selected piece.",
        "kinds": [
          "text"
        ],
        "perActor": 1,
        "visibility": "private",
        "round": "two",
        "input": {
          "result": "selected"
        }
      }
    ]
  },
  "inputs": {
    "starting_piece": {
      "type": "contribution",
      "kinds": [
        "text",
        "image",
        "audio"
      ]
    }
  }
}
```

## Concrete authorized handoff

This separate [request](typed-continuation-host-binding.json) is a privileged validation-host instance-creation fixture, not package JSON or a participant action. The previous local instance `continuation_one` must have a settled selection that is publicly projected and authorized for every destination viewer. The host resolves and attests its real source UUID/item, author/value/round and selection `via` separately. Merely knowing its ID is insufficient. Dates 100–400 are test-clock fixtures; real hosts resolve actual windows. The host launches a new finite instance explicitly; there is no automatic infinite successor loop.

```json
{
  "id": "continuation_two",
  "packageId": "org.harmonomicon.example.typed-continuation",
  "version": "0.1.0",
  "participants": [
    "Alice",
    "Bob",
    "Carol"
  ],
  "organizer": "Organizer",
  "hostBindings": {
    "starting_piece": {
      "instance": "continuation_one",
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
    },
    "next": {
      "actors": [
        "Alice",
        "Bob",
        "Carol"
      ],
      "opensAt": 300,
      "closesAt": 400
    }
  }
}
```

## Concerns addressed

| Concern | Executable contract |
|---|---|
| Choices derived from contributions | Frozen finally eligible actual candidates, stable UUID/source/item identity, real author and media authority. Multiple items and equal values remain distinct. |
| Vote changes | A concise allowed/prohibited setting, one current vote, exact retry handling and no changes after closing. |
| Private ballots and public totals | Ballot audiences remain separate from aggregate/result presentation. Explicit individual reveal is available. No universal anonymity promise. |
| Structured outcomes and ties | Counts, selected material/tied set/empty status and basis; uniform durable random policies. Calculation remains separate from presentation. |
| Continuing creative rounds | Declared qualified starting input, explicit selected result feeding the named later round, and host-launched separate instances with origin and handoff provenance. |
| Typed pooling consistency | One pool independently chooses accepted kinds and shared per-person quota. Compatible typed iteration, voting and one-source response consumers preserve attribution/access. |

Earlier text loops and source-response instructions already reused material in later steps. These candidates add selected typed outcomes, authoritative cross-instance inputs and now generic typed quotas/iteration; ordinary content reuse was not absent.

## Product rules still outside this profile

Designated-person tie decisions with timeout/random fallback and result-derived exclusion of a previous selected author remain deferred. Video, balanced/two-offer distribution, self fallbacks, unassigned responses, preparation offers, unlimited streams, product thread-ending/restart lifecycle, provider SMS rules and late processing after settled deadlines are not implemented. Hosts manage calendars/accounts/notification delivery/media/retention/UI; they must identify any external rule rather than claim it is defined by this package. Six complete historical migrations remain six; a useful witness is not faithful product parity.

The different [source-response/private-pairs workshop](examples/typed-response-workshop.json) collects several kinds and two items per person, assigns one non-self source per effective person, reveals only used linked pairs and preserves unused private material. It validates reuse beyond a creative voting activity.

Please distinguish a remaining failure of this core activity from a request for faithful product parity. For a core failure, identify the instruction, participant-visible result or missing supported reference that prevents the activity. For parity, identify the product rule and whether it is essential to adoption or an optional refinement. No submission, deployment, publication or 1.0 decision is included.
