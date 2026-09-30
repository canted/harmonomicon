#!/usr/bin/env python3
"""Two local app hosts: composed traces, durable execution, races and transfer."""
import concurrent.futures
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'format/0.19'))
from runtime import run
from check import held_out, package, pooled_combination
CASES=json.loads((ROOT/'format/0.19/conformance/cases.json').read_text())
PEOPLE=['a','b','c'];ADMIN='local-test-admin'
class Host:
    def __init__(self,kind,db,disabled=None,seed=1729):
        self.kind,self.db,self.disabled,self.seed=kind,db,disabled,seed;self.start()
    def start(self):
        cmd=[sys.executable,str(ROOT/'validation/0.19/python_host.py')] if self.kind=='python' else ['node',str(ROOT/'validation/0.19/node_host.mjs')]
        cmd += ['--db',str(self.db),'--port','0','--admin-token',ADMIN]
        if self.seed is not None:cmd += ['--assignment-seed',str(self.seed)]
        if self.disabled:cmd += ['--disable',self.disabled]
        self.process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        line=self.process.stdout.readline()
        if not line:
            raise RuntimeError(self.process.stderr.read())
        self.url='http://127.0.0.1:'+str(json.loads(line)['port'])
    def stop(self):
        self.process.terminate();self.process.wait(timeout=5)
        self.process.stdout.close();self.process.stderr.close()
    def restart(self):self.stop();self.start()
    def request(self,path,data=None,token=ADMIN):
        body=None if data is None else json.dumps(data).encode()
        req=urllib.request.Request(self.url+path,data=body,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=5) as response:return json.load(response)
        except urllib.error.HTTPError as error:return json.load(error)
    def clock(self,at):assert self.request('/clock',{'at':at})=={'outcome':'accepted'}
    def setup(self,p,iid='test',participants=PEOPLE,settings=None):
        imported=self.request('/packages',{'package':p});assert imported['outcome'] in ['imported','existing'],imported
        created=self.request('/instances',dict(id=iid,packageId=p['id'],version=p['version'],participants=participants,organizer='organizer',**({'settings':settings} if settings is not None else {})))
        assert created['outcome']=='created',created
        return created['tokens']

def trace(kind,case,directory):
    h=Host(kind,directory/(kind+'-'+case['id']+'.sqlite'),seed=case.get('seed',1729))
    try:
        p=case.get('definition') or package(case['package']);people=case.get('participants',PEOPLE);tokens=h.setup(p,participants=people,settings=case.get('settings'))
        ref=run(dict(package=p,participants=people,organizer='organizer',events=case['events'],settings=case.get('settings',{}),seed=case.get('seed')))
        snapshots=[]
        for i,event in enumerate(case['events']):
            h.clock(event['at'])
            if event['type']=='tick':outcome='accepted'
            else:
                payload={k:event[k] for k in ['eventId','type','step','payload']}
                outcome=h.request('/instances/test/events',payload,tokens[event['actor']])['outcome']
            assert outcome==case['outcomes'][i],(kind,case['id'],i,outcome)
            views={a:h.request('/instances/test/view',token=tokens[a])['view'] for a in people+['organizer']}
            assert views==ref['views'][i],(kind,case['id'],i,views,ref['views'][i])
            if i==len(case['events'])//2:
                h.restart()
                assert {a:h.request('/instances/test/view',token=tokens[a])['view'] for a in tokens}==views
            snapshots.append(views)
        return snapshots
    finally:h.stop()

