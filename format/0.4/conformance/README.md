# Candidate 0.4 conformance

The 15 JSON traces in this directory carry forward the four exact behavior contracts from 0.3 with 0.4 package identifiers and versions. Run `python3 format/0.4/check.py` to compare their expected outcomes and audience views with the reference model.

The [local two-host trial](../../../validation/0.4/README.md) imports every example package through each host's package exchange operation, then runs the same traces through independent Python and Node.js services. Its package exchange probes also exercise capability discovery, new package transfer, immutable `(id, version)` identity, rejection of invalid packages, two versions of one ID, authenticated import, and restart persistence. These exchange probes are host tests in `validation/0.4/run.py`; they are not event-trace JSON because exchange occurs before an activity instance exists.
