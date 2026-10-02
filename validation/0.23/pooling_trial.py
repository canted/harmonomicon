#!/usr/bin/env python3
"""Actual typed quotas, private iteration, consumer reuse and durable recovery."""
import base64,concurrent.futures,copy,json,sqlite3,tempfile,time
from pathlib import Path
from run import Host,package,ROOT
from runtime import run
from input_trial import create,control,record,media,read
from image_trial import png
from artifact_trial import wav

PEOPLE=['a','b','c']
BASE=['clock@1','durable_state@1','host_controls@1','identity@1','private_views@1','serial_events@1','text@1']
NEW=['pool@2','for_items@2','assign_item@2','acknowledge@2','reveal_item@2','vote@3','tally@4','select@3','present@3','reveal_ballots@3','assign_artifacts@2','artifact_response@2','reveal_artifact_responses@2','policy:next_nonself_item@1']

def body(event_id,kind,sid,payload):return dict(eventId=event_id,type=kind,step=sid,payload=payload)
def text(s):return dict(kind='text',text=s)
def pool_only(kinds=['text'],quota=2):
 p=package('typed-sharing');p['id']+='-probe-'+str(quota)+'-'+''.join(kinds);p['runbook']['steps']=p['runbook']['steps'][:1]
 p['runbook']['steps'][0].update(kinds=kinds,perActor=quota)
 p['requires']=sorted(BASE+['pool@2']+[k+'_contributions@1' for k in kinds if k!='text'])
 return p

def all_views(h,iid,tokens):return {a:h.request('/instances/'+iid+'/view',token=t)['view'] for a,t in tokens.items()}

class Fixture:
 def __init__(self,h,p,iid='test',people=PEOPLE,organizer='organizer',controls=None,started=0):
  self.h,self.p,self.iid=h,p,iid;self.created,_=create(h,p,iid,inputs=controls or {},people=people,organizer=organizer)
  assert self.created['outcome']=='created',self.created
  self.tokens=self.created['tokens'];self.at=started
  self.req=dict(package=p,participants=people,organizer=organizer,startedAt=started,instanceId=self.created['instanceIdentity'],hostInputs=controls or {},seed=h.seed,events=[],trustedMedia=[])
  if h.tie_choice is not None:self.req['tieChoices']=[h.tie_choice]*100
  self.reference=run(self.req);assert 'outcome' not in self.reference,self.reference
 def value(self,actor,kind,n=1):
  if kind=='text':return text('distinct '+str(n))
  blob=png(n%255) if kind=='image' else wav(n)
  value=media(self.h,self.iid,self.tokens,actor,kind,blob);self.req['trustedMedia'].append(dict(actor=actor,ref=value['ref'],kind=kind,ready=True));return value
 def verify(self,restart=True):
  expected=self.reference
  assert 'outcome' not in expected,expected
  wanted=expected['views'][-1]
  for actor in wanted:
   if actor not in self.tokens:
    self.tokens[actor]='host-bound-'+self.iid+'-'+actor
    assert self.h.request('/instances/'+self.iid+'/bindings',dict(actor=actor,token=self.tokens[actor]))['outcome']=='bound'
  got=all_views(self.h,self.iid,self.tokens)
  assert got==wanted,(self.h.kind,self.iid,len(self.req['events']),got,wanted)
  if restart:self.h.restart();assert all_views(self.h,self.iid,self.tokens)==wanted
  return got
 def act(self,actor,kind,sid,payload={},eid=None,at=None,want='accepted',restart=True):
  self.at=self.at if at is None else at;self.h.clock(self.at)
  event=dict(actor=actor,at=self.at,**body(eid or 'e'+str(len(self.req['events'])),kind,sid,payload))
  route='control' if actor=='system' else 'events'
  outcome=self.h.request('/instances/'+self.iid+'/'+route,{k:event[k] for k in ['eventId','type','step','payload']},self.tokens.get(actor,'local-test-admin'))['outcome']
  assert outcome==want,(self.h.kind,self.iid,event,outcome,want)
  recovered=dict(self.req,state=self.reference['state'],events=[event])
  self.reference=run(recovered);assert self.reference['outcomes']==[outcome],(event,self.reference,outcome)
  self.req['events'].append(event)
  return self.verify(restart)
 def submit(self,actor,item,value,sid='pieces',**kw):return self.act(actor,'submit',sid,dict(itemId=item,value=value),**kw)
 def close(self,sid='pieces',**kw):return self.act('system','close',sid,{},**kw)
 def view(self,actor='c'):return self.h.request('/instances/'+self.iid+'/view',token=self.tokens[actor])['view']
 def bytes(self,actor,value):return read(self.h,self.iid,self.tokens,actor,value['ref'])

