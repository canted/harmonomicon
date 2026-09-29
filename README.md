# Harmonomicon

Harmonomicon studies the rules that give shape to human group activities and develops a **programming-language-independent activity package** that more than one software host could interpret. The name takes **Harmon-** from Harmonia. Host-specific code may still implement the package or extend difficult cases; the package itself should not require the host's programming language.

The research includes activities that people can run without software. The proposed standard concerns what a mediating app presents, schedules, records, assigns, reveals, and communicates. Physical actions enter that app only through supported inputs or reported events.

## Working scope

An activity is in scope when two or more people participate under explicit instructions, roles, turns, prompts, timing, or other rules that shape their interaction. A person or software may guide it. Activities that need no software are in scope.

Three levels are recorded separately:

- **Occasion:** a dinner party, birthday party, kindergarten session, workshop, or ongoing group. An occasion may contain several activities.
- **Activity:** a runnable set of rules, such as Pass the Parcel, a conversation round, or a collaborative drawing exchange.
- **Mechanism:** a reusable part of an activity, such as passing an object, rotating partners, assigning a prompt, waiting for a timer, or revealing a result.

A recurring individual prompt belongs in the survey when a group relationship changes the activity—for example through shared viewing, responses, accountability, or aggregation.

## Research passes

1. **Observation format:** define a compact card that captures the complete runnable procedure, variants, source evidence, and possible software role. Calibrate it on a simple activity.
2. **Breadth survey:** collect examples across social hosting, celebrations, early-childhood activities, conversation, creation, feedback, collective thinking, games, rituals, and other families discovered along the way. Sample across live/asynchronous and in-person/remote settings.
3. **Mechanism survey:** compare the algorithms across cards. Identify repeated mechanisms and important counterexamples, including what happens when people arrive late, miss a turn, decline, or contribute too little.
4. **Contract experiments:** express unlike activities using a candidate portable package and host contract. Try more than one host implementation where possible. Revise the contract where the examples expose a real mismatch.

The initial card is an observation tool, not the future plugin schema. An activity may need only a host cue sheet; another may need software to assign work, preserve private contributions, or schedule a reveal.

The portability goal and its open design questions are recorded in [Portable activity packages](research/portable-activity-packages.md).

## Pass 1 artifacts

- [Activity card template](research/activity-card-template.md)
- [Pass the Parcel calibration card](research/activities/pass-the-parcel.md)

## Pass 2 working map

- [Breadth survey](research/breadth-survey.md): source-backed candidate activities, grouped by the kind of interaction they structure. This is a sampling map for deciding which algorithms to document in depth, not a complete inventory.

## Pass 3 mechanism survey

- [Mechanism survey](research/mechanism-survey.md): compact algorithms for eleven source-backed cards, repeated mechanisms, exception gaps, and boundary findings for a portable format.
- [Activity cards](research/activities/): full procedures and evidence for the contrasting examples, including physical, social, creative, care, and digital activities.

## Pass 4 contract experiment

- [Experimental contract and conformance cases](experiments/README.md): JSON activity definitions interpreted independently by JavaScript and Python, with expected event traces and capability checks.
- [Findings](experiments/findings.md): what the traces establish, choices made only for the experiment, and gaps before a public standard.
- [Named-mechanism comparison](experiments/named-mechanisms/README.md): smaller app-defined handoff and collection patterns tested in JavaScript and Python, including a digital Parcel experiment.
- [Offer-flow experiment](experiments/offer-flows/README.md): two-recipient relay and [Cover and Response](research/activities/cover-and-response.md), tested for race order, fallback, allocation, visibility, and cross-language process restart.
- [Composition experiment](experiments/composition/README.md): stage plans using shared operations for the relay, Cover and Response, and a held-out Drawception skip-and-requeue case; the [findings](experiments/composition/findings.md) compare definition and interpreter costs.
- [Creative-practice experiment revisit](experiments/creative-practice-revisit/README.md): runs the existing interpreters against privacy, daily-history, and repeated-progress diagnostic traces from the newer game-jam and journaling survey.
- [Ongoing-activity experiment](experiments/ongoing-activities/README.md): tests a proposed mediated jam session and contrasting private/public daily practice with independent JavaScript and Python interpreters.
- [Assignment-policy portability experiment](experiments/policy-portability/README.md): specifies one versioned offer algorithm and checks large IDs, ties, replay, unsupported versions, and restart in JavaScript, Python, and Ruby.
- [Contract synthesis](research/contract-synthesis.md): provisional direction for a first package envelope and the remaining host-level validation gate.

## Focused digital research extension

- [Digital activity stress cases](research/digital-activity-stress-cases.md): Drawception's asynchronous recovery, Moodle Workshop's phases and allocations, Board Game Arena's automated auction, and a clearly marked proposed two-recipient relay.
- [Game jams, group journaling, and parallel creative practice](research/creative-jams-and-shared-practice.md): source-backed game-jam and daily-practice variants, including Jamuary, with ten compact activity cards and a comparison to current protocol experiments.

## Evidence rules

- Link to the source of each documented rule. Prefer instructions from people or organizations that actually run or publish the activity.
- Separate documented rules, observed variants, and proposed software interpretations.
- Record missing rules as open questions; do not silently invent a canonical version.
- Paraphrase source material and keep enough detail to run the activity.
