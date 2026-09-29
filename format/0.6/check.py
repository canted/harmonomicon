#!/usr/bin/env python3
"""Reference checks for candidate 0.6; independent hosts are in validation/0.6."""

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = runpy.run_path(str(ROOT.parent / "0.5/check.py"))
check = BASE["check"]
fields = BASE["fields"]
text = BASE["text"]
integer = BASE["integer"]
SAFE_MAX = 9007199254740991
OLD = {"timed_collection@1", "sequential_handoff@1", "repeated_collection@1",
       "offered_response@1", "project_cycle@1"}
NEW = "ongoing_space@1"
REQUIRED = {"identity@1", "serial_events@1", "durable_state@1", "private_views@1", "clock@1", "text@1"}


def prior_package(package):
    copy = dict(package)
    copy["format"] = "harmonomicon.activity-package/0.5"
    if package["behavior"]["contract"] == NEW:
        copy["behavior"] = {"contract": "timed_collection@1", "medium": "text",
                            "allowPromptOverride": package["behavior"]["allowPromptOverride"]}
    return copy


def validate_package(package):
    check(type(package) is dict and package.get("format") == "harmonomicon.activity-package/0.6", "wrong format")
    behavior = package.get("behavior")
    check(type(behavior) is dict and behavior.get("contract") in OLD | {NEW}, "unknown behavior")
    BASE["validate_package"](prior_package(package))
    if behavior["contract"] != NEW:
        return
    fields(behavior, {"contract", "allowPromptOverride", "schedule"})
    check(type(behavior["allowPromptOverride"]) is bool, "invalid override flag")
    check(REQUIRED <= set(package["requires"]), "missing ongoing-space capability")
    schedule = behavior["schedule"]
    check(type(schedule) is dict and schedule.get("kind") in {"open", "fixed_prompt_series"}, "invalid schedule")
    if schedule["kind"] == "open":
        fields(schedule, {"kind"})
    else:
        fields(schedule, {"kind", "intervalMs", "windowMs", "prompts", "statusVisibility"})
        interval, window, prompts = schedule["intervalMs"], schedule["windowMs"], schedule["prompts"]
        check(integer(interval) and interval > 0 and integer(window) and 0 < window <= interval,
              "invalid prompt interval/window")
        check(type(prompts) is list and 2 <= len(prompts) <= 366 and all(text(x) for x in prompts),
              "invalid prompt series")
        check(schedule["statusVisibility"] in {"none", "group"}, "invalid status visibility")


