"""Current-profile review; no new runtime operations or candidate version."""
import copy,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'format/0.19'))
from runtime import run,validate,Engine
from check import node
PIN='eab8745fc5e0b70afc1617845e3c9005b5bad019'
def package(n):return json.loads((HERE/'examples'/f'{n}.json').read_text())
def cases():return json.loads((HERE/'cases.json').read_text())
def request(c):return dict(package=package(c['id']),participants=c['people'],organizer='organizer',events=c['events'],settings=c.get('settings',{}),seed=c.get('seed'),trustedMedia=c.get('trustedMedia',[]))
def positive(c):
 req=request(c);validate(req['package']);result=run(req);assert result==node(req),c['id'];assert result['outcomes']==c['outcomes'],(c['id'],result['outcomes'])
 for witness in c['checks']:
  view=result['views'][witness['after']][witness['actor']]
  for k,v in witness.items():
   if k in ['after','actor','record']:continue
   subject=next(r for r in view['records'] if r['key']==witness['record']) if 'record' in witness else view
   assert subject[k]==v,(c['id'],witness,subject)
 for cut in range(len(c['events'])+1):
  prefix=run(dict(req,events=c['events'][:cut]));after=dict(req,state=prefix['state'],events=c['events'][cut:]);assert run(after)==node(after);assert run(after)['state']==result['state']
 return result

def negative_witnesses():
 from image_check import package as candidate,event
 outcomes=[]
 # A collected image record cannot be the source of assign_sources.
 p=candidate('image-check-in');distribution=candidate('single-source-creative-response')['runbook']['steps'][1];distribution['source']='answer';p['runbook']['steps'].append(distribution);p['requires']=sorted(set(p['requires']+['assign_sources@1','policy:seeded_nonself_source@1','seeded_assignment@1']))
 assert run(dict(action='validate',package=p))==node(dict(action='validate',package=p))=={'outcome':'invalid_package'};outcomes.append(dict(id='collected-image-to-distribution',observed='invalid_package',gap='assignment source must be text pool'))
 # Adding an image medium to pool is not a declared supported operation shape.
 p=candidate('single-source-creative-response');p['runbook']['steps'][0]['medium']='image_ref';p['requires'].append('image_contributions@1');assert run(dict(action='validate',package=p))==node(dict(action='validate',package=p))=={'outcome':'invalid_package'};outcomes.append(dict(id='typed-image-pool',observed='invalid_package',gap='pool shape/text submission has no image value'))
 p=candidate('single-source-creative-response');req=dict(package=p,participants=list('ab'),organizer='organizer',seed=1,trustedMedia=[{'actor':'a','ref':'image:a','kind':'image','ready':True}],events=[event('image','a',0,'sources',{'itemId':'a','image':{'ref':'image:a'}})]);assert run(req)==node(req) and run(req)['outcomes']==['rejected'];outcomes.append(dict(id='image-value-in-text-pool',observed='rejected',gap='typed image payload is not text'))
 # Progress is one entry/actor, not an append stream alongside final submission.
 p=candidate('check-in');p['runbook']['steps'][0]['close']='organizer';req=dict(package=p,participants=list('ab'),organizer='organizer',events=[event('p1','a',0,'answer',{'answer':'First progress'}),event('p2','a',1,'answer',{'answer':'More progress'})]);assert run(req)==node(req) and run(req)['outcomes']==['accepted','rejected'];outcomes.append(dict(id='repeated-progress-in-one-window',observed=['accepted','rejected'],gap='one entry per actor; no ongoing stream/concurrent final window'))
 # Logging consent does not enforce an opinion gate. A deterministic sequence accepts after deny.
 p=candidate('choice-poll');p['runbook']['steps']=p['runbook']['steps'][:1];p['runbook']['steps'][0]['fields']['choice']['options']=['allow','deny'];p['runbook']['steps'][0]['close']='all';p['runbook']['steps'].append(dict(id='opinion',op='collect@1',actors='participants',prompt='Give an opinion',fields={'text':{'type':'text','visibility':'private'}},close='all',afterMs=10));req=dict(package=p,participants=list('ab'),organizer='organizer',events=[event('a','a',0,'vote',{'choice':'deny'}),event('b','b',0,'vote',{'choice':'deny'}),event('opinion','b',0,'opinion',{'text':'Still accepted'})]);assert run(req)==node(req) and run(req)['outcomes']==['accepted']*3;outcomes.append(dict(id='logged-denial-does-not-gate',observed=['accepted']*3,gap='no result-dependent permission/branch; not CRP parity'))
 # Fixed repetition cannot contain different window-specific prompt bindings.
 p=candidate('image-daily-prompt');p['runbook']['steps'][0]['prompts']=['A','B','C'];assert run(dict(action='validate',package=p))==node(dict(action='validate',package=p))=={'outcome':'invalid_package'};outcomes.append(dict(id='prompt-array-in-fixed-repeat',observed='invalid_package',gap='no prompt-per-index syntax; explicit top-level windows remain a bounded workaround'))
 return outcomes
if __name__=='__main__':
 for c in cases():positive(c);print('PASS',c['id'])
 failures=negative_witnesses()
 for f in failures:print('LIMIT',f['id'],f['observed'])
 import jsonschema
 schema=json.loads((ROOT/'format/0.19/package.schema.json').read_text())
 for c in cases():jsonschema.validate(package(c['id']),schema)
 assert subprocess.check_output(['git','rev-parse',PIN],cwd=ROOT,text=True).strip()==PIN
 assert subprocess.call(['git','diff','--quiet',PIN,'--','format/0.19/runtime.py','format/0.19/runtime.mjs','validation/0.19/python_host.py','validation/0.19/node_host.mjs'],cwd=ROOT)==0,'review must exercise pinned implementations'
 print('Four newly authored combinations: both engines, independent expected fields, restart every boundary and schema pass; six explicit limits verified. Runtime pinned to',PIN)
