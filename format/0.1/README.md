# Activity package format 0.1 candidate

**Status:** Candidate tested in two independent local hosts, not a published interoperability standard. This document defines the behavior of the two contracts below. The [JSON Schema](package.schema.json) checks package structure; this document defines runtime meaning. [Examples](examples/) and [conformance cases](conformance/README.md) accompany the draft.

## What a package is

A package is one UTF-8 JSON object that describes an app-mediated group activity. It contains human directions, participation bounds, provenance, required host capabilities, and one versioned behavior contract. It contains no participant accounts, scheduled instance dates, media files, server code, or database instructions. A host may implement it in any programming language.

A host creates an **instance** by binding real participant IDs and the contract's required setup values to a package. Two hosts can run the same package when they implement its exact behavior contract and capabilities. The package version identifies an author's revision; the `format` value identifies this document's package shape. The `(id, version)` pair is immutable: changed package content requires a new version. Neither implies support for other behavior versions.

The handoff and collection contracts build on the [named-mechanism experiment](../../experiments/named-mechanisms/contract.md), while this candidate gives them a new package envelope and exact host obligations. Its JSON is not interchangeable with the experiment definitions.

0.1 has one behavior contract per package. It supports `timed_collection@1` and `sequential_handoff@1`. A host must reject an unknown contract rather than guess at its meaning. Composition, voting, recurring schedules, assignment policies, general parameter definitions, package variants, executable extensions, and transfer of running instances are outside this candidate.

## Package fields

| Field | Meaning |
|---|---|
| `format` | Exactly `harmonomicon.activity-package/0.1`. |
| `id` | Stable dot-separated package identifier, independent of a host or instance. |
| `version` | Three nonnegative decimal components, such as `0.1.0`. A changed package is a new version. |
| `content` | A `language` identifier for this package's single language of human-facing text, plain-text `title`, `summary`, `setup`, `prompt`, `participant`, and `completion` directions, and an `access` note on participation requirements or accommodations. The host presents these to people according to the activity; it does not treat them as executable rules. |
| `provenance` | `kind` (`original` or `adaptation`), `credit`, `rights`, and optional `sourceUrl`. These describe the package's source and permission basis; they do not verify it. |
| `participants` | Inclusive `min` and `max` participant counts. An organizer is separate from participants. |
| `requires` | Unique, exact host capability tokens. The host checks these before creating an instance. |
| `behavior` | One recognized contract and its configuration. |

Unknown package fields and unknown behavior configuration fields are invalid in 0.1. Plain-text directions are portable content; hosts may lay them out differently. The JSON Schema checks types and enumerated values. It cannot prove that a host obeys privacy, scheduling, durability, or the behavior contract.

### Capabilities

| Token | Host obligation |
|---|---|
| `identity@1` | Bind authenticated actor IDs to `organizer` and `participant` roles; do not trust a client-supplied role. |
| `serial_events@1` | Give every instance one authoritative event order, including a stable order for equal timestamps. |
| `durable_state@1` | Commit an accepted event ID, its contribution, and resulting state atomically and retain them across restart. |
| `private_views@1` | Enforce the contract's audience rules at every read/API boundary, including cached and notified content. |
| `clock@1` | Supply trusted server-side time in integer Unix milliseconds and evaluate scheduled boundaries on reads and events. |
| `text@1` | Accept and render nonempty text contributions. |
| `image_ref@1` | Accept an opaque reference to an image stored and access-controlled by the host. The reference is not a portable image file. |

Both contracts require `identity@1`, `serial_events@1`, `durable_state@1`, and `private_views@1`, plus the token matching their `medium`. `timed_collection@1` also requires `clock@1`. A host missing a required capability or the exact behavior contract returns `unsupported` with sorted missing tokens before creating an instance. A missing behavior is reported as `behavior:<contract>`. Advertising a token is a claim, not certification; the [conformance cases](conformance/README.md) and later host integration test the claim.

## Instance and event boundary

An instance binds one organizer ID, distinct participant IDs within the package bounds, and any setup required by its behavior. Actor IDs are opaque nonempty strings. A host verifies that the configured actors consent or otherwise legitimately belong to the activity; the package cannot determine this.

All events have `eventId`, `type`, `actor`, `at`, and `payload`. IDs are nonempty, case-sensitive strings. `at` is trusted host time in the safe integer range `0` through `9007199254740991`, measured in milliseconds since the Unix epoch. Events are processed in authoritative order, and their timestamps must be nondecreasing. An event with an earlier timestamp is rejected without applying its operation. Equal timestamps are resolved by event order. `system` is a reserved actor ID used only for host-generated `tick` events. Other actors are bound at instance creation.

