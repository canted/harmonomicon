# Activity package format 0.4 candidate

**Status:** Candidate validated in two independent local hosts for text packages and package transfer. It is not a published standard.

Harmonomicon packages describe digitally mediated group activities as data. A package contains human directions, participation bounds, provenance, exact host requirements, and one behavior contract. A host creates an instance by binding real actors and schedule values to an imported package. The package contains no server code or participant accounts.

Candidate 0.4 adds **package exchange** to the [0.3 package and behavior rules](../0.3/README.md). The four behavior contracts—`timed_collection@1`, `sequential_handoff@1`, `repeated_collection@1`, and `offered_response@1`—retain their 0.3 event, scheduling, retry, audience, and capability semantics. Their contract tokens and policy token have not changed. In 0.4, the `format` field is exactly `harmonomicon.activity-package/0.4`. A package's `version` must change when its canonical content changes, including when its format field changes. The [0.4 schema](package.schema.json) and [examples](examples/) use this identifier and new package versions.

## What exchange means

A host implementing 0.4 provides these transport-independent operations. The [local validation API](../../validation/0.4/README.md) is one mapping to HTTP; apps may use other transports and programming languages.

| Operation | Required result |
|---|---|
| Discover support | Report `format`, sorted `behaviors`, and sorted `capabilities`. The format value is exactly `harmonomicon.activity-package/0.4`; behavior and capability strings are full versioned tokens. Disabled or unavailable support is omitted. |
| Import package | Validate the complete package and persist its canonical JSON and digest under `(id, version)` before returning `imported`. The same canonical package repeated returns `existing` with the same digest. A different package at the same `(id, version)` returns `package_conflict` without changing stored data. Invalid structure or cross-field rules return `invalid_package`. |
| Export package | Given an exact `(id, version)`, return the stored package object and its digest, or `not_found`. The export must be importable by another conforming host. |
| Create instance | Select an exact `(id, version)`, bind actors and setup values, and check the package's required behavior and capabilities. If any are unavailable, return `unsupported` with sorted missing tokens before creating state. Unknown package identity returns `invalid_package`. |

Import authorization is the host's responsibility. The local harness requires an administrator token. Importing a valid package does not assert that the host can run it: a text-only host may store and export an `image_ref@1` package but must refuse an instance until it has that capability. Hosts must not infer support for 0.3 from support for 0.4, or vice versa.

The `(id, version)` pair is immutable. A changed prompt, rights statement, requirement, behavior configuration, or format field requires a new package version. A host may retain several versions of one ID and bind different instances to them. An existing instance stays bound to its original version and digest across restart. This candidate does not migrate a running instance or convert a 0.3 package automatically.

## Canonical package digest

The digest is lowercase hexadecimal SHA-256 of a canonical UTF-8 JSON serialization of the package object. This gives different hosts a concrete way to compare package identity. Canonicalization is defined for the 0.4 schema's JSON subset:

1. Reject an object with unknown or missing schema fields, invalid cross-field combinations, non-Unicode-scalar strings, fractional numbers, or integers outside `0..9007199254740991`. The schema limits integers in participant bounds, steps, intervals, windows, and occurrences; every other numeric package value has the same safe-integer limit. All object property names in this version are fixed ASCII names.
2. Recursively sort object members by their ASCII property names. Keep array order unchanged. Emit no insignificant whitespace.
3. Emit booleans as `true` or `false` and nonnegative integers as ordinary base-ten digits without leading zeroes, except `0`. Emit strings with `"` and `\\` escaped; use `\b`, `\t`, `\n`, `\f`, and `\r` for those five controls, `\u00xx` with lowercase hexadecimal for other characters U+0000 through U+001F, and literal UTF-8 for other Unicode scalar values. Do not escape `/`.
4. Hash the resulting UTF-8 bytes. An imported canonical package larger than 1,000,000 bytes is `invalid_package`.

The digest identifies the complete package, including directions and provenance. It does not certify a package's license, safety, correctness, or behavior on a host. A host must apply the package's audience rules to activity data separately.

## Runtime and conformance

0.4 retains the [0.3 runtime specification](../0.3/README.md#instance-and-event-boundary). Events still use authenticated actors, trusted time, durable IDs, serial ordering, and exact versioned behavior semantics. The [0.4 conformance cases](conformance/README.md) cover the same 15 activity traces using 0.4 packages. The [two-host trial](../../validation/0.4/README.md) imports those packages through the exchange operation, runs all 15 cases in independent Python and Node.js SQLite-backed hosts, and transfers a newly authored package between them. It also checks duplicate import, changed content under one version, multiple versions, capability discovery, unauthorized import, and restart persistence.

Run `python3 format/0.4/check.py` for the reference-model activity cases and `python3 validation/0.4/run.py` for the local two-host trial. This candidate does not establish image storage, media transfer, notification delivery, voting, team/project streams, arbitrary executable rules, production deployment, or migration of an activity in progress.
