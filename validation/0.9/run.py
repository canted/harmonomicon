#!/usr/bin/env python3
"""Exercise the same 0.9 packages through independent local Python and Node hosts."""

import json
import select
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "format/0.9/conformance"
HOSTS = {
    "python": [sys.executable, str(ROOT / "validation/0.9/python_host.py")],
    "node": [shutil.which("node") or "node", "--no-warnings", str(ROOT / "validation/0.9/node_host.mjs")],
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def http(port, method, path, body=None, token=None, admin=None):
    headers = {}
    if body is not None:
        body = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    if admin:
        headers["X-Admin-Token"] = admin
    request = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


class Host:
    def __init__(self, kind, db, disabled=()):
        self.kind = kind
        self.db = db
        self.disabled = disabled
        self.admin = "admin-" + secrets.token_urlsafe(24)
        self.process = None
        self.port = None
        self.start()

    def start(self):
        cmd = [*HOSTS[self.kind], "--db", str(self.db), "--port", "0", "--admin-token", self.admin]
        for item in self.disabled:
            if item.startswith("behavior:"):
                cmd.extend(["--disable-contract", item.removeprefix("behavior:")])
            else:
                cmd.extend(["--disable-capability", item])
        self.process = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        deadline = time.monotonic() + 8
        output = []
        while time.monotonic() < deadline:
            ready, _, _ = select.select([self.process.stdout], [], [], 0.1)
            if not ready:
                if self.process.poll() is not None:
                    break
                continue
            line = self.process.stdout.readline().strip()
            if not line and self.process.poll() is not None:
                break
            output.append(line)
            if line.startswith("READY "):
                self.port = int(line.split()[1])
                require(http(self.port, "GET", "/health")[1] == {"status": "ok"}, "health check failed")
                for file in sorted((ROOT / "format/0.9/examples").glob("*.json")):
                    package = json.loads(file.read_text())
                    status, result = http(self.port, "POST", "/admin/packages/import", {"package": package}, admin=self.admin)
                    require(status in (200, 201) and result["status"] in ("existing", "imported"),
                            f"{self.kind}: package import failed: {status} {result}")
                return
        self.close()
        raise RuntimeError(f"{self.kind} host did not start: {output}")

    def restart(self):
        self.close()
        self.start()

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        if self.process and self.process.stdout:
            self.process.stdout.close()
        self.process = None

    def request(self, method, path, body=None, token=None, admin=False):
        return http(self.port, method, path, body, token, self.admin if admin else None)

    def set_clock(self, at):
        status, value = self.request("POST", "/admin/clock", {"at": at}, admin=True)
        require(status == 200 and value == {"at": at}, f"clock update failed: {status} {value}")


def db_query(db, sql, values=()):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql, values).fetchall()
    finally:
        conn.close()


def await_db(db, predicate, label):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError(f"worker did not reach {label}")


def case_instance(case, package, suffix):
    values = dict(case.get("instance", {"organizer": "host", "participants": ["a", "b"], "opensAt": 10, "closesAt": 20}))
    values.pop("createdAt", None)
    instance_id = f"{suffix}-instance"
    actors = [values["organizer"], *values["participants"]]
    tokens = {actor: f"token-{suffix}-{actor}" for actor in actors}
    body = {"instanceId": instance_id, "packageId": package["id"], "packageVersion": package["version"], **values, "tokens": tokens}
    return instance_id, tokens, body


def run_case(kind, path, directory):
    case = json.loads(path.read_text())
    package = json.loads((path.parent / case["package"]).read_text())
    disabled = case.get("missing", []) if case.get("expectStatus") == "unsupported" else []
    host = Host(kind, directory / f"{kind}-{path.stem}.sqlite", disabled)
    outputs = []
    try:
        instance_id, tokens, body = case_instance(case, package, path.stem)
        status, result = host.request("POST", "/admin/instances", body, admin=True)
        if case.get("expectStatus") == "unsupported":
            require(status == 200 and result == {"status": "unsupported", "missing": case["missing"]},
                    f"{kind} {path.stem}: unsupported mismatch {status} {result}")
            return [result]
        require(status == 201 and result["status"] == "created", f"{kind} {path.stem}: create failed {status} {result}")
        no_auth, _ = host.request("GET", f"/instances/{instance_id}/view")
        require(no_auth == 401, f"{kind} {path.stem}: unauthenticated view allowed")
        wrong_auth, _ = host.request("GET", f"/instances/{instance_id}/view", token="wrong-token")
        require(wrong_auth == 401, f"{kind} {path.stem}: wrong token allowed")
        outputs.append(result)
        for attempt in case.get("uploadAttempts", []):
            status, rejected = host.request("POST", f"/instances/{instance_id}/media",
                {"mediaType": attempt["mediaType"], "data": attempt["data"]}, token=tokens[attempt["actor"]])
            require(status == 400 and rejected == {"status": "invalid_media"},
                    f"{kind} {path.stem}: invalid upload accepted {status} {rejected}")
            outputs.append(rejected)
        for upload in case.get("uploads", []):
            status, stored = host.request("POST", f"/instances/{instance_id}/media",
                {"mediaType": upload["mediaType"], "data": upload["data"]}, token=tokens[upload["actor"]])
            require(status == 200 and stored == {"ref": upload["ref"]},
                    f"{kind} {path.stem}: image upload mismatch {status} {stored}")
            outputs.append(stored)
        for index, step in enumerate(case["events"]):
            event = step["event"]
            host.set_clock(event["at"])
            if event["type"] == "tick":
                await_db(host.db, lambda: bool(db_query(host.db,
                    "SELECT seq FROM event_log WHERE instance_id=? AND type='tick' AND at=?",
                    (instance_id, event["at"]))), f"{kind} tick at {event['at']}")
                outcome = "accepted"
            else:
                status, result = host.request("POST", f"/instances/{instance_id}/events",
                    {"eventId": event["eventId"], "type": event["type"], "payload": event["payload"]},
                    token=tokens[event["actor"]])
                require(status == 200, f"{kind} {path.stem}: HTTP {status} {result}")
                outcome = result["outcome"]
            require(outcome == step["outcome"], f"{kind} {path.stem} event {index + 1}: {outcome} != {step['outcome']}")
            outputs.append(outcome)
            for view in step.get("views", []):
                if "at" in view:
                    host.set_clock(view["at"])
                status, actual = host.request("GET", f"/instances/{instance_id}/view", token=tokens[view["actor"]])
                require(status == 200 and actual == view["expect"],
                        f"{kind} {path.stem} view {view['actor']}: {actual} != {view['expect']}")
                outputs.append(actual)
            for access in step.get("mediaReads", []):
                status, value = host.request("GET", f"/instances/{instance_id}/media/{access['ref']}",
                    token=tokens[access["actor"]])
                expected_status = 200 if access["expect"] == "allowed" else 404
                require(status == expected_status, f"{kind} {path.stem}: media read {access} returned {status} {value}")
                if status == 200:
                    matching = next(item for item in case["uploads"] if item["ref"] == access["ref"])
                    require(value == {"ref": access["ref"], "mediaType": "image/png", "data": matching["data"]},
                            f"{kind} {path.stem}: wrong media bytes")
                outputs.append(status)
            if (path.stem == "collection" and index == 1) or (path.stem == "handoff" and index == 1) or (path.stem == "repeated-private" and index == 1) or (path.stem == "offered-response" and index == 7) or (path.stem == "project-cycle" and index in (6, 10)) or (path.stem == "ongoing-open" and index in (1, 4)) or (path.stem == "ongoing-status" and index == 1) or (path.stem == "guided-rounds" and index in (5, 9)) or (path.stem == "competitive-complete" and index in (4, 7)) or (path.stem == "image-caption" and index in (7, 16)):
                host.restart()
                # The next fixture event retries after restart; the accepted-ID ledger must survive.
        return outputs
    finally:
        host.close()


