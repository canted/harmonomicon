# Scoring examples and their boundaries

## 25/10 proposed digital translation

The [Liberating Structures procedure](https://www.liberatingstructures.com/25-10-crowdsourcing) uses face-to-face idea cards, five 1–5 ratings, and a high-score reveal. When a card has an irregular rating count, the source suggests averaging and multiplying by five. It gives a minimum group size of fifteen and does not recommend online use because of logistics.

The [package](examples/crowd-scoring.json) is a proposed digital translation, not a source-endorsed online implementation. Its software rules are explicit:

- One text item per person, containing an idea and its first step; a five-minute collection window accepts partial participation.
- Five named routing/rating rounds, each with a one-minute rating window. Offset `1` through `5` in immutable roster order assigns five distinct non-author reviewers per item. This replaces physical passing with a deterministic digital rule.
- Enroll at least six participants so those five non-author assignments are possible. This digital minimum differs from the source's fifteen-person setting. People who missed the idea deadline may still review.
- Ratings stay private. Previous reviewers' scores are not exposed to later reviewers. Missing ratings are omitted, and exact mean-scaled scores use target count five. An idea with no ratings is listed as unrated.
- Publish a top-ten rank cutoff with every boundary tie. Equal results retain idea acceptance order; that order does not break ties. The source's spoken countdown is not app-observed.

These choices define the selected digital target's routing, recovery, arithmetic, and ties. The app does not observe physical passing, assess idea quality, or reproduce the whole social procedure. No random routing or source-specific activity code is hidden behind the package name.

## A second assessment and another use of numeric forms

The original [peer proposal assessment](examples/proposal-assessment.json) collects proposals, declares two distinct review rounds on a 0–10 scale, sums scores, publishes all ranks, and follows with private pair reflection. It reuses the same route/rate/aggregate/publication operations and existing group steps. Zero is a valid rating and differs from an absent rating. This package transfers between the independent apps without new activity code.

A [conformance witness](conformance/cases.json) also uses an integer field in a plain check-in form without routing or ranking. This checks that bounded numeric responses are a general form feature. Weighted grading, multiple criteria, arbitrary reviewer allocation, changing reviewers, and choosing one response from a caption ballot remain separate gaps.
