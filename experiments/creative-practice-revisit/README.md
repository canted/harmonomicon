# Revisit: game jams and shared creative practice

**Status:** Impact audit of existing experiments, not a new protocol or a port of any named product. The [research survey](../../research/creative-jams-and-shared-practice.md) supplies the source-backed cases. This audit keeps their documented behavior separate from the test configurations below.

Run the diagnostic against the existing independent interpreters:

```sh
python3 experiments/creative-practice-revisit/check.py
```

The checker tries all six combinations of the named `collection` mechanism's two view gates and three late policies: after one post, after two, after close, and after the next daily `open`. It also submits two progress artifacts by one actor to the composed stage-plan `collect` operation. Both JavaScript and Python agree on the outcomes. These tests establish the behavior of those **specific contracts**; they do not prove that no future package format could express the activities.

## Impact by experiment

| Existing experiment | What the new cases test | Result of the revisit |
|---|---|---|
| [General transitions](../README.md) | [750 Words](../../research/activities/750-words-month-challenge.md) keeps writing private while exposing completion; [Day One](../../research/activities/day-one-shared-journal.md) has author/member entry rights. | A package can keep writing out of state and expose a status field, but then content handling and verified word count are outside its semantics. Public progress could be appended to state, but views copy whole top-level fields: a map of many private entries cannot be projected as only the requesting participant's entry. The earlier 12-case result remains valid. |
| [Named mechanisms](../named-mechanisms/README.md) | Daily prompt, optional public posting, status-only check-in, and a month-long record. | The `collection` case already tests one daily occurrence and recurrence. In the diagnostic, either the artifact is hidden along with status (`at_close` before close) or visible as part of the whole `posts` map. On the next `open`, posts reset. A host can submit a status token instead of writing, but then it must manage the writing and monthly ledger separately. The earlier nine cases remain valid. |
| [Offer flows](../offer-flows/README.md) | [Relay Jam](../../research/activities/relay-jam-2026.md) has a scheduled A-to-B project handoff; a [game jam](../../research/activities/itch-ranked-game-jam.md) can have a later review window. | No original outcome changes. The proposed two-recipient picture-telephone relay is a **different algorithm** from Relay Jam's sequential source handoff. [Cover and Response](../../research/activities/cover-and-response.md) has a phase barrier and offers, but neither flow models a team project with continuing progress discussion. |
| [Composed stage plans](../composition/README.md) | [Jam progress](../../research/creative-jams-and-shared-practice.md#game-jam-shapes-found) can produce multiple updates during an ongoing work period; [Waffle](../../research/activities/waffle-shared-journal.md) can accumulate entries. | Two accepted `collect` events from one actor leave only the later artifact in that actor's slot. The stage plan has one current stage; it has no threaded comment or independent progress stream alongside final submission/review. Its 17 conformance cases remain valid for their original scopes. |

## Concrete diagnostic results

1. With `viewGate: after_own`, each participant's view contains the complete `posts` map after both write. If its artifacts are private journal references, each sees the other's reference. With `viewGate: at_close`, no participant sees either artifact before close; after close, both see the same complete map. Changing `latePolicy` does not change this projection. The current `collection` contract therefore has **no single configuration that both stores participant-private writing in `posts` and publishes only completion status**. A status-only token is a partial mapping, not the full journaling flow.
   After Alice alone posts, Bob sees no post under either gate. The same two options also cannot expose a [Jamuary](../../research/activities/jamuary.md) forum-style recording to a non-posting participant as soon as it appears.
2. Opening the next daily occurrence clears `posts` and `late`. This suits the earlier [daily photo trace](../named-mechanisms/cases/06-daily-recur.json), which tests only the current occurrence, but does not record [750 Words'](../../research/activities/750-words-month-challenge.md) month-to-date result or an ongoing [Jamuary](../../research/activities/jamuary.md) gallery.
3. In the composed `collect` operation, the second accepted update by `alice` replaces the first in `collections.updates.alice`. The operation is designed for one active artifact per actor, matching the [Cover and Response](../../research/activities/cover-and-response.md) cover collection. It does not preserve multiple [jam progress posts](../../research/creative-jams-and-shared-practice.md#game-jam-shapes-found). This is a contract boundary, not an interpreter bug.

## What remains covered and the follow-up test

The existing tests still establish their reported narrow behavior: recurrence and late marking for a BeReal-like photo collection, one-winner offer semantics, saved cover offers, queue skip/reassignment, and independent-language agreement. The new cases mainly challenge **composition over time and audience separation**, not those algorithms.

The diagnostic identified two short traces to test before expanding the schema:

- **Jam session:** register a team, post two optional progress updates and one response while the final-submission window stays open, submit a final project, then enter a separate review/reveal window. Give each record an explicit audience. This combines documented jam interactions, but the exact all-in-one mediation remains a proposed test design.
- **Daily practice:** compare a private writing/completion-only day with a public-as-posted creative submission day, then advance to the next day without losing the month record. The source-backed contrast is [750 Words](../../research/activities/750-words-month-challenge.md) versus [Jamuary](../../research/activities/jamuary.md); the combined test is not attributed to either product.

These probes should precede any claim that the current composed stage plan is a general core for ongoing activities. The previously identified [assignment-policy portability test](../composition/findings.md#limits-and-next-boundary) remains useful, but it answers a different question: whether two hosts make the same assignment after the activity shape is representable.

The subsequent [ongoing-activity experiment](../ongoing-activities/README.md) implements both probes under a separate, narrow contract and records their results. The diagnostic observations above still describe the earlier interpreters.