def worker_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-worker.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/group-check-in.json").read_text())
        body = {"instanceId": "worker", "packageId": package["id"], "packageVersion": package["version"], "organizer": "host",
                "participants": ["a", "b"], "opensAt": 10, "closesAt": 20,
                "tokens": {"host": "h", "a": "a", "b": "b"}}
        status, value = host.request("POST", "/admin/instances", body, admin=True)
        require(status == 201, f"{kind}: worker instance create failed {value}")
        host.set_clock(10)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT state_json FROM instances WHERE id='worker' AND json_extract(state_json,'$.phase')='open'")), f"{kind} open")
        host.set_clock(20)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT state_json FROM instances WHERE id='worker' AND json_extract(state_json,'$.phase')='closed'")), f"{kind} close")
        ticks = db_query(host.db, "SELECT at FROM event_log WHERE instance_id='worker' AND type='tick' ORDER BY seq")
        require(ticks == [(10,), (20,)], f"{kind}: worker tick log wrong {ticks}")
    finally:
        host.close()


def concurrent_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-concurrent.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/group-check-in.json").read_text())
        body = {"instanceId": "race", "packageId": package["id"], "packageVersion": package["version"], "organizer": "host",
                "participants": ["a", "b"], "opensAt": 10, "closesAt": 20,
                "tokens": {"host": "h", "a": "a", "b": "b"}}
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201, f"{kind}: race create failed")
        host.set_clock(10)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT seq FROM event_log WHERE instance_id='race' AND type='tick' AND at=10")), f"{kind} open")
        spoof_status, spoof = host.request("POST", "/instances/race/events",
            {"eventId": "spoof", "type": "submit", "actor": "b", "at": 19, "payload": {"value": "Spoofed"}}, token="a")
        require(spoof_status == 200 and spoof == {"outcome": "rejected"}, f"{kind}: accepted client actor/time spoof")
        def submit(index):
            return host.request("POST", "/instances/race/events",
                {"eventId": f"race-{index}", "type": "submit", "payload": {"value": f"Answer {index}"}}, token="a")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, [1, 2]))
        outcomes = sorted(value["outcome"] for status, value in results if status == 200)
        require(outcomes == ["accepted", "rejected"], f"{kind}: concurrent outcomes {results}")
        status, a_view = host.request("GET", "/instances/race/view", token="a")
        status_b, b_view = host.request("GET", "/instances/race/view", token="b")
        require(status == status_b == 200 and a_view["submissionCount"] == b_view["submissionCount"] == 1,
                f"{kind}: concurrent count wrong")
        require("own" in a_view and "own" not in b_view and "entries" not in b_view,
                f"{kind}: private pre-reveal view leaked")
        accepted = next((index for index, result in zip([1, 2], results) if result[1]["outcome"] == "accepted"))
        host.restart()
        status, replay = submit(accepted)
        require(status == 200 and replay == {"outcome": "replayed"}, f"{kind}: retry after restart {replay}")
        accepted_rows = db_query(host.db, "SELECT event_id FROM event_log WHERE instance_id='race' AND type='submit'")
        require(len(accepted_rows) == 1, f"{kind}: duplicate durable commit {accepted_rows}")
        denied, _ = host.request("POST", "/admin/clock", {"at": 20})
        require(denied == 401, f"{kind}: participant could control test clock")
    finally:
        host.close()



