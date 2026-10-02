"""Bounded first-completed-contribution collection and portable invitation queue."""
import copy
import artifacts as a
import continuation as c
import voting

OPS={'first_valid@1'}
POLICIES={'policy:rolling_pair@1'}
CAPS={'invitation_queue@1'}
MAX_FAILURES=100


def declarations(package,used):
    declared=package.get('queueInputs',{})
    a.demand(type(declared) is dict and len(declared)<=8 and all(voting.name(k) for k in declared))
    a.demand(all(a.exact(v,['type']) and v['type']=='invitation_queue' for v in declared.values()))
    if declared:used.add('invitation_queue@1')
    return declared


def validate(s,known,used,nested,declared,consumed,queues,consumed_queues):
    a.demand(not nested and a.exact(s,['id','op','prompt','kinds','policy','windowMs','retryAfterMs','input','queueInput']))
    a.demand(a.text(s['prompt']) and a.kinds(s['kinds']) and s['policy']=='policy:rolling_pair@1')
    a.demand(a.integer(s['windowMs']) and 1<=s['windowMs']<=604800000 and a.integer(s['retryAfterMs']) and 1<=s['retryAfterMs']<=604800000)
    for field,bindings,seen in [('input',declared,consumed),('queueInput',queues,consumed_queues)]:
        value=s[field]
        a.demand(value is None or a.exact(value,['binding']) and type(value['binding']) is str and value['binding'] in bindings)
        if value is not None:
            if field=='queueInput':a.demand(value['binding'] not in seen)
            seen.add(value['binding'])
    used.update(POLICIES|CAPS|{'host_controls@1','seeded_assignment@1'})
    used.update(kind+'_contributions@1' for kind in s['kinds'] if kind!='text')
    known[s['id']]=s


def valid_queue(q):
    if not a.exact(q,['ref','order','canonical','notBefore']):return False
    ref=q['ref'];order=q['order']
    return (a.exact(ref,['instance','source']) and c.uuid_urn(ref['instance']) and voting.name(ref['source'])
        and type(order) is list and 0<=len(order)<=100 and all(a.text(actor) and actor!='system' for actor in order) and len(set(order))==len(order)
        and (q['canonical'] is None or a.exact(q['canonical'],['instance','source','itemId']) and c.uuid_urn(q['canonical']['instance']) and voting.name(q['canonical']['source']) and a.text(q['canonical']['itemId']))
        and (q['notBefore'] is None or a.integer(q['notBefore'])))


def initialize(e,bindings,authorize,restored):
    e.authorize_queue=authorize
    declared=e.package.get('queueInputs',{})
    supplied=e.state.get('queueBindings',{}) if restored and bindings is None else ({} if bindings is None else bindings)
    a.demand(type(supplied) is dict and set(supplied)==set(declared) and all(valid_queue(q) for q in supplied.values()))
    a.demand(len({(q['ref']['instance'],q['ref']['source']) for q in supplied.values()})==len(supplied))
    if restored:a.demand(supplied==e.state.get('queueBindings',{}))
    for s in e.definitions.values():
        if s['op'] not in OPS or s['queueInput'] is None:continue
        queue=supplied[s['queueInput']['binding']]
        candidate=None if s['input'] is None else e.state['inputBindings'][s['input']['binding']]['candidate']
        a.demand(queue['canonical']==(None if candidate is None else candidate['ref']))
        if not restored:
            a.demand(queue['notBefore'] is not None and e.state['clock']>=queue['notBefore'] and callable(authorize))
            try:attested=authorize(copy.deepcopy(queue),a.bindings(e)) is True
            except Exception:attested=False
            a.demand(attested)
    if declared or any(s['op'] in OPS for s in e.definitions.values()):
        if not restored:e.state['queueBindings']=copy.deepcopy(supplied)


def authorize_expansion(e,actors):
    current=a.bindings(e)
    if all(actor in current for actor in actors):return True
    queues=e.state.get('queueBindings',{})
    if not queues:return True
    if not callable(e.authorize_queue):return False
    viewers=list(dict.fromkeys(current+actors))
    for queue in queues.values():
        try:
            if e.authorize_queue(copy.deepcopy(queue),viewers[:]) is not True:return False
        except Exception:return False
    return True


def predecessor(e,s):
    return None if s['input'] is None else copy.deepcopy(e.state['inputBindings'][s['input']['binding']]['candidate'])


def eligible(r):return [actor for actor in r['order'] if actor!=r['previousAuthor']]


def rotate(r,actors):
    r['order']=[actor for actor in r['order'] if actor not in actors]+[actor for actor in actors if actor in r['order']]


def finish(e,f,r,status,now,reason=None):
    candidate=r['canonical']
    if status!='selected' and (status=='clock_exhausted' or now+f['step']['retryAfterMs']>a.MAX):status='clock_exhausted';reason='clock_limit'
    r['status']=status;r['reason']=reason;r['closed']=True;r['revealed']=True;r['offer']=None
    r['queue']={'ref':{'instance':e.state['instanceId'],'source':f['step']['id']},'order':r['order'][:],
        'canonical':None if candidate is None else copy.deepcopy(candidate['ref']),
        'notBefore':None if status=='clock_exhausted' else now if status=='selected' else now+f['step']['retryAfterMs']}
    r['output']={'status':status,'reason':reason,'selected':copy.deepcopy(candidate) if status=='selected' else None,'canonical':copy.deepcopy(candidate),'queue':copy.deepcopy(r['queue'])}
    e.next(now)