def quotas(kind,directory):
 h=Host(kind,directory/(kind+'-quota.sqlite'))
 try:
  for i,(kinds,quota) in enumerate((k,q) for k in [['text'],['image'],['audio'],['text','image','audio']] for q in [1,2]):
   f=Fixture(h,pool_only(kinds,quota),'quota-'+str(i));accepted=[]
   for n in range(quota):
    value=f.value('a',kinds[n%len(kinds)],n+1);accepted.append(value);f.submit('a','item-'+str(n),value,eid='accepted-'+str(n))
   v=record(f.view(),'pieces');assert v['count']==quota and v['entries']==[] and f.view()['step']=='pieces'
   own=record(f.view('a'),'pieces');assert own['ownCount']==quota and own['remaining']==0 and len(own['entries'])==quota
   f.submit('a','overflow',text('overflow') if 'text' in kinds else accepted[0],want='rejected')
   f.submit('b','item-0',accepted[0],want='rejected')
   wrong=text('outside kind') if 'text' not in kinds else dict(kind='video',ref='unsupported')
   f.submit('b','wrong-kind',wrong,want='rejected')
   f.act('system','configure','pieces',control(['b','c']))
   f.submit('a','while-withdrawn',accepted[0],want='rejected')
   f.act('system','configure','pieces',control(PEOPLE))
   f.submit('a','restored-overflow',accepted[0],want='rejected')
   f.close();f.submit('a','late',accepted[0],want='rejected')
   f.submit('a','item-0',accepted[0],eid='accepted-0',want='replayed')
   assert record(f.view('a'),'pieces')['ownCount']==quota
  # Foreign/unready/wrong-kind refs fail before quota use; ready retries retain identity.
  f=Fixture(h,pool_only(['image','audio'],2),'authority')
  image=f.value('a','image',7);audio=f.value('b','audio',8)
  f.submit('b','foreign',image,want='rejected');f.submit('a','foreign-audio',audio,want='rejected')
  f.submit('a','wrong-ref-kind',dict(kind='audio',ref=image['ref']),want='rejected')
  with sqlite3.connect(h.db) as db:db.execute('UPDATE media SET ready=0 WHERE instance=? AND actor=?',('authority','a'))
  # The actual host authority changes; mirror readiness only for a fresh attempt.
  f.req['trustedMedia'][0]['ready']=False;f.submit('a','pending',image,eid='ready-retry',want='rejected')
  with sqlite3.connect(h.db) as db:db.execute('UPDATE media SET ready=1 WHERE instance=? AND actor=?',('authority','a'))
  f.req['trustedMedia'][0]['ready']=True;f.submit('a','pending',image,eid='ready-retry')
  f.submit('a','same-bytes-new-id',image)
  own=record(f.view('a'),'pieces')['entries'];assert own[0]['value']==own[1]['value'] and own[0]['ref']!=own[1]['ref']
  assert f.bytes('c',image)['outcome']=='unauthorized';f.close()
 finally:h.stop()
 print(kind+': independent kinds/shared quotas, distinct IDs, withdrawal accounting, private actual media and retries pass',flush=True)

