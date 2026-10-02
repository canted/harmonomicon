"""Exact first-valid and portable queue witnesses, independent engines/recovery."""
import copy,json,subprocess,sys
from pathlib import Path
from runtime import run,validate,Engine,MAX
HERE=Path(__file__).resolve().parent
PEOPLE=['a','b','c','d']
I='urn:uuid:00000000-0000-0000-0000-000000000024'
O='urn:uuid:00000000-0000-0000-0000-000000000023'
def package(which='start'):
 return json.loads((HERE/'examples'/('creative-relay-'+which+'.json')).read_text())
def node(req):return json.loads(subprocess.check_output(['node',str(HERE/'runtime.mjs')],input=json.dumps(req),text=True))
def base(which='start',people=PEOPLE,order=None,canonical=None,window=100):
 p=package(which);p['runbook']['steps'][0]['windowMs']=window;p['runbook']['steps'][0]['retryAfterMs']=50
 req=dict(package=p,participants=people,organizer='organizer',instanceId=I,seed=1729,events=[])
 if which!='start':
  q={'ref':{'instance':O,'source':'piece'},'order':order or people[:],'canonical':None if canonical is None else canonical['ref'],'notBefore':0}
  req.update(queueBindings={'line':q},trustedQueues=[dict(queue=q,viewers=people+['organizer'],ready=True)])
 if canonical is not None:
  binding={'candidate':canonical,'via':dict(canonical['ref'],round=canonical['round'])}
  req.update(inputBindings={'previous':binding},trustedInputs=[dict(binding=binding,viewers=people+['organizer'],ready=True)])
 return req
def candidate(actor='a',kind='text'):
 return {'ref':{'instance':O,'source':'piece','itemId':'prior'},'actor':actor,'value':{'kind':'text','text':'prior piece'} if kind=='text' else {'kind':kind,'ref':'oldmedia'},'round':None}
def event(req,actor,kind='submit',at=1,**changes):
 r=run(req)['state']['records'][0];offer=r['offer'];ticket=next(t for t in offer['invitations'] if t['actor']==actor)
 payload={'invitation':ticket['key'],'predecessor':None if r['canonical'] is None else r['canonical']['ref']}
 if kind=='submit':payload.update(itemId='item-'+str(len(req['events'])),value={'kind':'text','text':actor+' contributes'})
 payload.update(changes)
 return dict(eventId='event-'+str(len(req['events'])),type=kind,actor=actor,at=at,step='piece',payload=payload)
def append(req,ev):req['events'].append(ev);return run(req)
def compare(req):
 result=run(req);assert result==node(req),(req,result,node(req))
 initial=run(dict(req,events=[]))['state']
 for i,ev in enumerate(req['events']):
  restored=dict(req,state=initial,events=[ev]);part=run(restored);assert part==node(restored),(ev,part,node(restored))
  assert part['outcomes']==[result['outcomes'][i]] and part['views']==[result['views'][i]]
  initial=part['state']
 assert initial==result['state'];return result

