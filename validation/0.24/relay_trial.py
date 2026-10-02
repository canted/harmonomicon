#!/usr/bin/env python3
"""Authenticated SQLite hosts: atomic races, durable queue handoff and byte authority."""
import concurrent.futures,copy,json,sqlite3,tempfile,time
from pathlib import Path
from run import Host,ROOT,ADMIN
from runtime import Engine,run
from relay_check import package
from image_trial import png

DAY=86400000
PEOPLE=['a','b','c','d','e','preauthorized']
def record(view):return next(r for r in view['records'] if r['op']=='first_valid@1')
def all_views(h,iid,tokens):return {a:h.request('/instances/'+iid+'/view',token=t)['view'] for a,t in tokens.items()}
def import_package(h,p):assert h.request('/packages',{'package':p})['outcome'] in ['imported','existing']
def request(p,iid,people=PEOPLE):return dict(id=iid,packageId=p['id'],version=p['version'],participants=people,organizer='organizer')
def view(h,iid,tokens,a=None):return h.request('/instances/'+iid+'/view',token=tokens[a or next(iter(tokens))])['view']
def body(eid,kind,payload):return dict(eventId=eid,type=kind,step='piece',payload=payload)
def ticket_payload(r,actor,value=None,item='part'):
 p=dict(invitation=next(t['key'] for t in r['offer']['invitations'] if t['actor']==actor),predecessor=None if r['canonical'] is None else r['canonical']['ref'])
 if value is not None:p.update(itemId=item,value=value)
 return p
def text(value):return {'kind':'text','text':value}
def submit(h,iid,tokens,actor,payload,eid='send'):return h.request('/instances/'+iid+'/events',body(eid,'submit',payload),tokens[actor])
def control(h,iid,actors,eid='roster'):return h.request('/instances/'+iid+'/control',body(eid,'roster',{'actors':actors}))
def created(h,p,iid,people=PEOPLE):
 import_package(h,p);req=request(p,iid,people);r=h.request('/instances',req);assert r['outcome']=='created',r;return r,req

def successor_request(p,iid,origin,canonical,people=PEOPLE):
 req=request(p,iid,people);req['hostQueues']={'line':{'instance':origin,'source':'piece'}}
 if canonical is not None:
  # Direct origin lookup uses the canonical's true source, even after a failed pass.
  req['hostBindings']={'previous':{'instance':origin,'source':'piece','itemId':canonical['ref']['itemId']}}
 return req

