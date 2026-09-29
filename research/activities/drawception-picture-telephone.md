# Drawception picture telephone

## Identity and context

- **Description:** An online chain alternates drawings of captions with captions describing drawings, then reveals the finished sequence.
- **Group and mode:** Public games involve successive participants, potentially at different times. The documented standard game ends after 12 people have participated.
- **Facilitator:** Drawception assigns a queued panel, provides drawing and caption interfaces, enforces a drawing timer, and displays the completed chain.
- **Experience:** Players see how a phrase changes through repeated interpretation.

## Preparation

Participants need an account, an internet connection, and a way to enter text or draw with the site's tools. The site starts chains from prompts and assigns a player a drawing to describe or a caption to draw.

## Procedure

1. A player draws an opening phrase.
2. Drawception assigns that drawing to another player, who describes it in a caption.
3. It assigns the caption to another player, who draws it. Drawing panels have a ten-minute limit.
4. Drawing and caption panels alternate until 12 people have participated in the documented standard game.
5. The finished chain becomes viewable as a sequence.

## Rules and choices

- **Assignment:** The player receives a queued drawing or caption through Play. The public description says the next contributor is random; the exact queue-selection algorithm is not documented.
- **Contribution:** Describe the visible drawing or draw the visible caption. The rules prohibit intentional derailment and text-only drawings; a player may skip a prompt they do not understand.
- **Timing:** The public home page gives ten minutes for a drawing. The sources consulted do not state a caption timer.
- **Visibility:** The next player works from the assigned drawing or caption; the completed chain is revealed at the end. The consulted pages do not fully specify every intermediate visibility rule.
- **Completion:** The standard example ends after 12 contributions. The site may have other game lengths; this card does not generalize to them.

## Variants

The rules page describes behavior for the public game. Other site modes may differ and are outside this card.

## Exceptions and open questions

- **Documented recovery:** A player may exit or skip without committing a panel. Drawception says that panel returns to the queue for another player. A description repeatedly skipped by players may be removed as a “dustcatcher” so it does not clog the queue.
- **Unspecified:** The public pages do not describe reservation duration, simultaneous offers, collision resolution, queue fairness, a guarantee that every chain finishes, or the exact handling of a player who disconnects without pressing exit or skip. A dev log records several timer and auto-exit changes, so historical behavior should not be treated as current rules.

## Access and participation

The rules currently require English and human input. Drawing requires a usable pointing or touch interface; captions require written language. The consulted pages do not establish equivalent alternate input modes. Skipping is an explicit participation choice, but it can also delay a difficult chain.

## Mechanisms and possible software role

**Mechanisms:** Alternating media, assignment from a shared queue, concealed prior context, bounded drawing time, voluntary skip, release and reassignment, repeated-skip removal, final reveal. Software operates the documented version. A portable host would need to preserve the panel's state when an assignment is released and distinguish a skipped offer from a committed contribution.

## Sources and evidence

| Source | What it supports |
|---|---|
| [Drawception home page](https://drawception.com/) | Alternating sequence, random next player, 12-person standard game, ten-minute drawing, reveal |
| [Drawception FAQ](https://drawception.com/faq/) | Queue assignment, exit/skip and release, variable completion time, dustcatchers |
| [Drawception rules](https://drawception.com/rules/) | Contribution restrictions and permission to skip |
| [Drawception dev log](https://drawception.com/devlog/) | Historical timer and auto-exit changes; not used as the current rule |

This is a current product-behavior card. The mechanism labels and portability implications are analysis.
