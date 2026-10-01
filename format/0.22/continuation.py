"""Qualified contribution inputs and explicitly configured fallback outcomes."""
import copy
import re
import artifacts
import voting

OPS = {'artifact_pool@3', 'vote@2', 'tally@3', 'select@2', 'present@2', 'reveal_ballots@2'}
WINDOWS = {'artifact_pool@3', 'vote@2'}
POLICIES = {'policy:random_candidate@1', 'policy:retain_input@1'}


def uuid_urn(value):
    return type(value) is str and re.fullmatch(r'urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', value) is not None


def declarations(package, used):
    declared = package.get('inputs', {})
    artifacts.demand(type(declared) is dict and len(declared) <= 8 and all(voting.name(key) for key in declared))
    for declaration in declared.values():
        artifacts.demand(artifacts.exact(declaration, ['type', 'kinds']) and declaration['type'] == 'contribution' and artifacts.kinds(declaration['kinds']))
        for kind in declaration['kinds']:
            if kind != 'text': used.add(kind + '_contributions@1')
    if declared: used.add('contribution_inputs@1')
    return declared


def selected_pool(selection, known):
    tally = known.get(selection.get('source'), {})
    vote = known.get(tally.get('source'), {})
    candidates = vote.get('candidates', {})
    return known.get(candidates.get('source'), {}) if type(candidates) is dict else {}


def validate(step, known, used, nested, rounds, declared, consumed):
    demand, exact, text = artifacts.demand, artifacts.exact, artifacts.text
    demand(not nested)
    op = step['op']
    if op == 'artifact_pool@3':
        demand(exact(step, ['id', 'op', 'prompt', 'kinds', 'visibility', 'round', 'input']))
        demand(text(step['prompt']) and artifacts.kinds(step['kinds']) and step['visibility'] in ['private', 'group'])
        demand(voting.name(step['round']) and step['round'] not in rounds)
        rounds.add(step['round'])
        source = step['input']
        if source is not None:
            demand(type(source) is dict)
            if exact(source, ['binding']):
                demand(type(source['binding']) is str and source['binding'] in declared)
                consumed.add(source['binding'])
            else:
                demand(exact(source, ['result']) and type(source['result']) is str)
                selection = known.get(source['result'], {})
                demand(selection.get('op') == 'select@2' and selected_pool(selection, known).get('op') == 'artifact_pool@3')
        used.add('host_controls@1')
        for kind in step['kinds']:
            if kind != 'text': used.add(kind + '_contributions@1')
    elif op == 'vote@2':
        demand(exact(step, ['id', 'op', 'prompt', 'candidates', 'changes', 'ballots']))
        demand(text(step['prompt']) and step['changes'] in ['allowed', 'forbidden'] and step['ballots'] in ['private', 'group'])
        demand(exact(step['candidates'], ['source']) and type(step['candidates']['source']) is str and known.get(step['candidates']['source'], {}).get('op') == 'artifact_pool@3')
        used.add('host_controls@1')
    elif op == 'tally@3':
        demand(exact(step, ['id', 'op', 'source']) and type(step['source']) is str and known.get(step['source'], {}).get('op') == 'vote@2')
    elif op == 'select@2':
        demand(exact(step, ['id', 'op', 'source', 'policy', 'ties'] + (['noVotes'] if 'noVotes' in step else [])))
        demand(type(step['source']) is str and known.get(step['source'], {}).get('op') == 'tally@3')
        demand(step['policy'] == 'policy:most_votes@1' and step['ties'] in ['unresolved', 'random'])
        used.add(step['policy'])
        if step['ties'] == 'random': used.add('policy:random_tie@1')
        fallback = step.get('noVotes', 'unresolved')
        demand(fallback in ['unresolved', 'random', 'retain_input'])
        if fallback == 'random': used.add('policy:random_candidate@1')
        elif fallback == 'retain_input':
            used.add('policy:retain_input@1')
            demand(selected_pool(step, known).get('input') is not None)
    elif op == 'present@2':
        demand(exact(step, ['id', 'op', 'source', 'prompt', 'audience']) and type(step['source']) is str and known.get(step['source'], {}).get('op') in ['tally@3', 'select@2'])
        demand(text(step['prompt']) and step['audience'] == 'group')
    else:
        demand(exact(step, ['id', 'op', 'source']) and type(step['source']) is str and known.get(step['source'], {}).get('op') == 'vote@2')
    known[step['id']] = step


