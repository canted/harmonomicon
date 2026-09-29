# Pass 4 findings

**Result:** The JavaScript and Python interpreters match the manually stated results for **12 conformance cases**, covering six contrasting activities and two technical capability/atomicity probes. Run `python3 experiments/check.py` to reproduce the comparison. This is evidence that the specified small vocabulary can be interpreted consistently for these traces. It is not evidence that the vocabulary fully describes the human activities or that either interpreter is production ready.

## What the traces establish

| Trace | Result within this contract | Source boundary |
|---|---|---|
| Physical stop and unwrap | A host-reported holder controls who may unwrap; wrong-holder and post-completion events reject. | Software does not sense the parcel or choose fair stops. [Pass the Parcel card](../research/activities/pass-the-parcel.md) |
| Concealed serial drawing | Before reveal, only the current artist receives guide marks and no artist receives prior sections through the role view. After reveal, sections become visible. | Real paper concealment, drawing quality, and route choice remain outside the interpreter. [Exquisite Corpse card](../research/activities/exquisite-corpse-drawing.md) |
| Changing groups | Invalid duplicate membership rejects atomically; host-supplied pairs and quartet are checked for full membership and allowed sizes. | The interpreter does not choose compatible pairings or enforce the source's stage durations. [1-2-4-All card](../research/activities/1-2-4-all.md) |
| Daily digital prompt | One test shows the post-to-view gate; another shows on-time and late posts across two occurrences. | The test clock is host-supplied. It does not verify a real once-daily schedule, time-zone rules, camera capture, or friend relationships. [BeReal card](../research/activities/bereal-daily-post.md) |
| Permissioned opinion | A responder's opinion cannot be delivered before the maker permits it; a refusal clears the request. | The interpreter cannot tell whether a question is neutral or an opinion is appropriate. It models a narrow part of the creator's process. [Critical Response Process card](../research/activities/critical-response-process.md) |
| Live or separate cooking | The organizer selects a branch and the other branch's submission event rejects. | Food preparation, safety, and whether a result was actually shared remain human facts. [Cook Along card](../research/activities/cook-along-challenge.md) |
| Missing host capability | A generic host rejects the singing probe without `low_latency_audio`; a digital prompt rejects without `media`. | A capability name alone does not measure actual audio delay or guarantee service quality. [Call and Response card](../research/activities/call-and-response-songs.md) |
| Invalid second action | The atomicity probe changes a field, then attempts an invalid numeric addition; both interpreters reject and retain the prior state. | This checks interpreter behavior only, not an activity. |

## Explicit choices made for the experiment

- The [Cook Along definition](definitions/cook-along.json) sets `late_policy` to `accept` for separate cooking. Its source specifies a sharing deadline but gives no rule for a late result. Acceptance in the fixture is an **experimental organizer choice**, not a rule attributed to the Family Dinner Project.
- The [daily prompt definition](definitions/daily-photo-prompt.json) permits one stored post per actor per occurrence and treats all participants as mutual friends. The cited help page does not define the account, deletion, and friendship mechanics needed to implement the entire product. These are simplifications for the gate trace.
- The [Exquisite Corpse definition](definitions/exquisite-corpse.json) lets the current artist name the next artist, subject only to being a known, different participant. It does not enforce a prearranged route or unique contributors. The physical activity needs a host agreement about the route.
- The [1-2-4-All definition](definitions/1-2-4-all.json) verifies each announced partition but not that a quartet was formed from the previous pairs. It also relies on a host `advance` event rather than real one-, two-, five-, and seven-minute timers.
- The [Critical Response definition](definitions/critical-response.json) permits a facilitator to advance phases even if nobody contributed. It preserves phase and permission order, not the whole conversational practice.

These limits are visible in the definitions and traces. The experiment must not present any one of them as the canonical version of an activity.

## Cost and architectural implication

The six behavioral definitions are roughly **165–353 formatted JSON lines each**. This verbosity and the dedicated `partition` operation show the cost of pushing every human interaction into a general transition language. More activities may require more built-in operations or an increasingly powerful expression language. That would require every conforming host to implement more semantics and safety checks, even if it only hosts simple dinner games.

The evidence supports a narrower conclusion than “the plugin format is solved”: a **portable data package and host capability negotiation are feasible for selected rules**, but this transition vocabulary is still an experiment. A smaller common core with named, well-defined mechanisms could cover frequent cases; unusual behavior may need a separately negotiated extension. Whether that split is sufficient requires more traces and host implementations. The research does not yet establish a universal behavior language.

## Important gaps before a public standard

1. **Human instructions and context.** Each JSON definition carries concise text and a research-card link, but not the full setup, access choices, variants, cultural context, or source rights. A distributable package would need a portable content bundle and attribution rules.
2. **Trust in reported events.** `actor` and `at` are supplied by the test host. Real hosts would need authenticated identity, trusted time, authorization, and a way to distinguish software-observed from human-reported facts.
3. **Durability and delivery.** The engines use in-memory state and opaque artifact strings. They do not specify persistence, retries, message delivery, idempotency, recovery after a crash, or who may delete a contribution.
4. **Visibility enforcement.** Views filter top-level fields. A host that exposes internal state directly would leak concealed contributions; nested fields and friend-by-friend audiences require finer policy. The experiment does not prove storage or API access control.
5. **Timing quality.** A `clock` capability does not prove scheduled delivery, and `low_latency_audio` does not prove acceptable end-to-end delay or jitter. [Networked music research](https://onlinelibrary.wiley.com/doi/abs/10.1002/cpe.4730) and [JackTrip's setup guidance](https://support.jacktrip.com/how-to-optimize-latency-when-using-jacktrip) make this distinction important for remote singing.
6. **Composition and lifecycle.** Morning Meeting and CASEL's practices are session frames around activities. This test has one activity instance at a time and no session composition, pause/resume, or migration between hosts.

## Next evidence needed

The next iteration should test a simpler, named-mechanism package against the same traces and compare authoring size and host implementation burden with this transition language. It should add a case with a genuinely novel assignment or scoring rule, a host restart/replay case, and a view test with different audiences. Those experiments would show whether the common core can stay small and where an extension boundary is justified. Until then, `activity-experiment/0.1` should remain separate from the eventual public standard.

The later [creative-practice revisit](creative-practice-revisit/README.md) examines the effect of game jams and shared journaling on these findings. It identifies whole-field view projection as a limit for per-author private content, while leaving the original twelve trace results unchanged.
