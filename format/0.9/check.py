#!/usr/bin/env python3
"""Reference checks for candidate 0.9; independent hosts are in validation/0.9."""

import json
import base64
import hashlib
import re
import zlib
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = runpy.run_path(str(ROOT.parent / "0.7/check.py"))
check = BASE["check"]
fields = BASE["fields"]
text = BASE["text"]
integer = BASE["integer"]
SAFE_MAX = 9007199254740991
OLD = {"timed_collection@1", "sequential_handoff@1", "repeated_collection@1", "offered_response@1",
       "project_cycle@1", "ongoing_space@1", "guided_rounds@1"}
NEW = "competitive_handoff@1"
REQUIRED = {"identity@1", "serial_events@1", "durable_state@1", "private_views@1", "clock@1", "text@1"}


def valid_png(data):
    if type(data) is not bytes or not (8 <= len(data) <= 524288) or data[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    pos, width, height, channels, idat = 8, None, None, None, []
    while pos + 12 <= len(data):
        length = int.from_bytes(data[pos:pos+4], "big")
        end = pos + 12 + length
        if length > 524288 or end > len(data):
            return False
        kind, body = data[pos+4:pos+8], data[pos+8:pos+8+length]
        if zlib.crc32(kind+body) & 0xffffffff != int.from_bytes(data[pos+8+length:end], "big"):
            return False
        if width is None:
            if kind != b"IHDR" or length != 13:
                return False
            width, height = int.from_bytes(body[:4], "big"), int.from_bytes(body[4:8], "big")
            if not (1 <= width <= 1024 and 1 <= height <= 1024 and body[8] == 8
                    and body[9] in (2,6) and body[10:] == b"\0\0\0"):
                return False
            channels = 3 if body[9] == 2 else 4
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            if length != 0 or not idat or end != len(data):
                return False
            expected = height * (1 + width * channels)
            try:
                decoder = zlib.decompressobj()
                pixels = decoder.decompress(b"".join(idat), expected + 1)
                pixels += decoder.flush(max(1, expected - len(pixels) + 1))
            except zlib.error:
                return False
            return (decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
                    and len(pixels) == expected and
                    all(pixels[row * (1 + width * channels)] <= 4 for row in range(height)))
        elif kind == b"IHDR" or not (len(kind) == 4 and 97 <= kind[0] <= 122
                                            and 65 <= kind[2] <= 90 and all(65 <= c <= 90 or 97 <= c <= 122 for c in kind)):
            return False
        pos = end
    return False


def decode_upload(media_type, encoded):
    if media_type != "image/png" or type(encoded) is not str:
        return None
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error):
        return None
    return raw if base64.b64encode(raw).decode() == encoded and valid_png(raw) else None


def prior_package(package):
    copy = dict(package)
    copy["format"] = "harmonomicon.activity-package/0.7"
    if package["behavior"]["contract"] == NEW:
        copy["behavior"] = {"contract": "timed_collection@1", "medium": "text",
                            "allowPromptOverride": package["behavior"]["allowPromptOverride"]}
    return copy


def validate_package(package):
    check(type(package) is dict and package.get("format") == "harmonomicon.activity-package/0.9", "wrong format")
    behavior = package.get("behavior")
    check(type(behavior) is dict and behavior.get("contract") in OLD | {NEW}, "unknown behavior")
    BASE["validate_package"](prior_package(package))
    if behavior["contract"] != NEW:
        return
    fields(behavior, {"contract", "allowPromptOverride", "steps", "attemptMs"})
    check(type(behavior["allowPromptOverride"]) is bool, "invalid override flag")
    check(type(behavior["steps"]) is int and 2 <= behavior["steps"] <= 8, "invalid step count")
    check(integer(behavior["attemptMs"]) and behavior["attemptMs"] > 0, "invalid attempt duration")
    check(package["participants"]["min"] >= 2, "too few participants")
    check(REQUIRED <= set(package["requires"]), "missing competitive-handoff capability")


