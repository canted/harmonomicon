"""Authenticated durable evidence for ballots, outcomes and linked rounds."""
import copy
import concurrent.futures
import hashlib
import json
import tempfile
import time
from pathlib import Path
from run import Host, PEOPLE
from artifact_trial import upload, read, views, action, wav
from png_check import image
from runtime import run

ROOT=Path(__file__).resolve().parents[2]
def package(name):return json.loads((ROOT/'format/0.23/examples'/f'{name}.json').read_text())
def control(actors=PEOPLE,opening=0,closing=None):return dict(actors=actors,opensAt=opening,closesAt=closing)
def ev(id,actor,step,payload,at=0,type='submit'):return dict(eventId=id,actor=actor,step=step,payload=payload,at=at,type=type)
def ballot(id,actor,step,source,item,at=0):return ev(id,actor,step,{'candidate':{'source':source,'itemId':item}},at)
def piece(id,actor,step,item,text,at=0):return ev(id,actor,step,{'itemId':item,'value':{'kind':'text','text':text}},at)
def close(id,step,at=0):return ev(id,'system',step,{},at,'close')
def tick(at):return ev('tick-'+str(at),'system',None,{},at,'tick')
def record(view,sid):return next(r for r in view['records'] if r['step']==sid)

def execute(h,p,events,inputs=None,people=PEOPLE,iid='test',tie_choices=None):
 tokens=h.setup(p,iid,people,host_inputs=inputs)
 req=dict(package=p,participants=people,organizer='organizer',hostInputs=inputs,events=events)
 if tie_choices is not None:req['tieChoices']=tie_choices
 reference=run(req)
 for index,event in enumerate(events):
  h.clock(event['at']);outcome=action(h,event,tokens,iid)
  assert outcome==reference['outcomes'][index],(h.kind,index,outcome,reference['outcomes'][index])
  assert views(h,tokens,iid)==reference['views'][index],(h.kind,index)
  h.restart();assert views(h,tokens,iid)==reference['views'][index],(h.kind,'restart',index)
 return tokens,reference

def deterministic_traces(kind,directory):
 # New predefined poll keeps votes private and prohibits replacements.
 h=Host(kind,directory/(kind+'-new-poll.sqlite'))
 try:
  p=package('predefined-vote');events=[ballot('a','a','vote','vote','repair'),ballot('replace','a','vote','vote','garden'),ballot('b','b','vote','vote','repair'),ballot('invalid','c','vote','vote','missing'),tick(20),ballot('a','a','vote','vote','repair',20),ballot('late','c','vote','vote','garden',20)]
  tokens,ref=execute(h,p,events,{'vote':control(closing=20)})
  assert ref['outcomes']==['accepted','rejected','accepted','rejected','accepted','replayed','rejected']
  out=record(views(h,tokens)['c'],'poll_result')['output'];assert out['totalVotes']==2 and out['selected']['ref']['itemId']=='repair'
  assert record(views(h,tokens)['organizer'],'vote')['entries']==[]
 finally:h.stop()
 # Actual linked source identity through two rounds; same item ID is scoped.
 h=Host(kind,directory/(kind+'-linked.sqlite'),tie_choice=1)
 try:
  p=package('creative-continuation');inputs={s:control(closing=t) for s,t in [('continuations_one',10),('vote_one',20),('continuations_two',30),('vote_two',40)]}
  events=[piece('a','a','continuations_one','same','The rain answered.'),piece('b','b','continuations_one','other','A window answered.'),tick(10),ballot('va','a','vote_one','continuations_one','same',10),ballot('vb','b','vote_one','continuations_one','other',10),tick(20),piece('two-a','a','continuations_two','same','The window opened.',20),piece('two-b','b','continuations_two','other','The station listened.',20),piece('stale','c','continuations_one','late','Old round',20),tick(30),ballot('wrong-round','a','vote_two','continuations_one','same',30),ballot('two-va','a','vote_two','continuations_two','same',30),ballot('two-vb','b','vote_two','continuations_two','same',30),tick(40)]
  tokens,ref=execute(h,p,events,inputs,tie_choices=[1])
  assert ref['outcomes']==['accepted']*8+['rejected','accepted','rejected']+['accepted']*3
  inp=record(views(h,tokens)['c'],'continuations_two')['input'];assert inp['predecessorRound']=='verse_one' and inp['candidate']['ref']=={'source':'continuations_one','itemId':'other'}
  assert record(views(h,tokens)['c'],'two_result')['output']['selected']['round']=='verse_two'
  assert record(views(h,tokens)['organizer'],'vote_one')['entries']==[]
 finally:h.stop()
 print(kind+': predefined and linked-round traces match exact expectations with every-event restart',flush=True)

