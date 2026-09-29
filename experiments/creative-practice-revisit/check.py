"""Reproduce two boundary cases introduced by the creative-practice survey.

These are diagnostic runs against existing interpreters, not a proposed schema.
"""

import json
import subprocess
import tempfile
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parents[1]


def run(language, interpreter, *paths):
    command = (["node"] if language == "JavaScript" else ["python3"])
    command += [str(interpreter), *(str(path) for path in paths)]
    return json.loads(subprocess.run(command, check=True, capture_output=True, text=True).stdout)


def both(interpreter_dir, case_path, *extra):
    js = run("JavaScript", interpreter_dir / "run.mjs", case_path, *extra)
    py = run("Python", interpreter_dir / "run.py", case_path, *extra)
    assert js == py, f"{interpreter_dir.name}: interpreter disagreement"
    return js


with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)

    # Exhaust the collection mechanism's two view gates and three late policies.
    # A daily private-writing challenge wants public completion, private content.
    for gate in ("after_own", "at_close"):
        for late_policy in ("mark", "accept", "reject"):
            definition = {
                "format": "activity-named-mechanisms/0.1", "id": "private-writing-attempt",
                "kind": "collection", "requires": ["events", "clock", "access_control"],
                "actors": {"system": "system", "alice": "participant", "bob": "participant"},
                "config": {"participants": ["alice", "bob"], "schedule": "daily",
                           "viewGate": gate, "latePolicy": late_policy},
                "content": {"title": "Diagnostic only"},
            }
            def_path = root / "named-definition.json"
            case_path = root / "named-case.json"
            def_path.write_text(json.dumps(definition))
            base = [
                {"type": "open", "actor": "system", "at": 0,
                 "payload": {"occurrence": 1, "deadline": 100}},
                {"type": "submit", "actor": "alice", "at": 10,
                 "payload": {"artifact": "private-writing-alice"}},
                {"type": "submit", "actor": "bob", "at": 20,
                 "payload": {"artifact": "private-writing-bob"}},
            ]
            fixture = {"definition": "named-definition.json",
                       "capabilities": ["events", "clock", "access_control"],
                       "events": base[:2], "viewActors": ["alice", "bob"]}
            case_path.write_text(json.dumps(fixture))
            one_post = both(EXPERIMENTS / "named-mechanisms", case_path)
            assert one_post["outcomes"] == ["accepted"] * 2
            # Neither gate shows a newly published Jamuary-style post to a
            # participant who has not posted yet.
            assert "posts" not in one_post["views"]["bob"]

            fixture["events"] = base
            case_path.write_text(json.dumps(fixture))
            before = both(EXPERIMENTS / "named-mechanisms", case_path)
            assert before["outcomes"] == ["accepted"] * 3
            if gate == "after_own":
                for actor in ("alice", "bob"):
                    assert before["views"][actor]["posts"] == before["state"]["posts"]
            else:
                assert all("posts" not in view for view in before["views"].values())

            fixture["events"] = base + [
                {"type": "close", "actor": "system", "at": 100, "payload": {}}
            ]
            case_path.write_text(json.dumps(fixture))
            after = both(EXPERIMENTS / "named-mechanisms", case_path)
            for actor in ("alice", "bob"):
                # A visible completion always carries both private artifacts.
                assert after["views"][actor]["posts"] == {
                    "alice": "private-writing-alice", "bob": "private-writing-bob"}
            fixture["events"].append(
                {"type": "open", "actor": "system", "at": 101,
                 "payload": {"occurrence": 2, "deadline": 200}})
            case_path.write_text(json.dumps(fixture))
            next_day = both(EXPERIMENTS / "named-mechanisms", case_path)
            assert next_day["state"]["posts"] == {}  # no month-to-date ledger

    # The stage-plan collection pool has one slot per actor. Two progress posts
    # by that actor cannot coexist under this operation's defined semantics.
    definition = {
        "format": "activity-composition/0.1", "id": "jam-progress-attempt",
        "requires": ["events", "media"],
        "actors": {"system": "system", "alice": "participant"},
        "bindings": {"progress_post": "collect"}, "initialChain": [],
        "stages": [{"id": "progress", "type": "collection", "idlePhase": "building",
                    "pool": "updates", "idField": "postId", "artifactField": "artifact",
                    "minimum": 99, "deadline": 100, "removeBefore": 100,
                    "viewField": "ownUpdate"}],
        "donePhase": "done", "stalledPhase": "stalled", "reveal": {},
    }
    def_path = root / "stage-definition.json"
    case_path = root / "stage-case.json"
    def_path.write_text(json.dumps(definition))
    case_path.write_text(json.dumps({
        "capabilities": ["events", "media"],
        "events": [
            {"type": "progress_post", "actor": "alice", "at": 10,
             "payload": {"postId": 1, "artifact": "sketch"}},
            {"type": "progress_post", "actor": "alice", "at": 20,
             "payload": {"postId": 2, "artifact": "playable-prototype"}},
        ],
        "viewActors": ["alice"],
    }))
    result = both(EXPERIMENTS / "composition", case_path, def_path)
    assert result["outcomes"] == ["accepted", "accepted"]
    assert result["state"]["collections"]["updates"] == {
        "alice": {"id": 2, "actor": "alice", "artifact": "playable-prototype"}}

print("PASS diagnostic: 6 named configurations × 4 traces and one composed progress trace, both interpreters")
