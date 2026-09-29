# itch.io ranked game jam template

## Identity and context

This card describes itch.io's **configurable ranked-jam workflow**, not a single organizer's game jam. Organizers choose dates, eligibility, criteria, visibility, and voting rights. Teams may build games together; software coordinates submissions, comments, and ratings.

## Configured procedure

1. A host publishes a jam with submission start/end, optional theme and custom fields, rating criteria, a rating end, and a set of permitted voters.
2. During the submission window, an entrant chooses an itch.io game project and submits it. Project files and screenshots live on its project page; its jam submission gets a separate page and comment thread. The host may enable a jam community board.
3. After submissions close, permitted voters rate entries during the rating window. An optional rating queue assigns a selection of entries to voters to distribute attention and reach a minimum number of ratings.
4. At the end, ranked results appear unless the host has chosen to hide them for later release. The host may also supply a manual ranking criterion or judge feedback.

## Choices and exceptions

- Voting can be limited to submitters, contributors, judges, or public accounts. Criteria and vote exposure are configuration choices, not one universal jam rule.
- The host may hide the submissions list before the deadline, lock uploads during ratings, remove a submission, or generate a late-submission link. None is implied by the word *jam*.
- A non-ranked jam omits voting entirely and can focus on collaboration or exhibition. This card models the ranked branch.
- The documentation warns that contributor voting can distort results when one entry has many contributors. The rating queue improves distribution of reviews but does not guarantee impartiality or useful feedback.
- Brainstorming, team coordination, progress sharing, and playtesting may occur in the optional community or other tools; itch.io's jam workflow does not require these steps.

## Mechanisms and software boundary

**Mechanisms:** organizer configuration, submission window, project/submission distinction, optional community, eligibility, assigned review queue, private individual votes, aggregation, result reveal, moderation, late exception. The voting policy and ranking formula are host behavior that a portable package would have to specify more precisely than `pick_winner`.

## Source

| Primary source | Supports |
|---|---|
| [itch.io: Hosting a game jam](https://itch.io/docs/creators/game-jams) | Entire configurable workflow, including community, submission, ratings, queue, ranking, and exceptions |
