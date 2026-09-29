# Candidate 0.7 conformance

Run `python3 format/0.7/check.py` from the repository root. The 26 JSON traces include 22 carried-forward cases and four `guided_rounds@1` cases. The new cases cover solo, pair, and whole-group stages; private, within-group, and after-round visibility; exact deadline transitions; missing contributions; duplicate and changed retries; a second icebreaker package; and explicit unsupported requirements.

The [two-host trial](../../../validation/0.7/README.md) imports all examples and runs these traces through independent local services. It additionally checks worker jumps across multiple rounds, invalid group partitions, concurrent same-person submissions, audience filtering, and restart replay.
