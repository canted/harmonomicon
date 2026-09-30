# Local host validation for candidate 0.10

This trial imports the [0.10 example packages](../../format/0.10/examples/) into independent [Python](python_host.py) and [Node.js](node_host.mjs) localhost HTTP hosts. Each has its own SQLite package registry, media store, event transactions, deadline worker, and authenticated actor views. They share [packages](../../format/0.10/examples/) and [conformance traces](../../format/0.10/conformance/README.md), but no runtime behavior code.

Run from the repository root:

```sh
python3 validation/0.10/run.py
```

The runner creates temporary services and databases. It requires Python 3 with SQLite and Node.js with `node:sqlite`; it installs no packages. The administrator clock and package-exchange endpoints are local validation interfaces described in the [0.4 trial](../0.4/README.md), not a required public transport.

Both hosts pass all 38 cases and agree on semantic output. Voting probes check invalid setup, one atomic accepted vote when two requests from the same actor race, private ballots before completion, replay after restart, worker ticks at source, response, and vote deadlines, and the final tally. Carried image storage, access, worker, concurrency, package identity, and exchange probes also pass.

The trial does not test multi-criterion rankings, external notifications, public deployment, or movement of a running instance between hosts. The image subset remains the [0.9 PNG contract](../../format/0.9/README.md#image-reference-contract).
