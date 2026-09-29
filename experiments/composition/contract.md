# Composition contract 0.1

**Experimental scope.** A plan is JSON with `actors` (actor ID to role), `requires` (host capability names), `bindings` (event type to operation), an `initialChain`, ordered `stages`, terminal phases, and optional reveal/deadline settings. Events are `{type, actor, at, payload}`. The host supplies an authoritative serial event order and integer clock values. A missing capability returns `unsupported` before execution. Rejected events do not apply their requested operation; a clock update can still advance a scheduled phase before that operation is checked.

## Shared operations

| Operation | Meaning in this experiment |
|---|---|
| `collect` | Store or replace one participant's named artifact in the collection stage; reject a duplicate ID owned by another actor. |
| `remove` | Let the host remove a named collected artifact before its cutoff. |
| `advance` | Accept a system clock tick; the clock update itself evaluates stage and final deadlines. |
| `assign` | Create work access according to the stage's named assignment policy. |
| `choose` | Save one artifact choice from a prior offer. |
| `commit` | Accept one contribution according to the stage's completion mode. |
| `expire` | Close a timed recipient attempt and select the next configured attempt or stall. |
| `release` | Return an active queue lease to idle without changing its input. |

There are two stage types. A `collection` stage can advance once its `deadline` has passed and its `minimum` has been met, including by a later submission. A `work` stage accepts contributions under its assignment and commit configuration. A `finalDeadline` finishes an entire plan on or after that time. The stage plan, operation names, and binding names are data; both interpreters branch on operation, stage type, assignment policy, and commit mode. Neither branches on `id` or `source`.

## Policies and commit modes

`fixed_recipients` opens a configured recipient list for the current attempt until a supplied deadline. `queue_lease` grants the idle task to the actor whose claim event the host processes first; `release` frees it for another claim. `balanced_artifacts` selects a fixed number of other participants' collected artifacts, sorted by existing offer count and then by `cover_offer_score_v1`, the small-ID score described in the [Cover and Response contract](../offer-flows/contract.md#cover-and-response). Its saved offer survives repeat requests. Another host would have to implement the same score and ordering.

`first` accepts the first valid contribution from an active assignee and advances the stage. It can require a stage/attempt pair and request ID for replay detection. `per_actor` accepts one response per actor after a saved choice and links it to the chosen artifact. The media field is checked; artifact references are opaque strings. No storage or transcoding is performed.

The view exposes the current input only to an active assignee. A participant sees their own collected artifact, their own saved offer and choice, and their own response. The plan may reveal the chain or all responses at `done`. These are output projections, not a proof that an HTTP server or database enforces access control.

## Deliberate bounds

The relay uses preset recipients. The queue example uses two alternations rather than Drawception's documented standard twelve-person chain. A `claim` is already an authoritative host event: queue eligibility, random selection, timeouts, dustcatcher removal, and simultaneous server writes are outside this model. The selected Drawception source documents skip/requeue but does not publish the selection algorithm. The interpreters do not validate arbitrary plans, persist state, generate messages, schedule workers, or resume from checkpoints. Earlier [offer-flow tests](../offer-flows/findings.md) separately exercise JSON snapshot continuation.
