"""House rules for host-controlled typed contributions; host data is trusted input."""
import copy
OPS={'artifact_pool@1','assign_artifacts@1','artifact_response@1','reveal_artifact_responses@1'}
WINDOWS={'artifact_pool@1','artifact_response@1'}
MAX=9007199254740991
POLICIES={'policy:next_nonself_source@1','policy:seeded_nonself_source@1'}
def exact(x,keys):return type(x) is dict and set(x)==set(keys)
def text(x):return type(x) is str and bool(x) and all(not 0xd800<=ord(c)<=0xdfff for c in x)
def integer(x):return type(x) in [int,float] and not isinstance(x,bool) and x%1==0 and 0<=x<=MAX
def demand(x):
 if not x:raise ValueError('invalid_package')
def kinds(x):return type(x) is list and 1<=len(x)<=3 and all(k in ['text','image','audio'] for k in x) and len(set(x))==len(x)
def actors(x):return type(x) is list and len(x)<=100 and all(text(a) and a!='system' for a in x) and len(set(x))==len(x)
def validate(s,known,used,nested):
 demand(not nested);used.add('host_controls@1')
 op=s['op']
 if op=='artifact_pool@1':
  demand(exact(s,['id','op','prompt','kinds','visibility']) and text(s['prompt']) and kinds(s['kinds']) and s['visibility'] in ['private','group'])
 elif op=='assign_artifacts@1':
  demand(exact(s,['id','op','source','policy','recipients','cardinality','reuse','unmatched']) and known.get(s['source'],{}).get('op')=='artifact_pool@1')
  demand(s['policy'] in POLICIES and s['recipients'] in ['contributors','effective'] and s['cardinality']=='one' and s['reuse']=='allowed' and s['unmatched']=='skip');used.add(s['policy'])
  if s['policy']=='policy:seeded_nonself_source@1':used.add('seeded_assignment@1')
 elif op=='artifact_response@1':
  demand(exact(s,['id','op','source','prompt','kinds']) and known.get(s['source'],{}).get('op')=='assign_artifacts@1' and text(s['prompt']) and kinds(s['kinds']))
 else:demand(exact(s,['id','op','source']) and known.get(s['source'],{}).get('op')=='artifact_response@1')
 for k in s.get('kinds',[]):
  if k!='text':used.add(k+'_contributions@1')
 known[s['id']]=s

def valid_control(c):
 return exact(c,['actors','opensAt','closesAt']) and actors(c['actors']) and (c['opensAt'] is None or integer(c['opensAt'])) and (c['closesAt'] is None or integer(c['closesAt'])) and (c['opensAt'] is None or c['closesAt'] is None or c['closesAt']>c['opensAt'])
def safe_control(e,c):
 return valid_control(c) and all(t is None or t+e.timing_budget<=MAX for t in [c['opensAt'],c['closesAt']])
def initialize(e,inputs):
 if 'host_controls@1' not in e.package['requires']:
  demand(inputs is None or inputs=={});return
 if e.state.get('hostInputs') is not None:
  demand(inputs is None or e.state['hostInputs']==inputs);return
 supplied={} if inputs is None else inputs;demand(type(supplied) is dict)
 demand(all(k in e.definitions and e.definitions[k]['op'] in WINDOWS and safe_control(e,v) for k,v in supplied.items()))
 bound=list(dict.fromkeys(e.participants+[e.organizer]+[a for c in supplied.values() for a in c['actors']]));demand(len(bound)<=256)
 e.state['hostInputs']=copy.deepcopy(supplied);e.state['controls']=copy.deepcopy(supplied);e.state['hostActors']=bound

def bindings(e):return e.state.get('hostActors',list(dict.fromkeys(e.participants+[e.organizer])))
def control(e,f):
 if f['step']['id'] not in e.state['controls']:
  e.state['controls'][f['step']['id']]={'actors':e.participants[:],'opensAt':None,'closesAt':None}
 return e.state['controls'][f['step']['id']]
def opening(e,f):
 c=control(e,f);return e.state['openedAt'] if c['opensAt'] is None else c['opensAt']
def valid_value(e,actor,v,allowed):
 if type(v) is not dict or v.get('kind') not in allowed:return False
 if v['kind']=='text':return exact(v,['kind','text']) and text(v['text'])
 return exact(v,['kind','ref']) and text(v['ref']) and len(v['ref'])<=256 and callable(e.authorize_artifact) and e.authorize_artifact(actor,v['ref'],v['kind']) is True

