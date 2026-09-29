# Game jams, group journaling, and parallel creative practice

**Status:** Source-backed research extension; no new protocol rules adopted.

## Research question and evidence

What interactions surround the familiar `prompt → deadline → submission` pattern, and which of them are rules that a portable software host might need to mediate? This sample uses organizer documentation, product help, a community's own instructions, and first-person jam/community posts. Published rules establish what an organizer **offered**; they do not prove that participants used every channel or that a particular intervention improved outcomes.

## Game-jam shapes found

| Documented example | Event structure and requirements | Interactions during making |
|---|---|---|
| [Global Game Jam](activities/global-game-jam.md) | Shared theme; local kickoff and team formation; team game page and source upload by the deadline; optional diversifiers; GGJ itself is noncompetitive. | Sites may arrange networking, mentors, and a closing showcase. Local schedules vary. |
| [itch.io ranked-jam workflow](activities/itch-ranked-game-jam.md) | Host configures submission and rating periods, criteria, voter eligibility, and result release. Entry uses an itch.io game project. | Optional jam board, submission comments, progress posts, and later peer/judge feedback. A rating queue can spread reviews. |
| [Relay Jam 2026](activities/relay-jam-2026.md) | Published two-stage team rule: A builds foundation, hands editable source to B at midpoint; no simultaneous work; B finishes. | Partner search and explicit handoff communication. This page documents a rule design, not an observed successful run. |
| [GLC Summer Jam 2026](https://itch.io/jam/gdc-2026-summer-kinda-game-jam) | Published schedule includes early team formation/discussion, two demo showcases, then a polish phase. | Repeated show-and-play checkpoints give participants a way to compare progress before the final export. This is one local event schedule, not a game-jam default. |
| [Work in Progress Jam](https://itch.io/jam/work-in-progress-jam) | The description invites existing or new work, prototypes, and concept art for feedback; an informal rank is present. Its entry instructions also ask for a playable build, so eligibility is internally unclear. | Description asks for challenges and desired feedback; others inspect and respond before a finished game exists. |

The interactions between kickoff and final upload are observable in participant and organizer sources, even when they happen outside the official jam submission flow. [A Strawberry Jam forum](https://itch.io/jam/strawberry-jam-10/community) includes development logs and threads for screenshots and concept art. A [weekly jam organizer](https://itch.io/jam/4gameaweek/topic/6420148/discord-server) explicitly directs people to Discord for progress updates, rough builds, feedback, tools, and encouragement. A [participant's progress thread](https://itch.io/jam/strawberry-jam-10/topic/5806645/plans-and-progress) describes choosing a forum because Discord felt harder to post into. These sources support **multiple audience/channel choices and a continuing conversation**; they do not imply that all jam teams post progress or that the activity needs one specific social-feed design.

### Compact game-jam algorithm family

1. Organizer sets the theme/constraints, participation rules, work period, submission requirements, and optional review process.
2. People register, find collaborators if needed, and form project/team records.
3. Teams work on games. During this interval, they may share sketches, screenshots, builds, questions, devlogs, and feedback with teammates, other teams, mentors, or a public audience. Particular jams may schedule demos or an artifact handoff.
4. A team submits a final project by a deadline, or uses an organizer-defined late exception. A final submission is different from a progress post.
5. Some jams end with a showcase; others start a rating/review period and later reveal results. A winner is optional and absent from GGJ's global framing.

The optional steps are **variants**, not a single universal procedure. A simple deadline-only jam remains valid. A fully mediated app could coordinate more of steps 2–5, but this research does not require those interactions to move into one app.

## Journaling and parallel-practice shapes found

| Documented example | Recurrence and output | Group relationship and visibility |
|---|---|---|
| [Waffle](activities/waffle-shared-journal.md) | Ongoing entries; a daily prompt is optional. | A chosen group reads and comments in a shared journal. No source-backed required one-entry-per-day rule. |
| [Day One Shared Journals](activities/day-one-shared-journal.md) | Ongoing shared entries; Day One's daily prompts are a separate feature. | Invitation/approval, member comments/reactions, and a clear personal-to-shared privacy boundary. |
| [750 Words monthly challenge](activities/750-words-month-challenge.md) | At least 750 private words per local day for a month; no backfill. | Others may see success or missed-day status, not the text. The platform applies month-end consequences. |
| [Jamuary](activities/jamuary.md) | Record and share a music jam each January day; prompts may inspire a day. | Daily forum threads collect links for listening/commenting; people may publish recordings elsewhere first. Not restricted to synthesizers by the community description. |
| [The 100 Day Project](activities/the-100-day-project.md) | A self-chosen action repeated for 100 days; prompts and public sharing are optional. | People make separate work alongside a cohort and may share publicly, privately, or not at all. |
| [The January Challenge 2026](activities/the-january-challenge.md) | A different quick creative prompt each day; organizers can preview the 31-day set. | Groups may make together live, post to a channel, or share just a reflection. The organizer's 2026 edition was the last announced by that organization. |
| [Focusmate](activities/focusmate-coworking.md) | Booked live work interval with intention at start and report at end. | Two people do separate work in co-presence; no shared creative artifact or daily streak is required. |

These examples separate at least four notions often called “sharing”: sharing **the work**, sharing **a progress glimpse**, sharing **a reflection**, and sharing **only a completion signal**. [750 Words](https://original.750words.com/one_month) demonstrates the last while keeping writing private; [Day One's current shared-journal guide](https://dayoneapp.com/guides/shared-journals/shared-journals/) makes the content boundary explicit. A completion mark should not automatically expose the underlying work.

## Mechanisms added to the research map

| Mechanism | Evidence | Difference from an existing surveyed pattern |
|---|---|---|
| **Nested timelines** | [GGJ](activities/global-game-jam.md), [itch ranked jams](activities/itch-ranked-game-jam.md), [GLC](https://itch.io/jam/gdc-2026-summer-kinda-game-jam) | A jam has a work window and may have independent community, demo, submission, review, and reveal windows. A single linear stage list loses the ongoing interactions during making. |
| **Persistent team/project identity** | [GGJ upload](https://globalgamejam.org/upload-your-game), [Relay Jam](activities/relay-jam-2026.md) | Contributions attach to a team and evolving project, not just an individual turn or final artifact. |
| **Interim artifact versus final entry** | [Work in Progress Jam](https://itch.io/jam/work-in-progress-jam), [progress forum](https://itch.io/jam/strawberry-jam-10/community) | Screenshots, rough builds, questions, and feedback have different deadlines, audiences, and validity rules than final submissions. |
| **Cross-group conversation** | [GGJ site schedule](https://globalgamejam.org/group/75/announcements), [weekly jam Discord](https://itch.io/jam/4gameaweek/topic/6420148/discord-server) | Teams have internal work, while participants also exchange work and support across teams. The app may mediate only some of that. |
| **Soft versus hard cadence** | [Jamuary](activities/jamuary.md), [100 Day Project](activities/the-100-day-project.md), [750 Words](activities/750-words-month-challenge.md) | All repeat daily, but only the documented 750 Words challenge has a no-backfill day boundary and named consequence. Optional sharing must remain optional. |
| **Proof/status separate from content** | [750 Words](activities/750-words-month-challenge.md), [HabitShare](https://habitshareapp.com/) | A person can expose a habit check-in or completion state while the journal or creative work stays private. |
| **Review allocation and aggregation** | [itch.io jam documentation](https://itch.io/docs/creators/game-jams) | The rating queue, voter eligibility, criteria, and release of results are actual configurable policies, not merely `pick a winner`. |
| **Parallel work with reciprocal accountability** | [Focusmate](activities/focusmate-coworking.md), [100 Day Project](activities/the-100-day-project.md) | People are engaged in the same organized interval or campaign without making one combined artifact. |

## Effect on the portable-format research

The current [mechanism survey](mechanism-survey.md) already has prompts, recurrence, assignments, privacy, deadlines, and reveal. [Moodle Workshop](activities/moodle-workshop.md) already demonstrates staged submissions and peer review. These new cases **do not require declaring an entirely new protocol direction**. They expose combinations and distinctions that the current [composition experiment](../experiments/composition/findings.md) has not tested:

1. A long-running activity can have an **ongoing optional interaction layer** while a hard submission window and later review window advance. The current composed stage plans model one active stage at a time.
2. A project may belong to a **team** whose membership changes or whose members have different phase rights. Current traces mostly address named individual actors.
3. A **check-in, work-in-progress post, final artifact, and review** are different event types even when all contain media. They need different eligibility, audience, and completion semantics.
4. Daily cadence can be a **hard measured threshold**, a **soft invitation**, or a **common prompt**. A host should not invent a streak penalty for Jamuary or The 100 Day Project.
5. Content and status have **separate visibility**. Private writing with public completion differs from group-visible journal entries and from a public Jamuary recording.

The narrow contract probes identified by this survey are (a) a game-jam trace with team formation, optional mid-jam posts and comments, a final submission deadline, and a later review window; and (b) a daily-practice trace that distinguishes private work, status-only check-in, optional shared entry, and missed day. The tests should use the documented variants as constraints and mark any new all-in-one app choices as proposed behavior. This survey itself does not implement those probes.

An interim [revisit of the existing experiments](../experiments/creative-practice-revisit/README.md) runs diagnostic traces for the current collection and stage-plan contracts. It identifies specific view and history limits before either fuller probe is implemented.

A later [ongoing-activity experiment](../experiments/ongoing-activities/README.md) now implements both proposed probes in JavaScript and Python. Its test rules are still experimental combinations, not rules attributed to any one researched activity.

## Evidence limits

- Organizer pages define rules and available channels; forum posts give concrete examples of use. Neither supplies a representative count of how many teams communicate, seek feedback, or finish.
- Waffle and Day One product pages document features, not a mandatory shared-journaling ritual. Day One's current guide differs from its older launch post on account requirements, so this survey uses the current guide for procedure.
- The 100 Day Project and Jamuary are distributed practices. A single app's metrics or rule set would not define every participant's behavior.
- Relay Jam's zero-entry page supports analysis of a proposed handoff algorithm, not an observed completion outcome.
- The Work in Progress Jam page both welcomes non-playable materials and asks entrants to submit a playable build. The exact allowed submission type would need organizer clarification before encoding its entry rule.
