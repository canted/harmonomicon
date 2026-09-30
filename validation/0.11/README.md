# Local host validation for candidate 0.11

This trial imports the [0.11 packages](../../format/0.11/examples/) into independent [Python](python_host.py) and [Node.js](node_host.mjs) localhost HTTP hosts. Each has its own SQLite package registry, media store, event transactions, deadline worker, and authenticated actor views. They share package data and [conformance traces](../../format/0.11/conformance/README.md), but no runtime behavior code.

Run from the repository root:

```sh
python3 validation/0.11/run.py
```

The runner creates temporary services and databases. It requires Python 3 with SQLite and Node.js with `node:sqlite`; it installs no packages. The administrator clock and package exchange endpoints are local validation interfaces described in the [0.4 trial](../0.4/README.md), not required public transport.

Both hosts pass all 41 cases and agree on semantic output. Dialogue probes reject malformed packages and invalid maker binding, commit one of two competing decisions for the same request, preserve that decision across restart, and allow an opinion only when its particular request was granted. Carried voting, PNG storage, workers, concurrency, replay, privacy, package identity, and transfer probes also pass.

The trial does not test human judgment of questions or feedback, live speaking, Moodle grading, public deployment, or movement of a running instance between hosts.