def probes(kind,directory):
    h=Host(kind,directory/(kind+'-probes.sqlite'))
    try:
        p=package('check-in');tokens=h.setup(p)
        assert h.request('/instances/test/view',token='intruder')=={'outcome':'unauthorized'}
        forged=dict(eventId='forged',type='submit',step='answer',payload={'answer':'oops'},actor='a',at=0)
        assert h.request('/instances/test/events',forged,tokens['b'])=={'outcome':'rejected'}
        submissions=[dict(eventId=f'race-{i}',type='submit',step='answer',payload={'answer':str(i)}) for i in range(2)]
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results=list(pool.map(lambda e:h.request('/instances/test/events',e,tokens['a'])['outcome'],submissions))
        assert sorted(results)==['accepted','rejected'],(kind,results)
        winner=submissions[results.index('accepted')]
        h.restart();assert h.request('/instances/test/events',winner,tokens['a'])=={'outcome':'replayed'}
        view=h.request('/instances/test/view',token=tokens['b'])['view']
        assert view['records'][0]['count']==1 and view['records'][0]['entries']==[]
        assert h.request('/packages',{'package':p})['outcome']=='existing'
        changed=copy.deepcopy(p);changed['content']['title']='Changed'
        assert h.request('/packages',{'package':changed})['outcome']=='package_conflict'
        # Derive a distinct revision: a hard-coded 0.4.1 now equals the input revision.
        major,minor,patch=map(int,p['version'].split('.'));changed['version']=f'{major}.{minor}.{patch+1}'
        assert changed['version']!=p['version']
        assert h.request('/packages',{'package':changed})['outcome']=='imported'
        assert h.request('/packages',{'package':changed})['outcome']=='existing'
        assert h.request('/packages/'+p['id']+'/'+p['version'])['package']==p
        conflicting=copy.deepcopy(changed);conflicting['content']['title']='Conflicting second revision'
        assert h.request('/packages',{'package':conflicting})['outcome']=='package_conflict'
        assert h.request('/instances/test/view',token=tokens['a'])['view']['prompt']==p['runbook']['steps'][0]['prompt']
        story=package('timed-story');h.setup(story,'worker')
        h.clock(180000)
        deadline=time.monotonic()+3
        while h.request('/instances/worker/status')['phase']!='complete':
            assert time.monotonic()<deadline,'worker did not close timed turns'
            time.sleep(.02)
        assert h.request('/instances/worker/status')['clock']==180000
        h.restart();assert h.request('/instances/worker/status')['phase']=='complete'
    finally:h.stop()
    limited=Host(kind,directory/(kind+'-limited.sqlite'),'append@1')
    try:
        p=held_out();assert limited.request('/packages',{'package':p})['outcome']=='imported'
        response=limited.request('/instances',dict(id='unsupported',packageId=p['id'],version=p['version'],participants=PEOPLE,organizer='organizer'))
        assert response=={'outcome':'unsupported','missing':['append@1']},response
        assert limited.request('/instances/unsupported/status')=={'outcome':'not_found'}
        assert 'append@1' not in limited.request('/support')['operations']
    finally:limited.stop()

