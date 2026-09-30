# Simple digital patterns against format 0.12

This experiment tries to encode eight procedures from the [breadth survey](../../research/breadth-survey.md) in the [candidate 0.12 format](../../format/0.12/README.md). It asks a stricter question than the [25-card coverage audit](../../COVERAGE.md): can an app host enforce each selected **digital rule** from one imported package, without treating instructions to people as executable rules? The 0.12 format allows exactly one behavior contract per package. A package can direct offline conversation, but that text cannot validate a ballot, change an assignment, or calculate a score.

The selected set spans a timed changing-group sequence, an online poll, a hidden-answer guessing game, a private contribution pool, a cumulative story, an untimed three-prompt routine, changing partners, and repeated card scoring. These are not claimed to represent every activity in the survey. For offline originals, the target below explicitly states the digital translation being tested; it does not attribute that translation to the source.

## Test and classification rule

An **exact fit** means the package and 0.12 contract together determine the selected app-observable actions, acceptance conditions, phase transitions, stored result, and audience views. A person may still decide what to say, draw, or do away from the app. A text instruction alone does not count when the app is supposed to enforce the rule. A **slice fit** means the package determines the named digital slice but leaves other source steps to humans or other software. A **failure** has a concrete legal 0.12 trace that the target would forbid, or a required target trace that 0.12 rejects or cannot represent. This is a representability check, not a judgment of an activity's merit.

For each failure, the **primary change class** names the smallest plausible *design direction to test next*, not a proven implementation: 

- **Narrow contract:** one cohesive rule, such as a general option poll, could be defined by a new versioned behavior token within the existing package envelope. A complete game-specific contract would work only after every app host adds that game; it would not provide package-level composition.
- **Reusable composition rule:** the target combines recurring operations whose ordering, state handoff, or shared policy cannot be expressed by choosing one current contract. A future versioned composition contract could still fit inside today's one-`behavior` envelope.
- **Package structure:** the envelope itself would need to change, such as multiple independently versioned behaviors or nested package identities. This class requires evidence that a new single behavior token cannot express the case cleanly; this set did not establish that.
- **Composition design open:** combining rules in a package is needed for the broader authoring goal, but the exact reusable operations and their portable semantics are not yet settled.

## Results

| Selected digital target | Closest 0.12 attempt | Result | Primary change class |
|---|---|---|---|
| 1-2-4-All's fixed online stage timing and preassigned rooms | `guided_rounds@1` | **Exact for that coordination slice**; not the full practice | None |
| Moodle Choice: options, selection, and results | `timed_collection@1` | Fails | Narrow contract |
| Two Truths and a Tall Tale: speaker statements and group guesses | `timed_collection@1` / `offered_response_vote@1` | Fails for the selected digital variant | Package-level composition needed; rule design open |
| Gratefulness Grab Bag: two slips each, then staged reading | `timed_collection@1` | Fails | Reusable composition rule |
| Story by Sentence: timed turns continuing one story in a text adaptation | `sequential_handoff@1` | Fails | Reusable composition rule |
| See, Think, Wonder: facilitator-paced prompts and shared responses | `guided_rounds@1` / `permissioned_dialogue@1` | Fails | Reusable composition rule |
| Impromptu Networking: new partner chosen or assigned at each transition | `guided_rounds@1` | Fails for this target; preassigned rooms are a slice fit | Reusable composition rule |
| 25/10 Crowdsourcing: five independent card ratings and ranked reveal in a proposed digital translation | `guided_rounds@1` / `offered_response_vote@1` | Fails | Reusable composition rule |

**Count:** one exact *selected slice*, seven failed digital targets: one narrow-contract candidate, six composition candidates (one with its rule design still open), and no demonstrated package-structure change. None of the eight is claimed to be an exact digital reproduction of the entire source practice. The seven [nearest valid 0.12 attempts](nearest-0.12/) make the failure comparisons inspectable. The passing [package](packages/one-two-four-all-text.json) and [probe](probe.py) verify the selected 1-2-4-All timer, partition, and audience slice in the 0.12 reference model. The failures below are contract-level counterexamples; they are not claims that a particular app UI could never supplement 0.12 with non-portable behavior.

## Encoding attempts and failure witnesses

### 1. Fixed 1-2-4-All rooms and timing — slice fits

