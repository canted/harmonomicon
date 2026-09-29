# Local host validation for candidate 0.4

This trial imports the [0.4 example packages](../../format/0.4/examples/) through separate [Python](python_host.py) and [Node.js](node_host.mjs) localhost HTTP hosts. Each host has its own SQLite database, deadline worker, actor authentication, package registry, and behavior implementation. They share package JSON and [conformance cases](../../format/0.4/conformance/README.md), but no runtime behavior code.

Run from the repository root:

```sh
python3 validation/0.4/run.py
```

The runner starts each host on `127.0.0.1` with an ephemeral port and temporary database. It needs Python 3 with SQLite and Node.js with `node:sqlite`; it installs no packages. Node's built-in SQLite API is experimental in the tested runtime. The test clock is available only through an administrator endpoint.

The local API maps 0.4 exchange operations to `GET /capabilities`, `POST /admin/packages/import` with `{ "package": ... }`, and `GET /packages/{id}/{version}`. Instance creation through `POST /admin/instances` requires both `packageId` and `packageVersion`. These paths are a validation interface, not a required application transport.

Both hosts pass all 15 activity cases plus worker, concurrent-submission, privacy, replay, and restart probes from 0.3. Each imports examples instead of loading them as code-bundled packages. A newly authored text package is imported into the Python host, exported, imported into the Node host, run, and resumed after restart. The runner also checks the capability manifest, unauthorized import, exact re-import, changed content under an existing version, invalid behavior, and coexistence of two versions. Matching digests show agreement for the checked packages.

The hosts still implement text contribution storage only. They can import the valid image-caption example but report `unsupported` when asked to run it. The trial does not test actual image storage, media transfer, notifications, public deployment, migration of an active instance, or packages outside the supported 0.4 behavior set.
