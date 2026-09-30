# Candidate 0.13 conformance cases

[Cases](cases.json) are executable witnesses, with an example-package name, ordered reference events, exact expected outcomes, and selected expected or forbidden actor-view fields. They contain explicit expectations rather than accepting agreement between interpreters as sufficient evidence. The [checker](../check.py) also compares every full actor view and resulting state in independently written Python and JavaScript engines.

| Case | Witness |
|---|---|
| Two Truths privacy and rotation | Private answers and guesses; index validation; speaker authority; one guess per actor; retries and changed reuse; stale execution keys; all roster turns. |
| List Game | Reuse of the same operations with text answers and guesses. |
| Timed poll | Private ballots, option validation, forbidden participant close, deadline exclusion, exact counts and replay after close. |
| Empty poll close | Organizer may advance with no ballots; all option counts remain zero. |
| Manual prompted routine | Group-visible responses, organizer authority, and advancement independent of a timer. |
| Cumulative story timeout | Turn ownership, retained whole-story entries, timed omission, and rejection of a late previous-turn event. |
| Check-in | Complete-participation close followed by explicit reveal. |

Every trace is resumed from serialized state at every event boundary, then compared to uninterrupted execution. Additional checks reject seventeen invalid package definitions, enforce actor-view authentication, reconcile read deadlines and a clock jump across three story turns, accept ordinary event IDs such as `__proto__`, and normalize integer-valued JSON numbers identically. An additional authored check-in-then-story package proves a new arrangement executes without adding interpreter code.

Run `python3 format/0.13/check.py`. For JSON Schema verification, install `format/0.13/requirements-validation.txt` in a virtual environment and run the checker with `--schema`. The [local app-host trial](../../../validation/0.13/README.md) executes the same packages through authenticated HTTP interfaces with separate SQLite stores, concurrent writes, workers, restart, and exchange. These results establish the listed cases, not arbitrary composition or public deployment.
