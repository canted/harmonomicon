# Typed image contributions and host boundary

Candidate 0.24 retains the `image_ref` fields introduced by 0.19 to `collect@1`, `collect_until@1` and `collect_window@1`, gated by `image_contributions@1`. Existing operation meanings, text values and prior package revisions remain intact. Retained `collect_group@1`, `pool@1`, `route@1` and `respond@1` remain text-only; separate typed pools/assignments/responses carry image/audio values as specified in artifact notes.

## Language and authority

A field is exactly `{"type":"image_ref","visibility":"private"}` or uses `group` visibility. Its submitted value is exactly `{"ref":"opaque-host-identity"}`. The reference is a nonempty Unicode scalar string of at most 256 code points. There is no URL fetching, encoding, MIME claim, readiness claim or user-supplied attestation in the value. The host owns reference syntax and resolution. Neither the language nor `image_contributions@1` restricts images to PNG.

Before accepting a new event the interpreter calls a trusted instance-bound authority with the authenticated actor and reference. Strict boolean `true` attests all of the following:

- The reference resolves in this activity instance, not merely in a global Library/storage namespace.
- The submitting actor owns or has the host's immutable contribution authority for that reference. The local profile requires uploader ownership; seeing somebody else's revealed reference does not grant submission authority.
- The referenced artifact is an image, processing is complete, and its immutable content is available for the promised lifetime of accepted contributions.
- The reference will not be rebound to different content, kind or ownership. The host retains identity/content durably and applies authenticated view-based read authorization.

The runtime validates field/value shape, Unicode/length, exact event grammar, actor/window eligibility, quota, clock/deadline and host authority. It cannot inspect bytes or prove those attestations. Missing authority, inaccessible/foreign/unready/wrong-kind/wrong-owner references, and non-true answers reject the entire submission. Every field must validate before any entry/ledger acceptance is recorded. Hosts must run authority lookup and state acceptance in one serialized transaction; an authority service failure must fail closed without recording partial acceptance. The SQLite trials do so locally. Byte handling, scanning/processing, uploads, transcoding, authentication and storage lifecycle are host responsibilities.

## Discovery and compatibility

The normal support response includes `image_contributions@1` and an additional host profile describing `kind: image` and supported upload MIME types. The reference hosts advertise `image/png` only. This is an explicit local upload/validation limit, not a language-level image type or a promise that every image encoding works. Hosts can support other image encodings under the same semantic contract, after their own byte/processing validation. Authors choose the semantic image capability; authoring/upload UI should populate host-supported choices and explain incompatibility. A future encoding-specific activity requirement needs an explicit capability contract; it must not be silently converted or represented by today's generic image token.

Disabling the image capability reports unsupported before instance state, tokens or media are created. No public event or instance request can supply the trusted registry. The reference engines' `trustedMedia` input is a scoped harness registry for tests only, equivalent to an embedding authority callback; it is not accepted by the HTTP transport.

## Identity, retries and reads

Upload and contribution are separate operations. A successful upload returns a ready stable identity; a failed/late submission does not undo the upload or publish it. Retrying the same local upload is idempotent by content-addressed identity and uploader binding. Authors/hosts must preserve the upload receipt, then retry the same event ID and exact reference after uncertain acceptance. The first successful contribution freezes the value in the accepted entry and event ledger. A matching accepted event replays before any new authority check, including after deadline/restart; changed reuse rejects. Reference revocation or temporary retrieval failure must not mutate the accepted identity or imply the original event failed. A host must preserve retained blobs; this milestone does not define deletion/replacement/moderation.

Own ready uploads remain readable by their uploader even if they were never submitted. Other actors can read a blob only when their current authenticated projection contains its typed reference. Private fields reveal only to their author until explicit `reveal@1`; group fields are visible immediately. Organizer reads follow those same projection rules. Historical recurrence reveal does not expose a different unpublished reference in a later occurrence. After publication, seeing a reference grants read access but not submission ownership. The runtime keeps stable references and ordinary view semantics; the host gates the actual bytes.

## Local byte profile and evidence

The local hosts store instance/actor-bound, SHA-256-addressed PNG bytes in SQLite with immutable insert-or-ignore rows. Validation is independently implemented in Python and Node: at most 524,288 bytes, 1–1024 pixels on each axis, 8-bit RGB/RGBA, noninterlaced, bounded decode, chunk CRCs/order, complete decompression and scanline filters. Malformed/trailing/truncated bytes, unsupported MIME and unauthorized upload reject. This intentionally narrow decoder is not a general PNG processing product.

[Image engine checks](image_check.py) cover scheduled, recurring, ordinary mixed and no-reveal forms; host-attested opaque JPEG and PNG identities demonstrate encoding-independent runtime acceptance without claiming a JPEG byte decoder. [Durable trials](../../validation/0.24/image_trial.py) use actual PNG bytes, private/read-gated access, missing/foreign/unready/wrong-kind references, race/replay, partial-success retry, disabled support, workers, restart and a held-out image-to-story transfer. Four scenarios in each language compare image check-in and group-immediate image daily prompt against actual preserved 0.12 hosts. Package transfer exchanges definitions, not running state or uploaded blobs.

An independent review of the initial 0.19 commit found a Python output-bound error and noncontiguous IDAT acceptance in both hosts. The current local validators correct both; [direct regressions](../../validation/0.24/png_check.py) and actual upload trials verify bounded decode with no flush remainder and contiguous IDAT ordering. This corrects implementation behavior against the stated profile; it does not add an image encoding, runtime operation or optional product feature. The output budget is derived from bounded dimensions (at most `1024 × (1 + 1024 × 4) + 1` bytes), independent of the compressed stream's claimed expansion.

Raw chunk names are checked as four ASCII letters with an uppercase reserved third byte before any special-chunk interpretation. The core chunk profile admits IHDR, contiguous IDAT and terminal IEND; other critical chunks are unsupported. Ancillary chunks are treated as opaque metadata after name/CRC checks. The trial is a bounded structural/decompression profile, not a full validator for every ancillary chunk's semantic payload or ordering rules. No actual rendering pipeline, metadata conversion or general image-safety certification is claimed by these local hosts.

Candidate 0.24 retains 0.20 typed image references through source assignment and linked reveal; [typed media rules](artifact-notes.md) extend read projections and add an advertised local WAV profile without changing retained image-field semantics.