def pool_and_group_probes(kind,directory):
    h=Host(kind,directory/(kind+'-pool-races.sqlite'))
    try:
        p=package('gratitude-pool');p['runbook']['steps'][0]['close']='organizer'
        tokens=h.setup(p)
        events=[dict(eventId='same-'+actor,type='submit',step='slips',payload={'itemId':'same','text':actor+' value'}) for actor in ['a','b']]
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results=list(pool.map(lambda pair:h.request('/instances/test/events',pair[1],tokens[pair[0]])['outcome'],zip(['a','b'],events)))
        assert sorted(results)==['accepted','rejected'],(kind,results)
        author=['a','b'][results.index('accepted')]
        assert h.request('/instances/test/events',events[results.index('accepted')],tokens[author])['outcome']=='replayed'
        assert h.request('/instances/test/events',dict(eventId='close',type='advance',step='slips',payload={}),tokens['organizer'])['outcome']=='accepted'
        assert h.request('/instances/test/events',dict(eventId='own',type='claim',step='claim:0',payload={}),tokens[author])['outcome']=='rejected'
        eligible=[actor for actor in PEOPLE if actor!=author]
        claims=[dict(eventId='claim-'+actor,type='claim',step='claim:0',payload={}) for actor in eligible]
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results=list(pool.map(lambda pair:h.request('/instances/test/events',pair[1],tokens[pair[0]])['outcome'],zip(eligible,claims)))
        assert sorted(results)==['accepted','rejected'],(kind,results)
        reader=eligible[results.index('accepted')];loser=eligible[results.index('rejected')]
        h.restart()
        assert h.request('/instances/test/events',claims[results.index('accepted')],tokens[reader])['outcome']=='replayed'
        winner_view=h.request('/instances/test/view',token=tokens[reader])['view']
        loser_view=h.request('/instances/test/view',token=tokens[loser])['view']
        assert winner_view['records'][1]['item']=={'itemId':'same','text':author+' value'}
        assert 'item' not in loser_view['records'][1] and loser_view['records'][0]['entries']==[]
        ack=dict(eventId='read',type='advance',step='read:0',payload={})
        assert h.request('/instances/test/events',ack,tokens[loser])['outcome']=='rejected'
        assert h.request('/instances/test/events',ack,tokens[reader])['outcome']=='accepted'
        final=h.request('/instances/test/view',token=tokens[loser])['view']
        assert final['phase']=='complete' and final['records'][0]['entries']==[{'itemId':'same','text':author+' value'}]
        # A dynamic item body also progresses in a deadline worker without any participant read.
        worker_tokens=h.setup(p,'pool-worker')
        assert h.request('/instances/pool-worker/events',dict(eventId='entry',type='submit',step='slips',payload={'itemId':'worker-item','text':'private'}),worker_tokens['a'])['outcome']=='accepted'
        assert h.request('/instances/pool-worker/events',dict(eventId='go',type='advance',step='slips',payload={}),worker_tokens['organizer'])['outcome']=='accepted'
        h.clock(30000);deadline=time.monotonic()+3
        while h.request('/instances/pool-worker/status')['phase']!='complete':
            assert time.monotonic()<deadline,'dynamic worker did not finish';time.sleep(.02)
        h.restart();assert h.request('/instances/pool-worker/status')['phase']=='complete'
        assert h.request('/instances/pool-worker/view',token=worker_tokens['b'])['view']['records'][0]['entries']==[]
        # Invalid deterministic partitions are rejected at setup, before any source collection opens.
        p2=package('pooled-ideas-and-pairs');assert h.request('/packages',{'package':p2})['outcome']=='imported'
        response=h.request('/instances',dict(id='odd',packageId=p2['id'],version=p2['version'],participants=['a','b','c','d','e'],organizer='organizer'))
        assert response=={'outcome':'invalid_setup'} and h.request('/instances/odd/status')=={'outcome':'not_found'}
    finally:h.stop()
    limited=Host(kind,directory/(kind+'-policy-limited.sqlite'),'policy:claim_reader@1')
    try:
        p=package('gratitude-pool');assert limited.request('/packages',{'package':p})['outcome']=='imported'
        result=limited.request('/instances',dict(id='blocked',packageId=p['id'],version=p['version'],participants=PEOPLE,organizer='organizer'))
        assert result=={'outcome':'unsupported','missing':['policy:claim_reader@1']}
        assert limited.request('/instances/blocked/status')=={'outcome':'not_found'}
        assert 'policy:claim_reader@1' not in limited.request('/support')['capabilities']
    finally:limited.stop()

def transfer_pool(directory):
    hosts=[Host(kind,directory/(kind+'-pool-transfer.sqlite')) for kind in ['python','node']]
    try:
        p,people,events=pooled_combination();p['content']['title']='Pooled ideas → pairs: café 🎨'
        sent=hosts[0].request('/packages',{'package':p})
        exported=hosts[0].request('/packages/'+p['id']+'/'+p['version'])
        imported=hosts[1].request('/packages',{'package':exported['package']})
        assert sent['digest']==exported['digest']==imported['digest']
        reference=run(dict(package=p,participants=people,organizer='organizer',events=events))
        finals=[]
        for h in hosts:
            tokens=h.setup(p,participants=people)
            for i,event in enumerate(events):
                h.clock(event['at']);payload={k:event[k] for k in ['eventId','type','step','payload']}
                assert h.request('/instances/test/events',payload,tokens[event['actor']])['outcome']=='accepted'
                if i==7:h.restart()
            h.restart();views={a:h.request('/instances/test/view',token=tokens[a])['view'] for a in tokens}
            assert views==reference['views'][-1];finals.append(views)
        assert finals[0]==finals[1]
    finally:
        for h in hosts:h.stop()

