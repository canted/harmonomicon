#!/usr/bin/env python3
"""Local 0.1 host: Python HTTP server, independent SQLite state, and deadline worker."""

import argparse
import hashlib
import json
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = ROOT / "format/0.1/examples"
PACKAGE_FILES = list(PACKAGE_DIR.glob("*.json"))
PACKAGES = {package["id"]: package for package in (json.loads(p.read_text()) for p in PACKAGE_FILES)}
PACKAGE_HASHES = {json.loads(p.read_text())["id"]: hashlib.sha256(p.read_bytes()).hexdigest() for p in PACKAGE_FILES}
CAPABILITIES = {"identity@1", "serial_events@1", "durable_state@1", "private_views@1", "clock@1", "text@1"}
CONTRACTS = {"timed_collection@1", "sequential_handoff@1"}
SAFE_MAX = 9007199254740991


def valid_time(value):
    return type(value) is int and 0 <= value <= SAFE_MAX


def valid_text(value):
    return type(value) is str and bool(value)


def token_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def db_connect(path):
    conn = sqlite3.connect(path, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def initialize_db(path):
    with db_connect(path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            INSERT OR IGNORE INTO meta(key,value) VALUES ('clock','0');
            CREATE TABLE IF NOT EXISTS instances (
                id TEXT PRIMARY KEY, package_id TEXT NOT NULL, state_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tokens (
                instance_id TEXT NOT NULL, token_hash TEXT NOT NULL, actor TEXT NOT NULL,
                PRIMARY KEY(instance_id,token_hash)
            );
            CREATE TABLE IF NOT EXISTS event_log (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, instance_id TEXT NOT NULL,
                event_id TEXT, type TEXT NOT NULL, actor TEXT NOT NULL,
                at INTEGER NOT NULL, payload_json TEXT NOT NULL,
                UNIQUE(instance_id,event_id)
            );
        """)


def transact(path, operation):
    conn = db_connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        result = operation(conn)
        conn.execute("COMMIT")
        return result
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def clock(conn):
    return int(conn.execute("SELECT value FROM meta WHERE key='clock'").fetchone()["value"])


def write_state(conn, instance_id, state):
    conn.execute("UPDATE instances SET state_json=? WHERE id=?", (json.dumps(state, sort_keys=True), instance_id))


def append_event(conn, instance_id, event_id, event_type, actor, at, payload):
    conn.execute(
        "INSERT INTO event_log(instance_id,event_id,type,actor,at,payload_json) VALUES (?,?,?,?,?,?)",
        (instance_id, event_id, event_type, actor, at, json.dumps(payload, sort_keys=True)),
    )


def reconcile(conn, instance_id, state, now):
    if state["contract"] != "timed_collection@1":
        return
    changed = False
    if state["phase"] == "waiting" and now >= state["opensAt"]:
        state["phase"] = "open"
        append_event(conn, instance_id, None, "tick", "system", state["opensAt"], {})
        changed = True
    if state["phase"] == "open" and now >= state["closesAt"]:
        state["phase"] = "closed"
        append_event(conn, instance_id, None, "tick", "system", state["closesAt"], {})
        changed = True
    if changed:
        write_state(conn, instance_id, state)


def semantic_view(state, actor):
    entries = state["entries"]
    if state["contract"] == "timed_collection@1":
        view = {"phase": state["phase"], "submissionCount": len(entries)}
    else:
        index = state["index"]
        done = state["phase"] == "complete"
        view = {"phase": state["phase"], "step": min(index + 1, len(state["route"])),
                "currentActor": None if done else state["route"][index]}
    if actor in state["participants"]:
        own = next((entry for entry in entries if entry["actor"] == actor), None)
        if own is not None:
            view["own"] = own
    if state["contract"] == "timed_collection@1":
        if state["phase"] == "closed":
            view["entries"] = entries
    elif state["phase"] == "complete":
        view["entries"] = entries
    elif actor == state["route"][state["index"]]:
        view["input"] = state["prompt"] if state["index"] == 0 else entries[-1]["value"]
    return view


def create_instance(conn, body, disabled_capabilities, disabled_contracts):
    if type(body) is not dict or not {"instanceId", "packageId", "organizer", "participants", "tokens"} <= set(body):
        return 400, {"status": "invalid_instance"}
    package = PACKAGES.get(body["packageId"])
    if package is None or package.get("format") != "harmonomicon.activity-package/0.1":
        return 400, {"status": "invalid_package"}
    contract = package["behavior"]["contract"]
    available = CAPABILITIES - disabled_capabilities
    missing = sorted(set(package["requires"]) - available)
    if contract not in CONTRACTS - disabled_contracts:
        missing.append("behavior:" + contract)
    if missing:
        return 200, {"status": "unsupported", "missing": sorted(missing)}
    instance_id = body["instanceId"]
    participants = body["participants"]
    organizer = body["organizer"]
    tokens = body["tokens"]
    bounds = package["participants"]
    if not (valid_text(instance_id) and valid_text(organizer) and organizer != "system"
            and type(participants) is list and bounds["min"] <= len(participants) <= bounds["max"]
            and all(valid_text(p) and p != "system" for p in participants)
            and len(set(participants)) == len(participants) and organizer not in participants
            and type(tokens) is dict and set(tokens) == {organizer, *participants}
            and all(valid_text(t) for t in tokens.values()) and len(set(tokens.values())) == len(tokens)):
        return 400, {"status": "invalid_instance"}
    now = clock(conn)
    prompt = body.get("prompt", package["content"]["prompt"])
    if not valid_text(prompt) or ("prompt" in body and not package["behavior"]["allowPromptOverride"]):
        return 400, {"status": "invalid_instance"}
    state = {"packageVersion": package["version"], "packageHash": PACKAGE_HASHES[package["id"]],
             "contract": contract, "medium": package["behavior"]["medium"], "organizer": organizer,
             "participants": participants, "prompt": prompt, "entries": [], "index": 0, "lastAt": now}
    if contract == "timed_collection@1":
        opens_at, closes_at = body.get("opensAt"), body.get("closesAt")
        if not (valid_time(opens_at) and valid_time(closes_at) and now <= opens_at < closes_at):
            return 400, {"status": "invalid_instance"}
        state.update({"opensAt": opens_at, "closesAt": closes_at,
                      "phase": "waiting" if now < opens_at else "open"})
    else:
        route = body.get("route")
        if not (type(route) is list and len(route) == package["behavior"]["steps"]
                and len(route) == len(set(route)) and set(route) == set(participants)):
            return 400, {"status": "invalid_instance"}
        state.update({"route": route, "phase": "active"})
    try:
        conn.execute("INSERT INTO instances(id,package_id,state_json) VALUES (?,?,?)",
                     (instance_id, package["id"], json.dumps(state, sort_keys=True)))
    except sqlite3.IntegrityError:
        return 409, {"status": "already_exists"}
    for actor, token in tokens.items():
        conn.execute("INSERT INTO tokens(instance_id,token_hash,actor) VALUES (?,?,?)",
                     (instance_id, token_hash(token), actor))
    return 201, {"status": "created", "instanceId": instance_id}


def actor_for(conn, instance_id, authorization):
    if not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    row = conn.execute("SELECT actor FROM tokens WHERE instance_id=? AND token_hash=?",
                       (instance_id, token_hash(token))).fetchone()
    return row["actor"] if row else None


def submit_event(conn, instance_id, actor, body):
    row = conn.execute("SELECT state_json FROM instances WHERE id=?", (instance_id,)).fetchone()
    if row is None:
        return 404, {"status": "not_found"}
    state = json.loads(row["state_json"])
    now = clock(conn)
    if now < state["lastAt"]:
        return 400, {"status": "invalid_time"}
    reconcile(conn, instance_id, state, now)
    state["lastAt"] = now
    if type(body) is not dict or set(body) != {"eventId", "type", "payload"}:
        write_state(conn, instance_id, state)
        return 200, {"outcome": "rejected"}
    event_id, event_type, payload = body["eventId"], body["type"], body["payload"]
    if not valid_text(event_id) or not valid_text(event_type) or type(payload) is not dict:
        write_state(conn, instance_id, state)
        return 200, {"outcome": "rejected"}
    previous = conn.execute("SELECT type,actor,payload_json FROM event_log WHERE instance_id=? AND event_id=?",
                            (instance_id, event_id)).fetchone()
    if previous:
        outcome = "replayed" if previous["type"] == event_type and previous["actor"] == actor and json.loads(previous["payload_json"]) == payload else "rejected"
        write_state(conn, instance_id, state)
        return 200, {"outcome": outcome}
    value = payload.get("value") if set(payload) == {"value"} else None
    valid_value = valid_text(value) and state["medium"] == "text"
    if event_type != "submit" or actor not in state["participants"] or not valid_value:
        write_state(conn, instance_id, state)
        return 200, {"outcome": "rejected"}
    if state["contract"] == "timed_collection@1":
        allowed = state["phase"] == "open" and not any(x["actor"] == actor for x in state["entries"])
    else:
        allowed = state["phase"] == "active" and actor == state["route"][state["index"]]
    if not allowed:
        write_state(conn, instance_id, state)
        return 200, {"outcome": "rejected"}
    state["entries"].append({"actor": actor, "value": value})
    if state["contract"] == "sequential_handoff@1":
        state["index"] += 1
        if state["index"] == len(state["route"]):
            state["phase"] = "complete"
    append_event(conn, instance_id, event_id, event_type, actor, now, payload)
    write_state(conn, instance_id, state)
    return 200, {"outcome": "accepted"}


def worker(db_path, stop):
    while not stop.is_set():
        try:
            def work(conn):
                now = clock(conn)
                rows = conn.execute("SELECT id,state_json FROM instances").fetchall()
                for row in rows:
                    state = json.loads(row["state_json"])
                    reconcile(conn, row["id"], state, now)
            transact(db_path, work)
        except Exception as error:
            print("worker error:", error, flush=True)
        stop.wait(0.025)


def verify_persisted_packages(db_path):
    conn = db_connect(db_path)
    try:
        for row in conn.execute("SELECT package_id,state_json FROM instances"):
            package = PACKAGES.get(row["package_id"])
            state = json.loads(row["state_json"])
            if package is None or state.get("packageVersion") != package["version"] or state.get("packageHash") != PACKAGE_HASHES[row["package_id"]]:
                raise RuntimeError("persisted instance package changed without a new version")
    finally:
        conn.close()


def serve(args):
    db_path = str(Path(args.db).resolve())
    initialize_db(db_path)
    verify_persisted_packages(db_path)
    disabled_capabilities = set(args.disable_capability)
    disabled_contracts = set(args.disable_contract)
    stop = threading.Event()
    threading.Thread(target=worker, args=(db_path, stop), daemon=True).start()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *unused):
            return

        def respond(self, status, value):
            data = json.dumps(value, separators=(",", ":")).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def body(self):
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1000000:
                raise ValueError("body too large")
            return json.loads(self.rfile.read(length))

        def admin(self):
            return self.headers.get("X-Admin-Token") == args.admin_token

        def do_GET(self):
            parts = urlsplit(self.path).path.strip("/").split("/")
            if parts == ["health"]:
                return self.respond(200, {"status": "ok"})
            if len(parts) == 3 and parts[0] == "instances" and parts[2] == "view":
                instance_id = parts[1]
                def operation(conn):
                    actor = actor_for(conn, instance_id, self.headers.get("Authorization", ""))
                    if actor is None:
                        return 401, {"status": "unauthorized"}
                    row = conn.execute("SELECT state_json FROM instances WHERE id=?", (instance_id,)).fetchone()
                    if row is None:
                        return 404, {"status": "not_found"}
                    state = json.loads(row["state_json"])
                    now = clock(conn)
                    reconcile(conn, instance_id, state, now)
                    return 200, semantic_view(state, actor)
                return self.respond(*transact(db_path, operation))
            self.respond(404, {"status": "not_found"})

        def do_POST(self):
            path = urlsplit(self.path).path
            try:
                body = self.body()
            except (ValueError, json.JSONDecodeError):
                return self.respond(400, {"status": "invalid_json"})
            if path == "/admin/clock":
                if not self.admin():
                    return self.respond(401, {"status": "unauthorized"})
                def operation(conn):
                    at = body.get("at") if type(body) is dict else None
                    if not valid_time(at) or at < clock(conn):
                        return 400, {"status": "invalid_time"}
                    conn.execute("UPDATE meta SET value=? WHERE key='clock'", (str(at),))
                    return 200, {"at": at}
                return self.respond(*transact(db_path, operation))
            if path == "/admin/instances":
                if not self.admin():
                    return self.respond(401, {"status": "unauthorized"})
                return self.respond(*transact(db_path, lambda conn: create_instance(conn, body, disabled_capabilities, disabled_contracts)))
            parts = path.strip("/").split("/")
            if len(parts) == 3 and parts[0] == "instances" and parts[2] == "events":
                instance_id = parts[1]
                def operation(conn):
                    actor = actor_for(conn, instance_id, self.headers.get("Authorization", ""))
                    if actor is None:
                        return 401, {"status": "unauthorized"}
                    return submit_event(conn, instance_id, actor, body)
                return self.respond(*transact(db_path, operation))
            self.respond(404, {"status": "not_found"})

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"READY {server.server_port}", flush=True)
    try:
        server.serve_forever()
    finally:
        stop.set()
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--admin-token", required=True)
    parser.add_argument("--disable-capability", action="append", default=[])
    parser.add_argument("--disable-contract", action="append", default=[])
    serve(parser.parse_args())
