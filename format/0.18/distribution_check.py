"""Explicit policy vectors, invalid definitions and linked-response boundaries."""
import copy
import json
from pathlib import Path
from runtime import Engine, run, MAX
HERE=Path(__file__).resolve().parent

def definition(name='single-source-creative-response'):return json.loads((HERE/'examples'/f'{name}.json').read_text())
def event(i,t,a,at,step,payload):return dict(eventId=i,type=t,actor=a,at=at,step=step,payload=payload)
def contributions(people):return [event('source-'+str(i),'submit',a,1,'sources',dict(itemId=str(i),text='source '+str(i))) for i,a in enumerate(people)]

def boundaries(node):
    variants=[];base=definition()
    def add(change):
        p=copy.deepcopy(base);change(p);variants.append(p)
    for field,value in [('source','missing'),('recipients','anyone'),('policy','policy:balanced_offers@1'),('cardinality','two'),('reuse','forbidden'),('unmatched','self'),('extra',1)]:add(lambda p,f=field,v=value:p['runbook']['steps'][1].update({f:v}))
    for token in ['assign_sources@1','respond@1','reveal_responses@1','policy:seeded_nonself_source@1','seeded_assignment@1']:add(lambda p,t=token:p['requires'].remove(t))
    add(lambda p:p['runbook']['steps'][0].update(perActor=2))
    for field,value in [('source','sources'),('prompt',{'setting':'question'}),('afterMs',0),('afterMs',None),('close','organizer'),('afterMs',True),('afterMs',86400001)]:add(lambda p,f=field,v=value:p['runbook']['steps'][2].update({f:v}))
    add(lambda p:p['runbook']['steps'][3].update(source='distribution'))
    add(lambda p:p['runbook']['steps'].reverse())
    add(lambda p:p['runbook']['steps'].append(dict(id='leak',op='reveal@1',sources=['response'])))
    add(lambda p:p['runbook']['steps'].append(dict(id='turns',op='for_each@1',over='participants',steps=[dict(p['runbook']['steps'][1],id='nested_distribution')])))
    add(lambda p:p['runbook']['steps'][1].update(policy='policy:next_nonself_source@1',cardinality=1))
    for p in variants:assert run(dict(action='validate',package=p))==node(dict(action='validate',package=p))=={'outcome':'invalid_package'}
    request=dict(package=base,participants=list('abcd'),organizer='organizer',events=[])
    for seed in [None,0,True,-1,4294967296,1.5,'1']:
        args=dict(request,seed=seed);assert run(args)==node(args)=={'outcome':'invalid_setup'}
    # Policy known-answer vectors are independent of any activity interpretation.
    args=dict(request,seed=1,events=contributions('abcd')+[event('open','tick','system',10,None,{})]);result=run(args);assert result==node(args)
    assert result['state']['randomState']==307599695
    assert [(a['actor'],a['itemId']) for a in result['state']['records'][1]['assignments']]==[('a','3'),('b','0'),('c','3'),('d','1')]
    assert len(set(a['itemId'] for a in result['state']['records'][1]['assignments']))==3 # Reuse, not a bijection.
    # Max seed and integer-valued JSON float seed are defined, not coerced booleans.
    for seed in [4294967295,1.0]:
        q=dict(args,seed=seed);assert run(q)==node(q)
    # Restore rejects a changed initial seed; the generator's consumed state is retained.
    state=result['state'];resumed=dict(request,state=state,seed=1,events=[]);assert run(resumed)==node(resumed) and run(resumed)['state']==state
    for seed in [2,4294967295]:assert run(dict(resumed,seed=seed))==node(dict(resumed,seed=seed))=={'outcome':'invalid_setup'}
    # Reverse the versioned shift equations to force a rejection-sampling draw of UINT_MAX.
    mask=4294967295;y=mask
    z=y
    for shift in range(5,32,5):z ^= (y<<shift)&mask
    y=z^(z>>17);seed=(y^((y<<13)&mask)^((y<<26)&mask))&mask
    # The first draw is UINT_MAX: value=UINT_MAX-1 is outside the two-candidate limit.
    # The second draw is 253983, selecting index zero; the consumed state must reflect both.
    assert seed==1584200935
    engine=Engine(base,list('abcd'),'organizer',seed=seed)
    assert engine.random_index(2)==0 and engine.state['randomState']==253983
    # Exercise that rejection through both full interpreters, with two choices for b and d.
    q=dict(request,seed=seed,events=contributions('ac')+[event('open','tick','system',10,None,{})]);p=copy.deepcopy(base);p['runbook']['steps'][1]['recipients']='participants';q['package']=p
    result=run(q);assert result==node(q);assert result['state']['records'][1]['assignments'][1]['itemId']=='0'
    # No rerolls for a single candidate; unmatched actors do not consume the stream.
    q=dict(request,events=contributions('a')+[event('open','tick','system',10,None,{})],seed=1);p=copy.deepcopy(base);p['runbook']['steps'][1]['recipients']='participants';q['package']=p;result=run(q);assert result==node(q) and result['state']['randomState']==1
    # Seed and complete assignment map never occur in actor views, before or after reveal.
    for actors in run(args)['views']:
        for actor,view in actors.items():
            assert 'assignmentSeed' not in view and 'randomState' not in view
            for r in view['records']:
                if r['op'] in ['assign_sources@1','respond@1']:assert 'assignments' not in r
    # The deadline reconciles before replay; empty/invalid forms don't reserve their event IDs.
    actions=contributions('abcd')+[event('open','tick','system',10,None,{})]
    actions += [event('bad','submit','b',10,'response',dict(itemId='0',text='')),event('bad','submit','b',10,'response',dict(itemId='0',text='ok',extra=1)),event('bad','submit','b',10,'response',dict(itemId='0',text='ok')),event('seed','submit','a',11,'response',dict(itemId='3',text='A',seed=1)),event('host','submit','organizer',11,'response',dict(itemId='3',text='host')),event('bad','submit','b',20,'response',dict(itemId='0',text='ok'))]
    q=dict(request,seed=1,events=actions);result=run(q);assert result==node(q)
    assert result['outcomes'][-6:]==['rejected','rejected','accepted','rejected','rejected','replayed'];assert result['views'][-1]['a']['phase']=='complete'
    # Linked responses can remain private after completion; reveal is an explicit package choice.
    p=copy.deepcopy(base);p['runbook']['steps'].pop();q=dict(q,package=p);result=run(q);assert result==node(q)
    assert result['views'][-1]['organizer']['records'][2]['entries']==[]
    # Safe clock budget and two sequential distributions preserve operation-specific state.
    q=dict(request,seed=1,startedAt=MAX-19);assert run(q)==node(q)=={'outcome':'invalid_setup'}
    p=copy.deepcopy(base);p['runbook']['steps'] += [dict(p['runbook']['steps'][1],id='second_distribution'),dict(p['runbook']['steps'][2],id='second_response',source='second_distribution')]
    q=dict(request,package=p,seed=1,events=contributions('abcd')+[event('first_close','tick','system',20,None,{})]);result=run(q);assert result==node(q)
    assert result['views'][-1]['a']['step']=='second_response';assert result['state']['randomState']!=307599695
    state=result['state'];q=dict(request,package=p,state=state,seed=1);assert run(q)==node(q) and run(q)['state']==state
    # A fixed named policy is selected explicitly; unknown support must fail before creation.
    p=copy.deepcopy(base);p['requires'].append('future_linked_media@1');q=dict(request,package=p,seed=1);assert run(q)==node(q)==dict(outcome='unsupported',missing=['future_linked_media@1'])
    print(f'{len(variants)} distribution invalid definitions; exact sampler vectors/rejection, seed restore, response validation/privacy, clock budget and sequential distributions pass')
    return len(variants)

if __name__=='__main__':
    from check import node
    boundaries(node)


def schema_negatives(schema):
    """Structural failures are distinct from semantic source/scope/capability rules."""
    import jsonschema
    validator=jsonschema.Draft202012Validator(schema);invalid=[]
    for index,field,value in [(1,'recipients','anyone'),(1,'policy','policy:balanced_offers@1'),(1,'cardinality','two'),(1,'reuse','forbidden'),(1,'unmatched','self'),(1,'extra',1),(2,'prompt',{'setting':'question'}),(2,'afterMs',None),(2,'afterMs',True),(2,'afterMs',0),(2,'afterMs',86400001),(2,'close','organizer')]:
        p=definition();p['runbook']['steps'][index][field]=value;invalid.append(p)
    for p in invalid:assert list(validator.iter_errors(p)), 'schema accepted a structurally invalid new operation'
    print(f'{len(invalid)} distribution/response schema-negative witnesses pass')
