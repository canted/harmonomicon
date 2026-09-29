#!/usr/bin/env python3
"""Check 0.3 examples and cases with one reference model, not an independent host."""

import json
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = runpy.run_path(str(ROOT.parent / "0.2/check.py"))
check = BASE["check"]
fields = BASE["fields"]
text = BASE["text"]
integer = BASE["integer"]
SAFE_MAX = BASE["SAFE_MAX"]
POLICY = "policy:balanced_artifacts_exact32@1"
NEW = "offered_response@1"
OLD = {"timed_collection@1", "sequential_handoff@1", "repeated_collection@1"}
MAX_U64 = 18446744073709551615
M = 1 << 32


def canonical_u64(value):
    return type(value) is str and len(value) <= 20 and re.fullmatch(r"0|[1-9][0-9]*", value) is not None and int(value) <= MAX_U64


def prior_package(package):
    result = dict(package)
    result["format"] = "harmonomicon.activity-package/0.2"
    if package["behavior"]["contract"] == NEW:
        behavior = package["behavior"]
        result["behavior"] = {"contract": "timed_collection@1", "medium": behavior["sourceMedium"],
                              "allowPromptOverride": behavior["allowPromptOverride"]}
        result["requires"] = [token for token in package["requires"] if token != POLICY]
    return result


def validate_package(package):
    check(type(package) is dict and package.get("format") == "harmonomicon.activity-package/0.3", "wrong format")
    behavior = package.get("behavior")
    check(type(behavior) is dict and behavior.get("contract") in OLD | {NEW}, "unknown behavior")
    BASE["validate_package"](prior_package(package))
    if behavior["contract"] != NEW:
        return
    fields(behavior, {"contract", "sourceMedium", "allowPromptOverride", "assignmentPolicy"})
    check(behavior["assignmentPolicy"] == POLICY, "wrong assignment policy")
    requirements = package["requires"]
    check(type(requirements) is list and requirements.count(POLICY) == 1, "policy token required exactly once")
    check(package["participants"]["min"] >= 3, "offer activity needs at least three participants")
    required = {"identity@1", "serial_events@1", "durable_state@1", "private_views@1", "clock@1", "text@1", POLICY}
    if behavior["sourceMedium"] == "image_ref":
        required.add("image_ref@1")
    check(required <= set(requirements), f"missing requirement: {required - set(requirements)}")