def iteration(kind,directory,old_source=False):
 h=Host(kind,directory/(kind+'-iteration-'+str(old_source)+'.sqlite'))
 try:
  p=package('typed-sharing')
  if old_source:
   p['id']+='-old-source';p['runbook']['steps'][0]=dict(id='pieces',op='artifact_pool@1',prompt='Submit one ready piece.',kinds=['text','image','audio'],visibility='private')
   p['requires']=sorted(set(p['requires'])-{'pool@2'}|{'artifact_pool@1'})
  controls={'pieces':control(['a','b','c','d'])};f=Fixture(h,p,controls=controls)
  if old_source:
   value=f.value('b','audio',7);f.submit('b','old-audio',value);f.close()
   f.act('a','claim','claim:0');assert base64.b64decode(f.bytes('a',value)['data'])==wav(7)
   f.act('a','advance','read:0');assert record(f.view(),'share')['candidate']['actor']=='b'
   assert base64.b64decode(f.bytes('c',value)['data'])==wav(7)
   return
  first=text('first accepted');image=f.value('a','image',4);audio=f.value('b','audio',5)
  f.submit('a','first',first);f.submit('a','image',image);f.submit('b','audio',audio)
  f.act('system','configure','pieces',control(['a','b','d']))
  f.close();assert f.view()['step']=='claim:0'
  f.act('a','claim','claim:0',want='rejected');f.act('organizer','claim','claim:0',want='rejected');f.act('c','claim','claim:0',want='rejected')
  f.act('d','claim','claim:0',eid='first-claim')
  assigned=record(f.view('d'),'claim')['assignment'];assert assigned['actor']=='a' and assigned['value']==first
  assert record(f.view('c'),'claim')['assignment'] is None
  f.act('b','claim','claim:0',want='rejected');f.act('d','claim','claim:0',eid='first-claim',want='replayed')
  f.act('d','advance','read:0')
  assert record(f.view(),'share')['candidate']==assigned and f.view()['step']=='claim:1'
  f.act('b','claim','claim:1');assert base64.b64decode(f.bytes('b',image)['data'])==png(4)
  # A timeout does not publish the item; the saved reader grant remains available.
  f.act('c','advance','read:1',at=30000,want='rejected')
  shares=[r for r in f.view()['records'] if r['step']=='share'];assert shares[1]['candidate'] is None
  assert f.bytes('c',image)['outcome']=='unauthorized' and image['ref'] not in json.dumps(f.view('c'))
  assert base64.b64decode(f.bytes('b',image)['data'])==png(4)
  f.act('d','claim','claim:2');assert base64.b64decode(f.bytes('d',audio)['data'])==wav(5)
  assert f.bytes('c',audio)['outcome']=='unauthorized'
  f.act('d','advance','read:2')
  assert base64.b64decode(f.bytes('c',audio)['data'])==wav(5)
  shares=[r['candidate'] for r in f.view()['records'] if r['step']=='share'];assert [c['ref']['itemId'] if c else None for c in shares]==['first',None,'audio']
  assert f.view()['phase']=='complete' and not any(r['op']=='for_items@2' for r in f.view()['records'])
  assert image['ref'] not in json.dumps(f.view('c'))
  f.act('d','claim','claim:0',want='rejected')
  f.act('d','claim','claim:0',eid='first-claim',want='replayed')
 finally:h.stop()
 print(kind+': private typed iteration/order/frozen readers/ack timeout/attributed actual bytes/restart pass',flush=True)

def contest(kind,directory):
 h=Host(kind,directory/(kind+'-multi-contest.sqlite'),tie_choice=0)
 try:
  p=package('text-pool-vote');f=Fixture(h,p)
  f.submit('a','one',text('same value'));f.submit('a','two',text('same value'));f.submit('b','withdrawn',text('exclude'))
  f.act('system','configure','pieces',control(['a','c']))
  f.close();choices=record(f.view(),'vote')['candidates'];assert len(choices)==2 and choices[0]['value']==choices[1]['value'] and choices[0]['ref']!=choices[1]['ref']
  f.act('c','submit','vote',dict(candidate=dict(choices[0]['ref'],instance='urn:uuid:00000000-0000-0000-0000-000000000000')),want='rejected')
  f.act('c','submit','vote',dict(candidate=choices[0]['ref']),eid='ballot')
  f.act('c','submit','vote',dict(candidate=choices[1]['ref']),eid='change')
  f.act('c','submit','vote',dict(candidate=choices[0]['ref']),eid='ballot',want='replayed')
  f.close('vote');out=record(f.view(),'result')['output'];assert out['totalVotes']==1 and [r['count'] for r in out['counts']]==[0,1] and out['selected']==choices[1]
  for actor in ['a','b','organizer']:assert record(f.view(actor),'vote')['entries']==[]
  # Accepted qualified new result supplies a real starting input of a fresh instance.
  target=package('typed-continuation');bindings={'starting_piece':dict(instance='test',result='selected')}
  made,_=create(h,target,'successor',bindings,people=PEOPLE)
  assert made['outcome']=='created',made
  inp=record(h.request('/instances/successor/view',token=made['tokens']['c'])['view'],'continuations')['input']
  assert inp['candidate']==out['selected'] and inp['via']['instance']==f.created['instanceIdentity']
 finally:h.stop()
 print(kind+': multi-item current vote counts/final source eligibility/private totals and qualified successor binding pass',flush=True)

