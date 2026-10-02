# Candidate 0.19 held-out coverage and profile review

**Pinned implementation:** `eab8745fc5e0b70afc1617845e3c9005b5bad019`, including the independently rechecked PNG corrections after initial candidate commit `8411c02`. No runtime operation or version was added for this review. **Result:** useful bounded composition is demonstrated; image-source distribution is a concrete composability gap. This is a historical capability assessment at the stated pin.

[Inventory and next decision](inventory.md) records supported families, important missing primitives, optional nuances, the host contract and nonfunctional limits. [Cases](cases.json) and [authored packages](examples/) are review witnesses outside the candidate corpus. [probe.py](probe.py) runs independent engines/schema and restarts at every event boundary. [host_probe.py](host_probe.py) runs both durable hosts with actual PNGs and demonstrates why text reference assignment cannot grant image read access.

## Selection and evidence limits

Four new arrangements were authored after the implementation was pinned, reusing different existing operation families. They are held out of the implementation/conformance corpus, not a blind external or random sample: the author knows the candidate profile. Their independent expected outcomes/privacy facts and cross-language/durable agreement show that these arrangements work without new interpreter code. They do not estimate coverage across all activities.

Negative targets come from documented mechanisms in [Cover and Response](../../research/activities/cover-and-response.md), [permissioned feedback](../../research/activities/critical-response-process.md), and [changing creative prompt series](../../research/activities/the-january-challenge.md). The progress-stream target is a constructed digital project/journal variant, not a universal requirement of [Global Game Jam](../../research/activities/global-game-jam.md); that card explicitly does not prescribe an in-app progress feed. No fresh claims about current external products are made here. Simplified image-source exchange deliberately omits two alternatives/choice/exposure balancing in line with the user's scope clarification.

| New arrangement | Checked result |
|---|---|
| Recurring mixed moodboard → choice tally → pair reflection | Public energy, private image/choice until reveal, missed statuses, two fixed windows and retained room privacy pass. |
| Photo introduction → group poll → cumulative story | Private images, explicit reveal, exact poll counts, organizer close and authored turn continuation pass. |
| Photo introduction → randomized text idea exchange | Images and text distribution coexist; saved non-self text assignments and independent linked responses pass. Photos themselves are not assigned. |
| Private pair deliberation → full-group decision | Historical pair privacy remains intact through a later full-group poll and tally. |

All four pass in Python/JavaScript, schema, every-event serialized restart and both authenticated durable hosts with actual PNG references. Expectations are declared in `cases.json`, not generated from engine agreement.

Six direct limits are executable: collected images cannot feed assignment; pools have no image medium; typed images reject in text pools; repeated progress from one actor in the same form rejects; logging a denial does not gate a subsequent opinion; fixed recurrence has no prompt-list binding. The durable string-reference workaround is also tested: placing an image digest in pool text yields a non-self text assignment, but the recipient's image read remains unauthorized because no typed image projection was granted. Reply acceptance in that workaround is merely a text source link, not a response to an accessible authorized image.

## Run

```sh
PYTHONDONTWRITEBYTECODE=1 python3 experiments/format-0.19-readiness/probe.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/format-0.19-readiness/host_probe.py
```

The first command uses the optional JSON Schema validation dependency. The second launches temporary local loopback services and cleans them up. The probe verifies that runtime/host files still match the pinned commit. These review cases supplement, rather than silently inflate, candidate 0.19's 38 traces/114 invalid definitions/23 examples.
