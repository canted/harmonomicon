"""Behavior comparisons through actual 0.12 and 0.15 app hosts."""
import importlib.util
import json
import sqlite3
import time
from pathlib import Path
from migration_check import SCENARIOS,LEGACY,TRANSLATED,settings,semantic_view
ROOT=Path(__file__).resolve().parents[2]

def compare_hosts(kind,directory,Host):
    spec=importlib.util.spec_from_file_location('legacy_host_trial',ROOT/'validation/0.12/run.py')
    legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    for scenario in SCENARIOS:
        label=scenario['id'];instance=scenario['instance'];people=instance['participants'];organizer=instance['organizer']
        old=legacy.Host(kind,directory/(kind+'-legacy-'+label+'.sqlite'))
        new=Host(kind,directory/(kind+'-translated-'+label+'.sqlite'))
        try:
            old.set_clock(instance['createdAt']);new.clock(instance['createdAt'])
            old_tokens={a:'legacy-'+a for a in people+[organizer]}
            body=dict(instanceId='comparison',packageId=LEGACY['id'],packageVersion=LEGACY['version'],tokens=old_tokens,**{k:v for k,v in instance.items() if k!='createdAt'})
            status,created=old.request('POST','/admin/instances',body,admin=True)
            assert status==201 and created['status']=='created',created
            imported=new.request('/packages',{'package':TRANSLATED});assert imported['outcome']=='imported'
            created=new.request('/instances',dict(id='comparison',packageId=TRANSLATED['id'],version=TRANSLATED['version'],participants=people,organizer=organizer,settings=settings(instance)))
            assert created['outcome']=='created',created
            new_tokens=created['tokens']
            def compare():
                for actor in people+[organizer]:
                    status,before=old.request('GET','/instances/comparison/view',token=old_tokens[actor])
                    after=new.request('/instances/comparison/view',token=new_tokens[actor])['view']
                    assert status==200 and before==semantic_view(after,actor,people),(kind,label,actor,before,after)
            compare()
            for i,action in enumerate(scenario['actions']):
                at=action['event']['at'] if 'event' in action else action['view']['at']
                old.set_clock(at);new.clock(at)
                if 'event' in action:
                    event=action['event']
                    if event['type']!='tick':
                        payload={k:event[k] for k in ['eventId','type','payload']}
                        status,before=old.request('POST','/instances/comparison/events',payload,token=old_tokens[event['actor']])
                        after=new.request('/instances/comparison/events',dict(payload,step='answer'),new_tokens[event['actor']])
                        assert status==200 and before['outcome']==after['outcome']==action['outcome'],(kind,label,i,before,after)
                compare()
                if i==len(scenario['actions'])//2:
                    old.restart();new.restart();compare()
            with sqlite3.connect(new.db) as db:
                saved=json.loads(db.execute('SELECT state FROM instances WHERE id=?',('comparison',)).fetchone()[0])
            assert saved['settings']['question']==instance.get('prompt',LEGACY['content']['prompt'])
        finally:old.close();new.stop()
    # Progress must also persist when no participant asks for a view.
    old=legacy.Host(kind,directory/(kind+'-legacy-worker.sqlite'));new=Host(kind,directory/(kind+'-scheduled-worker.sqlite'))
    try:
        tokens={a:'worker-'+a for a in ['a','b','organizer']}
        status,created=old.request('POST','/admin/instances',dict(instanceId='worker',packageId=LEGACY['id'],packageVersion=LEGACY['version'],participants=['a','b'],organizer='organizer',opensAt=10,closesAt=20,tokens=tokens),admin=True)
        assert status==201
        new.setup(TRANSLATED,'worker',participants=['a','b'],settings={'opens_at':10,'closes_at':20})
        old.set_clock(100);new.clock(100)
        deadline=time.monotonic()+3
        while True:
            with sqlite3.connect(old.db) as db:
                prior=json.loads(db.execute('SELECT state_json FROM instances WHERE id=?',('worker',)).fetchone()[0])
            current=new.request('/instances/worker/status')
            if prior['phase']=='closed' and current['phase']=='complete':break
            assert time.monotonic()<deadline,'workers did not finish the scheduled window'
            time.sleep(.02)
        old.restart();new.restart()
        assert new.request('/instances/worker/status')['phase']=='complete'
    finally:old.close();new.stop()
    print(f'{kind}: six check-in migrations agree with actual 0.12 host; worker-only close and restart pass',flush=True)
