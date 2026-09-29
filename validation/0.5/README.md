# Local host validation for candidate 0.5

This trial imports the [0.5 example packages](../../format/0.5/examples/) into separate [Python](python_host.py) and [Node.js](node_host.mjs) localhost HTTP services. Each host has independent SQLite storage, an event transaction boundary, a deadline worker, actor authentication, package registry, and behavior code. They share package data and [conformance traces](../../format/0.5/conformance/README.md), but not runtime behavior code.

Run from the repository root:

```sh
python3 validation/0.5/run.py
```

The runner starts temporary services and databases, then stops and removes them. It needs Python 3 with SQLite and Node.js with `node:sqlite`; it installs no packages. Node's built-in SQLite API is experimental in the tested runtime. The local HTTP endpoints and administrator-controlled test clock are described in the [0.4 validation guide](../0.4/README.md); they are not a required app transport.

Both hosts pass all 18 activity cases and agree on their semantic outputs. The project probes check automatic work/review/completion boundaries, valid team partitions, one atomic final from concurrent teammates, concealed final content before review, late progress rejection, and replay after restart. The trial also carries forward the 0.4 package-transfer, immutable-version, capability, privacy, offer-race, and worker probes.

The hosts handle text contributions only. The image-caption package can be imported but reports `unsupported` for an instance because image storage is absent. The trial does not establish team formation, media storage, ratings, public deployment, message delivery, or migration of a running instance.
