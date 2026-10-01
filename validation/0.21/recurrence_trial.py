"""Recurrence through authenticated durable hosts and retained 0.12 hosts."""
import concurrent.futures
import copy
import importlib.util
import json
import sqlite3
import time
from pathlib import Path
from recurrence_check import fixtures, definition, adapted_event, project
from runtime import run
ROOT=Path(__file__).resolve().parents[2]

def compare_hosts(kind,directory,Host):
    spec=importlib.util.spec_from_file_location('legacy_recurrence_host',ROOT/'validation/0.12/run.py')
    legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    scenarios=fixtures()
    for scenario in scenarios:
        name=scenario['package'];instance=scenario['instance'];people=instance['participants'];organizer=instance['organizer'];p=definition(name)
        old=legacy.Host(kind,directory/(kind+'-old-recurrence-'+scenario['id']+'.sqlite'));new=Host(kind,directory/(kind+'-new-recurrence-'+scenario['id']+'.sqlite'))
        try:
            old.set_clock(instance['createdAt']);new.clock(instance['createdAt']);old_tokens={a:'legacy-'+a for a in people+[organizer]}
            source=json.loads((ROOT/'format/0.12/examples'/f'{name}.json').read_text())
            status,created=old.request('POST','/admin/instances',dict(instanceId='comparison',packageId=source['id'],packageVersion=source['version'],participants=people,organizer=organizer,startsAt=instance['startsAt'],tokens=old_tokens),admin=True)
            assert status==201 and created['status']=='created',created
            new.request('/packages',{'package':p});created=new.request('/instances',dict(id='comparison',packageId=p['id'],version=p['version'],participants=people,organizer=organizer,settings={'starts_at':instance['startsAt']}));assert created['outcome']=='created',created;tokens=created['tokens']
            def compare():
                for actor in people+[organizer]:
                    status,before=old.request('GET','/instances/comparison/view',token=old_tokens[actor]);after=new.request('/instances/comparison/view',token=tokens[actor])['view']
                    assert status==200 and before==project(after,actor,people,name),(kind,scenario['id'],actor,before,after)
            compare()
            for i,action in enumerate(scenario['actions']):
                at=action['event']['at'] if 'event' in action else action['view']['at'];old.set_clock(at);new.clock(at)
                if 'event' in action and action['event']['type']!='tick':
                    e=action['event'];mapped=adapted_event(e)
                    status,before=old.request('POST','/instances/comparison/events',{k:e[k] for k in ['eventId','type','payload']},token=old_tokens[e['actor']]);after=new.request('/instances/comparison/events',{k:mapped[k] for k in ['eventId','type','step','payload']},tokens[e['actor']]);assert status==200 and before['outcome']==after['outcome']==action['outcome'],(scenario['id'],i,before,after)
                compare()
                if i==len(scenario['actions'])//2:old.restart();new.restart();compare()
            old.restart();new.restart();compare()
        finally:old.close();new.stop()
    print(f'{kind}: {len(scenarios)} recurrence migrations match actual retained 0.12 app; gap/history/privacy and restart pass',flush=True)

