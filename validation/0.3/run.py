#!/usr/bin/env python3
"""Exercise the same 0.3 packages through independent local Python and Node hosts."""

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
CASES = ROOT / "format/0.3/conformance"
HOSTS = {
    "python": [sys.executable, str(ROOT / "validation/0.3/python_host.py")],
    "node": [shutil.which("node") or "node", "--no-warnings", str(ROOT / "validation/0.3/node_host.mjs")],
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
    body = {"instanceId": instance_id, "packageId": package["id"], **values, "tokens": tokens}
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
            if (path.stem == "collection" and index == 1) or (path.stem == "handoff" and index == 1) or (path.stem == "repeated-private" and index == 1) or (path.stem == "offered-response" and index == 7):
                host.restart()
                # The next fixture event retries after restart; the accepted-ID ledger must survive.
        return outputs
    finally:
        host.close()


def worker_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-worker.sqlite")
    try:
        package = json.loads((ROOT / "format/0.3/examples/group-check-in.json").read_text())
        body = {"instanceId": "worker", "packageId": package["id"], "organizer": "host",
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
        package = json.loads((ROOT / "format/0.3/examples/group-check-in.json").read_text())
        body = {"instanceId": "race", "packageId": package["id"], "organizer": "host",
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
        package = json.loads((ROOT / "format/0.3/examples/daily-private-practice.json").read_text())
        body = {"instanceId": "daily-worker", "packageId": package["id"], "organizer": "host",
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
        package = json.loads((ROOT / "format/0.3/examples/daily-private-practice.json").read_text())
        body = {"instanceId": "daily-jump", "packageId": package["id"], "organizer": "host",
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
        package = json.loads((ROOT / "format/0.3/examples/daily-private-practice.json").read_text())
        body = {"instanceId": "daily-race", "packageId": package["id"], "organizer": "host",
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
        package = json.loads((ROOT / "format/0.3/examples/paired-story-response.json").read_text())
        tokens = {"host": "h", "1": "t1", "2": "t2", "3": "t3", "4": "t4"}
        body = {"instanceId": "offer-worker", "packageId": package["id"], "organizer": "host",
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
        package = json.loads((ROOT / "format/0.3/examples/paired-story-response.json").read_text())
        tokens = {"host": "h", "1": "t1", "2": "t2", "3": "t3", "4": "t4"}
        body = {"instanceId": "offer-race", "packageId": package["id"], "organizer": "host",
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
        package = json.loads((ROOT / "format/0.3/examples/group-check-in.json").read_text())
        body = {"instanceId": "version", "packageId": package["id"], "organizer": "host",
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
            print(f"{kind}: {len(paths)} cases, staged workers, atomic offers/responses, privacy, restart, and package identity passed")
        require(results["python"] == results["node"], "hosts returned different semantic results")
        print("two independent local hosts matched on all 0.3 text packages and cases")


if __name__ == "__main__":
    main()
