"""Independent Python interpreter for two named activity mechanisms."""

import json
import sys
from pathlib import Path


def run(case_path):
    fixture = json.loads(case_path.read_text())
    definition = json.loads((case_path.parent / fixture["definition"]).read_text())
    missing = sorted(set(definition["requires"]) - set(fixture["capabilities"]))
    if missing:
        return {"status": "unsupported", "missing": missing}
    actors, config, kind = definition["actors"], definition["config"], definition["kind"]
    if kind == "handoff":
        if not isinstance(config.get("participants"), list) or config.get("start") not in config["participants"] or \
                type(config.get("steps")) is not int or config["steps"] < 1 or not \
                ((config.get("mode") == "contribute" and config.get("reveal") == "end") or
                 (config.get("mode") == "unlock" and config.get("reveal") == "each" and
                  isinstance(config.get("items"), list) and len(config["items"]) == config["steps"])):
            raise ValueError("unsupported handoff configuration")
    elif kind == "collection":
        if not isinstance(config.get("participants"), list) or config.get("schedule") not in ("daily", "one_shot") or \
                config.get("viewGate") not in ("after_own", "at_close") or \
                config.get("latePolicy") not in ("mark", "accept", "reject"):
            raise ValueError("unsupported collection configuration")
    if kind == "handoff":
        state = {"phase": "active", "current": config["start"], "index": 0, "entries": [], "guide": ""}
    elif kind == "collection":
        state = {"phase": "waiting", "occurrence": 0, "nextOccurrence": 1, "deadline": 0,
                 "posts": {}, "late": {}}
    else:
        raise ValueError("unknown mechanism")
    outcomes = []
    for event in fixture["events"]:
        role = actors.get(event["actor"])
        payload = event["payload"]
        accepted = False
        if kind == "handoff" and event["type"] == "advance" and role == "participant" and \
                state["phase"] == "active" and event["actor"] == state["current"]:
            last = state["index"] == config["steps"] - 1
            next_actor = payload.get("next")
            next_ok = last or (isinstance(next_actor, str) and next_actor in config["participants"]
                               and next_actor != event["actor"])
            item_ok = config["mode"] == "unlock" or isinstance(payload.get("item"), str)
            guide_ok = config["mode"] == "unlock" or last or isinstance(payload.get("guide"), str)
            if next_ok and item_ok and guide_ok:
                item = config["items"][state["index"]] if config["mode"] == "unlock" else payload["item"]
                state["entries"].append(item)
                state["index"] += 1
                state["guide"] = "" if last or config["mode"] == "unlock" else payload["guide"]
                state["current"] = None if last else next_actor
                if last:
                    state["phase"] = "done"
                accepted = True
        elif kind == "collection":
            if event["type"] == "open" and role in ("host", "system") and \
                    type(payload.get("occurrence")) is int and type(payload.get("deadline")) is int and \
                    payload["occurrence"] == state["nextOccurrence"] and \
                    (config["schedule"] == "daily" or payload["occurrence"] == 1):
                state = {"phase": "open", "occurrence": payload["occurrence"],
                         "nextOccurrence": payload["occurrence"] + 1, "deadline": payload["deadline"],
                         "posts": {}, "late": {}}
                accepted = True
            elif event["type"] == "submit" and role == "participant" and \
                    event["actor"] in config["participants"] and state["phase"] == "open" and \
                    event["actor"] not in state["posts"] and isinstance(payload.get("artifact"), str) and \
                    type(event.get("at")) is int:
                late = event["at"] > state["deadline"]
                if not late or config["latePolicy"] != "reject":
                    state["posts"][event["actor"]] = payload["artifact"]
                    state["late"][event["actor"]] = late
                    accepted = True
            elif event["type"] == "close" and role in ("host", "system") and state["phase"] == "open":
                state["phase"] = "closed"
                accepted = True
        outcomes.append("accepted" if accepted else "rejected")
    views = {}
    for actor in fixture["viewActors"]:
        role = actors.get(actor)
        if role is None:
            views[actor] = "unknown_actor"
        elif kind == "handoff":
            view = {"phase": state["phase"], "current": state["current"], "index": state["index"]}
            if config["mode"] == "contribute" and state["phase"] == "active" and \
                    actor == state["current"] and state["index"] > 0:
                view["guide"] = state["guide"]
            if config["reveal"] == "each" or state["phase"] == "done":
                view["entries"] = list(state["entries"])
            views[actor] = view
        else:
            view = {"phase": state["phase"], "occurrence": state["occurrence"]}
            allowed = role in ("host", "system") or (role == "participant" and actor in config["participants"]
                       and ((config["viewGate"] == "after_own" and actor in state["posts"])
                            or (config["viewGate"] == "at_close" and state["phase"] == "closed")))
            if allowed:
                view["posts"] = dict(state["posts"])
                view["late"] = dict(state["late"])
            views[actor] = view
    return {"status": "ok", "state": state, "outcomes": outcomes, "views": views}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 run.py case.json")
    print(json.dumps(run(Path(sys.argv[1]).resolve()), separators=(",", ":")))
