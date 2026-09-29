# Candidate 0.6 conformance

Run `python3 format/0.6/check.py` from the repository root. The 22 JSON traces include the 18 carried-forward activity cases and four `ongoing_space@1` cases:

- An unscheduled notebook with private and group entries, group comments, rejected private comments, deadline closure, and retry.
- A soft fixed prompt series with distinct per-occurrence prompts, rejected wrong occurrence, conversation during a gap, and no completion statuses.
- Private prompt entries that change group-visible completion status without exposing text, including missed status after close.
- Explicit unsupported behavior and capability reporting.

The [two-host trial](../../../validation/0.6/README.md) imports these packages and runs the traces through independent local services, plus deadline-jump, concurrency, privacy, restart, and exchange probes.
