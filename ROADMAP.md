# Format roadmap

Harmonomicon has candidate format versions, not a published standard. This roadmap records what each candidate defines, what has been tested, and what evidence is needed to advance it. Version numbers beyond 0.4 are provisional; a later candidate gets its number when its scope is settled.

## Three different versions

- The package's `format` value (for example, `harmonomicon.activity-package/0.2`) selects the shape and rules of the format candidate.
- A package's `version` (for example, `0.2.0`) identifies a revision of that particular activity package. Changing its bytes requires a new package version; it does not change the format for every package.
- A behavior token (for example, `repeated_collection@1`) identifies exact runtime semantics. A host must implement that token as specified or report it as unsupported. A future change to those semantics needs a new behavior token, not a silent change under `@1`.

A host must explicitly support the format and every behavior and capability a package requires. Support for a newer format does not by itself imply support for an older one. These distinctions follow the [package identity, contract, and capability rules](format/0.2/README.md).

## Candidate ledger

| Candidate | Defined scope | Evidence now | Advancement gate |
|---|---|---|---|
| [0.1](format/0.1/README.md) | Package envelope; one timed collection or sequential handoff; event order, replay, deadlines, and audience views. | Five reference cases and a [two-host localhost trial](validation/0.1/README.md) using independent Python and Node.js services with separate SQLite stores, workers, and authenticated views. | Met for the two text example packages and their cases. This is local validation of a narrow draft, not publication or proof for arbitrary packages. |
| [0.2](format/0.2/README.md) | Carries forward the two 0.1 behaviors and adds fixed-interval `repeated_collection@1` with retained occurrence history, group-visible completion status, and three content visibility modes. | Nine [reference cases](format/0.2/conformance/README.md) and the [two-host localhost trial](validation/0.2/README.md) pass for the text examples, including repeated-window workers, durable history, authenticated views, concurrency, and restart. | Met for the five checked-in text packages and their nine cases. Arbitrary package import, actual image storage, notifications, local-calendar scheduling, and deployment remain outside this result. |
| [0.3](format/0.3/README.md) | Carries forward the three 0.2 behaviors and adds `offered_response@1`: timed source collection, two saved offers chosen by `policy:balanced_artifacts_exact32@1`, linked text responses, and reveal. Voting is outside this slice. | Fifteen [reference cases](format/0.3/conformance/README.md) and a [two-host localhost trial](validation/0.3/README.md) pass for checked-in text packages, including large-ID ties, atomic offers and responses, privacy, workers, and restart. The [design notes](format/0.3/design-notes.md) compare the named contract with earlier composition evidence. | Met for the checked-in text packages and cases. The image-caption package correctly reports `unsupported` in the text-only hosts. Arbitrary package import, actual image storage, voting, and deployment remain outside this result. |
| [0.4](format/0.4/README.md) | Carries forward the four behavior contracts and adds package exchange: capability discovery, validated import, exact `(id, version)` identity, digest, export, and instance binding to one stored version. | Fifteen [reference cases](format/0.4/conformance/README.md) pass. In the [two-host trial](validation/0.4/README.md), both hosts import the text examples, pass the activity cases and existing runtime probes, and transfer and run a newly authored package across Python and Node.js, including immutable versions and restart. | Met for the specified JSON subset and local hosts. The image package can be imported but cannot run on text-only hosts. Media storage, voting, team streams, delivery, and public deployment remain outside this result. |

Package exchange and four activity contracts are now defined and locally validated for text. The caption-contest example in the [README](README.md#a-richer-example-image-caption-contest) still needs image media support, voting, and result rules. No version is assigned to that later work until its scope and conformance tests are chosen.

## Next candidate: project cycle

The next candidate is provisionally 0.5. The [game-jam and shared-practice survey](research/creative-jams-and-shared-practice.md) and [ongoing-activity experiment](experiments/ongoing-activities/findings.md) identify a gap that the four current contracts cannot express: a work period can contain several progress posts and comments while teams also prepare one final submission for a later review window. The proposed `project_cycle@1` contract will bind fixed teams at instance creation, preserve separate team-only and group-visible progress streams, accept one final entry per team by a deadline, collect text reviews of other teams in a later window, and reveal those reviews at completion. Each action will have exact event, retry, deadline, and audience rules. Team formation, changing membership, media files, ratings, and a winner are outside this slice.

The 0.5 gate is a schema and package example for a digital creative jam, conformance traces for privacy, concurrent posting, final submission, review eligibility, missed deadlines, restart, and unsupported capability handling, followed by two independent hosts passing the same traces through storage and authenticated views. The package exchange rules from 0.4 remain in force. A contract with fewer rules will be chosen if the full slice cannot be specified and validated without creating activity-specific exceptions.

The [mechanism survey](research/mechanism-survey.md) and [digital stress cases](research/digital-activity-stress-cases.md) still leave other digital patterns to assess after this slice: facilitator-controlled phase and group changes, opt-in or permissioned contribution, stalled turn recovery, image media, and selection or voting. The 1.0 scope will be decided by a coverage audit of these mechanisms and the source-backed activity cards, then by the publication gates below. It will not be set by reaching a particular 0.x number.

## Advancement rule for a candidate

A candidate is **defined** when its normative document, machine-readable schema, example packages, and conformance cases agree on inputs, outcomes, boundaries, and participant views. It is **reference checked** when those cases pass a reference model and invalid cross-field combinations are rejected. It is **two-host validated** when independent implementations load the same packages and produce the specified outcomes through real storage, scheduling, and access boundaries. Localhost services are sufficient for that gate; public web deployment is a separate operational test.

Each new behavior must state its exact token, required host capabilities, trusted inputs, event and retry semantics, deadline or ordering rules, views for each audience, and unsupported response. A candidate must record what it does not cover. When evidence exposes a mismatch, revise the unpublished candidate with new cases; after a version is published, incompatible semantics require a new version or token.

## Toward 1.0

A 1.0 release is a publication gate, not a promise to model every group activity. Before it, the selected behavior set needs a stable package format, a way for hosts to report supported format/behavior/capability versions, conformance cases for every required behavior, and at least two independent hosts passing those cases at their storage and access boundaries. The publication also needs explicit rules for package-version changes, backward compatibility, and what a conformance claim means. Running-instance migration, general code execution in packages, every media type, and public hosting are separate capabilities unless deliberately included and tested.

The [research synthesis](research/contract-synthesis.md) explains why the project is advancing with precise behavior contracts and host evidence rather than treating one experimental JSON shape as a universal activity language.
