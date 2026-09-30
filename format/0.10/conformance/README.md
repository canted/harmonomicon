# Candidate 0.10 conformance

Run `python3 format/0.10/check.py` from the repository root. The 38 JSON traces contain 35 carried cases and three `offered_response_vote@1` cases. The new cases cover a complete PNG caption vote with a tie, a text activity with no votes, and explicit unsupported behavior. They check early, exact, and late deadlines; private ballots; invalid self and unknown targets; changed and exact retries; scores and every tied winner; and authorized media reads during voting.

The [two-host trial](../../../validation/0.10/README.md) runs the same traces through independent services. Its additional probe races two votes from one participant, checks that only one commits, restarts, advances the worker through voting and result deadlines, and verifies the final tally.
