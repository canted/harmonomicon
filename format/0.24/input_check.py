"""Qualified input/continuation witnesses and fail-closed host authority checks.

These test the language's observable guarantees. Trusted fixtures model the
host's entire attestation; actual source lookup/media grants use durable trials.
"""
import copy
import json
import subprocess
from pathlib import Path
from runtime import Engine, run

HERE = Path(__file__).resolve().parent
INSTANCE = 'urn:uuid:11111111-1111-4111-8111-111111111111'
OTHER_INSTANCE = 'urn:uuid:33333333-3333-4333-8333-333333333333'


def cases():
    return json.loads((HERE/'conformance/input-cases.json').read_text())


def request(case):
    # JSON round-trip deliberately keeps caller bindings and trusted attestations
    # independent. Forging a caller snapshot must not also forge test authority.
    result = {k:v for k,v in case.items() if k not in ['id','definition','checks','stateChecks','outcomes']}
    result['package'] = case['definition']
    return json.loads(json.dumps(result))


def at_path(value, path):
    for key in path:
        value = value[key]
    return value


def event(identifier, actor, at, step, payload=None, kind='submit'):
    return dict(eventId=identifier,actor=actor,at=at,step=step,
                payload={} if payload is None else payload,type=kind)


def control(actors, opening=None, closing=None):
    return dict(actors=list(actors),opensAt=opening,closesAt=closing)


def record(result, op):
    return next(row for row in result['state']['records'] if row['op']==op)


def fixture(case, node):
    req = request(case)
    result = run(req)
    assert result == node(req), (case['id'],'independent engine disagreement')
    assert 'outcomes' in result, (case['id'],result)
    assert result['outcomes'] == case['outcomes'], (case['id'],result.get('outcomes'))
    for check in case['checks']:
        view = result['views'][check['after']][check['actor']]
        if check.get('missing'):
            try: at_path(view,check['path'])
            except (KeyError,IndexError): pass
            else: raise AssertionError((case['id'],'unexpected disclosure',check))
        else:
            assert at_path(view,check['path']) == check['equals'], (case['id'],check,view)
    for check in case['stateChecks']:
        assert at_path(result['state'],check['path']) == check['equals'], (case['id'],'saved binding changed',check)
    for cut in range(len(req['events'])+1):
        prefix = run(dict(req,events=req['events'][:cut]))
        restored = dict(req,state=prefix['state'],events=req['events'][cut:])
        after = run(restored)
        assert after == node(restored), (case['id'],'recovery parity',cut)
        assert after['state'] == result['state'], (case['id'],'recovery changed result',cut)
    return result


