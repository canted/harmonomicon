# Offer-flow contract experiment

This experiment tests two cases identified by the [digital activity stress study](../../research/digital-activity-stress-cases.md) and the earlier [named-mechanism comparison](../named-mechanisms/comparison.md). It does **not** propose a public plugin format.

| Case | Definition | What the app coordinates |
|---|---|---|
| Proposed [two-offer picture telephone](definitions/two-offer-relay.json) | `competitive_relay` | Two people may fill one pending step; one valid submission advances the chain. A deadline can reoffer the same step to a second pair. |
| [Cover and Response](definitions/cover-response.json) | `cover_response` | People submit cover images; after the deadline and a minimum count, each responder receives two other people's covers, chooses one, and submits a linked response. |

The first is a proposed digital variant of Eat Poop You Cat, **not** an observed rule of that game or Drawception. The second is a [constructed activity](../../research/activities/cover-and-response.md) for testing collection, balanced artifact offers, linked responses, and reveal; it is not attributed to a named product. Their common word “offer” hides different relationships: two recipients compete for **one task** in the relay; one recipient chooses between **two source artifacts** in Cover and Response.

## Run

```sh
python3 experiments/offer-flows/check.py
```

The checker compares independently written JavaScript and Python interpreters against [14 hand-stated fixtures](cases/). At each supported fixture's checkpoint, one process emits a JSON snapshot and a fresh process resumes it. Each language resumes both its own and the other language's snapshot, then the checker compares the result with uninterrupted replay. The [contract](contract.md) states the exact experimental semantics; the [findings](findings.md) summarize what the results do and do not establish.
