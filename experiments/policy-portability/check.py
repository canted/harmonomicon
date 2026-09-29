"""Compare three policy implementations and all cross-runtime JSON continuations."""

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = sorted((ROOT / "cases").glob("*.json"))
LANGUAGES = {
    "JavaScript": ["node", str(ROOT / "run.mjs")],
    "Python": ["python3", str(ROOT / "run.py")],
    "Ruby": ["ruby", str(ROOT / "run.rb")],
}
assert len(CASES) == 5


def run(language, case, snapshot=None, stop_at=None):
    command = LANGUAGES[language] + [str(case)]
    if snapshot or stop_at is not None:
        command += [str(snapshot) if snapshot else "-"]
    if stop_at is not None:
        command += [str(stop_at)]
    process = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(process.stdout)


def subset(actual, expected, label):
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{label}: expected object"
        for key, value in expected.items():
            assert key in actual, f"{label}: missing {key}"
            subset(actual[key], value, f"{label}.{key}")
    else:
        assert actual == expected, f"{label}: {actual!r} != {expected!r}"


continuations = 0
for case in CASES:
    fixture = json.loads(case.read_text())
    uninterrupted = {language: run(language, case) for language in LANGUAGES}
    reference = uninterrupted["Python"]
    for language, result in uninterrupted.items():
        assert result == reference, f"{case.name}: {language} disagrees"
    subset(reference, fixture["expected"], case.name)
    if "checkpointAt" not in fixture:
        continue
    with tempfile.TemporaryDirectory() as temporary:
        snapshot_path = Path(temporary) / "snapshot.json"
        for source in LANGUAGES:
            checkpoint = run(source, case, stop_at=fixture["checkpointAt"])
            assert checkpoint["status"] == "checkpoint", f"{case.name}: {source} checkpoint"
            assert checkpoint["policy"] == "balanced_artifacts_exact32@1"
            snapshot_path.write_text(json.dumps(checkpoint))
            for target in LANGUAGES:
                result = run(target, case, snapshot=snapshot_path)
                assert result == reference, f"{case.name}: {source} -> {target} restart disagrees"
                continuations += 1

print(f"PASS {len(CASES)} policy cases × 3 runtimes + {continuations} cross-runtime continuations")