def repeated_worker_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-repeated-worker.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/daily-private-practice.json").read_text())
        body = {"instanceId": "daily-worker", "packageId": package["id"], "packageVersion": package["version"], "organizer": "host",
                "participants": ["a", "b"], "startsAt": 10,
                "tokens": {"host": "h", "a": "a", "b": "b"}}
        status, value = host.request("POST", "/admin/instances", body, admin=True)
        require(status == 201, f"{kind}: repeated worker create failed {value}")
        boundaries = [(10, "open", 1), (72000010, "between", None),
                      (86400010, "open", 2), (158400010, "complete", None)]
        for at, phase, current in boundaries:
            host.set_clock(at)
            def reached():
                rows = db_query(host.db, "SELECT state_json FROM instances WHERE id='daily-worker'")
                if not rows:
                    return False
                state = json.loads(rows[0][0])
                return state["phase"] == phase and state["currentOccurrence"] == current and bool(db_query(host.db,
                    "SELECT seq FROM event_log WHERE instance_id='daily-worker' AND type='tick' AND at=?", (at,)))
            await_db(host.db, reached, f"{kind} repeated boundary {at}")
        ticks = db_query(host.db, "SELECT at FROM event_log WHERE instance_id='daily-worker' AND type='tick' ORDER BY seq")
        require(ticks == [(10,), (72000010,), (86400010,), (158400010,)], f"{kind}: repeated worker ticks {ticks}")
        status, view = host.request("GET", "/instances/daily-worker/view", token="a")
        require(status == 200 and view["phase"] == "complete" and
                [item["statuses"] for item in view["occurrences"]] == [
                    [{"actor": "a", "status": "missed"}, {"actor": "b", "status": "missed"}],
                    [{"actor": "a", "status": "missed"}, {"actor": "b", "status": "missed"}]],
                f"{kind}: repeated history missing after worker-only run {view}")
    finally:
        host.close()



def repeated_jump_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-repeated-jump.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/daily-private-practice.json").read_text())
        body = {"instanceId": "daily-jump", "packageId": package["id"], "packageVersion": package["version"], "organizer": "host",
                "participants": ["a", "b"], "startsAt": 10,
                "tokens": {"host": "h", "a": "a", "b": "b"}}
        invalid = [
            {**body, "route": ["a", "b"]},
            {key: value for key, value in body.items() if key != "startsAt"},
            {**body, "startsAt": 9007199254740991},
            {**body, "prompt": "Forbidden override"},
        ]
        for attempt in invalid:
            status, value = host.request("POST", "/admin/instances", attempt, admin=True)
            require(status == 400 and value == {"status": "invalid_instance"},
                    f"{kind}: accepted invalid repeated setup {status} {value}")
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: jump instance creation failed")
        host.set_clock(158400010)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT state_json FROM instances WHERE id='daily-jump' AND json_extract(state_json,'$.phase')='complete'")),
            f"{kind} jumped to final close")
        ticks = db_query(host.db, "SELECT at FROM event_log WHERE instance_id='daily-jump' AND type='tick' ORDER BY seq")
        require(ticks == [(10,), (72000010,), (86400010,), (158400010,)],
                f"{kind}: jumped worker skipped boundaries {ticks}")
        status, view = host.request("GET", "/instances/daily-jump/view", token="b")
        require(status == 200 and view["phase"] == "complete" and len(view["occurrences"]) == 2 and
                all(item["phase"] == "closed" and item["submissionCount"] == 0 for item in view["occurrences"]),
                f"{kind}: jumped history wrong {view}")
    finally:
        host.close()

def repeated_concurrent_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-repeated-concurrent.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/daily-private-practice.json").read_text())
        body = {"instanceId": "daily-race", "packageId": package["id"], "packageVersion": package["version"], "organizer": "host",
                "participants": ["a", "b"], "startsAt": 10,
                "tokens": {"host": "h", "a": "a", "b": "b"}}
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: repeated race create failed")
        host.set_clock(10)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT seq FROM event_log WHERE instance_id='daily-race' AND type='tick' AND at=10")), f"{kind} repeated open")
        def submit(index):
            return host.request("POST", "/instances/daily-race/events",
                {"eventId": f"day-1-{index}", "type": "submit",
                 "payload": {"occurrence": 1, "value": f"Private entry {index}"}}, token="a")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, [1, 2]))
        require(sorted(value["outcome"] for status, value in results if status == 200) == ["accepted", "rejected"],
                f"{kind}: repeated concurrent outcomes {results}")
        status, b_view = host.request("GET", "/instances/daily-race/view", token="b")
        status_h, h_view = host.request("GET", "/instances/daily-race/view", token="h")
        require(status == status_h == 200 and b_view == h_view and
                b_view["occurrences"][0]["submissionCount"] == 1 and
                b_view["occurrences"][0]["statuses"][0]["status"] == "complete" and
                "entries" not in b_view["occurrences"][0] and "own" not in b_view["occurrences"][0],
                f"{kind}: private repeated entry leaked {b_view} {h_view}")
        accepted = next(index for index, result in zip([1, 2], results) if result[1]["outcome"] == "accepted")
        host.restart()
        require(submit(accepted) == (200, {"outcome": "replayed"}), f"{kind}: repeated retry after restart failed")
        require(len(db_query(host.db, "SELECT event_id FROM event_log WHERE instance_id='daily-race' AND type='submit'")) == 1,
                f"{kind}: repeated accepted entry was not committed exactly once")
        host.set_clock(86400010)
        status, value = host.request("POST", "/instances/daily-race/events",
            {"eventId": "wrong-day", "type": "submit", "payload": {"occurrence": 1, "value": "late"}}, token="b")
        require(status == 200 and value == {"outcome": "rejected"}, f"{kind}: accepted a stale occurrence")
        status, a_view = host.request("GET", "/instances/daily-race/view", token="a")
        require(status == 200 and len(a_view["occurrences"]) == 2 and
                "own" in a_view["occurrences"][0] and "own" not in a_view["occurrences"][1],
                f"{kind}: repeated history not retained {a_view}")
    finally:
        host.close()


