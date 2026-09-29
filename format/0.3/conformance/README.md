# 0.3 conformance cases

Run `python3 format/0.3/check.py` from the repository root for a reference-model consistency check. The [two-host trial](../../../validation/0.3/README.md) runs these same cases through independent local HTTP services with durable storage and authenticated views.

A case supplies a package, instance setup, ordered events, expected outcomes, and semantic participant views. An absent `ownSource`, `offer`, `ownResponse`, `sources`, or `responses` key means that actor must not receive that content through the activity view. Hosts may use different screens or API field names while preserving these results.

The nine carried-forward 0.2 cases cover single collection, sequential handoff, and repeated collection without changing those behavior rules. Their package files use the 0.3 envelope and new package versions.

The six new cases cover:

- [Staged offer and response](offered-response.json): source collection, exact first and second offers, replay and `existing`, a linked response, wrong-source rejection, pre-reveal privacy, and the final reveal.
- [Too few sources](offered-insufficient.json): terminal state at the source deadline without group reveal or later offers.
- [Large numeric IDs](offered-large-ids.json): a score tie involving IDs above `2^53`, numeric-ID tie breaking, and the unsigned 64-bit boundary.
- [Missing policy](offered-unsupported-policy.json): rejection before instance creation when the exact assignment policy is unavailable.
- [Missing behavior](offered-unsupported-behavior.json): rejection before instance creation when the exact staged behavior is unavailable.
- [Missing image support](offered-unsupported-image.json): rejection of the image-caption package by a text-only host.

The text-source case checks assignment and linked responses without testing image storage. The image-caption example is structurally defined but needs a host with `image_ref@1` to run. These cases do not specify voting or winner selection.
