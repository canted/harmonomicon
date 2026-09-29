# Candidate 0.8 conformance

Run `python3 format/0.8/check.py` from the repository root. The 30 JSON traces contain 26 carried cases and four `competitive_handoff@1` cases. The new traces cover competing offers, first accepted submission, decline and immediate fallback, exact timeout boundaries, terminal stall, private immediate input, final reveal, retry and changed retry, and an explicit unsupported contract.

The [two-host trial](../../../validation/0.8/README.md) imports all examples and runs the traces through independent local services. It additionally checks worker-only time jumps, invalid route setup, concurrent offered submissions, durable replay after restart, and access-filtered views.
