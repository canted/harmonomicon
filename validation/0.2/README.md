# Local host validation for candidate 0.2

This trial loads the same [0.2 example packages](../../format/0.2/examples/) into separate [Python](python_host.py) and [Node.js](node_host.mjs) localhost HTTP hosts. Each host implements the behavior in its own language and uses its own SQLite database. The shared inputs are the package files and [conformance cases](../../format/0.2/conformance/README.md).

Run from the repository root:

```sh
python3 validation/0.2/run.py
```

The runner starts each host on `127.0.0.1` with an ephemeral port and temporary database, then stops it and removes the test data. It needs Python 3 with SQLite and Node.js with `node:sqlite`; it installs no packages. Node's built-in SQLite API is experimental in the tested runtime. An admin-only endpoint supplies deterministic test time. Each host has a periodic worker that advances deadlines without a participant request.

## What passed

- Both hosts loaded all five text example packages without branches on package ID and matched the expected outcomes and participant views in all nine 0.2 conformance cases.
- The repeated-collection cases covered private entries with group-visible completion status, immediate group sharing, reveal after each window, missing and stale submissions, retained history, and unsupported requirements.
- Workers opened and closed repeated windows without participant requests. A clock jump across both occurrences produced every scheduled boundary in order and left both missed statuses in the retained history.
- Bearer tokens bound read and submit requests to server-side actors. Missing or incorrect tokens could not read a view; a participant could not supply a trusted actor or timestamp or control the test clock.
- Two simultaneous submissions from one participant to one occurrence produced one accepted commit and one rejection. The accepted entry and event ID survived restart; retrying the accepted request returned `replayed` without a second entry.
- Hosts rejected unknown or missing instance setup fields, forbidden prompt overrides, and schedules whose final closing time exceeds the safe integer range.
- A host refused to restart a stored instance when the package content hash no longer matched the same package ID and version.

The runner compares the two hosts' semantic outputs after checking expected results. A passing run establishes agreement for these checked-in packages and cases through local storage, worker, and authenticated-view boundaries. The [0.1 trial](../0.1/README.md) remains a separate result for its earlier package files.

## Limits

These hosts load only the checked-in examples at startup and accept text contributions. They do not load arbitrary third-party packages, validate actual image references or media bytes, send notifications, measure delivery precision under load, moderate content, follow local-calendar days, or migrate a running instance between hosts. The controlled clock tests boundary behavior and worker catch-up, not real-world timing accuracy. These localhost services are validation harnesses, not public web deployments.