def offer(e,f,r,now,survivors=None,deadline=None):
    choices=eligible(r)
    if deadline is None and now+f['step']['windowMs']+f['step']['retryAfterMs']>a.MAX:finish(e,f,r,'clock_exhausted',now,'clock_limit');return
    if len(choices)<2:finish(e,f,r,'paused',now,'insufficient_members');return
    if r['failures']>=MAX_FAILURES:finish(e,f,r,'exhausted',now,'failure_budget');return
    if all(actor in r['attempted'] for actor in choices):finish(e,f,r,'exhausted',now,'pass_complete');return
    people=[] if survivors is None else [actor for actor in survivors if actor in choices]
    # Prefer fresh opportunities within this unsuccessful pass, retaining survivors.
    candidates=[actor for actor in choices if actor not in people]
    candidates.sort(key=lambda actor:actor in r['attempted'])
    people+=candidates[:2-len(people)]
    prior=[] if r['offer'] is None else r['offer']['invitations']
    tickets=[]
    for actor in people:
        existing=next((ticket for ticket in prior if ticket['actor']==actor),None) if survivors is not None and actor in survivors else None
        if existing is None:
            r['nextKey']+=1;existing={'actor':actor,'key':r['nextKey'],'opensAt':now}
        tickets.append(copy.deepcopy(existing))
    r['generation']+=1
    r['offer']={'generation':r['generation'],'actors':people,'invitations':tickets,'opensAt':now,'closesAt':now+f['step']['windowMs'] if deadline is None else deadline}


def settle(e,f,now):
    r=e.record(f);s=f['step']
    if 'order' not in r:
        candidate=predecessor(e,s)
        if s['queueInput'] is None:
            order=e.participants[:]
            for i in range(len(order)-1,0,-1):
                j=e.random_index(i+1);order[i],order[j]=order[j],order[i]
        else:
            saved=e.state['queueBindings'][s['queueInput']['binding']]['order']
            order=[actor for actor in saved if actor in e.participants]+[actor for actor in e.participants if actor not in saved]
        r.update(order=order,canonical=candidate,previousAuthor=None if candidate is None else candidate['actor'],attempted=[],failures=0,generation=0,nextKey=0,offer=None,status='open',reason=None,effective={'actors':order[:],'opensAt':now,'closesAt':None})
        offer(e,f,r,now)
    if r['closed']:return 'advance'
    if now>=r['offer']['closesAt']:
        actors=r['offer']['actors'];rotate(r,actors)
        r['attempted']=list(dict.fromkeys(r['attempted']+actors));r['failures']+=1
        offer(e,f,r,now)
    return 'advance' if r['closed'] else 'wait'


def event(e,f,event):
    r=e.record(f);s=f['step'];payload=event['payload'];actor=event['actor'];now=event['at']
    if actor=='system' and event['type']=='roster':
        if not a.exact(payload,['actors']) or not a.valid_control({'actors':payload['actors'],'opensAt':None,'closesAt':None}):return False
        if not c.authorize_expansion(e,payload['actors']) or not authorize_expansion(e,payload['actors']):return False
        members=payload['actors'];old=r['order'][:];current=r['offer'];survivors=[person for person in current['actors'] if person in members]
        r['order']=[person for person in old if person in members]+[person for person in members if person not in old]
        e.state['hostActors']=list(dict.fromkeys(a.bindings(e)+members))
        r['effective']['actors']=r['order'][:]
        if len(survivors)!=2:
            r['attempted']=list(dict.fromkeys(r['attempted']+[person for person in current['actors'] if person not in survivors]));r['failures']+=1
            offer(e,f,r,now,survivors,current['closesAt'])
        return True
    current=r['offer']
    reference=None if r['canonical'] is None else r['canonical']['ref']
    ticket=next((ticket for ticket in current['invitations'] if ticket['actor']==actor),None)
    if ticket is None or not a.integer(payload.get('invitation')) or payload.get('invitation')!=ticket['key'] or payload.get('predecessor')!=reference:return False
    if event['type']=='decline' and a.exact(payload,['invitation','predecessor']):
        rotate(r,[actor]);r['attempted']=list(dict.fromkeys(r['attempted']+[actor]));r['failures']+=1
        offer(e,f,r,now,[person for person in current['actors'] if person!=actor],current['closesAt']);return True
    if event['type']!='submit' or not a.exact(payload,['invitation','predecessor','itemId','value']) or not a.text(payload['itemId']) or not a.valid_value(e,actor,payload['value'],s['kinds']):return False
    entry={'actor':actor,'itemId':payload['itemId'],'value':copy.deepcopy(payload['value'])}
    r['entries'].append(entry);r['canonical']=c.qualified(e,r,entry)
    loser=next(person for person in current['actors'] if person!=actor)
    r['order']=[loser]+[person for person in r['order'] if person not in [loser,actor]]+[actor]
    finish(e,f,r,'selected',now);return True


def projection(e,r,item,actor):
    item.update(status=r['status'],reason=r['reason'],offer=copy.deepcopy(r['offer']),canonical=copy.deepcopy(r['canonical']),eligible=r['offer'] is not None and actor in r['offer']['actors'])
    item['entries']=[c.qualified(e,r,entry) for entry in r['entries']]
    if r['closed']:item['output']=copy.deepcopy(r['output'])
