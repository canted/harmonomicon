# Local host validation for candidate 0.8

This trial imports the [0.8 example packages](../../format/0.8/examples/) into separate [Python](python_host.py) and [Node.js](node_host.mjs) localhost HTTP hosts. Each has its own SQLite store, event transactions, deadline worker, authenticated actor views, package registry, and behavior implementation. They share package data and [conformance traces](../../format/0.8/conformance/README.md), but no runtime behavior code.

Run from the repository root:

```sh
python3 validation/0.8/run.py
```

The runner starts temporary services and databases and then removes them. It needs Python 3 with SQLite and Node.js with `node:sqlite`; it installs no packages. The administrator-controlled clock and local exchange endpoints are described in the [0.4 trial](../0.4/README.md); they are a validation interface, not a required app transport.

Both hosts pass all 30 activity cases and agree on semantic output. Competitive-handoff probes check a worker-only jump through both attempt deadlines, reject invalid route setup, commit exactly one of two concurrent offered submissions, preserve replay after restart, and enforce offer privacy. Prior collection, handoff, recurrence, offer, project, ongoing-space, guided-rounds, package identity, and exchange probes also pass.

These hosts store text contributions only. The image-caption package can be imported but reports `unsupported` for an instance because image storage is absent. This trial does not test an open assignment queue, image media, notifications, public deployment, or migration of a running instance.
