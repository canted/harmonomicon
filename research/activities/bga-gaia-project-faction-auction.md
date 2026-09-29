# Board Game Arena Gaia Project faction auction

## Identity and context

- **Description:** During an optional digital setup auction, players submit maximum bids for factions and the game executes a round-robin bidding process automatically.
- **Group and mode:** Players in a Board Game Arena Gaia Project game using the documented faction-drafting auction. The auction is one setup component, not the whole board game.
- **Facilitator:** Board Game Arena collects preferences, runs the auction, assigns factions, and adjusts starting victory points.
- **Experience:** Players express relative preferences without manually conducting every bid.

## Preparation

The game has a set of drafted factions and a player turn order. Each player chooses the maximum victory points they are willing to bid for each faction.

## Procedure

1. Collect all players' maximum bids for the drafted factions.
2. Once everyone has submitted, run an automatic round-robin auction in turn order. On each bidding opportunity, the software chooses the faction with the greatest gap between that player's maximum and its current bid, then places the next permissible bid on it.
3. Repeat until each player leads the bidding on one faction. Assign those factions and charge the winning bids.
4. Give all players enough victory points that the highest-paying player begins the main game with ten victory points. The source includes a three-player bid log demonstrating this calculation.

## Rules and choices

- **Participant input:** Maximum acceptable bid per faction, submitted before automatic resolution.
- **Barrier:** The auction begins after every player has supplied maxima.
- **Automatic work:** The service makes many interleaved bids, switches a player's target when another faction has a better gap, and calculates results without asking players to approve each step.
- **Visibility:** The help page includes a game-log example of the generated bids. The consulted source does not fully specify which maxima are visible to other players during setup.
- **Completion:** Every player leads on one faction, then the game proceeds with those assignments and adjusted victory points.

## Variants

The source describes this as an auction for drafting factions. It does not claim every Gaia Project table uses it. Other faction-selection methods are outside this card.

## Exceptions and open questions

The source illustrates several ties and switches but does not give a complete formal tie-breaker, validation policy for malformed maxima, timeout rule for a player who never submits, or all auction invariants. A faithful portable implementation would need these from the actual game module or a more complete specification. No generic activity host should infer them from the example log.

## Access and participation

Players must enter preferences through the game interface and understand that victory points may be spent before play. The source does not document an alternate input mode or an accessibility rule for this setup choice.

## Mechanisms and possible software role

**Mechanisms:** Parallel preference collection, all-input barrier, deterministic automated subroutine, derived assignments, resource adjustment, and explanatory log. This shows a digital medium's ability to execute repeated, intricate rule steps after a small amount of human input. The auction algorithm is game-specific; this card does not establish that a general activity package should encode arbitrary game logic.

## Sources and evidence

| Source | What it supports |
|---|---|
| [Board Game Arena Gaia Project help](https://en.doc.boardgamearena.com/Gamehelpgaiaproject) | Faction auction setup, automatic bidding and VP normalization, example log |
| [Board Game Arena Studio automatic-action guidance](https://en.doc.boardgamearena.com/images/7/76/5-guidelines.pdf) | General product guidance to make automatic actions understandable through logs; not an additional Gaia Project rule |

The auction procedure is summarized from game help. The mechanism labels and portability implications are analysis.
