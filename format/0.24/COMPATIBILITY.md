# Candidate 0.24 compatibility

All 0.23 files remain byte-for-byte retained. Translate only the format envelope to 0.24 for retained definitions; every existing operation version keeps its source, output, timing, identity and privacy meaning. New `first_valid@1` is not silently admitted to historical consumer source families. A canonical accepted item can be bound directly into a later instance through existing qualified contribution inputs.

The new optional `queueInputs` declaration, `first_valid@1`, `policy:rolling_pair@1` and `invitation_queue@1` are explicit negotiation requirements. Unsupported hosts refuse before target state/grants/claims. A package must declare all used media/seed/host/input capabilities. New host creation receipts apply to relay instances; retained instance creation conflicts stay unchanged.

[compatibility_check.py](compatibility_check.py) compares all 108 retained 0.23 traces with both historical engines, including full state and actor views. [check.py](check.py) retains the preceding 73-trace 0.22 comparison, schema and earlier migration evidence. [relay_check.py](relay_check.py) validates the new bounded semantics and a different composition. Durable host verification is recorded in [EVIDENCE](../../validation/0.24/EVIDENCE.md).
