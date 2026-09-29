"""Compare composed flows with legacy traces and check the held-out queue cases."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT.parent / "offer-flows"
LEGACY_CASES = sorted((LEGACY / "cases").glob("*.json"))
NEW_CASES = sorted((ROOT / "cases").glob("*.json"))
assert len(LEGACY_CASES) == 14 and len(NEW_CASES) == 3


def run(command):
    return json.loads(subprocess.run(command, check=True, capture_output=True, text=True).stdout)


def composed(case, definition, language):
    command = (["node", str(ROOT / "run.mjs")] if language == "JavaScript" else
               ["python3", str(ROOT / "run.py")])
    return run(command + [str(case), str(ROOT / "definitions" / definition)])


def subset(actual, expected, location):
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{location}: expected object"
        for key, value in expected.items():
            assert key in actual, f"{location}: missing {key}"
            subset(actual[key], value, f"{location}.{key}")
    else:
        assert actual == expected, f"{location}: {actual!r} != {expected!r}"


def absent(actual, path):
    node = actual
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return
        node = node[part]
    raise AssertionError(f"forbidden field present: {path}")


def equivalent_legacy(old, new, relay, label):
    assert old["status"] == new["status"], label
    if old["status"] == "unsupported":
        assert old == new, label
        return
    assert old["outcomes"] == new["outcomes"], f"{label}: outcomes"
    a, b = old["state"], new["state"]
    assert a["phase"] == b["phase"], f"{label}: phase"
    if relay:
        for old_key, new_key in (("step", "stage"), ("attempt", "attempt"),
                                 ("deadline", "deadline"), ("offers", "assignees"),
                                 ("chain", "chain"), ("acceptedRequests", "acceptedRequests")):
            assert a[old_key] == b[new_key], f"{label}: state.{old_key}"
    else:
        for old_key, new_value in (("covers", b["collections"]["covers"]),
                                   ("offers", b["assignments"]),
                                   ("responses", b["outputs"]["responses"])):
            assert a[old_key] == new_value, f"{label}: state.{old_key}"
    for actor, old_view in old["views"].items():
        view = new["views"][actor]
        for key, expected in old_view.items():
            mapped = {"step": "stage", "offers": "assignees" if relay else "assignments", "covers": "collections.covers",
                      "responses": "outputs.responses"}.get(key, key)
            actual = view
            for part in mapped.split("."):
                actual = actual[part]
            assert actual == expected, f"{label}: views.{actor}.{key}"
        # No participant may gain private data absent in the legacy projection.
        for key in ("input", "offeredCovers", "chosenCoverId", "results", "chain"):
            if key not in old_view and actor not in ("system", "host"):
                assert key not in view, f"{label}: unexpected views.{actor}.{key}"


for case in LEGACY_CASES:
    fixture = json.loads(case.read_text())
    relay = "relay" in fixture["definition"]
    definition = "relay.json" if relay else "cover-response.json"
    original = run(["python3", str(LEGACY / "run.py"), str(case)])
    js = composed(case, definition, "JavaScript")
    py = composed(case, definition, "Python")
    assert js == py, f"{case.name}: interpreter disagreement"
    equivalent_legacy(original, js, relay, case.name)
    for dotted in fixture.get("forbid", []):
        absent(js, dotted)

for case in NEW_CASES:
    fixture = json.loads(case.read_text())
    js = composed(case, "drawception.json", "JavaScript")
    py = composed(case, "drawception.json", "Python")
    assert js == py, f"{case.name}: interpreter disagreement"
    subset(js, fixture["expected"], case.name)
    for dotted in fixture.get("forbid", []):
        absent(js, dotted)

print(f"PASS {len(LEGACY_CASES)} legacy traces + {len(NEW_CASES)} held-out queue cases × 2 interpreters")
