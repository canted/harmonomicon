# Ongoing-activity contract probes

**Status:** Experimental tests of two gaps identified by the [creative-practice revisit](../creative-practice-revisit/README.md). These definitions are not a proposed public schema and do not port any named service.

Run from the repository root:

```sh
python3 experiments/ongoing-activities/check.py
```

The checker compares independent [JavaScript](run.mjs) and [Python](run.py) interpreters after each complete trace and at intermediate checkpoints. It checks both expected results and the absence of private content in another participant's view.

| Probe | Research constraint | Experimental choice being tested |
|---|---|---|
| [Jam session](cases/01-jam-session.json) | The [jam survey](../../research/creative-jams-and-shared-practice.md) documents team formation, optional progress sharing and discussion, final submission, and later review as actual or configurable jam interactions. | One app owns team registration, posts, responses, final submission, review, and reveal. A progress post can be team-only or visible to all participants. The exact windows and permissions are test choices. |
| [Private daily practice](cases/02-private-practice.json) | [750 Words](../../research/activities/750-words-month-challenge.md) distinguishes private writing from a visible completion result and retains month-level consequences. | The package stores an opaque private artifact reference, exposes completion/missed status, and retains two daily records. It does not verify word count or enforce a calendar day. |
| [Public daily practice](cases/03-public-practice.json) | [Jamuary](../../research/activities/jamuary.md) invites daily recordings shared with a community. | A post becomes visible to all participants immediately and remains in the record after the next day opens. The fixed deadlines and missing-day status are experiment choices, not universal Jamuary rules. |

The [contract](contract.md) defines this test vocabulary. [Findings](findings.md) report what the traces establish and which portability questions remain.
