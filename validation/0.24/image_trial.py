"""Actual PNG bytes, trusted host authorization, partial retries and durable privacy."""
import base64,concurrent.futures,copy,hashlib,json,sqlite3,struct,time,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def package(n):return json.loads((ROOT/f'format/0.24/examples/{n}.json').read_text())
def png(color=1):
 def chunk(kind,body):return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(bytes([0,color,0,0])))+chunk(b'IEND',b'')
def upload(h,iid,token,blob):return h.request(f'/instances/{iid}/media',{'mediaType':'image/png','data':base64.b64encode(blob).decode()},token)
def submit(h,iid,token,eventId,step,ref,**extra):return h.request(f'/instances/{iid}/events',dict(eventId=eventId,type='submit',step=step,payload={'value':{'ref':ref}},**extra),token)
def read(h,iid,token,ref):return h.request(f'/instances/{iid}/media/{ref}',token=token)
def probes(kind,directory,Host):
 h=Host(kind,directory/(kind+'-image.sqlite'))
 try:
  support=h.request('/support');assert support['media']=={'image_contributions@1':{'kind':'image','uploadMediaTypes':['image/png']},'audio_contributions@1':{'kind':'audio','uploadMediaTypes':['audio/wav']}}
  p=package('image-check-in');tokens=h.setup(p,participants=['a','b'],settings={'opens_at':10,'closes_at':20})
  assert upload(h,'test','intruder',png())['outcome']=='unauthorized'
  assert upload(h,'test',tokens['organizer'],png())['outcome']=='unauthorized'
  for blob in [b'',b'\x89PNG\r\n\x1a\n',png()+b'extra',png()[:-1],b'not a png']:
   assert upload(h,'test',tokens['a'],blob)=={'outcome':'invalid_media'}
  assert h.request('/instances/test/media',{'mediaType':'image/jpeg','data':base64.b64encode(png()).decode()},tokens['a'])=={'outcome':'invalid_media'}
  from png_check import fixtures
  for label,blob,valid in fixtures():
   result=upload(h,'test',tokens['a'],blob);assert result.get('outcome')==('ready' if valid else 'invalid_media'),(kind,label,result)
  ready=upload(h,'test',tokens['a'],png());ref=ready['ref'];assert ref=='sha256:'+hashlib.sha256(png()).hexdigest();assert upload(h,'test',tokens['a'],png())==ready
  assert read(h,'test',tokens['a'],ref)['data']==base64.b64encode(png()).decode()
  assert read(h,'test',tokens['b'],ref)['outcome']=='unauthorized';assert read(h,'test',tokens['organizer'],ref)['outcome']=='unauthorized'
  # Successful upload, rejected too-early contribution, and retry preserve identity.
  assert submit(h,'test',tokens['a'],'a','answer',ref)=={'outcome':'rejected'};h.restart();h.clock(10)
  assert submit(h,'test',tokens['b'],'foreign-owner','answer',ref)=={'outcome':'rejected'}
  assert submit(h,'test',tokens['a'],'forged','answer',ref,ready=True)=={'outcome':'rejected'}
  assert submit(h,'test',tokens['a'],'missing','answer','missing')=={'outcome':'rejected'}
  # Trusted registry-only fault witnesses; no public endpoint creates unready/audio refs.
  with sqlite3.connect(h.db) as db:
   for r,k,ready in [('pending','image',0),('wrong-kind','audio',1)]:db.execute('INSERT INTO media VALUES(?,?,?,?,?,?,?)',('test','a',r,k,ready,'image/png',png()))
  for r in ['pending','wrong-kind']:assert submit(h,'test',tokens['a'],r,'answer',r)=={'outcome':'rejected'}
  other=h.setup(p,'foreign',participants=['a','b'],settings={'opens_at':10,'closes_at':20});foreign=upload(h,'foreign',other['a'],png(2))['ref'];assert submit(h,'test',tokens['a'],'foreign-instance','answer',foreign)=={'outcome':'rejected'}
  assert read(h,'test',tokens['a'],foreign)['outcome']=='unauthorized'
  with concurrent.futures.ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda i:submit(h,'test',tokens['a'],'race-'+str(i),'answer',ref),range(2)))
  assert sorted(r['outcome'] for r in results)==['accepted','rejected'];winner=results.index({'outcome':'accepted'})
  h.restart();assert submit(h,'test',tokens['a'],'race-'+str(winner),'answer',ref)=={'outcome':'replayed'}
  assert h.request('/instances/test/view',token=tokens['b'])['view']['records'][1]['entries']==[]
  assert read(h,'test',tokens['b'],ref)['outcome']=='unauthorized'
  h.clock(20);time.sleep(.08);assert submit(h,'test',tokens['b'],'late','answer',ref)=={'outcome':'rejected'}
  h.restart();assert read(h,'test',tokens['b'],ref)['data']==base64.b64encode(png()).decode();assert read(h,'test',tokens['organizer'],ref)['ref']==ref
  assert submit(h,'test',tokens['a'],'race-'+str(winner),'answer',ref)=={'outcome':'replayed'}
  # Upload remains separately successful even when the later deadline prohibits acceptance.
  late=upload(h,'test',tokens['b'],png(3));assert late['outcome']=='ready';assert submit(h,'test',tokens['b'],'late-new','answer',late['ref'])=={'outcome':'rejected'};assert read(h,'test',tokens['a'],late['ref'])['outcome']=='unauthorized'
  recurring=package('image-daily-private');t=h.setup(recurring,'repeat',participants=['a','b'],settings={'starts_at':30});r=upload(h,'repeat',t['a'],png(4))['ref'];h.clock(30);assert submit(h,'repeat',t['a'],'first','entry:0',r)['outcome']=='accepted'
  assert read(h,'repeat',t['b'],r)['outcome']=='unauthorized';h.clock(86400030);assert read(h,'repeat',t['b'],r)['ref']==r
  assert submit(h,'repeat',t['a'],'stale','entry:0',r)['outcome']=='rejected';assert submit(h,'repeat',t['a'],'second','entry:1',r)['outcome']=='accepted'
  # Historical reveal does not authorize a new unrevealed reference from another occurrence.
  r2=upload(h,'repeat',t['a'],png(5))['ref'];assert read(h,'repeat',t['b'],r2)['outcome']=='unauthorized'
  h.clock(244800030);time.sleep(.08);h.restart();assert h.request('/instances/repeat/status')['phase']=='complete';assert submit(h,'repeat',t['a'],'second','entry:1',r)['outcome']=='replayed'
  hidden=package('check-in');hidden['id']='harmonomicon.image-noreveal';hidden['runbook']['steps'].pop();hidden['requires'].remove('reveal@1');hidden['requires'].append('image_contributions@1');hidden['runbook']['steps'][0]['fields']={'value':{'type':'image_ref','visibility':'private'}};hidden['runbook']['steps'][0]['afterMs']=1
  t=h.setup(hidden,'hidden',participants=['a','b']);r=upload(h,'hidden',t['a'],png(7))['ref'];assert submit(h,'hidden',t['a'],'hidden','answer',r)['outcome']=='accepted';h.clock(244800031);deadline=time.monotonic()+3
  while h.request('/instances/hidden/status')['phase']!='complete':
   assert time.monotonic()<deadline,'hidden form worker did not close';time.sleep(.02)
  h.restart();assert h.request('/instances/hidden/status')['phase']=='complete';assert read(h,'hidden',t['b'],r)['outcome']=='unauthorized';assert read(h,'hidden',t['organizer'],r)['outcome']=='unauthorized';assert read(h,'hidden',t['a'],r)['ref']==r

 finally:h.stop()
 h=Host(kind,directory/(kind+'-image-disabled.sqlite'),disabled='image_contributions@1')
 try:
  assert h.request('/support')['media']=={'audio_contributions@1':{'kind':'audio','uploadMediaTypes':['audio/wav']}};p=package('image-check-in');h.request('/packages',{'package':p});assert h.request('/instances',dict(id='no',packageId=p['id'],version=p['version'],participants=['a','b'],organizer='organizer',settings={'opens_at':0,'closes_at':20}))=={'outcome':'unsupported','missing':['image_contributions@1']}
  with sqlite3.connect(h.db) as db:assert db.execute('SELECT count(*) FROM instances').fetchone()[0]==db.execute('SELECT count(*) FROM media').fetchone()[0]==0
 finally:h.stop()
 print(f'{kind}: image actual bytes/authority/privacy/race, partial-success retry, recurrence, worker/restart and absent-capability checks pass',flush=True)