def definition_negatives(node, schema=None):
    variants, structural = [], []
    def bad(change, structural_error=False, base=0):
        p = copy.deepcopy(cases()[base]['definition'])
        change(p)
        variants.append(p)
        if structural_error: structural.append(p)
    for token in ['artifact_pool@3','vote@2','tally@3','select@2','present@2','host_controls@1','contribution_inputs@1','policy:most_votes@1']:
        bad(lambda p,t=token:p['requires'].remove(t))
    bad(lambda p:p['requires'].remove('image_contributions@1'),base=1)
    bad(lambda p:p['requires'].remove('audio_contributions@1'),base=2)
    bad(lambda p:p['requires'].remove('policy:random_candidate@1'),base=2)
    bad(lambda p:p['requires'].remove('policy:retain_input@1'),base=1)
    bad(lambda p:p['requires'].remove('policy:random_tie@1'),base=7)
    bad(lambda p:p.update(inputs=[]),True)
    bad(lambda p:p.update(inputs=True),True)
    bad(lambda p:p['inputs'].update({'bad-name':{'type':'contribution','kinds':['text']}}),True)
    bad(lambda p:p.update(inputs={'seed'+str(i):{'type':'contribution','kinds':['text']} for i in range(9)}),True)
    bad(lambda p:p['inputs']['seed'].update(type='lookup'),True)
    bad(lambda p:p['inputs']['seed'].update(kinds=[]),True)
    bad(lambda p:p['inputs']['seed'].update(kinds=['text','text']),True)
    bad(lambda p:p['inputs']['seed'].update(kinds=['video']),True)
    bad(lambda p:p['inputs']['seed'].update(optional=True),True)
    bad(lambda p:p['inputs']['seed'].pop('type'),True)
    bad(lambda p:p['inputs'].update(unused={'type':'contribution','kinds':['text']}))
    bad(lambda p:p['runbook']['steps'][0].update(input={'binding':'unknown'}))
    bad(lambda p:p['runbook']['steps'][0].update(input={'binding':1}),True)
    bad(lambda p:p['runbook']['steps'][0].update(input={'value':{'kind':'text','text':'Anonymous seed'}}),True)
    bad(lambda p:p['runbook']['steps'][0].update(input={'binding':'seed','result':'one_choice'}),True)
    bad(lambda p:p['runbook']['steps'][0].update(input={'result':'one_choice'}))
    bad(lambda p:p['runbook']['steps'][0].update(kinds=['video']),True)
    bad(lambda p:p['runbook']['steps'][0].update(perActor=2),True)
    bad(lambda p:p['runbook']['steps'][0].update(round='round-one'),True)
    bad(lambda p:p['runbook']['steps'][5].update(round='round_one'),base=1)
    bad(lambda p:p['runbook']['steps'][5].update(input={'result':'one_totals'}),base=1)
    bad(lambda p:p['runbook']['steps'][5].update(input={'result':'two_choice'}),base=1)
    bad(lambda p:p['runbook']['steps'][1].update(candidates={'options':[{'id':'a','label':'A'},{'id':'b','label':'B'}]}),True)
    bad(lambda p:p['runbook']['steps'][1].update(candidates={'source':'continuations','instance':INSTANCE}),True)
    bad(lambda p:p['runbook']['steps'][1].update(candidates={'source':'next'}))
    bad(lambda p:p['runbook']['steps'][1].update(changes='replace_ballot_workflow'),True)
    bad(lambda p:p['runbook']['steps'][1].update(ballots='anonymous'),True)
    bad(lambda p:p['runbook']['steps'][2].update(source='continuations'))
    bad(lambda p:p['runbook']['steps'][3].update(source='vote'))
    bad(lambda p:p['runbook']['steps'][3].update(policy='policy:count_with_expressions@1'),True)
    bad(lambda p:p['runbook']['steps'][3].update(ties='organizer_then_timeout'),True)
    bad(lambda p:p['runbook']['steps'][3].update(noVotes='winner'),True)
    bad(lambda p:p['runbook']['steps'][3].update(noVotes=True),True)
    bad(lambda p:p['runbook']['steps'][3].update(noCandidates='retain_input'),True)
    bad(lambda p:p['runbook']['steps'][4].update(source='vote'))
    bad(lambda p:p['runbook']['steps'][4].update(audience='push'),True)
    bad(lambda p:p['runbook']['steps'][4].update(prompt={'template':'${chosen}'}),True)
    bad(lambda p:p.update(hostBindings={'seed':{'instance':'local-name','result':'choice'}}),True)
    def retained_null(p):
        p.pop('inputs');p['runbook']['steps'][0]['input']=None
        p['runbook']['steps'][3]['noVotes']='retain_input';p['requires'].append('policy:retain_input@1')
    bad(retained_null)
    def vote_on_old_pool(p):
        p.pop('inputs');p['runbook']['steps'][0].update(op='artifact_pool@2',input=None)
        p['requires'].append('artifact_pool@2')
    bad(vote_on_old_pool)
    def nested(p):
        p['runbook']['steps']=[{'id':'each','op':'for_each@1','over':'participants','steps':p['runbook']['steps']}]
        p['requires'].append('for_each@1')
    bad(nested,True)
    def wrong_reveal(p):
        p['runbook']['steps'].append({'id':'reveal','op':'reveal_ballots@2','source':'one_totals'})
        p['requires'].append('reveal_ballots@2')
    bad(wrong_reveal)
    def missing_reveal(p):
        p['runbook']['steps'].append({'id':'reveal','op':'reveal_ballots@2','source':'vote'})
    bad(missing_reveal)
    for i,p in enumerate(variants):
        assert run({'action':'validate','package':p}) == node({'action':'validate','package':p}) == {'outcome':'invalid_package'}, ('input definition',i)
    if schema is not None:
        import jsonschema
        validator = jsonschema.Draft202012Validator(schema)
        for p in structural: assert list(validator.iter_errors(p)), ('schema accepted malformed input definition',p)
    return len(variants),len(structural)