def media_candidate_grants(kind,directory):
 h=Host(kind,directory/(kind+'-vote-media.sqlite'))
 try:
  p=package('contribution-contest');p['runbook']['steps'].append(dict(id='after',op='artifact_pool@2',prompt='Respond to the selected media.',kinds=['text'],visibility='private',round='response',input={'result':'contest_choice'}));inputs={'entries':control(closing=10),'vote':control(closing=20)};tokens=h.setup(p,host_inputs=inputs)
  blobs={'a':image(),'b':wav()};refs={}
  for a,blob in blobs.items():refs[a]=upload(h,'test',tokens[a],blob,'image' if a=='a' else 'audio')['ref']
  for a in 'ab':
   value={'kind':'image' if a=='a' else 'audio','ref':refs[a]};assert action(h,ev('submit-'+a,a,'entries',{'itemId':a,'value':value}),tokens)=='accepted'
  assert read(h,tokens['c'],refs['a'])=={'outcome':'unauthorized'}
  assert read(h,tokens['organizer'],refs['b'])=={'outcome':'unauthorized'}
  foreign=ev('foreign','c','entries',{'itemId':'foreign','value':{'kind':'image','ref':refs['a']}});assert action(h,foreign,tokens)=='rejected'
  h.clock(10)
  for viewer in ['a','b','c','organizer']:
   for ref in refs.values():assert read(h,tokens[viewer],ref)['ref']==ref
  assert action(h,ballot('v','a','vote','entries','b',10),tokens)=='accepted'
  assert action(h,ballot('replace','a','vote','entries','a',10),tokens)=='accepted'
  # Replaying the original accepted ballot cannot undo the newer current vote.
  assert action(h,ballot('v','a','vote','entries','b',10),tokens)=='replayed'
  h.clock(20);h.restart();v=views(h,tokens)
  out=record(v['c'],'contest_result')['output'];assert out['totalVotes']==1 and out['selected']['ref']['itemId']=='a'
  assert record(v['organizer'],'vote')['entries']==[] and record(v['b'],'vote')['entries']==[]
  assert record(v['a'],'vote')['entries']==[{'actor':'a','candidate':{'source':'entries','itemId':'a'}}]
  assert out['selected']['actor']=='a' and out['selected']['value']['ref']==refs['a']
  assert record(v['c'],'after')['input']['candidate']==out['selected'] and record(v['c'],'after')['input']['predecessorRound']=='contest'
  assert read(h,tokens['c'],refs['a'])['ref']==refs['a']
  # Media remains publicly viewable through candidates/results without ownership transfer.
  assert action(h,ev('forged','c','entries',{'itemId':'stale','value':{'kind':'image','ref':refs['a']}},20),tokens)=='rejected'
 finally:h.stop()
 print(kind+': actual PNG/audio candidate publication, ownership and ballot privacy survive restart',flush=True)

