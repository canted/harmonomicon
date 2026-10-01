#!/usr/bin/env python3
"""Run normative witnesses in the independent Python and JavaScript engines."""
import copy
import json
import subprocess
import sys
from pathlib import Path
from runtime import Engine, run, validate
HERE=Path(__file__).resolve().parent
PEOPLE=['a','b','c']

def package(name):return json.loads((HERE/'examples'/f'{name}.json').read_text())
def node(request):
    return json.loads(subprocess.check_output(['node',str(HERE/'runtime.mjs')],input=json.dumps(request,ensure_ascii=True),text=True))
def value_at(view,path):
    for key in path:view=view[key]
    return view

def check_case(case):
    p=case.get('definition') or package(case['package'])
    request=dict(package=p,participants=case.get('participants',PEOPLE),organizer='organizer',events=case['events'],settings=case.get('settings',{}),seed=case.get('seed'))
    python_result=run(request)
    js_result=node(request)
    assert python_result==js_result,case['id']+' engines disagree'
    assert python_result['outcomes']==case['outcomes'],(case['id'],python_result['outcomes'])
    for check in case['checks']:
        view=python_result['views'][check['after']][check['actor']]
        if check.get('missing'):
            try:value_at(view,check['path'])
            except (KeyError,IndexError):pass
            else:raise AssertionError((case['id'],'private field exposed',check))
        else:
            assert value_at(view,check['path'])==check['equals'],(case['id'],check,view)
    # Continue every trace from a serialized state at every event boundary.
    for cut in range(len(case['events'])+1):
        prefix=run(dict(request,events=case['events'][:cut]))
        resumed=dict(request,state=prefix['state'],events=case['events'][cut:])
        assert run(resumed)==node(resumed)
        assert run(resumed)['state']==python_result['state'],(case['id'],'restart changed state',cut)
    return python_result

