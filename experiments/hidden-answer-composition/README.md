# Hidden-answer turns: narrow contract versus composition

This experiment revisits the [Two Truths and a Tall Tale failure](../format-0.12-coverage-challenge/README.md) in the strict 0.12 audit. The [Family Dinner Project](https://thefamilydinnerproject.org/4week-program/support/games-and-activities/) says that each person presents two true facts and one invented fact, and the others guess which is invented. The source does **not** specify an app-stored answer, private ballots, one guess per person, scoring, or a reveal trigger. Those are choices in the digital variant below. The app cannot verify a speaker's real-world truth claims; it can only compare guesses with the answer that the speaker selected.

## The selected digital variant

These choices make one portable behavior testable; they are **not** attributed to the source:

1. The enrollment order determines speaker turns, once each. There are at least two participants.
2. On their turn, the speaker atomically publishes three nonempty statements and selects one index, `0..2`, as the invented statement. The statements become visible immediately; the selected index stays hidden from other participants.
3. Each other participant may submit one private index guess. The speaker cannot guess; later guesses and out-of-range indices are rejected. A participant sees only their own guess before reveal. Everyone may see the count of accepted guesses.
4. The speaker may reveal at any time, including when nobody guessed. The app then shows the selected index and all accepted guesses, omits missing guesses, and moves to the next speaker. There is no score, timer, edit, or answer-verification claim. The final reveal completes the instance.
5. Accepted event IDs can be replayed exactly without a second effect; changed reuse is rejected. This follows the established [0.12 event rule](../../format/0.12/README.md#instances-events-and-views), though the models here are experimental rather than 0.12 packages.

The [narrow definition](models/two-truths-narrow.json) names a `hidden_answer_guess@draft` contract fixed to three statements and index guesses. The [composed definition](models/two-truths-composed.json) names a `linear_turn_plan@draft` with four versioned operations: roster turns, publish with hidden answer, collect one response from each other participant, and speaker reveal/advance. Both are **draft representations**, not valid Harmonomicon 0.12 packages or published tokens.

## Held-out reuse check

The same source page also describes **List Game**: a person gives five things belonging to a category and others guess the category. The [held-out composed definition](models/list-game-composed.json) uses the **same four operations** with five visible items and a hidden text answer; guesses are text rather than indices. This is an explicit digital translation. The source does not define private guesses or speaker-controlled reveal for List Game either. The narrow Two Truths definition rejects this model; a new narrow contract or an expanded one would be needed.

| Comparison | Two Truths narrow | Two Truths composed | List Game composed |
|---|---:|---:|---:|
| Definition bytes, including whitespace | 241 | 503 | 491 |
| Visible item count | 3 | 3 | 5 |
| Hidden answer and guess type | item index | item index | text |
| Same tested event/view trace as Two Truths narrow | yes | yes | not applicable |
| Uses the same composed operation names | no | yes | yes |

The byte counts come from the checked-in JSON files and measure only definition size. The composed Two Truths definition is about twice as large. The [single Python probe](check.py) uses one shared experimental event engine for both encodings; it is deliberately **not** evidence that two independent app hosts can run the composition, nor a fair host-code-cost comparison. The held-out List Game shows configurability inside one hidden-answer-turn family. It does **not** establish a general composition grammar for polls, handoffs, or concurrent activities. The earlier [composition experiment](../composition/findings.md) likewise found reuse while its definitions and interpreters grew.

## Probe and decision boundary

Run from the repository root:

```sh
python3 experiments/hidden-answer-composition/check.py
```

The probe checks that both Two Truths definitions accept and reject the same actions, produce the same actor-visible views, hide the answer and other people's guesses before reveal, reject a second guess and invalid index, preserve replay behavior, and advance through all speakers. It then runs List Game on the composed definition, including text-answer validation and reveal. It also verifies that the narrow definition cannot import that held-out model.

**Finding:** The 0.12 failure remains, but the [original “narrow contract” classification](../format-0.12-coverage-challenge/README.md) was premature. One composed draft reuses its operations in a related held-out activity, at the cost of a larger definition. The primary change class is **composition versus narrow contract unresolved**. To settle it for a future release, the same candidate rules would need precise cross-language semantics, independent app-host implementation, conformance traces, and a comparison against adding separate narrow contracts across more unlike activities. No 0.12 normative rule changes in this experiment.