def races(kind,directory):
 for changes in ['allowed','forbidden']:
  h=Host(kind,directory/(kind+'-'+changes+'-vote-race.sqlite'))
  try:
   p=package('predefined-vote');p['runbook']['steps'][0]['changes']=changes;tokens=h.setup(p,host_inputs={'vote':control(closing=20)})
   submitted=[ballot('r-'+str(i),'a','vote','vote',item) for i,item in enumerate(['repair','garden'])]
   with concurrent.futures.ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(lambda e:action(h,e,tokens),submitted))
   assert sorted(outcomes)==(['accepted']*2 if changes=='allowed' else ['accepted','rejected'])
   h.restart();current=record(views(h,tokens)['a'],'vote')['entries'];assert len(current)==1
   for e,out in zip(submitted,outcomes):
    if out=='accepted':assert action(h,e,tokens)=='replayed'
   h.clock(20);out=record(views(h,tokens)['c'],'poll_result')['output'];assert out['totalVotes']==1 and sum(r['count'] for r in out['counts'])==1
   assert out['selected']['ref']==current[0]['candidate']
   assert action(h,ballot('after','a','vote','vote','share',20),tokens)=='rejected'
  finally:h.stop()
 # Concurrent new vote and trusted close: exact serialized result, never double count.
 h=Host(kind,directory/(kind+'-close-vote-race.sqlite'))
 try:
  p=package('predefined-vote');tokens=h.setup(p)
  e=ballot('race','a','vote','vote','garden');c=close('closing','vote')
  with concurrent.futures.ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(lambda event:action(h,event,tokens),[e,c]))
  assert outcomes[1]=='accepted' and outcomes[0] in ['accepted','rejected']
  out=record(views(h,tokens)['c'],'poll_result')['output'];assert out['totalVotes']==int(outcomes[0]=='accepted')
  h.restart();assert record(views(h,tokens)['c'],'poll_result')['output']==out
 finally:h.stop()
 # Two competing contribution IDs produce one immutable candidate.
 h=Host(kind,directory/(kind+'-candidate-race.sqlite'))
 try:
  p=package('contribution-contest');tokens=h.setup(p)
  events=[piece('x','a','entries','same','First'),piece('y','b','entries','same','Second')]
  with concurrent.futures.ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(lambda e:action(h,e,tokens),events))
  assert sorted(outcomes)==['accepted','rejected'];assert action(h,close('end','entries'),tokens)=='accepted'
  candidates=record(views(h,tokens)['c'],'vote')['candidates'];assert len(candidates)==1 and candidates[0]['actor']==events[outcomes.index('accepted')]['actor']
 finally:h.stop()
 print(kind+': current-vote/candidate/close races, retries and exclusive deadlines pass',flush=True)

def disclosure_and_withdrawal(kind,directory):
 for ballots in ['private','group']:
  h=Host(kind,directory/(kind+'-'+ballots+'-disclosure.sqlite'))
  try:
   p=package('predefined-vote');p['runbook']['steps'][0].update(changes='allowed',ballots=ballots)
   p['runbook']['steps'][3]['source']='poll_totals'
   p['runbook']['steps'].append(dict(id='release',op='reveal_ballots@1',source='vote'));p['requires'].append('reveal_ballots@1')
   tokens=h.setup(p)
   assert action(h,ballot('one','a','vote','vote','repair'),tokens)=='accepted'
   assert record(views(h,tokens)['b'],'vote')['entries']==([] if ballots=='private' else [{'actor':'a','candidate':{'source':'vote','itemId':'repair'}}])
   assert action(h,ballot('change','a','vote','vote','garden'),tokens)=='accepted'
   assert action(h,close('close','vote'),tokens)=='accepted';h.restart()
   v=views(h,tokens)['b'];assert record(v,'vote')['entries']==[{'actor':'a','candidate':{'source':'vote','itemId':'garden'}}]
   out=record(v,'poll_result')['output'];assert out['totalVotes']==1 and 'status' not in out and [x['count'] for x in out['counts']]==[0,1,0]
  finally:h.stop()
 h=Host(kind,directory/(kind+'-frozen-eligibility.sqlite'))
 try:
  p=package('contribution-contest');tokens=h.setup(p)
  for actor in 'ab':assert action(h,piece(actor,actor,'entries',actor,actor),tokens)=='accepted'
  assert action(h,ev('withdraw-source','system','entries',control(['a']),type='configure'),tokens)=='accepted'
  assert action(h,close('source-close','entries'),tokens)=='accepted'
  assert [x['ref']['itemId'] for x in record(views(h,tokens)['c'],'vote')['candidates']]==['a']
  assert action(h,ballot('ineligible-candidate','b','vote','entries','b'),tokens)=='rejected'
  for actor in 'ab':assert action(h,ballot('v-'+actor,actor,'vote','entries','a'),tokens)=='accepted'
  assert action(h,ev('withdraw-voter','system','vote',control(['a']),type='configure'),tokens)=='accepted'
  assert action(h,ballot('withdrawn-change','b','vote','entries','a'),tokens)=='rejected'
  assert action(h,close('vote-close','vote'),tokens)=='accepted';h.restart()
  v=views(h,tokens);assert record(v['c'],'contest_result')['output']['totalVotes']==1
  assert record(v['b'],'entries')['entries'][0]['itemId']=='b' and record(v['b'],'vote')['entries'][0]['actor']=='b'
 finally:h.stop()
 print(kind+': aggregate-only presentation, explicit current-ballot reveal and frozen/final eligibility pass',flush=True)