def setup_negatives(node):
    base = request(cases()[0]);base['events']=[]
    variants = []
    def bad(change, source=base):
        r=json.loads(json.dumps(source));change(r);variants.append(r)
    bad(lambda r:r.pop('instanceId'))
    for value in ['local-name',INSTANCE.upper(),INSTANCE+'\n',INSTANCE.replace('urn:uuid:',''),1]:
        bad(lambda r,v=value:r.update(instanceId=v))
    bad(lambda r:r.pop('inputBindings'))
    for bindings in [{},None,[],{'unknown':base['inputBindings']['seed']}]:
        bad(lambda r,b=bindings:r.update(inputBindings=copy.deepcopy(b)))
    bad(lambda r:r['inputBindings'].update(extra=copy.deepcopy(r['inputBindings']['seed'])))
    bad(lambda r:r['inputBindings']['seed'].pop('via'))
    bad(lambda r:r['inputBindings']['seed'].update(authority=True))
    bad(lambda r:r['inputBindings']['seed']['candidate'].update(author='copied label'))
    for key,value in [('instance',OTHER_INSTANCE),('source','other_source'),('itemId','other_item')]:
        bad(lambda r,k=key,v=value:r['inputBindings']['seed']['candidate']['ref'].update({k:v}))
    bad(lambda r:r['inputBindings']['seed']['candidate']['ref'].update(instance=INSTANCE.upper()))
    bad(lambda r:r['inputBindings']['seed']['candidate']['ref'].update(source='source:0'))
    bad(lambda r:r['inputBindings']['seed']['candidate']['ref'].update(itemId=0))
    bad(lambda r:r['inputBindings']['seed']['candidate']['ref'].update(round='opening_round'))
    bad(lambda r:r['inputBindings']['seed']['candidate']['ref'].pop('instance'))
    for actor in ['another_artist','system',False,'']:
        bad(lambda r,a=actor:r['inputBindings']['seed']['candidate'].update(actor=a))
    bad(lambda r:r['inputBindings']['seed']['candidate']['value'].update(text='Forged starting value'))
    bad(lambda r:r['inputBindings']['seed']['candidate']['value'].update(text=''))
    bad(lambda r:r['inputBindings']['seed']['candidate']['value'].update(text='bad\ud800'))
    bad(lambda r:r['inputBindings']['seed']['candidate']['value'].update(metadata='hidden'))
    bad(lambda r:r['inputBindings']['seed']['candidate'].update(value={'kind':'image','ref':'new:photo'}))
    for value in ['another_round','bad-round',False]:
        bad(lambda r,v=value:r['inputBindings']['seed']['candidate'].update(round=v))
    for key,value in [('instance',OTHER_INSTANCE),('source','other_source'),('itemId','other_item'),('round','other_round')]:
        # Even a host attestation cannot make a direct pointer contradict origin.
        def contradictory(r,k=key,v=value):
            r['inputBindings']['seed']['via'][k]=v
            r['trustedInputs'][0]['binding']=copy.deepcopy(r['inputBindings']['seed'])
        bad(contradictory)
    bad(lambda r:r['inputBindings']['seed']['via'].update(result='choice'))
    bad(lambda r:r['inputBindings']['seed']['via'].pop('round'))
    bad(lambda r:r.update(trustedInputs=[]))
    for ready in [False,1,'true']:
        bad(lambda r,v=ready:r['trustedInputs'][0].update(ready=v))
    bad(lambda r:r['trustedInputs'][0].update(permission='organizer'))
    for actor in ['a','organizer','observer']:
        bad(lambda r,a=actor:r['trustedInputs'][0]['viewers'].remove(a))
    bad(lambda r:r['trustedInputs'][0].update(viewers='a,b,c,organizer,observer'))
    media_base=request(cases()[1]);media_base['events']=[]
    bad(lambda r:r['inputBindings']['seed']['candidate']['value'].update(ref='wrong-owned-media'),media_base)
    bad(lambda r:r['inputBindings']['seed']['candidate']['value'].update(kind='audio'),media_base)
    bad(lambda r:r['inputBindings']['seed']['candidate']['value'].update(ref='x'*257),media_base)
    audio_base=request(cases()[2]);audio_base['events']=[]
    bad(lambda r:r['inputBindings']['seed']['via'].update(instance=OTHER_INSTANCE),audio_base)
    bad(lambda r:r['inputBindings']['seed']['via'].update(result='not_the_actual_choice'),audio_base)
    bad(lambda r:r['inputBindings']['seed']['via'].update(round='wrong_handoff_round'),audio_base)
    for i,r in enumerate(variants):
        assert run(r) == node(r) == {'outcome':'invalid_setup'}, ('input setup',i)
    # Stored binding and instance identity are immutable, while trusted restore
    # needs no fresh source-registry lookup or replacement callback.
    initial=run(base)
    restored=dict(base,state=initial['state'],trustedInputs=[],events=[event('read','system',0,None,kind='tick')])
    restored.pop('inputBindings');restored.pop('instanceId')
    assert run(restored)==node(restored) and run(restored)['outcomes']==['accepted']
    changed=dict(restored,instanceId=OTHER_INSTANCE)
    assert run(changed)==node(changed)=={'outcome':'invalid_setup'}
    forged=copy.deepcopy(base['inputBindings']);forged['seed']['candidate']['actor']='replacement_artist'
    changed=dict(restored,inputBindings=forged)
    assert run(changed)==node(changed)=={'outcome':'invalid_setup'}
    return len(variants)


