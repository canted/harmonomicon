"""Typed source exchange and trusted host-input witnesses, not app role semantics."""
import copy,json
from pathlib import Path
from runtime import Engine,run,MAX
HERE=Path(__file__).resolve().parent

def package(n):return json.loads((HERE/'examples'/f'{n}.json').read_text())
def ev(i,a,t,s,p,type='submit'):return dict(eventId=i,actor=a,at=t,step=s,payload=p,type=type)
def submit(i,a,t,s,id,value):return ev(i,a,t,s,dict(itemId=id,value=value))
def ref(kind,id):return dict(kind=kind,ref=id)
def txt(s):return dict(kind='text',text=s)
def control(actors,opens=None,closes=None):return dict(actors=actors,opensAt=opens,closesAt=closes)
def media(actor,id,kind,ready=True):return dict(actor=actor,ref=id,kind=kind,ready=ready)
def cases():
 p=package('simplified-chorus');people=list('abcd')+['viewer'];registry=[media(a,'image:'+a,'image') for a in 'abcd']+[media(a,'audio:'+a,'audio') for a in 'ab']+[media('a','pending','audio',False)]
 events=[submit('image-'+a,a,0,'covers',a,ref('image','image:'+a)) for a in 'abcd']
 events += [ev('phase','system',200000000,None,{},'tick'),submit('foreign','a',200000000,'response','d',ref('audio','audio:b')),submit('wrongkind','a',200000000,'response','d',ref('audio','image:a')),submit('pending','a',200000000,'response','d',ref('audio','pending')),submit('wrongsource','a',200000000,'response','b',txt('wrong source')),submit('d','d',200000001,'response','b',txt('Text response B')),submit('a','a',200000002,'response','d',ref('audio','audio:a')),submit('duplicate','a',200000003,'response','d',txt('replacement')),submit('late','c',400000000,'response','d',txt('late')),submit('a','a',400000000,'response','d',ref('audio','audio:a')),submit('a','a',400000000,'response','d',txt('changed'))]
 yield dict(id='multi-day-image-audio-chorus',package=p,participants=people,organizer='a',seed=1,hostInputs={'covers':control(list('abcd'),0,200000000),'response':control(list('abcd'),200000000,400000000)},trustedMedia=registry,events=events),['accepted']*5+['rejected']*4+['accepted']*2+['rejected']*2+['replayed','rejected']
 p=package('daily-music-journal');events=[submit('early','solo',99,'entry','note',ref('audio','take')),submit('one','solo',100,'entry','note',ref('audio','take')),ev('forged','solo',101,'entry',{},'close'),ev('close','system',101,'entry',{},'close'),submit('one','solo',200,'entry','note',ref('audio','take'))]
 yield dict(id='solo-journal-owner-also-host',package=p,participants=['solo'],organizer='solo',hostInputs={'entry':control(['solo'],100,None)},trustedMedia=[media('solo','take','audio')],events=events),['rejected','accepted','rejected','accepted','replayed']
 p=package('feedback-round');events=[submit('post','maker',0,'posts','one',txt('Open piece')),submit('reviewer-before','reviewer',0,'posts','two',txt('Not eligible yet')),ev('forged','maker',1,'posts',control(['maker','reviewer'],None,300000000),'configure'),ev('configure','system',1,'posts',control(['maker','reviewer','new'],None,300000000),'configure'),submit('reviewer','reviewer',2,'posts','two',ref('audio','clip')),submit('new','new',3,'posts','three',txt('Joined primary author')),ev('close','system',4,'posts',{},'close'),ev('configure','system',5,'posts',control(['maker','reviewer','new'],None,300000000),'configure')]
 yield dict(id='public-feedback-effective-actors',package=p,participants=['maker','reviewer','follower'],organizer='maker',hostInputs={'posts':control(['maker'],0,None)},trustedMedia=[media('reviewer','clip','audio')],events=events),['accepted','rejected','rejected','accepted','accepted','accepted','accepted','replayed']
 p=package('daily-music-journal');events=[submit('own','solo',0,'entry','first',txt('Private note')),submit('notwriter','observer',0,'entry','second',txt('no')),ev('end','system',20,None,{},'tick')]
 yield dict(id='private-journal-observer',package=p,participants=['solo','observer'],organizer='solo',hostInputs={'entry':control(['solo'],None,20)},events=events),['accepted','rejected','accepted']
 p=package('simplified-chorus');events=[submit('a','a',0,'covers','a',ref('image','image:a')),submit('b','b',0,'covers','b',ref('image','image:b')),ev('withdraw','system',1,'covers',control(['a'],0,10),'configure'),ev('phase','system',10,None,{},'tick')]
 yield dict(id='source-eligibility-freezes-without-self-fallback',package=p,participants=list('ab'),organizer='a',seed=1,hostInputs={'covers':control(list('ab'),0,10)},trustedMedia=[media(a,'image:'+a,'image') for a in 'ab'],events=events),['accepted']*4
 p=package('simplified-chorus');p['runbook']['steps'][1]['policy']='policy:next_nonself_source@1';p['requires'].remove('seeded_assignment@1');p['requires'].remove('policy:seeded_nonself_source@1');p['requires'].append('policy:next_nonself_source@1');events=[submit('a','a',0,'covers','a',ref('image','image:a')),submit('c','c',0,'covers','c',ref('image','image:c')),ev('close','system',1,'covers',{},'close'),ev('dates','system',1,'response',control(list('abc'),2,200000000),'configure'),submit('early','a',1,'response','c',txt('early')),submit('reply-a','a',2,'response','c',txt('response')),ev('reroll','system',2,'covers',control(list('abc'),0,100),'configure'),ev('close-response','system',3,'response',{},'close')]
 yield dict(id='partial-deterministic-manual-control',package=p,participants=list('abc'),organizer='a',trustedMedia=[media(a,'image:'+a,'image') for a in 'ac'],events=events),['accepted']*4+['rejected','accepted','rejected','accepted']