def transfer(directory):
    hosts=[Host(kind,directory/(kind+'-transfer.sqlite')) for kind in ['python','node']]
    try:
        p=held_out();p['content']['title']='A new combination: café 🎨'
        imported=hosts[0].request('/packages',{'package':p})
        export=hosts[0].request('/packages/'+p['id']+'/'+p['version'])
        assert export['package']==p
        received=hosts[1].request('/packages',{'package':export['package']})
        assert received['digest']==imported['digest']==export['digest']
        views=[]
        for h in hosts:
            tokens=h.setup(p)
            for a in PEOPLE:
                assert h.request('/instances/test/events',dict(eventId='answer-'+a,type='submit',step='answer',payload={'answer':a}),tokens[a])['outcome']=='accepted'
            for i,a in enumerate(PEOPLE):
                assert h.request('/instances/test/events',dict(eventId='story-'+a,type='submit',step=f'write:{i}',payload={'text':a}),tokens[a])['outcome']=='accepted'
            h.restart();views.append(h.request('/instances/test/view',token=tokens['a'])['view'])
        assert views[0]==views[1] and views[0]['phase']=='complete'
    finally:
        for h in hosts:h.stop()

def scheduled_probes(kind,directory):
    h=Host(kind,directory/(kind+'-scheduled-probes.sqlite'))
    try:
        p=package('scheduled-check-in');assert h.request('/packages',{'package':p})['outcome']=='imported'
        base=dict(id='bad',packageId=p['id'],version=p['version'],participants=PEOPLE,organizer='organizer')
        valid={'opens_at':10,'closes_at':20}
        for bad in [None,[],{},{'opens_at':10},dict(valid,extra=1),dict(valid,opens_at=True),dict(valid,closes_at=10),dict(valid,question='')]:
            assert h.request('/instances',dict(base,settings=bad))=={'outcome':'invalid_setup'}
            assert h.request('/instances/bad/status')=={'outcome':'not_found'}
        tokens=h.setup(p,settings=dict(valid,question='Saved question'))
        h.restart();assert h.request('/instances/test/view',token=tokens['a'])['view']['prompt']=='Saved question'
        h.clock(10)
        requests=[dict(eventId='scheduled-race-'+str(i),type='submit',step='answer',payload={'value':str(i)}) for i in range(2)]
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            outcomes=list(pool.map(lambda e:h.request('/instances/test/events',e,tokens['a'])['outcome'],requests))
        assert sorted(outcomes)==['accepted','rejected']
        winner=requests[outcomes.index('accepted')]
        for a in ['b','c']:
            assert h.request('/instances/test/events',dict(eventId=a,type='submit',step='answer',payload={'value':a}),tokens[a])['outcome']=='accepted'
        view=h.request('/instances/test/view',token=tokens['organizer'])['view']
        assert view['step']=='answer' and view['records'][1]['entries']==[]
        assert h.request('/instances/test/events',dict(eventId='skip',type='advance',step='answer',payload={}),tokens['organizer'])['outcome']=='rejected'
        h.clock(20);h.restart()
        assert h.request('/instances/test/events',winner,tokens['a'])['outcome']=='replayed'
        assert h.request('/instances/test/view',token=tokens['a'])['view']['phase']=='complete'
        h.clock(21)
        assert h.request('/instances',dict(base,settings=valid))=={'outcome':'invalid_setup'}
    finally:h.stop()
    limited=Host(kind,directory/(kind+'-settings-disabled.sqlite'),'instance_settings@1')
    try:
        p=package('scheduled-check-in');limited.request('/packages',{'package':p})
        assert limited.request('/instances',dict(id='unsupported',packageId=p['id'],version=p['version'],participants=PEOPLE,organizer='organizer',settings={'opens_at':10,'closes_at':20}))=={'outcome':'unsupported','missing':['instance_settings@1']}
        assert limited.request('/instances/unsupported/status')=={'outcome':'not_found'}
        assert 'instance_settings@1' not in limited.request('/support')['capabilities']
    finally:limited.stop()