def default_random_and_empty(kind,directory):
 h=Host(kind,directory/(kind+'-default-random.sqlite'))
 try:
  p=package('predefined-vote');p['runbook']['steps'][2]['ties']='random';p['requires'].append('policy:random_tie@1');tokens=h.setup(p,host_inputs={'vote':control(closing=10)})
  for a,item in [('a','repair'),('b','garden')]:assert action(h,ballot(a,a,'vote','vote',item),tokens)=='accepted'
  # Worker settles without reading; default host randomness is intentionally unseeded.
  h.clock(10)
  for _ in range(40):
   if h.request('/instances/test/status')['phase']=='complete':break
   time.sleep(.025)
  else:raise AssertionError('worker did not settle random result')
  initial=record(views(h,tokens)['c'],'poll_result')['output'];assert initial['selected']['ref']['itemId'] in ['repair','garden'] and len(initial['tied'])==2
  for _ in range(3):h.restart();assert record(views(h,tokens)['c'],'poll_result')['output']==initial
  assert action(h,ballot('a','a','vote','vote','repair',10),tokens)=='replayed'
  assert record(views(h,tokens)['organizer'],'vote')['entries']==[]
 finally:h.stop()
 for mode in ['no_votes','no_candidates','tie']:
  h=Host(kind,directory/(kind+'-'+mode+'-blocked.sqlite'))
  try:
   p=package('creative-continuation');p['runbook']['steps'][3]['ties']='unresolved';p['runbook']['steps'][8]['ties']='unresolved';p['requires'].remove('policy:random_tie@1')
   tokens=h.setup(p)
   if mode!='no_candidates':
    for a in 'ab':assert action(h,piece(a,a,'continuations_one',a,a),tokens)=='accepted'
   assert action(h,close('source','continuations_one'),tokens)=='accepted'
   if mode=='tie':
    for a in 'ab':assert action(h,ballot('v'+a,a,'vote_one','continuations_one',a),tokens)=='accepted'
   if mode!='no_candidates':assert action(h,close('vote-close','vote_one'),tokens)=='accepted'
   h.restart();v=views(h,tokens)['c'];inp=record(v,'continuations_two')['input'];assert inp['status']==mode and inp['predecessorRound']=='verse_one'
   assert record(v,'continuations_two')['blocked'] and v['phase']=='complete'
   assert record(v,'two_result')['output']['status']=='no_candidates'
  finally:h.stop()
 print(kind+': stable default random outcome and blocked empty/unresolved continuations pass',flush=True)

def empty_workshop(kind,directory):
 for mode in ['empty','tie']:
  h=Host(kind,directory/(kind+'-'+mode+'-workshop.sqlite'))
  try:
   p=package('proposal-workshop');people=list('abcd');tokens=h.setup(p,participants=people)
   if mode=='tie':
    for actor in 'ab':assert action(h,piece(actor,actor,'proposals',actor,actor),tokens)=='accepted'
   assert action(h,close('end-source','proposals'),tokens)=='accepted'
   if mode=='tie':
    for actor in 'ab':assert action(h,ballot('v-'+actor,actor,'vote','proposals',actor),tokens)=='accepted'
    assert action(h,close('end-vote','vote'),tokens)=='accepted'
   h.restart();v=views(h,tokens)['a'];assert record(v,'plans')['blocked'] and v['step']=='exercise'
   assert record(v,'plans')['input']['predecessorRound']=='proposing'
   assert 'If planning was blocked because no proposal was selected' in v['prompt']
   assert action(h,ev('reflection','a','exercise',{'text':'We need clearer criteria.'}),tokens)=='accepted'
   assert record(views(h,tokens)['b'],'exercise')['entries']==[{'actor':'a','value':{'text':'We need clearer criteria.'}}]
   assert record(views(h,tokens)['c'],'exercise')['entries']==[]
   h.clock(60000);assert views(h,tokens)['a']['phase']=='complete'
  finally:h.stop()
 print(kind+': empty/tied proposal path explicitly blocks planning and continues useful private-pair reflection',flush=True)

