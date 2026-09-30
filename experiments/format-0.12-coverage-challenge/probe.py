#!/usr/bin/env python3
"""Exact 0.12 probe for the selected timed-room coordination slice."""
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent / "packages/one-two-four-all-text.json"
reference = runpy.run_path(str(ROOT / "format/0.12/check.py"))
package = json.loads(PACKAGE.read_text())
reference["validate_package"](package)
nearest = sorted((Path(__file__).resolve().parent / "nearest-0.12").glob("*.json"))
assert len(nearest) == 7
for candidate in nearest:
    reference["validate_package"](json.loads(candidate.read_text()))
participants = list("abcdefgh")

def groups(*member_sets):
    return [{"id": "g" + str(i), "members": list(members)}
            for i, members in enumerate(member_sets, 1)]

instance = {
    "createdAt": 0, "startsAt": 0, "organizer": "organizer",
    "participants": participants,
    "groupsByRound": [
        groups("abcdefgh"),
        groups(*participants),
        groups("ab", "cd", "ef", "gh"),
        groups("abcd", "efgh"),
        groups("abcdefgh"),
    ],
}
model = reference["BASE"]["GuidedModel"](reference["prior_package"](package), instance)
assert [r["durationMs"] for r in package["behavior"]["rounds"]] == [60000, 60000, 120000, 300000, 420000]
assert model.view("a")["currentRound"] == 1
assert model.view("a", 60000)["currentRound"] == 2
assert model.event({"eventId":"solo-a","type":"submit","actor":"a","at":60001,
                    "payload":{"round":2,"value":"A private thought"}}) == "accepted"
assert model.view("b")["rounds"][1]["groups"][0]["entries"] == []
assert model.view("organizer")["rounds"][1]["groups"][0]["entries"] == []
assert model.view("a", 120000)["currentRound"] == 3
assert model.event({"eventId":"pair-a","type":"submit","actor":"a","at":120001,
                    "payload":{"round":3,"value":"An idea for the pair"}}) == "accepted"
assert model.view("b")["rounds"][2]["groups"][0]["entries"][0]["value"] == "An idea for the pair"
assert model.view("c")["rounds"][2]["groups"][0]["entries"] == []
assert model.view("a", 240000)["currentRound"] == 4
assert model.event({"eventId":"quartet-a","type":"submit","actor":"a","at":240001,
                    "payload":{"round":4,"value":"A quartet synthesis"}}) == "accepted"
assert model.view("d")["rounds"][3]["groups"][0]["entries"][0]["value"] == "A quartet synthesis"
assert model.view("e")["rounds"][3]["groups"][0]["entries"] == []
assert model.view("a", 540000)["currentRound"] == 5
assert model.event({"eventId":"all-a","type":"submit","actor":"a","at":540001,
                    "payload":{"round":5,"value":"An idea to share"}}) == "accepted"
assert model.view("h")["rounds"][4]["groups"][0]["entries"][0]["value"] == "An idea to share"
assert model.view("a", 960000)["phase"] == "complete"
assert model.event({"eventId":"late","type":"submit","actor":"b","at":960000,
                    "payload":{"round":5,"value":"Too late"}}) == "rejected"
print("8 valid 0.12 packages; timed-room slice: PASS")
