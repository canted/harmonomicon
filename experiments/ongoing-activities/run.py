"""Independent Python interpreter for two experimental ongoing-activity shapes."""

import json
import sys
from pathlib import Path


def copy(value):
    return json.loads(json.dumps(value))


def phase(definition, at):
    calendar = definition["calendar"]
    if at < calendar["registrationEnds"]:
        return "registration"
    if at < calendar["submissionsEnd"]:
        return "making"
    if at < calendar["reviewsEnd"]:
        return "review"
    return "reveal"


def initialize(definition):
    if definition["calendar"]["kind"] == "windows":
        return {"now": 0, "phase": phase(definition, 0), "teams": {}, "progress": [],
                "responses": [], "finals": {}, "reviews": []}
    return {"now": 0, "phase": "waiting", "day": 0, "deadline": None, "history": {}}


def valid_id(value):
    return isinstance(value, str) and bool(value)


def valid_integer(value):
    return type(value) is int and abs(value) <= 9007199254740991


def team_of(state, actor):
    return next((name for name, members in state["teams"].items() if actor in members), None)


def jam_event(definition, state, event, operation, role):
    actor, payload = event["actor"], event["payload"]
    if operation == "tick":
        return "accepted" if role == "system" else "rejected"
    if operation == "register_team":
        name, members = payload.get("team"), payload.get("members")
        if role != "host" or state["phase"] != "registration" or not valid_id(name) or \
                name in state["teams"] or not isinstance(members, list) or not members or \
                not all(valid_id(member) for member in members) or \
                len(members) != len(set(members)) or any(
                    definition["actors"].get(member) != "participant" or team_of(state, member)
                    for member in members):
            return "rejected"
        state["teams"][name] = list(members)
        return "accepted"
    team = team_of(state, actor)
    if role != "participant" or team is None:
        return "rejected"
    if operation == "post_progress":
        post_id, artifact, audience = payload.get("id"), payload.get("artifact"), payload.get("audience")
        if state["phase"] != "making" or not valid_id(post_id) or not valid_id(artifact) or \
                audience not in definition["progressAudiences"] or \
                any(post["id"] == post_id for post in state["progress"]):
            return "rejected"
        state["progress"].append({"id": post_id, "actor": actor, "team": team,
                                  "artifact": artifact, "audience": audience})
        return "accepted"
    if operation == "respond":
        response_id, post_id, text = payload.get("id"), payload.get("postId"), payload.get("text")
        post = next((item for item in state["progress"] if item["id"] == post_id), None)
        if state["phase"] != "making" or not valid_id(response_id) or not valid_id(text) or \
                post is None or (post["audience"] == "team" and post["team"] != team) or \
                any(item["id"] == response_id for item in state["responses"]):
            return "rejected"
        state["responses"].append({"id": response_id, "postId": post_id, "actor": actor,
                                   "text": text})
        return "accepted"
    if operation == "submit_final":
        artifact = payload.get("artifact")
        if state["phase"] != "making" or not valid_id(artifact) or team in state["finals"]:
            return "rejected"
        state["finals"][team] = {"team": team, "actor": actor, "artifact": artifact}
        return "accepted"
    if operation == "review":
        review_id, target, text = payload.get("id"), payload.get("team"), payload.get("text")
        if state["phase"] != "review" or not valid_id(review_id) or not valid_id(target) or \
                not valid_id(text) or \
                target not in state["finals"] or target == team or \
                any(item["id"] == review_id for item in state["reviews"]):
            return "rejected"
        state["reviews"].append({"id": review_id, "team": target, "actor": actor, "text": text})
        return "accepted"
    return "rejected"


def daily_event(definition, state, event, operation, role):
    actor, payload, at = event["actor"], event["payload"], event["at"]
    if operation == "open_day":
        day, deadline = payload.get("day"), payload.get("deadline")
        if role != "system" or state["phase"] != "waiting" or not valid_integer(day) or \
                day != state["day"] + 1 or not valid_integer(deadline) or deadline <= at:
            return "rejected"
        state["day"], state["deadline"], state["phase"] = day, deadline, "open"
        state["history"][str(day)] = {"status": {
            name: "pending" for name, kind in definition["actors"].items() if kind == "participant"},
            "entries": {}}
        return "accepted"
    if operation == "submit_day":
        artifact = payload.get("artifact")
        if role != "participant" or state["phase"] != "open" or at >= state["deadline"] or \
                not valid_id(artifact):
            return "rejected"
        current = state["history"][str(state["day"])]
        if actor in current["entries"]:
            return "rejected"
        current["entries"][actor] = {"actor": actor, "artifact": artifact}
        current["status"][actor] = "complete"
        return "accepted"
    if operation == "close_day":
        if role != "system" or state["phase"] != "open" or at < state["deadline"]:
            return "rejected"
        current = state["history"][str(state["day"])]
        current["status"] = {name: "missed" if status == "pending" else status
                             for name, status in current["status"].items()}
        state["phase"], state["deadline"] = "waiting", None
        return "accepted"
    return "rejected"


def apply(definition, state, event):
    if not isinstance(event, dict) or not valid_integer(event.get("at")) or \
            event["at"] < state["now"] or not isinstance(event.get("payload"), dict) or \
            not valid_id(event.get("actor")) or not valid_id(event.get("type")):
        return "rejected"
    role = definition["actors"].get(event.get("actor"))
    operation = definition["bindings"].get(event.get("type"))
    if role is None or operation is None:
        return "rejected"
    state["now"] = event["at"]
    if definition["calendar"]["kind"] == "windows":
        state["phase"] = phase(definition, event["at"])
        return jam_event(definition, state, event, operation, role)
    return daily_event(definition, state, event, operation, role)


def view(definition, state, actor):
    role = definition["actors"].get(actor)
    if role is None:
        return "unknown_actor"
    if definition["calendar"]["kind"] == "daily":
        history = {}
        for day, item in state["history"].items():
            source_entries = item["entries"]
            entries = source_entries if role in ("system", "host") or \
                definition["contentAudience"] == "participants" else \
                {actor: source_entries[actor]} if actor in source_entries else {}
            history[day] = {"status": copy(item["status"]), "entries": copy(entries)}
        return {"phase": state["phase"], "day": state["day"], "history": history}
    if role in ("system", "host"):
        return copy(state)
    team = team_of(state, actor)
    visible_posts = [post for post in state["progress"] if
                     post["audience"] == "participants" or post["team"] == team]
    post_ids = {post["id"] for post in visible_posts}
    finals = {name: item for name, item in state["finals"].items() if
              state["phase"] in ("review", "reveal") or name == team}
    reviews = [item for item in state["reviews"] if state["phase"] == "reveal" or
               item["actor"] == actor]
    return {"phase": state["phase"], "teams": copy(state["teams"]),
            "progress": copy(visible_posts),
            "responses": copy([item for item in state["responses"] if item["postId"] in post_ids]),
            "finals": copy(finals), "reviews": copy(reviews)}


def run(case_path, definition_path):
    fixture, definition = json.loads(case_path.read_text()), json.loads(definition_path.read_text())
    missing = sorted(set(definition["requires"]) - set(fixture["capabilities"]))
    if missing:
        return {"status": "unsupported", "missing": missing}
    state = initialize(definition)
    outcomes = [apply(definition, state, event) for event in fixture["events"]]
    return {"status": "ok", "state": state, "outcomes": outcomes,
            "views": {actor: view(definition, state, actor) for actor in fixture["viewActors"]}}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 run.py case.json definition.json")
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), separators=(",", ":")))
