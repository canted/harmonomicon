# Named-mechanism comparison

This follow-up compares the [general transition experiment](../README.md) with two built-in mechanisms that a host can implement directly. It is an experiment, not a proposed standard. JSON definitions select a mechanism and supply parameters; they contain no per-event guard/action program. JavaScript and Python implementations run the same fixtures.

The examples are two pairs:

| Mechanism | Definitions | Shared app behavior |
|---|---|---|
| `handoff` | [Digital Exquisite Corpse](definitions/digital-exquisite-corpse.json), [Digital Parcel](definitions/digital-parcel.json) | One current actor completes a step, then the app gives the next actor a turn. The first collects hidden contributions; the second reveals a preloaded item per step. Digital Parcel is an experimental translation inspired by [Pass the Parcel](../../research/activities/pass-the-parcel.md), not a documented traditional variant. |
| `collection` | [Daily Photo](definitions/daily-photo.json), [Photo Walk](definitions/photo-walk.json) | The app opens an occurrence, accepts participant media, applies a deadline policy, and controls when other submissions are visible. Photo Walk is an illustrative prompt from the project discussion, not an observed named activity. |

Run `python3 experiments/named-mechanisms/check.py`. The check compares both implementations with explicit expected outcomes and views, including invalid turns, duplicate submissions, late submissions, two visibility policies, recurrence, and an unsupported capability. The [comparison](comparison.md) records what became shorter and what complexity moved into hosts.
