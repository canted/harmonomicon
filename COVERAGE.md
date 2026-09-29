# Activity coverage toward 1.0

This audit compares the [25 source-backed and constructed activity cards](research/activities/) with the [0.5 candidate](format/0.5/README.md). A match means a package can express a **digitally mediated rule slice** of the card, not that software reproduces the whole social, artistic, physical, or human-facilitated practice. The cards remain the record of the real procedure. “Partial” names a rule still missing for a closer digital version; it is not an instruction to invent that rule for the original activity.

| Activity card | 0.5 digital slice | Missing for a closer digital version |
|---|---|---|
| [1-2-4-All](research/activities/1-2-4-all.md) | Prompt and timed collection. | Timed phase sequence, changing pair/quartet partitions, staged sharing. |
| [750 Words month challenge](research/activities/750-words-month-challenge.md) | Private repeated entries and group-visible completion status. | Local-calendar days, word threshold, monthly aggregate and source-specific consequences. |
| [BeReal daily post](research/activities/bereal-daily-post.md) | Repeated prompt and status. | Image storage, late-post branch, post-to-view gate, local-day timing. |
| [Gaia Project faction auction](research/activities/bga-gaia-project-faction-auction.md) | Collection of preferences could be timed. | Its exact game-specific auction and scoring algorithm; this would be a separately versioned policy, not a universal default. |
| [Call and Response Songs](research/activities/call-and-response-songs.md) | Directions and sequential cues. | Low-latency live audio synchrony and observation of singing; ordinary internet hosts cannot claim these from the package alone. |
| [Cook Along Challenge](research/activities/cook-along-challenge.md) | Prompt, deadline, and separate-result submission. | Live coordination and media sharing; food preparation remains outside software observation. |
| [Cover and Response](research/activities/cover-and-response.md) | `offered_response@1` models text sources, two offers, linked response, reveal. | Image or audio source storage and any later vote. |
| [Critical Response Process](research/activities/critical-response-process.md) | Directions and a work submission. | Ordered speaking rights and each maker-controlled permission decision. Human judgment of neutrality remains outside software. |
| [Day One shared journal](research/activities/day-one-shared-journal.md) | Group-visible repeated entries only if a fixed schedule is imposed. | Ongoing entry/comment space, optional prompt, membership and per-entry sharing choice. |
| [Drawception picture telephone](research/activities/drawception-picture-telephone.md) | Concealed sequential handoff. | Alternating image/text media, queue lease, skip/requeue, bounded turns. |
| [Exquisite Corpse drawing](research/activities/exquisite-corpse-drawing.md) | Text handoff and final reveal. | Drawing media and limited guide-mark view. Paper folding is a physical variant beyond app control. |
| [Focusmate paired coworking](research/activities/focusmate-coworking.md) | A timed prompt and check-in can be adapted. | Two-person live session with intention and closing report; presence is a host/media capability. |
| [Freeze Scenes](research/activities/freeze-scenes.md) | Prompt and countdown cue. | Parallel group planning and common reveal cue; the physical scene remains human-observed. |
| [Fukuwarai](research/activities/fukuwarai.md) | Directions only. | Physical piece placement and asymmetric sight, or a separately designed digital spatial game. |
| [Global Game Jam](research/activities/global-game-jam.md) | `project_cycle@1` covers fixed teams, progress, final submission, and later review in a proposed digital variant. | Team formation, file/media uploads, optional showcases, and local-site practices. GGJ itself is not globally competitive. |
| [Gratitude Spies](research/activities/gratitude-spies.md) | Prompt and timed closing collection. | Private target assignment and later disclosure; real-world observation remains human. |
| [itch.io ranked game jam](research/activities/itch-ranked-game-jam.md) | Team progress, final entry, text review window. | Rating eligibility, allocation, criteria, aggregation, release, and media/projects. |
| [Jamuary](research/activities/jamuary.md) | Fixed repeated windows with immediate sharing. | Local-calendar prompts, audio/link entries, comments, and optional participation without imposed missed-day penalty. |
| [Moodle Workshop](research/activities/moodle-workshop.md) | Staged final submission and peer text review in a narrow variant. | Configurable phase authority, reviewer allocation, grading policy, manual intervention, late work. |
| [Pass the Parcel](research/activities/pass-the-parcel.md) | Directions and a possible digital-possession adaptation. | The physical holder, layers, and music stop are not app-observed. A digital game needs its own exact rules. |
| [Relay Jam](research/activities/relay-jam-2026.md) | Fixed teams and a final showcase can be adapted. | Exclusive A-to-B work phases, editable artifact handoff, missed-turn recovery. |
| [Roll the Orange](research/activities/roll-the-orange.md) | Sequential prompts could be adapted. | Participant-chosen next recipient and turn coverage; the physical orange and speech remain human. |
| [The 100 Day Project](research/activities/the-100-day-project.md) | Repeated private or shared entries with retained history. | Soft invitation rather than required daily completion, optional posting, changing self-selected project context. |
| [The January Challenge](research/activities/the-january-challenge.md) | Fixed repeated collection. | A different prompt for each day, optional reflection and sharing, local-calendar timing. |
| [Waffle shared journal](research/activities/waffle-shared-journal.md) | Group-visible entries only under a fixed schedule. | Ongoing unscheduled entries, comments, optional prompt, persistent shared-space membership. |

## Coverage decisions

The current five contracts establish timed submission, hidden handoff, fixed recurrence, source-to-response assignment, and fixed-team project progress/review. These are **five behavior families**, not a claim that five cards are fully reproduced. The table shows why a simple count of runnable packages would overstate coverage: the media, schedule, authority, and recovery rules often change the activity.

For 1.0, the remaining **widely reused digital families** to test are:

1. **Ongoing shared space and soft cadence:** unscheduled journal or progress entries, comments, optional prompts and sharing, and day-indexed prompts when a cadence is chosen. This is the next candidate because it affects Waffle, Day One, Jamuary, The 100 Day Project, and The January Challenge.
2. **Facilitated phase and audience changes:** timed or facilitator-reported phase changes, changing groups, role-specific rights, and per-contribution permission. This affects 1-2-4-All, Critical Response, Focusmate adaptations, Freeze Scenes, and parts of Moodle Workshop.
3. **Turn recovery:** a queue, skip or timeout, reassignment, and one accepted contribution. This affects Drawception-like digital chains and stalled handoffs.
4. **Portable media and selection:** a host-controlled image reference with real storage and access checks, plus exact voting/review aggregation rules when an activity selects a result. This affects photo prompts, caption games, and ranked jams.

A behavior family reaches the 1.0 coverage set only after a normative contract, schema, examples, conformance cases, and independent host evidence agree. The 1.0 claim will identify a supported digital slice for each mapped card and keep unsupported source-specific rules explicit. Game-specific auctions, millisecond-synchronous singing, and unobservable physical actions remain bounded by separate capabilities or human reports; they are not hidden behind a generic “activity supported” label. Package exchange, version compatibility, and conformance claims must also meet the [roadmap publication gate](ROADMAP.md#toward-10).
