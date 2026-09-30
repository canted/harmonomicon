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
    p=package(case['package'])
    request=dict(package=p,participants=PEOPLE,organizer='organizer',events=case['events'])
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

if __name__=='__main__':
    cases=json.loads((HERE/'conformance/cases.json').read_text())
    for case in cases:check_case(case);print('ok',case['id'])
    count=invalid_packages();held_out();extra_boundaries()
    if '--schema' in sys.argv:
        import jsonschema
        schema=json.loads((HERE/'package.schema.json').read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        for path in (HERE/'examples').glob('*.json'): jsonschema.validate(json.loads(path.read_text()),schema)
        jsonschema.validate(held_out(),schema)
        print('Draft 2020-12 schema, six examples and held-out composition pass')
    print(f'{len(cases)} composed traces, {count} invalid definitions, restart at every boundary, and an unseen combination pass in Python and JavaScript')
