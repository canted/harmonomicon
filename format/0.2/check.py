#!/usr/bin/env python3
"""Check 0.2 packages and cases with one reference model, not a host or JSON Schema validator."""

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = runpy.run_path(str(ROOT.parent / "0.1/check.py"))
check = BASE["check"]
fields = BASE["fields"]
text = BASE["text"]
integer = BASE["integer"]
SAFE_MAX = BASE["SAFE_MAX"]
COMMON = BASE["COMMON"]
CAPABILITIES = BASE["CAPABILITIES"]
OLD_CONTRACTS = {"timed_collection@1", "sequential_handoff@1"}
NEW_CONTRACT = "repeated_collection@1"


def base_package(package):
    """Apply the unchanged 0.1 envelope and shared contract checks to 0.2 data."""
    copy = dict(package)
    copy["format"] = "harmonomicon.activity-package/0.1"
    if package["behavior"]["contract"] == NEW_CONTRACT:
        behavior = package["behavior"]
        copy["behavior"] = {"contract": "timed_collection@1", "medium": behavior["medium"],
                            "allowPromptOverride": behavior["allowPromptOverride"]}
    return copy


def validate_package(package):
    check(type(package) is dict and package.get("format") == "harmonomicon.activity-package/0.2", "wrong format")
    behavior = package.get("behavior")
    check(type(behavior) is dict, "missing behavior")
    contract = behavior.get("contract")
    check(contract in OLD_CONTRACTS | {NEW_CONTRACT}, "unknown behavior contract")
    BASE["validate_package"](base_package(package))
    if contract == NEW_CONTRACT:
        fields(behavior, {"contract", "medium", "allowPromptOverride", "intervalMs", "windowMs", "occurrences", "visibility"})
        interval = behavior["intervalMs"]
        window = behavior["windowMs"]
        count = behavior["occurrences"]
        check(type(interval) is int and 1 <= interval <= SAFE_MAX, "invalid interval")
        check(type(window) is int and 1 <= window <= interval, "invalid window")
        check(type(count) is int and 2 <= count <= 366, "invalid occurrence count")
        check(behavior["visibility"] in {"private", "group_after_close", "group_immediate"}, "invalid visibility")