def needs_contract(e):
    return bool(e.package.get('inputs')) or any(step['op'] in OPS for step in e.definitions.values())


def valid_value(value, kinds):
    if type(value) is not dict or value.get('kind') not in kinds: return False
    if value['kind'] == 'text': return artifacts.exact(value, ['kind', 'text']) and artifacts.text(value['text'])
    return artifacts.exact(value, ['kind', 'ref']) and artifacts.text(value['ref']) and len(value['ref']) <= 256


def valid_candidate(candidate, kinds):
    if not artifacts.exact(candidate, ['ref', 'actor', 'value', 'round']): return False
    ref = candidate['ref']
    return (artifacts.exact(ref, ['instance', 'source', 'itemId']) and uuid_urn(ref['instance']) and voting.name(ref['source']) and artifacts.text(ref['itemId'])
            and artifacts.text(candidate['actor']) and candidate['actor'] != 'system' and valid_value(candidate['value'], kinds)
            and (candidate['round'] is None or voting.name(candidate['round'])))


def valid_binding(binding, kinds):
    if not artifacts.exact(binding, ['candidate', 'via']) or not valid_candidate(binding['candidate'], kinds): return False
    via, candidate = binding['via'], binding['candidate']
    if type(via) is not dict or not uuid_urn(via.get('instance')) or not (via.get('round') is None or voting.name(via.get('round'))): return False
    if artifacts.exact(via, ['instance', 'source', 'itemId', 'round']):
        return {key: via[key] for key in ['instance', 'source', 'itemId']} == candidate['ref'] and via['round'] == candidate['round']
    return artifacts.exact(via, ['instance', 'result', 'round']) and voting.name(via['result'])


def attested(e, bindings, viewers):
    if not bindings: return True
    if not callable(e.authorize_input): return False
    for binding in bindings.values():
        try:
            if e.authorize_input(copy.deepcopy(binding), viewers[:]) is not True: return False
        except Exception: return False
    return True


def initialize(e, instance_id, input_bindings, authorize_input, restored, choose_tie):
    e.authorize_input = authorize_input
    if not needs_contract(e):
        artifacts.demand(input_bindings is None or input_bindings == {})
        return
    declared = e.package.get('inputs', {})
    if restored:
        artifacts.demand(uuid_urn(e.state.get('instanceId')) and type(e.state.get('inputBindings')) is dict)
        artifacts.demand(instance_id is None or instance_id == e.state['instanceId'])
        artifacts.demand(input_bindings is None or input_bindings == e.state['inputBindings'])
        supplied = e.state['inputBindings']
    else:
        artifacts.demand(uuid_urn(instance_id))
        supplied = {} if input_bindings is None else input_bindings
    artifacts.demand(type(supplied) is dict and set(supplied) == set(declared))
    artifacts.demand(all(valid_binding(supplied[key], declaration['kinds']) for key, declaration in declared.items()))
    if not restored:
        artifacts.demand(attested(e, supplied, artifacts.bindings(e)))
        e.state['instanceId'] = instance_id
        e.state['inputBindings'] = copy.deepcopy(supplied)
    randomized = any(step['op'] == 'select@2' and (step['ties'] == 'random' or step.get('noVotes') == 'random') for step in e.definitions.values())
    if randomized:
        artifacts.demand(choose_tie is None or callable(choose_tie))
        if restored: artifacts.demand('tieDraws' in e.state)
        else: e.state.setdefault('tieDraws', 0)
        artifacts.demand(artifacts.integer(e.state['tieDraws']))