def step_trial(kind,directory):
 h=Host(kind,directory/(kind+'-relay.sqlite'))
 try:
  start=package();follow=package('continue');empty=package('retry-empty')
  invalid=copy.deepcopy(start);invalid['queueInputs']=None
  assert h.request('/packages',{'package':invalid})=={'outcome':'invalid_package'}
  with sqlite3.connect(h.db) as db:assert db.execute('SELECT count(*) FROM packages').fetchone()[0]==0
  import_package(h,follow);import_package(h,empty)
  first,first_req=created(h,start,'first');tokens=first['tokens'];r=record(view(h,'first',tokens));pair=r['offer']['actors']
  h.clock(1000)
  submissions=[body('race-'+str(i),'submit',ticket_payload(r,a,text(a+' adds the first piece'),'part-'+str(i))) for i,a in enumerate(pair)]
  with concurrent.futures.ThreadPoolExecutor(2) as pool:
   results=list(pool.map(lambda pair:h.request('/instances/first/events',pair[1],tokens[pair[0]])['outcome'],zip(pair,submissions)))
  assert sorted(results)==['accepted','rejected'],(kind,results)
  winner=pair[results.index('accepted')];loser=next(a for a in pair if a!=winner);accepted=submissions[results.index('accepted')]
  r=record(view(h,'first',tokens));assert len(r['entries'])==1 and r['canonical']['actor']==winner and r['output']['queue']['order'][0]==loser
  before=all_views(h,'first',tokens);h.restart();assert all_views(h,'first',tokens)==before
  assert h.request('/instances/first/events',accepted,tokens[winner])['outcome']=='replayed'
  # Failed setup must leave source unclaimed, target nonexistent and grants absent.
  bad=successor_request(follow,'bad','first',r['canonical']);bad['hostBindings']['previous']['itemId']='invented'
  assert h.request('/instances',bad)['outcome']=='invalid_setup'
  with sqlite3.connect(h.db) as db:
   assert db.execute('SELECT count(*) FROM queue_consumptions').fetchone()[0]==0
   assert db.execute('SELECT count(*) FROM instances WHERE id=?',('bad',)).fetchone()[0]==0
   assert db.execute('SELECT count(*) FROM input_grants WHERE destination=?',('bad',)).fetchone()[0]==0
  # Same qualified source cannot create two successors, even concurrently.
  reqs=[successor_request(follow,'next-'+str(i),'first',r['canonical']) for i in range(2)]
  with concurrent.futures.ThreadPoolExecutor(2) as pool:answers=list(pool.map(lambda req:h.request('/instances',req),reqs))
  assert sorted(a['outcome'] for a in answers)==['created','queue_consumed'],answers
  chosen=next(i for i,a in enumerate(answers) if a['outcome']=='created');created_next=answers[chosen];next_req=reqs[chosen];iid=next_req['id'];next_tokens=created_next['tokens']
  nr=record(view(h,iid,next_tokens));assert nr['offer']['actors'][0]==loser and winner not in nr['offer']['actors'];assert nr['offer']['closesAt']==1000+DAY
  # Decline replaces one ticket within original deadline; retained partner can finish.
  partner=nr['offer']['actors'][1];old_partner=ticket_payload(nr,partner,text('partner continues'),'second')
  declined=nr['offer']['actors'][0]
  assert h.request('/instances/'+iid+'/events',body('decline','decline',ticket_payload(nr,declined)),next_tokens[declined])['outcome']=='accepted'
  replaced=record(view(h,iid,next_tokens));assert replaced['offer']['closesAt']==nr['offer']['closesAt']
  assert next(t['key'] for t in replaced['offer']['invitations'] if t['actor']==partner)==old_partner['invitation']
  assert submit(h,iid,next_tokens,declined,ticket_payload(nr,declined,text('stale')),'stale')['outcome']=='rejected'
  assert submit(h,iid,next_tokens,partner,old_partner,'partner')['outcome']=='accepted'
  # Lost creation response retry resolves original identity after old deadline, without relaunch.
  h.clock(1000+DAY+1);h.restart();receipt=h.request('/instances',next_req)
  assert receipt['outcome']=='existing' and receipt['instanceIdentity']==created_next['instanceIdentity']
  changed=copy.deepcopy(next_req);changed['participants']=list(reversed(PEOPLE));assert h.request('/instances',changed)['outcome']=='instance_conflict'
  # Initial empty full-pass completion and exact cooldown/null canonical successor.
  began,_=created(h,start,'empty',people=['a','b']);et=began['tokens'];opened=1000+DAY+1
  h.clock(opened+DAY);er=record(view(h,'empty',et));assert er['output']['status']=='exhausted' and er['output']['queue']['canonical'] is None
  retry=successor_request(empty,'empty-retry','empty',None,people=['a','b']);assert h.request('/instances',retry)['outcome']=='invalid_setup'
  h.clock(opened+2*DAY);retry_created=h.request('/instances',retry);assert retry_created['outcome']=='created',retry_created
  h.clock(opened+3*DAY);assert record(view(h,'empty-retry',retry_created['tokens']))['status']=='exhausted'
  h.restart();assert h.request('/instances',retry)['instanceIdentity']==retry_created['instanceIdentity']
  # Fresh shared window after a carried person's partner wins; no inherited lifetime timer.
  canonical=record(view(h,iid,next_tokens))['canonical'];next_canon_req=successor_request(follow,'third',iid,canonical)
  third=h.request('/instances',next_canon_req);assert third['outcome']=='created',third
  tr=record(view(h,'third',third['tokens']));now=opened+3*DAY;assert tr['offer']['closesAt']==now+DAY
  prior_author=canonical['actor'];h.clock(now+DAY);expired=record(view(h,'third',third['tokens']))
  assert prior_author not in expired['offer']['actors'] and expired['canonical']==canonical
  # Fully new viewer denied; prebound source viewer can be included after withdrawal.
  new_req=successor_request(follow,'unbound-newcomer',iid,canonical,people=PEOPLE+['new-person'])
  assert h.request('/instances',new_req)['outcome']=='invalid_setup'
  # Actual image acceptance/grants: foreign owner and unready image do not win.
  media_start,_=created(h,start,'media');mt=media_start['tokens'];mr=record(view(h,'media',mt));owner,other=mr['offer']['actors']
  media=h.request('/instances/media/media',{'mediaType':'image/png','data':__import__('base64').b64encode(png(77)).decode()},mt[owner]);assert media['outcome']=='ready'
  value={'kind':'image','ref':media['ref']}
  assert submit(h,'media',mt,other,ticket_payload(mr,other,value),'foreign')['outcome']=='rejected'
  with sqlite3.connect(h.db) as db:db.execute('UPDATE media SET ready=0 WHERE instance=?',('media',))
  assert submit(h,'media',mt,owner,ticket_payload(mr,owner,value),'ready')['outcome']=='rejected'
  with sqlite3.connect(h.db) as db:db.execute('UPDATE media SET ready=1 WHERE instance=?',('media',))
  assert control(h,'media',[a for a in PEOPLE if a!='preauthorized'])['outcome']=='accepted'
  assert submit(h,'media',mt,owner,ticket_payload(mr,owner,value),'ready')['outcome']=='accepted'
  image_canon=record(view(h,'media',mt))['canonical'];media_next_req=successor_request(follow,'media-next','media',image_canon)
  media_next=h.request('/instances',media_next_req);assert media_next['outcome']=='created',media_next
  pre=media_next['tokens']['preauthorized'];read=h.request('/instances/media-next/media/'+media['ref'],token=pre);assert read['mediaType']=='image/png'
  assert h.request('/instances/media-next/media/'+media['ref'],token='intruder')['outcome']=='unauthorized'
  state_before=all_views(h,'media-next',media_next['tokens']);h.restart();assert all_views(h,'media-next',media_next['tokens'])==state_before
  assert h.request('/instances/media-next/media/'+media['ref'],token=pre)==read
  # Qualified source alias rejection, even when the declaration names differ.
  alias=copy.deepcopy(follow);alias['id']+='-alias';alias['queueInputs']['alias']={'type':'invitation_queue'};second=copy.deepcopy(alias['runbook']['steps'][0]);second.update(id='other',queueInput={'binding':'alias'});alias['runbook']['steps'].append(second);import_package(h,alias)
  alias_req=successor_request(alias,'alias','media',image_canon);alias_req['hostQueues']['alias']=alias_req['hostQueues']['line'];assert h.request('/instances',alias_req)['outcome']=='invalid_setup'
  # Fresh unbound member is denied both source authority and media bytes.
  newcomer=successor_request(follow,'new-media-person','media',image_canon,people=PEOPLE+['new-media-person']);assert h.request('/instances',newcomer)['outcome']=='invalid_setup'
  # A failed continuation preserves true canonical origin, then consumes its own queue.
  origin,_=created(h,start,'origin',people=['a','b','c']);ot=origin['tokens'];orr=record(view(h,'origin',ot));author=orr['offer']['actors'][0]
  assert submit(h,'origin',ot,author,ticket_payload(orr,author,text('true origin')),'origin-piece')['outcome']=='accepted'
  canon=record(view(h,'origin',ot))['canonical'];failed_req=successor_request(follow,'failed','origin',canon,people=['a','b','c']);failed=h.request('/instances',failed_req);assert failed['outcome']=='created'
  current=record(view(h,'failed',failed['tokens']));failure_at=current['offer']['closesAt'];h.clock(failure_at);fr=record(view(h,'failed',failed['tokens']));assert fr['status']=='exhausted' and fr['canonical']==canon
  preserved=successor_request(follow,'preserved','failed',canon,people=['a','b','c']);preserved['hostBindings']['previous']['instance']='origin'
  assert h.request('/instances',preserved)['outcome']=='invalid_setup';h.clock(fr['output']['queue']['notBefore']);preserved_created=h.request('/instances',preserved);assert preserved_created['outcome']=='created',preserved_created
  pr=record(view(h,'preserved',preserved_created['tokens']));assert pr['canonical']==canon and author not in pr['offer']['actors']
  # Safe-clock termination is non-resumable in the actual durable host too.
  clock_start,_=created(h,start,'clock-limit',people=['a','b']);h.clock(9007199254740990)
  cr=record(view(h,'clock-limit',clock_start['tokens']));assert cr['status']=='clock_exhausted' and cr['output']['queue']['notBefore'] is None
  h.restart();assert record(view(h,'clock-limit',clock_start['tokens']))==cr
  no_resume=successor_request(empty,'no-clock-resume','clock-limit',None,people=['a','b']);assert h.request('/instances',no_resume)['outcome']=='invalid_setup'
  print(kind+': two-valid race, atomic canonical/closure, replay/restart, loser carryover/shared24h, decline retained tickets, expiry/exclusion, null retry/cooldown, successor race/rollback/alias, creation retry and real PNG origin grants pass',flush=True)
 finally:h.stop()

