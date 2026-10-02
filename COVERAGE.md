# Activity coverage for format 0.12

This audit compares the [25 source-backed and constructed activity cards](research/activities/) with the [candidate 0.12 format](format/0.12/README.md). A match means a package can express a **digitally mediated rule slice** of the card, not that software reproduces the whole social, artistic, physical, or human-facilitated practice. The cards remain the record of the real procedure. “Partial” names a rule still missing for a closer digital version; it is not an instruction to invent that rule for the original activity.

| Activity card | 0.12 digital slice | 0.12 audit | Missing for a closer digital version |
|---|---|---|---|
| [1-2-4-All](research/activities/1-2-4-all.md) | Timed prompts, solo/pair/quartet/full-group partitions, and after-round text sharing. | Modeled | Human synthesis, facilitator adjustment, and spoken discussion remain outside app observation. |
| [750 Words month challenge](research/activities/750-words-month-challenge.md) | Private recurring entries and group-visible completion status. | Partial | Local-calendar days, word threshold, monthly aggregate and source-specific consequences. |
| [BeReal daily post](research/activities/bereal-daily-post.md) | Repeated image prompt and status can use stored PNG references. | Partial | Late-post branch, post-to-view gate, local-day timing, and other image formats. |
| [Gaia Project faction auction](research/activities/bga-gaia-project-faction-auction.md) | Collection of preferences could be timed. | Reference | Its exact game-specific auction and scoring algorithm; this would be a separately versioned policy, not a universal default. |
| [Call and Response Songs](research/activities/call-and-response-songs.md) | Directions and sequential cues. | Reference | Low-latency live audio synchrony and observation of singing; ordinary internet app hosts cannot claim these from the package alone. |
| [Cook Along Challenge](research/activities/cook-along-challenge.md) | Prompt, deadline, and PNG result submission. | Modeled | Live coordination and other media; food preparation remains outside software observation. |
| [Cover and Response](research/activities/cover-and-response.md) | `offered_response_vote@1` models PNG or text sources, two offers, linked text responses, a vote, and a result. | Modeled | Audio storage and other selection policies. |
| [Critical Response Process](research/activities/critical-response-process.md) | Facilitator-controlled text phases, linked questions, and a maker decision for each opinion request. | Modeled | Human judgment of neutrality, tone, and live speech remains outside software. |
| [Day One shared journal](research/activities/day-one-shared-journal.md) | An ongoing text space with comments and per-entry private or group sharing. | Modeled | Media in this contract, reactions, approval or changing membership, and the source product’s full sharing controls. |
| [Drawception picture telephone](research/activities/drawception-picture-telephone.md) | Concealed sequential handoff or bounded competing text offers with deadline fallback. | Partial | Alternating image/text steps in one chain and the source-specific queue lease, skip/requeue rules. |
| [Exquisite Corpse drawing](research/activities/exquisite-corpse-drawing.md) | PNG handoff and final reveal are possible. | Partial | Drawing tools, alternating media, and limited guide-mark view. Paper folding is a physical variant beyond app control. |
| [Focusmate paired coworking](research/activities/focusmate-coworking.md) | Two-person timed rounds can prompt an intention and closing report. | Partial | Live presence and video remain app and media capabilities, not proven by the package. |
| [Freeze Scenes](research/activities/freeze-scenes.md) | Timed group rounds can guide parallel planning and a shared reveal cue. | Reference | The physical scene and performance remain human-observed. |
| [Fukuwarai](research/activities/fukuwarai.md) | Directions only. | Reference | Physical piece placement and asymmetric sight, or a separately designed digital spatial game. |
| [Global Game Jam](research/activities/global-game-jam.md) | `project_cycle@1` covers fixed teams, progress, final submission, and later review in a proposed digital variant. | Modeled | Team formation, media in the project-cycle contract, optional showcases, and local-site practices. GGJ itself is not globally competitive. |
| [Gratitude Spies](research/activities/gratitude-spies.md) | Prompt and timed closing collection. | Partial | Private target assignment and later disclosure; real-world observation remains human. |
| [itch.io ranked game jam](research/activities/itch-ranked-game-jam.md) | Team progress, final entry, and text review window; a separate simple caption vote demonstrates one selection policy. | Partial | The source-specific rating eligibility, allocation, criteria, aggregation, release, and project media remain outside this contract. |
| [Jamuary](research/activities/jamuary.md) | Optional prompt series with text entries, comments, and no imposed missed-day signal. | Partial | Local-calendar timing and audio/link entries in the ongoing-space contract. |
| [Moodle Workshop](research/activities/moodle-workshop.md) | Staged final submission and peer text review in a narrow variant; a separate dialogue contract demonstrates manual phase authority. | Partial | Reviewer allocation, grading policy, reversible phases, manual intervention, and late work. |
| [Pass the Parcel](research/activities/pass-the-parcel.md) | Directions and a possible digital-possession adaptation. | Reference | The physical holder, layers, and music stop are not app-observed. A digital game needs its own exact rules. |
| [Relay Jam](research/activities/relay-jam-2026.md) | Fixed teams and a final showcase can be adapted. | Partial | Exclusive A-to-B work phases, editable artifact handoff, missed-turn recovery. |
| [Roll the Orange](research/activities/roll-the-orange.md) | Sequential prompts or preassigned competing offers could be adapted. | Partial | Participant-chosen next recipient and turn coverage; the physical orange and speech remain human. |
| [The 100 Day Project](research/activities/the-100-day-project.md) | An ongoing text space with optional private or shared entries; a soft prompt series is possible. | Modeled | Local-calendar timing and changing self-selected project context. |
| [The January Challenge](research/activities/the-january-challenge.md) | Different prompts for successive windows with optional private or shared PNG submissions. | Modeled | Local-calendar timing, live group co-creation, and other media. |
| [Waffle shared journal](research/activities/waffle-shared-journal.md) | An unscheduled shared text notebook with comments and per-entry privacy. | Modeled | Media entries, read state, and mutable shared-space membership. |