def probes(kind,directory,Host):
    p=definition('daily-private-practice');p['id']='test.recurrence-race';p['runbook']['steps'][0].update(intervalMs=20,windowMs=10,occurrences=3)
    h=Host(kind,directory/(kind+'-recurrence-race.sqlite'))
    try:
        tokens=h.setup(p,settings={'starts_at':10});h.restart();h.clock(10)
        submissions=[dict(eventId='race-'+str(i),type='submit',step='entry:0',payload={'value':str(i)}) for i in range(2)]
        with concurrent.futures.ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(lambda e:h.request('/instances/test/events',e,tokens['a'])['outcome'],submissions))
        assert sorted(outcomes)==['accepted','rejected'];winner=submissions[outcomes.index('accepted')]
        h.restart();assert h.request('/instances/test/events',winner,tokens['a'])=={'outcome':'replayed'}
        assert h.request('/instances/test/view',token=tokens['b'])['view']['records'][1]['entries']==[]
        assert h.request('/instances/test/view',token='unbound')=={'outcome':'unauthorized'}
        assert h.request('/instances/test/events',dict(winner,actor='b',at=0),tokens['a'])=={'outcome':'rejected'}
        h.clock(25);gap=h.request('/instances/test/view',token=tokens['organizer'])['view'];assert gap['step']=='practice:1' and gap['deadline']==30
        assert h.request('/instances/test/events',dict(eventId='gap',type='submit',step='entry:1',payload={'value':'gap'}),tokens['b'])=={'outcome':'rejected'}
        h.restart();h.clock(30)
        assert h.request('/instances/test/events',dict(eventId='stale',type='submit',step='entry:0',payload={'value':'stale'}),tokens['b'])=={'outcome':'rejected'}
        # No participant read or event after this clock jump: use persisted status and DB only.
        h.clock(100);deadline=time.monotonic()+3
        while h.request('/instances/test/status')['phase']!='complete':
            assert time.monotonic()<deadline,'recurrence worker stalled';time.sleep(.02)
        with sqlite3.connect(h.db) as db:state=json.loads(db.execute('SELECT state FROM instances WHERE id=?',('test',)).fetchone()[0])
        windows=[r for r in state['records'] if r['op']=='collect_window@1'];assert len(windows)==3 and all(r['closed'] for r in windows)
        h.restart();assert h.request('/instances/test/events',winner,tokens['a'])=={'outcome':'replayed'}
        final=h.request('/instances/test/view',token=tokens['organizer'])['view'];assert all(e==[] for e in [r['entries'] for r in final['records'] if r['op']=='collect_window@1'])
        assert final['records'][5]['statuses']==[{'actor':a,'status':'missed'} for a in 'abc']
        # Invalid setup creates no state, including overflow and binding failures.
        for i,settings in enumerate([{}, {'starts_at':101}, {'starts_at':9007199254740991}, {'starts_at':True}]):
            if i==1:continue # A future first opening is valid.
            result=h.request('/instances',dict(id='bad-'+str(i),packageId=p['id'],version=p['version'],participants=list('abc'),organizer='organizer',settings=settings));assert result=={'outcome':'invalid_setup'}
            assert h.request('/instances/bad-'+str(i)+'/status')=={'outcome':'not_found'}
    finally:h.stop()
    for missing in ['for_windows@1','collect_window@1','completion_status@1']:
        h=Host(kind,directory/(kind+'-missing-'+missing.replace('@','-')+'.sqlite'),missing)
        try:
            h.request('/packages',{'package':p});assert h.request('/instances',dict(id='unsupported',packageId=p['id'],version=p['version'],participants=list('abc'),organizer='organizer',settings={'starts_at':10}))=={'outcome':'unsupported','missing':[missing]}
            assert h.request('/instances/unsupported/status')=={'outcome':'not_found'};support=h.request('/support');assert missing not in support['operations']+support['capabilities']
        finally:h.stop()
    print(f'{kind}: recurrence race, replay after restart, gap/stale rejection, worker-only long jump and unsupported/no-state probes pass',flush=True)

def transfer(directory,Host):
    hosts=[Host(kind,directory/(kind+'-recurrence-transfer.sqlite')) for kind in ['python','node']]
    try:
        p=definition('repeated-poll-and-pairs');p['id']='test.authored-recurring-assessment';p['content']['title']='A newly authored recurring choice and reflection';p['runbook']['steps'][0]['occurrences']=3
        imported=hosts[0].request('/packages',{'package':p});exported=hosts[0].request('/packages/'+p['id']+'/'+p['version']);received=hosts[1].request('/packages',{'package':exported['package']});assert imported['digest']==received['digest']==exported['digest']
        people=['🙂','__proto__','9007199254740993','é'];events=[dict(eventId='choice-'+str(i),type='submit',actor=people[i%4],at=10+20*i,step=f'entry:{i}',payload={'choice':'draw'}) for i in range(3)]
        events += [dict(eventId='close',type='tick',actor='system',at=60,step=None,payload={}),dict(eventId='note',type='submit',actor=people[0],at=61,step='reflection',payload={'text':'private'}),dict(eventId='done',type='tick',actor='system',at=60060,step=None,payload={})]
        ref=run(dict(package=p,participants=people,organizer='organizer',settings={'starts_at':10},events=events));assert ref['outcomes']==['accepted']*len(events)
        for h in hosts:
            tokens=h.setup(p,participants=people,settings={'starts_at':10});h.restart()
            for i,e in enumerate(events):
                h.clock(e['at'])
                if e['type']!='tick':assert h.request('/instances/test/events',{k:e[k] for k in ['eventId','type','step','payload']},tokens[e['actor']])=={'outcome':'accepted'}
                if i==1:h.restart()
            h.restart();views={a:h.request('/instances/test/view',token=tokens[a])['view'] for a in tokens};assert views==ref['views'][-1]
        print('Authored recurrence-to-pairs transfers and runs with opaque actors, immutable settings and durable private continuation',flush=True)
    finally:
        for h in hosts:h.stop()
