# Local host validation for candidate 0.9

This trial imports the [0.9 packages](../../format/0.9/examples/) into independent [Python](python_host.py) and [Node.js](node_host.mjs) localhost HTTP hosts. Each has its own SQLite package registry, media store, event transactions, deadline worker, and authenticated actor views. The hosts share packages and [conformance traces](../../format/0.9/conformance/README.md), but no runtime behavior code.

Run from the repository root:

```sh
python3 validation/0.9/run.py
```

The runner creates temporary services and databases. It requires Python 3 with SQLite and Node.js with `node:sqlite`; it installs no packages. The administrator clock and local package-exchange endpoints are validation interfaces described in the [0.4 trial](../0.4/README.md), not a mandated public transport.

Both hosts pass all 35 cases and agree on semantic output. They store real PNG bytes for caption, timed collection, sequential handoff, and repeated collection. Media probes check malformed base64, incorrect type, corrupt or truncated PNG, idempotent upload, actor ownership, private media reads, and retrieval after restart. Earlier worker, concurrency, privacy, replay, package identity, and cross-host package-transfer probes also pass.

The tested image subset is limited to the [0.9 PNG rules](../../format/0.9/README.md#image-reference-contract). The trial does not test voting, other file types, content moderation, public deployment, or migration of a running instance. Package transfer does not carry participant image bytes.