## 0.12 selection audit

**Modeled** means one defined package can run a recognizable digital version of the activity’s app-mediated steps. **Partial** means the format can run a substantive digital slice but lacks a key rule or medium of the documented activity. **Reference** means the current format would add little beyond directions, a timer, or a report of a physical event; claiming the activity itself would be misleading. These are analytical classifications of the [activity cards](research/activities/), not claims made by the source creators.

Of 25 cards, **9 are modeled, 11 are partial, and 5 are reference-only** under those definitions. Thus 20 have a tested digital slice, but the 11 partial cases are not source-equivalent packages. The modeled and partial cases exercise recurring digital mechanisms across timed and repeated prompts, concealed handoffs, teams and progress, shared spaces, changing groups, saved offers, media access, fallback, voting, and permissioned feedback. The reference-only cases require physical possession or performance, low-latency singing, or a game-specific auction that this specification does not provide. The number of cards is a check against the surveyed sample, not a forecast of coverage across all possible activities.

A separate [simple digital pattern audit](experiments/format-0.12-coverage-challenge/README.md) uses a stricter exact-rule test on eight breadth-survey procedures. It records one exact software-coordination slice and seven digital-target failures. A [follow-up comparison](experiments/hidden-answer-composition/README.md) tests one failure as both a game-specific draft and a reusable-rule draft. Neither is a 0.12 package; package-level composition remains unsupported.