def transfer(directory,Host):
 p=package('check-in');p['id']='harmonomicon.imagethenstory';p['requires'].append('image_contributions@1');p['runbook']['steps'][0]['fields']={'answer':{'type':'image_ref','visibility':'private'}}
 story=package('timed-story');p['requires']=sorted(set(p['requires']+story['requires']));p['runbook']['steps']+=story['runbook']['steps']
 hosts=[Host(k,directory/(k+'-image-transfer.sqlite')) for k in ['python','node']]
 try:
  hosts[0].request('/packages',{'package':p});export=hosts[0].request(f"/packages/{p['id']}/{p['version']}");assert hosts[1].request('/packages',{'package':export['package']})['digest']==export['digest'];snapshots=[]
  for h in hosts:
   tokens=h.setup(p,participants=['a','b']);refs={a:upload(h,'test',tokens[a],png(i+6))['ref'] for i,a in enumerate(['a','b'])}
   for a in ['a','b']:assert h.request('/instances/test/events',dict(eventId='image-'+a,type='submit',step='answer',payload={'answer':{'ref':refs[a]}}),tokens[a])['outcome']=='accepted'
   h.restart()
   for i,a in enumerate(['a','b']):assert h.request('/instances/test/events',dict(eventId='write-'+a,type='submit',step='write:'+str(i),payload={'text':a+' responds'}),tokens[a])['outcome']=='accepted'
   assert read(h,'test',tokens['b'],refs['a'])['ref']==refs['a'];v={a:h.request('/instances/test/view',token=tokens[a])['view'] for a in tokens};assert v['a']['phase']=='complete';snapshots.append(v)
  assert snapshots[0]==snapshots[1]
 finally:
  for h in hosts:h.stop()
 print('Image form/reveal/story held-out package transfers without interpreter changes',flush=True)