def invalid_packages():
    base=package('two-truths')
    variants=[]
    def add(change):
        p=copy.deepcopy(base);change(p);variants.append(p)
    add(lambda p:p.update(format='harmonomicon.activity-package/0.12'))
    add(lambda p:p.update(behavior={'contract':'hidden_answer_guess@1'}))
    add(lambda p:p['requires'].remove('collect@1'))
    add(lambda p:p['requires'].remove('private_views@1'))
    add(lambda p:p['runbook']['steps'][0]['steps'][0].update(op='guess_game@1'))
    add(lambda p:p['runbook']['steps'][0]['steps'][1].update(id='publish'))
    add(lambda p:p['runbook']['steps'][0]['steps'][1]['fields']['guess'].update(indexOf='future.items'))
    add(lambda p:p['runbook']['steps'][0]['steps'][0]['fields']['items'].update(visibility='private'))
    add(lambda p:p['runbook']['steps'][0]['steps'][0].update(close='anybody'))
    add(lambda p:p['runbook']['steps'][0]['steps'].append(copy.deepcopy(p['runbook']['steps'][0])))
    add(lambda p:p['runbook']['steps'].append({'id':'outside','op':'reveal@1','sources':['guess']}))
    add(lambda p:p['participants'].update(max=1))
    add(lambda p:p.update(version='01.0.0'))
    add(lambda p:p.update(id='harmonomicon.example\n'))
    add(lambda p:p.update(version='0.1.0\n'))
    add(lambda p:p['content'].update(title='bad\ud800'))
    poll=package('choice-poll');poll['runbook']['steps'].pop(1);variants.append(poll)
    def fresh(name, change):
        p=package(name);change(p);variants.append(p)
    fresh('gratitude-pool',lambda p:p['requires'].remove('policy:pool_order@1'))
    fresh('gratitude-pool',lambda p:p['runbook']['steps'][0].update(perActor=0))
    fresh('gratitude-pool',lambda p:p['runbook']['steps'][0].update(close='deadline',afterMs=None))
    fresh('gratitude-pool',lambda p:p['runbook']['steps'][1].update(source='future'))
    fresh('gratitude-pool',lambda p:p['runbook']['steps'][1].update(policy='policy:random@1'))
    fresh('gratitude-pool',lambda p:p['runbook']['steps'][1]['steps'][1].update(source='slips'))
    fresh('gratitude-pool',lambda p:p['runbook']['steps'][1]['steps'][2].update(source='claim'))
    fresh('gratitude-pool',lambda p:p['runbook']['steps'][1]['steps'].append(copy.deepcopy(p['runbook']['steps'][1])))
    fresh('partner-rounds',lambda p:p['runbook']['steps'][1].update(maxSize=13))
    fresh('partner-rounds',lambda p:p['runbook']['steps'][2].update(source='close'))
    fresh('partner-rounds',lambda p:p['runbook']['steps'][2].update(close='deadline',afterMs=None))
    fresh('one-two-four-all',lambda p:p['runbook']['steps'][3].update(afterMs=10))
    fresh('scheduled-check-in',lambda p:p['settings']['opens_at'].update(type='text'))
    fresh('scheduled-check-in',lambda p:p['settings']['opens_at'].update(default=1))
    fresh('scheduled-check-in',lambda p:p['settings']['question'].update(default=''))
    fresh('scheduled-check-in',lambda p:p['requires'].remove('instance_settings@1'))
    fresh('scheduled-check-in',lambda p:p['runbook']['steps'][1].update(until={'setting':'unknown'}))
    fresh('scheduled-check-in',lambda p:p['runbook']['steps'][1].update(prompt={'setting':'closes_at'}))
    fresh('scheduled-check-in',lambda p:p['runbook']['steps'][1].update(close='all'))
    fresh('scheduled-check-in',lambda p:p['runbook']['steps'][0].update(until=True))
    fresh('scheduled-check-in',lambda p:p['runbook']['steps'][0].update(until={'setting':'opens_at','extra':1}))
    fresh('scheduled-check-in',lambda p:p['runbook']['steps'][1].update(actors='turn'))
    fresh('scheduled-check-in',lambda p:p['settings'].update({'bad-name':{'type':'text'}}))
    fresh('two-truths',lambda p:p['runbook']['steps'][0]['steps'].append({'id':'wait','op':'wait_until@1','until':10,'prompt':'Wait'}))
    fresh('crowd-scoring',lambda p:p['requires'].remove('integer_values@1'))
    fresh('crowd-scoring',lambda p:p['requires'].remove('policy:roster_offset@1'))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][0].update(perActor=2))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][1].update(offset=0))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][1].update(offset=100))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][3].update(offset=1))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][3].update(round='round_1'))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][2].update(source='ideas'))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][2].update(min=6))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][2].update(close='organizer'))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][2].update(afterMs=None))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][11].update(sources=['future']))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][11].update(sources=['rate_1','rate_1']))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][4].update(max=4))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][11].update(targetCount=None))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][12].update(source='rate_1'))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][12].update(limit=0))
    fresh('crowd-scoring',lambda p:p['runbook']['steps'][12].update(policy='policy:random_tie@1'))
    fresh('proposal-assessment',lambda p:p['runbook']['steps'][5].update(targetCount=5))
    fresh('check-in',lambda p:p['runbook']['steps'][0]['fields'].update(answer={'type':'integer','visibility':'private','min':0,'max':1000001}))
    for p in variants:
        request={'action':'validate','package':p}
        assert run(request)==node(request)=={'outcome':'invalid_package'}
    return len(variants)

def held_out():
    # The exact arrangement is newly authored here using existing operations.
    p=package('check-in');story=package('timed-story')
    p['runbook']['steps']+=story['runbook']['steps']
    p['requires']=sorted(set(p['requires']+story['requires']))
    p['id']='harmonomicon.checkinthenstory'
    validate(p)
    events=[dict(eventId=f'answer-{a}',type='submit',actor=a,at=1,step='answer',payload={'answer':a}) for a in PEOPLE]
    events += [dict(eventId=f'write-{i}',type='submit',actor=a,at=2+i,step=f'write:{i}',payload={'text':a+' adds a line'}) for i,a in enumerate(PEOPLE)]
    request=dict(package=p,participants=PEOPLE,organizer='organizer',events=events)
    result=run(request)
    assert result==node(request)
    assert result['outcomes']==['accepted']*6
    assert result['views'][-1]['a']['phase']=='complete'
    assert len(result['views'][-1]['a']['story'])==3
    return p