The selected 0.12 set is the ten defined behavior families and their exact capabilities. The open queue in Drawception, post-to-view gate in BeReal, local-calendar schedules, private target draw, reviewer allocation, and multi-criterion grading remain identifiable digital extensions. None is inferred from a generic field or silently treated as supported. That boundary follows the [mechanism survey](research/mechanism-survey.md), [digital stress cases](research/digital-activity-stress-cases.md), and the [candidate 0.12 validation record](ROADMAP.md#candidate-012-validation). It defines the tested candidate's limits and identifies mechanisms for the [development direction](ROADMAP.md#development-direction).

## Remaining digital extensions

The 0.12 contracts have exact rules for timed collection, hidden handoff, fixed recurrence, source-to-response assignment, fixed-team progress and review, an ongoing text space, timed changing groups, bounded fallback, one voting branch, and permissioned dialogue. These are behavior families, not a claim that a source practice is completely reproduced.

The partial cards identify separate work: Drawception-style open queues and requeue, BeReal-style post-to-view gates, local-calendar schedules, private target assignment, alternating image/text handoffs, project media, reviewer allocation, and multi-criterion grading. The reference-only cards include physical possession or performance, low-latency singing, and a game-specific auction. The [development direction](ROADMAP.md#development-direction) is to express suitable digital variants through composed operations where possible, with new exact primitives where needed and independent app host evidence. An app host must not infer these rules from a prompt or from support for a related 0.12 contract.

## Composed candidate 0.13 evidence

The 25-card classifications above remain the audit of candidate 0.12. Candidate 0.13 is a separate runbook subset, not an automatic superset. Its [examples and conformance cases](format/0.13/conformance/README.md) exercise collection/reveal, a private hidden answer, typed guesses, a general option poll, manually advanced prompts, participant turns, and cumulative text with timeouts. A newly authored check-in-then-story package also runs in both [local app hosts](validation/0.13/README.md) without interpreter changes.

| Earlier strict challenge target | Candidate 0.13 evidence or remaining gap |
|---|---|
| Fixed 1-2-4-All rooms and timing | No within-group audiences or partition validation yet; the 0.12 slice does not transfer automatically. |
| Minimal Choice poll | Three exact options, one choice per participant, close/reveal, and per-option counts are exercised. Changes, capacities, and richer Moodle settings are outside the selected minimal target. |
| Selected Two Truths digital variant | All roster turns, public statements/private answer, typed one-per-person guesses, speaker close, and answer/guess reveal are exercised through composed steps. |
| Gratefulness Grab Bag | No independent two-item pool, concealed selection, or reader assignment yet. |
| Selected cumulative-story text variant | Ordered turns, append-only whole-story entries, one-minute deadlines, omission of missed turns, and rejection of stale events are exercised. |
| See, Think, Wonder | A selected one-response-per-person-per-stage variant has group-visible responses and organizer-controlled transitions. Broader conversation or multiple entries is not claimed. |
| Impromptu Networking | No transition-time participant regrouping or pair-specific audience yet. |
| Proposed 25/10 digital variant | No card routing, per-round numeric score collection, score aggregation, or ranked reveal yet. |

This establishes concrete progress on four earlier failures, including a bounded prompted-routine variant. It is not a new claim that all eight targets or the full activity cards are covered. The [development priorities](ROADMAP.md#path-from-013-onward) target pools and assignments first, then scoring/routed rounds and longer/media activities.

## Composed candidate 0.14 evidence

Candidate 0.14 adds [ten runbook examples](format/0.14/README.md#start-with-a-package) and [twelve exact traces](format/0.14/conformance/README.md), run in two independent [durable app hosts](validation/0.14/README.md). The 0.12 card classifications above remain historical; they are not silently inherited.

- The selected Gratefulness Grab Bag digital target now has two independent slips per person, non-author reader claims, private reader access, and item-by-item anonymous reveal. Accepted order and app acknowledgment are explicit digital choices; there is no claimed physical draw or proof of reading aloud.
- The selected Impromptu Networking coordination uses three organizer-supplied group maps and timed private group notes. Regrouping preserves each earlier round's access. It does not select diverse partners or observe spoken conversation.
- Fixed 1-2-4-All software coordination uses exact timed windows and roster-based solo/pair/quartet/whole-group partitions. Optional typed notes remain group-private; human synthesis and live discussion are not inferred. This differs from 0.12's after-round reveal and setup-supplied maps.
- A new pooled-ideas-and-pairs arrangement reuses both pool and group operations, transfers between apps, and preserves private results after restart. No complete-activity token was added.

The proposed 25/10 target still needs numeric ratings, repeated card routing, exact score aggregation, and ranked reveal. Streams, media, recurrence, and permissioned dialogue remain unported. The [migration checklist](format/0.14/MIGRATION.md) includes all twenty earlier packages: zero complete migrations, twenty requiring additional rules, zero dismissed as outside scope. Counts refer to full legacy behavior and supported setup choices, not similarity of titles or selected variants. The [next milestone](ROADMAP.md#path-from-013-onward) addresses exact timing and instance setup bindings first.

## Composed candidate 0.15 evidence

Candidate 0.15 adds [scheduled collection and saved settings](format/0.15/README.md#saved-instance-settings). Its twelve examples and sixteen traces pass both independent app hosts. The twelve previous traces retain the same outcomes and views.

The [migration checklist](format/0.15/MIGRATION.md) now records **one complete migration, nineteen requiring additional rules, and zero outside scope**. The scheduled text check-in reproduces its earlier opening/closing constraints, optional saved question, one private answer per participant, exact closing, missing-answer omission, and accepted-order reveal. Six scenarios compare the unchanged legacy reference model and actual 0.12 implementations with 0.15 in both languages. Envelope and view shapes differ; adapters compare behavior and audience access rather than asserting wire compatibility.

A scheduled check-in followed by paired reflection demonstrates the same schedule composed with a different audience and continuation; it transfers and survives restart in both apps. A structured scheduled poll additionally tests reveal and tally with a literal deadline. This does not supply recurrence, routed numeric scoring, ongoing streams, or media. Those remain explicit gaps in the [roadmap](ROADMAP.md#path-from-013-onward).

## Composed candidate 0.16 evidence

Candidate 0.16 adds bounded numeric form fields, item routing, private ratings, exact aggregation, and tied ranked publication. Fourteen examples and twenty-two traces pass the independent app hosts; the sixteen earlier traces keep their outcomes and views.

The proposed [25/10 digital target](format/0.16/scoring-notes.md) now has five distinct non-author reviewers per submitted idea, hidden raw scores, item/round-bound acceptance, exact five-rating normalized totals, and a top-ten rank cutoff including every boundary tie. Missing ratings are omitted from exact scaled means; no-score cards are published separately as unrated. Deterministic roster offsets, a six-person digital minimum, timed missing-rating recovery, and tie handling are declared digital choices, not claims about the physical source procedure or source endorsement of online use.

A second [proposal assessment](format/0.16/examples/proposal-assessment.json) uses two rounds, a 0–10 scale, summed scores, and private paired follow-up. Another witness uses integers in an ordinary form without scoring. Rating races, stale rounds, fractional/Boolean rejection, zero versus missing ratings, unpublished aggregate privacy, worker jumps, restart, opaque IDs, and transfer are checked.

The [legacy checklist](format/0.16/MIGRATION.md) remains **one complete migration and nineteen incomplete**, with none dropped from scope. Ranked item scores do not supply caption ballots, team-owned progress streams, weighted grading, arbitrary reviewer allocation, or recurrence. The [next milestone](ROADMAP.md#path-from-013-onward) addresses fixed repeated practice before longer/media flows.

## Composed candidate 0.17 evidence

Candidate 0.17 supplies bounded fixed recurrence through `for_windows@1` and `collect_window@1`, with public per-person completion status only when declared. Eighteen packages and twenty-seven traces pass independent interpreters and durable hosts. All twenty-two 0.16 traces preserve their outcomes/views. Eighty-four invalid definitions and maximum-clock/366-window/late-continuation probes check the bounded grammar and timing.

The three text daily-practice packages now have complete comparison evidence against the legacy reference and actual retained 0.12 hosts in both languages. Nine scenarios cover original fixtures, actual day-sized gaps and histories, stale actions and accepted retries, all visibility modes, maximum closing times and restart. Separate worker/race/unsupported/transfer probes check durable enforcement. A repeated choice/tally schedule followed by paired reflection demonstrates reuse beyond the migrated practices.

The [legacy inventory](format/0.17/MIGRATION.md) now records **four complete migrations and sixteen incomplete**, with no example silently dropped. Image recurrence still lacks authorized media values; fixed elapsed intervals do not provide local-calendar scheduling or notification delivery. Ongoing streams, linked sources, richer assignment, host roles and mutable lifecycle rules remain distinct work.

For readiness review, exact product parity and core experience are separate. A simplified creative response can use one assigned non-self source rather than two offered alternatives. The next bounded milestone targets explicit distribution algorithms and authoritative source-linked responses. Optional choice/exposure balancing remains deferred; a simplified package will not be labeled a complete Chorus or legacy offered-response migration.

## Composed candidate 0.18 evidence

Candidate 0.18 adds `assign_sources@1`, `respond@1` and `reveal_responses@1`. Two named policies select one non-self source from a closed text pool: next contributing person in roster order, or a precisely specified seeded sampler. Packages explicitly choose participants/contributors as recipients and declare one-source cardinality, allowed reuse and unmatched skip. Saved assignments and consumed generator state survive retry and restart. Neither policy promises balanced exposure or cryptographic randomness.

Twenty examples and thirty-four traces pass independent interpreters and durable hosts; all twenty-seven 0.17 traces keep their outcomes/views. One hundred nine invalid definitions, twelve schema-negative witnesses, exact sampler/rejection vectors, seed-restore checks and linked-response privacy/deadline probes exercise the new slice. Durable evidence includes assignment reads racing workers, response races, changed process seed without reroll, host-generated seed persistence and an authored random response/pairs transfer.

| Activity witness | Core experience now expressible | Remaining scope |
|---|---|---|
| Simplified Chorus-like creative response | One saved randomized non-self text source, independent source-bound text response, deadline and attributed linked reveal. | Actual image/audio/video, late cover threshold, replacements/moderation, host participation and mutable dates. Two alternatives, participant choice and exposure balancing remain optional refinements. Full Chorus parity is not asserted. |
| Legacy paired story response and caption family | General source distribution and authoritative response relations now exist. | Exact balanced two-offer selection, legacy schedule/insufficient-source branch, media and caption ballot rules remain unported. |
| Idea exchange with paired continuation | Deterministic non-self source assignment, independent text review, all-matched-response close and later pair-private reflection. | Human evaluation, reviewer balancing and scoring are not inferred. |

The [legacy checklist](format/0.18/MIGRATION.md) remains **four complete and sixteen incomplete**, with no false migration credit for simplified rules. The next proposed core milestone is authorized PNG values in scheduled/recurring forms: image check-in and image daily-practice each lack only media support. Ongoing multi-entry streams and permissions/lifecycle remain further gaps. Upload processing, drafts, notifications and publishing app records remain host integration concerns. Coverage review assesses useful core scope and explicit unsupported capabilities; real-world activity needs determine whether optional app details or new primitives merit work.

## Composed candidate 0.19: typed image forms

| Witness | Verified result | Limit |
|---|---|---|
| Image check-in | Host-authorized private image value, deadline reveal; full selected legacy timing/setup/phase/order/privacy compared in both actual host implementations. | PNG is the local byte profile, not the language type. |
| Daily image prompt | Group-immediate image values and occurrence-bound completion/missed history reproduce the selected legacy package; full day-sized comparisons, replay and restart. | Fixed bounded recurrence; no dynamic calendar scheduling. |
| Private recurring images | Independent additional package conceals each new contribution until its window reveal; historical reveal does not expose another unpublished reference. | This distinct authored variant is not counted as a legacy migration. |
| New image-to-story combination | Uploaded ready images, typed form, explicit reveal and cumulative text continuation transfer/run with no interpreter changes. | Package exchange does not migrate live state or stored blobs. |

The candidate has 23 examples, 38 engine traces, 114 invalid definitions and all 34 prior traces preserved. Both durable hosts pass actual bytes, authority/privacy, partial-success retries, races, workers and restart. Six legacy packages are now fully compared; fourteen remain incomplete. Image pools/routing/linked responses, ongoing streams, replacement/moderation, host participation and live schedule changes remain unsupported. Rich offers/choice/exposure balancing remain optional parity. The [supported-profile assessment](format/0.19/readiness-assessment.md) recommends a current held-out coverage challenge and supported-profile review before automatically adding more capabilities. Coverage remains limited to the documented supported profile.

## Candidate 0.19 held-out profile review

The [pinned review](experiments/format-0.19-readiness/README.md) adds four authored cross-family arrangements, all passing schema, independent engines, every-boundary restart and both durable hosts. Six direct limits and a real-byte workaround establish that typed image identity cannot flow into source assignment; a reference string assigned as text grants no image read access. Images/forms and text exchange can coexist, but this is not image-source exchange.

The [historical capability inventory](experiments/format-0.19-readiness/inventory.md) separates supported activity families, important missing primitives, optional parity, host responsibilities and nonfunctional limits. It recommends deciding whether single-source image exchange belongs in the initial core before further expansion; ongoing streams and enforced feedback permissions are separate scope decisions. These remain capability and scope questions. Independent review confirmed the PNG implementation defects closed at `eab8745`; they are not classified as optional scope.

## Composed candidate 0.20: typed exchange and host boundary

Typed image sources now retain authority and identity through saved non-self assignment, independent text/audio response and explicit linked reveal. The [three witnesses](format/0.20/artifact-notes.md) cover simplified Chorus, immediately public primary Feedback with external open discussion, and a solo host-dated daily journal. A newly authored typed exchange composes into retained private pair reflection. These are selected digital experiences, not full product migrations.

26 examples, 44 normative traces, 129 invalid definitions, all 38 previous traces preserved and both durable hosts cover actual image/audio uploads/grants, source/response/control races, every-event restart, partial retries, multi-day worker deadlines, negotiation and immutable transfer. Six historical migrations remain complete, fourteen incomplete. The [supported-profile assessment](format/0.20/readiness-assessment.md) keeps permissions/streams/replacements/general concurrency as explicit unsupported capabilities and two-option offers/fairness/exact product replication as optional. Host roles/calendars/discussion/administration are outside the language when later operations do not consume their outputs. Independent review and user review remain separate evidence.

## Composed candidate 0.21: voting and finite continuation

Accepted typed source identity can now feed voting; allowed vote changes retain one current counted ballot. Individual ballot visibility remains separate from aggregate publication. Most-votes selection produces structured selected/tied/no-vote/no-candidate outcomes, with a uniform and durably stable random tie policy. A general presentation instruction shows typed output; an explicitly named later round can consume selected material. [Four new witnesses](format/0.21/README.md) cover a predefined poll, contribution contest, creative continuation and proposal workshop using retained pair-private deliberation. All rules are package data, without activity-name dispatch.

[Current evidence](validation/0.21/EVIDENCE.md) records independent engines/schema, durable hosts, actual media, consequential boundaries and full 44-trace historical compatibility. Thirty examples and the new profile do not imply faithful prospective host app migration: prospective host app is a prospective host app, and result-derived eligibility, designated-person tie choices, unlimited streams and broader product lifecycle remain outside scope. The six complete historical migrations and fourteen incomplete migrations are unchanged. [Supported limits](format/0.21/readiness-assessment.md), [compatibility](format/0.21/COMPATIBILITY.md) and [review packet](format/0.21/HOST-REVIEW.md) accompany the candidate.

## Composed candidate 0.22: supplied material and host-launched continuation

A package can declare a real text/image/audio starting contribution, preserving its globally qualified identity, author and origin while separately recording the decision that supplied it. Authoritative setup checks every viewer, including the organizer, future actors and later additions, before publication or media grants. A five-step creative package collects continuations, privately votes, counts, selects and presents; the host may supply the actual selected contribution to another instance using the declared input contract. Ordinary reuse through `pool@1`/`for_items@1` and linked source/response instructions already existed.

Optional random or retain-input policies handle a nonempty pool with zero counted votes. Omission retains the no-vote stop; zero candidates always remains empty. Thirty-four examples, 73 independent-engine traces, 231 invalid definitions, full 57-trace historical compatibility and both durable hosts validate inputs, privacy, bytes, deadlines/races, retries/recovery, stable random selection and a distinct supplied-brief proposal/planning/pair exercise. See [evidence](validation/0.22/EVIDENCE.md), [supported limits](format/0.22/readiness-assessment.md) and [review packet](format/0.22/HOST-REVIEW.md).

Six historical migrations remain complete and fourteen incomplete. Successor scheduling, cross-provider trust/storage, product lifecycle, result-derived eligibility and designated-person tie decisions remain outside this profile. Author-selected kinds already exist in typed pools; configurable multi-entry quotas and compatible typed iteration are assessed for [0.23](format/0.22/POOLING-ASSESSMENT.md), not supported by this candidate.

## Composed candidate 0.23: typed quotas and compatible consumers

Authors configure one pool for text, image, audio or mixed material and up to eight immutable contributions per person. Typed item iteration preserves commit order and private reader access until explicit attributed reveal. Compatible voting keeps each item as a distinct qualified candidate; one-source linked exchange reveals only used source/response pairs. Six new witnesses include different pool configurations, typed sharing, contests, supplied continuation and a held-out response/private-pairs workshop. Earlier item loops and linked responses already reused material.

108 traces, 324 invalid definitions, all 40 schema-valid examples and actual historical comparison of all 73 retained traces pass; both durable hosts validate real media, quotas/order/eligibility, privacy, races/retries/restart and immutable package transfer. [Evidence](validation/0.23/EVIDENCE.md) and [profile](format/0.23/readiness-assessment.md) retain six complete/fourteen incomplete migration accounting. No exposure balancing, unlimited streams, result-derived roles or production certification is inferred.

## October 2, 2026: candidate 0.24 relay support

[0.24](format/0.24/README.md) adds a bounded first-valid typed collection with saved rolling invitations. Shared deadlines, loser carry-over, previous-author exclusion, expiry/decline/membership, canonical and queue authority, source consumption and retry are explicit. Host notification delivery/successor launching remains host work. [Evidence](validation/0.24/EVIDENCE.md) and [profile](format/0.24/readiness-assessment.md) distinguish supported behavior from production host requirements. Earlier migration counts remain six complete and fourteen incomplete; inspector/playground remain unchanged.

Independent authoring/schema review cleared the completed pin `af44752fa73007746108d555dc9338e4abb10c16`. Independent runtime clearance of its queue-audience correction remains unverified after a platform safeguard stopped the recheck; completed local validation does not substitute for that review.
