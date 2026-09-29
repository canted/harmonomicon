# Pass 3: mechanism survey

**Status:** Completed comparison of the first eleven full cards; a research model, not the package specification.


The cards document actual procedures. This file abstracts their rules to find what a programming-language-independent activity package would need to express. Mechanism names and format implications are analysis; the linked cards separate them from source rules. Pass 2 remains a [breadth sample](breadth-survey.md), not a claim of exhaustive coverage.

## Algorithm signatures

An arrow means the next stage of the documented variant, not a proposed software state machine. “Host” includes a human facilitator unless a card identifies software.

| Activity card | Compact algorithm | Important boundary |
|---|---|---|
| [Pass the Parcel](activities/pass-the-parcel.md) | Prepare layers → pass during music → host stops → holder unwraps one → repeat until center reveal | Physical holder and stop are human-observed; fairness is optional |
| [Roll the Orange](activities/roll-the-orange.md) | Read prompt → choose recipient → holder answers → holder chooses next → stop when all have answered | Possession grants speech; next recipient is participant-selected |
| [Call and Response Songs](activities/call-and-response-songs.md) | Leader calls → group responds → repeat phrase pattern → rotate leader if chosen | Performance is ephemeral; coordinated group singing needs live audio timing that an ordinary remote host may not provide |
| [Freeze Scenes](activities/freeze-scenes.md) | Prompt → groups plan in parallel → countdown → all show still scene → discuss or repeat | Parallel work and a common reveal cue; embodied result |
| [Gratitude Spies](activities/gratitude-spies.md) | Private name draw → observe through day → share appreciation in closing circle | Assignment secrecy differs from later public speech; draw constraints unresolved |
| [Cook Along Challenge](activities/cook-along-challenge.md) | Agree recipe/time → get ingredients → **live cook/share** or **separate cook/share by deadline** | One activity has two time modes and physical work outside host observation |
| [Exquisite Corpse, drawing](activities/exquisite-corpse-drawing.md) | Draw section → conceal except guide lines → pass → repeat → reveal whole image | Next actor sees a deliberately limited view of prior work |
| [Fukuwarai](activities/fukuwarai.md) | Prepare face/pieces → blindfold placer → group gives directions → place pieces → reveal | Participants have asymmetric perception of the same physical object |
| [1-2-4-All](activities/1-2-4-all.md) | Prompt → alone → pairs → quartets → full group sharing | Group partition changes at timed barriers; synthesis is human |
| [BeReal daily post](activities/bereal-daily-post.md) | Daily broadcast → post within window or late → unlock friends' feed → recur next day | Scheduled recurrence, late state, view gate, product-specific media |
| [Critical Response Process](activities/critical-response-process.md) | Present work → meaning → maker questions → neutral questions → permissioned opinions | Speech rights vary by phase; maker can decline each opinion |

## Repeated mechanisms and their distinct parameters

| Mechanism | Seen in | Variable that changes its meaning |
|---|---|---|
| **Turn or role handoff** | Parcel, Orange, Call and Response, Exquisite Corpse | Who selects next actor: physical location, current holder, host, or ordered sheet route. A “next participant” primitive alone loses this distinction. |
| **Trigger and barrier** | Parcel, Freeze Scenes, 1-2-4-All, BeReal | Human cue, countdown, fixed duration, or service schedule. Some barriers wait for a physical event; others only wait for time. |
| **Group partition** | Freeze Scenes, 1-2-4-All, Critical Response | Stable small teams, progressively merged teams, or role sets. One person may have a role while also belonging to the full group. |
| **Assignment** | Gratitude Spies, Exquisite Corpse, Freeze Scenes | Random private name draw, ordered section handoff, or group membership. Uniqueness and self-assignment rules cannot be guessed. |
| **Information visibility** | Exquisite Corpse, Gratitude Spies, Fukuwarai, BeReal, Critical Response | Hidden prior work, secret target, sensory asymmetry, post-to-view gate, or permission before speech. These have different owners and reveal conditions. |
| **Repeat and termination** | Parcel, Orange, Call and Response, Freeze Scenes, BeReal | Exhaust layers, cover everyone, finish song, host ends rounds, or recur without a fixed end. Repetition is not one universal loop. |
| **Contribution/artifact** | Freeze Scenes, Cook Along, Exquisite Corpse, BeReal, Critical Response | Embodied scene, cooked food, combined drawing, stored photo, or spoken feedback. Digital storage is optional in some activities and intrinsic to one documented product. |
| **Consent and inclusion** | Roll the Orange, Gratitude Spies, Critical Response, Fukuwarai | Inclusion check, unresolved participation choice, explicit permission for each opinion, or comfort with a blindfold. A generic `required=true` flag would not capture these relationships. |
| **Co-presence and timing quality** | Call and Response, Freeze Scenes, 1-2-4-All | Conversational turns and countdowns can tolerate different delay than coordinated singing. A host's generic “live” flag does not establish that an online music activity will work. |

## State that a host can know

The same rule can be represented as a stage without requiring the host to sense the world. Separate three kinds of fact:

1. **Host-controlled:** A timer expires, a message is sent, a digital contribution is received, or a stored view is unlocked. BeReal's gate and a digital Exquisite Corpse handoff could be enforced by software.
2. **Human-reported:** Music stopped, a parcel holder was selected, a paper section was folded, or a scene was performed. A person may report these to software if the activity needs tracking.
3. **Human-judged or private:** A singer responded, a scene was effective, appreciation was genuine, a question was neutral, or a cook handled food safely. Sources place these in human practice; the first contract experiment should not claim to verify them.

