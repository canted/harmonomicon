# Harmonomicon: toward a portable activity package

**Status:** Research synthesis and provisional 0.1 direction, not a published standard or a schema that hosts can implement yet. The conclusions below follow from the linked surveys and contract experiments.

## Goal and the demonstrated part

The target is an activity definition that one app can export and another app, written in a different language, can run with substantially the same participant rules when it implements the required capabilities. The [scope and portability layers](portable-activity-packages.md) distinguish instructions, behavior, presentation, and records. The experiments demonstrate cross-language agreement on selected event traces and view projections. They do not demonstrate import into two production apps.

The [breadth survey](breadth-survey.md) and [mechanism survey](mechanism-survey.md) establish that the format must accommodate prompts, turns, handoffs, assignments, clocks, late or absent participants, concealment, reveal, and activities with no digital artifact. [Digital stress cases](digital-activity-stress-cases.md) and [creative-practice cases](creative-jams-and-shared-practice.md) add recovery, automated rules, parallel progress, long-lived history, and content/status separation. The survey is a contrast sample, not an exhaustive catalog.

## What each experiment changed

| Experiment | Demonstrated | Constraint for a draft |
|---|---|---|
| [General transitions](../experiments/findings.md) | Two languages agree on selected unlike activities. | A general transition language can become verbose and still omit human context and host duties. |
| [Named mechanisms](../experiments/named-mechanisms/comparison.md) | Compact handoff and collection definitions can share host semantics. | Small definitions shift implementation burden to every host that claims a mechanism. |
| [Offer flows](../experiments/offer-flows/findings.md) | Race, fallback, allocation, visibility, and cross-language snapshot traces can be specified. | Similar-looking offers can require different algorithms. Serial traces do not prove atomic writes. |
| [Composition](../experiments/composition/findings.md) | Some operations can be reused without branching on activity ID. | Assignment policy remains a separate semantic boundary; the composed definitions and interpreters grew. |
| [Ongoing activities](../experiments/ongoing-activities/findings.md) | Repeated progress, concurrent social interaction, retained daily history, and separate content/status views can be interpreted in two languages. | A single linear stage and one artifact per actor do not cover long-running activities. |
| [Policy portability](../experiments/policy-portability/findings.md) | One versioned assignment rule agrees in three languages on ties, large IDs, retry, and checkpoint continuation. | Each supported policy needs precise semantics and host code; a version token alone is insufficient. |

## Provisional 0.1 architecture

The evidence supports drafting **a portable package envelope plus separately versioned behavior contracts**, rather than declaring any one experimental JSON format universal. The envelope should contain:

1. A stable package ID, package version, source attribution, human instructions, setup, variants, and participation/access notes. These are first-class content, not incidental links to research cards.
2. Configurable parameters with types and defaults, participant roles, named events, and expected input/artifact types. A package must identify facts reported by a person or host rather than implying that software sensed them.
3. A behavior reference to one or more standardized mechanisms or operations, with exact versions and conformance examples. A novel assignment or scoring rule may name a separately versioned policy. The exact composition grammar remains to be drafted and tested; the current stage-plan and ongoing-activity contracts are incompatible experiments, not parts of a settled schema.
4. Required host capabilities such as authenticated actors, trusted time, media references, private views, messaging, or a particular low-latency medium. A host must reject a package whose required behavior or capability it cannot provide. The [policy probe](../experiments/policy-portability/contract.md) shows an exact-version token and explicit `unsupported` result for one algorithm.
5. Conformance traces that state expected transitions and audience-specific views. Language-neutral examples are necessary because a JSON field name alone does not fix behavior.

The first draft should promise **definition portability** across hosts that satisfy a package's requirements. It should not yet promise migration of a running instance, byte-identical presentation, or successful physical-world observation. The current [record-portability question](portable-activity-packages.md#open-decisions) remains open; cross-language test checkpoints are evidence about selected serialized states, not a general migration contract. Deferring that promise keeps the first draft aligned with tested behavior.

This architecture is language-independent at the package boundary. It does not prohibit host-specific implementations of a named mechanism or policy. A JavaScript callback in the package would defeat the cross-language goal unless it were an explicitly negotiated extension; no such executable extension is selected by these experiments.

## Decisions still needed to turn this into a standard

- **Common behavior grammar:** decide the smallest normative mechanism/operation set. The existing `handoff`, `collection`, stage-plan, and ongoing-stream experiments do not yet form one grammar. A draft must say whether these are distinct profiles, composable operations, or examples from which a smaller core is extracted.
- **Capability claims:** define how a host proves or is tested for `access_control`, `clock`, `media`, and atomic commit, rather than accepting names alone. The current fixtures only check declarations and interpreter output.
- **Host obligations:** define event ordering, idempotency, durable state, artifact references, scheduled actions, and audience enforcement at API/storage boundaries. Real delivery and storage were outside the interpreters.
- **Package records and migration:** decide whether later versions standardize export of instances, event logs, artifacts, and history. If 0.1 promises this, a cross-host migration experiment is required before that claim.
- **Rights and provenance:** carry source attribution and permission information for human instructions and media; avoid presenting a research reconstruction as a canonical or licensed package for a named activity.

## Next validation gate

The next test should import the **same small candidate package** into two separate host implementations and exercise an actual durable event store, scheduler or worker, and participant view boundary. One simple handoff and one activity with either a versioned assignment policy or recurring private/public records would expose whether the envelope and host contract are usable. The hosts need different implementation stacks, but neither needs a polished interface. Their results should be compared with package conformance traces, including unsupported capabilities, retry, deadline, and access cases. This is a focused host integration experiment, not a request for more breadth surveying.
