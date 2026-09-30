# Candidate 0.16 conformance cases

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

Five additional traces cover two-item quotas and anonymous staged reveal; partial pools and claim/acknowledgment timeouts; empty pools; transition-time organizer regrouping with historical privacy; and fixed solo/pair/quartet/whole-group windows. Those bring the earlier set to twelve traces. Four more cover deadline-only close after everyone answers early, partial collection at the exact boundary, an empty window crossed by a worker jump, and scheduled reveal followed by private paired reflection: sixteen total.

Every trace is resumed from serialized state at every event boundary, then compared to uninterrupted execution. Additional checks reject sixty-one invalid package definitions, enforce actor-view authentication, reconcile read deadlines and a clock jump across three story turns, accept ordinary event IDs such as `__proto__`, and normalize integer-valued JSON numbers identically. Two additional arrangements, check-in-then-story and pooled-ideas-then-pairs, execute without activity-specific interpreter changes. The sixteen prior 0.15 traces retain identical outcomes and actor views. The checker verifies that the migration list contains each of the twenty earlier packages exactly once.

Run `python3 format/0.16/check.py`. For JSON Schema verification, install `format/0.16/requirements-validation.txt` in a virtual environment and run the checker with `--schema`. The [local app-host trial](../../../validation/0.16/README.md) executes the same packages through authenticated HTTP interfaces with separate SQLite stores, concurrent writes, workers, restart, and exchange. These results establish the listed cases, not arbitrary composition or public deployment.

The [migration scenarios](check-in-migration.json) compare six runs against the unchanged legacy collection model, including the two original 0.12 fixtures. The [comparison adapter](../migration_check.py) translates envelope/view shapes and checks phase, count, own answer, and ordered reveal. The HTTP trial repeats these comparisons against actual 0.12 implementations in both languages. Additional setup checks cover required/default settings, unknown keys, types, schedule ordering, immutable restore, maximum-safe timestamps, and a literal-deadline structured poll with reveal/tally.

Six further traces bring the corpus to **twenty-two**: five full routed ratings; partial pools with exact fractional normalized results and stale-round/replay checks; an empty pool; a two-round sum with valid zero ratings and private paired continuation; a cutoff retaining all tied leaders; and an integer form used without routing. Their expected routes, score rows, ranks, and private projections are explicit rather than derived by the interpreter under test.

Additional checks cover an offset that does not fit the instance roster, opaque Unicode/large-decimal/prototype-like actor IDs, maximum supported integer values, integer-valued JSON floats, equal exact means with different rating counts, and aggregation hidden before publication. All sixteen prior traces preserve their previous outcomes and views. Schema checks cover fourteen example packages and the authored inline definitions. The [app trial](../../../validation/0.16/README.md) adds rating races, worker-only multi-round progression, unsupported numeric/operation/policy tokens, restart, and transfer of the assessment with its private continuation.
