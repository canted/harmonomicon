"""Candidate 0.13 runbook validator and reference interpreter."""
import copy
import json
import re
import sys

FORMAT = 'harmonomicon.activity-package/0.13'
OPS = {'collect@1', 'reveal@1', 'append@1', 'tally@1', 'for_each@1'}
CAPS = {'identity@1', 'serial_events@1', 'durable_state@1', 'private_views@1', 'clock@1', 'text@1'}
MAX = 9007199254740991

def require(condition):
    if not condition:
        raise ValueError('invalid_package')

def obj(x, keys):
    return type(x) is dict and set(x) == set(keys)

def text(x):
    return type(x) is str and len(x) > 0

def integer(x, low=0, high=MAX):
    return type(x) in (int, float) and low <= x <= high and x == int(x)

def name(x):
    return type(x) is str and re.fullmatch('[a-z][a-z0-9_]{0,47}', x) is not None

def scalar_strings(x):
    if type(x) is str:
        return all(not 0xD800 <= ord(c) <= 0xDFFF for c in x)
    if type(x) is list:
        return all(scalar_strings(v) for v in x)
    if type(x) is dict:
        return all(scalar_strings(k) and scalar_strings(v) for k, v in x.items())
    return x is None or type(x) is bool or integer(x)

def validate(package):
    require(scalar_strings(package))
    require(obj(package, ['format', 'id', 'version', 'content', 'provenance', 'participants', 'requires', 'runbook']))
    require(package['format'] == FORMAT)
    require(type(package['id']) is str and re.fullmatch(r'[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)+', package['id']))
    require(type(package['version']) is str and re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', package['version']))
    require(obj(package['content'], ['language', 'title', 'summary', 'setup', 'prompt', 'participant', 'completion', 'access']))
    require(all(text(v) for v in package['content'].values()))
    provenance = package['provenance']
    require(type(provenance) is dict and provenance.get('kind') in ['original', 'adaptation'])
    require(obj(provenance, ['kind', 'credit', 'rights'] + (['sourceUrl'] if provenance['kind'] == 'adaptation' else [])))
    if provenance['kind'] == 'adaptation': require(type(provenance['sourceUrl']) is str and re.fullmatch(r'https?://[^\s]+', provenance['sourceUrl']))
    require(all(text(v) for v in package['provenance'].values()))
    bounds = package['participants']
    require(obj(bounds, ['min', 'max']) and integer(bounds['min'], 2, 100) and integer(bounds['max'], bounds['min'], 100))
    requires = package['requires']
    require(type(requires) is list and 1 <= len(requires) <= 64 and len(set(requires)) == len(requires) and all(text(v) for v in requires))
    require(CAPS <= set(requires))
    ids, used = set(), set()

    def steps(sequence, prior, in_turn=False):
        require(type(sequence) is list and 1 <= len(sequence) <= 32)
        available = dict(prior)
        for step in sequence:
            require(type(step) is dict and name(step.get('id')) and step['id'] not in ids)
            ids.add(step['id'])
            op = step.get('op')
            require(op in OPS)
            used.add(op)
            sid = step['id']
            if op == 'for_each@1':
                require(not in_turn and obj(step, ['id', 'op', 'over', 'steps']) and step['over'] == 'participants')
                steps(step['steps'], available, True)
                continue
            if op == 'collect@1':
                require(obj(step, ['id', 'op', 'actors', 'prompt', 'fields', 'close', 'afterMs']))
                require(step['actors'] in (['participants', 'turn', 'others'] if in_turn else ['participants']))
                require(text(step['prompt']))
                close = step['close']
                require(close in (['all', 'organizer', 'turn'] if in_turn else ['all', 'organizer']))
                require(step['afterMs'] is None or integer(step['afterMs'], 1, 86400000))
                fields = step['fields']
                require(type(fields) is dict and 1 <= len(fields) <= 8 and all(name(k) for k in fields))
                for fname, field in fields.items():
                    require(type(field) is dict and field.get('visibility') in ['group', 'private'])
                    kind = field.get('type')
                    if kind == 'text':
                        require(obj(field, ['type', 'visibility']))
                    elif kind == 'text_list':
                        require(obj(field, ['type', 'visibility', 'count']) and integer(field['count'], 1, 32))
                    elif kind == 'choice':
                        require(obj(field, ['type', 'visibility', 'options']))
                        options = field['options']
                        require(type(options) is list and 2 <= len(options) <= 32 and all(text(o) for o in options) and len(set(options)) == len(options))
                    elif kind == 'index':
                        require(obj(field, ['type', 'visibility', 'indexOf']) and text(field['indexOf']))
                        parts = field['indexOf'].split('.')
                        if len(parts) == 1:
                            source = fields.get(parts[0])
                        else:
                            require(len(parts) == 2 and parts[0] in available)
                            source_step = available[parts[0]]
                            require(source_step['op'] == 'collect@1' and source_step['actors'] == 'turn')
                            source = source_step['fields'].get(parts[1])
                            require(source and source['visibility'] == 'group')
                        require(source and source['type'] == 'text_list')
                    else:
                        require(False)
                available[sid] = step
            elif op == 'reveal@1':
                require(obj(step, ['id', 'op', 'sources']) and type(step['sources']) is list and 1 <= len(step['sources']) <= 32)
                require(len(set(step['sources'])) == len(step['sources']))
                for source in step['sources']:
                    require(source in available and available[source]['op'] == 'collect@1')
            elif op == 'append@1':
                require(in_turn and obj(step, ['id', 'op', 'prompt', 'afterMs']))
                require(text(step['prompt']) and (step['afterMs'] is None or integer(step['afterMs'], 1, 86400000)))
                available[sid] = step
            elif op == 'tally@1':
                require(obj(step, ['id', 'op', 'source', 'field']))
                require(step['source'] in available)
                source = available[step['source']]
                require(source['op'] == 'collect@1' and step['field'] in source['fields'])
                require(source['fields'][step['field']]['type'] == 'choice')
                require(any(s['op'] == 'reveal@1' and step['source'] in s['sources'] for s in sequence[:sequence.index(step)]))
        return available

    require(obj(package['runbook'], ['steps']))
    steps(package['runbook']['steps'], {})
    require(used <= set(requires))
    require(len(ids) <= 64)
    require(len(canonical(package).encode()) <= 1000000)
    return package

def canonical(value):
    def normalize(x):
        if type(x) is float and integer(x): return int(x)
        if type(x) is list: return [normalize(v) for v in x]
        if type(x) is dict: return {k: normalize(v) for k,v in x.items()}
        return x
    return json.dumps(normalize(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False)

class Engine:
    def __init__(self, package, participants, organizer, started_at=0, state=None):
        validate(package)
        require(type(participants) is list and package['participants']['min'] <= len(participants) <= package['participants']['max'])
        require(scalar_strings(participants) and all(text(p) and p != 'system' for p in participants) and len(set(participants)) == len(participants))
        require(scalar_strings(organizer) and text(organizer) and organizer != 'system' and organizer not in participants and integer(started_at))
        # Reserve sufficient clock range for every declared timed step, including roster expansion.
        budget = 0
        self.plan = []
        def expand(steps, turn=None, iteration=None):
            nonlocal budget
            for step in steps:
                if step['op'] == 'for_each@1':
                    for i, actor in enumerate(participants):
                        expand(step['steps'], actor, i)
                else:
                    self.plan.append({'step': step, 'turn': turn, 'iteration': iteration, 'key': step['id'] if iteration is None else f"{step['id']}:{iteration}"})
                    budget += step.get('afterMs') or 0
        expand(package['runbook']['steps'])
        require(started_at + budget <= MAX)
        self.package, self.participants, self.organizer = package, participants[:], organizer
        self.state = copy.deepcopy(state) if state is not None else {'pc': 0, 'clock': started_at, 'openedAt': started_at, 'records': [], 'ledger': {}}
        self.settle(self.state['clock'])

    def actors(self, frame):
        selector = frame['step'].get('actors', 'turn')
        return self.participants if selector == 'participants' else [frame['turn']] if selector == 'turn' else [p for p in self.participants if p != frame['turn']]

    def source(self, sid, frame):
        matches = [r for r in self.state['records'] if r['step'] == sid and r['iteration'] in [None, frame['iteration']]]
        return matches[-1]

    def record(self, frame):
        matches = [r for r in self.state['records'] if r['key'] == frame['key']]
        if matches:
            return matches[0]
        record = {'key': frame['key'], 'step': frame['step']['id'], 'op': frame['step']['op'], 'iteration': frame['iteration'], 'turn': frame['turn'], 'entries': [], 'revealed': False, 'closed': False}
        self.state['records'].append(record)
        return record

    def next(self, at):
        self.state['pc'] += 1
        self.state['openedAt'] = at

    def settle(self, now):
        while self.state['pc'] < len(self.plan):
            frame = self.plan[self.state['pc']]
            step, op = frame['step'], frame['step']['op']
            if op in ['collect@1', 'append@1']:
                record = self.record(frame)
                duration = step['afterMs']
                deadline = min(MAX, self.state['openedAt'] + duration) if duration is not None else None
                if deadline is not None and now >= deadline:
                    record['closed'] = True
                    self.next(deadline)
                    continue
                break
            if op == 'reveal@1':
                for sid in step['sources']:
                    self.source(sid, frame)['revealed'] = True
            elif op == 'tally@1':
                source = self.source(step['source'], frame)
                options = self.find_step(source['step'])['fields'][step['field']]['options']
                record = self.record(frame)
                record['counts'] = [{'value': value, 'count': sum(e['value'][step['field']] == value for e in source['entries'])} for value in options]
                record['closed'] = record['revealed'] = True
            self.next(self.state['openedAt'])
        self.state['clock'] = now

    def find_step(self, sid):
        return next(f['step'] for f in self.plan if f['step']['id'] == sid)

    def valid_fields(self, step, payload, frame):
        if not obj(payload, step['fields']):
            return False
        for fname, spec in step['fields'].items():
            value, kind = payload[fname], spec['type']
            if kind == 'text' and not text(value): return False
            if kind == 'text_list' and not (type(value) is list and len(value) == spec['count'] and all(text(v) for v in value)): return False
            if kind == 'choice' and value not in spec['options']: return False
            if kind == 'index':
                parts = spec['indexOf'].split('.')
                items = payload.get(parts[0]) if len(parts) == 1 else self.source(parts[0], frame)['entries'][0]['value'][parts[1]] if self.source(parts[0], frame)['entries'] else []
                if not (type(items) is list and integer(value, 0, len(items)-1)): return False
        return True

    def event(self, event):
        if not obj(event, ['eventId', 'type', 'actor', 'at', 'step', 'payload']) or not scalar_strings(event): return 'rejected'
        if not (text(event['eventId']) and integer(event['at']) and event['at'] >= self.state['clock'] and type(event['payload']) is dict): return 'rejected'
        if event['actor'] not in self.participants + [self.organizer, 'system']: return 'rejected'
        now = event['at']
        self.settle(now)
        identity = {k: event[k] for k in ['type', 'actor', 'step', 'payload']}
        ledger = self.state['ledger']
        if event['eventId'] in ledger:
            return 'replayed' if canonical(ledger[event['eventId']]) == canonical(identity) else 'rejected'
        accepted = False
        if event['type'] == 'tick':
            accepted = event['actor'] == 'system' and event['step'] is None and event['payload'] == {}
        elif self.state['pc'] < len(self.plan):
            frame = self.plan[self.state['pc']]
            step = frame['step']
            if event['step'] != frame['key']: return 'rejected'
            record = self.record(frame)
            if event['type'] == 'submit' and event['actor'] in self.actors(frame) and not any(e['actor'] == event['actor'] for e in record['entries']):
                valid = self.valid_fields(step, event['payload'], frame) if step['op'] == 'collect@1' else obj(event['payload'], ['text']) and text(event['payload']['text'])
                if valid:
                    record['entries'].append({'actor': event['actor'], 'value': copy.deepcopy(event['payload'])})
                    accepted = True
                    if step['op'] == 'append@1' or step['close'] == 'all' and len(record['entries']) == len(self.actors(frame)):
                        record['closed'] = True
                        self.next(now)
            elif event['type'] == 'advance' and step['op'] == 'collect@1' and event['payload'] == {}:
                authority = self.organizer if step['close'] == 'organizer' else frame['turn'] if step['close'] == 'turn' else None
                if event['actor'] == authority and authority is not None:
                    record['closed'] = True
                    self.next(now)
                    accepted = True
        if accepted:
            ledger[event['eventId']] = copy.deepcopy(identity)
            self.settle(now)
        return 'accepted' if accepted else 'rejected'

    def view(self, actor, now=None):
        if actor not in self.participants + [self.organizer]: raise ValueError('unauthorized')
        if now is not None:
            require(integer(now) and now >= self.state['clock'])
            self.settle(now)
        active = self.plan[self.state['pc']] if self.state['pc'] < len(self.plan) else None
        result = {'phase': 'active' if active else 'complete', 'step': active['key'] if active else None, 'turn': active['turn'] if active else None, 'prompt': active['step']['prompt'] if active else None, 'openedAt': self.state['openedAt'] if active else None, 'deadline': min(MAX, self.state['openedAt'] + active['step']['afterMs']) if active and active['step']['afterMs'] is not None else None, 'records': [], 'story': []}
        for record in self.state['records']:
            item = {k: copy.deepcopy(record[k]) for k in ['key', 'step', 'op', 'turn', 'closed', 'revealed']}
            if record['op'] == 'collect@1':
                fields = self.find_step(record['step'])['fields']
                item['count'] = len(record['entries'])
                item['entries'] = []
                for entry in record['entries']:
                    value = {k: copy.deepcopy(v) for k,v in entry['value'].items() if record['revealed'] or entry['actor'] == actor or fields[k]['visibility'] == 'group'}
                    if value: item['entries'].append({'actor': entry['actor'], 'value': value})
            elif record['op'] == 'append@1':
                item['entries'] = copy.deepcopy(record['entries'])
                result['story'].extend(copy.deepcopy(record['entries']))
            else:
                item['counts'] = copy.deepcopy(record['counts'])
            result['records'].append(item)
        return result

def run(request):
    if request.get('action') == 'validate':
        try: validate(request['package']); return {'outcome': 'valid'}
        except (ValueError, TypeError, KeyError): return {'outcome': 'invalid_package'}
    validate(request['package'])
    missing = sorted(set(request['package']['requires']) - (OPS | CAPS))
    if missing: return {'outcome': 'unsupported', 'missing': missing}
    engine = Engine(request['package'], request['participants'], request['organizer'], request.get('startedAt', 0), request.get('state'))
    outcomes, views = [], []
    for event in request.get('events', []):
        outcomes.append(engine.event(event))
        views.append({a: engine.view(a) for a in engine.participants + [engine.organizer]})
    return {'outcomes': outcomes, 'views': views, 'state': engine.state}

if __name__ == '__main__':
    try: print(json.dumps(run(json.load(sys.stdin)), ensure_ascii=False))
    except (ValueError, TypeError, KeyError): print(json.dumps({'outcome':'invalid_package'}))