def engine_for(req, callback=None, state=None):
    return Engine(req['package'],req['participants'],req['organizer'],
                  state=state,host_inputs=req.get('hostInputs'),
                  instance_id=req.get('instanceId'),input_bindings=req.get('inputBindings'),
                  authorize_input=callback)


def callback_contracts():
    req=request(cases()[0]);req['events']=[]
    required=set(['a','b','c','organizer','observer'])
    calls=[]
    def attest(binding,viewers):
        calls.append((copy.deepcopy(binding),set(viewers)))
        return binding==req['inputBindings']['seed'] and set(viewers)==required
    valid=engine_for(req,attest)
    assert calls and all(b==req['inputBindings']['seed'] and v==required for b,v in calls)
    tests=[]
    def throwing(binding,viewers):raise RuntimeError('source registry unavailable')
    for callback in [None,lambda b,v:False,lambda b,v:1,throwing]:
        try:engine_for(req,callback)
        except (ValueError,TypeError):tests.append(False)
        else:tests.append(True)
    assert tests==[False]*4
    def mutate(binding,viewers):
        binding['candidate']['actor']='invented author';viewers.append('invented viewer');return True
    protected=engine_for(req,mutate)
    assert protected.state['inputBindings']==req['inputBindings']
    assert 'invented viewer' not in protected.state['hostActors']
    # Configure exceptions reject, preserve actor bindings and current controls.
    before=copy.deepcopy(valid.state)
    valid.authorize_input=throwing
    change=event('add-viewer','system',1,'continuations',control(['a','b','c','unauthorized'],0,10),'configure')
    assert valid.event(change)=='rejected'
    assert valid.state['hostActors']==before['hostActors'] and valid.state['controls']==before['controls']
    try:valid.view('unauthorized')
    except ValueError:pass
    else:raise AssertionError('denied viewer acquired a projection')
    # A trusted restored state can be opened without attestation, but cannot add
    # a new viewer until the callback grants access to all retained snapshots.
    restored=engine_for(req,None,state=before)
    assert restored.state['inputBindings']==before['inputBindings']
    assert restored.event(change)=='rejected' and 'unauthorized' not in restored.state['hostActors']
    script=r"""
import fs from 'node:fs';
import {Engine} from './runtime.mjs';
const q=JSON.parse(fs.readFileSync(0,'utf8'));
const make=(cb,state=null)=>new Engine(q.package,q.participants,q.organizer,0,state,null,null,null,q.hostInputs,null,null,q.instanceId,q.inputBindings,cb);
const required=['a','b','c','organizer','observer'];let calls=[];
const good=make((binding,viewers)=>{calls.push({binding,viewers:[...viewers].sort()});return JSON.stringify(binding)===JSON.stringify(q.inputBindings.seed)&&viewers.length===required.length&&required.every(v=>viewers.includes(v));});
const failed=[null,()=>false,()=>1,()=>{throw new Error('source registry unavailable');}].map(cb=>{try{make(cb);return true;}catch{return false;}});
const protectedState=make((binding,viewers)=>{binding.candidate.actor='invented author';viewers.push('invented viewer');return true;}).state;
const before=structuredClone(good.state);good.authorizeInput=()=>{throw new Error('source registry unavailable');};
const change={eventId:'add-viewer',actor:'system',at:1,step:'continuations',payload:{actors:['a','b','c','unauthorized'],opensAt:0,closesAt:10},type:'configure'};
const denied=good.event(change),actorsSame=JSON.stringify(good.state.hostActors)===JSON.stringify(before.hostActors),controlsSame=JSON.stringify(good.state.controls)===JSON.stringify(before.controls);
let unbound=false;try{good.view('unauthorized');}catch{unbound=true;}
const restored=make(null,before),restoreDenied=restored.event(change);
console.log(JSON.stringify({calls,failed,protectedBindings:protectedState.inputBindings,protectedActors:protectedState.hostActors,denied,actorsSame,controlsSame,unbound,restoreDenied,restoredBindings:restored.state.inputBindings}));
"""
    output=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=HERE,input=json.dumps(req),text=True))
    assert output['failed']==tests and output['calls']
    assert all(x['binding']==req['inputBindings']['seed'] and set(x['viewers'])==required for x in output['calls'])
    assert output['protectedBindings']==req['inputBindings'] and 'invented viewer' not in output['protectedActors']
    assert output['denied']==output['restoreDenied']=='rejected'
    assert output['actorsSame'] and output['controlsSame'] and output['unbound']
    assert output['restoredBindings']==req['inputBindings']