def workshop(kind,directory):
 h=Host(kind,directory/(kind+'-workshop.sqlite'),seed=1729)
 try:
  f=Fixture(h,package('typed-response-workshop'),people=list('abcd'))
  a1=text('first proposal');a2=f.value('a','audio',9);b1=f.value('b','image',8);b2=text('unused second idea')
  for a,item,value in [('a','a-first',a1),('a','a-second',a2),('b','b-first',b1),('b','b-second',b2)]:f.submit(a,item,value)
  f.close();assign={a:record(f.view(a),'sources')['assignment'] for a in 'abcd'}
  assert [assign[a]['ref']['itemId'] for a in 'abcd']==['b-first','a-first','a-first','a-first']
  assert all(assign[a]['actor']!=a for a in 'abcd')
  assert f.bytes('c',a2)['outcome']=='unauthorized'
  assert base64.b64decode(f.bytes('a',b1)['data'])==png(8)
  for a in 'abcd':
   chosen=assign[a]['ref']
   f.act(a,'submit','response',dict(candidate=dict(chosen,itemId='wrong'),value=text('wrong')),want='rejected')
   f.act(a,'submit','response',dict(candidate=chosen,value=text('next '+a)),eid='response-'+a)
  f.act('a','submit','response',dict(candidate=assign['a']['ref'],value=text('replacement')),want='rejected')
  f.close('response')
  for a in 'abcd':
   linked=record(f.view(a),'response')['entries'];assert len(linked)==4 and all(x['source']['ref']['itemId'] in ['a-first','b-first'] for x in linked)
  assert f.bytes('c',a2)['outcome']=='unauthorized' and a2['ref'] not in json.dumps(f.view('c'))
  for a in 'abcd':f.act(a,'submit','discussion',dict(text='private '+a))
  v=f.view('a');assert {x['actor'] for x in record(v,'discussion')['entries']}=={'a','b'}
  assert record(f.view('organizer'),'discussion')['entries']==[]
  export=h.request('/packages/'+f.p['id']+'/'+f.p['version']);assert export['package']==f.p
  return f.p,export['digest']
 finally:h.stop()

