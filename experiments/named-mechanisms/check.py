"""Compare both named-mechanism interpreters with independent expected fixtures."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = sorted((ROOT / "cases").glob("*.json"))
assert CASES, "No cases found"
for case in CASES:
    fixture = json.loads(case.read_text())
    for label, command in (
        ("JavaScript", ["node", str(ROOT / "run.mjs"), str(case)]),
        ("Python", ["python3", str(ROOT / "run.py"), str(case)]),
    ):
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        actual = json.loads(result.stdout)
        if actual != fixture["expected"]:
            raise AssertionError(f"{case.name} {label}\nexpected: {fixture['expected']}\nactual: {actual}")
print(f"PASS {len(CASES)} cases × 2 interpreters")
