"""Independent Python interpreter for two experimental offer flows."""

import json
import sys
from pathlib import Path


def clone(value):
    return json.loads(json.dumps(value))


def assignment_score(round_id, user_id, artifact_id):
    value = ((round_id * 73856093) ^ (user_id * 19349663) ^ (artifact_id * 83492791)) & 0xFFFFFFFF
    value ^= value >> 16
    return value & 0xFFFFFFFF


def initial(definition):
    config = definition["config"]
    if definition["kind"] == "competitive_relay":
        media = config.get("mediaByStep")
        routes = config.get("routes")
        if not isinstance(media, list) or not isinstance(routes, list) or len(media) != len(routes) or not all(
            isinstance(attempts, list) and attempts and all(
                isinstance(pair, list) and len(pair) == 2 and pair[0] != pair[1] for pair in attempts
            ) for attempts in routes
        ):
            raise ValueError("invalid relay configuration")
        return {"phase": "ready", "step": 0, "attempt": 0, "deadline": None, "offers": [],
                "chain": [clone(config["initial"])], "acceptedRequests": {}}
    if definition["kind"] == "cover_response":
        if type(config.get("roundId")) is not int or type(config.get("minimumCovers")) is not int or \
                type(config.get("coverDeadline")) is not int or type(config.get("responseDeadline")) is not int or \
                config["responseDeadline"] <= config["coverDeadline"] or \
                not isinstance(config.get("participants"), list):
            raise ValueError("invalid cover-response configuration")
        return {"phase": "collecting_covers", "covers": {}, "offers": {}, "responses": {}}
    raise ValueError(f"unknown flow: {definition['kind']}")


def relay_event(state, event, config, role):
    payload = event.get("payload") or {}
    at = event.get("at")
    if event["type"] == "open" and role == "system" and state["phase"] == "ready" and \
            type(at) is int and type(payload.get("deadline")) is int and payload["deadline"] > at:
        state["offers"] = list(config["routes"][state["step"]][state["attempt"]])
        state["deadline"] = payload["deadline"]
        state["phase"] = "open"
        return "accepted"
    if event["type"] == "submit" and role == "participant" and isinstance(payload.get("requestId"), str) and \
            payload["requestId"]:
        request_id = payload["requestId"]
        if request_id in state["acceptedRequests"]:
            prior = state["acceptedRequests"][request_id]
            return "replayed" if prior == {"actor": event["actor"], "step": payload.get("step"),
                                           "attempt": payload.get("attempt"), "media": payload.get("media"),
                                           "artifact": payload.get("artifact")} else "rejected"
        if state["phase"] != "open" or event["actor"] not in state["offers"] or \
                payload.get("step") != state["step"] or payload.get("attempt") != state["attempt"] or \
                type(at) is not int or at > state["deadline"] or \
                payload.get("media") != config["mediaByStep"][state["step"]] or \
                not isinstance(payload.get("artifact"), str) or not payload["artifact"]:
            return "rejected"
        state["chain"].append({"actor": event["actor"], "media": payload["media"],
                               "artifact": payload["artifact"]})
        state["acceptedRequests"][request_id] = {"actor": event["actor"], "step": payload["step"],
                                                  "attempt": payload["attempt"], "media": payload["media"],
                                                  "artifact": payload["artifact"]}
        state["step"] += 1
        state["attempt"] = 0
        state["deadline"] = None
        state["offers"] = []
        state["phase"] = "done" if state["step"] == len(config["mediaByStep"]) else "ready"
        return "accepted"
    if event["type"] == "timeout" and role == "system" and state["phase"] == "open" and \
            type(at) is int and at >= state["deadline"] and \
            payload.get("step") == state["step"] and payload.get("attempt") == state["attempt"]:
        state["attempt"] += 1
        state["deadline"] = None
        state["offers"] = []
        state["phase"] = "ready" if state["attempt"] < len(config["routes"][state["step"]]) else "stalled"
        return "accepted"
    return "rejected"


def cover_phase(state, config, at):
    if state["phase"] == "complete" or at >= config["responseDeadline"]:
        return "complete"
    return "collecting_responses" if at >= config["coverDeadline"] and \
        len(state["covers"]) >= config["minimumCovers"] else "collecting_covers"


