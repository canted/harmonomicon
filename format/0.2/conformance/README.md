# 0.2 conformance cases

Run `python3 format/0.2/check.py` from the repository root. This checks package fields, cross-field constraints, events, and participant views with one reference model. It is not a JSON Schema validator or an independent host implementation.

Each JSON case supplies a package, instance setup, ordered events, expected outcomes, and semantic participant views. A host may display those views with different screens or API field names. An absent `own`, `input`, or `entries` key means the viewer must not receive that content through the activity view.

The five carried-forward 0.1 cases check [timed collection](collection.json), [read at closing time](collection-read-close.json), [sequential handoff](handoff.json), [missing capability](unsupported.json), and [missing behavior](unsupported-behavior.json). Their behavior rules are unchanged; their example packages use the 0.2 envelope and new package versions.

The new cases check:

- [Private repeated collection](repeated-private.json): group-visible completion status without shared entry content, a missed window, history retained after the next opening, stale occurrence rejection, final completion, and event-ID replay.
- [Immediate group sharing](repeated-public.json): an entry appears to other participants before the window closes, and the prior occurrence remains visible in the next window.
- [Reveal after close](repeated-after-close.json): status is visible while content is private, then accepted entries appear when that occurrence closes.
- [Unsupported repeated collection](repeated-unsupported.json): a host missing the exact behavior and clock tokens rejects the package before creating an instance.

Times in the new cases are synthetic Unix milliseconds. The examples use a fixed 86,400,000 ms interval and a 72,000,000 ms submission window. The cases test exact boundaries; they do not claim local-calendar scheduling, notification delivery, actual media storage, or durable host behavior. The [0.2 local host trial](../../../validation/0.2/README.md) runs these cases through separate Python and Node.js hosts with durable state, workers, and authenticated views. It remains limited to the checked-in text packages and local test conditions.