def offered_worker_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-offered-worker.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/paired-story-response.json").read_text())
        tokens = {"host": "h", "1": "t1", "2": "t2", "3": "t3", "4": "t4"}
        body = {"instanceId": "offer-worker", "packageId": package["id"], "packageVersion": package["version"], "organizer": "host",
                "participants": ["1", "2", "3", "4"], "opensAt": 10, "sourceDeadline": 20,
                "responseDeadline": 40, "roundId": "42", "tokens": tokens}
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: offered worker instance failed")
        host.set_clock(10)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT seq FROM event_log WHERE instance_id='offer-worker' AND type='tick' AND at=10")), f"{kind} offered open")
        for actor in ["1", "2", "3", "4"]:
            status, result = host.request("POST", "/instances/offer-worker/events",
                {"eventId": "source-" + actor, "type": "submit_source", "payload": {"value": "Source " + actor}},
                token=tokens[actor])
            require(status == 200 and result == {"outcome": "accepted"}, f"{kind}: source setup failed {result}")
        host.set_clock(40)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT state_json FROM instances WHERE id='offer-worker' AND json_extract(state_json,'$.phase')='complete'")),
            f"{kind} offered worker final reveal")
        ticks = db_query(host.db, "SELECT at FROM event_log WHERE instance_id='offer-worker' AND type='tick' ORDER BY seq")
        require(ticks == [(10,), (20,), (40,)], f"{kind}: offered worker skipped boundaries {ticks}")
        status, view = host.request("GET", "/instances/offer-worker/view", token="h")
        require(status == 200 and view["phase"] == "complete" and len(view["sources"]) == 4 and
                view["responses"] == [], f"{kind}: worker final view wrong {view}")
    finally:
        host.close()


def offered_concurrent_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-offered-concurrent.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/paired-story-response.json").read_text())
        tokens = {"host": "h", "1": "t1", "2": "t2", "3": "t3", "4": "t4"}
        body = {"instanceId": "offer-race", "packageId": package["id"], "packageVersion": package["version"], "organizer": "host",
                "participants": ["1", "2", "3", "4"], "opensAt": 10, "sourceDeadline": 20,
                "responseDeadline": 40, "roundId": "42", "tokens": tokens}
        invalid = [
            {**body, "roundId": "042"},
            {**body, "roundId": "18446744073709551616"},
            {**body, "roundId": "9" * 5000},
            {**body, "participants": ["01", "2", "3", "4"], "tokens": {"host": "h", "01": "t1", "2": "t2", "3": "t3", "4": "t4"}},
            {**body, "sourceDeadline": 10},
        ]
        for attempt in invalid:
            status, value = host.request("POST", "/admin/instances", attempt, admin=True)
            require(status == 400 and value == {"status": "invalid_instance"},
                    f"{kind}: accepted invalid offered setup {status} {value}")
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: offered race instance failed")
        host.set_clock(10)
        for actor in ["1", "2", "3", "4"]:
            status, result = host.request("POST", "/instances/offer-race/events",
                {"eventId": "source-" + actor, "type": "submit_source", "payload": {"value": "Source " + actor}},
                token=tokens[actor])
            require(status == 200 and result == {"outcome": "accepted"}, f"{kind}: source setup failed {result}")
        host.set_clock(20)
        def request_offer(index):
            return host.request("POST", "/instances/offer-race/events",
                {"eventId": f"offer-{index}", "type": "request_offer", "payload": {}}, token="t1")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(request_offer, [1, 2]))
        outcomes = sorted(value["outcome"] for status, value in results if status == 200)
        require(outcomes == ["accepted", "existing"], f"{kind}: concurrent offer outcomes {results}")
        status, own_view = host.request("GET", "/instances/offer-race/view", token="t1")
        status_h, host_view = host.request("GET", "/instances/offer-race/view", token="h")
        require(status == status_h == 200 and [item["actor"] for item in own_view["offer"]] == ["4", "2"] and
                "offer" not in host_view and "sources" not in host_view,
                f"{kind}: private saved offer wrong {own_view} {host_view}")
        offer_rows = db_query(host.db, "SELECT event_id FROM event_log WHERE instance_id='offer-race' AND type='request_offer'")
        require(len(offer_rows) == 2, f"{kind}: request ledger not atomic {offer_rows}")
        host.restart()
        for index in [1, 2]:
            require(request_offer(index) == (200, {"outcome": "replayed"}),
                    f"{kind}: offer request {index} not replayed after restart")
        status, saved = host.request("GET", "/instances/offer-race/view", token="t1")
        require(status == 200 and saved["offer"] == own_view["offer"], f"{kind}: saved offer changed after restart")
        def respond(index, source):
            return host.request("POST", "/instances/offer-race/events",
                {"eventId": f"response-{index}", "type": "submit_response",
                 "payload": {"source": source, "value": f"Response {index}"}}, token="t1")
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda args: respond(*args), [(1, "4"), (2, "2")]))
        require(sorted(value["outcome"] for status, value in responses if status == 200) == ["accepted", "rejected"],
                f"{kind}: concurrent responses {responses}")
        status, other_view = host.request("GET", "/instances/offer-race/view", token="t2")
        require(status == 200 and other_view["responseCount"] == 1 and "ownResponse" not in other_view and
                "responses" not in other_view and "sources" not in other_view,
                f"{kind}: private response leaked before reveal {other_view}")
        host.set_clock(40)
        status, final_view = host.request("GET", "/instances/offer-race/view", token="t2")
        require(status == 200 and final_view["phase"] == "complete" and len(final_view["sources"]) == 4 and
                len(final_view["responses"]) == 1, f"{kind}: final reveal missing {final_view}")
    finally:
        host.close()

def package_immutability_probe(kind, directory):
    db = directory / f"{kind}-package-version.sqlite"
    host = Host(kind, db)
    try:
        package = json.loads((ROOT / "format/0.9/examples/group-check-in.json").read_text())
        body = {"instanceId": "version", "packageId": package["id"], "packageVersion": package["version"], "organizer": "host",
                "participants": ["a", "b"], "opensAt": 10, "closesAt": 20,
                "tokens": {"host": "h", "a": "a", "b": "b"}}
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: package version instance failed")
    finally:
        host.close()
    conn = sqlite3.connect(db)
    try:
        state = json.loads(conn.execute("SELECT state_json FROM instances WHERE id='version'").fetchone()[0])
        state["packageHash"] = "wrong-content-for-same-version"
        conn.execute("UPDATE instances SET state_json=? WHERE id='version'", (json.dumps(state),))
        conn.commit()
    finally:
        conn.close()
    try:
        changed = Host(kind, db)
    except RuntimeError:
        return
    changed.close()
    raise AssertionError(f"{kind}: resumed an instance against changed package bytes")


