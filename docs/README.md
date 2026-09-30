# Activity package inspector

A static, browser-based first pass at rendering Harmonomicon 0.12 packages. It uses [Cytoscape.js](https://js.cytoscape.org/) for the interactive graph and a small contract-specific model in [`model.js`](model.js) for stage labels and details. No server or account is required. The bundled library is pinned to 3.34.3 under its [MIT license](vendor/LICENSE.cytoscape).

The viewer ships with the two README examples and accepts a local JSON file for any of the ten defined 0.12 behavior contracts. Select a stage in the graph or the accessible stage list to inspect its events, setup, views, and boundaries. The graph can be saved as PNG. The two static SVG previews in [`previews/`](previews/) are generated from the same model for display in the repository README.

## Run locally

From the repository root:

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000/docs/`. The server is needed to fetch the bundled examples; the **Open package JSON** control also accepts files from your computer. Nothing is uploaded to a server by this viewer.

## GitHub display

GitHub renders the checked-in SVG previews in the repository README. Its repository file view does not execute this interactive JavaScript application. To host the interactive viewer from the same repository, publish the `docs/` folder with [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) after the repository has a remote and is pushed. In repository **Settings → Pages**, choose **Deploy from a branch**, the main branch, and `/docs`. This project has not configured or activated Pages.

## Scope

This is a **package blueprint**, not an instance simulator or full schema validator. It shows contract phases and representative allowed actions. The package does not include the real participants, actual deadline values, chosen group partitions, event history, or resulting audience views. Those belong to instance setup and execution. The diagram uses contract-specific templates; unknown formats and behavior tokens fail explicitly. It does not infer extra rules from `content` text. Read the normative [0.12 format](../format/0.12/README.md) and [behavior contracts](../format/0.12/contracts.md) for exact implementation requirements.

The first pass summarizes repeated occurrences and handoff steps as loops or ranges, rather than drawing hundreds of identical nodes. It does not currently accept an instance or event trace. The viewer checks basic identifying fields before drawing but does **not** replace the repository's reference validator.

## Maintain and check

From the repository root:

```sh
node docs/sync-examples.mjs
node docs/generate-previews.mjs
node --test docs/viewer.test.mjs
python3 format/0.12/check.py
```

Run the first two commands when either bundled example or its diagram model changes. The test checks that all twenty example packages produce graphs, the two bundled samples match the normative examples, and the two README flows retain their central visibility and branch rules.
