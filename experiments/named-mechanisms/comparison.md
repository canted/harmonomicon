# Comparison with the transition vocabulary

**Result:** Two independent interpreters passed **9 cases each** for four compact definitions using two named mechanisms. The cases test app-side turns, hidden and revealed contributions, per-step reveal, scheduled collection, late marking, duplicate rejection, and a missing capability. Reproduce with `python3 experiments/named-mechanisms/check.py`.

## What became smaller

| Activity-shaped example | General transition definition | Named-mechanism definition |
|---|---:|---:|
| Digital Exquisite Corpse | 227 formatted JSON lines | 35 formatted JSON lines |
| Daily photo pattern | 254 formatted JSON lines | 33 formatted JSON lines |

The figures are file lengths in this repository, not a claim about all future packages. The two versions test similar core transitions but do not have identical content fields or every same edge case. The named definitions are shorter because the host already knows what `handoff` and `collection` mean. The [JavaScript](run.mjs) and [Python](run.py) implementations are 93 and 106 lines for **only these two mechanisms**; the [general interpreters](../interpreters/) are 135 and 152 lines but cover six activity definitions. Those implementation sizes are not directly comparable as a total-cost measure.

The reuse is concrete: `handoff` runs both a [concealed drawing](definitions/digital-exquisite-corpse.json) and an experimental [digital parcel](definitions/digital-parcel.json); `collection` runs both a [daily photo round](definitions/daily-photo.json) and a [one-shot photo walk](definitions/photo-walk.json). The latter two differ in recurrence and visibility policy without adding a new interpreter branch.

## Where the burden moved

Each host must implement the full meaning of each named mechanism. The `handoff` engine currently permits only two mode/reveal combinations. A variant requiring simultaneous contributions, a different handoff rule, an optional turn, or multiple recipients would need either another parameter with specified semantics or a new mechanism. The `collection` engine does not schedule the next day itself, prove media contents, send notifications, or persist artifacts. Its host supplies `open` events and opaque artifact references.

This is a clear portability tradeoff: definitions are compact only to the extent that every conforming host already supports their named mechanisms. A declaration of `requires` must be checked against real host behavior, not just a list of strings. A host that lacks `handoff` or interprets its visibility differently cannot run the package faithfully.

## Cover and Response as an additional contrast

[Cover and Response](../../research/activities/cover-and-response.md) is a constructed digital activity that combines a minimum cover count, a scheduled phase change, saved offers of two other people's covers, participant choice, linked responses, and delayed reveal. It also permits early host removal of a cover. Its full procedure is documented in the activity card; no external app is required to understand the example.

A `collection` or `handoff` mechanism alone cannot express all of those relationships. A portable definition needs to state how the host stores covers, changes phases, assigns offers, remembers each person's choice, links the response, and filters views. The [offer-flow](../offer-flows/README.md) and [composition](../composition/README.md) experiments test that added behavior explicitly.

## Current conclusion

The evidence supports compact, language-independent **definitions for a known mechanism set**. It does not establish that a small mechanism set can cover the broader survey, nor that new activities can run instantly on any app. A host can run a package when it implements the package's named semantics and required capabilities, including their visibility and timing rules. The Cover and Response contrast and a novel-rule case help locate the extension boundary.

The [offer-flow experiment](../offer-flows/findings.md) performs that comparison for Cover and Response and a proposed two-recipient relay. It finds two different offer semantics and tests JSON state continuation across separate JavaScript and Python processes. The paragraph above remains the conclusion of the two-mechanism experiment.

The [creative-practice diagnostic](../creative-practice-revisit/README.md) later exhausts the `collection` view-gate and late-policy configurations for a private-writing/public-status case. It also checks public-as-posted visibility and the loss of prior posts on daily `open`. These are boundaries of this named mechanism, not failures of its original nine fixtures.