def project_body(package, instance_id):
    return {"instanceId": instance_id, "packageId": package["id"], "packageVersion": package["version"],
            "organizer": "host", "participants": ["a", "b", "c", "d"],
            "teams": [{"id": "red", "members": ["a", "b"]}, {"id": "blue", "members": ["c", "d"]}],
            "opensAt": 10, "submissionDeadline": 30, "reviewDeadline": 50,
            "tokens": {"host": instance_id + "-host", "a": instance_id + "-a", "b": instance_id + "-b",
                       "c": instance_id + "-c", "d": instance_id + "-d"}}


def project_worker_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-project-worker.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/small-team-jam.json").read_text())
        body = project_body(package, "project-worker")
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: project worker instance failed")
        for at, phase in ((10, "work"), (30, "review"), (50, "complete")):
            host.set_clock(at)
            await_db(host.db, lambda: bool(db_query(host.db,
                "SELECT state_json FROM instances WHERE id='project-worker' AND json_extract(state_json,'$.phase')=?",
                (phase,))), f"{kind} project {phase}")
        ticks = db_query(host.db, "SELECT at FROM event_log WHERE instance_id='project-worker' AND type='tick' ORDER BY seq")
        require(ticks == [(10,), (30,), (50,)], f"{kind}: project worker tick order {ticks}")
    finally:
        host.close()


def project_concurrent_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-project-race.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/small-team-jam.json").read_text())
        body = project_body(package, "project-race")
        invalid = json.loads(json.dumps(body))
        invalid["instanceId"] = "invalid-partition"
        invalid["teams"][1]["members"] = ["b", "d"]
        status, value = host.request("POST", "/admin/instances", invalid, admin=True)
        require(status == 400 and value == {"status": "invalid_instance"}, f"{kind}: duplicate team member accepted")
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: project race instance failed")
        host.set_clock(10)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT seq FROM event_log WHERE instance_id='project-race' AND type='tick' AND at=10")), f"{kind} project open")
        def submit(actor):
            return host.request("POST", "/instances/project-race/events",
                {"eventId": "final-" + actor, "type": "submit_final", "payload": {"value": "Final " + actor}},
                token="project-race-" + actor)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, ["a", "b"]))
        require(sorted(value["outcome"] for status, value in results if status == 200) == ["accepted", "rejected"],
                f"{kind}: competing teammate finals {results}")
        winner = next(actor for actor, result in zip(("a", "b"), results) if result[1]["outcome"] == "accepted")
        status, other_view = host.request("GET", "/instances/project-race/view", token="project-race-c")
        require(status == 200 and other_view["finalCount"] == 1 and "finals" not in other_view
                and "ownFinal" not in other_view, f"{kind}: final leaked before review")
        host.restart()
        require(submit(winner)[1] == {"outcome": "replayed"}, f"{kind}: final retry after restart failed")
        state = json.loads(db_query(host.db, "SELECT state_json FROM instances WHERE id='project-race'")[0][0])
        require(len(state["finals"]) == 1, f"{kind}: duplicate final persisted")
        host.set_clock(30)
        status, revealed = host.request("GET", "/instances/project-race/view", token="project-race-c")
        require(status == 200 and revealed["phase"] == "review" and len(revealed["finals"]) == 1,
                f"{kind}: final did not reveal at review boundary")
        status, late = host.request("POST", "/instances/project-race/events",
            {"eventId": "late-post", "type": "post_progress", "payload": {"audience": "group", "value": "Late"}},
            token="project-race-c")
        require(status == 200 and late == {"outcome": "rejected"}, f"{kind}: late progress accepted")
    finally:
        host.close()


def ongoing_worker_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-ongoing-worker.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/prompt-series-status.json").read_text())
        invalid_package = json.loads(json.dumps(package))
        invalid_package["version"] = "0.6.1"
        invalid_package["behavior"]["schedule"]["windowMs"] = invalid_package["behavior"]["schedule"]["intervalMs"] + 1
        status, result = host.request("POST", "/admin/packages/import", {"package": invalid_package}, admin=True)
        require(status == 400 and result == {"status": "invalid_package"},
                f"{kind}: overlapping prompt windows imported")
        body = {"instanceId": "ongoing-worker", "packageId": package["id"], "packageVersion": package["version"],
                "organizer": "host", "participants": ["a", "b"], "startsAt": 10,
                "tokens": {"host": "h", "a": "a", "b": "b"}}
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: ongoing worker instance failed")
        host.set_clock(158400010)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT state_json FROM instances WHERE id='ongoing-worker' AND json_extract(state_json,'$.phase')='complete'")),
            f"{kind} ongoing completion")
        ticks = db_query(host.db, "SELECT at FROM event_log WHERE instance_id='ongoing-worker' AND type='tick' ORDER BY seq")
        require(ticks == [(10,), (72000010,), (86400010,), (158400010,)],
                f"{kind}: ongoing worker missed a boundary: {ticks}")
        status, view = host.request("GET", "/instances/ongoing-worker/view", token="a")
        require(status == 200 and view["phase"] == "complete"
                and all(item["statuses"][0]["status"] == "missed" for item in view["occurrences"]),
                f"{kind}: missed status after time jump wrong: {view}")
    finally:
        host.close()


