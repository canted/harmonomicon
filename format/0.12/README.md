# Harmonomicon activity package format 0.12

**Status:** Candidate specification for the behavior, media, and exchange subset defined here. The checked-in conformance corpus passes in a reference model and two independent local hosts. This status does not certify other hosts or all possible packages.

An activity package is a UTF-8 JSON object that describes the digital steps of one group activity. It contains directions for people, participant bounds, provenance, exact host requirements, and one behavior contract. A **host** is an app that imports the package and runs an **instance** by binding real actors and setup values. Packages contain no server code, accounts, scheduled instance dates, media bytes, or database instructions. Hosts may use any programming language or transport.

This document defines the common package, event, exchange, and version rules. The [behavior contracts](contracts.md) define the ten activity procedures and their audience views. The [image-reference capability](media.md) defines actual PNG storage and access. The [JSON Schema](package.schema.json) checks structure; this document and the contracts define cross-field and runtime rules. [Examples](examples/) and [conformance cases](conformance/README.md) make the rules concrete.

## Package envelope

A package has exactly these top-level fields; unknown or missing fields are invalid.

| Field | Rule |
|---|---|
| `format` | Exactly `harmonomicon.activity-package/0.12`. |
| `id` | Stable lowercase dotted identifier matching the schema, independent of a host or instance. |
| `version` | Three nonnegative decimal components such as `1.0.0`; this identifies a revision of this one package. |
| `content` | Nonempty `language`, `title`, `summary`, `setup`, `prompt`, `participant`, `completion`, and `access` strings. They are human-facing text, not executable rules. |
| `provenance` | `kind` is `original` or `adaptation`; `credit` and `rights` are nonempty. An adaptation also has an HTTP(S) `sourceUrl`. These are declarations, not a license audit. |
| `participants` | Inclusive `min` and `max` counts, each at least two, with `min ≤ max`. The organizer is separate. |
| `requires` | Unique exact capability and policy tokens supported by the host. It must include every token required by the selected behavior and medium. |
| `behavior` | Exactly one of the ten [behavior contracts](contracts.md), with only its defined configuration fields. |

The format defines nonempty text as a nonempty JSON string; hosts do not trim or normalize it for contract decisions. Package fields and behavior configuration must satisfy the schema and the contract's cross-field rules. A structurally or semantically invalid package yields `invalid_package`. A valid package can be imported by a host that cannot run it; creation then yields `unsupported`.

## Exact tokens and host duties

