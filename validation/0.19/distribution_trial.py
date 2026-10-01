"""Durable single-source assignment, linked-response races and held-out transfer."""
import concurrent.futures
import copy
import json
import sqlite3
import time
from distribution_check import definition,contributions,event
from runtime import run

def saved(h):
    with sqlite3.connect(h.db) as db:return json.loads(db.execute('SELECT state FROM instances WHERE id=?',('test',)).fetchone()[0])

def probes(kind,directory,Host):
    p=definition();h=Host(kind,directory/(kind+'-distribution-race.sqlite'),seed=1)
    try:
        tokens=h.setup(p,participants=list('abcd'))
        # State binds the seed before source collection: process restart cannot reroll it.
        assert saved(h)['assignmentSeed']==1;h.seed=999;h.restart()
        for e in contributions('abcd'):
            h.clock(e['at']);assert h.request('/instances/test/events',{k:e[k] for k in ['eventId','type','step','payload']},tokens[e['actor']])=={'outcome':'accepted'}
        h.clock(10)
        # Concurrent reads race with worker progression; all must observe one assignment.
        with concurrent.futures.ThreadPoolExecutor(4) as pool:views=list(pool.map(lambda _:h.request('/instances/test/view',token=tokens['a'])['view'],range(4)))
        assert all(v==views[0] for v in views);assert views[0]['records'][1]['assignment']==dict(itemId='3',text='source 3')
        state=saved(h);assert state['assignmentSeed']==1 and state['randomState']==307599695
        assert [(a['actor'],a['itemId']) for a in state['records'][1]['assignments']]==[('a','3'),('b','0'),('c','3'),('d','1')]
        h.restart();assert saved(h)==state
        assert h.request('/instances/test/view',token=tokens['organizer'])['view']['records'][1]['assignment'] is None
        assert h.request('/instances/test/view',token='unbound')=={'outcome':'unauthorized'}
        wrong=dict(eventId='wrong',type='submit',step='response',payload={'itemId':'0','text':'wrong source'})
        assert h.request('/instances/test/events',wrong,tokens['a'])=={'outcome':'rejected'}
        forged=dict(wrong,actor='b',at=0,seed=1);assert h.request('/instances/test/events',forged,tokens['a'])=={'outcome':'rejected'}
        submissions=[dict(eventId='race-'+str(i),type='submit',step='response',payload={'itemId':'3','text':'response '+str(i)}) for i in range(2)]
        with concurrent.futures.ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(lambda e:h.request('/instances/test/events',e,tokens['a'])['outcome'],submissions))
        assert sorted(outcomes)==['accepted','rejected'];winner=submissions[outcomes.index('accepted')]
        assert saved(h)['randomState']==307599695
        h.restart();assert h.request('/instances/test/events',winner,tokens['a'])=={'outcome':'replayed'}
        assert h.request('/instances/test/view',token=tokens['b'])['view']['records'][2]['entries']==[]
        assert h.request('/instances/test/view',token=tokens['a'])['view']['records'][2]['entries'][0]['source']==dict(itemId='3',text='source 3')
        h.clock(20)
        deadline=time.monotonic()+3
        while h.request('/instances/test/status')['phase']!='complete':
            assert time.monotonic()<deadline,'linked-response worker stalled';time.sleep(.02)
        after=saved(h);assert after['records'][2]['revealed'] and after['randomState']==307599695
        assert h.request('/instances/test/events',dict(eventId='late',type='submit',step='response',payload={'itemId':'0','text':'late'}),tokens['b'])=={'outcome':'rejected'}
        h.restart();assert h.request('/instances/test/events',winner,tokens['a'])=={'outcome':'replayed'}
        entries=h.request('/instances/test/view',token=tokens['organizer'])['view']['records'][2]['entries']
        assert entries==[dict(actor='a',source=dict(actor='d',itemId='3',text='source 3'),text=winner['payload']['text'])]
        assert h.request('/packages/'+p['id']+'/'+p['version'])['package']==p
        # Tokens cannot set the seed or gain organizer response eligibility.
        assert h.request('/instances',dict(id='bad-seed',packageId=p['id'],version=p['version'],participants=list('abcd'),organizer='organizer',seed=1))=={'outcome':'invalid_request'}
        assert h.request('/instances/bad-seed/status')=={'outcome':'not_found'}
    finally:h.stop()
    # Worker creates the random assignment and closes the whole flow on one clock jump, without reads.
    h=Host(kind,directory/(kind+'-distribution-worker.sqlite'),seed=1)
    try:
        tokens=h.setup(p,participants=list('abcd'))
        for e in contributions('abcd'):
            h.clock(e['at']);assert h.request('/instances/test/events',{k:e[k] for k in ['eventId','type','step','payload']},tokens[e['actor']])=={'outcome':'accepted'}
        h.clock(100);deadline=time.monotonic()+3
        while h.request('/instances/test/status')['phase']!='complete':
            assert time.monotonic()<deadline,'distribution worker stalled';time.sleep(.02)
        state=saved(h);assert state['records'][1]['assignments'] and state['records'][2]['entries']==[] and state['records'][2]['revealed']
        assert state['randomState']==307599695;h.seed=17;h.restart();assert saved(h)==state
    finally:h.stop()
    for missing in ['assign_sources@1','respond@1','reveal_responses@1','policy:seeded_nonself_source@1','seeded_assignment@1']:
        h=Host(kind,directory/(kind+'-missing-'+missing.replace('@','-').replace(':','-')+'.sqlite'),disabled=missing)
        try:
            assert h.request('/packages',{'package':p})['outcome']=='imported'
            assert h.request('/instances',dict(id='unsupported',packageId=p['id'],version=p['version'],participants=list('abcd'),organizer='organizer'))=={'outcome':'unsupported','missing':[missing]}
            assert h.request('/instances/unsupported/status')=={'outcome':'not_found'};support=h.request('/support');assert missing not in support['operations']+support['capabilities']
        finally:h.stop()
    # An invalid trusted test seed is an invalid setup, not a silent default or created state.
    h=Host(kind,directory/(kind+'-invalid-seed.sqlite'),seed=0)
    try:
        h.request('/packages',{'package':p});assert h.request('/instances',dict(id='bad',packageId=p['id'],version=p['version'],participants=list('abcd'),organizer='organizer'))=={'outcome':'invalid_setup'};assert h.request('/instances/bad/status')=={'outcome':'not_found'}
    finally:h.stop()
    # Default host randomness also persists before/after restart; no fixed fixture seed used.
    h=Host(kind,directory/(kind+'-generated-seed.sqlite'),seed=None)
    try:
        h.setup(p,participants=list('abcd'));before=saved(h);assert 1<=before['assignmentSeed']<=4294967295
        h.restart();assert saved(h)==before
    finally:h.stop()
    print(f'{kind}: stable seeded assignment races, changed process seed, linked-response race/replay/privacy, worker-only jumps, unsupported/no-state and generated-seed persistence pass',flush=True)