class OngoingModel:
    def __init__(self, package, instance):
        validate_package(package)
        self.package = package
        self.schedule = package["behavior"]["schedule"]
        required = {"createdAt", "organizer", "participants", "startsAt"}
        required.add("endsAt" if self.schedule["kind"] == "open" else "startsAt")
        fields(instance, required, {"prompt"})
        self.now, self.starts_at = instance["createdAt"], instance["startsAt"]
        check(integer(self.now) and integer(self.starts_at) and self.now <= self.starts_at, "invalid start")
        if self.schedule["kind"] == "open":
            self.ends_at = instance["endsAt"]
            check(integer(self.ends_at) and self.starts_at < self.ends_at, "invalid end")
        else:
            self.ends_at = self.starts_at + (len(self.schedule["prompts"]) - 1) * self.schedule["intervalMs"] + self.schedule["windowMs"]
            check(self.ends_at <= SAFE_MAX, "series exceeds safe time")
        self.participants = instance["participants"]
        bounds = package["participants"]
        check(type(self.participants) is list and bounds["min"] <= len(self.participants) <= bounds["max"]
              and all(text(p) and p != "system" for p in self.participants)
              and len(self.participants) == len(set(self.participants)), "invalid participants")
        self.organizer = instance["organizer"]
        check(text(self.organizer) and self.organizer != "system" and self.organizer not in self.participants,
              "invalid organizer")
        self.prompt = instance.get("prompt", package["content"]["prompt"])
        check(text(self.prompt) and ("prompt" not in instance or package["behavior"]["allowPromptOverride"]),
              "invalid prompt")
        self.entries = []
        self.accepted_ids = {}

    def position(self):
        if self.now < self.starts_at:
            return "waiting", None, 0
        if self.now >= self.ends_at:
            return "complete", None, 0 if self.schedule["kind"] == "open" else len(self.schedule["prompts"])
        if self.schedule["kind"] == "open":
            return "open", None, 0
        index = min((self.now - self.starts_at) // self.schedule["intervalMs"], len(self.schedule["prompts"]) - 1)
        closes = self.starts_at + index * self.schedule["intervalMs"] + self.schedule["windowMs"]
        return ("open", index + 1, index + 1) if self.now < closes else ("between", None, index + 1)

    def event(self, event):
        if type(event) is not dict or set(event) != {"eventId", "type", "actor", "at", "payload"}:
            return "rejected"
        at = event["at"]
        if not integer(at) or at < self.now:
            return "rejected"
        self.now = at
        event_id, kind, actor, payload = event["eventId"], event["type"], event["actor"], event["payload"]
        if not text(event_id) or not text(kind) or not text(actor) or type(payload) is not dict:
            return "rejected"
        identity = (kind, actor, json.dumps(payload, sort_keys=True, ensure_ascii=False))
        if event_id in self.accepted_ids:
            return "replayed" if self.accepted_ids[event_id] == identity else "rejected"
        if kind == "tick" and actor == "system" and not payload:
            self.accepted_ids[event_id] = identity
            return "accepted"
        if actor not in self.participants:
            return "rejected"
        phase, current, _ = self.position()
        if kind == "post_entry" and phase == "open":
            keys = {"audience", "value"} if self.schedule["kind"] == "open" else {"occurrence", "audience", "value"}
            if set(payload) != keys or payload["audience"] not in {"private", "group"} or not text(payload["value"]):
                return "rejected"
            if self.schedule["kind"] != "open" and (type(payload["occurrence"]) is not int or payload["occurrence"] != current):
                return "rejected"
            self.entries.append({"id": event_id, "actor": actor, "occurrence": current,
                                 "audience": payload["audience"], "value": payload["value"], "comments": []})
        elif kind == "comment" and phase in {"open", "between"} and set(payload) == {"entryId", "value"}:
            entry = next((entry for entry in self.entries if entry["id"] == payload["entryId"]), None)
            if not entry or entry["audience"] != "group" or not text(payload["value"]):
                return "rejected"
            entry["comments"].append({"actor": actor, "value": payload["value"]})
        else:
            return "rejected"
        self.accepted_ids[event_id] = identity
        return "accepted"

    def view(self, actor, at=None):
        check(actor == self.organizer or actor in self.participants, "unknown actor")
        if at is not None:
            check(integer(at) and at >= self.now, "invalid view time")
            self.now = at
        phase, current, opened = self.position()
        view = {"phase": phase,
                "entries": [entry for entry in self.entries if entry["audience"] == "group" or entry["actor"] == actor]}
        if self.schedule["kind"] == "fixed_prompt_series":
            view["currentOccurrence"] = current
            view["occurrences"] = []
            for index in range(opened):
                number = index + 1
                closes = self.starts_at + index * self.schedule["intervalMs"] + self.schedule["windowMs"]
                status = "closed" if self.now >= closes else "open"
                item = {"number": number, "prompt": self.schedule["prompts"][index], "phase": status}
                if self.schedule["statusVisibility"] == "group":
                    posted = {entry["actor"] for entry in self.entries if entry["occurrence"] == number}
                    item["statuses"] = [{"actor": person, "status": "complete" if person in posted
                                         else "missed" if status == "closed" else "pending"} for person in self.participants]
                view["occurrences"].append(item)
        return view


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
    check(not missing, f"{path.name}: unsupported: {missing}")
    if contract == NEW:
        model = OngoingModel(package, case["instance"])
    else:
        old = prior_package(package)
        if contract == "project_cycle@1":
            model = BASE["ProjectModel"](old, case["instance"])
        else:
            pkg04 = BASE["prior_package"](old)
            m04 = BASE["BASE"]
            if contract == "offered_response@1":
                model = m04["OfferModel"](pkg04, case["instance"])
            else:
                pkg02 = m04["prior_package"](pkg04)
                m02 = m04["BASE"]
                if contract == "repeated_collection@1":
                    model = m02["RepeatedCollection"](pkg02, case["instance"])
                else:
                    model = m02["BASE"]["ReferenceModel"](m02["base_package"](pkg02), case["instance"])
    for index, step in enumerate(case["events"], 1):
        actual = model.event(step["event"])
        check(actual == step["outcome"], f"{path.name} event {index}: {actual} != {step['outcome']}")
        for view in step.get("views", []):
            actual_view = model.view(view["actor"], view.get("at"))
            check(actual_view == view["expect"], f"{path.name} view {index}: {actual_view} != {view['expect']}")


def main():
    paths = sorted((ROOT / "conformance").glob("*.json"))
    check(bool(paths), "no cases")
    for path in paths:
        check_case(path)
        print("ok", path.relative_to(ROOT))
    print(f"{len(paths)} candidate 0.6 cases passed in the reference model")


if __name__ == "__main__":
    main()
