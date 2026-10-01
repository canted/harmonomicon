"""Compare the migrated check-in with the legacy reference delegated by 0.12."""
import copy
import json
import runpy
from pathlib import Path
from runtime import Engine
HERE=Path(__file__).resolve().parent
SCENARIOS=json.loads((HERE/'conformance/check-in-migration.json').read_text())
LEGACY=json.loads((HERE.parent/'0.12/examples/group-check-in.json').read_text())
TRANSLATED=json.loads((HERE/'examples/scheduled-check-in.json').read_text())

def settings(instance):
    result={'opens_at':instance['opensAt'],'closes_at':instance['closesAt']}
    if 'prompt' in instance:result['question']=instance['prompt']
    return result

def adapted_event(event):
    return dict(event,step=None if event['type']=='tick' else 'answer')

def semantic_view(view,actor,participants):
    # View shape changed; compare the same user-visible phase, count, own value, and ordered reveal.
    phase='closed' if view['phase']=='complete' else 'waiting' if view['step']=='opening' else 'open'
    record=next((r for r in view['records'] if r['step']=='answer'),{'count':0,'entries':[]})
    entries=[{'actor':e['actor'],'value':e['value']['value']} for e in record['entries']]
    result={'phase':phase,'submissionCount':record['count']}
    own=next((e for e in entries if e['actor']==actor),None)
    if actor in participants and own is not None:result['own']=own
    if phase=='closed':result['entries']=entries
    return result

def check_reference():
    # 0.12/check.py delegates timed_collection through earlier candidates to this unchanged model.
    old=runpy.run_path(str(HERE.parent/'0.1/check.py'))
    source=copy.deepcopy(LEGACY);source['format']='harmonomicon.activity-package/0.1'
    assert TRANSLATED['id']==LEGACY['id'] and TRANSLATED['version']!=LEGACY['version']
    assert TRANSLATED['participants']==LEGACY['participants']
    for scenario in SCENARIOS:
        instance=scenario['instance'];people=instance['participants'];organizer=instance['organizer']
        previous=old['ReferenceModel'](source,instance)
        current=Engine(TRANSLATED,people,organizer,instance['createdAt'],settings=settings(instance))
        assert current.settings['question']==previous.prompt
        actors=people+[organizer]
        def compare():
            for actor in actors:
                assert semantic_view(current.view(actor),actor,people)==previous.view(actor),(scenario['id'],actor)
        compare()
        for i,action in enumerate(scenario['actions']):
            if 'event' in action:
                event=action['event'];before=previous.event(event);after=current.event(adapted_event(event))
                assert before==after==action['outcome'],(scenario['id'],i,before,after)
            else:
                read=action['view'];before=previous.view(read['actor'],read['at']);after=semantic_view(current.view(read['actor'],read['at']),read['actor'],people)
                assert before==after
                if 'expect' in action:assert after==action['expect']
            compare()
            # A durable checkpoint at each action must preserve settings and all access decisions.
            current=Engine(TRANSLATED,people,organizer,instance['createdAt'],state=current.state)
            compare()
    print(f'{len(SCENARIOS)} legacy check-in comparison scenarios pass, including both original fixtures')

if __name__=='__main__':check_reference()
