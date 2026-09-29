"""Compare both interpreters with manually specified conformance outcomes."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = sorted((ROOT / "cases").glob("*.json"))


def invoke(command, case):
    result = subprocess.run(command + [str(case)], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


failures = []
for case in CASES:
    fixture = json.loads(case.read_text())
    expected = fixture["expected"]
    definition_path = (case.parent / fixture["definition"]).resolve()
    definition = json.loads(definition_path.read_text())
    assert definition["format"] == "activity-experiment/0.1", definition_path
    content = definition["content"]
    assert all(content.get(key) for key in ("title", "setup", "steps", "completion", "source")), definition_path
    assert (definition_path.parent / content["sourceCard"]).exists(), definition_path
    outputs = {
        "JavaScript": invoke(["node", str(ROOT / "interpreters/run.mjs")], case),
        "Python": invoke(["python3", str(ROOT / "interpreters/run.py")], case),
    }
    for name, actual in outputs.items():
        if actual != expected:
            failures.append((case.name, name, expected, actual))

if not CASES:
    raise SystemExit("No conformance cases found")
if failures:
    for case, name, expected, actual in failures:
        print(f"FAIL {case} {name}\n expected: {expected}\n actual:   {actual}")
    raise SystemExit(1)
print(f"PASS {len(CASES)} cases × 2 interpreters")
