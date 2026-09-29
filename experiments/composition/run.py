"""Interpreter for an experimental plan of reusable activity operations."""

import json
import sys
from pathlib import Path


def copy(value):
    return json.loads(json.dumps(value))


def score(round_id, user_id, artifact_id):
    value = ((round_id * 73856093) ^ (user_id * 19349663) ^ (artifact_id * 83492791)) & 0xFFFFFFFF
    return (value ^ (value >> 16)) & 0xFFFFFFFF


def stage(definition, state):
    index = state["stage"]
    return definition["stages"][index] if index < len(definition["stages"]) else None


def advance_stage(definition, state):
    state["stage"] += 1
    state["status"] = "idle"
    state["attempt"] = 0
    state["deadline"] = None
    state["assignees"] = []
    next_stage = stage(definition, state)
    state["phase"] = next_stage["idlePhase"] if next_stage else definition["donePhase"]
    if next_stage is None:
        state["status"] = "done"


def finish(definition, state):
    state["stage"] = len(definition["stages"])
    state["status"] = "done"
    state["phase"] = definition["donePhase"]
    state["deadline"] = None
    state["assignees"] = []


def synchronize_time(definition, state, at):
    if type(at) is not int or state["status"] in ("done", "stalled"):
        return
    if type(definition.get("finalDeadline")) is int and at >= definition["finalDeadline"]:
        finish(definition, state)
        return
    current = stage(definition, state)
    if current and current["type"] == "collection" and at >= current["deadline"] and \
            len(state["collections"][current["pool"]]) >= current["minimum"]:
        advance_stage(definition, state)


def initialize(definition):
    collections = {item["pool"]: {} for item in definition["stages"] if item["type"] == "collection"}
    outputs = {item["commit"]["target"]: {} for item in definition["stages"]
               if item["type"] == "work" and item["commit"]["mode"] == "per_actor"}
    return {"stage": 0, "status": "idle", "phase": definition["stages"][0]["idlePhase"],
            "attempt": 0, "deadline": None, "assignees": [], "chain": copy(definition["initialChain"]),
            "collections": collections, "assignments": {}, "outputs": outputs,
            "acceptedRequests": {}, "skips": 0}


def collect(definition, state, current, event, role):
    payload = event["payload"]
    if current is None or current["type"] != "collection" or role != "participant":
        return "rejected"
    artifact_id, artifact = payload.get(current["idField"]), payload.get(current["artifactField"])
    if type(artifact_id) is not int or not isinstance(artifact, str) or not artifact:
        return "rejected"
    pool = state["collections"][current["pool"]]
    if any(item["id"] == artifact_id and item["actor"] != event["actor"] for item in pool.values()):
        return "rejected"
    pool[event["actor"]] = {"id": artifact_id, "actor": event["actor"], "artifact": artifact}
    synchronize_time(definition, state, event["at"])
    return "accepted"


def remove(state, current, event, role):
    if current is None or current["type"] != "collection" or role != "host" or \
            event["at"] >= current["removeBefore"]:
        return "rejected"
    artifact_id = event["payload"].get(current["idField"])
    if type(artifact_id) is not int:
        return "rejected"
    pool = state["collections"][current["pool"]]
    for actor, item in list(pool.items()):
        if item["id"] == artifact_id:
            del pool[actor]
            return "accepted"
    return "rejected"


