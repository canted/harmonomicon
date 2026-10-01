"""Independent negative/boundary evidence and legacy recurrence comparisons."""
import copy
import json
import runpy
from pathlib import Path
from runtime import Engine, run, MAX
HERE=Path(__file__).resolve().parent
NAMES=['daily-private-practice','daily-reveal','daily-shared-prompt']

def definition(name):return json.loads((HERE/'examples'/f'{name}.json').read_text())

def fixtures():
    result=[]
    for file,name in [('repeated-private','daily-private-practice'),('repeated-after-close','daily-reveal'),('repeated-public','daily-shared-prompt')]:
        source=json.loads((HERE.parent/'0.2/conformance'/f'{file}.json').read_text())
        result.append(dict(id=file,package=name,instance=source['instance'],actions=[dict(event=e['event'],outcome=e['outcome'],views=e.get('views',[])) for e in source['events']]))
    # All three full legacy packages, their actual day-sized timing and selected setup choices.
    for name in NAMES:
        p=json.loads((HERE.parent/'0.12/examples'/f'{name}.json').read_text());b=p['behavior'];first=10;second=first+b['intervalMs'];end=first+(b['occurrences']-1)*b['intervalMs']+b['windowMs']
        def e(i,t,a,at,payload):return dict(eventId=i,type=t,actor=a,at=at,payload=payload)
        actions=[dict(event=e('early','submit','a',9,dict(occurrence=1,value='early')),outcome='rejected'),dict(event=e('a','submit','a',first,dict(occurrence=1,value='café 🎨')),outcome='accepted'),dict(event=e('b','submit','b',first+1,dict(occurrence=1,value='B')),outcome='accepted'),dict(view=dict(actor='organizer',at=first+2)),dict(event=e('late','submit','c',first+b['windowMs'],dict(occurrence=1,value='late')),outcome='rejected'),dict(view=dict(actor='a',at=second-1)),dict(event=e('stale','submit','c',second,dict(occurrence=1,value='old')),outcome='rejected'),dict(event=e('c','submit','c',second,dict(occurrence=2,value='C')),outcome='accepted'),dict(event=e('a','submit','a',second+1,dict(occurrence=1,value='café 🎨')),outcome='replayed'),dict(event=e('a','submit','a',second+1,dict(occurrence=1,value='changed')),outcome='rejected'),dict(view=dict(actor='organizer',at=end)),dict(event=e('c','submit','c',end,dict(occurrence=2,value='C')),outcome='replayed')]
        result.append(dict(id=name+'-gaps-and-history',package=name,instance=dict(createdAt=0,startsAt=first,participants=list('abc'),organizer='organizer'),actions=actions))
        # Exact maximum closing time: safe in both numeric domains, with no saturation.
        result.append(dict(id=name+'-maximum-clock',package=name,instance=dict(createdAt=0,startsAt=MAX-(b['occurrences']-1)*b['intervalMs']-b['windowMs'],participants=list('ab'),organizer='organizer'),actions=[dict(view=dict(actor='organizer',at=MAX))]))
    return result

def adapted_event(event):
    payload=event['payload'];step=None if event['type']=='tick' else '!invalid';value=payload
    if event['type']=='submit' and type(payload) is dict and set(payload)=={'occurrence','value'} and type(payload['occurrence']) is int:
        step=f"entry:{payload['occurrence']-1}";value={'value':payload['value']}
    return dict(event,step=step,payload=value)

def semantic_view(view,actor,participants):
    active=view.get('window');phase='complete' if view['phase']=='complete' else 'open' if view['step'].startswith('entry:') else 'waiting' if active['index']==0 else 'between'
    result={'phase':phase,'currentOccurrence':active['index']+1 if phase=='open' else None,'occurrences':[]}
    for record in view['records']:
        if record['op']!='collect_window@1':continue
        entries=[{'actor':e['actor'],'value':e['value']['value']} for e in record['entries']]
        item={'number':record['window']['index']+1,'phase':'closed' if record['closed'] else 'open','submissionCount':record['count'],'statuses':record['statuses']}
        own=next((e for e in entries if e['actor']==actor),None)
        if actor in participants and own is not None:item['own']=own
        # Match presence of legacy entries, including an empty list for public visibility.
        if record['revealed'] or view['_visibility']=='group_immediate':item['entries']=entries
        result['occurrences'].append(item)
    return result

def project(view,actor,people,name):
    visibility={'daily-private-practice':'private','daily-reveal':'group_after_close','daily-shared-prompt':'group_immediate'}[name]
    return semantic_view(dict(view,_visibility=visibility),actor,people)