Before checking an event, the host advances any time-based phase to the event's `at`. It also advances phases before answering a view request using current trusted time. Thus a late `submit` cannot keep a collection open when a scheduled worker is delayed. A rejected event never adds a contribution, but its trusted time can still advance the phase. The host should schedule ticks at named boundaries so participants see changes promptly; late delivery may delay a notification but cannot extend an acceptance window.

Accepted event IDs are durable. Retrying an accepted `eventId` with the same `type`, `actor`, and structurally equal JSON `payload` returns `replayed` and makes no second contribution, even after a deadline. Reusing it with different values is `rejected`. `at` may differ on a retry; it still advances the time-based phase. Unknown actors, event types, invalid payloads, and invalid actions are `rejected`. The outcome vocabulary is `accepted`, `replayed`, or `rejected`. A host may provide more detail, but these statuses and resulting participant-visible behavior must agree.

A `text` value is a nonempty JSON string; hosts do not trim or normalize it for contract decisions. An `image_ref` value is a nonempty opaque string whose existence and access the host verifies. No package may instruct a host to fetch or execute code from an arbitrary URL. Media bytes, delivery, moderation, accessibility, and text layout remain host responsibilities.

## `timed_collection@1`

The package's `behavior` is `{ "contract": "timed_collection@1", "medium": "text" | "image_ref", "allowPromptOverride": boolean }`. The host supplies `opensAt` and `closesAt` at instance creation, with `opensAt < closesAt`; both are trusted integer Unix milliseconds. Creation must occur no later than `opensAt`. If `allowPromptOverride` is true, the organizer may set a nonempty prompt at creation; otherwise the package's `content.prompt` is used.

The phases are `waiting` before `opensAt`, `open` in `[opensAt, closesAt)`, and `closed` at or after `closesAt`. A participant's first valid `submit` during `open` stores `{actor, value}`. Its payload is `{ "value": ... }`, with the value matching `medium`. A second submission by the same participant is rejected unless it is a replay of the first accepted event ID. `tick` from `system` has an empty payload, may advance the phase, and is accepted even if it changes nothing. The collection closes at `closesAt` regardless of missing submissions. Missing participants contribute no entry.

Before close, every participant and the organizer may see the phase and submission count. A participant may also see their own entry. No one receives another person's entry through the activity view, including the organizer. After close, all bound participants and the organizer may see the ordered entries; their order is the order of accepted submissions. The host may store private data internally but must enforce this projection at its read boundaries.

## `sequential_handoff@1`

The package's `behavior` is `{ "contract": "sequential_handoff@1", "medium": "text" | "image_ref", "steps": integer, "allowPromptOverride": boolean }`. `steps` is at least two and equals both `participants.min` and `participants.max`. At instance creation the host supplies `route`: every participant ID exactly once, in a chosen order, with length `steps`. The first route member is current. The prompt override rule is the same as above.

The phase starts `active`. A valid `submit` from the current participant stores their `{actor, value}` and advances to the next route member. Its payload is `{ "value": ... }`, matching `medium`. Other actors' submissions are rejected. After the final accepted submission, the phase is `complete`, the current actor is null, and no further contribution is accepted.

Before completion, everyone may see the phase, current actor, and one-based step number. A participant may see their own accepted entry. Only the current actor sees the immediate predecessor's value as input; the first actor instead sees the prompt. The organizer sees no entry content before completion. The package prompt is public content, so this contract does not claim that the first input is secret. On completion, all bound participants and the organizer may see the full ordered chain. This contract has no timeout, skip, replacement, or reassignment rule: an unfinished handoff waits for its current actor. A package needing recovery must use a later contract with defined recovery semantics.

## Versioning and validation

Hosts compare the full contract token, including `@1`; they never silently substitute a different version. The package schema is [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12) and checks structure only. Cross-field checks—such as required capabilities and `steps` matching participant bounds—and runtime behavior are defined here and exercised by the [examples and conformance cases](conformance/README.md). A package that fails structural or cross-field validation is `invalid_package`, distinct from a valid package whose requirements are `unsupported` by a host.

Run `python3 format/0.1/check.py` from the repository root for a single reference-model consistency check. The [local host validation](../../validation/0.1/README.md) imports the same examples into independent Python and Node.js HTTP hosts with separate SQLite state, scheduled workers, and participant-facing access control. The five conformance cases and additional concurrency, restart, and worker probes pass in both. This does not establish support for other behaviors or production deployment. Its scope follows the [contract synthesis](../../research/contract-synthesis.md): package portability first, with running-instance migration and a universal composition grammar deferred.
