#!/usr/bin/env python3
"""Reference checks for candidate 0.5; independent hosts are in validation/0.5."""

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = runpy.run_path(str(ROOT.parent / "0.4/check.py"))
check = BASE["check"]
fields = BASE["fields"]
text = BASE["text"]
integer = BASE["integer"]
OLD = {"timed_collection@1", "sequential_handoff@1", "repeated_collection@1", "offered_response@1"}
NEW = "project_cycle@1"
REQUIRED = {"identity@1", "serial_events@1", "durable_state@1", "private_views@1", "clock@1", "text@1"}


def prior_package(package):
    copy = dict(package)
    copy["format"] = "harmonomicon.activity-package/0.4"
    if package["behavior"]["contract"] == NEW:
        copy["behavior"] = {"contract": "timed_collection@1", "medium": "text",
                            "allowPromptOverride": package["behavior"]["allowPromptOverride"]}
    return copy


def validate_package(package):
    check(type(package) is dict and package.get("format") == "harmonomicon.activity-package/0.5", "wrong format")
    behavior = package.get("behavior")
    check(type(behavior) is dict and behavior.get("contract") in OLD | {NEW}, "unknown behavior")
    BASE["validate_package"](prior_package(package))
    if behavior["contract"] == NEW:
        fields(behavior, {"contract", "allowPromptOverride"})
        check(type(behavior["allowPromptOverride"]) is bool, "invalid prompt override")
        check(REQUIRED <= set(package["requires"]), "missing project-cycle capability")
        check(package["participants"]["min"] >= 2, "project cycle requires two participants")


class ProjectModel:
    def __init__(self, package, instance):
        validate_package(package)
        fields(instance, {"createdAt", "organizer", "participants", "teams", "opensAt", "submissionDeadline", "reviewDeadline"}, {"prompt"})
        self.package = package
        self.now = instance["createdAt"]
        self.opens_at = instance["opensAt"]
        self.submission_deadline = instance["submissionDeadline"]
        self.review_deadline = instance["reviewDeadline"]
        check(all(integer(x) for x in (self.now, self.opens_at, self.submission_deadline, self.review_deadline))
              and self.now <= self.opens_at < self.submission_deadline < self.review_deadline, "invalid schedule")
        self.participants = instance["participants"]
        bounds = package["participants"]
        check(type(self.participants) is list and bounds["min"] <= len(self.participants) <= bounds["max"]
              and all(text(p) and p != "system" for p in self.participants)
              and len(self.participants) == len(set(self.participants)), "invalid participants")
        self.organizer = instance["organizer"]
        check(text(self.organizer) and self.organizer != "system" and self.organizer not in self.participants,
              "invalid organizer")
        self.teams = instance["teams"]
        check(type(self.teams) is list and 2 <= len(self.teams) <= len(self.participants), "invalid teams")
        ids, members = [], []
        for team in self.teams:
            fields(team, {"id", "members"})
            check(text(team["id"]) and team["id"] != "system" and type(team["members"]) is list
                  and len(team["members"]) > 0 and all(text(p) for p in team["members"]), "invalid team")
            ids.append(team["id"])
            members.extend(team["members"])
        check(len(ids) == len(set(ids)) and len(members) == len(set(members))
              and set(members) == set(self.participants), "teams must partition participants")
        self.team_of = {member: team["id"] for team in self.teams for member in team["members"]}
        self.prompt = instance.get("prompt", package["content"]["prompt"])
        check(text(self.prompt) and ("prompt" not in instance or package["behavior"]["allowPromptOverride"]),
              "invalid prompt")
        self.posts = []
        self.finals = []
        self.reviews = []
        self.accepted_ids = {}

    def phase(self):
        if self.now < self.opens_at:
            return "waiting"
        if self.now < self.submission_deadline:
            return "work"
        if self.now < self.review_deadline:
            return "review"
        return "complete"

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
        if actor not in self.team_of:
            return "rejected"
        team = self.team_of[actor]
        phase = self.phase()
        if kind == "post_progress" and phase == "work" and set(payload) == {"audience", "value"}:
            if payload["audience"] in {"team", "group"} and text(payload["value"]):
                self.posts.append({"id": event_id, "team": team, "actor": actor,
                                   "audience": payload["audience"], "value": payload["value"], "comments": []})
            else:
                return "rejected"
        elif kind == "comment" and phase == "work" and set(payload) == {"postId", "value"}:
            post = next((p for p in self.posts if p["id"] == payload["postId"]), None)
            if not post or not text(payload["value"]) or (post["audience"] == "team" and post["team"] != team):
                return "rejected"
            post["comments"].append({"actor": actor, "value": payload["value"]})
        elif kind == "submit_final" and phase == "work" and set(payload) == {"value"}:
            if not text(payload["value"]) or any(f["team"] == team for f in self.finals):
                return "rejected"
            self.finals.append({"team": team, "actor": actor, "value": payload["value"]})
        elif kind == "submit_review" and phase == "review" and set(payload) == {"team", "value"}:
            target = payload["team"]
            if (not text(target) or not text(payload["value"]) or target == team
                    or not any(f["team"] == target for f in self.finals)
                    or any(r["actor"] == actor and r["team"] == target for r in self.reviews)):
                return "rejected"
            self.reviews.append({"actor": actor, "team": target, "value": payload["value"]})
        else:
            return "rejected"
        self.accepted_ids[event_id] = identity
        return "accepted"

    def view(self, actor, at=None):
        check(actor == self.organizer or actor in self.team_of, "unknown actor")
        if at is not None:
            check(integer(at) and at >= self.now, "invalid view time")
            self.now = at
        phase = self.phase()
        own_team = self.team_of.get(actor)
        view = {"phase": phase,
                "finalStatuses": [{"team": team["id"], "status": "submitted" if any(f["team"] == team["id"] for f in self.finals)
                                   else "pending" if phase in {"waiting", "work"} else "missed"} for team in self.teams],
                "progress": [post for post in self.posts if post["audience"] == "group" or post["team"] == own_team],
                "finalCount": len(self.finals), "reviewCount": len(self.reviews)}
        if own_team is not None:
            own_final = next((f for f in self.finals if f["team"] == own_team), None)
            if own_final is not None:
                view["ownFinal"] = own_final
            view["ownReviews"] = [r for r in self.reviews if r["actor"] == actor]
        if phase in {"review", "complete"}:
            view["finals"] = self.finals
        if phase == "complete":
            view["reviews"] = self.reviews
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
        model = ProjectModel(package, case["instance"])
    else:
        old = prior_package(package)
        if contract == "offered_response@1":
            model = BASE["OfferModel"](old, case["instance"])
        elif contract == "repeated_collection@1":
            model = BASE["BASE"]["RepeatedCollection"](BASE["prior_package"](old), case["instance"])
        else:
            prior = BASE["BASE"]["base_package"](BASE["prior_package"](old))
            model = BASE["BASE"]["BASE"]["ReferenceModel"](prior, case["instance"])
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
    print(f"{len(paths)} candidate 0.5 cases passed in the reference model")


if __name__ == "__main__":
    main()
