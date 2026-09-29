#!/usr/bin/env python3
"""Reference checks for candidate 0.7; independent hosts are in validation/0.7."""

import json
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = runpy.run_path(str(ROOT.parent / "0.6/check.py"))
check = BASE["check"]
fields = BASE["fields"]
text = BASE["text"]
integer = BASE["integer"]
SAFE_MAX = 9007199254740991
OLD = {"timed_collection@1", "sequential_handoff@1", "repeated_collection@1",
       "offered_response@1", "project_cycle@1", "ongoing_space@1"}
NEW = "guided_rounds@1"
REQUIRED = {"identity@1", "serial_events@1", "durable_state@1", "private_views@1", "clock@1", "text@1"}
VISIBILITY = {"private", "group", "all_after_round"}


def prior_package(package):
    copy = dict(package)
    copy["format"] = "harmonomicon.activity-package/0.6"
    if package["behavior"]["contract"] == NEW:
        copy["behavior"] = {"contract": "timed_collection@1", "medium": "text",
                            "allowPromptOverride": package["behavior"]["allowPromptOverride"]}
    return copy


def validate_package(package):
    check(type(package) is dict and package.get("format") == "harmonomicon.activity-package/0.7", "wrong format")
    behavior = package.get("behavior")
    check(type(behavior) is dict and behavior.get("contract") in OLD | {NEW}, "unknown behavior")
    BASE["validate_package"](prior_package(package))
    if behavior["contract"] != NEW:
        return
    fields(behavior, {"contract", "allowPromptOverride", "rounds"})
    check(type(behavior["allowPromptOverride"]) is bool, "invalid override flag")
    check(REQUIRED <= set(package["requires"]), "missing guided-rounds capability")
    rounds = behavior["rounds"]
    check(type(rounds) is list and 2 <= len(rounds) <= 8, "invalid round count")
    ids = []
    for stage in rounds:
        fields(stage, {"id", "prompt", "durationMs", "groupMin", "groupMax", "visibility"})
        check(text(stage["id"]) and re.fullmatch(r"[a-z][a-z0-9-]*", stage["id"]), "invalid round ID")
        check(text(stage["prompt"]) and integer(stage["durationMs"]) and stage["durationMs"] > 0,
              "invalid prompt or duration")
        check(integer(stage["groupMin"]) and integer(stage["groupMax"])
              and 1 <= stage["groupMin"] <= stage["groupMax"] <= package["participants"]["max"],
              "invalid group bounds")
        check(stage["visibility"] in VISIBILITY, "invalid visibility")
        ids.append(stage["id"])
    check(len(ids) == len(set(ids)), "duplicate round ID")


class GuidedModel:
    def __init__(self, package, instance):
        validate_package(package)
        fields(instance, {"createdAt", "organizer", "participants", "startsAt", "groupsByRound"}, {"prompt"})
        self.package = package
        self.rounds = package["behavior"]["rounds"]
        self.now, self.starts_at = instance["createdAt"], instance["startsAt"]
        check(integer(self.now) and integer(self.starts_at) and self.now <= self.starts_at, "invalid start")
        self.ends_at = self.starts_at + sum(stage["durationMs"] for stage in self.rounds)
        check(self.ends_at <= SAFE_MAX, "session exceeds safe time")
        self.participants = instance["participants"]
        bounds = package["participants"]
        check(type(self.participants) is list and bounds["min"] <= len(self.participants) <= bounds["max"]
              and all(text(p) and p != "system" for p in self.participants)
              and len(self.participants) == len(set(self.participants)), "invalid participants")
        self.organizer = instance["organizer"]
        check(text(self.organizer) and self.organizer != "system" and self.organizer not in self.participants,
              "invalid organizer")
        self.groups = instance["groupsByRound"]
        check(type(self.groups) is list and len(self.groups) == len(self.rounds), "invalid group schedule")
        for stage, groups in zip(self.rounds, self.groups):
            check(type(groups) is list and groups, "missing round groups")
            ids, members = [], []
            for group in groups:
                fields(group, {"id", "members"})
                check(text(group["id"]) and group["id"] != "system" and type(group["members"]) is list
                      and stage["groupMin"] <= len(group["members"]) <= stage["groupMax"]
                      and all(text(p) for p in group["members"]), "invalid group")
                ids.append(group["id"])
                members.extend(group["members"])
            check(len(ids) == len(set(ids)) and len(members) == len(set(members))
                  and set(members) == set(self.participants), "groups must partition participants")
        self.prompt = instance.get("prompt", package["content"]["prompt"])
        check(text(self.prompt) and ("prompt" not in instance or package["behavior"]["allowPromptOverride"]),
              "invalid prompt")
        self.entries = [[] for _ in self.rounds]
        self.accepted_ids = {}

    def position(self):
        if self.now < self.starts_at:
            return "waiting", None, 0
        if self.now >= self.ends_at:
            return "complete", None, len(self.rounds)
        boundary = self.starts_at
        for index, stage in enumerate(self.rounds):
            boundary += stage["durationMs"]
            if self.now < boundary:
                return "round", index + 1, index + 1
        raise AssertionError("unreachable position")

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
        phase, current, _ = self.position()
        if kind != "submit" or phase != "round" or actor not in self.participants or set(payload) != {"round", "value"}:
            return "rejected"
        if type(payload["round"]) is not int or payload["round"] != current or not text(payload["value"]):
            return "rejected"
        entries = self.entries[current - 1]
        if any(entry["actor"] == actor for entry in entries):
            return "rejected"
        group = next(group["id"] for group in self.groups[current - 1] if actor in group["members"])
        entries.append({"group": group, "actor": actor, "value": payload["value"]})
        self.accepted_ids[event_id] = identity
        return "accepted"

    def view(self, actor, at=None):
        check(actor == self.organizer or actor in self.participants, "unknown actor")
        if at is not None:
            check(integer(at) and at >= self.now, "invalid view time")
            self.now = at
        phase, current, opened = self.position()
        view = {"phase": phase, "currentRound": current, "rounds": []}
        boundary = self.starts_at
        for index in range(opened):
            stage = self.rounds[index]
            boundary += stage["durationMs"]
            closed = self.now >= boundary
            item = {"number": index + 1, "id": stage["id"], "prompt": stage["prompt"],
                    "phase": "closed" if closed else "open", "groups": []}
            for group in self.groups[index]:
                entries = [entry for entry in self.entries[index] if entry["group"] == group["id"]]
                if stage["visibility"] == "private":
                    visible = [entry for entry in entries if entry["actor"] == actor]
                elif stage["visibility"] == "group":
                    visible = entries if actor in group["members"] else []
                else:
                    visible = entries if closed else [entry for entry in entries if entry["actor"] == actor]
                item["groups"].append({"id": group["id"], "members": group["members"],
                                       "submissionCount": len(entries), "entries": visible})
            view["rounds"].append(item)
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
        model = GuidedModel(package, case["instance"])
    else:
        old = prior_package(package)
        if contract == "ongoing_space@1":
            model = BASE["OngoingModel"](old, case["instance"])
        else:
            m05, pkg05 = BASE["BASE"], BASE["prior_package"](old)
            if contract == "project_cycle@1":
                model = m05["ProjectModel"](pkg05, case["instance"])
            else:
                m04, pkg04 = m05["BASE"], m05["prior_package"](pkg05)
                if contract == "offered_response@1":
                    model = m04["OfferModel"](pkg04, case["instance"])
                else:
                    m02, pkg02 = m04["BASE"], m04["prior_package"](pkg04)
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
    print(f"{len(paths)} candidate 0.7 cases passed in the reference model")


if __name__ == "__main__":
    main()
