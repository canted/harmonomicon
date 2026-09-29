# Local host validation for candidate 0.1

This trial imports the same [candidate 0.1 example packages](../../format/0.1/examples/) into two separate local HTTP hosts: [Python](python_host.py) and [Node.js](node_host.mjs). They have independent behavior code and separate SQLite databases. The shared inputs are the package JSON files and [conformance cases](../../format/0.1/conformance/README.md).

Run from the repository root:

```sh
python3 validation/0.1/run.py
```

The runner starts each host on `127.0.0.1` with an ephemeral port and a temporary database, then stops it and removes the test data. It needs Python 3 with SQLite and Node.js with `node:sqlite`; it installs no packages. Node's built-in SQLite API is experimental in the tested runtime. The admin-only clock endpoint supplies deterministic test time; the hosts' periodic workers still run as separate processes and commit phase changes without a participant request.

## What the trial checks

- Both hosts load the group check-in and three-person handoff packages without activity-ID branches.
- The [five 0.1 conformance cases](../../format/0.1/conformance/README.md) produce the specified outcomes and participant views in both hosts.
- Bearer tokens select a server-bound actor. Missing or wrong tokens cannot read a view; participant requests cannot supply an actor or trusted timestamp.
- Before reveal, another participant and the organizer cannot read a private contribution through the HTTP view endpoint.
- A worker opens and closes a collection without any participant request; a read also enforces the closing deadline.
- Two simultaneous submissions by one participant produce one accepted commit and one rejection. The accepted event and its request ID survive a process restart; its retry is `replayed`.
- A host refuses to resume a stored instance if the bytes of its package change while the package ID and version remain the same.
- A missing capability or behavior contract returns `unsupported` before instance creation.

The runner compares the two hosts' semantic outputs after asserting the expected results. A passing run establishes agreement for these packages and cases across two local implementations with durable storage, a worker, and an authenticated read boundary. It does not establish support for other behavior contracts or arbitrary third-party packages.

## Limits

The hosts load only the checked-in examples at startup and support text contributions. They do not store image bytes, send notifications, measure real-world delivery latency, moderate content, or migrate a running instance between hosts. The controlled clock tests boundary behavior and worker execution; it does not measure timing accuracy under deployment load. These localhost services are validation harnesses, not public web deployments.