def pooled_combination():
    p=package('pooled-ideas-and-pairs');people=['a','b','c','d']
    events=[dict(eventId='item-'+a,type='submit',actor=a,at=0,step='slips',payload={'itemId':'i'+a,'text':a+' idea'}) for a in people]
    for i,a in enumerate(['b','c','d','a']):
        events += [dict(eventId='take-'+str(i),type='claim',actor=a,at=0,step='claim:'+str(i),payload={}),dict(eventId='read-'+str(i),type='advance',actor=a,at=0,step='read:'+str(i),payload={})]
    events += [dict(eventId='note',type='submit',actor='a',at=0,step='discuss',payload={'text':'Our pair reflection'}),dict(eventId='done',type='advance',actor='organizer',at=0,step='discuss',payload={})]
    request=dict(package=p,participants=people,organizer='organizer',events=events)
    result=run(request);assert result==node(request)
    assert result['outcomes']==['accepted']*len(events)
    final=result['views'][-1];assert final['a']['phase']=='complete'
    assert final['b']['records'][-1]['entries']==[{'actor':'a','value':{'text':'Our pair reflection'}}]
    assert final['c']['records'][-1]['entries']==final['organizer']['records'][-1]['entries']==[]
    return p,people,events

def extra_boundaries():
    # Mathematical integer JSON numbers have the same value in both runtimes.
    p=package('check-in');p['runbook']['steps'][0]['afterMs']=100.0
    request=dict(package=p,participants=PEOPLE,organizer='organizer',events=[])
    assert run(request)==node(request)
    from runtime import canonical
    assert canonical(p)==subprocess.check_output(['node','--input-type=module','-e',"import {canonical} from './runtime.mjs'; import fs from 'node:fs'; console.log(canonical(JSON.parse(fs.readFileSync(0,'utf8'))));"],cwd=HERE,input=json.dumps(p),text=True).strip()
    p=package('check-in');e=Engine(p,PEOPLE,'organizer')
    event=dict(eventId='one',type='submit',actor='a',at=1,step='answer',payload={'answer':'hello'})
    assert e.event(event)=='accepted'
    assert e.event(dict(event,payload={'answer':True}))=='rejected'
    assert e.event(dict(event,at=0))=='rejected'
    try:e.view('intruder')
    except ValueError:pass
    else:raise AssertionError('unbound actor read')
    assert e.view('a',3600000)['phase']=='complete'
    # A late tick advances multiple timed roster turns at their original boundaries.
    request=dict(package=package('timed-story'),participants=PEOPLE,organizer='organizer',events=[dict(eventId='jump',type='tick',actor='system',at=180000,step=None,payload={})])
    assert run(request)==node(request)
    assert run(request)['views'][0]['a']['phase']=='complete'
    # An empty timed-out publication cannot manufacture an indexable list.
    p2=package('two-truths')
    p2['runbook']['steps'][0]['steps'][0]['afterMs']=10
    p2['runbook']['steps'][0]['steps'][1]['afterMs']=10
    request=dict(package=p2,participants=PEOPLE,organizer='organizer',events=[
        dict(eventId='empty',type='tick',actor='system',at=10,step=None,payload={}),
        dict(eventId='bad',type='submit',actor='b',at=11,step='guess:0',payload={'guess':0}),
        dict(eventId='next',type='tick',actor='system',at=20,step=None,payload={})])
    assert run(request)==node(request)
    assert run(request)['outcomes']==['accepted','rejected','accepted']
    assert run(request)['views'][-1]['a']['step']=='publish:1'
    p3=package('check-in');p3['requires'].append('unavailable@1')
    request=dict(package=p3,participants=PEOPLE,organizer='organizer',events=[])
    assert run(dict(action='validate',package=p3))=={'outcome':'valid'}
    assert run(request)==node(request)=={'outcome':'unsupported','missing':['unavailable@1']}
    # Accepted IDs can be object-prototype names; no special ID semantics.
    request=dict(package=p,participants=PEOPLE,organizer='organizer',events=[dict(event,eventId='__proto__'),dict(event,eventId='__proto__',at=2)])
    assert run(request)==node(request)
    assert run(request)['outcomes']==['accepted','replayed']