def different_composition(directory):
 p=json.loads((ROOT/'format/0.24/examples/relay-paired-reflection.json').read_text());people=['a','b','c','d']
 hosts=[Host(kind,directory/(kind+'-different.sqlite')) for kind in ['python','node']]
 try:
  import_package(hosts[0],p);export=hosts[0].request('/packages/'+p['id']+'/'+p['version']);imported=hosts[1].request('/packages',{'package':export['package']});assert imported['digest']==export['digest']
  for h in hosts:
   assert h.request('/instances',request(p,'different-odd',['a','b','c']))['outcome']=='invalid_setup'
   made=h.request('/instances',request(p,'different',people));assert made['outcome']=='created';tokens=made['tokens'];r=record(view(h,'different',tokens));author=r['offer']['actors'][0];payload=ticket_payload(r,author,text('piece for reflection'))
   assert submit(h,'different',tokens,author,payload)['outcome']=='accepted'
   assert h.request('/instances/different/events',dict(eventId='note',type='submit',step='reflect',payload={'text':'private note'}),tokens['a'])['outcome']=='accepted'
   got=all_views(h,'different',tokens);assert got['a']['records'][-1]['entries']==got['b']['records'][-1]['entries'] and got['c']['records'][-1]['entries']==got['organizer']['records'][-1]['entries']==[]
   reference=run(dict(package=p,participants=people,organizer='organizer',seed=h.seed,instanceId=made['instanceIdentity'],events=[dict(actor=author,at=0,**body('send','submit',payload)),dict(eventId='note',type='submit',actor='a',at=0,step='reflect',payload={'text':'private note'})]))
   assert got==reference['views'][-1];h.restart();assert all_views(h,'different',tokens)==got
   empty=h.request('/instances',request(p,'different-empty',people));assert empty['outcome']=='created';et=empty['tokens'];h.clock(DAY);assert record(view(h,'different-empty',et))['status']=='open';h.clock(2*DAY)
   er=record(view(h,'different-empty',et));assert er['status']=='exhausted' and er['canonical'] is None
   assert h.request('/instances/different-empty/events',dict(eventId='empty-note',type='submit',step='reflect',payload={'text':'an idea to start'}),et['a'])['outcome']=='accepted'
   notes=all_views(h,'different-empty',et);assert notes['b']['records'][-1]['entries'][0]['value']['text']=='an idea to start'
   assert notes['c']['records'][-1]['entries']==notes['organizer']['records'][-1]['entries']==[]
   h.restart();assert all_views(h,'different-empty',et)==notes
  print('Different 24-hour first-valid/private-pair composition transfers identical definition/digest; selected/empty paths, odd-roster refusal and exact private views survive restart in both hosts',flush=True)
 finally:
  for h in hosts:h.stop()

