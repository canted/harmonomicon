# Pass 4: portable activity contract experiment

**Status:** Experimental conformance exercise, not a proposed standard.

The [research cards](../research/activities/) describe human procedures. This directory tests whether unlike activities can share a small, language-independent executable representation. The definitions are JSON data; [JavaScript](interpreters/run.mjs) and [Python](interpreters/run.py) interpret the same files independently. A host may be a person assisted by software. A recorded event can therefore be a fact a person reports, not something software sensed.

## Scope

Definitions and traces cover [Pass the Parcel](../research/activities/pass-the-parcel.md), [Exquisite Corpse](../research/activities/exquisite-corpse-drawing.md), [1-2-4-All](../research/activities/1-2-4-all.md), [BeReal's daily post pattern](../research/activities/bereal-daily-post.md), [Critical Response Process](../research/activities/critical-response-process.md), and [Cook Along Challenge](../research/activities/cook-along-challenge.md). The last two are named practices and the BeReal trace describes product behavior; these files are research exercises, not distributable implementations of those activities.

Every definition carries brief human instructions and source attribution, and names required capabilities, actor roles, initial state, event transitions, and role-dependent state views. Traces include valid and rejected events. A separate capability case asks a generic host to load a live singing definition requiring low-latency audio and expects `unsupported`.

## Tiny contract

The precise grammar is in [contract.md](contract.md). Its purpose is to test semantic agreement, so it deliberately has few operations. It does **not** encode interfaces, human instructions in full, media transport, real timers, identity proof, storage, or legal rights. An `artifact` is an opaque reference; the host decides how to store and display it. `at` timestamps in traces are integer milliseconds supplied by the test host.

The two interpreters must:

1. Reject a package with a missing capability before any event runs.
2. Process each event atomically: select exactly one transition whose event type, actor role, and conditions match; apply its actions to a copy of state; reject without changing state if none or more than one matches or an action is invalid.
3. Resolve view rules separately for a named actor after the trace. A hidden field is absent from the view, not set to `null`.
4. Produce the same canonical JSON output as each fixture's `expected` block.

Run both implementations and compare them with fixtures:

```sh
python3 experiments/check.py
```

No dependency installation is required beyond Python 3 and Node.js. The fixtures test the defined examples, not every possible package. The [findings](findings.md) record mismatches, missing expressiveness, and the next decision points.

A [named-mechanism follow-up](named-mechanisms/README.md) tests smaller definitions for digital handoff and collection patterns, including an experimental digital version inspired by Pass the Parcel.

The [offer-flow experiment](offer-flows/README.md) tests the proposed two-recipient relay and the constructed [Cover and Response](../research/activities/cover-and-response.md) activity in two languages, with deadline races and JSON checkpoint continuation.

The [composition follow-up](composition/README.md) replays those traces through a stage-plan interpreter and adds a held-out Drawception queue case. Its [findings](composition/findings.md) identify the policy portability boundary.

The [ongoing-activity follow-up](ongoing-activities/README.md) tests two gaps raised by the later creative-practice survey: optional jam conversation alongside a final-submission window, and daily records with content visibility separate from completion status.

The [assignment-policy portability follow-up](policy-portability/README.md) specifies one versioned offer algorithm over decimal-string IDs, then compares JavaScript, Python, and Ruby results and cross-runtime checkpoints.

The [creative-practice revisit](creative-practice-revisit/README.md) audits all four experiment families against the later game-jam and group-journaling cases. Its diagnostic runs existing interpreters without changing their contracts.