def authority_and_races(node):
    req=request(cases()[0]);req['events']=[]
    initial=run(req);assert initial==node(req)
    change=event('add-viewer','system',1,'continuations',control(['a','b','c','new_viewer'],0,10),'configure')
    denied=dict(req,state=initial['state'],events=[change])
    result=run(denied);assert result==node(denied) and result['outcomes']==['rejected']
    assert result['state']['hostActors']==initial['state']['hostActors'] and result['state']['controls']==initial['state']['controls']
    allowed=copy.deepcopy(denied);allowed['trustedInputs'][0]['viewers'].append('new_viewer')
    result=run(allowed);assert result==node(allowed) and result['outcomes']==['accepted']
    assert result['views'][0]['new_viewer']['records'][0]['input']['candidate']==req['inputBindings']['seed']['candidate']
    forged=event('forged-authority','a',1,'continuations',change['payload'],'configure')
    injected=event('inject-binding','a',1,'continuations',{'binding':req['inputBindings']['seed'],'instance':OTHER_INSTANCE},'bind')
    result=run(dict(req,events=[forged,injected]));assert result==node(dict(req,events=[forged,injected])) and result['outcomes']==['rejected']*2
    # Denial of any one retained input rejects adding a viewer, even when that
    # input is used only by a future phase. Each named input is immutable/reusable.
    two=copy.deepcopy(req);two['package']['inputs']['other']={'type':'contribution','kinds':['text']}
    first=two['package']['runbook']['steps'][0]
    second=copy.deepcopy(first);second.update(id='later',round='later_round',input={'binding':'other'})
    two['package']['runbook']['steps'].append(second)
    b=copy.deepcopy(two['inputBindings']['seed']);b['candidate']['ref']['itemId']='other';b['via']['itemId']='other';b['candidate']['value']['text']='Another shared source'
    two['inputBindings']['other']=copy.deepcopy(b);two['trustedInputs'].append({'binding':copy.deepcopy(b),'viewers':list(two['trustedInputs'][0]['viewers']),'ready':True})
    two['trustedInputs'][0]['viewers'].append('new_viewer')
    result=run(dict(two,events=[change]));assert result==node(dict(two,events=[change])) and result['outcomes']==['rejected']
    assert 'new_viewer' not in result['state']['hostActors']
    two['trustedInputs'][1]['viewers'].append('new_viewer')
    result=run(dict(two,events=[change]));assert result==node(dict(two,events=[change])) and result['outcomes']==['accepted']
    # Reusing the same declared input in another round needs no rebinding.
    repeat=copy.deepcopy(req);later=copy.deepcopy(repeat['package']['runbook']['steps'][0]);later.update(id='later',round='later_round')
    repeat['package']['runbook']['steps'].append(later);repeat['hostInputs']['later']=control('abc',20,30)
    repeat['events']=[event('finish-first','system',20,None,kind='tick')]
    result=run(repeat);assert result==node(repeat)
    assert result['views'][0]['a']['records'][-1]['input']['candidate']==req['inputBindings']['seed']['candidate']
    # Full retained-input authorization also applies to a later unchanged window
    # operation; choosing its old version cannot bypass the new instance contract.
    legacy=copy.deepcopy(req)
    legacy['package']['runbook']['steps'].append({'id':'notes','op':'artifact_pool@1','prompt':'Write a reflection.','kinds':['text'],'visibility':'group'})
    legacy['package']['requires'].append('artifact_pool@1')
    legacy['hostInputs']['notes']=control('abc',20,40)
    legacy['events']=[event('reach-legacy','system',20,None,kind='tick')]
    prefix=run(legacy);assert prefix==node(legacy) and prefix['views'][0]['a']['step']=='notes'
    old_change=event('old-op-viewer','system',21,'notes',control(['a','b','c','late_viewer'],20,40),'configure')
    denied=dict(legacy,state=prefix['state'],events=[old_change])
    result=run(denied);assert result==node(denied) and result['outcomes']==['rejected']
    assert 'late_viewer' not in result['state']['hostActors']
    allowed=copy.deepcopy(denied);allowed['trustedInputs'][0]['viewers'].append('late_viewer')
    result=run(allowed);assert result==node(allowed) and result['outcomes']==['accepted']
    assert result['views'][0]['late_viewer']['records'][0]['input']['candidate']==req['inputBindings']['seed']['candidate']
    # The eight-declaration limit is usable: all eight inputs are required,
    # attested and explicitly consumed, rather than merely rejecting nine names.
    maximum=copy.deepcopy(req);maximum['package']['inputs']={};maximum['package']['runbook']['steps']=[]
    maximum['inputBindings']={};maximum['trustedInputs']=[];maximum['hostInputs']={}
    for i in range(8):
        key='seed'+str(i);maximum['package']['inputs'][key]={'type':'contribution','kinds':['text']}
        step=copy.deepcopy(req['package']['runbook']['steps'][0]);step.update(id='pool'+str(i),round='round'+str(i),input={'binding':key})
        maximum['package']['runbook']['steps'].append(step);maximum['hostInputs'][step['id']]=control('abc',i*10,(i+1)*10)
        b=copy.deepcopy(req['inputBindings']['seed']);b['candidate']['ref']['itemId']='origin'+str(i);b['via']['itemId']='origin'+str(i)
        maximum['inputBindings'][key]=copy.deepcopy(b);maximum['trustedInputs'].append({'binding':copy.deepcopy(b),'viewers':['a','b','c','organizer'],'ready':True})
    maximum['events']=[event('all-inputs','system',80,None,kind='tick')]
    result=run(maximum);assert result==node(maximum) and result['outcomes']==['accepted']
    assert len(result['state']['inputBindings'])==8 and result['views'][0]['a']['phase']=='complete'
    assert [row['input']['candidate'] for row in result['views'][0]['a']['records']]==[maximum['inputBindings']['seed'+str(i)]['candidate'] for i in range(8)]
    # Same-timestamp close/submission and final voter withdrawal use ordered
    # accepted actions; the source input never changes during those races.
    source=event('source','a',1,'continuations',{'itemId':'new','value':{'kind':'text','text':'A new continuation'}})
    close=event('close','system',1,'continuations',kind='close')
    for events,expected,count in [([source,close],['accepted','accepted'],1),([close,source],['accepted','rejected'],0)]:
        result=run(dict(req,events=events));assert result==node(dict(req,events=events)) and result['outcomes']==expected
        assert len(record(result,'vote@2')['candidates'])==count
    voting=dict(req,events=[source,event('open','system',10,None,kind='tick'),event('vote','a',12,'vote',{'candidate':{'instance':INSTANCE,'source':'continuations','itemId':'new'}}),event('withdraw','system',13,'vote',control(['b','c','observer'],12,20),'configure'),event('boundary','b',20,'vote',{'candidate':{'instance':INSTANCE,'source':'continuations','itemId':'new'}})])
    result=run(voting);assert result==node(voting) and result['outcomes']==['accepted']*4+['rejected']
    assert record(result,'select@2')['output']['status']=='no_votes' and record(result,'tally@3')['output']['totalVotes']==0
    # Source-author and voter eligibility remain independent in the new chain.
    # Withdrawing a source author before closure removes that candidate without
    # erasing the private accepted contribution or forbidding that actor to vote.
    c_a={'ref':{'instance':INSTANCE,'source':'continuations','itemId':'A'},'actor':'a','value':{'kind':'text','text':'A continuation'},'round':'round_one'}
    eligibility=dict(req,events=[
        event('source-a','a',1,'continuations',{'itemId':'A','value':c_a['value']}),
        event('source-b','b',1,'continuations',{'itemId':'B','value':{'kind':'text','text':'Withdrawn continuation'}}),
        event('withdraw-author','system',2,'continuations',control(['a'],0,10),'configure'),
        event('publish','system',10,None,kind='tick'),
        event('ineligible-source','b',12,'vote',{'candidate':{'instance':INSTANCE,'source':'continuations','itemId':'B'}}),
        event('still-voter','b',12,'vote',{'candidate':c_a['ref']}),
        event('result','system',20,None,kind='tick')])
    result=run(eligibility);assert result==node(eligibility) and result['outcomes']==['accepted']*4+['rejected','accepted','accepted']
    assert record(result,'vote@2')['candidates']==[c_a]
    assert result['views'][3]['b']['records'][0]['entries']==[{'actor':'b','itemId':'B','value':{'kind':'text','text':'Withdrawn continuation'}}]
    assert record(result,'select@2')['output']=={'counts':[{'candidate':c_a,'count':1}],'totalVotes':1,'status':'selected','selected':c_a,'tied':[],'basis':'most_votes'}
    # Unsupported capability negotiation creates no instance state.
    p=copy.deepcopy(req['package']);p['requires'].append('cross_provider_trust@1')
    unsupported=dict(req,package=p)
    assert run(unsupported)==node(unsupported)=={'outcome':'unsupported','missing':['cross_provider_trust@1']}


