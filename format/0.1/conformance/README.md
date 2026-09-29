# 0.1 conformance cases

Run `python3 format/0.1/check.py` from the repository root to check the examples and cases with one reference model. This is a consistency check, not a second host implementation.

These JSON cases give a host the same package, instance setup, ordered events, expected outcomes, and semantic participant views. `expect` is a **semantic projection** for comparison; a host may present it with different screens or API field names. An omitted `own`, `input`, or `entries` key means the viewer must not receive that content through the activity view.

- [Read at closing time](collection-read-close.json) checks that a view request closes the collection even without a closing worker tick.
- [Timed collection](collection.json) checks a private answer, an exact retry, a submit at the closing boundary, reveal, and a changed-payload request ID.
- [Sequential handoff](handoff.json) checks turn ownership, predecessor-only input, private views, replay, and final reveal.
- [Unsupported capability](unsupported.json) checks rejection before instance creation when `clock@1` is absent.
- [Unsupported behavior](unsupported-behavior.json) checks rejection when the host lacks the exact behavior contract.

For a supported case, `package` resolves relative to the case file; `instance` binds actors and setup values. Each `event` has an expected `outcome`. A `views` entry is checked immediately after that event. The view's phase and named data should match; unlisted presentation details may differ. The cases use small integer times as synthetic Unix milliseconds to keep the boundary order readable.

A language-independent format needs hosts to agree on these rules, including absence of private values. The cases alone do not prove storage transactions, worker execution, or access control at an HTTP boundary. The [local two-host trial](../../../validation/0.1/README.md) exercises those properties for the two example packages; it does not establish production deployment behavior.
