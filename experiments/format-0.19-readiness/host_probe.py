"""Review-only durable execution and image-distribution boundary demonstration."""
import copy,json,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'validation/0.19'));sys.path.insert(0,str(HERE))
from run import Host
from image_trial import png,upload,read
from probe import cases,request,positive
from runtime import run

def replace_refs(value,refs):
 if isinstance(value,dict):return {k:replace_refs(v,refs) for k,v in value.items()}
 if isinstance(value,list):return [replace_refs(v,refs) for v in value]
 return refs.get(value,value) if isinstance(value,str) else value

def durable(kind,c,directory):
 h=Host(kind,directory/(kind+'-'+c['id']+'.sqlite'),seed=c.get('seed',1729))
 try:
  req=request(c);tokens=h.setup(req['package'],participants=c['people'],settings=c.get('settings'));refs={}
  for i,a in enumerate(c['people']):
   if any(m['actor']==a for m in c.get('trustedMedia',[])):refs['image:'+a]=upload(h,'test',tokens[a],png(i+30))['ref']
  req=replace_refs(req,refs);ref=run(req)
  assert ref['outcomes']==c['outcomes']
  for i,e in enumerate(req['events']):
   h.clock(e['at'])
   if e['type']!='tick':assert h.request('/instances/test/events',{k:e[k] for k in ['eventId','type','step','payload']},tokens[e['actor']])['outcome']==c['outcomes'][i]
   views={a:h.request('/instances/test/view',token=tokens[a])['view'] for a in tokens};assert views==ref['views'][i],(kind,c['id'],i)
   if i==len(req['events'])//2:h.restart();assert {a:h.request('/instances/test/view',token=tokens[a])['view'] for a in tokens}==views
  h.restart();assert h.request('/instances/test/view',token=tokens[c['people'][0]])['view']['phase']=='complete'
 finally:h.stop()
 print('DURABLE',kind,c['id'],flush=True)

def string_workaround(kind,directory):
 examples=ROOT/'format/0.19/examples';p=json.loads((examples/'check-in.json').read_text());p['id']='review.reference-smuggling';p['version']='0.1.0';p['requires'].append('image_contributions@1');p['runbook']['steps']=p['runbook']['steps'][:1];p['runbook']['steps'][0]['fields']['answer']['type']='image_ref'
 exchange=json.loads((examples/'idea-response-and-pairs.json').read_text());p['runbook']['steps']+=exchange['runbook']['steps'][:3];p['runbook']['steps'][1]['close']='all';p['requires']=sorted(set(p['requires']+exchange['requires']))
 # Extra requires are allowed; only the first three text-exchange operations execute.
 h=Host(kind,directory/(kind+'-reference-smuggling.sqlite'))
 try:
  tokens=h.setup(p,participants=['a','b']);refs={a:upload(h,'test',tokens[a],png(i+40))['ref'] for i,a in enumerate(['a','b'])}
  for a in ['a','b']:assert h.request('/instances/test/events',dict(eventId='image-'+a,type='submit',step='answer',payload={'answer':{'ref':refs[a]}}),tokens[a])['outcome']=='accepted'
  for a in ['a','b']:assert h.request('/instances/test/events',dict(eventId='source-'+a,type='submit',step='sources',payload={'itemId':a,'text':refs[a]}),tokens[a])['outcome']=='accepted'
  h.restart();view=h.request('/instances/test/view',token=tokens['a'])['view'];assignment=next(r for r in view['records'] if r['op']=='assign_sources@1')['assignment'];assert assignment=={'itemId':'b','text':refs['b']}
  # Text assignment exposes a string, not an authorized typed image projection.
  assert read(h,'test',tokens['a'],refs['b'])['outcome']=='unauthorized';assert read(h,'test',tokens['b'],refs['b'])['ref']==refs['b']
  assert h.request('/instances/test/events',dict(eventId='reply',type='submit',step='response',payload={'itemId':'b','text':'Blind response'}),tokens['a'])['outcome']=='accepted'
 finally:h.stop()
 print('LIMIT',kind,'text reference assignment grants no image byte access; no faithful image-source response',flush=True)

if __name__=='__main__':
 with tempfile.TemporaryDirectory(prefix='harmonomicon-019-review-') as d:
  for kind in ['python','node']:
   for c in cases():durable(kind,c,Path(d))
   string_workaround(kind,Path(d))
 print('Four new compositions pass both durable hosts; image-string workaround fails the read contract as specified.')