def settle(e,f,now):
 s=f['step'];op=s['op'];r=e.record(f)
 if op in WINDOWS:
  c=control(e,f);r['effective']=copy.deepcopy(c)
  if op=='artifact_response@1':
   r['assignments']=copy.deepcopy(e.source(s['source'],f)['assignments'])
   if not r['assignments']:r['closed']=True;e.next(e.state['openedAt']);return 'advance'
  if c['closesAt'] is not None and now>=c['closesAt']:
   r['closed']=True;e.next(max(c['closesAt'],e.state['openedAt']));return 'advance'
  return 'wait'
 if op=='assign_artifacts@1':
  pool=e.source(s['source'],f);roster=pool['effective']['actors'];entries=[x for x in pool['entries'] if x['actor'] in roster]
  recipients=[a for a in roster if s['recipients']=='effective' or any(x['actor']==a for x in entries)];assignments=[];unmatched=[]
  for a in recipients:
   candidates=[x for x in entries if x['actor']!=a]
   if not candidates:unmatched.append(a);continue
   if s['policy']=='policy:next_nonself_source@1':chosen=min(candidates,key=lambda x:(roster.index(x['actor'])-roster.index(a))%len(roster))
   else:chosen=candidates[0] if len(candidates)==1 else candidates[e.random_index(len(candidates))]
   assignments.append({'actor':a,'sourceActor':chosen['actor'],'itemId':chosen['itemId'],'value':copy.deepcopy(chosen['value'])})
  r.update(recipients=recipients,assignments=assignments,unmatched=unmatched,closed=True)
 else:e.source(s['source'],f)['revealed']=True;r['closed']=True
 e.next(e.state['openedAt']);return 'advance'

def event(e,f,ev):
 s=f['step'];r=e.record(f);c=control(e,f);payload=ev['payload'];now=ev['at']
 if ev['actor']=='system' and ev['type']=='configure':
  if not safe_control(e,payload) or payload['closesAt'] is not None and payload['closesAt']<=now:return False
  bound=list(dict.fromkeys(bindings(e)+payload['actors']))
  if len(bound)>256:return False
  e.state['controls'][s['id']]=copy.deepcopy(payload);e.state['hostActors']=bound;r['effective']=copy.deepcopy(payload);return True
 if ev['actor']=='system' and ev['type']=='close' and payload=={}:
  r['closed']=True;e.next(now);return True
 if ev['type']!='submit' or ev['actor'] not in c['actors'] or now<opening(e,f) or any(x['actor']==ev['actor'] for x in r['entries']):return False
 if s['op']=='artifact_pool@1':
  if not exact(payload,['itemId','value']) or not text(payload['itemId']) or any(x['itemId']==payload['itemId'] for x in r['entries']) or not valid_value(e,ev['actor'],payload['value'],s['kinds']):return False
  r['entries'].append({'actor':ev['actor'],'itemId':payload['itemId'],'value':copy.deepcopy(payload['value'])});return True
 assigned=next((a for a in r['assignments'] if a['actor']==ev['actor']),None)
 if assigned is None or not exact(payload,['itemId','value']) or payload['itemId']!=assigned['itemId'] or not valid_value(e,ev['actor'],payload['value'],s['kinds']):return False
 r['entries'].append({'actor':ev['actor'],'source':{'actor':assigned['sourceActor'],'itemId':assigned['itemId'],'value':copy.deepcopy(assigned['value'])},'value':copy.deepcopy(payload['value'])});return True

def projection(e,r,item,actor):
 op=r['op']
 if op=='artifact_pool@1':
  item['count']=len(r['entries']);item['eligible']=actor in r['effective']['actors'];item['opensAt']=r['effective']['opensAt'];item['closesAt']=r['effective']['closesAt'];item['entries']=[copy.deepcopy(x) for x in r['entries'] if x['actor']==actor or e.find_step(r['step'])['visibility']=='group']
 elif op in ['assign_artifacts@1','artifact_response@1']:
  assigned=next((a for a in r['assignments'] if a['actor']==actor),None);item['assignment']=None if assigned is None else {'itemId':assigned['itemId'],'value':copy.deepcopy(assigned['value'])}
  if op=='assign_artifacts@1':item['eligible']=actor in r['recipients'];item['unmatched']=actor in r['unmatched']
  else:
   item['count']=len(r['entries']);item['eligible']=actor in r['effective']['actors'] and assigned is not None;item['opensAt']=r['effective']['opensAt'];item['closesAt']=r['effective']['closesAt'];item['entries']=[]
   for x in r['entries']:
    if r['revealed']:item['entries'].append(copy.deepcopy(x))
    elif x['actor']==actor:item['entries'].append({'actor':actor,'source':{'itemId':x['source']['itemId'],'value':copy.deepcopy(x['source']['value'])},'value':copy.deepcopy(x['value'])})