def scoring_boundaries():
    p=package('proposal-assessment');p['runbook']['steps'][3]['offset']=4
    request=dict(package=p,participants=['a','b','c','d'],organizer='organizer',events=[])
    assert node(request)==run(request)=={'outcome':'invalid_setup'}
    # Integer-valued floats normalize exactly, including scaled means and maximum numeric bounds.
    p=package('proposal-assessment');p['runbook']['steps']=p['runbook']['steps'][:-2]
    for step in p['runbook']['steps']:
        if step['op']=='rate@1':step.update(min=0,max=1000000)
    p['runbook']['steps'][5].update(policy='policy:mean_scaled_scores@1',targetCount=100.0)
    p['requires'].append('policy:mean_scaled_scores@1')
    people=['🙂','__proto__','9007199254740993','é']
    events=[dict(eventId='idea-'+str(i),type='submit',actor=a,at=0,step='ideas',payload={'itemId':str(i),'text':'Item '+str(i)}) for i,a in enumerate(people)]
    events.append(dict(eventId='open',type='tick',actor='system',at=300000,step=None,payload={}))
    for round in [1,2]:
        for i,a in enumerate(people):events.append(dict(eventId='score-'+str(round)+'-'+str(i),type='submit',actor=people[(i+round)%4],at=300000+(round-1)*60000,step='rate_'+str(round),payload={'itemId':str(i),'round':'round_'+str(round),'score':1000000.0}))
        events.append(dict(eventId='close-'+str(round),type='tick',actor='system',at=300000+round*60000,step=None,payload={}))
    request=dict(package=p,participants=people,organizer='organizer',events=events)
    result=run(request);assert result==node(request)
    final=result['views'][-1]['organizer'];assert final['records'][5]['ranking'][0]['score']=={'numerator':100000000,'denominator':1}
    assert [r['itemId'] for r in final['records'][5]['ranking']]==['0','1','2','3']
    assert final['records'][1]['assignments']==[]
    # Equal exact means with different score counts and totals have the same rank.
    tied=copy.deepcopy(request);tied['package']=copy.deepcopy(p);tied['package']['runbook']['steps'][5]['targetCount']=5
    tied['events']=[copy.deepcopy(e) for e in events if e['type']=='tick' or e['step']=='ideas' or (e['payload'].get('itemId')=='0') or (e['payload'].get('itemId')=='1' and e['payload'].get('round')=='round_1')]
    for e in tied['events']:
        if e['type']=='submit' and e['step'].startswith('rate_'):
            e['payload']['score']=3 if e['payload']['itemId']=='1' else 2 if e['payload']['round']=='round_1' else 4
    tied_result=run(tied);assert tied_result==node(tied)
    leaders=tied_result['views'][-1]['organizer']['records'][5]['ranking']
    assert [r['score'] for r in leaders]==[{'numerator':15,'denominator':1}]*2 and [r['rank'] for r in leaders]==[1,1]
    # Unpublished aggregate results must not appear in any actor projection.
    p['runbook']['steps'].pop();p['runbook']['steps'].append(dict(id='wait',op='pause@1',prompt='Wait before publication.',afterMs=1000))
    p['requires'].append('pause@1');request['package']=p;result=run(request);assert result==node(request)
    for actor in people+['organizer']:assert 'ranking' not in result['views'][-1][actor]['records'][5] and 'results' not in result['views'][-1][actor]['records'][5]
    print('Routing setup, opaque IDs, safe integer scoring, rational ties, and unpublished aggregate privacy pass')

