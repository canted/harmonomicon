"""Python implementation of balanced_artifacts_exact32@1."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MASK = (1 << 32) - 1
MAX_ID = (1 << 64) - 1


def valid_id(value):
    return isinstance(value, str) and re.fullmatch(r"(?:0|[1-9][0-9]*)", value) is not None and \
        int(value) <= MAX_ID


def score(round_id, recipient, artifact):
    x = ((round_id * 73856093) & MASK) ^ ((int(recipient) * 19349663) & MASK) ^ \
        ((int(artifact) * 83492791) & MASK)
    return x ^ (x >> 16)


def load_policy():
    manifest = json.loads((ROOT / "policy.json").read_text())
    plan = json.loads((ROOT / manifest["basePlan"]).resolve().read_text())
    assignment = next(item["assignment"] for item in plan["stages"]
                      if item["type"] == "work" and item["assignment"]["policy"] == "balanced_artifacts")
    assert assignment["tie"] == "cover_offer_score_v1" and assignment["excludeSelf"] is True
    assert type(assignment["roundId"]) is int and 0 <= assignment["roundId"] <= MAX_ID
    return manifest, assignment


def validate_covers(covers):
    if not isinstance(covers, list) or not all(isinstance(item, dict) and
            valid_id(item.get("id")) and valid_id(item.get("owner")) for item in covers):
        raise ValueError("covers must have canonical unsigned IDs")
    if len({item["id"] for item in covers}) != len(covers) or \
            len({item["owner"] for item in covers}) != len(covers):
        raise ValueError("artifact IDs and owners must be unique")


def request(state, covers, setting, event):
    if not isinstance(event, dict):
        return {"status": "rejected"}
    request_id, recipient = event.get("requestId"), event.get("recipient")
    if not isinstance(request_id, str) or not request_id or not valid_id(recipient):
        return {"status": "rejected"}
    ledger, offers = state["requestLedger"], state["offers"]
    if request_id in ledger:
        if ledger[request_id] != recipient:
            return {"status": "rejected"}
        return {"status": "replayed", "options": list(offers[recipient])}
    if recipient in offers:
        ledger[request_id] = recipient
        return {"status": "existing", "options": list(offers[recipient])}
    if not any(item["owner"] == recipient for item in covers):
        return {"status": "rejected"}
    candidates = [item for item in covers if item["owner"] != recipient]
    if len(candidates) < setting["count"]:
        return {"status": "rejected"}
    counts = {}
    for saved in offers.values():
        for artifact_id in saved:
            counts[artifact_id] = counts.get(artifact_id, 0) + 1
    candidates.sort(key=lambda item: (counts.get(item["id"], 0),
        score(setting["roundId"], recipient, item["id"]), int(item["id"])))
    options = [item["id"] for item in candidates[:setting["count"]]]
    offers[recipient] = options
    ledger[request_id] = recipient
    return {"status": "accepted", "options": list(options)}


def run(case_path, snapshot_path=None, stop_at=None):
    case = json.loads(case_path.read_text())
    manifest, setting = load_policy()
    missing = sorted(set(manifest["requires"]) - set(case["capabilities"]))
    if missing:
        return {"status": "unsupported", "missing": missing}
    validate_covers(case["covers"])
    snapshot = json.loads(snapshot_path.read_text()) if snapshot_path else None
    if snapshot and snapshot["policy"] != manifest["policy"]:
        raise ValueError("checkpoint policy mismatch")
    state = snapshot["state"] if snapshot else {"offers": {}, "requestLedger": {}}
    outcomes = snapshot["outcomes"] if snapshot else []
    start = snapshot["nextIndex"] if snapshot else 0
    end = len(case["requests"]) if stop_at is None else stop_at
    if not 0 <= start <= end <= len(case["requests"]):
        raise ValueError("invalid checkpoint index")
    for event in case["requests"][start:end]:
        outcomes.append(request(state, case["covers"], setting, event))
    if stop_at is not None:
        return {"status": "checkpoint", "policy": manifest["policy"], "nextIndex": end,
                "state": state, "outcomes": outcomes}
    return {"status": "ok", "state": state, "outcomes": outcomes}


if __name__ == "__main__":
    if not 2 <= len(sys.argv) <= 4:
        raise SystemExit("usage: python3 run.py case.json [snapshot.json|-] [stopAt]")
    snapshot_arg = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "-" else None
    stop_arg = int(sys.argv[3]) if len(sys.argv) > 3 else None
    print(json.dumps(run(Path(sys.argv[1]), snapshot_arg, stop_arg), separators=(",", ":")))