The [source instructions](https://www.liberatingstructures.com/1-2-4-all/) give a one-minute invitation, one minute alone, two minutes in pairs, five minutes in quartets, then seven minutes in the full group, with online variants. The checked-in package has those five durations and group sizes. Its instance supplies eight participants, four pairs, two quartets, and the full group before start. `guided_rounds@1` advances by the specified durations and gates text visibility by group. The [probe](probe.py) checks boundaries and views.

This says only that the **software coordination slice** fits. The source includes spoken discussion, facilitator choice of prompt and surfaced ideas, and possible mid-session adjustments; the package cannot decide what constitutes a good synthesis. Optional text is at most one contribution per participant per stage under `guided_rounds@1`, so this package must not be presented as a full chat implementation. This narrower claim follows the [0.12 guided-rounds contract](../../format/0.12/contracts.md#guided_rounds1) and the [existing activity card](../../research/activities/1-2-4-all.md).

### 2. Moodle Choice poll — narrow contract

[Moodle's Choice documentation](https://docs.moodle.org/405/en/Choice_module) describes organizer-defined options, one or multiple selections, optional changes, option capacities, and configurable result visibility. Test the minimal digital pattern: three named options, exactly one valid selection per participant, and a per-option tally visible after close. A `timed_collection@1` text package can put the choices in `content.prompt`, but its `submit` accepts **any nonempty text** and its post-close view lists attributed raw entries. A participant's `"fourth option"` is therefore accepted, and no tally is produced. `offered_response_vote@1` validates votes only on another participant's linked response in its source-caption procedure; it is not a general option poll. A versioned `choice_poll` behavior with option IDs, selection count, update/capacity policy, and result view could fit the existing envelope.

### 3. Two Truths and a Tall Tale — composition needed; rule design open

The [Family Dinner Project instructions](https://thefamilydinnerproject.org/4week-program/support/games-and-activities/) say each speaker shares two true facts and one invented fact; the others guess which is invented, then the group goes around the table. They do **not** specify app storage of the answer, ballot privacy, one guess per person, scoring, or exactly when to reveal. The [selected digital variant](../hidden-answer-composition/README.md) deliberately chooses these rules: the current speaker publishes three statements and a hidden selected index; each other participant may make one private index guess; the speaker may reveal at any time; the app shows the answer and guesses and advances to the next speaker. The app can compare a guess with the speaker's selected index, but cannot verify that the other two statements are true.

`timed_collection@1` cannot store a hidden answer alongside three public statements, validate index guesses, or rotate speakers. `offered_response_vote@1` accepts a ballot only on a submitted source-caption response, with its own deadlines and result policy; it cannot point a guess to one of three statements or withhold a speaker's selected answer. The [comparison experiment](../hidden-answer-composition/README.md) encodes the selected variant as both a narrow `hidden_answer_guess@draft` definition and a composed four-operation plan. Its single Python probe gives both the same Two Truths event/view trace and reuses the composed operations for a held-out List Game with text guesses. That shows reuse within one family but does not establish a general composition language. Neither draft is a 0.12 package. The narrow draft works only because the experimental interpreter has game-specific support; adding that same support to every app host would not let a package author assemble new activities. The 0.12 failure is firm, and the exact reusable rule design remains open.

### 4. Gratefulness Grab Bag — composition

The [source procedure](https://thefamilydinnerproject.org/fun_content/gratefulness-grab-bag/) asks each person to write **two** gratitude slips, place them in a bowl, and have different people read slips as the bowl passes. Guessing the writer is an optional variant, so it is excluded from this target. In a digital translation, the app would accept two independent slips per participant, pool them, and reveal or assign one slip at a time to successive readers without displaying the author's identity first. `timed_collection@1` rejects the second slip, then reveals all `{actor, value}` entries together. `ongoing_space@1` permits multiple entries but has no pooled draw or reader-turn rule. This combines reusable multi-item collection, concealed pooled selection, and staged reveal/reader assignment. The source does **not** specify a random draw algorithm, so this experiment does not invent one.

### 5. Story by Sentence — composition, with a source correction

The linked [Family Dinner Project page](https://thefamilydinnerproject.org/fun_content/story-by-sentence/) says a participant starts a story, speaks for no more than a minute, and passes it to the next person, who continues it. It does **not** require exactly one sentence per turn. The [breadth-survey row](../../research/breadth-survey.md) is corrected accordingly. The digital target here is an explicit **text adaptation**: each actor appends to one accumulated story during their turn, with a one-minute maximum before passing or resolving a missed turn. `sequential_handoff@1` has a fixed one-pass route and exposes only the immediate predecessor's value to the next actor; it does not maintain an append-only whole story or enforce a turn deadline. `competitive_handoff@1` has an attempt timer and fallback, but it also passes only the last accepted contribution and uses a different two-person offer rule. The missing combination is guarded turns, cumulative artifact append, and timeout/advance policy. Requiring each actor to paste the entire story into a free-text response would be an unenforced convention and would store full copies rather than appends.

### 6. See, Think, Wonder — composition

[Project Zero's instructions](https://www.pz.harvard.edu/resources/see-think-wonder) give an ordered observation, interpretation, and question routine, typically discussed in a group, with no fixed stage durations. The selected digital target lets a facilitator advance among three labeled response stages and posts responses to the group. `guided_rounds@1` supplies the three prompts but always advances on preset durations; a facilitator cannot wait for the group. `permissioned_dialogue@1` can advance manually, but its four prescribed roles, phase names, and event types do not accept a generic observation/interpretation/question stage. A reusable manually advanced prompt sequence with an explicit group-response policy fits this target. Human judgment of whether a response is observation or interpretation is outside this app rule.

### 7. Impromptu Networking — composition

The [source](https://www.liberatingstructures.com/impromptu-networking/) has an introduction, three short partner rounds with a new partner, and a full-group close. Its online instructions permit a facilitator to assign new breakout rooms at transitions. `guided_rounds@1` can schedule three preassigned partner partitions, and one *instance* can happen to have distinct partners, so that is a useful slice. The contract only validates each round's partition independently at instance creation. It has no event that lets the facilitator remix or assign breakout rooms **at a transition**, as described in the online instructions. It also permits an instance with the same pair in all three rounds. The source recognizes that repeats can occur, so this is a failure to encode the *regrouping step*, not proof that every repeat must be rejected. A reusable regrouping operation plus timed phases and transition authority is the composition to test. Any distinctness preference, odd-person trios, and late arrival would need exact policy choices; they are not inferred from the source.

### 8. 25/10 Crowdsourcing — composition, proposed digital version only

The [source](https://www.liberatingstructures.com/25-10-crowdsourcing/) asks participants to create idea cards, exchange cards repeatedly, score a held card from one to five without looking at earlier scores, then total scores and surface high-scoring ideas. It explicitly says the published procedure is for face-to-face use and does **not recommend** online use because of logistics. This test is therefore a proposed digital translation of its app-observable card, rating, and result rules, not a claim of a source-endorsed online version. `guided_rounds@1` can make five timed rounds but has no card identity, reassignment, numeric rating, or sum. `offered_response_vote@1` aggregates one private ballot on a revealed response, not five hidden scores per circulating card. The reusable pieces are artifact routing, a score event bound to a card and round, hiding prior scores until a rating commits, exact aggregation, and ranked reveal. A later scoring policy would also need to define ties and the source's irregular-card-count fallback rather than guess them here.

## What this changes in the research record

1. The 0.12 envelope did **not** fail this set: a single new behavior token could technically express any one finite procedure. The composition classification instead records recurring cross-contract operations and the risk of adding a separate monolithic contract for every arrangement. The [earlier composition experiment](../composition/findings.md) already found reuse in assignment and commit operations, while also finding that interpreter size and policy complexity rose.
2. The 25-card [coverage audit](../../COVERAGE.md) remains true under its stated **digitally mediated slice** definition. This stricter experiment shows why a “modeled” slice must not be read as source-equivalent. The next change should be judged against the concrete witnesses above, including whether a later contract supports them in independent app hosts as required by the [roadmap](../../ROADMAP.md#goal-for-10).
3. No tested case proves a need to change `format`, the top-level fields, or the one-`behavior` package envelope. A separate test of independently reusable child activities or concurrent behaviors would be needed before claiming a package-structure change.

## Run the positive probe

From the repository root:

```sh
python3 experiments/format-0.12-coverage-challenge/probe.py
```

The probe validates all eight checked-in packages against the 0.12 reference validator and exercises timing, privacy, pair/quartet views, and completion. It does not validate the other seven source procedures through an app host; their failures are witnessed by the normative 0.12 contracts above.

## Subsequent candidate evidence

[Candidate 0.13](../../format/0.13/README.md) implements package-level runbooks and tests the minimal poll, selected Two Truths variant, cumulative story, and a bounded manually advanced prompted routine. The [coverage update](../../COVERAGE.md#composed-candidate-013-evidence) records the tested digital variants and remaining gaps. This does not alter the historical 0.12 failures above.