def witnesses():
 cases=[]
 def save(name,req,wants):cases.append({'id':name,'request':req,'outcomes':wants})
 q=base('retry-empty');r=run(q)['state']['records'][0];assert r['offer']['actors']==['a','b']
 win=event(q,'a');append(q,win);late=copy.deepcopy(win);late.update(eventId='loser',actor='b');late['payload']['invitation']=2
 q['events']+=[late,dict(win,at=101),dict(win,at=102,payload=dict(win['payload'],itemId='changed'))]
 save('first-valid-race-and-replay',q,['accepted','rejected','replayed','rejected'])
 q=base('retry-empty');q['events'].append(event(q,'a',value={'kind':'image','ref':'foreign'}));q['events'].append(event(q,'b'));save('invalid-media-does-not-win',q,['rejected','accepted'])
 q=base('retry-empty');stale=event(q,'a',at=100);q['events']=[stale];save('exclusive-deadline-stale-ticket',q,['rejected'])
 q=base('retry-empty');before=event(q,'b');q['events'].append(event(q,'a','decline'));r=run(q)['state']['records'][0]
 assert r['offer']['actors']==['b','c'] and r['offer']['closesAt']==100 and r['offer']['invitations'][0]['key']==before['payload']['invitation']
 q['events'].append(dict(before,eventId='retained-partner',at=2));save('decline-keeps-partner-ticket',q,['accepted','accepted'])
 q=base('retry-empty');decline=event(q,'a','decline');q['events'].append(event(q,'b'));q['events'].append(dict(decline,at=2));save('partner-wins-before-decline',q,['accepted','rejected'])
 q=base('continue',canonical=candidate(),order=['a','b','c','d']);q['events']=[event(q,'b')];save('loser-front-old-author-order',q,['accepted'])
 assert run(q)['state']['records'][0]['queue']['order']==['c','a','d','b']
 q=base('continue',canonical=candidate(),order=['a','b','c','d']);q['events']=[dict(eventId='expire',type='tick',actor='system',at=100,step=None,payload={})]
 r=run(q)['state']['records'][0];assert r['offer']['actors']==['d','b'] and 'a' not in r['offer']['actors']
 q['events'].append(dict(q['events'][0],eventId='exhaust',at=200));save('odd-tail-prior-author-excluded-full-pass',q,['accepted','accepted'])
 assert run(q)['state']['records'][0]['output']['reason']=='pass_complete'
 q=base('continue',people=['a','b'],canonical=candidate());save('small-roster-pause',q,[])
 assert run(q)['state']['records'][0]['status']=='paused'
 q=base('retry-empty');q['events']=[dict(eventId='late',type='tick',actor='system',at=1000,step=None,payload={})];save('late-worker-fresh-window',q,['accepted'])
 assert run(q)['state']['records'][0]['offer']['closesAt']==1100
 q=base('retry-empty');q['events']=[dict(eventId='near-max',type='tick',actor='system',at=MAX-1,step=None,payload={})];save('nonresumable-safe-clock-exhaustion',q,['accepted'])
 assert run(q)['state']['records'][0]['queue']['notBefore'] is None
 q=base('continue',canonical=candidate(),window=86400000);q['events']=[dict(eventId='day-expiry',type='tick',actor='system',at=86400000,step=None,payload={})];save('shared24h-expiration-exclusion',q,['accepted'])
 q=base('retry-empty');old=event(q,'a');q['events']=[dict(eventId='withdraw',type='roster',actor='system',at=1,step='piece',payload={'actors':['b','c','d']}),dict(old,at=2),event(dict(q,events=q['events'][:1]),'b',at=3)]
 save('membership-withdrawal-ticket-retention',q,['accepted','rejected','accepted'])
 q=base('continue',canonical=candidate());q['events']=[dict(eventId='new-person',type='roster',actor='system',at=1,step='piece',payload={'actors':['a','b','c','new']})];save('newcomer-denied-without-canonical-authority',q,['rejected'])
 q=base('retry-empty');q['events']=[dict(eventId='queue-outsider',type='roster',actor='system',at=0,step='piece',payload={'actors':PEOPLE+['outsider']})];save('queue-audience-denies-roster-expansion-without-canonical',q,['rejected'])
 assert 'outsider' not in run(q)['state']['hostActors']
 q=base('retry-empty');q['trustedQueues'][0]['viewers'].append('preauthorized');q['events']=[dict(eventId='queue-authorized',type='roster',actor='system',at=0,step='piece',payload={'actors':PEOPLE+['preauthorized']})];save('queue-audience-permits-preauthorized-roster-expansion',q,['accepted'])
 q=base('retry-empty');q['package']['queueInputs']['other']={'type':'invitation_queue'};other=copy.deepcopy(q['package']['runbook']['steps'][0]);other.update(id='other',queueInput={'binding':'other'});q['package']['runbook']['steps'].append(other);q['queueBindings']['other']=copy.deepcopy(q['queueBindings']['line']);q['queueBindings']['other']['ref']['source']='other';q['trustedQueues'][0]['viewers'].append('outsider');q['trustedQueues'].append(dict(queue=copy.deepcopy(q['queueBindings']['other']),viewers=PEOPLE+['organizer'],ready=True));q['events']=[dict(eventId='all-queues-outsider',type='roster',actor='system',at=0,step='piece',payload={'actors':PEOPLE+['outsider']})];save('queue-audience-rechecks-every-retained-source',q,['rejected'])
 q=base('retry-empty');p=q['package'];p['runbook']['steps'].append(dict(id='later',op='pool@2',prompt='Collect later.',kinds=['text'],perActor=1,visibility='private'));p['requires'].append('pool@2');q['events']=[event(q,'a')];q['events'].append(dict(eventId='later-queue-outsider',type='configure',actor='system',at=1,step='later',payload={'actors':PEOPLE+['outsider'],'opensAt':None,'closesAt':None}));save('queue-audience-denies-later-window-expansion',q,['accepted','rejected'])
 assert 'outsider' not in run(q)['state']['hostActors']
 q=base('retry-empty');q['events']=[event(q,'a',invitation=True),event(q,'b',predecessor=None)];save('typed-ticket-bool-rejected',q,['rejected','accepted'])
 return cases

