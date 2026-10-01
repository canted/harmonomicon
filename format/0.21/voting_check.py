"""New voting/finite-round witnesses: exact deterministic rules and random properties.

No activity ID/name dispatch occurs in the engines. tieChoices belongs solely to
this trusted test harness; it is deliberately absent from the package schema.
"""
import copy
import json
from pathlib import Path
from runtime import run

HERE = Path(__file__).resolve().parent
PEOPLE = list('abc')


def package(name):
    return json.loads((HERE / 'examples' / (name + '.json')).read_text())


def event(identifier, actor, at, step, payload=None, kind='submit'):
    return dict(eventId=identifier, actor=actor, at=at, step=step,
                payload={} if payload is None else payload, type=kind)


def ballot(identifier, actor, at, source, item, step='vote'):
    return event(identifier, actor, at, step,
                 {'candidate': {'source': source, 'itemId': item}})


def control(actors, opening=None, closing=None):
    return dict(actors=list(actors), opensAt=opening, closesAt=closing)


def fixture_request(case):
    return {**{k: copy.deepcopy(v) for k, v in case.items()
               if k not in ['id', 'definition', 'package', 'outcomes', 'checks']},
            'package': copy.deepcopy(case.get('definition') or package(case['package']))}


def at_path(value, path):
    for key in path:
        value = value[key]
    return value


def record(result, op):
    return next(r for r in result['state']['records'] if r['op'] == op)


def check_fixture(case, node):
    request = fixture_request(case)
    result = run(request)
    assert result == node(request), (case['id'], 'independent engines disagree')
    assert result['outcomes'] == case['outcomes'], (case['id'], result['outcomes'])
    for assertion in case['checks']:
        view = result['views'][assertion['after']][assertion['actor']]
        if assertion.get('missing'):
            try:
                at_path(view, assertion['path'])
            except (KeyError, IndexError):
                pass
            else:
                raise AssertionError((case['id'], 'unexpected disclosure', assertion))
        else:
            assert at_path(view, assertion['path']) == assertion['equals'], (case['id'], assertion, view)
    # Serialize and recover at every accepted, rejected and replayed action boundary.
    for cut in range(len(request['events']) + 1):
        prefix = run(dict(request, events=request['events'][:cut]))
        resumed = dict(request, state=prefix['state'], events=request['events'][cut:])
        restored = run(resumed)
        assert restored == node(resumed), (case['id'], 'recovery parity', cut)
        assert restored['state'] == result['state'], (case['id'], 'recovery state', cut)
    return result


