#!/usr/bin/env python3
"""Check candidate 0.1 examples and conformance cases with one reference model.

This is not an independent host or a general JSON Schema validator.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAFE_MAX = 9007199254740991
CAPABILITIES = {
    "identity@1", "serial_events@1", "durable_state@1", "private_views@1",
    "clock@1", "text@1", "image_ref@1",
}
COMMON = {"identity@1", "serial_events@1", "durable_state@1", "private_views@1"}
CONTENT = {"language", "title", "summary", "setup", "prompt", "participant", "completion", "access"}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, required, optional=()):
    check(type(value) is dict, "expected object")
    keys = set(value)
    check(set(required) <= keys, f"missing fields: {set(required) - keys}")
    check(keys <= set(required) | set(optional), f"unknown fields: {keys - set(required) - set(optional)}")


def text(value):
    return type(value) is str and len(value) > 0


def integer(value):
    return type(value) is int and 0 <= value <= SAFE_MAX


def validate_package(package):
    fields(package, {"format", "id", "version", "content", "provenance", "participants", "requires", "behavior"})
    check(package["format"] == "harmonomicon.activity-package/0.1", "wrong format")
    check(text(package["id"]) and re.fullmatch(r"[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+", package["id"]), "invalid package ID")
    check(text(package["version"]) and re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", package["version"]), "invalid package version")
    fields(package["content"], CONTENT)
    check(all(text(v) for v in package["content"].values()), "empty content field")
    provenance = package["provenance"]
    fields(provenance, {"kind", "credit", "rights"}, {"sourceUrl"})
    check(provenance["kind"] in {"original", "adaptation"}, "invalid provenance kind")
    check(text(provenance["credit"]) and text(provenance["rights"]), "missing provenance text")
    if provenance["kind"] == "adaptation":
        check(text(provenance.get("sourceUrl")) and provenance["sourceUrl"].startswith(("http://", "https://")), "adaptation requires sourceUrl")
    bounds = package["participants"]
    fields(bounds, {"min", "max"})
    check(type(bounds["min"]) is int and type(bounds["max"]) is int and 2 <= bounds["min"] <= bounds["max"], "invalid participant bounds")
    requirements = package["requires"]
    check(type(requirements) is list and all(type(x) is str for x in requirements) and len(requirements) == len(set(requirements)) and set(requirements) <= CAPABILITIES, "invalid capability list")
    behavior = package["behavior"]
    contract = behavior.get("contract") if type(behavior) is dict else None
    if contract == "timed_collection@1":
        fields(behavior, {"contract", "medium", "allowPromptOverride"})
        required = COMMON | {"clock@1"}
    elif contract == "sequential_handoff@1":
        fields(behavior, {"contract", "medium", "steps", "allowPromptOverride"})
        check(type(behavior["steps"]) is int and behavior["steps"] >= 2, "invalid handoff step count")
        check(bounds["min"] == bounds["max"] == behavior["steps"], "handoff steps must match participant bounds")
        required = set(COMMON)
    else:
        raise ValueError(f"unknown behavior contract: {contract}")
    check(behavior["medium"] in {"text", "image_ref"}, "invalid medium")
    check(type(behavior["allowPromptOverride"]) is bool, "invalid prompt override flag")
    required.add("text@1" if behavior["medium"] == "text" else "image_ref@1")
    check(required <= set(requirements), f"missing package capability: {required - set(requirements)}")


class ReferenceModel:
    def __init__(self, package, instance):
        validate_package(package)
        self.package = package
        self.behavior = package["behavior"]
        self.contract = self.behavior["contract"]
        self.instance = instance
        self.entries = []
        self.accepted_ids = {}
        self.index = 0
        self.now = instance["createdAt"]
        check(integer(self.now), "invalid creation time")
        participants = instance["participants"]
        bounds = package["participants"]
        check(type(participants) is list and bounds["min"] <= len(participants) <= bounds["max"], "invalid participant count")
        check(all(text(x) and x != "system" for x in participants), "invalid participant IDs")
        check(len(participants) == len(set(participants)), "duplicate participant IDs")
        check(text(instance["organizer"]) and instance["organizer"] not in participants and instance["organizer"] != "system", "invalid organizer")
        self.participants = set(participants)
        self.organizer = instance["organizer"]
        self.prompt = instance.get("prompt", package["content"]["prompt"])
        check(text(self.prompt), "invalid prompt")
        check("prompt" not in instance or self.behavior["allowPromptOverride"], "prompt override forbidden")
        if self.contract == "timed_collection@1":
            fields(instance, {"createdAt", "organizer", "participants", "opensAt", "closesAt"}, {"prompt"})
            self.opens_at = instance["opensAt"]
            self.closes_at = instance["closesAt"]
            check(integer(self.opens_at) and integer(self.closes_at) and self.now <= self.opens_at < self.closes_at, "invalid collection window")
            self.phase = "waiting" if self.now < self.opens_at else "open"
        else:
            fields(instance, {"createdAt", "organizer", "participants", "route"}, {"prompt"})
            self.route = instance["route"]
            check(type(self.route) is list and len(self.route) == self.behavior["steps"] and set(self.route) == self.participants and len(self.route) == len(set(self.route)), "invalid handoff route")
            self.phase = "active"

    def advance(self, at):
        if self.contract == "timed_collection@1":
            if at >= self.closes_at:
                self.phase = "closed"
            elif at >= self.opens_at:
                self.phase = "open"
        self.now = at

    def event(self, event):
        if type(event) is not dict or set(event) != {"eventId", "type", "actor", "at", "payload"}:
            return "rejected"
        at = event["at"]
        if not integer(at) or at < self.now:
            return "rejected"
        self.advance(at)
        event_id = event["eventId"]
        if not text(event_id) or not text(event["type"]) or not text(event["actor"]) or type(event["payload"]) is not dict:
            return "rejected"
        identity = (event["type"], event["actor"], json.dumps(event["payload"], sort_keys=True, ensure_ascii=False))
        if event_id in self.accepted_ids:
            return "replayed" if self.accepted_ids[event_id] == identity else "rejected"
        actor = event["actor"]
        if event["type"] == "tick" and self.contract == "timed_collection@1" and actor == "system" and not event["payload"]:
            self.accepted_ids[event_id] = identity
            return "accepted"
        if event["type"] != "submit" or actor not in self.participants or set(event["payload"]) != {"value"}:
            return "rejected"
        value = event["payload"]["value"]
        if not text(value):
            return "rejected"
        if self.contract == "timed_collection@1":
            if self.phase != "open" or any(entry["actor"] == actor for entry in self.entries):
                return "rejected"
        else:
            if self.phase != "active" or actor != self.route[self.index]:
                return "rejected"
        self.entries.append({"actor": actor, "value": value})
        if self.contract == "sequential_handoff@1":
            self.index += 1
            if self.index == len(self.route):
                self.phase = "complete"
        self.accepted_ids[event_id] = identity
        return "accepted"

    def view(self, actor, at=None):
        check(actor in self.participants or actor == self.organizer, "unknown view actor")
        if at is not None:
            check(integer(at) and at >= self.now, "invalid view time")
            self.advance(at)
        if self.contract == "timed_collection@1":
            result = {"phase": self.phase, "submissionCount": len(self.entries)}
        else:
            result = {
                "phase": self.phase,
                "step": min(self.index + 1, len(self.route)),
                "currentActor": self.route[self.index] if self.phase == "active" else None,
            }
        if actor in self.participants:
            own = next((entry for entry in self.entries if entry["actor"] == actor), None)
            if own is not None:
                result["own"] = own
        if self.contract == "timed_collection@1":
            if self.phase == "closed":
                result["entries"] = list(self.entries)
        elif self.phase == "complete":
            result["entries"] = list(self.entries)
        elif actor == self.route[self.index]:
            result["input"] = self.prompt if self.index == 0 else self.entries[-1]["value"]
        return result


def check_case(path):
    case = json.loads(path.read_text())
    package = json.loads((path.parent / case["package"]).read_text())
    validate_package(package)
    missing = sorted(set(package["requires"]) - set(case["capabilities"]))
    if package["behavior"]["contract"] not in case["contracts"]:
        missing.append("behavior:" + package["behavior"]["contract"])
    missing.sort()
    if case.get("expectStatus") == "unsupported":
        check(sorted(missing) == case["missing"], f"{path.name}: wrong missing capabilities")
        return
    check(not missing, f"{path.name}: unexpectedly unsupported: {missing}")
    model = ReferenceModel(package, case["instance"])
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
    print(f"{len(cases)} candidate cases passed in the reference model")


if __name__ == "__main__":
    main()