def random_properties(node):
    all_cases=cases()
    random_case=next(c for c in all_cases if c['id']=='audio-handoff-random-no-vote-over-typed-candidates')
    req=request(random_case)
    for choice in range(3):
        r=dict(req,tieChoices=[choice]);result=run(r);assert result==node(r)
        output=record(result,'select@2')['output']
        assert output['selected']==output['counts'][choice]['candidate'] and result['state']['tieDraws']==1
    for case in all_cases:
        if case['id'].startswith('zero-candidates-') or case['id'] in ['single-candidate-random-no-vote-needs-no-draw','retained-image-origin-and-explicit-next-round-pointer','default-no-vote-blocked-continuation','explicit-unresolved-no-vote-blocked-continuation']:
            r=request(case);result=run(r);assert result==node(r) and result['state'].get('tieDraws',0)==0
    # Invalid trusted draws fail rather than produce an out-of-set choice.
    for choice in [3,4]:
        bad=dict(req,tieChoices=[choice])
        try:run(bad)
        except (ValueError,TypeError,KeyError):pass
        else:raise AssertionError('invalid draw accepted')
        assert node(bad)=={'outcome':'invalid_package'}
    # Host random streams may differ. Independently check membership and durable
    # exact output after read/retry/restart, then transfer a committed choice.
    for name in ['audio-handoff-random-no-vote-over-typed-candidates','positive-random-tie-overrides-no-vote-policy']:
        r=request(next(c for c in all_cases if c['id']==name));r.pop('tieChoices',None)
        for runner in [run,node]:
            for _ in range(4):
                result=runner(r);output=record(result,'select@2')['output']
                eligible=output['tied'] or [row['candidate'] for row in output['counts']]
                assert output['selected'] in eligible and result['state']['tieDraws']==1
                replay=copy.deepcopy(r['events'][0]);replay['at']=21
                resumed=dict(r,state=result['state'],trustedInputs=[],trustedMedia=[],events=[event('read','system',21,None,kind='tick'),replay])
                restored=runner(resumed)
                assert restored['outcomes']==['accepted','replayed'] and record(restored,'select@2')['output']==output and restored['state']['tieDraws']==1
                other=node if runner is run else run
                assert other(resumed)==restored