def assign(state, current, event, role):
    if current is None or current["type"] != "work":
        return "rejected"
    policy = current["assignment"]["policy"]
    if policy == "fixed_recipients":
        deadline = event["payload"].get("deadline")
        if role != "system" or state["status"] != "idle" or type(deadline) is not int or \
                deadline <= event["at"]:
            return "rejected"
        state["assignees"] = list(current["assignment"]["routes"][state["attempt"]])
        state["deadline"] = deadline
        state["status"] = "active"
        state["phase"] = current["activePhase"]
        return "accepted"
    if policy == "queue_lease":
        if role != "participant" or state["status"] != "idle":
            return "rejected"
        state["assignees"] = [event["actor"]]
        state["status"] = "active"
        state["phase"] = current["activePhase"]
        return "accepted"
    if policy == "balanced_artifacts":
        setting = current["assignment"]
        if setting["tie"] != "cover_offer_score_v1":
            raise ValueError(f"unsupported assignment tie-breaker: {setting['tie']}")
        pool = state["collections"][setting["pool"]]
        actor = event["actor"]
        if role != "participant" or actor not in pool:
            return "rejected"
        if actor in state["assignments"]:
            return "accepted"
        counts = {}
        for offer in state["assignments"].values():
            for artifact_id in offer["options"]:
                counts[artifact_id] = counts.get(artifact_id, 0) + 1
        candidates = [item for item in pool.values() if not setting["excludeSelf"] or item["actor"] != actor]
        if len(candidates) < setting["count"]:
            return "rejected"
        candidates.sort(key=lambda item: (counts.get(item["id"], 0),
                        score(setting["roundId"], int(actor), item["id"])))
        state["assignments"][actor] = {"options": [item["id"] for item in candidates[:setting["count"]]],
                                       "chosen": None}
        return "accepted"
    raise ValueError(f"unsupported assignment policy: {policy}")


def choose(state, current, event, role):
    if current is None or current["type"] != "work" or role != "participant":
        return "rejected"
    offer = state["assignments"].get(event["actor"])
    chosen = event["payload"].get(current["assignment"]["choiceField"])
    if offer is None or chosen not in offer["options"]:
        return "rejected"
    offer["chosen"] = chosen
    return "accepted"


def commit(definition, state, current, event, role):
    payload = event["payload"]
    request_id = payload.get("requestId")
    if isinstance(request_id, str) and request_id in state["acceptedRequests"]:
        prior = state["acceptedRequests"][request_id]
        same = prior == {"actor": event["actor"], "step": payload.get("step"),
                         "attempt": payload.get("attempt"), "media": payload.get("media"),
                         "artifact": payload.get("artifact")}
        return "replayed" if same else "rejected"
    if current is None or current["type"] != "work" or role != "participant":
        return "rejected"
    setting = current["commit"]
    allowed = setting["media"] if isinstance(setting["media"], list) else [setting["media"]]
    if payload.get("media") not in allowed or not isinstance(payload.get("artifact"), str) or \
            not payload["artifact"]:
        return "rejected"
    actor = event["actor"]
    if setting["mode"] == "first":
        if state["status"] != "active" or actor not in state["assignees"]:
            return "rejected"
        if setting.get("stepAttempt") and (payload.get("step") != state["stage"] or
            payload.get("attempt") != state["attempt"] or event["at"] > state["deadline"]):
            return "rejected"
        if setting.get("requestId") and (not isinstance(request_id, str) or not request_id):
            return "rejected"
        state["chain"].append({"actor": actor, "media": payload["media"],
                               "artifact": payload["artifact"]})
        if setting.get("requestId"):
            state["acceptedRequests"][request_id] = {"actor": actor, "step": payload["step"],
                                                       "attempt": payload["attempt"], "media": payload["media"],
                                                       "artifact": payload["artifact"]}
        advance_stage(definition, state)
        return "accepted"
    if setting["mode"] == "per_actor":
        offer = state["assignments"].get(actor)
        response_id = payload.get(setting["idField"])
        if offer is None or offer["chosen"] is None or not isinstance(response_id, str) or not response_id:
            return "rejected"
        cover_id = offer["chosen"]
        if not any(item["id"] == cover_id for pool in state["collections"].values()
                   for item in pool.values()):
            return "rejected"
        state["outputs"][setting["target"]][actor] = {"id": response_id, "actor": actor,
             setting["linkField"]: cover_id, "media": payload["media"], "artifact": payload["artifact"]}
        return "accepted"
    raise ValueError(f"unsupported completion mode: {setting['mode']}")


def expire(definition, state, current, event, role):
    if current is None or current["type"] != "work" or \
            current["assignment"]["policy"] != "fixed_recipients" or role != "system" or \
            state["status"] != "active" or event["at"] < state["deadline"] or \
            event["payload"].get("step") != state["stage"] or \
            event["payload"].get("attempt") != state["attempt"]:
        return "rejected"
    state["attempt"] += 1
    state["deadline"] = None
    state["assignees"] = []
    if state["attempt"] < len(current["assignment"]["routes"]):
        state["status"] = "idle"
        state["phase"] = current["idlePhase"]
    else:
        state["status"] = "stalled"
        state["phase"] = definition["stalledPhase"]
    return "accepted"


