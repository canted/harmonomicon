# Ongoing-activity findings

**Result:** `python3 experiments/ongoing-activities/check.py` passes four traces and five intermediate checkpoints in independent JavaScript and Python interpreters. The interpreters agree on full state, outcomes, and participant views. The fixtures assert the expected rules and check that selected private artifacts never appear in another participant's serialized view.

## What the probes establish

| Question | Observed result in this experimental contract | Limit |
|---|---|---|
| Can optional interactions continue during a jam's making window? | Two progress posts by one team remain distinct, and another team's response remains linked to the visible post. A team-only sketch is absent from the other team's view. | The test app combines channels that real jams may keep in separate services. It does not validate media, notify anyone, or model a thread beyond one response layer. |
| Can final work have different timing and audience rules from progress posts? | The team submits a final project during making; a premature review rejects. In review, participants see finals; in reveal, all see the accepted review. Progress posts reject after the submission boundary. | The exact windows and review permissions are experiment choices. No rating allocation, moderation, edit, or winner rule is tested. |
| Can private daily work expose status without exposing content? | Another participant sees `complete` and later `missed`, but never the private writing references. An at-deadline submission rejects. | The interpreter trusts the artifact and completion event. It does not prove 750 words were written or enforce a local calendar day. |
| Can a public daily post appear immediately and survive recurrence? | Another participant sees the first recording before the day closes, and both daily artifacts remain visible after day two closes. | The imposed deadline and `missed` state are test choices, not a claimed Jamuary penalty. |
| Can a host declare it cannot enforce the required visibility? | A host missing `access_control` returns `unsupported` before any event is processed. | A capability name does not prove correct storage or API access control. |

The older [collection diagnostic](../creative-practice-revisit/README.md) found that its single posts map exposed content and status together and reset on the next `open`. The older composed `collect` operation replaced an actor's earlier progress artifact. These new definitions separate content from status, retain occurrence history, and append progress records. They establish that those particular gaps can be addressed by explicit semantics in two languages. They do **not** establish that this calendar/stream vocabulary is a sufficient general core or that the added implementation cost is justified for every activity.

## Remaining boundary

Both interpreters use a serial host event order, trusted actor IDs and timestamps, and in-memory state. They do not test concurrent writes, idempotent retries, durable snapshots, notifications, or full privacy enforcement. The jam has fixed teams and a single final submission per team; the daily probe has one entry per participant per day. Further breadth is needed before those constraints become standard rules.

The separate [assignment-policy portability test](../composition/findings.md#limits-and-next-boundary) remains open. It asks whether two hosts make the same assignment when the policy itself, rather than the surrounding activity shape, is specified and versioned.