def invalid_definitions(node, schema=None):
    variants = []
    structural = []

    def bad(name, change, schema_reject=False):
        p = package(name)
        change(p)
        variants.append(p)
        if schema_reject:
            structural.append(p)

    bad('predefined-vote', lambda p: p['requires'].remove('vote@1'))
    bad('predefined-vote', lambda p: p['requires'].remove('host_controls@1'))
    bad('predefined-vote', lambda p: p['requires'].remove('tally@2'))
    bad('predefined-vote', lambda p: p['requires'].remove('select@1'))
    bad('predefined-vote', lambda p: p['requires'].remove('present@1'))
    bad('predefined-vote', lambda p: p['requires'].remove('policy:most_votes@1'))
    bad('contribution-contest', lambda p: p['requires'].remove('policy:random_tie@1'))
    bad('creative-continuation', lambda p: p['requires'].remove('artifact_pool@2'))
    bad('contribution-contest', lambda p: p['requires'].remove('image_contributions@1'))
    bad('contribution-contest', lambda p: p['requires'].remove('audio_contributions@1'))
    bad('contribution-contest', lambda p: p['runbook']['steps'][1]['candidates'].update(source='future'))
    bad('contribution-contest', lambda p: p['runbook']['steps'][1]['candidates'].update(source='contest_totals'))
    bad('predefined-vote', lambda p: p['runbook']['steps'][0].update(changes='replacement_workflow'), True)
    bad('predefined-vote', lambda p: p['runbook']['steps'][0].update(ballots='anonymous'), True)
    bad('predefined-vote', lambda p: p['runbook']['steps'][0].update(roles=['voter']), True)
    bad('predefined-vote', lambda p: p['runbook']['steps'][0].update(candidates={'source':'x','options':[]}), True)
    bad('predefined-vote', lambda p: p['runbook']['steps'][0].update(candidates={'options':[]}), True)
    bad('predefined-vote', lambda p: p['runbook']['steps'][0]['candidates']['options'][1].update(id='repair'))
    bad('predefined-vote', lambda p: p['runbook']['steps'][0]['candidates']['options'][0].update(id=''), True)
    bad('predefined-vote', lambda p: p['runbook']['steps'][0]['candidates']['options'][0].update(label=''), True)
    bad('predefined-vote', lambda p: p['runbook']['steps'][0]['candidates']['options'][0].update(id='bad\ud800'))
    bad('predefined-vote', lambda p: p['runbook']['steps'][0]['candidates']['options'].append({'id':'extra','label':'Extra','value':'hidden'}), True)
    bad('predefined-vote', lambda p: p['runbook']['steps'][1].update(source='poll_choice'))
    bad('predefined-vote', lambda p: p['runbook']['steps'][2].update(source='vote'))
    bad('predefined-vote', lambda p: p['runbook']['steps'][2].update(policy='policy:weighted_votes@1'), True)
    bad('predefined-vote', lambda p: p['runbook']['steps'][2].update(ties='person_then_random'), True)
    bad('predefined-vote', lambda p: p['runbook']['steps'][3].update(source='vote'))
    bad('predefined-vote', lambda p: p['runbook']['steps'][3].update(audience='sms'), True)
    bad('predefined-vote', lambda p: p['runbook']['steps'][3].update(prompt={'template':'${winner}'}), True)
    bad('creative-continuation', lambda p: p['runbook']['steps'][5].update(round='verse_one'))
    bad('creative-continuation', lambda p: p['runbook']['steps'][5].update(round='bad-name'), True)
    bad('creative-continuation', lambda p: p['runbook']['steps'][5].update(input={'result':'two_choice'}))
    bad('creative-continuation', lambda p: p['runbook']['steps'][5].update(input={'result':'one_totals'}))
    bad('creative-continuation', lambda p: p['runbook']['steps'][5].update(input={'result':'one_choice','path':'selected'}), True)
    bad('creative-continuation', lambda p: p['runbook']['steps'][0].update(input={'value':{'kind':'audio','ref':'clip'}}), True)
    bad('creative-continuation', lambda p: p['runbook']['steps'][0].update(input={'value':{'kind':'text','text':''}}), True)
    bad('creative-continuation', lambda p: p['runbook']['steps'][0].update(input={'value':{'kind':'text','text':'seed','actor':'a'}}), True)
    bad('creative-continuation', lambda p: p['runbook']['steps'][0].update(kinds=['video']), True)
    bad('creative-continuation', lambda p: p['runbook']['steps'][0].update(perActor=2), True)
    bad('creative-continuation', lambda p: p['runbook']['steps'][0].update(eligibility={'excludeWinner':'previous'}), True)

    def predefined_input(p):
        source = package('creative-continuation')['runbook']['steps'][5]
        source['input'] = {'result':'poll_choice'}
        p['runbook']['steps'].append(source)
        p['requires'].append('artifact_pool@2')
    bad('predefined-vote', predefined_input)

    def nested(p):
        p['runbook']['steps'] = [{'id':'each','op':'for_each@1','over':'participants','steps':p['runbook']['steps']}]
        p['requires'].append('for_each@1')
    for name in ['predefined-vote', 'contribution-contest', 'creative-continuation']:
        bad(name, nested, True)

    def wrong_reveal(p):
        p['runbook']['steps'].append({'id':'reveal','op':'reveal_ballots@1','source':'poll_totals'})
        p['requires'].append('reveal_ballots@1')
    bad('predefined-vote', wrong_reveal)

    def missing_reveal(p):
        p['runbook']['steps'].append({'id':'reveal','op':'reveal_ballots@1','source':'vote'})
    bad('predefined-vote', missing_reveal)

    for index, p in enumerate(variants):
        request = {'action':'validate','package':p}
        assert run(request) == node(request) == {'outcome':'invalid_package'}, ('invalid voting definition', index)
    if schema is not None:
        import jsonschema
        validator = jsonschema.Draft202012Validator(schema)
        for p in structural:
            assert list(validator.iter_errors(p)), ('schema accepted unsupported shape', p)
    return len(variants), len(structural)