def scheduled_boundaries():
    p=package('scheduled-check-in')
    valid={'opens_at':10,'closes_at':20}
    invalid=[{}, {'opens_at':10},dict(valid,extra=1),dict(valid,opens_at=True),dict(valid,closes_at=10),dict(valid,closes_at=9),dict(valid,opens_at=-1),dict(valid,question=''),dict(valid,question='bad\ud800'),dict(valid,closes_at=9007199254740992),dict(valid,opens_at=10.5)]
    for values in invalid:
        try: Engine(p,PEOPLE,'organizer',settings=values)
        except (ValueError,TypeError): pass
        else: raise AssertionError(('invalid settings accepted',values))
        assert node(dict(package=p,participants=PEOPLE,organizer='organizer',settings=values,events=[]))=={'outcome':'invalid_setup'}
    try: Engine(p,PEOPLE,'organizer',started_at=11,settings=valid)
    except ValueError: pass
    else: raise AssertionError('creation after opening accepted')
    assert node(dict(package=p,participants=PEOPLE,organizer='organizer',startedAt=11,settings=valid,events=[]))=={'outcome':'invalid_setup'}
    e=Engine(p,PEOPLE,'organizer',settings=valid)
    assert e.view('a')['prompt']==p['content']['prompt']
    try: Engine(p,PEOPLE,'organizer',state=e.state,settings=dict(valid,question='Different'))
    except ValueError: pass
    else: raise AssertionError('settings changed on restart')
    assert node(dict(package=p,participants=PEOPLE,organizer='organizer',state=e.state,settings=dict(valid,question='Different'),events=[]))=={'outcome':'invalid_setup'}
    assert Engine(p,PEOPLE,'organizer',state=e.state).state==e.state
    # Final boundary may equal the maximum safe clock for the migrated check-in.
    high={'opens_at':9007199254740990,'closes_at':9007199254740991}
    req=dict(package=p,participants=PEOPLE,organizer='organizer',settings=high,events=[dict(eventId='last',type='tick',actor='system',at=high['closes_at'],step=None,payload={})])
    assert run(req)==node(req) and run(req)['views'][-1]['a']['phase']=='complete'
    # Literal deadlines and structured choices can use the same reveal/tally rules.
    poll=json.loads((HERE/'conformance/scheduled-poll-package.json').read_text())
    vote=poll['runbook']['steps'][0];key=next(iter(vote['fields']));option=vote['fields'][key]['options'][0]
    req=dict(package=poll,participants=PEOPLE,organizer='organizer',events=[dict(eventId='vote',type='submit',actor='a',at=0,step=vote['id'],payload={key:option}),dict(eventId='close',type='tick',actor='system',at=50,step=None,payload={})])
    result=run(req);assert result==node(req);assert result['views'][-1]['a']['records'][-1]['counts'][0]['count']==1
    print('Scheduled setup, immutable restart, maximum clock, and structured deadline collection pass')

def group_boundaries():
    # A timed-out partition has no groups, so its collection cannot wait forever.
    p=package('partner-rounds');p['runbook']['steps']=p['runbook']['steps'][1:3]
    p['runbook']['steps'][0]['afterMs']=10
    request=dict(package=p,participants=['a','b','c','d'],organizer='organizer',events=[dict(eventId='timeout',type='tick',actor='system',at=10,step=None,payload={})])
    result=run(request);assert result==node(request)
    assert result['views'][-1]['a']['phase']=='complete'
    assert result['views'][-1]['a']['records'][-1]['entries']==[]
    # Feasibility is checked for manual group sizes as well as automatic chunks.
    p=package('partner-rounds')
    p['runbook']['steps'][1].update(minSize=3,maxSize=3)
    try: Engine(p,['a','b','c','d'],'organizer')
    except ValueError: pass
    else: raise AssertionError('impossible manual groups accepted')
    assert node(dict(package=p,participants=['a','b','c','d'],organizer='organizer',events=[]))=={'outcome':'invalid_setup'}

def migration_check():
    rows=json.loads((HERE/'migration.json').read_text())
    originals={p.name:json.loads(p.read_text()) for p in (HERE.parent/'0.12/examples').glob('*.json')}
    assert len(rows)==len(originals)==20
    assert len({row['example'] for row in rows})==20
    assert {row['example'] for row in rows}==set(originals)
    for row in rows:
        assert row['behavior']==originals[row['example']]['behavior']['contract']
        assert row['status'] in ['expressible','needs_operations','outside_scope']
        if row['status']=='needs_operations': assert row['missing']
        if row['status']=='expressible':
            assert row.get('evidence') and all((HERE/path).exists() for path in row['evidence'])
    print('Migration checklist covers all 20 earlier packages; six full migrations have comparison evidence')