def check(node,schema=None):
 for req,expected in cases():
  result=run(req);assert result==node(req),req['id'];assert result['outcomes']==expected,(req['id'],result['outcomes'])
  for cut in range(len(req['events'])+1):
   prefix=run(dict(req,events=req['events'][:cut]));resumed=dict(req,state=prefix['state'],events=req['events'][cut:]);assert run(resumed)==node(resumed);assert run(resumed)['state']==result['state'],(req['id'],cut)
  if req['id']=='multi-day-image-audio-chorus':
   a=result['views'][4]['a']['records'][1]['assignment'];assert a=={'itemId':'d','value':ref('image','image:d')};assert result['views'][10]['viewer']['records'][2]['entries']==[]
   final=result['views'][-1]['viewer']['records'][2];assert final['revealed'] and final['entries']==[{'actor':'d','source':{'actor':'b','itemId':'b','value':ref('image','image:b')},'value':txt('Text response B')},{'actor':'a','source':{'actor':'d','itemId':'d','value':ref('image','image:d')},'value':ref('audio','audio:a')}]
  if req['id']=='public-feedback-effective-actors':assert result['views'][0]['follower']['records'][0]['entries']==[{'actor':'maker','itemId':'one','value':txt('Open piece')}];assert len(result['views'][-1]['new']['records'][0]['entries'])==3
  if req['id']=='private-journal-observer':assert result['views'][-1]['observer']['records'][0]['entries']==[]
  if req['id'].startswith('source-eligibility'):assert result['views'][-1]['a']['phase']=='complete' and result['views'][-1]['a']['records'][1]['unmatched'] is True
  if req['id'].startswith('partial-deterministic'):assert result['views'][2]['a']['records'][1]['assignment']['itemId']=='c' and result['views'][2]['c']['records'][1]['assignment']['itemId']=='a'
  if schema:
   import jsonschema;jsonschema.validate(req['package'],schema)
 variants=[]
 def bad(name,change):
  p=package(name);change(p);variants.append(p)
 bad('simplified-chorus',lambda p:p['requires'].remove('host_controls@1'))
 bad('simplified-chorus',lambda p:p['requires'].remove('audio_contributions@1'))
 bad('simplified-chorus',lambda p:p['requires'].remove('image_contributions@1'))
 bad('simplified-chorus',lambda p:p['runbook']['steps'][0].update(visibility='host'))
 bad('simplified-chorus',lambda p:p['runbook']['steps'][0].update(kinds=['video']))
 bad('simplified-chorus',lambda p:p['runbook']['steps'][0].update(kinds=['image','image']))
 bad('simplified-chorus',lambda p:p['runbook']['steps'][0].update(afterMs=86400000))
 bad('simplified-chorus',lambda p:p['runbook']['steps'][1].update(recipients='roles'))
 bad('simplified-chorus',lambda p:p['runbook']['steps'][1].update(policy='policy:balanced@1'))
 bad('simplified-chorus',lambda p:p['runbook']['steps'][1].update(source='response'))
 bad('simplified-chorus',lambda p:p['runbook']['steps'][2].update(source='covers'))
 bad('simplified-chorus',lambda p:p['runbook']['steps'][3].update(source='covers'))
 bad('simplified-chorus',lambda p:p['runbook']['steps'][1].update(cardinality='two'))
 bad('simplified-chorus',lambda p:p['runbook']['steps'][1].update(unmatched='self'))
 bad('simplified-chorus',lambda p:p['runbook']['steps'][0].update(roles=['participant']))
 for p in variants:assert run({'action':'validate','package':p})==node({'action':'validate','package':p})=={'outcome':'invalid_package'}
 p=package('daily-music-journal')
 invalid=[{'entry':control(['a','a'])},{'entry':control(['system'])},{'entry':control(['a'],20,10)},{'entry':control(['a'],False,30)},{'unknown':control(['a'])},{'entry':dict(control(['a']),roles=['maker'])}]
 for inputs in invalid:
  req=dict(package=p,participants=['a'],organizer='a',hostInputs=inputs);assert run(req)==node(req)=={'outcome':'invalid_setup'}
 # Initial controls are immutable setup inputs; later edits are explicit ordered control events.
 req=dict(package=p,participants=['a'],organizer='a',hostInputs={'entry':control(['a'],None,None)});state=run(req)['state'];assert run(dict(req,state=state,hostInputs={'entry':control(['a'],0,30)}))==node(dict(req,state=state,hostInputs={'entry':control(['a'],0,30)}))=={'outcome':'invalid_setup'}
 for cfg in [control(['a'],0,0),dict(control(['a']),replace=True),control(['system']),control(['a'],MAX+1,None)]:
  event=ev('cfg','system',0,'entry',cfg,'configure');result=run(dict(req,events=[event]));assert result==node(dict(req,events=[event])) and result['outcomes']==['rejected']
 # Saved accepted media identity is replayed even if a later resolver denies access.
 req=dict(package=p,participants=['a'],organizer='a',trustedMedia=[media('a','opaque:opus','audio')],events=[submit('one','a',0,'entry','one',ref('audio','opaque:opus'))]);result=run(req);assert result==node(req) and result['outcomes']==['accepted'];resumed=dict(req,state=result['state'],trustedMedia=[],events=[submit('one','a',MAX,'entry','one',ref('audio','opaque:opus'))]);assert run(resumed)==node(resumed) and run(resumed)['outcomes']==['replayed']
 if schema:
  import jsonschema
  for index in [3,4,5,6,7,8,12,13,14]:assert list(jsonschema.Draft202012Validator(schema).iter_errors(variants[index]))
 # Effective recipients can include noncontributors; a one-source pool never assigns self.
 p=package('simplified-chorus');p['runbook']['steps'][0]['kinds']=['audio'];p['runbook']['steps'][1]['recipients']='effective';p['runbook']['steps'][2]['kinds']=['image']
 req=dict(package=p,participants=list('abc'),organizer='a',seed=1,hostInputs={'covers':control(list('abc'),0,10),'response':control(list('abc'),10,20)},trustedMedia=[media('a','clip','audio'),media('b','photo','image')],events=[submit('source','a',0,'covers','source',ref('audio','clip')),ev('tick','system',10,None,{},'tick'),submit('reply','b',10,'response','source',ref('image','photo')),ev('end','system',20,None,{},'tick')])
 result=run(req);assert result==node(req) and result['outcomes']==['accepted']*4
 assert result['views'][1]['a']['records'][1]['unmatched'] and result['views'][1]['b']['records'][1]['assignment']=={'itemId':'source','value':ref('audio','clip')} and result['views'][1]['c']['records'][1]['assignment']=={'itemId':'source','value':ref('audio','clip')}
 assert result['state']['randomState']==1 and result['views'][-1]['c']['records'][2]['entries'][0]['value']==ref('image','photo')
 # Prototype-like/opaque identities stay scalar IDs, not role labels or object keys.
 p=package('feedback-round');people=['__proto__','constructor','9007199254740999','😀'];events=[submit('event-'+str(i),a,0,'posts','item-'+str(i),txt(a)) for i,a in enumerate(people)]
 req=dict(package=p,participants=people,organizer='__proto__',hostInputs={'posts':control(people)},events=events);result=run(req);assert result==node(req) and result['outcomes']==['accepted']*4 and len(result['views'][-1]['__proto__']['records'][0]['entries'])==4
 # Resolved host dates must leave safe integer room for retained relative operations.
 p=package('daily-music-journal');p['runbook']['steps'].append({'id':'later','op':'pause@1','prompt':'Continue','afterMs':10});p['requires'].append('pause@1')
 req=dict(package=p,participants=['a'],organizer='a',hostInputs={'entry':control(['a'],0,MAX)})
 assert run(req)==node(req)=={'outcome':'invalid_setup'}
 req['hostInputs']={'entry':control(['a'],0,MAX-10)};assert run(req)==node(req) and 'state' in run(req)
 e=ev('overflow','system',0,'entry',control(['a'],0,MAX),'configure');assert run(dict(req,events=[e]))==node(dict(req,events=[e])) and run(dict(req,events=[e]))['outcomes']==['rejected']
 print('6 typed-artifact/host-control traces; 15 invalid definitions; setup/control/media/ownership/deadline/privacy/replay boundaries pass')
 return len(variants)
if __name__=='__main__':
 from check import node
 check(node,json.loads((HERE/'package.schema.json').read_text()))