def transfer_scheduled(directory):
    hosts=[Host(kind,directory/(kind+'-scheduled-transfer.sqlite')) for kind in ['python','node']]
    try:
        p=package('scheduled-check-in-pairs');p['content']['title']='Scheduled café → pair reflection 🎨'
        sent=hosts[0].request('/packages',{'package':p});exported=hosts[0].request('/packages/'+p['id']+'/'+p['version']);received=hosts[1].request('/packages',{'package':exported['package']})
        assert sent['digest']==exported['digest']==received['digest']
        people=['a','b','c','d'];values={'opens_at':10,'closes_at':20,'question':'Shared imported question'}
        snapshots=[]
        for h in hosts:
            tokens=h.setup(p,participants=people,settings=values);h.restart();h.clock(10)
            assert h.request('/instances/test/events',dict(eventId='answer',type='submit',step='answer',payload={'value':'A thought'}),tokens['a'])['outcome']=='accepted'
            h.clock(20);h.restart()
            assert h.request('/instances/test/events',dict(eventId='note',type='submit',step='reflect',payload={'text':'Pair-only response'}),tokens['a'])['outcome']=='accepted'
            h.clock(300020);h.restart()
            views={a:h.request('/instances/test/view',token=tokens[a])['view'] for a in tokens}
            assert views['a']['phase']=='complete' and views['b']['records'][-1]['count']==1
            assert views['c']['records'][-1]['entries']==views['organizer']['records'][-1]['entries']==[]
            snapshots.append(views)
        assert snapshots[0]==snapshots[1]
    finally:
        for h in hosts:h.stop()

def scoring_probes(kind,directory):
    h=Host(kind,directory/(kind+'-scoring.sqlite'))
    try:
        p=package('crowd-scoring');people=list('abcdef');tokens=h.setup(p,participants=people)
        for a in people:assert h.request('/instances/test/events',dict(eventId='idea-'+a,type='submit',step='ideas',payload={'itemId':'i-'+a,'text':'Idea '+a}),tokens[a])['outcome']=='accepted'
        h.clock(300000)
        view=h.request('/instances/test/view',token=tokens['b'])['view'];assert view['records'][1]['assignments']==[{'itemId':'i-a','text':'Idea a'}]
        assert h.request('/instances/test/events',dict(eventId='self',type='submit',step='rate_1',payload={'itemId':'i-a','round':'round_1','score':5}),tokens['a'])['outcome']=='rejected'
        scores=[dict(eventId='score-'+str(i),type='submit',step='rate_1',payload={'itemId':'i-a','round':'round_1','score':i+1}) for i in range(2)]
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            outcomes=list(pool.map(lambda e:h.request('/instances/test/events',e,tokens['b'])['outcome'],scores))
        assert sorted(outcomes)==['accepted','rejected']
        winner=scores[outcomes.index('accepted')]
        h.restart();assert h.request('/instances/test/events',winner,tokens['b'])['outcome']=='replayed'
        for actor in ['a','c','organizer']:
            assert h.request('/instances/test/view',token=tokens[actor])['view']['records'][2]['entries']==[]
        h.clock(360000)
        assert h.request('/instances/test/events',dict(eventId='old-step',type='submit',step='rate_1',payload=winner['payload']),tokens['b'])['outcome']=='rejected'
        assert h.request('/instances/test/events',dict(eventId='wrong-round',type='submit',step='rate_2',payload={'itemId':'i-a','round':'round_1','score':5}),tokens['c'])['outcome']=='rejected'
        h.clock(600000)
        deadline=time.monotonic()+3
        while h.request('/instances/test/status')['phase']!='complete':
            assert time.monotonic()<deadline,'rating worker failed to cross all deadlines'
            time.sleep(.02)
        h.restart();final=h.request('/instances/test/view',token=tokens['organizer'])['view']
        assert final['records'][11]['ranking'][0]['score']=={'numerator':winner['payload']['score']*5,'denominator':1}
        assert len(final['records'][11]['unrated'])==5
        assert h.request('/instances/test/events',winner,tokens['b'])['outcome']=='replayed'
        # Offset must fit the actual roster, not merely the package maximum.
        p=package('proposal-assessment');p['runbook']['steps'][3]['offset']=4
        assert h.request('/packages',{'package':p})['outcome']=='imported'
        assert h.request('/instances',dict(id='bad-route',packageId=p['id'],version=p['version'],participants=list('abcd'),organizer='organizer'))=={'outcome':'invalid_setup'}
        assert h.request('/instances/bad-route/status')=={'outcome':'not_found'}
    finally:h.stop()
    for missing in ['integer_values@1','rate@1','policy:mean_scaled_scores@1']:
        limited=Host(kind,directory/(kind+'-'+missing.replace(':','-').replace('@','-')+'.sqlite'),missing)
        try:
            p=package('crowd-scoring');limited.request('/packages',{'package':p})
            assert limited.request('/instances',dict(id='unsupported',packageId=p['id'],version=p['version'],participants=list('abcdef'),organizer='organizer'))=={'outcome':'unsupported','missing':[missing]}
            assert limited.request('/instances/unsupported/status')=={'outcome':'not_found'}
            support=limited.request('/support');assert missing not in support['operations']+support['capabilities']
        finally:limited.stop()