def check_reference():
    old=runpy.run_path(str(HERE.parent/'0.2/check.py'))
    scenarios=json.loads((HERE/'conformance/recurrence-migration.json').read_text())
    assert scenarios==fixtures(), 'migration fixture drift'
    for scenario in scenarios:
        name=scenario['package'];instance=scenario['instance'];people=instance['participants'];organizer=instance['organizer'];source=json.loads((HERE.parent/'0.12/examples'/f'{name}.json').read_text());source['format']='harmonomicon.activity-package/0.2'
        p=definition(name);assert p['id']==source['id'] and p['version']!=source['version'] and p['participants']==source['participants']
        before=old['RepeatedCollection'](source,instance);after=Engine(p,people,organizer,instance['createdAt'],settings={'starts_at':instance['startsAt']})
        def compare():
            for actor in people+[organizer]:
                a=project(after.view(actor),actor,people,name);b=before.view(actor)
                assert a==b,(scenario['id'],actor,a,b)
        compare()
        for action in scenario['actions']:
            if 'event' in action:
                event=action['event'];a=before.event(event);b=after.event(adapted_event(event));assert a==b==action['outcome'],(scenario['id'],a,b)
                for view in action.get('views',[]):assert before.view(view['actor'],view.get('at'))==view['expect']
            else:
                read=action['view'];assert before.view(read['actor'],read['at'])==project(after.view(read['actor'],read['at']),read['actor'],people,name)
            compare();after=Engine(p,people,organizer,instance['createdAt'],state=after.state);compare()
    print(f'{len(scenarios)} recurrence comparisons pass: three original fixtures, full legacy timing/privacy and maximum clock; restart after every action')

def boundaries(node):
    p=definition('daily-reveal');variants=[]
    def add(change):
        d=copy.deepcopy(p);change(d);variants.append(d)
    for field,value in [('intervalMs',0),('intervalMs',True),('windowMs',0),('windowMs',86400001),('occurrences',0),('occurrences',367),('occurrences',True),('occurrences',1.5),('startsAt',{'setting':'missing'}),('startsAt',{'setting':'starts_at','extra':1}),('steps',[]),('steps',[None])]:add(lambda d,f=field,v=value:d['runbook']['steps'][0].update({f:v}))
    add(lambda d:d['requires'].remove('for_windows@1'))
    add(lambda d:d['requires'].remove('collect_window@1'))
    add(lambda d:d['requires'].remove('completion_status@1'))
    add(lambda d:d['runbook']['steps'][0]['steps'][0].update(completion='secret'))
    add(lambda d:d['runbook']['steps'][0]['steps'][0].update(actors='turn'))
    add(lambda d:d['runbook']['steps'][0]['steps'][0].update(until=10))
    add(lambda d:d['runbook']['steps'].append(copy.deepcopy(d['runbook']['steps'][0]['steps'][0])))
    add(lambda d:d['runbook']['steps'][0]['steps'].append(copy.deepcopy(d['runbook']['steps'][0])))
    add(lambda d:d['runbook']['steps'][0]['steps'].append(dict(id='illegal',op='pause@1',prompt='Not a window body',afterMs=1)))
    add(lambda d:d['runbook']['steps'][0]['steps'].reverse())
    add(lambda d:d['runbook']['steps'].append(dict(id='bad_reference',op='reveal@1',sources=['entry'])))
    for d in variants:assert run({'action':'validate','package':d})==node({'action':'validate','package':d})=={'outcome':'invalid_package'}
    request=dict(package=p,participants=list('ab'),organizer='organizer',events=[])
    for settings in [{},{'starts_at':-1},{'starts_at':True},{'starts_at':MAX},{'starts_at':0,'unknown':1}]:
        args=dict(request,settings=settings);assert run(args)==node(args)=={'outcome':'invalid_setup'}
    assert run(dict(request,startedAt=11,settings={'starts_at':10}))==node(dict(request,startedAt=11,settings={'starts_at':10}))=={'outcome':'invalid_setup'}
    # 366 contiguous windows must settle on one jump, with exact integer-valued JSON floats allowed.
    d=copy.deepcopy(p);d['runbook']['steps'][0].update(intervalMs=1.0,windowMs=1.0,occurrences=366.0)
    args=dict(request,package=d,settings={'starts_at':0},events=[dict(eventId='jump',type='tick',actor='system',at=366,step=None,payload={})]);result=run(args);assert result==node(args)
    view=result['views'][-1]['organizer'];assert view['phase']=='complete' and len([r for r in view['records'] if r['op']=='collect_window@1'])==366
    assert all(r['statuses']==[{'actor':'a','status':'missed'},{'actor':'b','status':'missed'}] for r in view['records'] if r['op']=='collect_window@1')
    # A continuation reached after its fixed schedule misses elapsed windows without backdating actions.
    d=copy.deepcopy(p);d['runbook']['steps'][0].update(intervalMs=20,windowMs=10,occurrences=2);d['runbook']['steps'].insert(0,dict(id='pause',op='pause@1',prompt='Prior work',afterMs=100));d['requires'].append('pause@1')
    args=dict(request,package=d,settings={'starts_at':10},events=[dict(eventId='jump',type='tick',actor='system',at=100,step=None,payload={})]);result=run(args);assert result==node(args) and result['views'][-1]['a']['phase']=='complete'
    print(f'{len(variants)} recurrence invalid definitions; setup, 366-window jumps, integer floats and late continuation pass')
    return len(variants)

if __name__=='__main__':check_reference()
