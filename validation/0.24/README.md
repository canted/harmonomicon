# Candidate 0.24 validation

[Evidence](EVIDENCE.md) records exact new relay and retained compatibility checks. Run the optional schema checks with jsonschema from requirements-validation.txt; runtimes have no schema dependency.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 format/0.24/check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 format/0.24/relay_check.py --schema
PYTHONDONTWRITEBYTECODE=1 python3 format/0.24/compatibility_check.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.24/relay_trial.py
PYTHONDONTWRITEBYTECODE=1 python3 validation/0.24/run.py
```

[Python](python_host.py) and [Node](node_host.mjs) are separate serial SQLite hosts with authenticated actor tokens, controlled trusted test clock/workers, immutable package digests, actual PNG/audio authority and qualified source/input grants. [relay_trial.py](relay_trial.py) adds concurrent first-valid acceptance, portable queue authority/consumption, fresh shared windows, stale tickets, cooldown/null predecessor, exact creation retries, true-origin carry-forward, safe-clock non-resumability and a different private-pair composition. The inherited run checks all retained operations and transfers. No real notifications are sent; loopback services/databases are temporary.

Admin creation may pass hostQueues bindings to closed first_valid records, with actual predecessor hostBindings when non-null. Reauthorize every retained queue and material source before later roster or window configuration expands bound viewers; null canonical does not waive queue-metadata authority. Restored hosts reconnect both callbacks, and denied expansion leaves target state/tokens/grants/claims unchanged. Consume the qualified source UUID/step at most once, atomically with creation/grants/tokens. Exact relay creation retries return the original identity/digest; changed retries conflict. A lost credential response can use trusted existing actor re-binding. See [full contract](../../format/0.24/relay-notes.md).

No merging, publication, deployment, 1.0 or implementation-review clearance is implied by this local validation.
