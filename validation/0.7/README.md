# Local host validation for candidate 0.7

This trial imports the [0.7 example packages](../../format/0.7/examples/) into separate [Python](python_host.py) and [Node.js](node_host.mjs) localhost HTTP hosts. Each has independent SQLite storage, event transactions, deadline workers, authenticated actor views, a package registry, and behavior code. They share package data and [conformance traces](../../format/0.7/conformance/README.md), but not runtime behavior code.

Run from the repository root:

```sh
python3 validation/0.7/run.py
```

The runner starts temporary services and databases, then removes them. It needs Python 3 with SQLite and Node.js with `node:sqlite`; it installs no packages. Node's built-in SQLite API is experimental in the tested runtime. The administrator-controlled clock and local exchange endpoints are described in the [0.4 trial](../0.4/README.md); they are a validation interface, not a required app transport.

Both hosts pass all 26 activity cases and agree on semantic output. The guided-round probes check every timed boundary after a clock jump, reject an invalid participant partition, accept only one of two concurrent submissions from the same actor in a round, preserve replay after restart, and enforce pair-specific views. Prior collection, handoff, offer, project, ongoing-space, exchange, privacy, and worker probes also pass.

The hosts store text contributions only. The image-caption package can be imported but reports `unsupported` for an instance because image storage is absent. This trial does not test live conversation quality, facilitator judgments, manual early advancement, media files, public deployment, or migration of a running instance.