def negotiation(kind,directory):
 p=package('creative-continuation');p['runbook']['steps'].append(dict(id='reveal',op='reveal_ballots@1',source='vote_one'));p['requires'].append('reveal_ballots@1')
 for token in ['artifact_pool@2','vote@1','tally@2','select@1','present@1','reveal_ballots@1','policy:most_votes@1','policy:random_tie@1']:
  h=Host(kind,directory/(kind+'-unsupported-'+token.split('@')[0].replace(':','-')+'.sqlite'),disabled=token)
  try:
   assert token not in h.request('/support')['operations']+h.request('/support')['capabilities']
   assert h.request('/packages',{'package':p})['outcome']=='imported'
   req=dict(id='blocked',packageId=p['id'],version=p['version'],participants=PEOPLE,organizer='organizer')
   assert h.request('/instances',req)=={'outcome':'unsupported','missing':[token]}
   assert h.request('/instances/blocked/status')=={'outcome':'not_found'}
  finally:h.stop()
 print(kind+': operation/policy negotiation rejects before creating state',flush=True)

def held_out_transfer(directory):
 p=package('proposal-workshop');people=list('abcd');inputs={'proposals':control(people,0,10),'vote':control(people,10,20),'plans':control(people,20,30)}
 events=[piece('proposal-'+a,a,'proposals',a,'Proposal '+a) for a in 'ab']+[tick(10)]+[ballot('vote-'+a,a,'vote','proposals','b',10) for a in 'abc']+[tick(20)]+[piece('plan-'+a,a,'plans',a,'First step '+a,20) for a in 'abcd']+[tick(30)]+[ev('exercise-'+a,a,'exercise',{'text':'Experiment '+a},30) for a in 'ac']+[tick(60030)]
 snapshots=[];digest=None
 for kind in ['python','node']:
  h=Host(kind,directory/(kind+'-new-heldout.sqlite'))
  try:
   imported=h.request('/packages',{'package':p});export=h.request('/packages/'+p['id']+'/'+p['version'])
   assert export['package']==p and imported['digest']==export['digest']
   if digest is None:digest=export['digest']
   else:assert digest==export['digest']
   tokens,reference=execute(h,export['package'],events,inputs,people)
   v=views(h,tokens);assert record(v['a'],'plans')['input']['candidate']['ref']=={'source':'proposals','itemId':'b'}
   assert record(v['b'],'exercise')['entries']==[{'actor':'a','value':{'text':'Experiment a'}}]
   assert record(v['d'],'exercise')['entries']==[{'actor':'c','value':{'text':'Experiment c'}}]
   assert record(v['organizer'],'exercise')['entries']==[] and record(v['organizer'],'vote')['entries']==[]
   snapshots.append(v)
  finally:h.stop()
 assert snapshots[0]==snapshots[1]
 print('Held-out proposal selection feeds shared planning and retained private-pair exercise through identical package transfer',flush=True)

def check(directory):
 for kind in ['python','node']:
  deterministic_traces(kind,directory);media_candidate_grants(kind,directory);races(kind,directory);disclosure_and_withdrawal(kind,directory);default_random_and_empty(kind,directory);empty_workshop(kind,directory);negotiation(kind,directory)
 held_out_transfer(directory)

if __name__=='__main__':
 with tempfile.TemporaryDirectory(prefix='harmonomicon-021-voting-') as path:check(Path(path))