def negatives():
 variants=[]
 def change(fn):
  req=base();fn(req['package']);variants.append(req['package'])
 for field,value in [('windowMs',0),('windowMs',604800001),('windowMs',True),('retryAfterMs',0),('policy','policy:unknown@1'),('kinds',[]),('kinds',['video']),('input',{'binding':'missing'}),('queueInput',{'binding':'missing'})]:change(lambda p,f=field,v=value:p['runbook']['steps'][0].update({f:v}))
 change(lambda p:p['requires'].remove('first_valid@1'));change(lambda p:p['requires'].remove('invitation_queue@1'));change(lambda p:p.update(queueInputs={'orphan':{'type':'invitation_queue'}}));change(lambda p:p['runbook']['steps'][0].update(extra=True))
 change(lambda p:p.update(queueInputs=None))
 for p in variants:assert run(dict(action='validate',package=p))==node(dict(action='validate',package=p))=={'outcome':'invalid_package'}
 q=base('continue',canonical=candidate())
 setups=[]
 for mutate in [lambda q:q.update(seed=0),lambda q:q['queueBindings']['line'].update(canonical=None),lambda q:q['queueBindings']['line'].update(notBefore=1),lambda q:q['queueBindings']['line'].update(notBefore=None),lambda q:q.update(trustedQueues=[]),lambda q:q.update(trustedInputs=[]),lambda q:q['queueBindings']['line'].update(order=['a','a'])]:
  x=copy.deepcopy(q);mutate(x);setups.append(x)
 for lone_surrogate in ['\ud800','\udfff']:
  x=base('retry-empty');x['queueBindings']['line']['order'].append(lone_surrogate);x['trustedQueues'][0]['queue']=copy.deepcopy(x['queueBindings']['line']);setups.append(x)
 for lone_surrogate in ['\ud800','\udfff']:
  x=base('continue',canonical=candidate());x['queueBindings']['line']['canonical']['itemId']=lone_surrogate;x['inputBindings']['previous']['candidate']['ref']['itemId']=lone_surrogate;x['inputBindings']['previous']['via']['itemId']=lone_surrogate;x['trustedQueues'][0]['queue']=copy.deepcopy(x['queueBindings']['line']);x['trustedInputs'][0]['binding']=copy.deepcopy(x['inputBindings']['previous']);setups.append(x)
 for req in setups:assert run(req)==node(req)=={'outcome':'invalid_setup'}
 # Two binding names cannot alias one actual qualified queue record.
 alias=copy.deepcopy(q);alias['package']['queueInputs']['alias']={'type':'invitation_queue'};other=copy.deepcopy(alias['package']['runbook']['steps'][0]);other.update(id='other',queueInput={'binding':'alias'});alias['package']['runbook']['steps'].append(other);alias['queueBindings']['alias']=copy.deepcopy(alias['queueBindings']['line'])
 assert run(alias)==node(alias)=={'outcome':'invalid_setup'}
 # A valid Unicode scalar outside the destination roster is still a valid saved identity.
 unicode_queue=base('retry-empty');unicode_queue['queueBindings']['line']['order'].append('🙂');unicode_queue['trustedQueues'][0]['queue']=copy.deepcopy(unicode_queue['queueBindings']['line']);assert run(unicode_queue)==node(unicode_queue) and 'outcome' not in run(unicode_queue)
 return variants,len(variants)+len(setups)+1

def churn():
 q=base('retry-empty');q['participants']=['a','b','c'];q['queueBindings']['line']['order']=['a','b','c'];q['trustedQueues'][0]['viewers']=['a','b','c','organizer']+['new'+str(i) for i in range(100)]+['waiting'+str(i) for i in range(100)]
 # Replace only a non-survivor at every transition, so full eligible pass never completes.
 for i in range(100):
  r=run(q)['state']['records'][0];survivor=r['offer']['actors'][0];new='new'+str(i)
  q['events'].append(dict(eventId='churn-'+str(i),type='roster',actor='system',at=i,step='piece',payload={'actors':[survivor,new,'waiting'+str(i)]}))
 r=run(q)['state']['records'][0];assert r['failures']==100 and r['output']['reason']=='failure_budget'
 assert run(q)==node(q)
 boundary=copy.deepcopy(q);boundary['events']=boundary['events'][:99];boundary['events'].append(dict(eventId='hundredth-expiry',type='tick',actor='system',at=100,step=None,payload={}))
 r=run(boundary)['state']['records'][0];assert r['failures']==100 and r['output']['reason']=='failure_budget'
 assert run(boundary)==node(boundary)
 return q

