# Creative continuation — candidate 0.22

The accompanying [package JSON](examples/creative-continuation-input.json) is the executable activity definition, validated in independent Python and JavaScript engines and durable hosts. Candidate 0.22 is prepared for independent review; existing 0.21 hosts must explicitly add the new operation versions and input capability. See the [verification record](../../validation/0.22/EVIDENCE.md) for evidence and limits.

Give participants a starting piece with its real author and origin. They propose continuations, privately vote on the accepted contributions, and see a structured result. The host can then start another instance of the same package using the actual selected contribution as the new starting piece.

The package has five instructions:

1. Collect one text, image, or audio continuation per eligible participant, using the supplied starting piece.
2. Vote on accepted contributions. Each voter has one current choice and may change it until closing.
3. Count current eligible votes privately.
4. Select the contribution with the most votes, resolving positive-vote ties randomly. If candidates exist but no votes were counted, choose one of those candidates randomly.
5. Show the counts, selection and reason for the outcome. Individual ballots remain private.

The `inputs.starting_piece` declaration is where the package asks for typed material. The first instruction's `input:{binding:"starting_piece"}` consumes that material. The host binds the name to authorized durable source data; it does not replace it with a copied title or accept a caller's claimed author/value.

## What belongs to the host

The host chooses dates and eligible participants, supplies authorized source material, stores media and renders the results. It decides whether and when to start a later instance. The package does not contain a calendar or an automatic infinite loop.

The separate [host binding example](creative-continuation-host-binding.json) illustrates a privileged instance-creation request. It is **not package JSON** and is not a participant action. `starting_piece` points to the settled selection `selected` in the preceding local instance `creative_one`. The numeric dates 100/200/300 are controlled test-clock fixtures; real hosts must supply actual resolved windows. The host resolves that real output and preserves its globally unique originating instance identity, source step, item ID, author and round. It separately records the selection that handed the material onward.

For the first instance, a host can instead bind a real accepted contribution using `{instance:"opening_material",source:"piece",itemId:"opening"}`. The reference profile requires the source to be closed and publicly projected to every destination actor, including ready authorized bytes for media. Merely knowing a private source ID is insufficient. Receiving a media viewing grant does not grant ownership for submission.

## Boundaries participants should see

Starting material is visible when collection begins. Accepted eligible contributions and their authors become visible when voting is entered, even if voting's configured opening is later. Voting stays open until its deadline or a trusted host close; it does not close just because everyone has voted.

An empty candidate pool gives `no_candidates` and no selected material. Random selection cannot choose from an empty set. The alternative `retain_input` no-vote policy applies when people supplied candidate continuations but no votes were counted: it deliberately keeps the previous source rather than advancing to a candidate. Empty collection still stops because the package has received no possible continuation at all. Hosts can present that distinction plainly. Omitting the new fallback preserves 0.21's `no_votes` stop behavior.

This example demonstrates the core activity and a generic host handoff. It does not claim complete product parity, notification delivery, previous-winner exclusion, a designated-person tie decision, multiple contributions per participant, video or unlimited streams. No publishing or 1.0 decision is included.