def races_deadlines(kind,directory):
 h=Host(kind,directory/(kind+'-typed-pool-races.sqlite'))
 try:
  p=pool_only(['text'],2);tokens=h.setup(p)
  def post(a,e):return h.request('/instances/test/events',e,tokens[a])['outcome']
  first=body('first','submit','pieces',dict(itemId='first',value=text('first')));assert post('a',first)=='accepted'
  contenders=[body('slot-'+str(i),'submit','pieces',dict(itemId='slot-'+str(i),value=text('slot'))) for i in range(2)]
  with concurrent.futures.ThreadPoolExecutor(2) as ex:out=list(ex.map(lambda e:post('a',e),contenders))
  assert sorted(out)==['accepted','rejected'];winner=contenders[out.index('accepted')]
  h.restart();assert post('a',winner)=='replayed' and record(h.request('/instances/test/view',token=tokens['a'])['view'],'pieces')['ownCount']==2
  t=h.setup(p,'id-race');bodies=[body('same-'+a,'submit','pieces',dict(itemId='same',value=text(a))) for a in 'ab']
  with concurrent.futures.ThreadPoolExecutor(2) as ex:out=list(ex.map(lambda pair:h.request('/instances/id-race/events',pair[1],t[pair[0]])['outcome'],zip('ab',bodies)))
  assert sorted(out)==['accepted','rejected']
  for n in range(3):
   iid='close-'+str(n);t=h.setup(p,iid);submit=body('submit','submit','pieces',dict(itemId='x',value=text('x')));close=body('close','close','pieces',{})
   with concurrent.futures.ThreadPoolExecutor(2) as ex:
    calls=[ex.submit(h.request,'/instances/'+iid+'/events',submit,t['a']),ex.submit(h.request,'/instances/'+iid+'/control',close)]
    outcomes=[c.result()['outcome'] for c in calls]
   assert outcomes[1]=='accepted' and outcomes[0] in ['accepted','rejected'];h.restart()
   v=h.request('/instances/'+iid+'/view',token=t['a'])['view'];assert record(v,'pieces')['count']==(1 if outcomes[0]=='accepted' else 0)
   assert h.request('/instances/'+iid+'/events',body('late','submit','pieces',dict(itemId='late',value=text('late'))),t['a'])['outcome']=='rejected'
   assert h.request('/instances/'+iid+'/events',submit,t['a'])['outcome']==('replayed' if outcomes[0]=='accepted' else 'rejected')
  f=Fixture(h,p,'deadline',controls={'pieces':control(PEOPLE,10,20)})
  f.submit('a','early',text('early'),at=9,want='rejected');f.submit('a','on-open',text('open'),at=10,eid='accepted-open')
  f.submit('a','at-close',text('late'),at=20,want='rejected');f.submit('a','on-open',text('open'),eid='accepted-open',want='replayed')
  t=h.setup(package('typed-sharing'),'claim-race');value=media(h,'claim-race',t,'a','audio',wav(21))
  assert h.request('/instances/claim-race/events',body('piece','submit','pieces',dict(itemId='piece',value=value)),t['a'])['outcome']=='accepted'
  assert h.request('/instances/claim-race/control',body('close','close','pieces',{}))['outcome']=='accepted'
  claims={a:body('claim-'+a,'claim','claim:0',{}) for a in 'bc'}
  with concurrent.futures.ThreadPoolExecutor(2) as ex:
   results=list(ex.map(lambda a:h.request('/instances/claim-race/events',claims[a],t[a])['outcome'],'bc'))
  assert sorted(results)==['accepted','rejected'];winner='bc'[results.index('accepted')];loser='bc'[results.index('rejected')]
  h.restart();assert h.request('/instances/claim-race/events',claims[winner],t[winner])['outcome']=='replayed'
  assert base64.b64decode(read(h,'claim-race',t,winner,value['ref'])['data'])==wav(21)
  assert read(h,'claim-race',t,loser,value['ref'])['outcome']=='unauthorized'
  assert h.request('/instances/claim-race/events',body('wrong-ack','advance','read:0',{}),t[loser])['outcome']=='rejected'
 finally:h.stop()
 print(kind+': quota/ID/close/reader concurrent races, private winner grants, exclusive deadlines, immutable retries and recovery pass',flush=True)

