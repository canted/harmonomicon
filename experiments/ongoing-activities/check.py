"""Check source-constrained ongoing-activity probes in independent runtimes."""

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = sorted((ROOT / "cases").glob("*.json"))
assert len(CASES) == 4


def run(language, case, definition):
    command = (["node", str(ROOT / "run.mjs")] if language == "JavaScript" else
               ["python3", str(ROOT / "run.py")])
    return json.loads(subprocess.run(command + [str(case), str(definition)],
                                     check=True, capture_output=True, text=True).stdout)


def subset(actual, expected, location):
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{location}: expected object"
        for key, value in expected.items():
            assert key in actual, f"{location}: missing {key}"
            subset(actual[key], value, f"{location}.{key}")
    else:
        assert actual == expected, f"{location}: {actual!r} != {expected!r}"


def at_path(actual, dotted):
    for part in dotted.split("."):
        actual = actual[part]
    return actual


def check_result(case, definition, expected, absent_text, label):
    js = run("JavaScript", case, definition)
    py = run("Python", case, definition)
    assert js == py, f"{label}: interpreter disagreement"
    subset(js, expected, label)
    for dotted, forbidden in absent_text.items():
        assert forbidden not in json.dumps(at_path(js, dotted)), f"{label}: leaked {forbidden}"
    return js


checkpoints = 0
for case in CASES:
    fixture = json.loads(case.read_text())
    definition = ROOT / "definitions" / fixture["definition"]
    check_result(case, definition, fixture["expected"], fixture.get("absentText", {}), case.name)
    for point in fixture.get("checkpoints", []):
        with tempfile.TemporaryDirectory() as temporary:
            prefix_case = Path(temporary) / "prefix.json"
            prefix_fixture = dict(fixture, events=fixture["events"][:point["through"]])
            prefix_case.write_text(json.dumps(prefix_fixture))
            check_result(prefix_case, definition, point["expected"],
                         point.get("absentText", {}), f"{case.name}@{point['through']}")
        checkpoints += 1

print(f"PASS {len(CASES)} ongoing-activity traces + {checkpoints} checkpoints × 2 interpreters")
