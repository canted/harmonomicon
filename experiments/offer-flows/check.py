"""Check explicit outcomes, independent implementations, and JSON checkpoint continuation."""

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = sorted((ROOT / "cases").glob("*.json"))
assert CASES, "No cases found"


def run(label, case, prefix=None, resume=None):
    command = (["node", str(ROOT / "run.mjs")] if label == "JavaScript" else
               ["python3", str(ROOT / "run.py")]) + [str(case)]
    if prefix is not None:
        command += ["--prefix", str(prefix)]
    if resume is not None:
        command += ["--resume", str(resume)]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def assert_subset(actual, expected, location="result"):
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{location}: expected object, got {actual!r}"
        for key, value in expected.items():
            assert key in actual, f"{location}: missing {key}"
            assert_subset(actual[key], value, f"{location}.{key}")
    elif isinstance(expected, list):
        assert actual == expected, f"{location}: expected {expected!r}, got {actual!r}"
    else:
        assert actual == expected, f"{location}: expected {expected!r}, got {actual!r}"


def assert_forbidden(actual, dotted):
    value = actual
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return
        value = value[part]
    raise AssertionError(f"forbidden path present: {dotted}")


def assert_invariant(actual, name):
    if name == "each_offer_has_two_other_covers":
        offers = actual["state"]["offers"]
        covers = actual["state"]["covers"]
        for actor, offer in offers.items():
            options = offer["options"]
            assert len(options) == 2 and len(set(options)) == 2, (actor, options)
            assert covers[actor]["id"] not in options, (actor, options)
            assert all(any(cover["id"] == option for cover in covers.values()) for option in options)
    elif name == "no_results_before_complete":
        assert actual["state"]["phase"] != "complete"
        assert all("results" not in view for view in actual["views"].values())
    else:
        raise AssertionError(f"unknown invariant: {name}")


for case in CASES:
    fixture = json.loads(case.read_text())
    results = {label: run(label, case) for label in ("JavaScript", "Python")}
    assert results["JavaScript"] == results["Python"], f"{case.name}: interpreter disagreement"
    actual = results["JavaScript"]
    assert_subset(actual, fixture["expected"], case.name)
    for dotted in fixture.get("forbid", []):
        assert_forbidden(actual, dotted)
    for name in fixture.get("invariants", []):
        assert_invariant(actual, name)
    if "checkpointAt" in fixture:
        checkpoint = fixture["checkpointAt"]
        assert 0 <= checkpoint <= len(fixture["events"]), case.name
        prefixes = {label: run(label, case, prefix=checkpoint) for label in results}
        assert prefixes["JavaScript"] == prefixes["Python"], f"{case.name}: checkpoint disagreement"
        assert prefixes["JavaScript"]["status"] == "checkpoint", case.name
        with tempfile.TemporaryDirectory() as directory:
            for producer, snapshot in prefixes.items():
                path = Path(directory) / "snapshot.json"
                path.write_text(json.dumps(snapshot))
                for consumer in results:
                    resumed = run(consumer, case, resume=path)
                    assert resumed == results[consumer], \
                        f"{case.name}: {consumer} continuation from {producer} snapshot changed result"

print(f"PASS {len(CASES)} cases × 2 interpreters, with cross-language process restart where specified")
