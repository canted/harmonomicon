"""Typed pool quotas, qualified consumers, private grants and bounded recovery.

Fixtures state expected activity outcomes. Host media attestations stand in for
readiness/ownership registries; SQLite and actual byte grants have separate trials.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path
from runtime import Engine, run
from input_check import at_path, event, control

HERE = Path(__file__).resolve().parent
INSTANCE = 'urn:uuid:11111111-1111-4111-8111-111111111111'
MAX = 9007199254740991


def cases():
    return json.loads((HERE/'conformance/pooling-cases.json').read_text())


def request(case):
    value = {k:v for k,v in case.items() if k not in ['id','definition','checks','stateChecks','outcomes']}
    value['package'] = case['definition']
    # Forging a caller binding cannot also change its authority fixture by alias.
    return json.loads(json.dumps(value))


def find(name):
    return next(c for c in cases() if c['id']==name)


def record(result, op):
    return next(r for r in result['state']['records'] if r['op']==op)


def fixture(case, node):
    req=request(case);result=run(req)
    assert result==node(req), (case['id'],'engine disagreement')
    assert result.get('outcomes')==case['outcomes'], (case['id'],result)
    for assertion in case['checks']:
        view=result['views'][assertion['after']][assertion['actor']]
        if assertion.get('missing'):
            try:at_path(view,assertion['path'])
            except (KeyError,IndexError):pass
            else:raise AssertionError((case['id'],'private value disclosed',assertion))
        else:assert at_path(view,assertion['path'])==assertion['equals'], (case['id'],assertion,view)
    for assertion in case['stateChecks']:
        assert at_path(result['state'],assertion['path'])==assertion['equals'], (case['id'],assertion)
    for cut in range(len(req['events'])+1):
        prefix=run(dict(req,events=req['events'][:cut]))
        resumed=dict(req,state=prefix['state'],events=req['events'][cut:])
        recovered=run(resumed)
        assert recovered==node(resumed), (case['id'],'recovery disagreement',cut)
        assert recovered['state']==result['state'], (case['id'],'recovery changed state',cut)
    return result


def definition_negatives(node,schema=None):
    variants=[];structural=[]
    def bad(change,shape=False,base='equal-value-distinct-candidates-current-votes-private-result'):
        p=copy.deepcopy(find(base)['definition']);change(p);variants.append(p)
        if shape:structural.append(p)
    vote_base='equal-value-distinct-candidates-current-votes-private-result'
    loop_base='typed-reader-private-grant-then-attributed-publication'
    response_base='multiple-items-next-author-earliest-source-and-linked-privacy'
    retained_base='zero-votes-retain_input'
    # Every new operation must be negotiated, including typed body operations.
    for token in ['pool@2','vote@3','tally@4','select@3','present@3','host_controls@1','policy:most_votes@1','private_views@1']:
        bad(lambda p,t=token:p['requires'].remove(t))
    for token in ['for_items@2','assign_item@2','acknowledge@2','reveal_item@2','policy:pool_order@1','policy:claim_reader@1','image_contributions@1']:
        bad(lambda p,t=token:p['requires'].remove(t),base=loop_base)
    for token in ['assign_artifacts@2','artifact_response@2','reveal_artifact_responses@2','policy:next_nonself_item@1','audio_contributions@1']:
        bad(lambda p,t=token:p['requires'].remove(t),base=response_base)
    bad(lambda p:p['requires'].remove('reveal_ballots@3'),base='forbidden-vote-changes-explicit-ballot-release')
    bad(lambda p:p['requires'].remove('policy:random_candidate@1'),base='zero-votes-random')
    bad(lambda p:p['requires'].remove('policy:random_tie@1'),base='positive-random-tie')
    bad(lambda p:p['requires'].remove('policy:retain_input@1'),base=retained_base)
    bad(lambda p:p['requires'].remove('contribution_inputs@1'),base=retained_base)
    for field in ['id','op','prompt','kinds','perActor','visibility']:
        bad(lambda p,f=field:p['runbook']['steps'][0].pop(f),True)
    for quota in [0,9,True,2.5,'2',None]:
        bad(lambda p,q=quota:p['runbook']['steps'][0].update(perActor=q),True)
    for kinds in [[],['text','text'],['video'],['image','integer'],True]:
        bad(lambda p,k=kinds:p['runbook']['steps'][0].update(kinds=k),True)
    for key,value in [('round','bad-round'),('round',True),('input',{'value':{'kind':'text','text':'copied'}}),('input',{'result':'selected','binding':'seed'}),('visibility','anonymous'),('perKind',2),('close','all')]:
        bad(lambda p,k=key,v=value:p['runbook']['steps'][0].update({k:v}),True)
    bad(lambda p:p['runbook']['steps'][0].update(input={'result':'selected'}))
    bad(lambda p:p['runbook']['steps'][0].update(input={'binding':'unknown'}))
    bad(lambda p:p['runbook']['steps'][3].update(noVotes='retain_input'))
    bad(lambda p:p['runbook']['steps'][1].update(candidates={'options':[{'id':'a','label':'A'},{'id':'b','label':'B'}]}),True)
    bad(lambda p:p['runbook']['steps'][1].update(candidates={'source':'selected'}))
    bad(lambda p:p['runbook']['steps'][2].update(source='pieces'))
    bad(lambda p:p['runbook']['steps'][3].update(source='vote'))
    bad(lambda p:p['runbook']['steps'][4].update(source='vote'))
    bad(lambda p:p['runbook']['steps'][4].update(audience='push'),True)
    bad(lambda p:p['runbook']['steps'][4].update(prompt={'template':'${outcome}'}),True)
    bad(lambda p:p['runbook']['steps'][3].update(noVotes='fallback_workflow'),True)
    bad(lambda p:p['runbook']['steps'][3].update(noCandidates='random'),True)
    bad(lambda p:p['runbook']['steps'][3].update(ties='designated_person'),True)
    bad(lambda p:p['runbook']['steps'][1].update(changes='workflow'),True)
    bad(lambda p:p['runbook']['steps'][1].update(ballots='anonymous'),True)
    for change,shape in [
        (lambda p:p['runbook']['steps'][1].update(source='future'),False),
        (lambda p:p['runbook']['steps'][1].update(policy='policy:random_order@1'),True),
        (lambda p:p['runbook']['steps'][1]['steps'][0].update(afterMs=0),True),
        (lambda p:p['runbook']['steps'][1]['steps'][0].update(afterMs=True),True),
        (lambda p:p['runbook']['steps'][1]['steps'][0].update(policy='policy:choose_reader@1'),True),
        (lambda p:p['runbook']['steps'][1]['steps'][1].update(source='pieces'),False),
        (lambda p:p['runbook']['steps'][1]['steps'][2].update(source='claim'),False),
        (lambda p:p['runbook']['steps'].append(dict(id='escaped',op='reveal@1',sources=['read'])),False),
        (lambda p:p['runbook']['steps'][1]['steps'].append(dict(id='nested',op='for_items@2',source='pieces',policy='policy:pool_order@1',steps=copy.deepcopy(p['runbook']['steps'][1]['steps']))),True),
        (lambda p:p['runbook']['steps'][1]['steps'].append(dict(id='nested',op='pool@2',prompt='Not a loop instruction.',kinds=['text'],perActor=1,visibility='private')),True),
        (lambda p:p['runbook']['steps'][1]['steps'][0].update(op='assign_item@1'),True),
        (lambda p:p['runbook']['steps'].append(copy.deepcopy(p['runbook']['steps'][1]['steps'][0])),True),
    ]:bad(change,shape,loop_base)
    # Versioned restrictions reject typed/untyped adapters rather than silently widen.
    def old_pool(p):
        p['runbook']['steps'][0]=dict(id='pieces',op='pool@1',prompt='Text slips',perActor=2,visibility='private',close='organizer',afterMs=None)
        p['requires'].append('pool@1')
    for target in [vote_base,loop_base,response_base]:bad(old_pool,base=target)
    bad(lambda p:(p['runbook']['steps'][1].update(op='vote@2'),p['requires'].append('vote@2')))
    bad(lambda p:(p['runbook']['steps'][1].update(op='for_items@1'),p['requires'].append('for_items@1')),True,loop_base)
    bad(lambda p:(p['runbook']['steps'][1].update(op='assign_artifacts@1',policy='policy:next_nonself_source@1'),p['requires'].extend(['assign_artifacts@1','policy:next_nonself_source@1'])),base=response_base)
    for change,shape in [
        (lambda p:p['runbook']['steps'][1].update(source='future'),False),
        (lambda p:p['runbook']['steps'][1].update(policy='policy:next_nonself_source@1'),True),
        (lambda p:p['runbook']['steps'][1].update(recipients='each_item'),True),
        (lambda p:p['runbook']['steps'][1].update(cardinality='many'),True),
        (lambda p:p['runbook']['steps'][1].update(reuse='balanced'),True),
        (lambda p:p['runbook']['steps'][1].update(unmatched='self'),True),
        (lambda p:p['runbook']['steps'][2].update(source='pieces'),False),
        (lambda p:p['runbook']['steps'][2].update(perActor=2),True),
        (lambda p:p['runbook']['steps'][2].update(kinds=['video']),True),
        (lambda p:p['runbook']['steps'][3].update(source='sources'),False),
    ]:bad(change,shape,response_base)
    def nested(p):
        p['runbook']['steps']=[dict(id='turn',op='for_each@1',over='participants',steps=p['runbook']['steps'])];p['requires'].append('for_each@1')
    bad(nested,True)
    for p in variants:
        req=dict(action='validate',package=p)
        assert run(req)==node(req)=={'outcome':'invalid_package'}, ('invalid typed definition accepted',p)
    if schema is not None:
        import jsonschema
        validator=jsonschema.Draft202012Validator(schema)
        for p in structural:assert list(validator.iter_errors(p)), ('schema accepted malformed typed operation',p)
    return len(variants),len(structural)


def setup_boundaries(node):
    req=request(find('mixed-shared-quota-owned-ready-values-and-retries'));req['events']=[]
    variants=[]
    def bad(change):
        v=copy.deepcopy(req);change(v);variants.append(v)
    for value in [None,'local',INSTANCE.upper(),'urn:uuid:11111111-1111-4111-8111-11111111111g']:
        bad(lambda r,v=value:r.update(instanceId=v))
    for value in [True,['a']]:bad(lambda r,v=value:r.update(hostInputs=v))
    for c in [control(['a','a'],0,10),control(['system'],0,10),control(['x'+str(i) for i in range(101)],0,10),control(['a'],10,10),control(['a'],10,9),control(['a'],True,10),control(['a'],0,MAX+1),dict(control(['a'],0,10),extra=True)]:
        bad(lambda r,v=c:r['hostInputs'].update(pieces=v))
    bad(lambda r:r['hostInputs'].update(unknown=control(['a'],0,10)))
    bad(lambda r:r.update(inputBindings={'undeclared':{}}))
    for r in variants:assert run(r)==node(r)=={'outcome':'invalid_setup'}, ('invalid typed setup accepted',r)
    retained=request(find('zero-votes-retain_input'));retained['events']=[]
    # Forged origin, value, author, round and handoff must fail whole-snapshot authority.
    mutations=[lambda r:r.update(trustedInputs=[]),lambda r:r['inputBindings']['seed']['candidate'].update(actor='a'),lambda r:r['inputBindings']['seed']['candidate'].update(round='copied'),lambda r:r['inputBindings']['seed']['candidate']['value'].update(ref='asset:forged'),lambda r:r['inputBindings']['seed']['candidate']['ref'].update(instance=INSTANCE),lambda r:r['inputBindings']['seed']['via'].update(round='copied'),lambda r:r['hostInputs'].update(next=control(['new_viewer'],0,10))]
    for mutation in mutations:
        v=json.loads(json.dumps(retained));mutation(v)
        assert run(v)==node(v)=={'outcome':'invalid_setup'}, ('new pool bypassed input authority',v)
    # Round null is the omitted default. Quota eight is a valid exact integer.
    valid=copy.deepcopy(req);valid['package']['runbook']['steps'][0].update(round=None,input=None,perActor=8)
    result=run(valid);assert result==node(valid) and result['state']['records'][0]['round'] is None
    return len(variants)+len(mutations)


def ordered_boundaries(node):
    req=request(find('equal-value-distinct-candidates-current-votes-private-result'))
    req['events']=req['events'][:3]+[event('open','system',1,'pieces',kind='close')]
    # Exclusive opening/closing and same-time order remain rules of the activity.
    prefix=run(req);assert prefix==node(req)
    for events,expected in [
        ([event('early','c',1,'vote',{'candidate':{'instance':INSTANCE,'source':'pieces','itemId':'x'}})],['rejected']),
        ([event('settle','system',10,'vote',kind='close'),event('late','a',10,'vote',{'candidate':{'instance':INSTANCE,'source':'pieces','itemId':'x'}})],['rejected','rejected']),
        ([event('ballot','a',2,'vote',{'candidate':{'instance':INSTANCE,'source':'pieces','itemId':'x'}}),event('settle','system',2,'vote',kind='close'),event('change','a',2,'vote',{'candidate':{'instance':INSTANCE,'source':'pieces','itemId':'y'}})],['accepted','accepted','rejected']),
        ([event('settle','system',2,'vote',kind='close'),event('ballot','a',2,'vote',{'candidate':{'instance':INSTANCE,'source':'pieces','itemId':'x'}})],['accepted','rejected']),
    ]:
        r=dict(req,state=prefix['state'],events=events);out=run(r)
        assert out==node(r) and out['outcomes']==expected, ('ordered voting race',out)
    # Configuration is trusted system-only; strict ready/kind/owner registry applies.
    req=request(find('mixed-shared-quota-owned-ready-values-and-retries'));req['events']=[]
    malformed=[{'kind':'text','text':''},{'kind':'text','text':True},{'kind':'image','ref':'asset:image_a','extra':1},{'kind':'image','ref':'asset:unready'},{'kind':'audio','ref':'asset:image_a'},{'kind':'audio','ref':'asset:wrongowner'}]
    req['trustedMedia'] += [{'actor':'a','ref':'asset:unready','kind':'image','ready':False},{'actor':'b','ref':'asset:wrongowner','kind':'audio','ready':True}]
    req['events']=[event('bad'+str(i),'a',0,'pieces',{'itemId':'bad'+str(i),'value':v}) for i,v in enumerate(malformed)]
    req['events'] += [event('forged','a',0,'pieces',control(['new'],0,10),kind='configure'),event('trusted','system',0,'pieces',control(['a','new'],0,10),kind='configure'),event('new','new',0,'pieces',{'itemId':'new','value':{'kind':'text','text':'Accepted'}})]
    r=run(req);assert r==node(req) and r['outcomes']==['rejected']*7+['accepted','accepted']
    # Every unsupported token is negotiated before state or projection creation.
    for token in ['pool@99','video_contributions@1','policy:exposure_balanced@1','unlimited_stream@1']:
        r=copy.deepcopy(req);r['package']['requires'].append(token)
        assert run(r)==node(r)=={'outcome':'unsupported','missing':[token]}


def seeded_assignments(node):
    req=request(find('multiple-items-next-author-earliest-source-and-linked-privacy'))
    req['package']['runbook']['steps']=req['package']['runbook']['steps'][:2]
    req['package']['runbook']['steps'][1]['policy']='policy:seeded_nonself_source@1'
    req['package']['requires']+=['policy:seeded_nonself_source@1','seeded_assignment@1']
    req['events']=req['events'][:6];req['hostInputs'].pop('response');req['seed']=1
    result=run(req);assert result==node(req)
    source=record(result,'pool@2')['entries'];assignments=record(result,'assign_artifacts@2')['assignments']
    assert [r['actor'] for r in assignments]==['a','b','c','d']
    # A small independent oracle exercises the retained exact sampling contract.
    state=1;expected=[]
    for actor in ['a','b','c','d']:
        eligible=[item for item in source if item['actor']!=actor]
        if len(eligible)>1:
            limit=(4294967295//len(eligible))*len(eligible)
            while True:
                state ^= (state<<13)&0xffffffff;state ^= state>>17;state ^= (state<<5)&0xffffffff;state &= 0xffffffff
                if state-1<limit:break
            selected=eligible[(state-1)%len(eligible)]
        else:selected=eligible[0]
        expected.append((actor,selected['itemId']))
    assert [(a['actor'],a['candidate']['ref']['itemId']) for a in assignments]==expected
    assert result['state']['randomState']==state
    for cut in range(len(req['events'])+1):
        initial=run(dict(req,events=req['events'][:cut]))
        restored=dict(req,state=initial['state'],events=req['events'][cut:]);restored.pop('seed')
        recovered=run(restored)
        assert recovered==node(restored) and recovered['state']==result['state']
    for seed in [None,0,True,1.5,4294967296]:
        invalid=dict(req,seed=seed,events=[])
        assert run(invalid)==node(invalid)=={'outcome':'invalid_setup'}
    wrong=dict(req,state=result['state'],seed=2,events=[])
    assert run(wrong)==node(wrong)=={'outcome':'invalid_setup'}
    one=copy.deepcopy(req);one['events']=one['events'][:1]+[event('closed','system',1,'pieces',kind='close')]
    r=run(one);assert r==node(one) and r['state']['randomState']==1
    assert record(r,'assign_artifacts@2')['unmatched']==['a']
    return 6


def random_properties(node):
    for name in ['positive-random-tie','zero-votes-random']:
        req=request(find(name));req.pop('tieChoices')
        # A dependent open pool is fine; selection is already settled and saved.
        for runner in [run,node]:
            result=runner(req);output=record(result,'select@3')['output']
            eligible=output['tied'] or [r['candidate'] for r in output['counts']]
            assert output['selected'] in eligible and result['state']['tieDraws']==1
            retry=copy.deepcopy(req['events'][0]);retry['at']=11
            resumed=dict(req,state=result['state'],events=[event('read','system',11,None,kind='tick'),retry])
            recovered=runner(resumed)
            assert recovered['outcomes']==['accepted','replayed']
            assert record(recovered,'select@3')['output']==output and recovered['state']['tieDraws']==1
            other=node if runner is run else run
            assert other(resumed)==recovered


def maximum_bounds(node):
    req=request(find('empty-typed-loop-creates-no-iteration'));req['events']=[]
    # Eight hundred items remain possible even with one original participant and
    # one hundred trusted effective actors. Budget must not use roster length.
    req['participants']=['original'];actors=['p'+str(i) for i in range(100)]
    req['hostInputs']['pieces']=control(actors,0,MAX-8000)
    valid=run(req);assert valid==node(req) and 'state' in valid
    invalid=copy.deepcopy(req);invalid['hostInputs']['pieces']['closesAt']=MAX-7999
    assert run(invalid)==node(invalid)=={'outcome':'invalid_setup'}
    invalid=copy.deepcopy(req);invalid['startedAt']=MAX-7999
    assert run(invalid)==node(invalid)=={'outcome':'invalid_setup'}
    configured=dict(req,state=valid['state'],events=[event('too_late','system',0,'pieces',control(actors,0,MAX-7999),kind='configure')])
    result=run(configured);assert result==node(configured) and result['outcomes']==['rejected']
    # Avoid retaining 800*102 complete actor views in the CLI. Direct engine
    # probes still compare final full state and selected complete projections.
    req['hostInputs']['pieces']=control(actors,0,10)
    events=[event('item'+str(i)+'_'+str(j),actor,0,'pieces',{'itemId':str(i)+'_'+str(j),'value':{'kind':'text','text':'Piece'}}) for i,actor in enumerate(actors) for j in range(8)]
    events += [event('closed','system',1,'pieces',kind='close'),event('jump','system',8001,None,kind='tick')]
    engine=Engine(req['package'],req['participants'],req['organizer'],host_inputs=req['hostInputs'],instance_id=INSTANCE)
    outcomes=[engine.event(e) for e in events]
    expected=dict(outcomes=outcomes,state=engine.state,views={a:engine.view(a) for a in ['p0','p99','organizer']})
    script="""import fs from 'node:fs';import {Engine} from './runtime.mjs';
