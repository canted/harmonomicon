"""Instruction-level voting, outcomes, presentation and finite linked rounds."""
import copy
import re
import artifacts

OPS = {'artifact_pool@2', 'vote@1', 'tally@2', 'select@1', 'present@1', 'reveal_ballots@1'}
POLICIES = {'policy:most_votes@1', 'policy:random_tie@1'}
WINDOWS = {'artifact_pool@2', 'vote@1'}


def name(value):
    return type(value) is str and re.fullmatch('[a-z][a-z0-9_]{0,47}', value) is not None


def contribution_source(selection, known):
    """A linked input must come from a typed contribution vote, never labels."""
    tally = known.get(selection.get('source'), {})
    vote = known.get(tally.get('source'), {})
    candidates = vote.get('candidates', {})
    return known.get(candidates.get('source'), {}) if type(candidates) is dict else {}


def validate(step, known, used, nested, rounds):
    demand, exact, text = artifacts.demand, artifacts.exact, artifacts.text
    demand(not nested)
    op = step['op']
    if op == 'artifact_pool@2':
        demand(exact(step, ['id', 'op', 'prompt', 'kinds', 'visibility', 'round', 'input']))
        demand(text(step['prompt']) and artifacts.kinds(step['kinds']) and step['visibility'] in ['private', 'group'])
        demand(name(step['round']) and step['round'] not in rounds)
        rounds.add(step['round'])
        source = step['input']
        if source is not None:
            demand(type(source) is dict)
            if exact(source, ['value']):
                demand(exact(source['value'], ['kind', 'text']) and source['value']['kind'] == 'text' and text(source['value']['text']))
            else:
                demand(exact(source, ['result']) and type(source['result']) is str)
                selection = known.get(source['result'], {})
                demand(selection.get('op') == 'select@1' and contribution_source(selection, known).get('op') in ['artifact_pool@1', 'artifact_pool@2'])
        used.add('host_controls@1')
        for kind in step['kinds']:
            if kind != 'text': used.add(kind + '_contributions@1')
    elif op == 'vote@1':
        demand(exact(step, ['id', 'op', 'prompt', 'candidates', 'changes', 'ballots']))
        demand(text(step['prompt']) and step['changes'] in ['allowed', 'forbidden'] and step['ballots'] in ['private', 'group'])
        candidates = step['candidates']
        if exact(candidates, ['source']):
            demand(type(candidates['source']) is str and known.get(candidates['source'], {}).get('op') in ['artifact_pool@1', 'artifact_pool@2'])
        else:
            demand(exact(candidates, ['options']))
            options = candidates['options']
            demand(type(options) is list and 2 <= len(options) <= 32)
            demand(all(exact(option, ['id', 'label']) and text(option['id']) and text(option['label']) for option in options))
            demand(len({option['id'] for option in options}) == len(options))
        used.add('host_controls@1')
    elif op == 'tally@2':
        demand(exact(step, ['id', 'op', 'source']) and type(step['source']) is str and known.get(step['source'], {}).get('op') == 'vote@1')
    elif op == 'select@1':
        demand(exact(step, ['id', 'op', 'source', 'policy', 'ties']) and type(step['source']) is str and known.get(step['source'], {}).get('op') == 'tally@2')
        demand(step['policy'] == 'policy:most_votes@1' and step['ties'] in ['unresolved', 'random'])
        used.add(step['policy'])
        if step['ties'] == 'random': used.add('policy:random_tie@1')
    elif op == 'present@1':
        demand(exact(step, ['id', 'op', 'source', 'prompt', 'audience']) and type(step['source']) is str and known.get(step['source'], {}).get('op') in ['tally@2', 'select@1'])
        demand(text(step['prompt']) and step['audience'] == 'group')
    else:
        demand(exact(step, ['id', 'op', 'source']) and type(step['source']) is str and known.get(step['source'], {}).get('op') == 'vote@1')
    known[step['id']] = step


def initialize(e, choose_tie, restored=False):
    if not any(step['op'] == 'select@1' and step['ties'] == 'random' for step in e.definitions.values()):
        return
    if choose_tie is not None: artifacts.demand(callable(choose_tie))
    if restored: artifacts.demand('tieDraws' in e.state)
    else: e.state['tieDraws'] = 0
    artifacts.demand(artifacts.integer(e.state['tieDraws']))


def candidates(e, step, frame):
    spec = step['candidates']
    if 'options' in spec:
        return [{'ref': {'source': step['id'], 'itemId': option['id']}, 'label': option['label']} for option in spec['options']]
    source = e.source(spec['source'], frame)
    definition = e.find_step(source['step'])
    eligible = source['effective']['actors']
    return [{'ref': {'source': source['step'], 'itemId': entry['itemId']}, 'actor': entry['actor'], 'value': copy.deepcopy(entry['value']), 'round': definition.get('round')} for entry in source['entries'] if entry['actor'] in eligible]


def linked_input(e, step, frame):
    spec = step['input']
    if spec is None:
        return {'status': 'none', 'predecessorRound': None, 'candidate': None}
    if 'value' in spec:
        return {'status': 'initial', 'predecessorRound': None, 'candidate': {'value': copy.deepcopy(spec['value'])}}
    outcome = e.source(spec['result'], frame)['output']
    selected = copy.deepcopy(outcome['selected'])
    predecessor = contribution_source(e.find_step(spec['result']), e.definitions)
    return {'status': outcome['status'], 'predecessorRound': predecessor.get('round'), 'candidate': selected}