def release(state, current, event, role):
    if current is None or current["type"] != "work" or \
            current["assignment"]["policy"] != "queue_lease" or role != "participant" or \
            state["status"] != "active" or state["assignees"] != [event["actor"]]:
        return "rejected"
    state["assignees"] = []
    state["status"] = "idle"
    state["phase"] = current["idlePhase"]
    state["skips"] += 1
    return "accepted"


def apply(definition, state, event):
    role = definition["actors"].get(event["actor"])
    operation = definition["bindings"].get(event["type"])
    if role is None or operation is None or type(event.get("at")) is not int or \
            not isinstance(event.get("payload"), dict):
        return "rejected"
    synchronize_time(definition, state, event["at"])
    current = stage(definition, state)
    if operation == "advance":
        return "accepted" if role == "system" else "rejected"
    if operation == "collect":
        return collect(definition, state, current, event, role)
    if operation == "remove":
        return remove(state, current, event, role)
    if operation == "assign":
        return assign(state, current, event, role)
    if operation == "choose":
        return choose(state, current, event, role)
    if operation == "commit":
        return commit(definition, state, current, event, role)
    if operation == "expire":
        return expire(definition, state, current, event, role)
    if operation == "release":
        return release(state, current, event, role)
    raise ValueError(f"unknown operation: {operation}")


def view(definition, state, actor):
    role = definition["actors"].get(actor)
    if role is None:
        return "unknown_actor"
    result = {"phase": state["phase"], "stage": state["stage"], "attempt": state["attempt"]}
    for item in definition["stages"]:
        if item["type"] == "collection":
            pool = state["collections"][item["pool"]]
            if item.get("countViewField"):
                result[item["countViewField"]] = len(pool)
            if role == "participant" and actor in pool:
                result[item["viewField"]] = copy(pool[actor])
    if role in ("host", "system"):
        result["assignees"] = copy(state["assignees"])
        result["chain"] = copy(state["chain"])
        result["collections"] = copy(state["collections"])
        result["assignments"] = copy(state["assignments"])
        result["outputs"] = copy(state["outputs"])
    else:
        current = stage(definition, state)
        if current and current["type"] == "work" and state["status"] == "active" and \
                actor in state["assignees"] and state["chain"]:
            result["input"] = copy(state["chain"][-1])
            result["media"] = current["commit"]["media"]
            if state["deadline"] is not None:
                result["deadline"] = state["deadline"]
        if actor in state["assignments"]:
            offer = state["assignments"][actor]
            for item in definition["stages"]:
                if item["type"] == "work" and item["assignment"]["policy"] == "balanced_artifacts":
                    setting = item["assignment"]
                    pool = state["collections"][setting["pool"]]
                    result[setting["viewField"]] = [copy(next(entry for entry in pool.values()
                        if entry["id"] == artifact_id)) for artifact_id in offer["options"]]
                    if offer["chosen"] is not None:
                        result[setting["choiceViewField"]] = offer["chosen"]
        for item in definition["stages"]:
            if item["type"] == "work" and item["commit"]["mode"] == "per_actor":
                setting = item["commit"]
                if actor in state["outputs"][setting["target"]]:
                    result[setting["viewField"]] = copy(state["outputs"][setting["target"]][actor])
    if state["status"] == "done":
        if definition.get("reveal", {}).get("chain") == "on_done":
            result["chain"] = copy(state["chain"])
        if definition.get("reveal", {}).get("outputs") == "on_done":
            result["results"] = [copy(entry) for pool in state["outputs"].values() for entry in pool.values()]
    return result


def run(case_path, definition_path):
    fixture = json.loads(case_path.read_text())
    definition = json.loads(definition_path.read_text())
    missing = sorted(set(definition["requires"]) - set(fixture["capabilities"]))
    if missing:
        return {"status": "unsupported", "missing": missing}
    state = initialize(definition)
    outcomes = [apply(definition, state, event) for event in fixture["events"]]
    views = {actor: view(definition, state, actor) for actor in fixture["viewActors"]}
    return {"status": "ok", "state": state, "outcomes": outcomes, "views": views}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 run.py source-case.json composed-definition.json")
    print(json.dumps(run(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()), separators=(",", ":")))