def transfer_assessment(directory):
    hosts=[Host(kind,directory/(kind+'-assessment-transfer.sqlite')) for kind in ['python','node']]
    try:
        p=package('proposal-assessment');p['content']['title']='A new assessment: café → private reflection 🎨'
        imported=hosts[0].request('/packages',{'package':p});exported=hosts[0].request('/packages/'+p['id']+'/'+p['version']);received=hosts[1].request('/packages',{'package':exported['package']})
        assert imported['digest']==exported['digest']==received['digest']
        people=['🙂','__proto__','9007199254740993','é'];events=[]
        def event(i,t,a,at,step,payload):return dict(eventId=i,type=t,actor=a,at=at,step=step,payload=payload)
        events += [event('idea-'+str(i),'submit',a,0,'ideas',{'itemId':'i'+str(i),'text':'Idea '+str(i)}) for i,a in enumerate(people)]
        events.append(event('open','tick','system',300000,None,{}))
        for round in [1,2]:
            events += [event('score-'+str(round)+'-'+str(i),'submit',people[(i+round)%4],300000+(round-1)*60000,'rate_'+str(round),{'itemId':'i'+str(i),'round':'round_'+str(round),'score':i}) for i in range(4)]
            events.append(event('end-'+str(round),'tick','system',300000+round*60000,None,{}))
        events += [event('note','submit',people[0],420000,'reflection',{'text':'Private paired note'}),event('done','tick','system',480000,None,{})]
        reference=run(dict(package=p,participants=people,organizer='organizer',events=events));assert reference['outcomes']==['accepted']*len(events)
        snapshots=[]
        for h in hosts:
            tokens=h.setup(p,participants=people)
            for i,e in enumerate(events):
                h.clock(e['at'])
                if e['type']!='tick':assert h.request('/instances/test/events',{k:e[k] for k in ['eventId','type','step','payload']},tokens[e['actor']])['outcome']=='accepted'
                if i==6:h.restart()
            h.restart();views={a:h.request('/instances/test/view',token=tokens[a])['view'] for a in tokens}
            assert views==reference['views'][-1];snapshots.append(views)
            assert views[people[1]]['records'][7]['count']==1 and views[people[2]]['records'][7]['entries']==[]
        assert snapshots[0]==snapshots[1]
    finally:
        for h in hosts:h.stop()

if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='harmonomicon-018-') as directory:
        directory=Path(directory);results={}
        for kind in ['python','node']:
            results[kind]=[trace(kind,c,directory) for c in CASES];probes(kind,directory);pool_and_group_probes(kind,directory);scheduled_probes(kind,directory);scoring_probes(kind,directory)
            from migration_trial import compare_hosts
            compare_hosts(kind,directory,Host)
            import recurrence_trial
            recurrence_trial.compare_hosts(kind,directory,Host);recurrence_trial.probes(kind,directory,Host)
            import distribution_trial
            distribution_trial.probes(kind,directory,Host)
            import image_trial
            image_trial.probes(kind,directory,Host);image_trial.compare_legacy(kind,directory,Host)
            print(f'{kind}: {len(CASES)} traces, pool/reader races, group privacy, policy negotiation, durable replay, workers and restart passed',flush=True)
        assert results['python']==results['node'];transfer(directory);transfer_pool(directory);transfer_scheduled(directory);transfer_assessment(directory);recurrence_trial.transfer(directory,Host);distribution_trial.transfer(directory,Host);image_trial.transfer(directory,Host)
        print('Independent app hosts agree; a newly composed package transfers and runs without changing either interpreter.')