def execution_boundaries(node):
    p = package('predefined-vote')
    p['runbook']['steps'][0]['changes'] = 'allowed'
    request = dict(package=p, participants=PEOPLE, organizer='organizer',
                   hostInputs={'vote':control(PEOPLE,0,10)}, events=[
                       ballot('old','a',9,'vote','repair'),
                       ballot('new','a',9,'vote','garden'),
                       ballot('b','b',9,'vote','garden'),
                       ballot('boundary','c',10,'vote','repair'),
                       ballot('old','a',10,'vote','repair'),
                       ballot('new','a',10,'vote','repair')])
    result = run(request)
    assert result == node(request)
    assert result['outcomes'] == ['accepted','accepted','accepted','rejected','replayed','rejected']
    tally = record(result,'tally@2')['output']
    assert [row['count'] for row in tally['counts']] == [0,2,0] and tally['totalVotes'] == 2
    # Same-timestamp close/action races are judged in their serialized order.
    submit = ballot('cast','a',5,'vote','repair')
    close = event('end','system',5,'vote',kind='close')
    for events, outcomes, counted in [([submit,close],['accepted','accepted'],1),
                                      ([close,submit],['accepted','rejected'],0)]:
        r = dict(request,events=events)
        result = run(r)
        assert result == node(r) and result['outcomes'] == outcomes
        assert record(result,'tally@2')['output']['totalVotes'] == counted
    # An ordinary actor cannot reconfigure voting or close it.
    events = [event('forged-close','a',0,'vote',kind='close'),
              event('forged-config','a',0,'vote',control(PEOPLE,0,20),'configure'),
              event('bad-date','system',0,'vote',control(PEOPLE,0,0),'configure'),
              event('add-voter','system',0,'vote',control(PEOPLE+['new'],0,20),'configure'),
              ballot('new-vote','new',1,'vote','repair')]
    r = dict(request,events=events)
    result = run(r)
    assert result == node(r) and result['outcomes'] == ['rejected']*3+['accepted']*2
    assert result['views'][-1]['new']['records'][0]['submitted'] is True
    # Restore-bound setup cannot secretly substitute another vote window.
    r = dict(request,events=[])
    initial = run(r)
    changed = dict(r,state=initial['state'],hostInputs={'vote':control(PEOPLE,0,30)})
    assert run(changed) == node(changed) == {'outcome':'invalid_setup'}
    # Unsupported negotiated capability is clear and does not create state.
    p = package('predefined-vote');p['requires'].append('unlimited_rounds@1')
    r = dict(package=p,participants=PEOPLE,organizer='organizer',events=[])
    assert run({'action':'validate','package':p}) == node({'action':'validate','package':p}) == {'outcome':'valid'}
    assert run(r) == node(r) == {'outcome':'unsupported','missing':['unlimited_rounds@1']}