class CompetitiveModel:
    def __init__(self, package, instance):
        validate_package(package)
        fields(instance, {"createdAt", "organizer", "participants", "startsAt", "routes"}, {"prompt"})
        self.package = package
        self.now, self.starts_at = instance["createdAt"], instance["startsAt"]
        check(integer(self.now) and integer(self.starts_at) and self.now <= self.starts_at, "invalid start")
        self.attempt_ms = package["behavior"]["attemptMs"]
        self.step_count = package["behavior"]["steps"]
        check(self.starts_at + self.step_count * 2 * self.attempt_ms <= SAFE_MAX,
              "route can exceed safe time")
        self.participants = instance["participants"]
        bounds = package["participants"]
        check(type(self.participants) is list and bounds["min"] <= len(self.participants) <= bounds["max"]
              and all(text(p) and p != "system" for p in self.participants)
              and len(self.participants) == len(set(self.participants)), "invalid participants")
        self.organizer = instance["organizer"]
        check(text(self.organizer) and self.organizer != "system" and self.organizer not in self.participants,
              "invalid organizer")
        self.routes = instance["routes"]
        check(type(self.routes) is list and len(self.routes) == self.step_count, "invalid route length")
        for attempts in self.routes:
            check(type(attempts) is list and 1 <= len(attempts) <= 2, "invalid attempt count")
            for pair in attempts:
                check(type(pair) is list and len(pair) == 2 and all(text(p) and p in self.participants for p in pair)
                      and pair[0] != pair[1], "invalid offer pair")
        self.prompt = instance.get("prompt", package["content"]["prompt"])
        check(text(self.prompt) and ("prompt" not in instance or package["behavior"]["allowPromptOverride"]),
              "invalid prompt")
        self.phase = "waiting" if self.now < self.starts_at else "open"
        self.step = 0
        self.attempt = 0
        self.deadline = self.starts_at + self.attempt_ms
        self.declined = set()
        self.entries = []
        self.accepted_ids = {}

    def advance_attempt(self, at):
        if self.attempt + 1 < len(self.routes[self.step]):
            self.attempt += 1
            self.deadline = at + self.attempt_ms
            self.declined.clear()
        else:
            self.phase = "stalled"
            self.deadline = None
            self.declined.clear()

    def reconcile(self):
        if self.phase == "waiting" and self.now >= self.starts_at:
            self.phase = "open"
        while self.phase == "open" and self.now >= self.deadline:
            self.advance_attempt(self.deadline)

    def event(self, event):
        if type(event) is not dict or set(event) != {"eventId", "type", "actor", "at", "payload"}:
            return "rejected"
        at = event["at"]
        if not integer(at) or at < self.now:
            return "rejected"
        self.now = at
        self.reconcile()
        event_id, kind, actor, payload = event["eventId"], event["type"], event["actor"], event["payload"]
        if not text(event_id) or not text(kind) or not text(actor) or type(payload) is not dict:
            return "rejected"
        identity = (kind, actor, json.dumps(payload, sort_keys=True, ensure_ascii=False))
        if event_id in self.accepted_ids:
            return "replayed" if self.accepted_ids[event_id] == identity else "rejected"
        if kind == "tick" and actor == "system" and not payload:
            self.accepted_ids[event_id] = identity
            return "accepted"
        if self.phase != "open" or actor not in self.routes[self.step][self.attempt] or actor in self.declined:
            return "rejected"
        if kind == "decline" and set(payload) == {"step", "attempt"}:
            if type(payload["step"]) is not int or payload["step"] != self.step + 1 or type(payload["attempt"]) is not int or payload["attempt"] != self.attempt + 1:
                return "rejected"
            self.declined.add(actor)
            self.accepted_ids[event_id] = identity
            if len(self.declined) == 2:
                self.advance_attempt(self.now)
            return "accepted"
        if kind == "submit" and set(payload) == {"step", "attempt", "value"}:
            if (type(payload["step"]) is not int or payload["step"] != self.step + 1
                    or type(payload["attempt"]) is not int or payload["attempt"] != self.attempt + 1
                    or not text(payload["value"])):
                return "rejected"
            self.entries.append({"step": self.step + 1, "actor": actor, "value": payload["value"]})
            self.accepted_ids[event_id] = identity
            if self.step + 1 == self.step_count:
                self.phase = "complete"
                self.deadline = None
                self.declined.clear()
            else:
                self.step += 1
                self.attempt = 0
                self.deadline = self.now + self.attempt_ms
                self.declined.clear()
            return "accepted"
        return "rejected"

    def view(self, actor, at=None):
        check(actor == self.organizer or actor in self.participants, "unknown actor")
        if at is not None:
            check(integer(at) and at >= self.now, "invalid view time")
            self.now = at
        self.reconcile()
        view = {"phase": self.phase, "step": None if self.phase == "complete" else self.step + 1,
                "attempt": self.attempt + 1 if self.phase == "open" else None,
                "deadline": self.deadline if self.phase == "open" else None,
                "acceptedCount": len(self.entries)}
        if actor in self.participants:
            view["ownEntries"] = [entry for entry in self.entries if entry["actor"] == actor]
        if self.phase == "open" and actor in self.routes[self.step][self.attempt] and actor not in self.declined:
            view["offer"] = {"step": self.step + 1, "attempt": self.attempt + 1,
                             "deadline": self.deadline,
                             "input": self.prompt if self.step == 0 else self.entries[-1]["value"]}
        if self.phase == "complete":
            view["entries"] = self.entries
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
        model = CompetitiveModel(package, case["instance"])
    else:
        old = prior_package(package)
        if contract == "guided_rounds@1":
            model = BASE["GuidedModel"](old, case["instance"])
        else:
            m06, pkg06 = BASE["BASE"], BASE["prior_package"](old)
            if contract == "ongoing_space@1":
                model = m06["OngoingModel"](pkg06, case["instance"])
            else:
                m05, pkg05 = m06["BASE"], m06["prior_package"](pkg06)
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
    for attempt in case.get("uploadAttempts", []):
        fields(attempt, {"actor", "mediaType", "data", "expectStatus"})
        check(attempt["actor"] in case["instance"]["participants"] and attempt["expectStatus"] == "invalid_media"
              and decode_upload(attempt["mediaType"], attempt["data"]) is None,
              "invalid upload attempt expectation")
    uploads = {}
    for upload in case.get("uploads", []):
        fields(upload, {"actor", "mediaType", "data", "ref"})
        check(upload["actor"] in case["instance"]["participants"] and upload["mediaType"] == "image/png", "invalid media owner or type")
        raw = decode_upload(upload["mediaType"], upload["data"])
        check(raw is not None and re.fullmatch(r"sha256:[0-9a-f]{64}", upload["ref"])
              and upload["ref"] == "sha256:" + hashlib.sha256(raw).hexdigest(), "invalid media reference")
        uploads.setdefault(upload["actor"], set()).add(upload["ref"])
    def visible(node, ref):
        if node == ref:
            return True
        if type(node) is dict:
            return any(visible(value, ref) for value in node.values())
        if type(node) is list:
            return any(visible(value, ref) for value in node)
        return False
    medium = package["behavior"].get("sourceMedium", package["behavior"].get("medium"))
    for index, step in enumerate(case["events"], 1):
        event = step["event"]
        if (medium == "image_ref" and event["type"] in ("submit", "submit_source")
                and event["payload"].get("value") not in uploads.get(event["actor"], set())):
            invalid = dict(event, payload={**event["payload"], "value": ""})
            actual = model.event(invalid)
        else:
            actual = model.event(event)
        check(actual == step["outcome"], f"{path.name} event {index}: {actual} != {step['outcome']}")
        for view in step.get("views", []):
            actual_view = model.view(view["actor"], view.get("at"))
            check(actual_view == view["expect"], f"{path.name} view {index}: {actual_view} != {view['expect']}")
        for access in step.get("mediaReads", []):
            fields(access, {"actor", "ref", "expect"})
            actor, ref = access["actor"], access["ref"]
            check(access["expect"] in ("allowed", "denied"), "invalid media access expectation")
            allowed = actor in uploads and ref in uploads[actor] or visible(model.view(actor), ref)
            check(allowed == (access["expect"] == "allowed"), f"{path.name} media access {index}: {actor} {ref}")


def main():
    paths = sorted((ROOT / "conformance").glob("*.json"))
    check(bool(paths), "no cases")
    for path in paths:
        check_case(path)
        print("ok", path.relative_to(ROOT))
    print(f"{len(paths)} candidate 0.9 cases passed in the reference model")


if __name__ == "__main__":
    main()