| Capability or policy token | Host obligation |
|---|---|
| `identity@1` | Bind authenticated actor IDs to the organizer and participants; never trust a client-supplied role. |
| `serial_events@1` | Give each instance one authoritative event order, including equal-time events. |
| `durable_state@1` | Commit accepted event IDs, contributions, and resulting state atomically and preserve them across restart. |
| `private_views@1` | Enforce contract audience rules at every read, cache, notification, and media-byte boundary. |
| `clock@1` | Supply trusted integer Unix-millisecond time and reconcile scheduled phases on events and reads. |
| `text@1` | Accept and render nonempty text contributions. |
| `image_ref@1` | Store and authorize the bounded PNG references defined in [media.md](media.md). |
| `policy:balanced_artifacts_exact32@1` | Implement the exact two-source ranking in [`offered_response@1`](contracts.md#offered_response1). |

The behavior tokens are `timed_collection@1`, `sequential_handoff@1`, `repeated_collection@1`, `offered_response@1`, `project_cycle@1`, `ongoing_space@1`, `guided_rounds@1`, `competitive_handoff@1`, `offered_response_vote@1`, and `permissioned_dialogue@1`. The schema enumerates these tokens. Every behavior requires `identity@1`, `serial_events@1`, `durable_state@1`, and `private_views@1`. Additional requirements are exact:

| Behavior | Additional required tokens |
|---|---|
| `timed_collection@1`, `repeated_collection@1` | `clock@1` and the configured medium token: `text@1` or `image_ref@1`. |
| `sequential_handoff@1` | The configured medium token: `text@1` or `image_ref@1`. |
| `offered_response@1`, `offered_response_vote@1` | `clock@1`, `text@1`, `policy:balanced_artifacts_exact32@1`, and `image_ref@1` when the source medium is `image_ref`. |
| `project_cycle@1`, `ongoing_space@1`, `guided_rounds@1`, `competitive_handoff@1`, `permissioned_dialogue@1` | `clock@1` and `text@1`. |

A host compares complete token strings, including `@1`, and never silently substitutes a different behavior or policy. An unknown or unavailable token produces `unsupported` with sorted missing tokens before an instance exists. A missing behavior is reported as `behavior:<contract>`.

## Instances, events, and views

An instance binds one organizer ID and distinct participant IDs within the package bounds, plus the setup values named by its contract. Actor IDs are opaque nonempty strings unless a contract imposes a narrower ID syntax. The organizer is distinct from every participant; `system` is reserved for host-generated `tick` events. The host verifies that the people legitimately belong to the activity. The package cannot determine consent or identity by itself.

An event has exactly `eventId`, `type`, `actor`, `at`, and `payload`. Event IDs are nonempty, case-sensitive strings. The host authenticates `actor` and supplies `at` as trusted integer milliseconds since the Unix epoch in `0..9007199254740991`. Timestamps must be nondecreasing per instance. Equal times use authoritative commit order. An earlier time, unknown actor, unknown type, invalid payload, or forbidden action is `rejected` without a contribution.

The host reconciles time-based phase transitions before checking an event and before returning a view. A rejected event with a valid later trusted time may still advance the phase. Scheduled workers should wake at named boundaries, but delayed workers cannot extend an acceptance window. Time windows are half-open unless a contract says otherwise: the opening instant is included and the closing instant excluded. All accepted event IDs and resulting state survive restart.

Retrying an accepted `eventId` with the same type, actor, and structurally equal JSON payload returns `replayed` without a second effect, even after a deadline. The retry's `at` may differ and still advances time. Changed reuse is `rejected`; rejected requests do not reserve IDs. A contract may define an additional result such as `existing` for a new offer request that returns a saved offer. The general outcomes are `accepted`, `replayed`, and `rejected`. A host may include diagnostic details, but its resulting state and actor-visible views must match the contract. Views are authenticated projections, not a dump of stored state.

## Package exchange and identity

The following operations are transport-independent. The [local HTTP trial](../../validation/0.12/README.md) is one implementation, not a mandated API shape.

| Operation | Required result |
|---|---|
| Discover support | Report the exact `format`, sorted supported `behaviors`, and sorted supported `capabilities`. Omit disabled or unavailable support. |
| Import | Validate and persist the canonical package and digest under `(id, version)` before returning `imported`. Exact duplicate returns `existing` with the same digest; changed content at the same identity returns `package_conflict` without replacing it. Invalid structure or cross-field rules return `invalid_package`. |
| Export | Return the exact stored package object and digest for `(id, version)`, or `not_found`. Another conforming host can import this definition. |
| Create | Select an exact stored `(id, version)`, bind actors and setup, and check behavior and capability support. Missing support returns `unsupported` and sorted missing tokens before state is created; unknown package identity returns `invalid_package`. |

Import authorization is a host responsibility. Import is not a claim that the host can run the package. The `(id, version)` pair is immutable: any changed package field, including `format`, text, provenance, or requirements, needs a new package version. A host may store several versions of one ID. Each instance remains pinned to its exact package version and digest across restart. This specification does not move or migrate a running instance between hosts.

The digest is lowercase hexadecimal SHA-256 of canonical UTF-8 JSON. Before hashing, reject unknown or missing fields, invalid cross-field combinations, non-Unicode-scalar strings, fractional or negative numbers, and integers above `9007199254740991`. Recursively sort object members by their fixed ASCII names; retain array order; emit no whitespace. Emit booleans as `true` or `false`, integers as ordinary base-ten digits, and strings with `"` and `\` escaped. Use `\b`, `\t`, `\n`, `\f`, and `\r` for those five controls, lowercase `\u00xx` for other U+0000–U+001F controls, and literal UTF-8 for other Unicode scalar values. Do not escape `/`. A canonical package over 1,000,000 bytes is `invalid_package`. The digest compares package content; it does not certify rights, safety, or host behavior.

## Versioning and conformance

`format`, package `version`, behavior tokens, and capability tokens have different roles. `format` selects this envelope and exchange specification. The package version identifies an author's immutable revision of one activity. Behavior and capability tokens select exact runtime semantics. Supporting format 0.12 does not imply supporting an earlier candidate format, and supporting a token does not imply supporting a future token. Incompatible behavior or capability semantics require a new token; incompatible package-envelope semantics require a new format identifier. Earlier candidate identifiers remain historical and are not aliases for 0.12.

A host may claim **format 0.12 exchange support** when it validates, imports, exports, digests, discovers support, and pins instances as defined above. It may claim **partial runtime support** only for the exact behavior and capability tokens it advertises and implements; valid packages outside that set must return `unsupported`. A claim of **full Harmonomicon 0.12 local-profile support** means all ten behavior tokens, all eight listed capability/policy tokens, the 41 conformance traces, and the storage, scheduling, concurrency, restart, privacy, image, and cross-host package-transfer probes in [validation/0.12](../../validation/0.12/README.md) pass. A passing local profile is evidence for those cases, not a certification of arbitrary deployments or security. Public notification delivery, deployment, running-instance migration, arbitrary executable rules, other media, and source-specific human or physical acts are outside the profile.

Run `python3 format/0.12/check.py` for the reference model and `python3 validation/0.12/run.py` for the independent-host trial from the repository root. The [coverage audit](../../COVERAGE.md) maps the source activity cards to modeled, partial, and reference-only digital forms; it does not equate a tested rule slice with a complete source practice.