def ongoing_concurrent_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-ongoing-concurrent.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/shared-notebook.json").read_text())
        body = {"instanceId": "ongoing-race", "packageId": package["id"], "packageVersion": package["version"],
                "organizer": "host", "participants": ["a", "b"], "startsAt": 10, "endsAt": 50,
                "tokens": {"host": "h", "a": "a", "b": "b"}}
        invalid_instance = dict(body, instanceId="invalid-ongoing", endsAt=10)
        status, result = host.request("POST", "/admin/instances", invalid_instance, admin=True)
        require(status == 400 and result == {"status": "invalid_instance"},
                f"{kind}: zero-length ongoing window accepted")
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: ongoing race instance failed")
        host.set_clock(10)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT seq FROM event_log WHERE instance_id='ongoing-race' AND type='tick' AND at=10")),
            f"{kind} ongoing open")
        status, private = host.request("POST", "/instances/ongoing-race/events",
            {"eventId": "private-a", "type": "post_entry", "payload": {"audience": "private", "value": "Only A"}}, token="a")
        require(status == 200 and private == {"outcome": "accepted"}, f"{kind}: private entry failed")
        status, b_view = host.request("GET", "/instances/ongoing-race/view", token="b")
        require(status == 200 and b_view["entries"] == [], f"{kind}: private entry leaked to B")
        def post(actor):
            return host.request("POST", "/instances/ongoing-race/events",
                {"eventId": "group-" + actor, "type": "post_entry",
                 "payload": {"audience": "group", "value": "From " + actor}}, token=actor)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(post, ("a", "b")))
        require(all(status == 200 and result == {"outcome": "accepted"} for status, result in results),
                f"{kind}: concurrent group posts failed {results}")
        host.restart()
        require(post("a")[1] == {"outcome": "replayed"}, f"{kind}: group entry retry failed")
        status, view = host.request("GET", "/instances/ongoing-race/view", token="b")
        require(status == 200 and len(view["entries"]) == 2 and all(x["audience"] == "group" for x in view["entries"]),
                f"{kind}: concurrent entries lost or private entry leaked: {view}")
        rows = db_query(host.db, "SELECT event_id FROM event_log WHERE instance_id='ongoing-race' AND type='post_entry'")
        require(len(rows) == 3, f"{kind}: duplicate entry committed after retry")
    finally:
        host.close()


def guided_body(package, instance_id):
    solo = [{"id": "s-" + actor, "members": [actor]} for actor in "abcd"]
    pairs = [{"id": "ab", "members": ["a", "b"]}, {"id": "cd", "members": ["c", "d"]}]
    everyone = [{"id": "all", "members": ["a", "b", "c", "d"]}]
    return {"instanceId": instance_id, "packageId": package["id"], "packageVersion": package["version"],
            "organizer": "host", "participants": ["a", "b", "c", "d"], "startsAt": 10,
            "groupsByRound": [solo, pairs, everyone],
            "tokens": {"host": instance_id + "-host", "a": instance_id + "-a", "b": instance_id + "-b",
                       "c": instance_id + "-c", "d": instance_id + "-d"}}


def guided_worker_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-guided-worker.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/small-group-synthesis.json").read_text())
        body = guided_body(package, "guided-worker")
        invalid = json.loads(json.dumps(body))
        invalid["instanceId"] = "invalid-guided"
        invalid["groupsByRound"][1][1]["members"] = ["b", "d"]
        status, result = host.request("POST", "/admin/instances", invalid, admin=True)
        require(status == 400 and result == {"status": "invalid_instance"},
                f"{kind}: invalid round partition accepted")
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: guided worker instance failed")
        host.set_clock(360010)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT state_json FROM instances WHERE id='guided-worker' AND json_extract(state_json,'$.phase')='complete'")),
            f"{kind} guided completion")
        ticks = db_query(host.db, "SELECT at FROM event_log WHERE instance_id='guided-worker' AND type='tick' ORDER BY seq")
        require(ticks == [(10,), (60010,), (180010,), (360010,)],
                f"{kind}: guided worker missed a boundary: {ticks}")
    finally:
        host.close()


def guided_concurrent_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-guided-race.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/small-group-synthesis.json").read_text())
        body = guided_body(package, "guided-race")
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: guided race instance failed")
        host.set_clock(10)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT seq FROM event_log WHERE instance_id='guided-race' AND type='tick' AND at=10")),
            f"{kind} guided open")
        def submit(index):
            return host.request("POST", "/instances/guided-race/events",
                {"eventId": "solo-" + str(index), "type": "submit",
                 "payload": {"round": 1, "value": "Secret " + str(index)}}, token="guided-race-a")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, (1, 2)))
        require(sorted(value["outcome"] for status, value in results if status == 200) == ["accepted", "rejected"],
                f"{kind}: competing solo submissions {results}")
        accepted = next(index for index, result in zip((1, 2), results) if result[1]["outcome"] == "accepted")
        status, b_view = host.request("GET", "/instances/guided-race/view", token="guided-race-b")
        require(status == 200 and all(group["entries"] == [] for group in b_view["rounds"][0]["groups"]),
                f"{kind}: private solo entry leaked")
        host.restart()
        require(submit(accepted)[1] == {"outcome": "replayed"}, f"{kind}: solo retry after restart failed")
        host.set_clock(60010)
        status, result = host.request("POST", "/instances/guided-race/events",
            {"eventId": "pair-a", "type": "submit", "payload": {"round": 2, "value": "Pair context"}},
            token="guided-race-a")
        require(status == 200 and result == {"outcome": "accepted"}, f"{kind}: pair entry rejected")
        status, partner = host.request("GET", "/instances/guided-race/view", token="guided-race-b")
        status_other, other = host.request("GET", "/instances/guided-race/view", token="guided-race-c")
        require(status == status_other == 200
                and partner["rounds"][1]["groups"][0]["entries"][0]["value"] == "Pair context"
                and other["rounds"][1]["groups"][0]["entries"] == [],
                f"{kind}: pair audience wrong")
    finally:
        host.close()