def compare_legacy(kind,directory,Host):
 import importlib.util
 from migration_check import semantic_view as scheduled_view
 from recurrence_check import project
 spec=importlib.util.spec_from_file_location('legacy_image_trial',ROOT/'validation/0.12/run.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
 def unwrap(x):
  if type(x) is dict:return x['ref'] if set(x)=={'ref'} else {k:unwrap(v) for k,v in x.items()}
  return [unwrap(v) for v in x] if type(x) is list else x
 for name in ['image-check-in','image-daily-prompt']:
  for empty in [False,True]:
   label=name+('-empty' if empty else '-partial');old=legacy.Host(kind,directory/(kind+'-old-'+label+'.sqlite'));new=Host(kind,directory/(kind+'-new-'+label+'.sqlite'))
   try:
    p=package(name);source=json.loads((ROOT/f'format/0.12/examples/{name}.json').read_text());assert p['id']==source['id'] and p['version']!=source['version'] and p['participants']==source['participants']
    people=['a','b'];tokens={a:'old-'+a for a in people+['organizer']};setup={'opensAt':10,'closesAt':20} if name=='image-check-in' else {'startsAt':10};bindings={'opens_at':10,'closes_at':20} if name=='image-check-in' else {'starts_at':10}
    status,out=old.request('POST','/admin/instances',dict(instanceId='test',packageId=source['id'],packageVersion=source['version'],participants=people,organizer='organizer',tokens=tokens,**setup),admin=True);assert status==201,out
    t=new.setup(p,participants=people,settings=bindings)
    def compare():
     for actor in tokens:
      status,before=old.request('GET','/instances/test/view',token=tokens[actor]);after=new.request('/instances/test/view',token=t[actor])['view'];after=scheduled_view(after,actor,people) if name=='image-check-in' else project(after,actor,people,'daily-shared-prompt');assert before==unwrap(after),(kind,label,actor,before,after)
    compare();body={'mediaType':'image/png','data':base64.b64encode(png()).decode()};status,out=old.request('POST','/instances/test/media',body,token=tokens['a']);assert status==200,out;ref=out['ref'];assert upload(new,'test',t['a'],png())['ref']==ref
    actions=[(9,'early','a',1,ref,'rejected')]
    if not empty:actions += [(10,'ok','a',1,ref,'accepted'),(11,'wrong-owner','b',1,ref,'rejected')]
    if name=='image-check-in':actions += [(20,'late','b',1,ref,'rejected')]
    else:actions += [(72000010,'late','b',1,ref,'rejected'),(86400010,'stale','b',1,ref,'rejected'),(86400011,'next','a',2,ref,'accepted')]
    if not empty:actions += [(86400012 if name!='image-check-in' else 20,'ok','a',1,ref,'replayed')]
    for at,i,actor,occ,value,expected in actions:
     old.set_clock(at);new.clock(at);payload={'value':value,**({'occurrence':occ} if name!='image-check-in' else {})};status,before=old.request('POST','/instances/test/events',dict(eventId=i,type='submit',payload=payload),token=tokens[actor]);after=submit(new,'test',t[actor],i,'answer' if name=='image-check-in' else f'entry:{occ-1}',ref);assert status==200 and before['outcome']==after['outcome']==expected,(label,i,before,after);compare();old.restart();new.restart();compare()
    end=20 if name=='image-check-in' else 244800010;old.set_clock(end);new.clock(end);compare()
    if not empty:
     for actor in ['b','organizer']:
      status,blob=old.request('GET','/instances/test/media/'+ref,token=tokens[actor]);assert status==200 and blob['data']==read(new,'test',t[actor],ref)['data']
   finally:old.close();new.stop()
 print(f'{kind}: four actual 0.12 image-package comparisons pass phase/count/status/visibility/ordered values, byte access, boundary/replay and restart',flush=True)

if __name__=='__main__':
 import tempfile
 from run import Host
 with tempfile.TemporaryDirectory() as d:
  for k in ['python','node']:probes(k,Path(d),Host);compare_legacy(k,Path(d),Host)
  transfer(Path(d),Host)
