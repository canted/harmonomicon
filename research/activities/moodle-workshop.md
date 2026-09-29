# Moodle Workshop

## Identity and context

- **Description:** Learners submit work, assess assigned peers' submissions using a teacher-defined form, and receive submission and assessment grades after evaluation.
- **Group and mode:** A course group working asynchronously over days or weeks in Moodle. A teacher configures and oversees the workshop.
- **Facilitator:** Moodle controls phase-specific access, stores submissions and assessments, can allocate reviews, and calculates grades; the teacher controls setup, overrides, and final closure.
- **Experience:** Produce work, examine peers' work, give structured feedback, and receive feedback.

## Preparation

The teacher creates a Workshop, supplies submission and assessment instructions, chooses an assessment strategy and form, and optionally provides examples. The teacher can set submission and assessment opening dates and deadlines, choose late-submission behavior, and select manual, random, or scheduled reviewer allocation. The workshop must be moved into Submission phase before learners can submit.

## Procedure

1. **Setup:** The teacher configures instructions, assessment form, grades, dates, and allocation policy. Learners cannot submit or assess yet.
2. **Submission:** Learners submit text or permitted files during the access window. The teacher sees who has submitted. If enabled, Moodle moves to Assessment after the submission deadline on a later cron run.
3. **Allocation:** The teacher assigns reviewers manually, asks Moodle to assign them randomly, or configures scheduled random allocation with the automatic phase switch. Allocation settings can specify reviews per submission or reviewer, group restrictions, self assessment, and whether a learner can review without submitting.
4. **Assessment:** Assigned reviewers assess submissions using the configured form during the assessment access window. The teacher monitors progress and moves the workshop to Grading evaluation.
5. **Grading evaluation:** Moodle calculates separate submission and assessment grades. The teacher can change grades and select submissions to publish.
6. **Closed:** The teacher closes the workshop. Grades move to the course gradebook; learners can see their results and selected published submissions.

## Rules and choices

- **Phase gates:** Setup → Submission → Assessment → Grading evaluation → Closed is typical. Teachers can also move back to earlier phases; it is not an irreversible linear workflow.
- **Time gates:** A workshop phase and its access dates are separate. Being in Submission phase does not itself grant access outside configured submission dates.
- **Late work:** If enabled, late submissions are allowed but learners cannot edit them after submission. Moodle's settings page says late submissions require subsequent reviewer allocation by the teacher.
- **Allocation:** Scheduled allocation depends on the configured automatic move to Assessment. The teacher still initiates Submission and closes the workshop manually.
- **Grades:** Moodle computes a weighted mean of reviewers' grades for a submission. For assessment quality, the standard evaluation subplugin compares each assessment's criterion-level responses with a computed best assessment. The method is deterministic but Moodle's user documentation says there is no single simple formula for it. Teacher overrides remain possible.
- **Visibility:** Reviewers see assigned work during Assessment. Final grades and selected published work become available to participants when Closed; the teacher can view and adjust more during evaluation.

## Variants

Moodle documents four grading strategies: accumulative numeric criteria, comments only, number of errors, and rubric. It also supports optional example assessments, self assessment, manual versus automatic allocation, and workshops with no deadlines. Each choice changes what learners do or when they can do it.

## Exceptions and open questions

- **Documented recovery:** The teacher can move back a phase, allow resubmission, manually allocate late work, override grades, and recalculate evaluation. A learner may delete a still-editable submission before assessment; teacher deletion after assessment warns about effects on reviews and grades.
- **Unspecified in these pages:** A universal policy for absent reviewers, a guarantee that every submission receives a review, and a full machine-readable formula for every grading strategy. These are not safe defaults for a portable package.

## Access and participation

This activity requires Moodle access, submission in permitted formats, and the ability to read and assess assigned work. Examples and feedback may contain private learner work. The reviewed Moodle pages document configurable file types and text submission but do not establish an accessible equivalent for every assessment form or submission format.

## Mechanisms and possible software role

**Mechanisms:** Teacher-configured phases, separate time gates, deadline-triggered transition, late branch, allocation constraints, reviewer assignments, participant-specific views, deterministic grading, manual override, and final publication. The teacher and software share authority: some transitions can be scheduled, while initial opening, closure, and judgment can remain human-controlled.

## Sources and evidence

| Source | What it supports |
|---|---|
| [Moodle 5.2 Workshop activity](https://docs.moodle.org/502/en/Workshop_activity) | Setup and participant workflow |
| [Moodle 5.2 Workshop settings](https://docs.moodle.org/502/en/Workshop_settings) | Strategies, deadlines, late submissions, allocation, automatic switch limitations |
| [Moodle 5.2 Using Workshop](https://docs.moodle.org/502/en/Using_Workshop) | Phase controls, visibility, grading method, recovery |

The Moodle pages describe configurable behavior, not one universal workshop configuration. Mechanism labels and portability implications are analysis.
