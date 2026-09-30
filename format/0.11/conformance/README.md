# Candidate 0.11 conformance

Run `python3 format/0.11/check.py` from the repository root. The 41 JSON traces contain 38 carried cases and three `permissioned_dialogue@1` cases. The new cases cover the four ordered phases, facilitator-only advancement, maker and responder rights, valid and invalid question links, pending and denied permission, an opinion tied to a specific grant, sparse completion, exact and changed retries, and explicit unsupported behavior.

The [two-host trial](../../../validation/0.11/README.md) runs these traces through independent services. It additionally rejects invalid maker setup and incomplete phase prompts, races two opposing maker decisions for one request, verifies one atomic decision and its effect on the opinion, and checks replay after restart.