def cover_event(state, event, config, role):
    payload = event.get("payload") or {}
    at = event.get("at")
    if type(at) is not int:
        return "rejected"
    state["phase"] = cover_phase(state, config, at)
    actor = event["actor"]
    if event["type"] == "tick" and role == "system":
        return "accepted"
    if event["type"] == "submit_cover" and role == "participant" and actor in config["participants"] and \
            state["phase"] == "collecting_covers" and type(payload.get("coverId")) is int and \
            isinstance(payload.get("artifact"), str) and payload["artifact"]:
        if any(cover["id"] == payload["coverId"] and cover["actor"] != actor
               for cover in state["covers"].values()):
            return "rejected"
        state["covers"][actor] = {"id": payload["coverId"], "actor": actor,
                                   "artifact": payload["artifact"]}
        state["phase"] = cover_phase(state, config, at)
        return "accepted"
    if event["type"] == "remove_cover" and role == "host" and at < config["coverDeadline"] and \
            type(payload.get("coverId")) is int:
        for participant, cover in list(state["covers"].items()):
            if cover["id"] == payload["coverId"]:
                del state["covers"][participant]
                return "accepted"
        return "rejected"
    if event["type"] == "request_offer" and role == "participant" and \
            state["phase"] == "collecting_responses" and actor in state["covers"]:
        if actor in state["offers"]:
            return "accepted"
        counts = {}
        for offer in state["offers"].values():
            for cover_id in offer["options"]:
                counts[cover_id] = counts.get(cover_id, 0) + 1
        candidates = [cover for cover in state["covers"].values() if cover["actor"] != actor]
        if len(candidates) < 2:
            return "rejected"
        candidates.sort(key=lambda cover: (counts.get(cover["id"], 0),
                          assignment_score(config["roundId"], int(actor), cover["id"])))
        state["offers"][actor] = {"options": [candidates[0]["id"], candidates[1]["id"]],
                                  "chosen": None}
        return "accepted"
    if event["type"] == "choose_cover" and role == "participant" and \
            state["phase"] == "collecting_responses" and actor in state["offers"] and \
            payload.get("coverId") in state["offers"][actor]["options"]:
        state["offers"][actor]["chosen"] = payload["coverId"]
        return "accepted"
    if event["type"] == "submit_response" and role == "participant" and \
            state["phase"] == "collecting_responses" and actor in state["offers"] and \
            state["offers"][actor]["chosen"] is not None and \
            payload.get("media") in config["responseMedia"] and \
            isinstance(payload.get("responseId"), str) and payload["responseId"] and \
            isinstance(payload.get("artifact"), str) and payload["artifact"]:
        cover_id = state["offers"][actor]["chosen"]
        if not any(cover["id"] == cover_id for cover in state["covers"].values()):
            return "rejected"
        state["responses"][actor] = {"id": payload["responseId"], "actor": actor,
                                     "coverId": cover_id, "media": payload["media"],
                                     "artifact": payload["artifact"]}
        return "accepted"
    return "rejected"


def view(definition, state, actor):
    role = definition["actors"].get(actor)
    if role is None:
        return "unknown_actor"
    if definition["kind"] == "competitive_relay":
        result = {"phase": state["phase"], "step": state["step"], "attempt": state["attempt"]}
        if role == "system":
            result["chain"] = clone(state["chain"])
            result["offers"] = list(state["offers"])
        if state["phase"] == "open" and actor in state["offers"]:
            result["input"] = clone(state["chain"][-1])
            result["media"] = definition["config"]["mediaByStep"][state["step"]]
            result["deadline"] = state["deadline"]
        if state["phase"] == "done" and role == "participant":
            result["chain"] = clone(state["chain"])
        return result
    result = {"phase": state["phase"], "coverCount": len(state["covers"])}
    if role in ("host", "system"):
        result["covers"] = clone(state["covers"])
        result["offers"] = clone(state["offers"])
        result["responses"] = clone(state["responses"])
    elif role == "participant":
        if actor in state["covers"]:
            result["cover"] = clone(state["covers"][actor])
        if actor in state["offers"]:
            ids = state["offers"][actor]["options"]
            result["offeredCovers"] = [clone(next(cover for cover in state["covers"].values()
                                                  if cover["id"] == cover_id)) for cover_id in ids]
            if state["offers"][actor]["chosen"] is not None:
                result["chosenCoverId"] = state["offers"][actor]["chosen"]
        if actor in state["responses"]:
            result["response"] = clone(state["responses"][actor])
    if state["phase"] == "complete":
        result["results"] = clone(list(state["responses"].values()))
    return result


def run(case_path, stop_at=None, resume_path=None):
    fixture = json.loads(case_path.read_text())
    definition = json.loads((case_path.parent / fixture["definition"]).read_text())
    missing = sorted(set(definition["requires"]) - set(fixture["capabilities"]))
    if missing:
        return {"status": "unsupported", "missing": missing}
    snapshot = json.loads(resume_path.read_text()) if resume_path else None
    start_at = snapshot["nextIndex"] if snapshot else 0
    if type(start_at) is not int or start_at < 0 or start_at > len(fixture["events"]) or \
            (stop_at is not None and (type(stop_at) is not int or stop_at < start_at or
                                      stop_at > len(fixture["events"]))):
        raise ValueError("invalid event range")
    state = snapshot["state"] if snapshot else initial(definition)
    outcomes = snapshot["outcomes"] if snapshot else []
    if not isinstance(outcomes, list) or len(outcomes) != start_at:
        raise ValueError("invalid snapshot")
    end_at = stop_at if stop_at is not None else len(fixture["events"])
    for event in fixture["events"][start_at:end_at]:
        role = definition["actors"].get(event["actor"])
        outcome = relay_event(state, event, definition["config"], role) if \
            definition["kind"] == "competitive_relay" else \
            cover_event(state, event, definition["config"], role)
        outcomes.append(outcome)
    if stop_at is not None:
        return {"status": "checkpoint", "nextIndex": end_at, "state": state, "outcomes": outcomes}
    views = {actor: view(definition, state, actor) for actor in fixture["viewActors"]}
    return {"status": "ok", "state": state, "outcomes": outcomes, "views": views}


if __name__ == "__main__":
    if len(sys.argv) not in (2, 4):
        raise SystemExit("usage: python3 run.py case.json [--prefix count | --resume snapshot.json]")
    options = {}
    if len(sys.argv) == 4:
        if sys.argv[2] == "--prefix":
            options = {"stop_at": int(sys.argv[3])}
        elif sys.argv[2] == "--resume":
            options = {"resume_path": Path(sys.argv[3]).resolve()}
        else:
            raise SystemExit("unknown option")
    print(json.dumps(run(Path(sys.argv[1]).resolve(), **options),
                     separators=(",", ":")))
