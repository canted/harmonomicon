# Local host validation for candidate 0.6

This trial imports the [0.6 examples](../../format/0.6/examples/) into separate [Python](python_host.py) and [Node.js](node_host.mjs) localhost HTTP hosts. Each has independent SQLite storage, event transactions, deadline workers, authenticated actor views, a package registry, and behavior code. They share package data and [conformance traces](../../format/0.6/conformance/README.md), but not runtime behavior code.

Run from the repository root:

```sh
python3 validation/0.6/run.py
```

The runner starts temporary services and databases, then removes them. It needs Python 3 with SQLite and Node.js with `node:sqlite`; it installs no packages. Node's built-in SQLite API is experimental in the tested runtime. The administrator-controlled clock and local exchange endpoints are described in the [0.4 trial](../0.4/README.md); they are a validation interface, not a required app transport.

Both hosts pass all 22 activity cases and agree on their semantic results. The new probes jump over every boundary of a two-prompt series and check the worker log and missed statuses. They concurrently append group entries, check that private entries remain invisible to another participant, and retry an entry after restart without duplicating it. The prior project, offer, collection, handoff, package-transfer, and privacy probes also pass.

The hosts store text contributions only. The image-caption package can be imported but reports `unsupported` for an instance because image storage is absent. This trial does not test local-calendar recurrence, media files, notification delivery, public deployment, or migration of a running instance.