def queue_audience_trial(kind,directory):
 h=Host(kind,directory/(kind+'-queue-audience.sqlite'))
 try:
  start=package();start['id']+='-audience';start['runbook']['steps'][0].update(windowMs=100,retryAfterMs=50)
  empty=package('retry-empty');empty['id']+='-audience';empty['runbook']['steps'][0].update(windowMs=100,retryAfterMs=50)
  empty['requires'].append('pool@2');empty['runbook']['steps'].append(dict(id='later',op='pool@2',prompt='Collect a later private note.',kinds=['text'],perActor=1,visibility='private'))
  import_package(h,empty)
  def snapshot(iid):
   with sqlite3.connect(h.db) as db:
    return (db.execute('SELECT state FROM instances WHERE id=?',(iid,)).fetchone()[0],db.execute('SELECT actor,hash FROM tokens WHERE instance=? ORDER BY actor,hash',(iid,)).fetchall(),db.execute('SELECT * FROM input_grants WHERE destination=? ORDER BY actor,origin,ref',(iid,)).fetchall(),db.execute('SELECT * FROM queue_consumptions ORDER BY source_instance,source').fetchall())
  source,_=created(h,start,'audience-source',people=['a','b']);h.clock(100)
  sr=record(view(h,'audience-source',source['tokens']));assert sr['status']=='exhausted' and sr['canonical'] is None and sr['output']['queue']['notBefore']==150
  h.clock(150)
  denied=successor_request(empty,'audience-outsider-create','audience-source',None,people=['a','b','outsider'])
  assert h.request('/instances',denied)['outcome']=='invalid_setup'
  req=successor_request(empty,'audience-retry','audience-source',None,people=['a','b']);made=h.request('/instances',req);assert made['outcome']=='created';tokens=made['tokens']
  h.restart();before=all_views(h,'audience-retry',tokens);stored=snapshot('audience-retry')
  assert control(h,'audience-retry',['a','b','outsider'])['outcome']=='rejected'
  assert snapshot('audience-retry')==stored and all_views(h,'audience-retry',tokens)==before
  assert h.request('/instances/audience-retry/bindings',{'actor':'outsider','token':'outsider-token'})['outcome']=='invalid_request'
  assert h.request('/instances/audience-retry/view',token='outsider-token')['outcome']=='unauthorized'
  assert snapshot('audience-retry')==stored
  r=record(before['a']);actor=r['offer']['actors'][0];assert submit(h,'audience-retry',tokens,actor,ticket_payload(r,actor,text('later phase')))['outcome']=='accepted'
  h.restart();before=all_views(h,'audience-retry',tokens);stored=snapshot('audience-retry')
  configure=dict(eventId='later-outsider',type='configure',step='later',payload={'actors':['a','b','outsider'],'opensAt':None,'closesAt':None})
  assert h.request('/instances/audience-retry/control',configure)['outcome']=='rejected'
  assert snapshot('audience-retry')==stored and all_views(h,'audience-retry',tokens)==before
  assert h.request('/instances/audience-retry/bindings',{'actor':'outsider','token':'later-outsider-token'})['outcome']=='invalid_request'
  assert snapshot('audience-retry')==stored
  # A source-bound person removed from active membership retains read authority.
  prebound,_=created(h,start,'audience-prebound-source',people=['a','b','preauthorized'])
  assert control(h,'audience-prebound-source',['a','b'])['outcome']=='accepted'
  h.clock(250);pr=record(view(h,'audience-prebound-source',prebound['tokens']));assert pr['status']=='exhausted' and pr['canonical'] is None
  h.clock(300);pre_req=successor_request(empty,'audience-prebound-retry','audience-prebound-source',None,people=['a','b']);allowed=h.request('/instances',pre_req);assert allowed['outcome']=='created';pt=allowed['tokens']
  h.restart();r=record(view(h,'audience-prebound-retry',pt));partner=r['offer']['actors'][0];ticket=ticket_payload(r,partner,text('authorized queue viewer'))
  assert control(h,'audience-prebound-retry',['a','b','preauthorized'])['outcome']=='accepted'
  assert h.request('/instances/audience-prebound-retry/bindings',{'actor':'preauthorized','token':'preauthorized-token'})['outcome']=='bound'
  visible=h.request('/instances/audience-prebound-retry/view',token='preauthorized-token')['view'];retained=record(visible)
  assert retained['offer']==r['offer']
  assert submit(h,'audience-prebound-retry',pt,partner,ticket)['outcome']=='accepted'
  h.restart();assert h.request('/instances/audience-prebound-retry/view',token='preauthorized-token')['view']['records'][-1]['step']=='later'
  print(kind+': null-canonical queue audience rechecked on roster/later configuration after restart; denial preserves exact state/tokens/grants/claims, prebound source viewer permitted',flush=True)
 finally:h.stop()

def capability_trial(kind,directory):
 for disabled in ['first_valid@1','policy:rolling_pair@1','invitation_queue@1','seeded_assignment@1']:
  h=Host(kind,directory/(kind+'-'+disabled.replace(':','-')+'.sqlite'),disabled=disabled)
  try:
   p=package();import_package(h,p);assert h.request('/instances',request(p,'unsupported'))=={'outcome':'unsupported','missing':[disabled]}
   with sqlite3.connect(h.db) as db:
    for table in ['instances','tokens','queue_consumptions','input_grants']:assert db.execute('SELECT count(*) FROM '+table).fetchone()[0]==0
  finally:h.stop()
 print(kind+': exact capability refusal without state/grants/claims passes',flush=True)
if __name__=='__main__':
 with tempfile.TemporaryDirectory() as tmp:
  for kind in ['python','node']:step_trial(kind,Path(tmp));queue_audience_trial(kind,Path(tmp));capability_trial(kind,Path(tmp))
  different_composition(Path(tmp))