class OfferModel:
    def __init__(self, package, instance):
        validate_package(package)
        fields(instance, {"createdAt", "organizer", "participants", "opensAt", "sourceDeadline", "responseDeadline", "roundId"}, {"prompt"})
        self.package = package
        self.now = instance["createdAt"]
        self.opens_at = instance["opensAt"]
        self.source_deadline = instance["sourceDeadline"]
        self.response_deadline = instance["responseDeadline"]
        check(all(integer(value) for value in [self.now, self.opens_at, self.source_deadline, self.response_deadline])
              and self.now <= self.opens_at < self.source_deadline < self.response_deadline, "invalid stage times")
        self.round_id = instance["roundId"]
        check(canonical_u64(self.round_id), "invalid round ID")
        participants = instance["participants"]
        bounds = package["participants"]
        check(type(participants) is list and bounds["min"] <= len(participants) <= bounds["max"], "invalid participants")
        check(all(canonical_u64(person) for person in participants) and len(participants) == len(set(participants)),
              "invalid participant ID")
        organizer = instance["organizer"]
        check(text(organizer) and organizer != "system" and organizer not in participants, "invalid organizer")
        self.participants = participants
        self.organizer = organizer
        self.prompt = instance.get("prompt", package["content"]["prompt"])
        check(text(self.prompt) and ("prompt" not in instance or package["behavior"]["allowPromptOverride"]),
              "invalid prompt override")
        self.sources = []
        self.offers = {}
        self.responses = []
        self.accepted_ids = {}

    def phase(self):
        if self.now < self.opens_at:
            return "waiting"
        if self.now < self.source_deadline:
            return "sources_open"
        if len(self.sources) < 3:
            return "insufficient_sources"
        if self.now < self.response_deadline:
            return "responses_open"
        return "complete"

    def offer_for(self, actor):
        exposed = {source["actor"]: 0 for source in self.sources}
        for offer in self.offers.values():
            for source_id in offer:
                exposed[source_id] += 1
        r, u = int(self.round_id), int(actor)
        def key(source):
            a = int(source["actor"])
            x = ((r * 73856093) % M) ^ ((u * 19349663) % M) ^ ((a * 83492791) % M)
            score = x ^ (x >> 16)
            return exposed[source["actor"]], score, a
        eligible = [source for source in self.sources if source["actor"] != actor]
        return [source["actor"] for source in sorted(eligible, key=key)[:2]]

    def event(self, event):
        if type(event) is not dict or set(event) != {"eventId", "type", "actor", "at", "payload"}:
            return "rejected"
        at = event["at"]
        if not integer(at) or at < self.now:
            return "rejected"
        self.now = at
        event_id, event_type, actor, payload = event["eventId"], event["type"], event["actor"], event["payload"]
        if not text(event_id) or not text(event_type) or not text(actor) or type(payload) is not dict:
            return "rejected"
        identity = (event_type, actor, json.dumps(payload, sort_keys=True, ensure_ascii=False))
        if event_id in self.accepted_ids:
            return "replayed" if self.accepted_ids[event_id] == identity else "rejected"
        if event_type == "tick" and actor == "system" and not payload:
            self.accepted_ids[event_id] = identity
            return "accepted"
        if actor not in self.participants:
            return "rejected"
        phase = self.phase()
        if event_type == "submit_source" and phase == "sources_open" and set(payload) == {"value"}:
            if not text(payload["value"]) or any(source["actor"] == actor for source in self.sources):
                return "rejected"
            self.sources.append({"actor": actor, "value": payload["value"]})
            self.accepted_ids[event_id] = identity
            return "accepted"
        if event_type == "request_offer" and phase == "responses_open" and not payload:
            if not any(source["actor"] == actor for source in self.sources):
                return "rejected"
            if actor in self.offers:
                self.accepted_ids[event_id] = identity
                return "existing"
            self.offers[actor] = self.offer_for(actor)
            self.accepted_ids[event_id] = identity
            return "accepted"
        if event_type == "submit_response" and phase == "responses_open" and set(payload) == {"source", "value"}:
            source_id, value = payload["source"], payload["value"]
            if actor not in self.offers or type(source_id) is not str or source_id not in self.offers[actor] or not text(value) \
                    or any(response["actor"] == actor for response in self.responses):
                return "rejected"
            self.responses.append({"actor": actor, "source": source_id, "value": value})
            self.accepted_ids[event_id] = identity
            return "accepted"
        return "rejected"

    def view(self, actor, at=None):
        check(actor == self.organizer or actor in self.participants, "unknown view actor")
        if at is not None:
            check(integer(at) and at >= self.now, "invalid view time")
            self.now = at
        phase = self.phase()
        result = {"phase": phase, "sourceCount": len(self.sources), "responseCount": len(self.responses)}
        if actor in self.participants:
            own_source = next((source for source in self.sources if source["actor"] == actor), None)
            if own_source is not None:
                result["ownSource"] = own_source
            if actor in self.offers:
                result["offer"] = [next(source for source in self.sources if source["actor"] == source_id)
                                   for source_id in self.offers[actor]]
            own_response = next((response for response in self.responses if response["actor"] == actor), None)
            if own_response is not None:
                result["ownResponse"] = own_response
        if phase == "complete":
            result["sources"] = list(self.sources)
            result["responses"] = list(self.responses)
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
    check(not missing, f"{path.name}: unsupported: {missing}")
    model = (OfferModel(package, case["instance"]) if contract == NEW else
             BASE["RepeatedCollection"](prior_package(package), case["instance"]) if contract == "repeated_collection@1" else
             BASE["BASE"]["ReferenceModel"](BASE["base_package"](prior_package(package)), case["instance"]))
    for n, step in enumerate(case["events"], 1):
        outcome = model.event(step["event"])
        check(outcome == step["outcome"], f"{path.name} event {n}: {outcome} != {step['outcome']}")
        for view in step.get("views", []):
            actual = model.view(view["actor"], view.get("at"))
            check(actual == view["expect"], f"{path.name} event {n} view {view['actor']}: {actual} != {view['expect']}")


def main():
    paths = sorted((ROOT / "conformance").glob("*.json"))
    check(bool(paths), "no cases found")
    for path in paths:
        check_case(path)
        print("ok", path.relative_to(ROOT))
    print(f"{len(paths)} candidate 0.3 cases passed in the reference model")


if __name__ == "__main__":
    main()