def authorize_expansion(e, actors):
    bound = list(dict.fromkeys(artifacts.bindings(e) + actors))
    if len(bound) > 256: return False
    if not any(actor not in artifacts.bindings(e) for actor in actors): return True
    return attested(e, e.state.get('inputBindings', {}), bound)


def qualified(e, source, entry):
    return {'ref': {'instance': e.state['instanceId'], 'source': source['step'], 'itemId': entry['itemId']}, 'actor': entry['actor'], 'value': copy.deepcopy(entry['value']), 'round': e.find_step(source['step'])['round']}


def pool_input(e, step, frame):
    source = step['input']
    if source is None: return {'status': 'none', 'predecessorRound': None, 'candidate': None, 'via': None}
    if 'binding' in source:
        binding = e.state['inputBindings'][source['binding']]
        return {'status': 'initial', 'predecessorRound': binding['via']['round'], 'candidate': copy.deepcopy(binding['candidate']), 'via': copy.deepcopy(binding['via'])}
    output = e.source(source['result'], frame)['output']
    pool = selected_pool(e.find_step(source['result']), e.definitions)
    return {'status': output['status'], 'predecessorRound': pool['round'], 'candidate': copy.deepcopy(output['selected']), 'via': {'instance': e.state['instanceId'], 'result': source['result'], 'round': pool['round']}}


def draw(e, candidates):
    if len(candidates) == 1: return copy.deepcopy(candidates[0])
    artifacts.demand(artifacts.integer(e.state.get('tieDraws')) and e.state['tieDraws'] < artifacts.MAX)
    index = e.choose_tie(len(candidates))
    artifacts.demand(artifacts.integer(index) and index < len(candidates))
    e.state['tieDraws'] += 1
    return copy.deepcopy(candidates[int(index)])


def outcome(e, step, frame):
    output = copy.deepcopy(e.source(step['source'], frame)['output'])
    output.update(status='no_candidates', selected=None, tied=[], basis=None)
    if not output['counts']: return output
    if not output['totalVotes']:
        output['status'] = 'no_votes'
        fallback = step.get('noVotes', 'unresolved')
        if fallback == 'random': output.update(status='selected', selected=draw(e, [row['candidate'] for row in output['counts']]), basis='random_no_votes')
        elif fallback == 'retain_input':
            pool = selected_pool(step, e.definitions)
            candidate = e.source(pool['id'], frame)['input']['candidate']
            if candidate is not None: output.update(status='selected', selected=copy.deepcopy(candidate), basis='retained_input')
        return output
    highest = max(row['count'] for row in output['counts'])
    tied = [row['candidate'] for row in output['counts'] if row['count'] == highest]
    if len(tied) == 1: output.update(status='selected', selected=copy.deepcopy(tied[0]), basis='most_votes')
    elif step['ties'] == 'unresolved': output.update(status='tie', tied=copy.deepcopy(tied))
    else: output.update(status='selected', selected=draw(e, tied), tied=copy.deepcopy(tied), basis='random_tie')
    return output


