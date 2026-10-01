# Harmonomicon

![Harmonomicon pixel logo with the Harmonia symbol above the wordmark](assets/harmonomicon-logo.svg)

Harmonomicon describes a common format for group activities coordinated by software. An **activity package** describes one activity so different apps can run it. It tells the app what to show, when people can act, what each person can see, and how the activity moves from one step to the next.

Think of an icebreaker in a group chat, a collaborative drawing game on a website, or a daily creative prompt sent by an app. The app might send a prompt, collect contributions, pass a turn, or reveal a result. An activity package puts those instructions and rules together so they can be reused.

Each activity has its own package. Some packages need only a prompt and a timer; others need private submissions, assignments, and a record of what happened. People may step away from the app to take a photo or make something. The package describes the digital steps around that work: the prompt, submission, deadline, and sharing.

**Current candidate:** [0.16](format/0.16/README.md) lets a package assemble reusable steps into a runbook. It can collect contributions, reveal them, count choices, append to a shared story, and repeat steps for each participant. It also supports item pools, reader claims, private group rounds, and scheduled collection with saved instance settings. It now supports bounded numeric ratings and ranked results. Recurrence, media, and ongoing activity streams still need work before the [1.0 goal](ROADMAP.md#goal-for-10) is met.

## A simple example: one question for a group

Imagine an organizer starts a check-in for eight people in an app. At the start, the app asks everyone, “What made you smile today?” Each person can send one text answer. Answers stay private while people write. When everybody has answered, or an hour has passed, the app shows the answers to the group.

The package would describe the activity in terms like these:

| Part | What this activity says |
|---|---|
| Who takes part | The organizer and the invited participants |
| What people do | Answer one question with text |
| When it happens | Start at the chosen time; reveal when everyone answers or after one hour |
| Who can see what | A participant sees their own answer before the reveal; everyone sees the answers afterward |
| What happens if someone misses it | The reveal still happens after one hour |

The runbook has two steps: **collect answers**, then **reveal answers**. The collection step defines who can answer, what an answer looks like, its privacy, and when collection ends. The reveal step makes those answers visible. Another app can run the same [0.16 package](format/0.16/examples/check-in.json) if it supports those operations.

![Runbook structure generated from the check-in package: answer then reveal](docs/previews/check-in.svg)

## A richer example: image caption contest

Imagine a group caption contest run in an app. Instead of everyone captioning the same picture, participants first upload several images. The app then gives each image contributor two images uploaded by other people. They choose one and write a caption. More than one person may caption the same image.

The activity has a few stages:

1. Participants upload one image each before the image deadline.
2. After the image deadline, if at least three images are available, the app offers each contributor two images from other people. It favors images that have been offered fewer times.
3. Each contributor chooses one offered image and submits a caption. Captions stay private during this stage.
4. At the caption deadline, the app reveals the image-caption pairs. Participants vote for a caption by someone else; the app shows totals and any tied winners when voting closes.

The package says when each stage starts and ends, how the app chooses image offers, who can see captions before the reveal, and how votes are counted. It also says what happens if fewer than three images arrive or someone never submits a caption. In format 0.12, fewer than three images ends the activity without a group reveal; missing captions do not delay the deadline. A future runbook could select a different recovery step. Repeated requests for an offer should return the same two images, so a participant does not get a new choice by refreshing the screen.

The earlier [0.12 image-caption vote package](format/0.12/examples/image-caption-vote.json) runs this through one predefined behavior, with stored PNG images and audience-controlled access. Expressing its image assignments and voting as reusable runbook steps is part of the remaining work. Candidate 0.16 does not yet run this caption contest.

Other packages could describe a hidden drawing handoff in a browser, a recurring photo challenge, or an online game jam with progress posts and a final submission window. The activity package covers what the app asks, records, assigns, and shares, even when participants make something away from the screen.

## What goes in a package?

An activity package brings together:

- **Directions for people:** what the activity is, how to join, and what to do at each step.
- **Settings:** prompts, participant limits, and timing for the app to use.
- **Roles and actions:** who may submit, whose turn it is, and who can see the reveal.
- **Timing and visibility:** when actions are allowed and who can see each contribution.
- **Rules for interruptions:** what happens when someone is late, absent, or retries. Each step states how it ends and what happens to missing contributions.
- **App requirements:** features such as a clock, private views, or support for particular media.
- **Example runs:** sample actions and expected results that an app can use to check its implementation.

The app that runs a package is called an **app host**. It provides accounts, storage, scheduling, messages, and screens. It also executes the steps the package declares. The app host must say when it cannot provide a required feature or rule. Apps can be written in different programming languages and still use the same package when they implement the same behavior.

## Candidate 0.16 format

A package now contains a **runbook**: an ordered list of steps. Each step names an operation and supplies its settings. The package decides the sequence; the app implements the reusable operations.

For example, the [Two Truths package](format/0.16/examples/two-truths.json) repeats three steps for each speaker: collect visible statements with a private answer, collect private guesses from everybody else, and reveal the answer and guesses when the speaker advances. The [List Game package](format/0.16/examples/list-game.json) uses the same operations with five items and text guesses. A [poll](format/0.16/examples/choice-poll.json) uses collection, reveal, and counting. A [prompted routine](format/0.16/examples/see-think-wonder.json) uses three collections that the organizer advances. A [timed story](format/0.16/examples/timed-story.json) repeats a text-append step for each participant.

The [authoring guide](format/0.16/authoring.md) shows how these packages are written. The [specification](format/0.16/README.md), [schema](format/0.16/package.schema.json), and [operation rules](format/0.16/operations.md) define what an app must do. The [conformance cases](format/0.16/conformance/README.md) are sample actions and expected results that check an implementation.

In the [local trial](validation/0.16/README.md), separate Python and Node.js apps run the same composed packages with their own databases. The trial also creates a new package that performs a check-in followed by a story relay, transfers it between the apps, and runs it without changing either interpreter. The trial also transfers a new pooled-ideas-then-pairs arrangement. Tests check private group history, competing item IDs and reader claims, deadlines, retries, and restart.

New packages add a [two-item gratitude pool](format/0.16/examples/gratitude-pool.json), [changing partner rounds](format/0.16/examples/partner-rounds.json), [timed solo/pair/quartet rounds](format/0.16/examples/one-two-four-all.json), and [pooled ideas followed by paired reflection](format/0.16/examples/pooled-ideas-and-pairs.json). The package states how items are ordered and how groups are chosen; it does not infer those rules from instructions.

The [migration checklist](format/0.16/MIGRATION.md) accounts for all twenty earlier examples. It records available steps and missing rules; the scheduled check-in is now a complete migration, with nineteen remaining. Fourteen current runbook examples demonstrate selected digital activities, rather than all earlier functionality.

The [earlier 0.12 candidate](format/0.12/README.md) contains ten complete activity behaviors and PNG support. Its richer examples remain useful for testing which rules the runbook needs next. Support for one candidate does not imply support for the other.

A [scheduled check-in](format/0.16/examples/scheduled-check-in.json) keeps collection open until a chosen closing time, even when everyone answers early. Its package declares opening time, closing time, and question settings for the organizer to choose when starting it. The app validates and saves those choices. Another [package](format/0.16/examples/scheduled-check-in-pairs.json) follows the reveal with private paired reflection using the same scheduling rules.

A [proposal assessment](format/0.16/examples/proposal-assessment.json) shows another combination: collect ideas, assign each idea to two different reviewers, collect private 0–10 ratings, publish ranked totals, then invite private paired reflection. The package states the routing rule, score calculation, and what happens if a reviewer misses a deadline. Individual ratings stay private even after totals appear. A [25/10 digital translation](format/0.16/examples/crowd-scoring.json) uses five rounds and exact scaled averages; its [notes](format/0.16/scoring-notes.md) explain the digital choices.

## Package inspector

**[Open the live Runbook Structure diagrammer](https://canted.github.io/harmonomicon/)**

The [activity package inspector](docs/README.md) renders candidate 0.16 runbooks directly from their JSON. It lists all current examples and can open another package file locally. Select a step to see its operation and settings. Arrows show declared sequence and nesting; the viewer does not simulate an activity. Generated SVG diagrams display in this repository. Use the [live diagrammer](https://canted.github.io/harmonomicon/) in your browser, or follow the [local setup instructions](docs/README.md#run-locally). The live site is published from `docs/` on the repository’s default branch.

### Runbook Structure screenshots

**Group check-in:** collect private answers, then reveal them to the group.

![Group check-in in the diagrammer, showing Answer followed by Reveal and the selected step inspector](docs/screenshots/check-in.jpg)

**Two Truths and a Tall Tale:** a participant loop encloses Publish, Guess, and Reveal. The container declares repetition without expanding each participant’s turn.

![Two Truths and a Tall Tale in the diagrammer, showing three nested steps inside the Turns participant loop](docs/screenshots/two-truths.jpg)

## Roadmap

The [format roadmap](ROADMAP.md) records the candidate evidence and the requirements for 1.0, including composable packages. The [coverage audit](COVERAGE.md) maps the research examples to current rules and remaining gaps.

## Research

- [Activity cards](research/activities/) describe individual activities, including offline practices studied for possible digital adaptations. The [card template](research/activity-card-template.md) shows what each description records.
- [Breadth survey](research/breadth-survey.md) maps group activities from many settings as source material for digital versions.
- [Mechanism survey](research/mechanism-survey.md) compares recurring rules such as turns, assignments, deadlines, and reveals.
- [Digital activity cases](research/digital-activity-stress-cases.md) examine queues, missed turns, and complex rules run by software.
- [Game jams and shared creative practice](research/creative-jams-and-shared-practice.md) cover group projects, journaling, and recurring prompts.
- [Portable activity packages](research/portable-activity-packages.md) and [contract synthesis](research/contract-synthesis.md) record the open design questions and the current direction.

## Experiments

- [First contract experiment](experiments/README.md) defines several unlike activities and checks their behavior in JavaScript and Python; its [findings](experiments/findings.md) explain the limits.
- [Named mechanisms](experiments/named-mechanisms/README.md) test compact rules for handoffs and collections.
- [Offer flows](experiments/offer-flows/README.md) test a two-person relay and Cover and Response, including deadlines, retries, and saved offers.
- [Composition](experiments/composition/README.md) tests whether shared operations can describe different activities.
- [Creative-practice revisit](experiments/creative-practice-revisit/README.md) checks the earlier experiments against game-jam and journaling cases.
- [Ongoing activities](experiments/ongoing-activities/README.md) test project progress and repeated private or public practice.
- [Assignment-policy portability](experiments/policy-portability/README.md) specifies one offer rule precisely and checks it in JavaScript, Python, and Ruby.
- [Simple digital pattern audit](experiments/format-0.12-coverage-challenge/README.md) tries eight source-backed procedures against format 0.12, including exact failure witnesses and a runnable timed-room package.
- [Hidden-answer comparison](experiments/hidden-answer-composition/README.md) tests a narrow contract and reusable operations on Two Truths and a Tall Tale, then checks reuse on List Game.