def transfer(directory,Host):
    hosts=[Host(kind,directory/(kind+'-distribution-transfer.sqlite'),seed=29) for kind in ['python','node']]
    try:
        p=definition('idea-response-and-pairs');p['id']='test.authored-random-response-pairs';p['content']['title']='A new source-response activity with private paired continuation'
        step=p['runbook']['steps'][1];step['policy']='policy:seeded_nonself_source@1';p['requires'].remove('policy:next_nonself_source@1');p['requires'] += ['policy:seeded_nonself_source@1','seeded_assignment@1'];p['runbook']['steps'][2]['close']='deadline'
        received=hosts[0].request('/packages',{'package':p});exported=hosts[0].request('/packages/'+p['id']+'/'+p['version']);imported=hosts[1].request('/packages',{'package':exported['package']});assert received['digest']==exported['digest']==imported['digest']
        people=['🙂','__proto__','9007199254740993','é'];events=contributions(people)+[event('open','tick','system',10,None,{})]
        prefix=run(dict(package=p,participants=people,organizer='organizer',seed=29,events=events));assignments=prefix['state']['records'][1]['assignments']
        for i,a in enumerate(assignments[:2]):events.append(event('response-'+str(i),'submit',a['actor'],11,'response',dict(itemId=a['itemId'],text='response '+str(i))))
        events += [event('close','tick','system',20,None,{}),event('note','submit',people[0],21,'reflection',dict(text='Private pair')),event('done','tick','system',30,None,{})]
        reference=run(dict(package=p,participants=people,organizer='organizer',seed=29,events=events));assert reference['outcomes']==['accepted']*len(events)
        for h in hosts:
            tokens=h.setup(p,participants=people);h.seed=99;h.restart()
            for i,e in enumerate(events):
                h.clock(e['at'])
                if e['type']!='tick':assert h.request('/instances/test/events',{k:e[k] for k in ['eventId','type','step','payload']},tokens[e['actor']])=={'outcome':'accepted'}
                if i==6:h.restart()
            h.restart();views={a:h.request('/instances/test/view',token=tokens[a])['view'] for a in tokens};assert views==reference['views'][-1]
            assert views[people[1]]['records'][4]['count']==1 and views[people[2]]['records'][4]['entries']==[]
        print('Authored random source-response-pairs transfers with opaque actors, stable seed/results and private group continuation',flush=True)
    finally:
        for h in hosts:h.stop()