def exchange_probe(directory):
    """Move one newly authored package from the Python host to the Node host."""
    source = Host("python", directory / "exchange-python.sqlite")
    target = Host("node", directory / "exchange-node.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/group-check-in.json").read_text())
        package["id"] = "org.harmonomicon.exchange-probe"
        package["version"] = "1.0.0"
        package["content"]["prompt"] = "What did we learn? café 🎨"
        for host in (source, target):
            status, manifest = host.request("GET", "/capabilities")
            require(status == 200 and manifest["format"] == "harmonomicon.activity-package/0.9"
                    and "timed_collection@1" in manifest["behaviors"]
                    and "text@1" in manifest["capabilities"], f"{host.kind}: manifest mismatch")
        denied, _ = source.request("POST", "/admin/packages/import", {"package": package})
        require(denied == 401, "unauthenticated package import succeeded")
        status, imported = source.request("POST", "/admin/packages/import", {"package": package}, admin=True)
        require(status == 201 and imported["status"] == "imported", f"source import failed {status} {imported}")
        status, exported = source.request("GET", f"/packages/{package['id']}/{package['version']}")
        require(status == 200 and exported["package"] == package and exported["sha256"] == imported["sha256"],
                "source export mismatch")
        status, transferred = target.request("POST", "/admin/packages/import", {"package": exported["package"]}, admin=True)
        require(status == 201 and transferred["sha256"] == imported["sha256"], "cross-host transfer mismatch")
        status, duplicate = target.request("POST", "/admin/packages/import", {"package": package}, admin=True)
        require(status == 200 and duplicate == {"status": "existing", "sha256": imported["sha256"]},
                "exact re-import should be idempotent")
        changed = json.loads(json.dumps(package))
        changed["content"]["prompt"] = "Changed under the same version"
        status, conflict = target.request("POST", "/admin/packages/import", {"package": changed}, admin=True)
        require(status == 409 and conflict == {"status": "package_conflict"}, "same-version change was accepted")
        invalid = json.loads(json.dumps(package))
        invalid["version"] = "1.0.1"
        invalid["behavior"]["contract"] = "imaginary@1"
        status, result = target.request("POST", "/admin/packages/import", {"package": invalid}, admin=True)
        require(status == 400 and result == {"status": "invalid_package"}, "invalid behavior was imported")
        malformed = json.loads(json.dumps(package))
        malformed["version"] = "1.0.2"
        malformed["content"]["prompt"] = "Broken \ud800"
        for host in (source, target):
            status, result = host.request("POST", "/admin/packages/import", {"package": malformed}, admin=True)
            require(status == 400 and result == {"status": "invalid_package"},
                    f"{host.kind}: malformed Unicode was imported")
        changed["version"] = "1.0.1"
        status, newer = target.request("POST", "/admin/packages/import", {"package": changed}, admin=True)
        require(status == 201 and newer["status"] == "imported", "new package version was rejected")
        target.restart()
        for version, expected_prompt in (("1.0.0", "What did we learn? café 🎨"), ("1.0.1", "Changed under the same version")):
            instance_id = "exchange-" + version.replace(".", "-")
            body = {"instanceId": instance_id, "packageId": package["id"], "packageVersion": version,
                    "organizer": "host", "participants": ["a", "b"], "opensAt": 10, "closesAt": 20,
                    "tokens": {"host": instance_id + "-host", "a": instance_id + "-a", "b": instance_id + "-b"}}
            status, result = target.request("POST", "/admin/instances", body, admin=True)
            require(status == 201 and result["status"] == "created", f"imported package cannot run: {result}")
            state = db_query(target.db, "SELECT state_json FROM instances WHERE id=?", (instance_id,))[0][0]
            require(json.loads(state)["prompt"] == expected_prompt, "wrong package version bound to instance")
        target.set_clock(10)
        status, outcome = target.request("POST", "/instances/exchange-1-0-0/events",
            {"eventId": "e1", "type": "submit", "payload": {"value": "A reply"}}, token="exchange-1-0-0-a")
        require(status == 200 and outcome == {"outcome": "accepted"}, "transferred package did not run")
        target.restart()
        status, own = target.request("GET", "/instances/exchange-1-0-0/view", token="exchange-1-0-0-a")
        require(status == 200 and own.get("own") == {"actor": "a", "value": "A reply"},
                "transferred package lost state across restart")
    finally:
        source.close()
        target.close()


def competitive_body(package, instance_id):
    return {"instanceId": instance_id, "packageId": package["id"], "packageVersion": package["version"],
            "organizer": "host", "participants": ["a", "b", "c", "d"], "startsAt": 10,
            "routes": [[ ["a", "b"], ["c", "d"] ],
                       [ ["c", "d"], ["a", "b"] ],
                       [ ["a", "d"], ["b", "c"] ]],
            "tokens": {"host": instance_id + "-host", **{actor: instance_id + "-" + actor for actor in "abcd"}}}


def competitive_worker_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-competitive-worker.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/two-offer-story-chain.json").read_text())
        body = competitive_body(package, "competitive-worker")
        invalid = json.loads(json.dumps(body))
        invalid["instanceId"] = "invalid-route"
        invalid["routes"][0][0] = ["a", "a"]
        status, result = host.request("POST", "/admin/instances", invalid, admin=True)
        require(status == 400 and result == {"status": "invalid_instance"},
                f"{kind}: duplicate offer actor accepted")
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: competitive worker instance failed")
        host.set_clock(120010)
        await_db(host.db, lambda: bool(db_query(host.db,
            "SELECT state_json FROM instances WHERE id='competitive-worker' AND json_extract(state_json,'$.phase')='stalled'")),
            f"{kind} competitive stalled")
        ticks = db_query(host.db, "SELECT at FROM event_log WHERE instance_id='competitive-worker' AND type='tick' ORDER BY seq")
        require(ticks == [(10,), (60010,), (120010,)], f"{kind}: competitive boundary ticks {ticks}")
        status, view = host.request("GET", "/instances/competitive-worker/view", token="competitive-worker-host")
        require(status == 200 and view["phase"] == "stalled" and "entries" not in view,
                f"{kind}: stalled chain leaked or remained open {view}")
    finally:
        host.close()


