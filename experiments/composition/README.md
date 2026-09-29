# Composition experiment

This follow-up to [offer flows](../offer-flows/README.md) tests whether reusable operations can describe two unlike flows and a held-out queue recovery case without dispatching on an activity ID. The JSON stage plans are interpreted independently by [Python](run.py) and [JavaScript](run.mjs). This is an experiment, not a public package format.

| Plan | Evidence and scope | Tested behavior |
|---|---|---|
| [Two-recipient relay](definitions/relay.json) | [Proposed digital variant](../../research/digital-activity-stress-cases.md), not a documented Eat Poop You Cat rule | One winner, retry, timeout fallback, private input |
| [Cover and Response](definitions/cover-response.json) | [Constructed activity](../../research/activities/cover-and-response.md) | Minimum-cover barrier, saved balanced offer, linked response, reveal |
| [Picture telephone queue slice](definitions/drawception.json) | [Drawception card](../../research/activities/drawception-picture-telephone.md); skip and requeue are documented, selection is unspecified | Lease, skip/release, another participant claims, final reveal |

Run from the repository root:

```sh
python3 experiments/composition/check.py
```

The checker replays all 14 unchanged [offer-flow event traces](../offer-flows/cases/) through both new interpreters, compares their outcomes and relevant state and view fields with the earlier Python interpreter, then runs three newly written queue cases. [Contract](contract.md) gives the narrow semantics. [Findings](findings.md) record costs and unresolved boundaries.
