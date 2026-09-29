# Portable activity packages: design question

**Status:** Research direction, not a settled format.

## Goal

Describe an activity once so that multiple host systems, written in different programming languages, can run or assist it with substantially the same rules. A Node.js/SQL implementation could be one host, rather than the language or storage model of the activity itself.

The [current Pass the Parcel card](activities/pass-the-parcel.md) already describes the human rules without requiring a programming language. That is descriptive portability. Executable portability requires further decisions.

## Distinct kinds of portability

| Layer | Cross-system question |
|---|---|
| Instructions | Can a host present the same purpose, setup, and participant directions? |
| Behavior | Do the same events cause the same assignments, transitions, and outcomes? |
| Presentation | Can different interfaces show the activity adequately without identical screens? |
| Records | Can a host preserve and export the activity's configuration, events, artifacts, and final state? |

Sharing a JSON or YAML file answers only part of the question. Two hosts need the same meanings for its fields and rules, not merely parsers for its syntax.

## Candidate separation

1. **Portable activity package:** identifier and version; human instructions; configurable parameters; roles; named events; phases or steps; rules; required host capabilities; data and visibility requirements; example runs. The precise fields remain open.
2. **Host contract:** identity, durable state, timing, messaging, access enforcement, artifact storage, and ways for a human facilitator to report physical events. It may also need to declare media and timing capabilities, such as whether participants can hear one another with sufficiently low and stable delay for a particular live activity. Hosts may implement these using any language or infrastructure.
3. **Optional extension mechanism:** an answer for behavior that cannot be expressed by the common rules. Possibilities include standardized algorithm primitives, a portable sandboxed runtime, or a separate service interface. None has been chosen.

The activity package should describe *what* a host must do without embedding a particular database schema, queue, or server language. Presentation may vary by host while behavior stays conformant.

## Why code may still appear

Pass the Parcel's basic loop could be described declaratively if the host can receive events such as `music_stopped` and `layer_unwrapped`. A human still determines who physically holds the parcel unless the host has a way to observe or record that fact.

An activity with a novel balancing or assignment algorithm may exceed a fixed set of declarative rules. If its algorithm is written only as a JavaScript callback, a PHP or Rust host cannot execute the same package directly. Adding a universal expression language, sandbox, or remote-code interface would expand the format and its security and compatibility obligations. The research must show which cases justify that burden.

## Tests for the contract experiments

- Express a physical, host-led game such as Pass the Parcel without requiring accounts or stored contributions.
- Express a collaborative passing activity with concealed intermediate work.
- Express an asynchronous recurring prompt with missed-day behavior.
- Express a critique with participant assignments and delayed reveal.
- Have two small, independent host interpreters—or a written interpreter plus conformance fixtures—produce the same transitions for identical event traces.
- State what happens when a host lacks a required capability. An unsupported package should fail clearly rather than silently change the activity's rules.
- Test a live music activity against an ordinary call and, separately, a specialized low-latency setup. The package must not label separately recorded or turn-by-turn singing as the same synchronous experience. [Networked music research](https://onlinelibrary.wiley.com/doi/abs/10.1002/cpe.4730) describes an ensemble performance threshold below roughly 25 milliseconds; [JackTrip](https://support.jacktrip.com/how-to-optimize-latency-when-using-jacktrip) documents the infrastructure constraints. The exact tolerance for the particular activity remains to be established.

## Related standards to examine, not adopt by default

- [JSON Schema](https://json-schema.org/draft/2020-12/json-schema-core) is platform-independent and can validate package structure. It does not define the activity's runtime behavior.
- [W3C SCXML](https://www.w3.org/TR/scxml/) defines event-driven states and transitions. It may inform behavioral semantics, but group roles, human instructions, privacy, and media access still need their own definitions.
- [OMG BPMN](https://www.omg.org/spec/BPMN/2.0.2/PDF/) models processes and collaborations, including executable subsets. Its scope is much larger than many party or classroom activities; it is a comparison point for interoperability costs.

## Open decisions

1. Must every activity be executable by every conforming host, or may packages declare optional capabilities and extensions?
2. What is the smallest shared behavior language that covers the simple activities without becoming a general workflow language?
3. Must hosts present the same participant interface, or only preserve the same rules and results?
4. Are activity instances and their records portable between hosts, or only the definitions?

While these questions remain open, **portable activity package** names the target artifact; **host implementation** names the system that runs it; **module** refers only to host-specific code or an optional executable extension.

## First contract experiment

The [Pass 4 experiment](../experiments/README.md) tests JSON definitions with JavaScript and Python interpreters over contrasting event traces. Its [findings](../experiments/findings.md) show agreement on selected transitions and visibility rules, alongside substantial gaps in human context, event trust, timing quality, and authoring cost. `activity-experiment/0.1` is a research artifact and does not settle the portable package format.

The [named-mechanism follow-up](../experiments/named-mechanisms/README.md) tests more compact definitions for digital handoffs and collections. Its [comparison](../experiments/named-mechanisms/comparison.md) records the smaller packages and the new burden on hosts to implement each mechanism faithfully.

The [offer-flow experiment](../experiments/offer-flows/README.md) tests a proposed two-recipient relay and the constructed [Cover and Response](activities/cover-and-response.md) activity. Its independent interpreters agree on selected race, deadline, allocation, visibility, and restart traces; [findings](../experiments/offer-flows/findings.md) explain why this still does not settle the extension mechanism.

The [composition experiment](../experiments/composition/README.md) replaces activity-specific dispatch with a small operation vocabulary and stage plans, then tests a held-out skip-and-requeue case. Its [findings](../experiments/composition/findings.md) show that assignment policies remain an unresolved portability boundary and that the original two definitions grew in this representation.

The [game-jam and shared-practice research](creative-jams-and-shared-practice.md) identifies two further format tests: optional progress and discussion running alongside a jam's submission/review windows, and daily private work whose visible output may be only a completion mark. These are research questions, not adopted package fields.

The [ongoing-activity experiment](../experiments/ongoing-activities/README.md) runs these two probes in independent JavaScript and Python interpreters. It shows one possible way to retain repeated progress and daily history while projecting private content separately from public status; its [findings](../experiments/ongoing-activities/findings.md) keep the limits of that narrow result explicit.

The [assignment-policy portability experiment](../experiments/policy-portability/README.md) isolates Cover and Response's offer rule, specifies exact integer semantics and an algorithm-version capability, and passes fixtures in JavaScript, Python, and Ruby. The [contract synthesis](contract-synthesis.md) draws provisional conclusions from all of the experiments without declaring a public format.
