# Activity package inspector

**[Open the live diagrammer](https://canted.github.io/harmonomicon/)**

A static browser inspector with all 44 candidate 0.24 examples and local file inspection for formats 0.20–0.24. It loads package JSON and renders `runbook.steps` in array order. Nested `steps` are enclosed in containers. Participant and item loops state what repeats; step cards show prompts, actors, field types, options, privacy, sources, and close conditions. Selecting a node shows its operation, JSON location, all settings, and the original step JSON.

There are no activity templates, contract-specific phases, or inferred waiting/completion nodes. Node labels are the declared step IDs. **next** connects siblings in the same array; containers enclose nested bodies. These are structural links, not a runtime trace: repeated participant turns are not expanded, and arrows do not imply extra close conditions, outcomes, or events. Operation semantics remain in the [specification](../format/0.24/operations.md).

The example catalog is generated from every JSON file in `format/0.24/examples/`. New examples require no viewer code changes. Local package files can also be opened without adding them to the catalog. Unknown operation names can be inspected as data; the viewer does not claim to execute them or validate conformance.

## Run locally

From the repository root:

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000/docs/`. The viewer uses the same SVG renderer as the static previews, with no external diagram library. GitHub Pages can serve the same folder; GitHub’s repository file view displays the generated SVG previews but does not run the interactive viewer.

## Refresh examples and previews

```sh
npm --prefix docs run build
npm --prefix docs test
python3 docs/validate-examples.py
```

Synchronization copies source JSON unchanged, generates the catalog from package titles and identities, and removes stale bundled examples. Preview generation uses the same model and layout as the viewer. Tests verify that arbitrary step IDs, operations, ordering, nesting, and settings come from JSON, retained 0.20–0.23 packages remain inspectable, and bundled bytes and previews match the current sources. The separate schema check needs `jsonschema` from `format/0.24/requirements-validation.txt`; it validates catalog packages against the selected format’s actual schema without importing or executing a runtime. Browser file inspection checks structure only and links to the matching schema and operation rules; it does not perform schema or semantic validation.

Scheduled steps show declared setting references rather than invented dates or resolved prompt values. The setup panel lists the package's declared types and defaults; chosen instance values do not belong to the blueprint.

Rating steps show declared numeric bounds and routing rounds. Aggregation and publication show their exact policies and cutoff settings; the inspector does not generate scores or infer winners.

Window containers show declared count, interval and duration; body collections show completion-status policy. The viewer keeps a single structural body and does not expand occurrences, resolve instance dates or simulate missed-window status.

Distribution steps show declared recipient set, exact policy, cardinality, reuse and unmatched handling. Response steps show the saved-source relation. The inspector does not generate randomness, assign recipients, publish results or claim product parity.

Image field summaries show the declared `image_ref` type and visibility. The inspector never invents an upload encoding, ready identity, authorization or byte preview. Those are host profile/runtime facts, not package blueprint facts.

Typed contribution cards show declared kinds/visibility and source relations. Effective actor lists and resolved dates are host instance inputs, so the blueprint reports that boundary without inventing roles, dates, assignments or media encoding.

Contribution and invitation queue declarations remain visible in package details. Step cards distinguish null input, host bindings and preceding result references; voting cards show candidate sources/options, ballot visibility, change rules, tie/no-vote policy and presentation audience. Typed item containers retain their declared order policy. First-valid cards show the declared invitation window and failed-pass retry delay without inventing invitation state, winners or queue members.

These inspector/schema checks do not replace runtime review. Candidate 0.24’s independent queue-audience runtime recheck remains unverified after a platform safeguard stopped it; see the [existing evidence record](../validation/0.24/EVIDENCE.md).

## GitHub Pages

The public site at <https://canted.github.io/harmonomicon/> is served from the `docs/` folder on `main`. Pushes to `main` publish updates automatically. `docs/.nojekyll` keeps the site as plain static files.