def generated_randomness_and_empty(kind,directory):
 """Use real host entropy; check saved properties without requiring identical streams."""
 h=Host(kind,directory/(kind+'-typed-generated.sqlite'),seed=None)
 try:
  p=package('typed-response-workshop');p['id']+='-random-probe'
  p['runbook']['steps'][1]['policy']='policy:seeded_nonself_source@1'
  p['requires']=sorted(set(p['requires'])-{'policy:next_nonself_item@1'}|{'policy:seeded_nonself_source@1','seeded_assignment@1'})
  t=h.setup(p,participants=list('abcd'));values={}
  for a in 'ab':
   for n in range(2):
    item=a+str(n);value=text(item) if n==0 else media(h,'test',t,a,'audio',wav(n+ord(a)))
    values[item]=(a,value)
    assert h.request('/instances/test/events',body(item,'submit','pieces',dict(itemId=item,value=value)),t[a])['outcome']=='accepted'
  with sqlite3.connect(h.db) as db:saved=json.loads(db.execute('SELECT state FROM instances WHERE id=?',('test',)).fetchone()[0])
  assert 0<saved['assignmentSeed']<=4294967295
  h.seed=42;h.restart() # A different process option cannot replace the saved instance seed.
  assert h.request('/instances/test/control',body('close','close','pieces',{}))['outcome']=='accepted'
  before=all_views(h,'test',t);assigned={a:record(before[a],'sources')['assignment'] for a in 'abcd'}
  assert set(assigned)==set('abcd')
  for a,candidate in assigned.items():
   author,value=values[candidate['ref']['itemId']];assert candidate['actor']==author!=a and candidate['value']==value
   if value['kind']=='audio':assert base64.b64decode(read(h,'test',t,a,value['ref'])['data'])==wav(1+ord(author))
  h.seed=99;h.restart();assert all_views(h,'test',t)==before
  # New vote chain: ordinary host randomness must select only tied/frozen candidates and persist.
  for case in ['tie','zero']:
   p=package('text-pool-vote');iid='random-'+case;t2=h.setup(p,iid)
   for a in 'ab':assert h.request('/instances/'+iid+'/events',body('entry-'+a,'submit','pieces',dict(itemId=a,value=text(a))),t2[a])['outcome']=='accepted'
   assert h.request('/instances/'+iid+'/control',body('pool-close','close','pieces',{}))['outcome']=='accepted'
   candidates=record(h.request('/instances/'+iid+'/view',token=t2['c'])['view'],'vote')['candidates']
   if case=='tie':
    for a,candidate in zip('ab',candidates):assert h.request('/instances/'+iid+'/events',body('vote-'+a,'submit','vote',dict(candidate=candidate['ref'])),t2[a])['outcome']=='accepted'
   assert h.request('/instances/'+iid+'/control',body('vote-close','close','vote',{}))['outcome']=='accepted'
   final=all_views(h,iid,t2);out=record(final['c'],'result')['output']
   assert out['selected'] in candidates and out['basis']==('random_tie' if case=='tie' else 'random_no_votes')
   h.restart();assert all_views(h,iid,t2)==final
   assert h.request('/instances/'+iid+'/control',body('vote-close','close','vote',{}))['outcome']=='replayed'
  # No reader exists for a solo author; no private item/media is published.
  p=package('typed-sharing');p['id']+='-solo';p['participants']={'min':1,'max':1}
  t3=h.setup(p,'solo',participants=['a']);value=media(h,'solo',t3,'a','audio',wav(17))
  assert h.request('/instances/solo/events',body('solo','submit','pieces',dict(itemId='solo',value=value)),t3['a'])['outcome']=='accepted'
  assert h.request('/instances/solo/control',body('close','close','pieces',{}))['outcome']=='accepted'
  solo=h.request('/instances/solo/view',token=t3['organizer'])['view']
  assert solo['phase']=='complete' and record(solo,'share')['candidate'] is None and value['ref'] not in json.dumps(solo)
  assert read(h,'solo',t3,'organizer',value['ref'])['outcome']=='unauthorized';h.restart()
  assert h.request('/instances/solo/view',token=t3['organizer'])['view']==solo
 finally:h.stop()
 print(kind+': generated seed, changed process seed, multi-item sampling, default outcome randomness and no-reader privacy survive restart',flush=True)

def unsupported(kind,directory):
 for token in NEW:
  chosen=package('typed-sharing' if token in NEW[:5] else 'typed-response-workshop' if token in NEW[10:] else 'text-pool-vote')
  if token=='reveal_ballots@3':chosen['runbook']['steps'].append(dict(id='ballot_reveal',op=token,source='vote'));chosen['requires'].append(token)
  h=Host(kind,directory/(kind+'-disabled-'+token.replace('@','-').replace(':','-')+'.sqlite'),disabled=token)
  try:
   assert token not in h.request('/support')['operations']+h.request('/support')['capabilities']
   result,_=create(h,chosen,'disabled',people=list('abcd') if chosen['participants']['min']==4 else PEOPLE)
   assert result['outcome']=='unsupported' and token in result['missing'],(kind,token,result)
   assert h.request('/instances/disabled/status')['outcome']=='not_found'
  finally:h.stop()
 print(kind+': every new consumer/pool/policy negotiates separately before state creation',flush=True)

def check(directory):
 proofs=[]
 for kind in ['python','node']:
  quotas(kind,directory);iteration(kind,directory);iteration(kind,directory,True);contest(kind,directory);proofs.append(workshop(kind,directory));races_deadlines(kind,directory);generated_randomness_and_empty(kind,directory);unsupported(kind,directory)
 assert proofs[0]==proofs[1]
 py=Host('python',directory/'transfer-from.sqlite');node=Host('node',directory/'transfer-to.sqlite')
 try:
  p,digest=proofs[0];assert py.request('/packages',dict(package=p))['digest']==digest
  exported=py.request('/packages/'+p['id']+'/'+p['version']);assert node.request('/packages',dict(package=exported['package']))['digest']==digest
 finally:py.stop();node.stop()
 print('Typed multi-source workshop transfers identical data/digest and matches exact engine views at every host event/restart; private unused material and pair history stay private',flush=True)

if __name__=='__main__':
 with tempfile.TemporaryDirectory(prefix='harmonomicon-023-pooling-') as path:check(Path(path))