Fukuwarai is a useful warning: the group knows where pieces are, while the placer does not. A digital host might know coordinates in an adapted version, but the documented physical game only requires people to guide one another. A package must distinguish **rule visibility** from **host observability**.

## Exception and choice audit

These are questions to resolve during a particular activity definition or facilitation plan. “Open” means the cited instructions do not supply a rule; it does not authorize inventing a universal default.

| Case | Cards where it matters | Documented rule or gap |
|---|---|---|
| A participant declines a turn, question, solo role, blindfold, or public sharing | Orange, Call and Response, Gratitude Spies, Fukuwarai | Open in the cited instructions. Critical Response explicitly permits the maker to decline hearing an offered opinion, which is narrower. |
| A person arrives late or leaves mid-round | Parcel, Freeze Scenes, 1-2-4-All, Exquisite Corpse | Open. Group partitions and passing routes may need human reassignment. |
| A contribution is missed or unfinished | Exquisite Corpse, Cook Along, Gratitude Spies | Open. Cook Along sets a deadline in its separate branch but gives no late-result rule. |
| A timed response is late | BeReal | Late posting is allowed and visibly marked; posting unlocks the friends feed. |
| The host wants equal turns | Parcel, Orange, Call and Response | Parcel sources document optional turn balancing; Orange's structured version ends when all answer; Call and Response does not require everyone to lead. |
| An assignment conflicts or duplicates | Gratitude Spies, 1-2-4-All | Gratitude Spies gives no self-draw or duplicate rule; 1-2-4-All permits a trio when pairing is awkward but leaves many partition choices to the host. |
| Someone needs different sensory, movement, language, or technology access | All cards | Card-specific demands are recorded; [RNIB](https://www.rnib.org.uk/documents/465/APDF-RE190403_Parties_and_Playdates-v07.pdf) and [Playworks](https://www.playworks.org/resource/tips-for-making-play-access-easier/) support clear instructions and individualized adaptations. No single transformation makes every game accessible. |

## Boundary findings for Pass 4

- **Package, session, occurrence, and host are different objects.** Pass 2's [Morning Meeting and CASEL examples](breadth-survey.md#rituals-and-group-care) are session frames. BeReal recurs as multiple daily occurrences. A host may be a person, software, or both.
- **The common core should describe rules and participant experience without demanding executable code.** The cards expose a small set of recurring constructs: roles, groups, instructions, triggers, phases, assignments, visibility, completion, and optional branches. They do not yet show that these constructs form a sufficient language. This remains a hypothesis for contract experiments.
- **Capabilities should be declared per activity.** The physical games need almost no software. BeReal-like digital behavior requires scheduling, identity, media storage, and access control. Cook Along needs messaging and perhaps media exchange only if software coordinates it.
- **Remote feasibility is not implied by portable rules.** Carnegie Hall's Call and Response activity is documented in person. [Networked music research](https://onlinelibrary.wiley.com/doi/abs/10.1002/cpe.4730) treats ensemble delay in tens of milliseconds, and [JackTrip's setup guidance](https://support.jacktrip.com/how-to-optimize-latency-when-using-jacktrip) shows how network, distance, and equipment affect it. A host can interpret the activity instructions but should not claim to support distributed group singing unless it can meet the needed audio conditions; sequential or separately recorded singing changes the activity.
- **Human authority must remain explicit.** Parcel possession, scene performance, neutral questions, and consent cannot be derived from an event log unless a participant or facilitator reports them. A package can specify who is allowed to report a fact and what the host then does.
- **Visibility rules need an explicit subject and transition.** “Private” is insufficient: the Gratitude Spies target is secret until a circle, Exquisite Corpse exposes only guide marks to the next contributor, BeReal hides others' posts until one's own post, and Critical Response gates a responder's opinion on the maker's permission.
- **Unsupported or unspecified behavior needs a clear outcome.** In Pass 4, examples should say when a host lacks a capability and when an activity's source leaves a choice to the organizer. Neither case should silently acquire a default rule.

## Next contract experiments

The [portable activity package direction](portable-activity-packages.md) can now be tested against a small set of unlike traces: physical stop-and-pass (Parcel), visibility-preserving serial handoff (Exquisite Corpse), changing partitions (1-2-4-All), recurring late submission and view gate (BeReal), and per-opinion permission (Critical Response). A Cook Along trace should test the live/async branch. For each, write the same human-readable rules, a candidate portable definition, and expected state after a few events, then check whether two independently written interpreters can agree. That is a Pass 4 test plan, not a schema chosen by this survey.

## Later digital extension

The [digital activity stress cases](digital-activity-stress-cases.md) add three source-backed examples after the first eleven-card comparison: Drawception's skip and requeue, Moodle Workshop's phase/deadline/allocation interactions, and Board Game Arena's automatic Gaia Project faction auction. They also spell out a **proposed**, unimplemented two-recipient relay to test concurrent acceptance and stalled-chain recovery. The original Pass 3 table remains the record of the first card set; the extension does not retroactively turn the relay design into a sourced activity rule.

The later [game-jam and shared-practice survey](creative-jams-and-shared-practice.md) adds nested timelines, team/project identity, interim artifacts, optional social interaction during work, and the distinction between shared content and shared completion status. It compares these against the existing recurrence, assignment, and visibility mechanisms without changing the original eleven-card signatures.
