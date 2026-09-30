# Candidate 0.9 conformance

Run `python3 format/0.9/check.py` from the repository root. The 35 JSON traces include 30 carried behavior cases and five image-reference cases. The new cases cover image caption offers and reveal; image collection, sequential handoff, and repeated collection; uploaded-byte digests, uploader ownership, private reads, offered-source reads, group reveal, and malformed upload attempts.

Each image case includes canonical base64 PNG bytes and the SHA-256 reference expected from them. `uploadAttempts` describe uploads that must be rejected; `uploads` establish actor ownership before activity events; `mediaReads` after an event say which actors can read a reference. The [two-host trial](../../../validation/0.9/README.md) performs those operations against independent storage and access boundaries, including restart.
