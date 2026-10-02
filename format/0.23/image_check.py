"""Typed image-reference witnesses; registry is trusted harness input, not event data."""
import copy,json
from pathlib import Path
from runtime import Engine,run
HERE=Path(__file__).resolve().parent
PEOPLE=['a','b','c']
def package(n):return json.loads((HERE/'examples'/f'{n}.json').read_text())
def event(i,actor,at,step,value):return dict(eventId=i,type='submit',actor=actor,at=at,step=step,payload=value)
def media(actor,ref,kind='image',ready=True):return dict(actor=actor,ref=ref,kind=kind,ready=ready)
def witnesses():
 p=package('image-check-in');registry=[media('a','opaque:jpeg'),media('b','opaque:png'),media('a','pending',ready=False),media('a','audio',kind='audio')]
 events=[event('early','a',9,'answer',{'value':{'ref':'opaque:jpeg'}}),event('pending','a',10,'answer',{'value':{'ref':'pending'}}),event('audio','a',10,'answer',{'value':{'ref':'audio'}}),event('foreign','b',10,'answer',{'value':{'ref':'opaque:jpeg'}}),event('extra','a',10,'answer',{'value':{'ref':'opaque:jpeg','ready':True}}),event('a','a',10,'answer',{'value':{'ref':'opaque:jpeg'}}),event('dup','a',11,'answer',{'value':{'ref':'opaque:jpeg'}}),event('boundary','b',20,'answer',{'value':{'ref':'opaque:png'}}),event('a','a',20,'answer',{'value':{'ref':'opaque:jpeg'}})]
 yield dict(id='scheduled-image-attestation-private-reveal',package=p,participants=PEOPLE,organizer='organizer',settings={'opens_at':10,'closes_at':20},trustedMedia=registry,events=events),['rejected']*5+['accepted','rejected','rejected','replayed']
 p=package('image-daily-private');events=[event('a','a',10,'entry:0',{'value':{'ref':'opaque:jpeg'}}),event('stale','b',86400010,'entry:0',{'value':{'ref':'opaque:png'}}),event('b','b',86400010,'entry:1',{'value':{'ref':'opaque:png'}}),event('a','a',244800010,'entry:0',{'value':{'ref':'opaque:jpeg'}})]
 yield dict(id='recurring-image-occurrence-history',package=p,participants=PEOPLE,organizer='organizer',settings={'starts_at':10},trustedMedia=registry,events=events),['accepted','rejected','accepted','replayed']
 p=package('check-in');p['requires'].append('image_contributions@1');p['runbook']['steps'][0]['fields']={'caption':{'type':'text','visibility':'group'},'image':{'type':'image_ref','visibility':'private'}}
 events=[event('bad','a',0,'answer',{'caption':'must not partially save','image':{'ref':'missing'}}),event('ok','a',0,'answer',{'caption':'caption','image':{'ref':'opaque:jpeg'}}),event('end','b',3600000,'answer',{'caption':'late','image':{'ref':'opaque:png'}})]
 yield dict(id='ordinary-mixed-form-atomic-reveal',package=p,participants=PEOPLE,organizer='organizer',trustedMedia=registry,events=events),['rejected','accepted','rejected']
 p=copy.deepcopy(p);p['runbook']['steps'].pop();events=[event('ok','a',0,'answer',{'caption':'caption','image':{'ref':'opaque:jpeg'}}),event('end','b',3600000,'answer',{'caption':'late','image':{'ref':'opaque:png'}})]
 yield dict(id='ordinary-private-image-without-reveal',package=p,participants=PEOPLE,organizer='organizer',trustedMedia=registry,events=events),['accepted','rejected']
