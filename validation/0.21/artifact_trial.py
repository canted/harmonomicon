"""Authenticated typed-source witnesses: authority, grants, controls and recovery."""
import ast,base64,copy,concurrent.futures,hashlib,json,sqlite3,struct,subprocess,time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'format/0.21'))
from artifact_check import cases,package,control,txt
from runtime import run
from png_check import image
HERE=Path(__file__).resolve().parent

def wav(n=1,channels=1,rate=8000,samples=1):
 body=struct.pack('<h',n)*channels*samples;align=channels*2
 return struct.pack('<4sI4s4sIHHIIHH4sI',b'RIFF',len(body)+36,b'WAVE',b'fmt ',16,1,channels,rate,rate*align,align,16,b'data',len(body))+body

def upload(h,iid,token,blob,kind):return h.request(f'/instances/{iid}/media',dict(mediaType='image/png' if kind=='image' else 'audio/wav',data=base64.b64encode(blob).decode()),token)
def read(h,token,ref,iid='test'):return h.request(f'/instances/{iid}/media/{ref}',token=token)
def action(h,e,tokens,iid='test'):
 if e['type']=='tick':return 'accepted'
 body={k:e[k] for k in ['eventId','type','step','payload']}
 return h.request(f'/instances/{iid}/'+('control' if e['actor']=='system' else 'events'),body,tokens.get(e['actor'],'local-test-admin'))['outcome']
