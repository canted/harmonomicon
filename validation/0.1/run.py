#!/usr/bin/env python3
"""Exercise the same 0.1 packages through independent local Python and Node hosts."""

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
CASES = ROOT / "format/0.1/conformance"
HOSTS = {
    "python": [sys.executable, str(ROOT / "validation/0.1/python_host.py")],
    "node": [shutil.which("node") or "node", "--no-warnings", str(ROOT / "validation/0.1/node_host.mjs")],
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
            if (path.stem == "collection" and index == 1) or (path.stem == "handoff" and index == 1):
                host.restart()
                # The next fixture event retries after restart; the accepted-ID ledger must survive.
        return outputs
    finally:
        host.close()


def worker_probe(kind, directory):
    host = Host(kind, directory / f"{kind}-worker.sqlite")
    try:
        package = json.loads((ROOT / "format/0.1/examples/group-check-in.json").read_text())
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
        package = json.loads((ROOT / "format/0.1/examples/group-check-in.json").read_text())
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


def package_immutability_probe(kind, directory):
    db = directory / f"{kind}-package-version.sqlite"
    host = Host(kind, db)
    try:
        package = json.loads((ROOT / "format/0.1/examples/group-check-in.json").read_text())
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
            package_immutability_probe(kind, directory)
            print(f"{kind}: {len(paths)} cases, worker, concurrent commit, privacy, restart, and package identity passed")
        require(results["python"] == results["node"], "hosts returned different semantic results")
        print("two independent local hosts matched on both 0.1 packages")


if __name__ == "__main__":
    main()