def workshop_boundaries(node):
    p = package('proposal-workshop')
    request = dict(package=p, participants=list('abcd'), organizer='organizer',
                   hostInputs={'proposals':control('abcd',0,10),
                               'vote':control('abcd',10,20),
                               'plans':control('abcd',20,30)}, events=[
                       event('proposal-a','a',1,'proposals',{'itemId':'A','value':{'kind':'text','text':'Add a repair table'}}),
                       event('proposal-b','b',1,'proposals',{'itemId':'B','value':{'kind':'text','text':'Add plants'}}),
                       event('open-vote','system',10,None,kind='tick'),
                       ballot('vote-a','a',11,'proposals','A'),
                       ballot('vote-b','b',11,'proposals','B'),
                       event('tie','system',20,None,kind='tick'),
                       event('discuss','a',21,'exercise',{'text':'Compare the two tied proposals before choosing.'})])
    result = run(request)
    assert result == node(request) and result['outcomes'] == ['accepted']*7
    view = result['views'][5]['a']
    assert view['step'] == 'exercise' and view['prompt'] == p['runbook']['steps'][7]['prompt']
    assert view['records'][4]['output']['status'] == 'tie'
    assert view['records'][5]['blocked'] is True and view['records'][5]['entries'] == []
    assert view['records'][5]['input'] == {'status':'tie','predecessorRound':'proposing','candidate':None}
    assert result['views'][6]['b']['records'][7]['entries'] == [{'actor':'a','value':{'text':'Compare the two tied proposals before choosing.'}}]
    assert result['views'][6]['c']['records'][7]['entries'] == []
    prefix = run(dict(request,events=request['events'][:6]))
    restored = dict(request,state=prefix['state'],events=request['events'][6:])
    assert run(restored) == node(restored) and run(restored)['state'] == result['state']
    # The example promises exact pairs, so an odd roster is an invalid setup.
    odd = dict(request,participants=list('abcde'),events=[])
    assert run(odd) == node(odd) == {'outcome':'invalid_setup'}


def random_properties(node):
    case = next(c for c in json.loads((HERE/'conformance/voting-cases.json').read_text())
                if c['id']=='random-tie-and-explicit-next-round-input')
    request = fixture_request(case)
    request['events'] = request['events'][:6]
    # Empty and unique outcomes need no random draw, even with a random policy.
    for name in ['current-ballots-private-public-totals', 'empty-candidate-set',
                 'no-votes-blocks-linked-round', 'text-image-audio-candidates']:
        fixture = next(c for c in json.loads((HERE/'conformance/voting-cases.json').read_text()) if c['id']==name)
        r = dict(fixture_request(fixture), tieChoices=[])
        result = run(r)
        assert result == node(r) and result['state']['tieDraws'] == 0
    # Inject both tied positions: deterministic expected results, no RNG parity claim.
    for index in [0,1]:
        r = dict(request,tieChoices=[index])
        result = run(r)
        assert result == node(r)
        selected = record(result,'select@1')['output']['selected']
        assert selected == record(result,'select@1')['output']['tied'][index]
        assert result['state']['tieDraws'] == 1
    # Default host randomness has membership and durable-choice obligations, not
    # identical cross-host streams. Check each independent host separately.
    request.pop('tieChoices',None)
    for runner in [run,node]:
        for _ in range(8):
            result = runner(request)
            output = record(result,'select@1')['output']
            assert output['selected'] in output['tied'] and len(output['tied']) == 2
            assert result['state']['tieDraws'] == 1
            repeated = dict(request,state=result['state'],events=[
                event('read-tick','system',20,None,kind='tick'),
                ballot('vote-a-one','a',20,'continuations_one','same','vote_one')])
            restored = runner(repeated)
            assert restored['outcomes'] == ['accepted','replayed']
            assert record(restored,'select@1')['output'] == output
            assert restored['state']['tieDraws'] == 1
            # A committed result can transfer to the other host without a redraw.
            other = node if runner is run else run
            assert other(repeated) == restored


def check(node, schema=None):
    cases = json.loads((HERE/'conformance/voting-cases.json').read_text())
    for case in cases:
        check_fixture(case,node)
        if schema is not None:
            import jsonschema
            jsonschema.validate(fixture_request(case)['package'],schema)
    invalid_count, structural_count = invalid_definitions(node,schema)
    execution_boundaries(node)
    workshop_boundaries(node)
    random_properties(node)
    if schema is not None:
        import jsonschema
        for name in ['predefined-vote','contribution-contest','creative-continuation','proposal-workshop']:
            jsonschema.validate(package(name),schema)
    print(f'{len(cases)} voting/linked-round traces; {invalid_count} invalid definitions; '
          f'{structural_count} schema negatives; every-boundary recovery, privacy, '
          'current-vote counts, reference/eligibility/deadline/close races, '
          'held-out group exercise and durable random properties pass')
    return invalid_count


if __name__ == '__main__':
    from check import node
    check(node,json.loads((HERE/'package.schema.json').read_text()))