def check(node,schema=None):
 for request,expected in witnesses():
  result=run(request);assert result==node(request);assert result['outcomes']==expected,(request['id'],result['outcomes'])
  for cut in range(len(request['events'])+1):
   state=run(dict(request,events=request['events'][:cut]))['state'];resumed=dict(request,state=state,events=request['events'][cut:]);assert run(resumed)==node(resumed);assert run(resumed)['state']==result['state']
  if request['id'].startswith('scheduled'):
   assert result['views'][5]['b']['records'][1]['entries']==[]
   assert result['views'][-1]['organizer']['records'][1]['entries']==[{'actor':'a','value':{'value':{'ref':'opaque:jpeg'}}}]
  if request['id'].startswith('ordinary'):
   first=0 if 'without' in request['id'] else 1
   assert result['views'][first]['b']['records'][0]['entries']==[{'actor':'a','value':{'caption':'caption'}}]
   if 'without' in request['id']:assert 'image' not in result['views'][-1]['b']['records'][0]['entries'][0]['value']
  if schema:
   import jsonschema;jsonschema.validate(request['package'],schema)
 p=package('image-check-in');bad=[]
 for change in [lambda p:p['requires'].remove('image_contributions@1'),lambda p:p['runbook']['steps'][1]['fields']['value'].update(type='audio_ref'),lambda p:p['runbook']['steps'][1]['fields']['value'].update(encoding='png'),lambda p:p['runbook']['steps'][1]['fields']['value'].update(visibility='owner'),lambda p:p['runbook']['steps'][1]['fields']['value'].update(ready=True)]:
  q=copy.deepcopy(p);change(q);bad.append(q)
 for q in bad:assert run(dict(action='validate',package=q))==node(dict(action='validate',package=q))=={'outcome':'invalid_package'}
 if schema:
  import jsonschema
  for q in bad[1:]:assert list(jsonschema.Draft202012Validator(schema).iter_errors(q))
 # Engine requires a trusted authority; self-attested event fields cannot supply it.
 e=Engine(p,PEOPLE,'organizer',settings={'opens_at':0,'closes_at':20});assert e.event(event('no-authority','a',0,'answer',{'value':{'ref':'opaque:jpeg'}}))=='rejected'
 registry=lambda actor,ref:actor=='a' and ref=='opaque:jpeg'
 e=Engine(p,PEOPLE,'organizer',settings={'opens_at':0,'closes_at':20},authorize_image=registry);accepted=event('stable','a',0,'answer',{'value':{'ref':'opaque:jpeg'}});assert e.event(accepted)=='accepted'
 e=Engine(p,PEOPLE,'organizer',state=e.state,authorize_image=lambda a,r:False);assert e.event(dict(accepted,at=20))=='replayed';assert e.state['records'][1]['entries'][0]['value']=={'value':{'ref':'opaque:jpeg'}}
 for ref in ['', 'x'*257, {'ref':'nested'}, 3]:
  req=dict(package=p,participants=PEOPLE,organizer='organizer',settings={'opens_at':0,'closes_at':20},events=[event('shape','a',0,'answer',{'value':{'ref':ref}})]);assert run(req)==node(req);assert run(req)['outcomes']==['rejected']
 # Maximum scalar length and supplementary characters agree in both languages.
 ref='🙂'*256;req=dict(package=p,participants=PEOPLE,organizer='organizer',settings={'opens_at':0,'closes_at':20},trustedMedia=[media('a',ref)],events=[event('unicode','a',0,'answer',{'value':{'ref':ref}})]);assert run(req)==node(req) and run(req)['outcomes']==['accepted']
 for ref in ['🙂'*257,'bad\ud800']:
  req['events']=[event('unicode-invalid','a',0,'answer',{'value':{'ref':ref}})];assert run(req)==node(req) and run(req)['outcomes']==['rejected']
 print('4 image traces, 5 invalid definitions, image schema negatives, atomic mixed forms, immutable replay and host-attested encoding independence pass')
 return len(bad)
if __name__=='__main__':
 from check import node
 check(node,json.loads((HERE/'package.schema.json').read_text()))
