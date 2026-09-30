# Activity package inspector

A static browser viewer for candidate 0.17 activity packages. It loads package JSON and renders `runbook.steps` in array order. Nested `steps` are enclosed in containers. Participant and item loops state what repeats; step cards show prompts, actors, field types, options, privacy, sources, and close conditions. Selecting a node shows its operation, JSON location, all settings, and the original step JSON.

There are no activity templates, contract-specific phases, or inferred waiting/completion nodes. Node labels are the declared step IDs. **next** connects siblings in the same array; containers enclose nested bodies. These are structural links, not a runtime trace: repeated participant turns are not expanded, and arrows do not imply extra close conditions, outcomes, or events. Operation semantics remain in the [specification](../format/0.17/operations.md).

The example catalog is generated from every JSON file in `format/0.17/examples/`. New examples require no viewer code changes. Local package files can also be opened without adding them to the catalog. Unknown operation names can be inspected as data; the viewer does not claim to execute them or validate conformance.

## Run locally

From the repository root:

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000/docs/`. The viewer uses the same SVG renderer as the static previews, with no external diagram library. GitHub Pages can serve the same folder; GitHub’s repository file view displays the generated SVG previews but does not run the interactive viewer.

## Refresh examples and previews

```sh
node docs/sync-examples.mjs
node docs/generate-previews.mjs
node --test docs/viewer.test.mjs
```

Synchronization copies source JSON unchanged, generates the catalog from package titles, and removes stale bundled examples. Preview generation uses the same model and layout as the viewer. Tests verify that arbitrary step IDs, operations, ordering, nesting, and settings come from JSON.

Scheduled steps show declared setting references rather than invented dates or resolved prompt values. The setup panel lists the package's declared types and defaults; chosen instance values do not belong to the blueprint.

Rating steps show declared numeric bounds and routing rounds. Aggregation and publication show their exact policies and cutoff settings; the inspector does not generate scores or infer winners.

Window containers show declared count, interval and duration; body collections show completion-status policy. The viewer keeps a single structural body and does not expand occurrences, resolve instance dates or simulate missed-window status.