def settle(e, frame, now):
    step = frame['step']; op = step['op']; record = e.record(frame)
    if op in WINDOWS:
        control = artifacts.control(e, frame)
        record['effective'] = copy.deepcopy(control)
        if op == 'artifact_pool@2' and 'input' not in record:
            record['round'] = step['round']
            record['input'] = linked_input(e, step, frame)
            record['blocked'] = record['input']['status'] in ['tie', 'no_votes', 'no_candidates']
        if op == 'artifact_pool@2' and record['blocked']:
            record['closed'] = True; e.next(e.state['openedAt']); return 'advance'
        if op == 'vote@1' and 'candidates' not in record:
            record['candidates'] = candidates(e, step, frame)
        if op == 'vote@1' and not record['candidates']:
            record['closed'] = True; e.next(e.state['openedAt']); return 'advance'
        if control['closesAt'] is not None and now >= control['closesAt']:
            record['closed'] = True; e.next(max(control['closesAt'], e.state['openedAt'])); return 'advance'
        return 'wait'
    if not record['closed']:
        if op == 'tally@2':
            vote = e.source(step['source'], frame)
            ballots = [entry for entry in vote['entries'] if entry['actor'] in vote['effective']['actors']]
            record['output'] = {'counts': [{'candidate': copy.deepcopy(candidate), 'count': sum(entry['candidate'] == candidate['ref'] for entry in ballots)} for candidate in vote['candidates']], 'totalVotes': len(ballots)}
        elif op == 'select@1':
            output = copy.deepcopy(e.source(step['source'], frame)['output'])
            output.update(status='no_candidates' if not output['counts'] else 'no_votes', selected=None, tied=[])
            if output['counts'] and output['totalVotes']:
                greatest = max(row['count'] for row in output['counts'])
                tied = [copy.deepcopy(row['candidate']) for row in output['counts'] if row['count'] == greatest]
                if len(tied) == 1:
                    output.update(status='selected', selected=tied[0])
                elif step['ties'] == 'unresolved':
                    output.update(status='tie', tied=tied)
                else:
                    index = e.choose_tie(len(tied))
                    artifacts.demand(artifacts.integer(index) and index < len(tied))
                    e.state['tieDraws'] += 1
                    output.update(status='selected', selected=tied[int(index)], tied=tied)
            record['output'] = output
        elif op == 'present@1':
            record['output'] = copy.deepcopy(e.source(step['source'], frame)['output'])
        else:
            e.source(step['source'], frame)['revealed'] = True
        record['closed'] = True
    e.next(e.state['openedAt']); return 'advance'


def event(e, frame, event):
    step = frame['step']; record = e.record(frame); control = artifacts.control(e, frame)
    payload = event['payload']; now = event['at']
    if event['actor'] == 'system' and event['type'] == 'configure':
        if not artifacts.safe_control(e, payload) or payload['closesAt'] is not None and payload['closesAt'] <= now: return False
        bound = list(dict.fromkeys(artifacts.bindings(e) + payload['actors']))
        if len(bound) > 256: return False
        e.state['controls'][step['id']] = copy.deepcopy(payload)
        e.state['hostActors'] = bound; record['effective'] = copy.deepcopy(payload)
        return True
    if event['actor'] == 'system' and event['type'] == 'close' and payload == {}:
        record['closed'] = True; e.next(now); return True
    if event['type'] != 'submit' or event['actor'] not in control['actors'] or now < artifacts.opening(e, frame): return False
    previous = next((entry for entry in record['entries'] if entry['actor'] == event['actor']), None)
    if step['op'] == 'artifact_pool@2':
        if previous is not None or not artifacts.exact(payload, ['itemId', 'value']) or not artifacts.text(payload['itemId']): return False
        if any(entry['itemId'] == payload['itemId'] for entry in record['entries']) or not artifacts.valid_value(e, event['actor'], payload['value'], step['kinds']): return False
        record['entries'].append({'actor': event['actor'], 'itemId': payload['itemId'], 'value': copy.deepcopy(payload['value'])}); return True
    if previous is not None and step['changes'] == 'forbidden': return False
    if not artifacts.exact(payload, ['candidate']) or not artifacts.exact(payload['candidate'], ['source', 'itemId']): return False
    if not any(candidate['ref'] == payload['candidate'] for candidate in record['candidates']): return False
    ballot = {'actor': event['actor'], 'candidate': copy.deepcopy(payload['candidate'])}
    if previous is None: record['entries'].append(ballot)
    else: record['entries'][record['entries'].index(previous)] = ballot
    return True


def projection(e, record, item, actor):
    op = record['op']; definition = e.find_step(record['step'])
    if op in WINDOWS:
        item['eligible'] = actor in record['effective']['actors']
        item['opensAt'] = record['effective']['opensAt']; item['closesAt'] = record['effective']['closesAt']
        if op == 'artifact_pool@2':
            item.update(round=record['round'], input=copy.deepcopy(record['input']), blocked=record['blocked'], count=len(record['entries']))
            item['entries'] = [copy.deepcopy(entry) for entry in record['entries'] if entry['actor'] == actor or definition['visibility'] == 'group']
        else:
            item['candidates'] = copy.deepcopy(record['candidates'])
            item['submitted'] = any(entry['actor'] == actor for entry in record['entries'])
            item['entries'] = [copy.deepcopy(entry) for entry in record['entries'] if entry['actor'] == actor or definition['ballots'] == 'group' or record['revealed']]
    elif op == 'present@1':
        item['output'] = copy.deepcopy(record['output'])