def settle(e, frame, now):
    step = frame['step']; op = step['op']; record = e.record(frame)
    if op in WINDOWS:
        record['effective'] = copy.deepcopy(artifacts.control(e, frame))
        if op == 'artifact_pool@3':
            if 'input' not in record:
                record['round'] = step['round']; record['input'] = pool_input(e, step, frame)
                record['blocked'] = record['input']['status'] not in ['none', 'initial', 'selected']
            if record['blocked']:
                record['closed'] = True; e.next(e.state['openedAt']); return 'advance'
        else:
            if 'candidates' not in record:
                source = e.source(step['candidates']['source'], frame)
                record['candidates'] = [qualified(e, source, entry) for entry in source['entries'] if entry['actor'] in source['effective']['actors']]
            if not record['candidates']:
                record['closed'] = True; e.next(e.state['openedAt']); return 'advance'
        deadline = record['effective']['closesAt']
        if deadline is not None and now >= deadline:
            record['closed'] = True; e.next(max(deadline, e.state['openedAt'])); return 'advance'
        return 'wait'
    if not record['closed']:
        if op == 'tally@3':
            vote = e.source(step['source'], frame)
            ballots = [entry for entry in vote['entries'] if entry['actor'] in vote['effective']['actors']]
            record['output'] = {'counts': [{'candidate': copy.deepcopy(candidate), 'count': sum(entry['candidate'] == candidate['ref'] for entry in ballots)} for candidate in vote['candidates']], 'totalVotes': len(ballots)}
        elif op == 'select@2': record['output'] = outcome(e, step, frame)
        elif op == 'present@2': record['output'] = copy.deepcopy(e.source(step['source'], frame)['output'])
        else: e.source(step['source'], frame)['revealed'] = True
        record['closed'] = True
    e.next(e.state['openedAt']); return 'advance'


def event(e, frame, event):
    step = frame['step']; record = e.record(frame); control = artifacts.control(e, frame); payload = event['payload']; now = event['at']
    if event['actor'] == 'system' and event['type'] == 'configure':
        if not artifacts.safe_control(e, payload) or payload['closesAt'] is not None and payload['closesAt'] <= now: return False
        bound = list(dict.fromkeys(artifacts.bindings(e) + payload['actors']))
        if len(bound) > 256: return False
        e.state['controls'][step['id']] = copy.deepcopy(payload); e.state['hostActors'] = bound; record['effective'] = copy.deepcopy(payload)
        return True
    if event['actor'] == 'system' and event['type'] == 'close' and payload == {}:
        record['closed'] = True; e.next(now); return True
    if event['type'] != 'submit' or event['actor'] not in control['actors'] or now < artifacts.opening(e, frame): return False
    previous = next((entry for entry in record['entries'] if entry['actor'] == event['actor']), None)
    if step['op'] == 'artifact_pool@3':
        if previous is not None or not artifacts.exact(payload, ['itemId', 'value']) or not artifacts.text(payload['itemId']): return False
        if any(entry['itemId'] == payload['itemId'] for entry in record['entries']) or not artifacts.valid_value(e, event['actor'], payload['value'], step['kinds']): return False
        record['entries'].append({'actor': event['actor'], 'itemId': payload['itemId'], 'value': copy.deepcopy(payload['value'])}); return True
    if previous is not None and step['changes'] == 'forbidden': return False
    if not artifacts.exact(payload, ['candidate']) or not artifacts.exact(payload['candidate'], ['instance', 'source', 'itemId']): return False
    if not any(candidate['ref'] == payload['candidate'] for candidate in record['candidates']): return False
    ballot = {'actor': event['actor'], 'candidate': copy.deepcopy(payload['candidate'])}
    if previous is None: record['entries'].append(ballot)
    else: record['entries'][record['entries'].index(previous)] = ballot
    return True


def projection(e, record, item, actor):
    definition = e.find_step(record['step'])
    if record['op'] in WINDOWS:
        item['eligible'] = actor in record['effective']['actors']; item['opensAt'] = record['effective']['opensAt']; item['closesAt'] = record['effective']['closesAt']
        if record['op'] == 'artifact_pool@3':
            item.update(round=record['round'], input=copy.deepcopy(record['input']), blocked=record['blocked'], count=len(record['entries']))
            item['entries'] = [copy.deepcopy(entry) for entry in record['entries'] if entry['actor'] == actor or definition['visibility'] == 'group']
        else:
            item['candidates'] = copy.deepcopy(record['candidates']); item['submitted'] = any(entry['actor'] == actor for entry in record['entries'])
            item['entries'] = [copy.deepcopy(entry) for entry in record['entries'] if entry['actor'] == actor or definition['ballots'] == 'group' or record['revealed']]
    elif record['op'] == 'present@2': item['output'] = copy.deepcopy(record['output'])