def prior_compatibility():
    # Historical engines run in separate processes/module environments. Translate
    # only the candidate envelope: retained operations must preserve full state.
    def previous(request, language):
        old=copy.deepcopy(request)
        old['package']['format']='harmonomicon.activity-package/0.21'
        binary=sys.executable if language=='python' else 'node'
        file='runtime.py' if language=='python' else 'runtime.mjs'
        return json.loads(subprocess.check_output([binary,str(HERE.parent/'0.21'/file)],input=json.dumps(old),text=True))
    requests=[]
    for case in json.loads((HERE/'conformance/cases.json').read_text()):
        p=copy.deepcopy(case['definition']) if 'definition' in case else package(case['package'])
        requests.append(dict(package=p,participants=case.get('participants',PEOPLE),organizer='organizer',events=case['events'],settings=case.get('settings',{}),seed=case.get('seed')))
    from image_check import witnesses
    requests += [req for req,_ in witnesses()]
    from artifact_check import cases as artifact_cases
    requests += [req for req,_ in artifact_cases()]
    from voting_check import fixture_request
    requests += [fixture_request(case) for case in json.loads((HERE/'conformance/voting-cases.json').read_text())]
    for request in requests:
        after=run(request)
        assert previous(request,'python')==after,('Python historical compatibility',request.get('id'))
        assert previous(request,'javascript')==node(request)==after,('JavaScript historical compatibility',request.get('id'))
    print(f'All {len(requests)} prior 0.21 traces preserve outcomes, actor views and full state in both historical engines')

if __name__=='__main__':
    cases=json.loads((HERE/'conformance/cases.json').read_text())
    for case in cases:check_case(case);print('ok',case['id'])
    from migration_check import check_reference
    check_reference()
    from recurrence_check import check_reference as check_recurrence, boundaries as recurrence_boundaries
    check_recurrence()
    recurrence_count=recurrence_boundaries(node)
    from distribution_check import boundaries as distribution_boundaries
    distribution_count=distribution_boundaries(node)
    from image_check import check as check_images
    image_count=check_images(node)
    from artifact_check import check as check_artifacts
    artifact_count=check_artifacts(node)
    from voting_check import check as check_voting
    voting_count=check_voting(node)
    from input_check import check as check_inputs
    input_count=check_inputs(node)
    count=invalid_packages();scoring_boundaries();scheduled_boundaries();held_out();extra_boundaries();pooled_combination();migration_check();prior_compatibility();group_boundaries()
    if '--schema' in sys.argv:
        import jsonschema
        schema=json.loads((HERE/'package.schema.json').read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        from distribution_check import schema_negatives
        schema_negatives(schema)
        check_images(node,schema)
        check_artifacts(node,schema)
        check_voting(node,schema)
        check_inputs(node,schema)
        for path in (HERE/'examples').glob('*.json'): jsonschema.validate(json.loads(path.read_text()),schema)
        jsonschema.validate(held_out(),schema)
        jsonschema.validate(json.loads((HERE/'conformance/scheduled-poll-package.json').read_text()),schema)
        for case in cases:
            if 'definition' in case: jsonschema.validate(case['definition'],schema)
        print('Draft 2020-12 schema, all examples and held-out compositions pass')
    voting_traces=len(json.loads((HERE/'conformance/voting-cases.json').read_text()))
    input_traces=len(json.loads((HERE/'conformance/input-cases.json').read_text()))
    print(f'{len(cases)+10+voting_traces+input_traces} composed traces ({len(cases)+10+voting_traces} retained plus {input_traces} qualified-input/fallback), {count+recurrence_count+distribution_count+image_count+artifact_count+voting_count+input_count} invalid definitions, restart at every boundary, and cross-family compositions pass in Python and JavaScript')