class RepeatedCollection:
    def __init__(self, package, instance):
        validate_package(package)
        fields(instance, {"createdAt", "organizer", "participants", "startsAt"}, {"prompt"})
        self.behavior = package["behavior"]
        self.now = instance["createdAt"]
        self.starts_at = instance["startsAt"]
        interval = self.behavior["intervalMs"]
        window = self.behavior["windowMs"]
        count = self.behavior["occurrences"]
        check(integer(self.now) and integer(self.starts_at) and self.now <= self.starts_at,
              "invalid creation or opening time")
        check(self.starts_at + (count - 1) * interval + window <= SAFE_MAX,
              "final closing time exceeds safe range")
        participants = instance["participants"]
        bounds = package["participants"]
        check(type(participants) is list and bounds["min"] <= len(participants) <= bounds["max"],
              "invalid participant count")
        check(all(text(x) and x != "system" for x in participants) and len(participants) == len(set(participants)),
              "invalid participants")
        organizer = instance["organizer"]
        check(text(organizer) and organizer != "system" and organizer not in participants, "invalid organizer")
        self.participants = participants
        self.organizer = organizer
        self.prompt = instance.get("prompt", package["content"]["prompt"])
        check(text(self.prompt) and ("prompt" not in instance or self.behavior["allowPromptOverride"]),
              "invalid prompt override")
        self.entries = [[] for _ in range(count)]
        self.accepted_ids = {}

    def phase_at(self, at):
        if at < self.starts_at:
            return "waiting", None, 0
        interval = self.behavior["intervalMs"]
        window = self.behavior["windowMs"]
        count = self.behavior["occurrences"]
        index = min((at - self.starts_at) // interval, count - 1)
        opened = index + 1
        opens_at = self.starts_at + index * interval
        if at < opens_at + window:
            return "open", opened, opened
        return ("complete" if index == count - 1 else "between"), None, opened

    def event(self, event):
        if type(event) is not dict or set(event) != {"eventId", "type", "actor", "at", "payload"}:
            return "rejected"
        at = event["at"]
        if not integer(at) or at < self.now:
            return "rejected"
        self.now = at
        event_id = event["eventId"]
        event_type = event["type"]
        actor = event["actor"]
        payload = event["payload"]
        if not text(event_id) or not text(event_type) or not text(actor) or type(payload) is not dict:
            return "rejected"
        identity = (event_type, actor, json.dumps(payload, sort_keys=True, ensure_ascii=False))
        if event_id in self.accepted_ids:
            return "replayed" if self.accepted_ids[event_id] == identity else "rejected"
        if event_type == "tick" and actor == "system" and not payload:
            self.accepted_ids[event_id] = identity
            return "accepted"
        if event_type != "submit" or actor not in self.participants or set(payload) != {"occurrence", "value"}:
            return "rejected"
        occurrence = payload["occurrence"]
        if type(occurrence) is not int or not text(payload["value"]):
            return "rejected"
        phase, current, _ = self.phase_at(at)
        if phase != "open" or occurrence != current:
            return "rejected"
        entries = self.entries[occurrence - 1]
        if any(entry["actor"] == actor for entry in entries):
            return "rejected"
        entries.append({"actor": actor, "value": payload["value"]})
        self.accepted_ids[event_id] = identity
        return "accepted"

    def view(self, actor, at=None):
        check(actor == self.organizer or actor in self.participants, "unknown view actor")
        if at is not None:
            check(integer(at) and at >= self.now, "invalid view time")
            self.now = at
        phase, current, opened = self.phase_at(self.now)
        result = {"phase": phase, "currentOccurrence": current, "occurrences": []}
        for index in range(opened):
            number = index + 1
            close = self.starts_at + index * self.behavior["intervalMs"] + self.behavior["windowMs"]
            item_phase = "closed" if self.now >= close else "open"
            entries = self.entries[index]
            submitted = {entry["actor"] for entry in entries}
            item = {
                "number": number,
                "phase": item_phase,
                "submissionCount": len(entries),
                "statuses": [
                    {"actor": participant,
                     "status": "complete" if participant in submitted else "pending" if item_phase == "open" else "missed"}
                    for participant in self.participants
                ],
            }
            if actor in self.participants:
                own = next((entry for entry in entries if entry["actor"] == actor), None)
                if own is not None:
                    item["own"] = own
            visibility = self.behavior["visibility"]
            if visibility == "group_immediate" or (visibility == "group_after_close" and item_phase == "closed"):
                item["entries"] = list(entries)
            result["occurrences"].append(item)
        return result


def check_case(path):
    case = json.loads(path.read_text())
    package = json.loads((path.parent / case["package"]).read_text())
    validate_package(package)
    missing = sorted(set(package["requires"]) - set(case["capabilities"]))
    contract = package["behavior"]["contract"]
    if contract not in case["contracts"]:
        missing.append("behavior:" + contract)
    missing.sort()
    if case.get("expectStatus") == "unsupported":
        check(missing == case["missing"], f"{path.name}: wrong missing tokens")
        return
    check(not missing, f"{path.name}: unexpectedly unsupported: {missing}")
    model = BASE["ReferenceModel"](base_package(package), case["instance"]) if contract in OLD_CONTRACTS else RepeatedCollection(package, case["instance"])
    for n, step in enumerate(case["events"], 1):
        outcome = model.event(step["event"])
        check(outcome == step["outcome"], f"{path.name} event {n}: {outcome} != {step['outcome']}")
        for view in step.get("views", []):
            actual = model.view(view["actor"], view.get("at"))
            check(actual == view["expect"], f"{path.name} event {n} view {view['actor']}: {actual} != {view['expect']}")


def main():
    cases = sorted((ROOT / "conformance").glob("*.json"))
    check(bool(cases), "no cases found")
    for path in cases:
        check_case(path)
        print("ok", path.relative_to(ROOT))
    print(f"{len(cases)} candidate 0.2 cases passed in the reference model")


if __name__ == "__main__":
    main()
