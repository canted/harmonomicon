"""Independent Python interpreter for the experimental JSON activity contract."""

import copy
import json
import sys
from pathlib import Path

MISSING = object()


def at(root, dotted):
    current = root
    for key in dotted.split("."):
        if not isinstance(current, dict) or key not in current:
            return MISSING
        current = current[key]
    return current


def value(expr, state, event):
    if isinstance(expr, dict) and set(expr) == {"ref"}:
        pieces = expr["ref"].split(".")
        if len(pieces) < 2 or pieces[0] not in ("state", "event"):
            return MISSING
        return at(state if pieces[0] == "state" else event, ".".join(pieces[1:]))
    return expr


def equal(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def condition(rule, state, event):
    left = value(rule.get("left"), state, event)
    right = value(rule.get("right"), state, event)
    if left is MISSING or right is MISSING:
        return False
    op = rule["op"]
    if op == "eq":
        return equal(left, right)
    if op == "ne":
        return not equal(left, right)
    if op in ("lt", "lte", "gt", "gte"):
        if type(left) not in (int, float) or type(right) not in (int, float):
            return False
        return {"lt": left < right, "lte": left <= right, "gt": left > right, "gte": left >= right}[op]
    if op == "has_key":
        return isinstance(left, dict) and isinstance(right, str) and right in left
    if op == "lacks_key":
        return isinstance(left, dict) and isinstance(right, str) and right not in left
    if op in ("length_eq", "length_lt", "length_gte"):
        if not isinstance(left, list) or type(right) not in (int, float):
            return False
        return {"length_eq": len(left) == right, "length_lt": len(left) < right,
                "length_gte": len(left) >= right}[op]
    return False


def destination(state, dotted):
    pieces = dotted.split(".")
    parent = state if len(pieces) == 1 else at(state, ".".join(pieces[:-1]))
    if not isinstance(parent, dict) or pieces[-1] not in parent:
        raise ValueError("invalid path")
    return parent, pieces[-1]


def apply(action, state, event, actors):
    parent, key = destination(state, action["path"])
    operand = value(action.get("value"), state, event)
    if operand is MISSING:
        raise ValueError("missing value")
    op = action["op"]
    if op == "set":
        parent[key] = copy.deepcopy(operand)
    elif op == "add":
        if type(parent[key]) not in (int, float) or type(operand) not in (int, float):
            raise ValueError("numeric add")
        parent[key] += operand
    elif op == "append":
        if not isinstance(parent[key], list):
            raise ValueError("array append")
        parent[key].append(copy.deepcopy(operand))
    elif op == "put":
        map_key = value(action["key"], state, event)
        if not isinstance(parent[key], dict) or not isinstance(map_key, str):
            raise ValueError("object put")
        parent[key][map_key] = copy.deepcopy(operand)
    elif op == "partition":
        if not isinstance(operand, dict) or not isinstance(action.get("sizes"), list):
            raise ValueError("invalid partition")
        groups = list(operand.values())
        if any(not isinstance(group, list) or len(group) not in action["sizes"] for group in groups):
            raise ValueError("invalid group sizes")
        actual = [member for group in groups for member in group]
        expected = [actor for actor, role in actors.items() if role == "participant"]
        if len(actual) != len(expected) or len(set(actual)) != len(actual) or set(actual) != set(expected):
            raise ValueError("partition mismatch")
        parent[key] = copy.deepcopy(operand)
    else:
        raise ValueError("unknown action")


def run(fixture_path):
    fixture = json.loads(fixture_path.read_text())
    definition = json.loads((fixture_path.parent / fixture["definition"]).read_text())
    missing = sorted(set(definition["requires"]) - set(fixture["capabilities"]))
    if missing:
        return {"status": "unsupported", "missing": missing}
    state = copy.deepcopy(definition["initial"])
    outcomes = []
    for event in fixture["events"]:
        role = definition["actors"].get(event["actor"])
        matches = [transition for transition in definition["transitions"]
                   if transition["on"] == event["type"] and role in transition["by"]
                   and all(condition(item, state, event) for item in transition.get("if", []))]
        if len(matches) != 1:
            outcomes.append("rejected")
            continue
        draft = copy.deepcopy(state)
        try:
            for action in matches[0]["do"]:
                apply(action, draft, event, definition["actors"])
        except (ValueError, TypeError, KeyError):
            outcomes.append("rejected")
        else:
            state = draft
            outcomes.append("accepted")
    views = {}
    for actor in fixture.get("viewActors", []):
        role = definition["actors"].get(actor)
        if role is None:
            views[actor] = "unknown_actor"
            continue
        context = {"actor": actor}
        projection = {}
        for rule in definition["views"]:
            if role in rule["by"] and all(condition(item, state, context) for item in rule.get("if", [])):
                projection[rule["field"]] = copy.deepcopy(state[rule["field"]])
        views[actor] = projection
    return {"status": "ok", "state": state, "outcomes": outcomes, "views": views}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 run.py fixture.json")
    print(json.dumps(run(Path(sys.argv[1]).resolve()), separators=(",", ":")))