def schema_checks(schema):
    import jsonschema
    validator=jsonschema.Draft202012Validator(schema)
    for case in cases():validator.validate(case['definition'])
    binding_validator=jsonschema.Draft202012Validator({'$schema':schema['$schema'],'$defs':schema['$defs'],'$ref':'#/$defs/normalizedBinding'})
    for case in cases():
        for b in case.get('inputBindings',{}).values():binding_validator.validate(b)
    b=copy.deepcopy(cases()[0]['inputBindings']['seed'])
    malformed=[]
    for change in [lambda b:b['candidate']['ref'].update(instance=INSTANCE.upper()),lambda b:b['candidate']['ref'].update(instance='local'),lambda b:b['candidate']['ref'].pop('instance'),lambda b:b['candidate']['ref'].update(round='round'),lambda b:b['candidate'].pop('actor'),lambda b:b['candidate'].update(round='bad-round'),lambda b:b['candidate']['value'].update(kind='video'),lambda b:b['via'].update(actor='a'),lambda b:b.pop('via')]:
        v=copy.deepcopy(b);change(v);malformed.append(v)
    for v in malformed:assert list(binding_validator.iter_errors(v)),('qualified binding schema accepted malformed shape',v)
    return len(malformed)


def check(node,schema=None):
    corpus=cases()
    for case in corpus:fixture(case,node)
    invalid,structural=definition_negatives(node,schema)
    setup_count=setup_negatives(node)
    callback_contracts()
    authority_and_races(node)
    random_properties(node)
    if schema is not None:schema_checks(schema)
    print(f'{len(corpus)} qualified-input/fallback traces; {invalid} invalid definitions; '
          f'{structural} package schema negatives; {setup_count} setup/authority negatives; '
          'full-audience callbacks, immutable origins/bindings, configure denial, '
          'qualified stale references, exact fallback matrix, races, every-boundary '
          'recovery and durable random properties pass')
    return invalid


if __name__=='__main__':
    from check import node
    check(node,json.loads((HERE/'package.schema.json').read_text()))