def held_out():
 q=base(window=86400000);p=q['package'];p['id']='org.harmonomicon.example.relay-paired-reflection'
 p['runbook']['steps'][0]['retryAfterMs']=86400000
 p['participants']['min']=2
 p['content'].update(title='Creative contribution and paired reflection',
  summary='Two people are invited to add one canonical story piece; then everyone writes private notes in pairs.',
  setup='Enroll an even number of participants, from 2 to 100, and keep the roster fixed for this exercise. Shuffle once and invite two people with a shared 24-hour deadline. After selection, a full unsuccessful pass or pause, form pairs in enrollment order. The organizer closes reflection, or it closes after 24 hours.',
  prompt='Add a story piece, then reflect with your partner.',
  participant='If invited, submit a complete text or image, or decline. The first valid accepted piece becomes canonical. Then everyone may submit one note visible only to their pair. If no piece was accepted, discuss an idea for starting the story.',
  completion='After the invitation phase ends, move into paired reflection; the notes close when the organizer advances or 24 hours pass. The saved queue permits a separate host-launched relay continuation; this exercise does not automatically launch it.',
  access='Canonical contributions are attributed and visible to all bound viewers. Reflection notes stay within each pair, including after closure. An organizer has no extra note-reading access; a participating organizer can read only their own pair notes. The organizer can see all pair membership and close reflection. Media bytes require host authority; queue membership gives no new access.')
 p['runbook']['steps'] += [dict(id='pairs',op='partition@1',policy='policy:roster_chunks@1',minSize=2,maxSize=2,prompt='Form reflection pairs in enrollment order.',afterMs=None),dict(id='reflect',op='collect_group@1',source='pairs',prompt='Reflect with your partner on the accepted piece. If nobody contributed, discuss an idea for starting the story. Your note is visible only within your pair.',close='organizer',afterMs=86400000)]
 p['requires']+=['partition@1','collect_group@1','policy:roster_chunks@1']
 pair=run(q)['state']['records'][0]['offer']['actors'];q['events']=[event(q,pair[0])]
 q['events']+=[dict(eventId='private-reflection',type='submit',actor='a',at=2,step='reflect',payload={'text':'private pair note'}),dict(eventId='finish-reflection',type='advance',actor='organizer',at=3,step='reflect',payload={})]
 result=compare(q);assert result['outcomes']==['accepted']*3
 assert result['views'][-1]['a']['records'][-1]['entries']==result['views'][-1]['b']['records'][-1]['entries']
 assert result['views'][-1]['c']['records'][-1]['entries']==[]
 assert result['views'][-1]['organizer']['records'][-1]['entries']==[]
 empty=copy.deepcopy(q);empty['events']=[]
 for day in [1,2]:empty['events'].append(dict(eventId='empty-day-'+str(day),type='tick',actor='system',at=day*86400000,step=None,payload={}))
 empty['events'] += [dict(eventId='empty-reflection',type='submit',actor='a',at=2*86400000,step='reflect',payload={'text':'an idea to start'}),dict(eventId='empty-finish',type='advance',actor='organizer',at=2*86400000+1,step='reflect',payload={})]
 empty_result=compare(empty);assert empty_result['outcomes']==['accepted']*4
 assert empty_result['state']['records'][0]['canonical'] is None and empty_result['state']['records'][0]['status']=='exhausted'
 assert empty_result['views'][-1]['b']['records'][-1]['entries'][0]['value']['text']=='an idea to start'
 assert empty_result['views'][-1]['c']['records'][-1]['entries']==empty_result['views'][-1]['organizer']['records'][-1]['entries']==[]
 odd=copy.deepcopy(q);odd['participants']=['a','b','c'];odd['events']=[];assert run(odd)==node(odd)=={'outcome':'invalid_setup'}
 (HERE/'examples/relay-paired-reflection.json').write_text(json.dumps(p,indent=2)+'\n')
 print('Held-out 24-hour first-valid/private-pair reflection: selected and empty paths, even roster and private notes pass without interpreter edits')
 return q

def check(schema=False):
 cases=witnesses()
 for case in cases:
  result=compare(case['request']);assert result['outcomes']==case['outcomes'];print('ok',case['id'])
 variants,count=negatives();churn();held_out()
 if schema:
  import jsonschema
  definition=json.loads((HERE/'package.schema.json').read_text());jsonschema.Draft202012Validator.check_schema(definition)
  for p in (HERE/'examples').glob('*.json'):jsonschema.validate(json.loads(p.read_text()),definition)
  for i in [0,1,2,3,4,5,6,12,13]:
   try:jsonschema.validate(variants[i],definition)
   except jsonschema.ValidationError:pass
   else:raise AssertionError(('invalid structural schema',i))
  print('0.24 schema and all examples pass')
 (HERE/'conformance/relay-cases.json').write_text(json.dumps(cases,indent=2)+'\n')
 print(f'{len(cases)} relay traces with exact views/state and every-boundary restart; {count} invalid package/setup witnesses; 100-transition churn cap pass')
 return len(cases),count
if __name__=='__main__':check('--schema' in sys.argv)
