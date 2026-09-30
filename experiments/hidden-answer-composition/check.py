#!/usr/bin/env python3
"""Experimental narrow/composed model comparison; not a 0.12 app host."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PEOPLE = ["a", "b", "c"]


def fields(value, required):
    return isinstance(value, dict) and set(value) == set(required)


def nonempty(value):
    return isinstance(value, str) and bool(value)


class TurnEngine:
    """One deliberately small linear author -> guess -> reveal turn grammar."""

    def __init__(self, item_count, answer_type, response_type, participants):
        if not (isinstance(item_count, int) and not isinstance(item_count, bool) and item_count >= 2):
            raise ValueError("invalid item count")
        if answer_type not in ("item_index", "text") or response_type != answer_type:
            raise ValueError("unsupported answer/response pairing")
        if not (isinstance(participants, list) and len(participants) >= 2 and
                all(nonempty(p) for p in participants) and len(set(participants)) == len(participants)):
            raise ValueError("invalid participants")
        self.item_count = item_count
        self.answer_type = answer_type
        self.participants = participants
        self.index = 0
        self.rounds = []
        self.ledger = {}

    @property
    def speaker(self):
        return self.participants[self.index] if self.index < len(self.participants) else None

    @property
    def phase(self):
        if self.speaker is None:
            return "complete"
        return "author" if len(self.rounds) == self.index else "guessing"

    def valid_value(self, value):
        if self.answer_type == "item_index":
            return isinstance(value, int) and not isinstance(value, bool) and 0 <= value < self.item_count
        return nonempty(value)

    def event(self, event):
        if not fields(event, ("eventId", "type", "actor", "payload")):
            return "rejected"
        event_id, kind, actor, payload = (event[k] for k in ("eventId", "type", "actor", "payload"))
        if not (nonempty(event_id) and nonempty(kind) and actor in self.participants and isinstance(payload, dict)):
            return "rejected"
        identity = (kind, actor, json.dumps(payload, sort_keys=True, ensure_ascii=False))
        if event_id in self.ledger:
            return "replayed" if self.ledger[event_id] == identity else "rejected"
        if kind == "publish" and self.phase == "author" and actor == self.speaker:
            if not fields(payload, ("items", "answer")):
                return "rejected"
            items = payload["items"]
            if not (isinstance(items, list) and len(items) == self.item_count and
                    all(nonempty(item) for item in items) and self.valid_value(payload["answer"])):
                return "rejected"
            self.rounds.append({"speaker": actor, "items": items[:], "answer": payload["answer"],
                                "guesses": [], "revealed": False})
        elif kind == "guess" and self.phase == "guessing" and actor != self.speaker:
            if not fields(payload, ("value",)) or not self.valid_value(payload["value"]):
                return "rejected"
            guesses = self.rounds[self.index]["guesses"]
            if any(g["actor"] == actor for g in guesses):
                return "rejected"
            guesses.append({"actor": actor, "value": payload["value"]})
        elif kind == "reveal" and self.phase == "guessing" and actor == self.speaker and payload == {}:
            self.rounds[self.index]["revealed"] = True
            self.index += 1
        else:
            return "rejected"
        self.ledger[event_id] = identity
        return "accepted"

    def view(self, actor):
        if actor not in self.participants:
            raise ValueError("unbound actor")
        result = {"phase": self.phase, "speaker": self.speaker, "rounds": []}
        for number, record in enumerate(self.rounds, 1):
            revealed = record["revealed"]
            item = {"number": number, "speaker": record["speaker"], "items": record["items"],
                    "guessCount": len(record["guesses"]), "revealed": revealed,
                    "guesses": record["guesses"][:] if revealed else
                    [g for g in record["guesses"] if g["actor"] == actor]}
            if revealed or actor == record["speaker"]:
                item["answer"] = record["answer"]
            result["rounds"].append(item)
        return result


def narrow_model(definition, participants):
    if not fields(definition, ("representation", "contract", "speakerOrder", "statementCount",
                               "answerType", "guessType", "guessLimit", "revealAuthority")):
        raise ValueError("invalid narrow definition")
    if not (definition["representation"] == "narrow" and
            definition["contract"] == "hidden_answer_guess@draft" and
            definition["speakerOrder"] == "enrollment" and definition["statementCount"] == 3 and
            definition["answerType"] == definition["guessType"] == "item_index" and
            definition["guessLimit"] == 1 and definition["revealAuthority"] == "speaker"):
        raise ValueError("unsupported narrow definition")
    return TurnEngine(3, "item_index", "item_index", participants)


def composed_model(definition, participants):
    if not fields(definition, ("representation", "contract", "operations")) or not (
            definition["representation"] == "composed" and definition["contract"] == "linear_turn_plan@draft"):
        raise ValueError("invalid composed definition")
    operations = definition["operations"]
    if not isinstance(operations, list) or len(operations) != 4:
        raise ValueError("this draft supports exactly four operations")
    turns, publish, collect, reveal = operations
    if not (turns == {"op": "roster_turns@draft", "order": "enrollment", "cycles": 1} and
            fields(publish, ("op", "itemCount", "answerType")) and
            publish["op"] == "publish_with_hidden_answer@draft" and
            fields(collect, ("op", "actorSet", "responseType", "perActor", "visibility")) and
            collect == {"op": "collect_responses@draft", "actorSet": "other_participants",
                        "responseType": publish["answerType"], "perActor": 1,
                        "visibility": "own_until_reveal"} and
            reveal == {"op": "reveal_and_advance@draft", "authority": "speaker",
                       "missingResponses": "omit"}):
        raise ValueError("unsupported operation sequence")
    return TurnEngine(publish["itemCount"], publish["answerType"], collect["responseType"], participants)


def load(name):
    return json.loads((HERE / "models" / name).read_text())


def event(event_id, kind, actor, payload):
    return {"eventId": event_id, "type": kind, "actor": actor, "payload": payload}


def two_truths_trace(model):
    snapshots = []
    publish = event("a-publish", "publish", "a", {"items": ["I ski", "I cook", "I visited Mars"],
                                                   "answer": 2})
    assert model.event(publish) == "accepted"
    assert model.event(publish) == "replayed"
    changed = event("a-publish", "publish", "a", {"items": ["I ski", "I cook", "I visited Mars"],
                                                   "answer": 1})
    assert model.event(changed) == "rejected"
    snapshots.append([model.view(actor) for actor in PEOPLE])
    assert model.view("b")["rounds"][0].get("answer") is None
    assert model.view("a")["rounds"][0]["answer"] == 2
    assert model.event(event("bad-speaker", "guess", "a", {"value": 2})) == "rejected"
    assert model.event(event("bad-index", "guess", "b", {"value": 3})) == "rejected"
    assert model.event(event("b-guess", "guess", "b", {"value": 2})) == "accepted"
    assert model.view("c")["rounds"][0]["guesses"] == []
    assert model.view("b")["rounds"][0]["guesses"] == [{"actor": "b", "value": 2}]
    snapshots.append([model.view(actor) for actor in PEOPLE])
    assert model.event(event("second-guess", "guess", "b", {"value": 1})) == "rejected"
    assert model.event(event("early-reveal", "reveal", "c", {})) == "rejected"
    assert model.event(event("a-reveal", "reveal", "a", {})) == "accepted"
    assert model.view("c")["rounds"][0]["answer"] == 2
    assert model.view("c")["rounds"][0]["guesses"] == [{"actor": "b", "value": 2}]
    assert model.view("c")["speaker"] == "b"
    snapshots.append([model.view(actor) for actor in PEOPLE])
    assert model.event(event("b-publish", "publish", "b", {"items": ["A", "B", "C"], "answer": 0})) == "accepted"
    assert model.event(event("b-reveal", "reveal", "b", {})) == "accepted"
    assert model.event(event("c-publish", "publish", "c", {"items": ["D", "E", "F"], "answer": 1})) == "accepted"
    assert model.event(event("c-reveal", "reveal", "c", {})) == "accepted"
    assert model.view("a")["phase"] == "complete"
    snapshots.append([model.view(actor) for actor in PEOPLE])
    return snapshots


def list_game_trace(model):
    assert model.event(event("a-publish", "publish", "a", {
        "items": ["torch", "water", "map", "snack", "raincoat"], "answer": "hiking kit"})) == "accepted"
    assert "answer" not in model.view("b")["rounds"][0]
    assert model.event(event("wrong-kind", "guess", "b", {"value": 2})) == "rejected"
    assert model.event(event("b-guess", "guess", "b", {"value": "camping gear"})) == "accepted"
    assert model.event(event("a-reveal", "reveal", "a", {})) == "accepted"
    assert model.view("c")["rounds"][0]["answer"] == "hiking kit"
    assert model.view("c")["rounds"][0]["guesses"] == [{"actor": "b", "value": "camping gear"}]
    return model.view("c")


if __name__ == "__main__":
    narrow = narrow_model(load("two-truths-narrow.json"), PEOPLE)
    composed = composed_model(load("two-truths-composed.json"), PEOPLE)
    assert two_truths_trace(narrow) == two_truths_trace(composed)
    list_game_trace(composed_model(load("list-game-composed.json"), PEOPLE))
    held_out_as_narrow = load("two-truths-narrow.json")
    held_out_as_narrow.update(statementCount=5, answerType="text", guessType="text")
    try:
        narrow_model(held_out_as_narrow, PEOPLE)
    except ValueError:
        pass
    else:
        raise AssertionError("narrow contract unexpectedly accepted five-item text-answer game")
    print("two encodings agree on Two Truths trace; composed rules run List Game: PASS")