def competitive_concurrent_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-competitive-concurrent.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/two-offer-story-chain.json").read_text())
        body = competitive_body(package, "competitive-race")
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: competitive race instance failed")
        host.set_clock(11)
        def submit(actor):
            return host.request("POST", "/instances/competitive-race/events",
                {"eventId": "line-" + actor, "type": "submit", "payload": {"step": 1, "attempt": 1, "value": "Line " + actor}},
                token="competitive-race-" + actor)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, ("a", "b")))
        require(sorted(value["outcome"] for status, value in results if status == 200) == ["accepted", "rejected"],
                f"{kind}: competitive simultaneous offers {results}")
        winner = next(actor for actor, result in zip(("a", "b"), results) if result[1]["outcome"] == "accepted")
        status, next_view = host.request("GET", "/instances/competitive-race/view", token="competitive-race-c")
        status_h, host_view = host.request("GET", "/instances/competitive-race/view", token="competitive-race-host")
        require(status == status_h == 200 and next_view["offer"]["input"] == "Line " + winner
                and next_view["acceptedCount"] == 1 and "offer" not in host_view and "entries" not in host_view,
                f"{kind}: next offer or private view wrong {next_view} {host_view}")
        host.restart()
        require(submit(winner) == (200, {"outcome": "replayed"}),
                f"{kind}: competitive retry after restart failed")
        require(len(db_query(host.db, "SELECT event_id FROM event_log WHERE instance_id='competitive-race' AND type='submit'")) == 1,
                f"{kind}: duplicate competitive step committed")
    finally:
        host.close()


def media_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-media.sqlite")
    try:
        package = json.loads((ROOT / "format/0.9/examples/image-caption-circle.json").read_text())
        fixture = json.loads((ROOT / "format/0.9/conformance/image-caption.json").read_text())
        upload = fixture["uploads"][0]
        body = {"instanceId": "media-probe", "packageId": package["id"], "packageVersion": package["version"],
                "organizer": "host", "participants": ["1", "2", "3"], "opensAt": 10,
                "sourceDeadline": 20, "responseDeadline": 40, "roundId": "42",
                "tokens": {"host": "media-host", "1": "media-1", "2": "media-2", "3": "media-3"}}
        require(host.request("POST", "/admin/instances", body, admin=True)[0] == 201,
                f"{kind}: media probe instance failed")
        endpoint = "/instances/media-probe/media"
        denied, _ = host.request("POST", endpoint, {"mediaType": "image/png", "data": upload["data"]})
        require(denied == 401, f"{kind}: anonymous media upload allowed")
        for invalid in ({"mediaType": "image/png", "data": "not-base64"},
                        {"mediaType": "image/jpeg", "data": upload["data"]},
                        {"mediaType": "image/png", "data": "AA=="},
                        {"mediaType": "image/png", "data": upload["data"][:-4] + "AAAA"}):
            status, value = host.request("POST", endpoint, invalid, token="media-1")
            require(status == 400 and value == {"status": "invalid_media"},
                    f"{kind}: invalid PNG accepted {status} {value}")
        for _ in range(2):
            status, value = host.request("POST", endpoint,
                {"mediaType": "image/png", "data": upload["data"]}, token="media-1")
            require(status == 200 and value == {"ref": upload["ref"]},
                    f"{kind}: duplicate image upload changed reference")
        require(len(db_query(host.db, "SELECT ref FROM media WHERE instance_id='media-probe'")) == 1,
                f"{kind}: duplicate bytes stored twice")
        host.set_clock(10)
        status, value = host.request("POST", "/instances/media-probe/events",
            {"eventId": "foreign", "type": "submit_source", "payload": {"value": upload["ref"]}}, token="media-2")
        require(status == 200 and value == {"outcome": "rejected"},
                f"{kind}: another actor submitted uploaded image")
        require(host.request("GET", endpoint + "/" + upload["ref"], token="media-2")[0] == 404,
                f"{kind}: private uploaded image leaked")
        host.restart()
        status, value = host.request("GET", endpoint + "/" + upload["ref"], token="media-1")
        require(status == 200 and value == {"ref": upload["ref"], "mediaType": "image/png", "data": upload["data"]},
                f"{kind}: image bytes lost across restart")
    finally:
        host.close()


def main():
    with tempfile.TemporaryDirectory(prefix="harmonomicon-host-validation-") as temp:
        directory = Path(temp)
        results = {}
        paths = sorted(CASES.glob("*.json"))
        for kind in HOSTS:
            results[kind] = {path.stem: run_case(kind, path, directory) for path in paths}
            worker_probe(kind, directory)
            concurrent_probe(kind, directory)
            repeated_worker_probe(kind, directory)
            repeated_jump_probe(kind, directory)
            repeated_concurrent_probe(kind, directory)
            offered_worker_probe(kind, directory)
            offered_concurrent_probe(kind, directory)
            package_immutability_probe(kind, directory)
            project_worker_probe(kind, directory)
            project_concurrent_probe(kind, directory)
            ongoing_worker_probe(kind, directory)
            ongoing_concurrent_probe(kind, directory)
            guided_worker_probe(kind, directory)
            guided_concurrent_probe(kind, directory)
            competitive_worker_probe(kind, directory)
            competitive_concurrent_probe(kind, directory)
            media_probe(kind, directory)
            print(f"{kind}: {len(paths)} cases, stored images, worker deadlines, atomic writes, privacy, restart, and package identity passed")
        require(results["python"] == results["node"], "hosts returned different semantic results")
        exchange_probe(directory)
        print("two independent local hosts matched on all 0.9 text and image packages and cases, plus cross-host package transfer")


if __name__ == "__main__":
    main()
