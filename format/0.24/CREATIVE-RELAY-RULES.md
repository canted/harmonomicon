# Harmonomicon 0.24 — Creative relay rules

The group builds one story from a sequence of text and images. Each step invites two people. The first valid completed contribution becomes the next official piece immediately.

1. Shuffle the group once to make a queue. Invite the first two eligible people.
2. Give both invitations one shared deadline: 24 hours in this example.
3. When someone contributes, put that person at the back. Put the other invitee at the front, then invite them with the next eligible person. Both get a fresh 24 hours for the new story piece.
4. Exclude the author of the latest official piece until somebody else contributes.
5. If neither invitee contributes before the deadline, put both at the back and invite the next pair to respond to the same piece.
6. A person may decline. Replace them while keeping their partner's existing invitation and deadline.
7. If a whole pass through the eligible group produces nothing, pause and wait before trying again. The example uses a 24-hour retry delay.

For example, start with A, B, C, D, E. Invite A and B. A contributes, so B and C receive the next invitations and a fresh 24-hour window. If B and C both expire, invite D and E against A's piece. A remains excluded until a different author contributes. With only four people, the last untried person pairs with someone who already had an opportunity; A remains excluded.

The app preserves a losing person's next opportunity, but cannot guarantee they win. An inactive person can remain in the invitation pair while partners respond quickly. Removing or declining participation can rotate them out. At least three available participants are normally needed after excluding the latest author; otherwise the activity pauses.

The app handles invitation delivery, accounts, images, clock and starting the next step. Harmonomicon defines the queue, deadline and acceptance rules. Joining the queue does not automatically grant access to prior material: the host must authorize readers.

This candidate is implemented locally with independent Python and JavaScript runtimes and durable host validation. It is isolated from the main repository and awaits independent review. It has not been published or deployed, and the separate playground is unchanged.
