# Local host validation for candidate 0.3

This trial loads the same [0.3 example packages](../../format/0.3/examples/) into separate [Python](python_host.py) and [Node.js](node_host.mjs) localhost HTTP hosts. Each host implements the rules in its own language and keeps an independent SQLite database. They share package JSON and [conformance cases](../../format/0.3/conformance/README.md), but no behavior code.

Run from the repository root:

```sh
python3 validation/0.3/run.py
```

The runner starts each host on `127.0.0.1` with an ephemeral port and temporary database, then stops it and removes the test data. It needs Python 3 with SQLite and Node.js with `node:sqlite`; it installs no packages. Node's built-in SQLite API is experimental in the tested runtime. An admin-only endpoint supplies deterministic test time. Each host runs its own periodic deadline worker.

## What passed

- Both hosts matched all 15 candidate conformance cases: nine carried-forward cases and six for `offered_response@1`, including a large-ID assignment tie and explicit rejection of unsupported policy and image requirements.
- The text source package ran without a package-ID branch. At the source deadline, the source pool became fixed; requests saved ordered pairs selected by the exact policy. A second request ID for the same actor returned `existing` without changing the offer.
- Simultaneous offer requests from one actor produced one `accepted` and one `existing` result. Both request IDs survived restart and replayed without reallocating the offer. Simultaneous response attempts from one actor produced one accepted linked response and one rejection.
- Before completion, authenticated views exposed only each participant's own source, offer, and response; the organizer saw counts. The final deadline revealed all accepted sources and responses to bound actors.
- Workers opened and closed stages without a participant request. A jump from source collection to final completion processed both elapsed deadlines in order. Too few sources ended the activity at the source deadline.
- Hosts rejected invalid numeric actor and round IDs, invalid stage times, client-supplied actor/time fields, missing authentication, and changed package bytes under the same package ID and version.

The runner compares the hosts' semantic outputs after checking expected results. A passing run establishes agreement for these checked-in text packages and cases through local storage, worker, concurrency, and access boundaries.

## Limits

The hosts load only checked-in examples at startup and accept text sources and responses. They correctly reject the image-caption example because they do not provide `image_ref@1`. They do not store image bytes, load arbitrary third-party packages, send notifications, moderate content, measure delivery under load, provide voting, or migrate a running instance between hosts. The controlled clock checks ordering and boundaries, not deployment timing accuracy. These localhost services are validation harnesses, not public web deployments.