const r=JSON.parse(fs.readFileSync(0,'utf8'));const e=new Engine(r.package,r.participants,r.organizer,0,null,null,null,null,r.hostInputs,null,null,r.instanceId);
const outcomes=r.events.map(x=>e.event(x));console.log(JSON.stringify({outcomes,state:e.state,views:Object.fromEntries(['p0','p99','organizer'].map(a=>[a,e.view(a)]))}));"""
    actual=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=HERE,input=json.dumps(dict(req,events=events)),text=True))
    assert actual==expected and outcomes==['accepted']*802
    assert len(engine.state['typedItems']['sharing']['items'])==800
    assert len(engine.state['plan'])==2401 and engine.view('p0')['phase']=='complete'
    # Stored private snapshots survive cross-engine restore after expansion.
    restored=dict(req,state=expected['state'],events=[])
    assert run(restored)==node(restored) and run(restored)['state']==expected['state']
    return 3


def check(node,schema=None):
    corpus=cases()
    for case in corpus:fixture(case,node)
    invalid,structural=definition_negatives(node,schema)
    setup=setup_boundaries(node)+seeded_assignments(node)+maximum_bounds(node)
    ordered_boundaries(node);random_properties(node)
    if schema is not None:
        import jsonschema
        validator=jsonschema.Draft202012Validator(schema)
        for case in corpus:validator.validate(case['definition'])
        null_round=copy.deepcopy(corpus[0]['definition']);null_round['runbook']['steps'][0].update(round=None,input=None)
        validator.validate(null_round)
    print(f'{len(corpus)} typed-pooling traces; {invalid} invalid definitions; {structural} schema negatives; '
          f'{setup} setup/seed/budget negatives; shared quotas, typed identity, private reader grants, '
          'final eligibility, linked responses, current ballots, fallback matrix, 800-item bounds, '
          'random properties and every-boundary recovery pass')
    return invalid


if __name__=='__main__':
    from check import node
    check(node,json.loads((HERE/'package.schema.json').read_text()))