def views(h,tokens,iid='test'):return {a:h.request(f'/instances/{iid}/view',token=t)['view'] for a,t in tokens.items()}
def audio_check():
 fixtures=[('mono',wav(),True),('stereo',wav(channels=2,rate=48000),True),('max-bytes',wav(samples=(524288-44)//2),True),('oversize',wav(samples=(524288-44)//2+1),False),('empty',wav(samples=0),False),('low-rate',wav(rate=7999),False),('high-rate',wav(rate=48001),False),('three-channels',wav(channels=3),False),('truncated',wav()[:-1],False),('trailing',wav()+b'00',False)]
 for off in [0,8,12,36]:
  for pos in range(4):
   b=bytearray(wav());b[off+pos]|=128;fixtures.append((f'raw-name-{off}-{pos}',bytes(b),False))
 for off in [16,20,28,32,34,40]:
  b=bytearray(wav());b[off]^=1;fixtures.append((f'header-{off}',bytes(b),False))
 tree=ast.parse((HERE/'python_host.py').read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='valid_wav');ns={'struct':struct};exec(compile(ast.Module(body=[f],type_ignores=[]),'wav-validator','exec'),ns)
 source=(HERE/'node_host.mjs').read_text();source=source[source.index('function validWav'):source.index('function route(')]
 js=source+"\nconsole.log(JSON.stringify(JSON.parse(require('fs').readFileSync(0,'utf8')).map(x=>validWav(Buffer.from(x,'base64')))));"
 expected=[v for _,_,v in fixtures];assert [ns['valid_wav'](b) for _,b,_ in fixtures]==expected
 got=json.loads(subprocess.check_output(['node','-e',js],input=json.dumps([base64.b64encode(b).decode() for _,b,_ in fixtures]),text=True));assert got==expected
 print(f'{len(fixtures)} actual-validator PCM WAV profile fixtures agree')
 return fixtures

def trace(kind,directory,Host,req,expected):
 h=Host(kind,directory/(kind+'-artifact-'+req['id']+'.sqlite'),seed=req.get('seed',1))
 try:
  tokens=h.setup(req['package'],participants=req['participants'],organizer=req['organizer'],host_inputs=req.get('hostInputs'));mapped=copy.deepcopy(req);mapping={}
  for i,m in enumerate(req.get('trustedMedia',[])):
   blob=image(raw=bytes([0,i+1,0,0])) if m['kind']=='image' else wav(i+1)
   if m['ready']:
    receipt=upload(h,'test',tokens[m['actor']],blob,m['kind']);assert receipt['outcome']=='ready',receipt;ref=receipt['ref']
   else:
    ref='pending-ref'
    with sqlite3.connect(h.db) as db:db.execute('INSERT INTO media VALUES(?,?,?,?,?,?,?)',('test',m['actor'],ref,m['kind'],0,'audio/wav',blob))
   mapping[m['ref']]=ref
  def replace(x):
   if isinstance(x,dict):return {k:(mapping[v] if k=='ref' and v in mapping else replace(v)) for k,v in x.items()}
   if isinstance(x,list):return [replace(v) for v in x]
   return x
  export=h.request('/packages/'+req['package']['id']+'/'+req['package']['version']);assert export['package']==req['package'] and h.request('/packages',{'package':export['package']})['digest']==export['digest']
  mapped=replace(mapped);reference=run(mapped);assert reference['outcomes']==expected
  for i,e in enumerate(mapped['events']):
   h.clock(e['at']);outcome=action(h,e,tokens);assert outcome==expected[i],(kind,req['id'],i,outcome)
   for actor in reference['views'][i]:
    if actor not in tokens:
     tokens[actor]='host-bound-'+actor;assert h.request('/instances/test/bindings',dict(actor=actor,token=tokens[actor]))=={'outcome':'bound'}
   assert views(h,tokens)==reference['views'][i],(kind,req['id'],i)
   if req['id']=='multi-day-image-audio-chorus':
    if i==3:assert read(h,tokens['viewer'],mapping['image:a'])=={'outcome':'unauthorized'}
    if i==4:
     assert read(h,tokens['a'],mapping['image:d'])['ref']==mapping['image:d'];assert read(h,tokens['viewer'],mapping['image:d'])=={'outcome':'unauthorized'}
    if i==10:assert read(h,tokens['viewer'],mapping['audio:a'])=={'outcome':'unauthorized'}
    if i==12:
     assert read(h,tokens['viewer'],mapping['audio:a'])['ref']==mapping['audio:a'];assert read(h,tokens['viewer'],mapping['image:b'])['ref']==mapping['image:b'];assert read(h,tokens['viewer'],mapping['image:a'])=={'outcome':'unauthorized'}
   h.restart();assert views(h,tokens)==reference['views'][i],(kind,req['id'],'restart',i)
  return views(h,tokens)
 finally:h.stop()

def probes(kind,directory,Host):
 h=Host(kind,directory/(kind+'-artifact-probes.sqlite'),seed=1)
 try:
  p=package('daily-music-journal');tokens=h.setup(p,participants=['solo','observer'],organizer='solo',host_inputs={'entry':control(['solo'],0,200000000)})
  assert h.request('/instances/test/control',dict(eventId='forge',type='close',step='entry',payload={}),tokens['solo'])=={'outcome':'unauthorized'}
  for label,b,valid in audio_check():assert upload(h,'test',tokens['solo'],b,'audio')['outcome']==('ready' if valid else 'invalid_media'),(kind,label)
  receipt=upload(h,'test',tokens['solo'],wav(),'audio');ref=receipt['ref'];e=dict(eventId='retry',type='submit',step='entry',payload={'itemId':'one','value':{'kind':'audio','ref':'missing'}})
  assert h.request('/instances/test/events',e,tokens['solo'])['outcome']=='rejected';e['payload']['value']['ref']=ref
  with concurrent.futures.ThreadPoolExecutor(2) as pool:
   es=[dict(e,eventId='winner-'+str(i)) for i in range(2)];out=list(pool.map(lambda e:h.request('/instances/test/events',e,tokens['solo'])['outcome'],es))
  assert sorted(out)==['accepted','rejected'];winner=es[out.index('accepted')];h.restart();assert h.request('/instances/test/events',winner,tokens['solo'])['outcome']=='replayed';assert read(h,tokens['observer'],ref)=={'outcome':'unauthorized'}
  cfg=dict(eventId='extend',type='configure',step='entry',payload=control(['solo'],100,300000000));assert h.request('/instances/test/control',cfg)['outcome']=='accepted'
  before=views(h,tokens);assert before['solo']['records'][0]['entries'][0]['value']['ref']==ref
  h.clock(300000000)
  end=time.monotonic()+3
  while h.request('/instances/test/status')['phase']!='complete':
   assert time.monotonic()<end;time.sleep(.02)
  assert h.request('/instances/test/control',dict(cfg,eventId='reopen'))['outcome']=='rejected';assert h.request('/instances/test/control',cfg)['outcome']=='replayed';h.restart();assert h.request('/instances/test/events',winner,tokens['solo'])['outcome']=='replayed'
  assert read(h,tokens['observer'],ref)=={'outcome':'unauthorized'}
  # A different instance cannot attest ownership of this receipt.
  t=h.setup(p,'foreign',participants=['solo'],organizer='solo');assert h.request('/instances/foreign/events',winner,t['solo'])['outcome']=='rejected';assert read(h,t['solo'],ref,'foreign')=={'outcome':'unauthorized'}
  # Host resolves daily local-calendar dates; the language simply uses each instance's dates.
  for n,(opening,closing) in enumerate([(300000000,382800000),(382800000,472800000)]):
   iid='day-'+str(n);t=h.setup(p,iid,participants=['solo'],organizer='solo',host_inputs={'entry':control(['solo'],opening,closing)});assert h.request(f'/instances/{iid}/view',token=t['solo'])['view']['records'][0]['closesAt']==closing
  # Open discussion is host-owned and may continue after closing the primary-post phase.
  fb=package('feedback-round');t=h.setup(fb,'feedback',participants=['maker','reviewer','follower'],organizer='maker',host_inputs={'posts':control(['maker'],None,None)})
  post=dict(eventId='post',type='submit',step='posts',payload={'itemId':'post','value':txt('Primary')});assert h.request('/instances/feedback/events',post,t['maker'])['outcome']=='accepted'
  assert h.request('/instances/feedback/view',token=t['follower'])['view']['records'][0]['entries'][0]['value']==txt('Primary')
  assert h.request('/instances/feedback/control',dict(eventId='close',type='close',step='posts',payload={}))['outcome']=='accepted'
  with sqlite3.connect(h.db) as db:
   old=db.execute("SELECT state FROM instances WHERE id='feedback'").fetchone()[0];db.execute('CREATE TABLE app_replies(author TEXT,primary_id TEXT,text TEXT)');db.execute('INSERT INTO app_replies VALUES(?,?,?)',('reviewer','post','Open reply after closing'));assert db.execute("SELECT state FROM instances WHERE id='feedback'").fetchone()[0]==old
  # Typed linked responses retain assignment and serialize per-actor acceptance.
  ch=package('simplified-chorus');t=h.setup(ch,'linked-race',participants=list('abc'),organizer='a')
  images={}
  for i,a in enumerate('abc'):
   images[a]=upload(h,'linked-race',t[a],image(raw=bytes([0,i+1,0,0])),'image')['ref']
  bodies=[dict(eventId='pool-'+a,type='submit',step='covers',payload={'itemId':'same','value':{'kind':'image','ref':images[a]}}) for a in 'ab']
  with concurrent.futures.ThreadPoolExecutor(2) as pool:out=list(pool.map(lambda pair:h.request('/instances/linked-race/events',pair[1],t[pair[0]])['outcome'],zip('ab',bodies)))
  assert sorted(out)==['accepted','rejected']
  loser='ab'[out.index('rejected')];body=dict(bodies[out.index('rejected')]);body['eventId']='pool-second';body['payload']=dict(body['payload'],itemId='second');assert h.request('/instances/linked-race/events',body,t[loser])['outcome']=='accepted'
  assert h.request('/instances/linked-race/control',dict(eventId='freeze',type='close',step='covers',payload={}))['outcome']=='accepted'
  assigned=h.request('/instances/linked-race/view',token=t['a'])['view']['records'][1]['assignment'];assert assigned['value']['ref']==images['b']
  replies=[dict(eventId='reply-'+str(i),type='submit',step='response',payload={'itemId':assigned['itemId'],'value':txt(str(i))}) for i in range(2)]
  with concurrent.futures.ThreadPoolExecutor(2) as pool:out=list(pool.map(lambda e:h.request('/instances/linked-race/events',e,t['a'])['outcome'],replies))
  assert sorted(out)==['accepted','rejected'];winner_reply=replies[out.index('accepted')];h.restart();assert h.request('/instances/linked-race/events',winner_reply,t['a'])['outcome']=='replayed'
  assert h.request('/instances/linked-race/view',token=t['a'])['view']['records'][1]['assignment']==assigned
  assert h.request('/instances/linked-race/control',dict(eventId='finish',type='close',step='response',payload={}))['outcome']=='accepted'
  # Close versus submit is serialized; a closed window cannot accept a late contribution.
  t=h.setup(p,'race',participants=['solo'],organizer='solo');submit=dict(eventId='submit',type='submit',step='entry',payload={'itemId':'one','value':txt('Race')});close=dict(eventId='close',type='close',step='entry',payload={})
  with concurrent.futures.ThreadPoolExecutor(2) as pool:
   futures=[pool.submit(h.request,'/instances/race/events',submit,t['solo']),pool.submit(h.request,'/instances/race/control',close)];out=[f.result()['outcome'] for f in futures]
  assert out[1]=='accepted' and out[0] in ['accepted','rejected'];h.restart();v=h.request('/instances/race/view',token=t['solo'])['view'];assert v['phase']=='complete' and v['records'][0]['count']==(out[0]=='accepted')
  assert h.request('/instances/race/control',close)['outcome']=='replayed'
 finally:h.stop()
 for disabled in ['host_controls@1','audio_contributions@1','artifact_pool@1']:
  h=Host(kind,directory/(kind+'-missing-'+disabled.replace('@','')+'.sqlite'),disabled)
  try:
   p=package('daily-music-journal');assert h.request('/packages',{'package':p})['outcome']=='imported';response=h.request('/instances',dict(id='no',packageId=p['id'],version=p['version'],participants=['solo'],organizer='solo'));assert response=={'outcome':'unsupported','missing':[disabled]};assert h.request('/instances/no/status')=={'outcome':'not_found'}
   with sqlite3.connect(h.db) as db:assert db.execute('SELECT count(*) FROM instances').fetchone()[0]==db.execute('SELECT count(*) FROM media').fetchone()[0]==0
  finally:h.stop()
 print(kind+': typed authority/grants, partial retry, races, controls, long-deadline worker, solo/daily/public-host-discussion and unsupported/no-state pass',flush=True)

def transfer(directory,Host):
 # A newly authored typed exchange followed by retained pair-private reflection.
 p=package('simplified-chorus');tail=package('idea-response-and-pairs')
 p['id']='harmonomicon.typed-response-pairs-transfer';p['runbook']['steps']+=tail['runbook']['steps'][-2:]
 for cap in ['partition@1','policy:roster_chunks@1','collect_group@1']:
  if cap not in p['requires']:p['requires'].append(cap)
 blobs={a:image(raw=bytes([0,i+1,0,0])) for i,a in enumerate('abcd')};refs={a:'sha256:'+hashlib.sha256(b).hexdigest() for a,b in blobs.items()}
 inputs={'covers':control(list('abcd'),0,10),'response':control(list('abcd'),10,20)}
 events=[dict(eventId='cover-'+a,actor=a,at=0,type='submit',step='covers',payload={'itemId':a,'value':{'kind':'image','ref':refs[a]}}) for a in 'abcd']
 tick=lambda at:dict(eventId='tick-'+str(at),actor='system',at=at,type='tick',step=None,payload={})
 events.append(tick(10));base=dict(package=p,participants=list('abcd'),organizer='a',seed=1,hostInputs=inputs,trustedMedia=[dict(actor=a,ref=r,kind='image',ready=True) for a,r in refs.items()])
 preview=run(dict(base,events=events));assigned={a:preview['views'][-1][a]['records'][1]['assignment']['itemId'] for a in 'abcd'}
 assert assigned['a']=='d' and assigned['d']=='b' and all(a!=id for a,id in assigned.items())
 for a in 'abcd':events.append(dict(eventId='reply-'+a,actor=a,at=11,type='submit',step='response',payload={'itemId':assigned[a],'value':txt('Response '+a)}))
 events.append(tick(20))
 for a in 'ac':events.append(dict(eventId='reflect-'+a,actor=a,at=21,type='submit',step='reflection',payload={'text':'Private '+a}))
 events.append(tick(30));reference=run(dict(base,events=events));assert reference['outcomes']==['accepted']*len(events)
 hosts=[];snapshots=[]
 try:
  for kind in ['python','node']:
   h=Host(kind,directory/(kind+'-typed-transfer.sqlite'),seed=1);hosts.append(h)
   imported=h.request('/packages',{'package':p});export=h.request('/packages/'+p['id']+'/'+p['version']);assert export['package']==p and export['digest']==imported['digest']
   if kind=='python':exported=export
   else:assert export==exported
   tokens=h.setup(export['package'],participants=list('abcd'),organizer='a',host_inputs=inputs)
   for a,b in blobs.items():assert upload(h,'test',tokens[a],b,'image')['ref']==refs[a]
   for i,e in enumerate(events):
    h.clock(e['at']);assert action(h,e,tokens)=='accepted';assert views(h,tokens)==reference['views'][i]
    if i in [4,9,11]:h.restart();assert views(h,tokens)==reference['views'][i]
   v=views(h,tokens);assert v['b']['records'][-1]['entries']==[{'actor':'a','value':{'text':'Private a'}}] and v['d']['records'][-1]['entries']==[{'actor':'c','value':{'text':'Private c'}}];snapshots.append(v)
  assert snapshots[0]==snapshots[1]
 finally:
  for h in hosts:h.stop()
 print('Typed image exchange transfers by identical digest and composes into retained private-pair reflection, with durable privacy and restart')

def check(directory,Host):
 audio_check();results={}
 for kind in ['python','node']:
  results[kind]=[trace(kind,directory,Host,req,expected) for req,expected in cases()];probes(kind,directory,Host)
 assert results['python']==results['node'];transfer(directory,Host);print('All six typed witnesses agree through actual authenticated durable hosts, every-event restart and identical transferred package bytes')
if __name__=='__main__':
 import tempfile
 from run import Host
 with tempfile.TemporaryDirectory(prefix='harmonomicon-020-artifacts-') as d:check(Path(d),Host)
