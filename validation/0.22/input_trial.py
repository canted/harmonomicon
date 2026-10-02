#!/usr/bin/env python3
"""Generic typed-input authority, continuation and durable outcome witnesses."""
import base64
import concurrent.futures
import copy
import json
import sqlite3
import tempfile
from pathlib import Path
from run import Host, package, ROOT
from runtime import run
from image_trial import png as image
from artifact_trial import wav

PEOPLE = ['a', 'b', 'c']
VIEWERS = PEOPLE + ['organizer']

def control(actors=None, opening=0, closing=None):
    return dict(actors=PEOPLE if actors is None else actors, opensAt=opening, closesAt=closing)

def create(h, p, iid, bindings=None, inputs=None, people=None, organizer='organizer'):
    imported = h.request('/packages', {'package': p})
    assert imported['outcome'] in ['imported', 'existing'], imported
    body = dict(id=iid, packageId=p['id'], version=p['version'], participants=PEOPLE if people is None else people, organizer=organizer)
    if bindings is not None: body['hostBindings'] = bindings
    if inputs is not None: body['hostInputs'] = inputs
    return h.request('/instances', body), body

def view(h, iid, tokens, actor='c'):
    return h.request('/instances/'+iid+'/view', token=tokens[actor])['view']

def record(v, sid):
    return next(r for r in v['records'] if r['step']==sid)

def submit(h, iid, tokens, actor, sid, item, value, event_id=None):
    return h.request('/instances/'+iid+'/events', dict(eventId=event_id or sid+'-'+actor+'-'+item, type='submit', step=sid, payload=dict(itemId=item, value=value)), tokens[actor])['outcome']

def close(h, iid, sid, event_id=None):
    return h.request('/instances/'+iid+'/control', dict(eventId=event_id or 'close-'+sid, type='close', step=sid, payload={}))['outcome']

def ballot(h, iid, tokens, actor, candidate, event_id='ballot', sid='vote'):
    return h.request('/instances/'+iid+'/events', dict(eventId=event_id, type='submit', step=sid, payload=dict(candidate=candidate)), tokens[actor])['outcome']

def media(h, iid, tokens, actor, kind, blob):
    result=h.request('/instances/'+iid+'/media', dict(mediaType='image/png' if kind=='image' else 'audio/wav', data=base64.b64encode(blob).decode()), tokens[actor])
    assert result['outcome']=='ready',result
    return dict(kind=kind,ref=result['ref'])

def read(h,iid,tokens,actor,ref):
    return h.request('/instances/'+iid+'/media/'+ref,token=tokens[actor])

def seed(h, iid='seed', kind='text', private=False, people=None, author='a'):
    p=package('starting-contribution')
    if private:p['runbook']['steps'][0]['visibility']='private';p['id'] += '-private'
    created,_=create(h,p,iid,people=people,inputs={'piece':control(actors=[author])})
    assert created['outcome']=='created',created
    tokens=created['tokens'];blob=None
    value=dict(kind='text',text='A real authored starting piece.')
    if kind!='text':
        blob=image() if kind=='image' else wav();value=media(h,iid,tokens,author,kind,blob)
    assert submit(h,iid,tokens,author,'piece','opening',value)=='accepted'
    assert close(h,iid,'piece')=='accepted'
    return created,tokens,value,blob

def absent(h, iid, response):
    assert response['outcome'] in ['invalid_setup','invalid_request'],response
    assert h.request('/instances/'+iid+'/status')=={'outcome':'not_found'}

def authority(kind,directory):
    h=Host(kind,directory/(kind+'-input-authority.sqlite'))
    try:
        source,source_tokens,value,blob=seed(h,kind='image')
        p=package('creative-continuation-input');pointer={'starting_piece':dict(instance='seed',source='piece',itemId='opening')}
        inputs={'continuations':control(),'vote':control()}
        for iid,bindings,people,organizer,controls in [
            ('missing',None,None,'organizer',inputs),
            ('extra',{**pointer,'unknown':pointer['starting_piece']},None,'organizer',inputs),
            ('wrong-origin',{'starting_piece':dict(instance='missing',source='piece',itemId='opening')},None,'organizer',inputs),
            ('wrong-item',{'starting_piece':dict(instance='seed',source='piece',itemId='other')},None,'organizer',inputs),
            ('wrong-step',{'starting_piece':dict(instance='seed',source='other',itemId='opening')},None,'organizer',inputs),
            ('forged-author',{'starting_piece':dict(pointer['starting_piece'],actor='b')},None,'organizer',inputs),
            ('forged-value',{'starting_piece':dict(pointer['starting_piece'],value=dict(kind='text',text='fake'))},None,'organizer',inputs),
            ('outsider-roster',pointer,['a','outsider'],'organizer',inputs),
            ('outsider-organizer',pointer,None,'outsider',inputs),
            ('outsider-future',pointer,None,'organizer',{'continuations':control(),'vote':control(['outsider'])})
        ]:
            result,_=create(h,p,iid,bindings,controls,people,organizer);absent(h,iid,result)
        text_only=copy.deepcopy(p);text_only['id']+='-text-input';text_only['inputs']['starting_piece']['kinds']=['text']
        result,_=create(h,text_only,'wrong-kind',pointer,inputs);absent(h,'wrong-kind',result)
        private,_,_,_=seed(h,'private-seed',private=True)
        result,_=create(h,p,'private-target',{'starting_piece':dict(instance='private-seed',source='piece',itemId='opening')},inputs);absent(h,'private-target',result)
        withdrawn, _=create(h,package('starting-contribution'),'withdrawn-source',inputs={'piece':control(['a'])})
        assert submit(h,'withdrawn-source',withdrawn['tokens'],'a','piece','withdrawn',dict(kind='text',text='An ineligible saved entry.'))=='accepted'
        assert h.request('/instances/withdrawn-source/control',dict(eventId='withdraw',type='configure',step='piece',payload=control(['b'])))['outcome']=='accepted'
        assert close(h,'withdrawn-source','piece')=='accepted'
        result,_=create(h,p,'withdrawn-target',{'starting_piece':dict(instance='withdrawn-source',source='piece',itemId='withdrawn')},inputs);absent(h,'withdrawn-target',result)
        elder,_,elder_value,elder_blob=seed(h,'external-author',kind='audio',people=PEOPLE+['elder'],author='elder')
        supplied,_=create(h,p,'external-author-target',{'starting_piece':dict(instance='external-author',source='piece',itemId='opening')},inputs)
        assert supplied['outcome']=='created' and 'elder' not in supplied['tokens']
        old=record(view(h,'external-author-target',supplied['tokens']),'continuations')['input']['candidate']
        assert old['actor']=='elder' and old['ref']['instance']==elder['instanceIdentity']
        assert base64.b64decode(read(h,'external-author-target',supplied['tokens'],'c',elder_value['ref'])['data'])==elder_blob
        # Trusted stored source media still must be ready when new read grants are made.
        with sqlite3.connect(h.db) as db:db.execute('UPDATE media SET ready=0 WHERE instance=?',('seed',))
        result,_=create(h,p,'unready',pointer,inputs);absent(h,'unready',result)
        with sqlite3.connect(h.db) as db:db.execute('UPDATE media SET ready=1 WHERE instance=?',('seed',))
        created,body=create(h,p,'target',pointer,inputs);assert created['outcome']=='created',created
        tokens=created['tokens'];before=view(h,'target',tokens)
        inp=record(before,'continuations')['input'];assert inp['candidate']['actor']=='a' and inp['candidate']['value']==value
        assert inp['candidate']['ref']==dict(instance=source['instanceIdentity'],source='piece',itemId='opening')
        assert inp['candidate']['round'] is None and inp['via']==dict(instance=source['instanceIdentity'],source='piece',itemId='opening',round=None)
        for actor in VIEWERS:assert base64.b64decode(read(h,'target',tokens,actor,value['ref'])['data'])==blob
        # Viewing old material does not authorize its submission under new ownership.
        assert submit(h,'target',tokens,'b','continuations','borrowed',value)=='rejected'
        forged_control=dict(eventId='expand',type='configure',step='continuations',payload=control(['a','outsider']))
        assert h.request('/instances/target/control',forged_control)['outcome']=='rejected'
        assert view(h,'target',tokens)==before
        assert h.request('/instances/target/bindings',dict(actor='outsider',token='outside-token'))['outcome']=='invalid_request'
        assert h.request('/instances/target/media/'+value['ref'],token='outside-token')['outcome']=='unauthorized'
        assert h.request('/instances/target/events',forged_control,tokens['a'])['outcome']=='rejected'
        assert h.request('/instances/target/events',dict(eventId='inject',type='submit',step='continuations',payload=dict(itemId='fake',value=value),inputBindings=pointer),tokens['a'])['outcome']=='rejected'
        h.restart();assert view(h,'target',tokens)==before
        assert h.request('/instances',body)['outcome']=='instance_conflict'
        body['id']='setup-race'
        with concurrent.futures.ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda _:h.request('/instances',body),range(2)))
        assert sorted(x['outcome'] for x in results)==['created','instance_conflict']
        winner=next(x for x in results if x['outcome']=='created');h.restart()
        assert record(view(h,'setup-race',winner['tokens']),'continuations')['input']==inp
    finally:h.stop()
    print(kind+': full-snapshot input authority, organizer/future/new-viewer privacy, unready bytes, ownership, setup races and restart pass',flush=True)

def continuation(kind,directory,media_kind):
    h=Host(kind,directory/(kind+'-handoff-'+media_kind+'.sqlite'),tie_choice=0)
    try:
        source,source_tokens,value,blob=seed(h,kind=media_kind)
        p=package('creative-continuation-input');pointer={'starting_piece':dict(instance='seed',source='piece',itemId='opening')}
        controls={'continuations':control(),'vote':control()}
        first,_=create(h,p,'first',pointer,controls);assert first['outcome']=='created',first
        tokens=first['tokens'];new_value=dict(kind='text',text='The next real continuation.')
        if media_kind!='text':new_value=media(h,'first',tokens,'a',media_kind,blob)
        assert submit(h,'first',tokens,'a','continuations','same',new_value)=='accepted'
        assert submit(h,'first',tokens,'b','continuations','other',dict(kind='text',text='Another continuation.'))=='accepted'
        assert close(h,'first','continuations')=='accepted'
        choices=record(view(h,'first',tokens),'vote')['candidates'];chosen=choices[0]
        bad_ref=dict(chosen['ref'],instance=source['instanceIdentity'])
        assert ballot(h,'first',tokens,'b',bad_ref,'wrong-instance')=='rejected'
        assert ballot(h,'first',tokens,'b',chosen['ref'],'original')=='accepted'
        assert ballot(h,'first',tokens,'b',choices[1]['ref'],'change')=='accepted'
        assert ballot(h,'first',tokens,'b',chosen['ref'],'original')=='replayed'
        assert ballot(h,'first',tokens,'b',chosen['ref'],'change-back')=='accepted'
        h.restart();assert close(h,'first','vote')=='accepted'
        output=record(view(h,'first',tokens),'result')['output']
        assert output['status']=='selected' and output['basis']=='most_votes' and output['selected']==chosen and output['totalVotes']==1
        assert output['selected']['ref']==dict(instance=first['instanceIdentity'],source='continuations',itemId='same')
        for actor in ['c','organizer']:assert record(view(h,'first',tokens,actor),'vote')['entries']==[]
        retained=package('creative-retained-source')
        second,_=create(h,retained,'second',{'starting_piece':dict(instance='first',result='selected')},controls)
        assert second['outcome']=='created',second
        two=second['tokens'];inp=record(view(h,'second',two),'continuations')['input']
        assert inp['candidate']==chosen and inp['via']==dict(instance=first['instanceIdentity'],result='selected',round='continuation')
        if blob is not None:
            for actor in VIEWERS:assert base64.b64decode(read(h,'second',two,actor,new_value['ref'])['data'])==blob
            assert submit(h,'second',two,'b','continuations','stolen',new_value)=='rejected'
        assert submit(h,'second',two,'b','continuations','same',dict(kind='text',text='An unvoted proposed continuation.'))=='accepted'
        assert close(h,'second','continuations')=='accepted'
        assert ballot(h,'second',two,'a',chosen['ref'],'stale-origin')=='rejected'
        assert close(h,'second','vote')=='accepted'
        kept=record(view(h,'second',two),'result')['output']
        assert kept['basis']=='retained_input' and kept['selected']==chosen and kept['totalVotes']==0 and kept['tied']==[]
        assert [row['count'] for row in kept['counts']]==[0]
        h.restart();assert record(view(h,'second',two),'result')['output']==kept
        third,_=create(h,p,'third',{'starting_piece':dict(instance='second',result='selected')},controls)
        assert third['outcome']=='created',third
        again=record(view(h,'third',third['tokens']),'continuations')['input']
        assert again['candidate']==chosen and again['candidate']['ref']['instance']==first['instanceIdentity']
        assert again['via']==dict(instance=second['instanceIdentity'],result='selected',round='continuation')
        assert again['predecessorRound']=='continuation'
        if blob is not None:assert base64.b64decode(read(h,'third',third['tokens'],'c',new_value['ref'])['data'])==blob
        # A settled but unpresented result cannot be imported through a result pointer.
        hidden=copy.deepcopy(p);hidden['id']+='-hidden-result';hidden['runbook']['steps'].pop()
        private,_=create(h,hidden,'hidden',pointer,controls);assert private['outcome']=='created'
        assert submit(h,'hidden',private['tokens'],'a','continuations','only',dict(kind='text',text='Hidden selected decision.'))=='accepted'
        assert close(h,'hidden','continuations')=='accepted' and close(h,'hidden','vote')=='accepted'
        failed,_=create(h,p,'from-hidden',{'starting_piece':dict(instance='hidden',result='selected')},controls);absent(h,'from-hidden',failed)
        wrong,_=create(h,p,'from-counts',{'starting_piece':dict(instance='first',result='counts')},controls);absent(h,'from-counts',wrong)
    finally:h.stop()
    print(kind+': '+media_kind+' selected-source handoff preserves material origin, author/round, distinct selection provenance, private ballots, bytes and retention across three durable instances',flush=True)

def actor_expansion(kind,directory):
    h=Host(kind,directory/(kind+'-input-expansion.sqlite'))
    try:
        source,_,value,blob=seed(h,kind='audio',people=PEOPLE+['late'])
        p=package('creative-continuation-input');pointer={'starting_piece':dict(instance='seed',source='piece',itemId='opening')}
        made,_=create(h,p,'target',pointer,{'continuations':control(),'vote':control()});assert made['outcome']=='created'
        expansion=dict(eventId='expand-authorized',type='configure',step='continuations',payload=control(PEOPLE+['late']))
        assert h.request('/instances/target/control',expansion)['outcome']=='accepted'
        assert h.request('/instances/target/bindings',dict(actor='late',token='late-token'))['outcome']=='bound'
        tokens=dict(made['tokens'],late='late-token')
        assert record(view(h,'target',tokens,'late'),'continuations')['input']['candidate']['value']==value
        assert base64.b64decode(read(h,'target',tokens,'late',value['ref'])['data'])==blob
        h.restart();assert base64.b64decode(read(h,'target',tokens,'late',value['ref'])['data'])==blob
        assert submit(h,'target',tokens,'late','continuations','not-owned',value)=='rejected'
        # An actor permitted by one input must still have access to every other input.
        seed(h,'restricted',kind='text')
        multiple=copy.deepcopy(p);multiple['id']+='-two-inputs';multiple['inputs']['secondary']=dict(type='contribution',kinds=['text'])
        multiple['runbook']['steps'].append(dict(id='second_source',op='artifact_pool@3',round='second',input={'binding':'secondary'},prompt='Use the other supplied source.',kinds=['text'],visibility='private'))
        pointers=dict(pointer,secondary=dict(instance='restricted',source='piece',itemId='opening'))
        target,_=create(h,multiple,'multiple',pointers,{'continuations':control(),'vote':control(),'second_source':control()});assert target['outcome']=='created'
        assert h.request('/instances/multiple/control',expansion)['outcome']=='rejected'
        with sqlite3.connect(h.db) as db:assert db.execute('SELECT COUNT(*) FROM input_grants WHERE destination=? AND actor=?',('multiple','late')).fetchone()[0]==0
        assert h.request('/instances/multiple/bindings',dict(actor='late',token='late-multiple'))['outcome']=='invalid_request'
    finally:h.stop()
    print(kind+': authorized added viewers receive durable bytes without ownership; multi-input authorization fails atomically before any viewer/grant expansion',flush=True)

def fallback_profiles(kind,directory):
    h=Host(kind,directory/(kind+'-fallbacks.sqlite'),seed=None)
    try:
        source,_,_,_=seed(h)
        pointer={'starting_piece':dict(instance='seed',source='piece',itemId='opening')}
        for count in [0,2]:
            for mode in ['omitted','unresolved','random','retain_input']:
                p=package('creative-continuation-input');p['id']+='-'+mode.replace('_','-')
                selection=p['runbook']['steps'][3]
                if mode=='omitted':selection.pop('noVotes')
                else:selection['noVotes']=mode
                p['requires'].remove('policy:random_candidate@1')
                if mode=='random':p['requires'].append('policy:random_candidate@1')
                if mode=='retain_input':p['requires'].append('policy:retain_input@1')
                p['runbook']['steps'].append(dict(id='next_round',op='artifact_pool@3',round='next',input={'result':'selected'},prompt='Use the actual selected material, if any.',kinds=['text'],visibility='private'))
                iid='fallback-'+str(count)+'-'+mode
                created,_=create(h,p,iid,pointer,{'continuations':control(),'vote':control(),'next_round':control()});assert created['outcome']=='created',created
                tokens=created['tokens'];starting=record(view(h,iid,tokens),'continuations')['input']['candidate']
                for i in range(count):assert submit(h,iid,tokens,PEOPLE[i],'continuations',str(i),dict(kind='text',text='Proposed '+str(i)))=='accepted'
                assert close(h,iid,'continuations')=='accepted'
                if count:assert close(h,iid,'vote')=='accepted'
                outcome=record(view(h,iid,tokens),'result')['output']
                assert outcome['totalVotes']==0 and all(row['count']==0 for row in outcome['counts']) and outcome['tied']==[]
                if not count:assert outcome['status']=='no_candidates' and outcome['selected'] is None and outcome['basis'] is None
                elif mode in ['omitted','unresolved']:assert outcome['status']=='no_votes' and outcome['selected'] is None and outcome['basis'] is None
                elif mode=='random':assert outcome['status']=='selected' and outcome['basis']=='random_no_votes' and outcome['selected'] in [row['candidate'] for row in outcome['counts']]
                else:assert outcome['status']=='selected' and outcome['basis']=='retained_input' and outcome['selected']==starting
                next_record=record(view(h,iid,tokens),'next_round')
                assert next_record['blocked']==(outcome['selected'] is None)
                if outcome['selected'] is not None:assert next_record['input']['candidate']==outcome['selected']
                h.restart();assert record(view(h,iid,tokens),'result')['output']==outcome
        # Exclusive deadlines, current counts and close/vote serialization under opt-in fallback.
        p=package('creative-continuation-input');created,_=create(h,p,'deadline',pointer,{'continuations':control(closing=10),'vote':control(opening=10,closing=20)})
        assert created['outcome']=='created';tokens=created['tokens']
        assert submit(h,'deadline',tokens,'a','continuations','one',dict(kind='text',text='A deadline continuation.'))=='accepted'
        h.clock(10);candidate=record(view(h,'deadline',tokens),'vote')['candidates'][0]
        h.clock(19);assert ballot(h,'deadline',tokens,'a',candidate['ref'],'before-close')=='accepted'
        h.clock(20);assert ballot(h,'deadline',tokens,'b',candidate['ref'],'at-close')=='rejected'
        result=record(view(h,'deadline',tokens),'result')['output'];assert result['basis']=='most_votes' and result['totalVotes']==1
        assert ballot(h,'deadline',tokens,'a',candidate['ref'],'before-close')=='replayed'
        for i in range(3):
            iid='close-race-'+str(i);created,_=create(h,p,iid,pointer,{'continuations':control(opening=20),'vote':control(opening=20)})
            assert created['outcome']=='created';tokens=created['tokens']
            assert submit(h,iid,tokens,'a','continuations','one',dict(kind='text',text='Race candidate.'))=='accepted'
            assert close(h,iid,'continuations')=='accepted';candidate=record(view(h,iid,tokens),'vote')['candidates'][0]
            with concurrent.futures.ThreadPoolExecutor(2) as pool:
                vote=pool.submit(ballot,h,iid,tokens,'a',candidate['ref'],'race-vote');closing=pool.submit(close,h,iid,'vote')
                voted,closed=vote.result(),closing.result()
            assert closed=='accepted' and voted in ['accepted','rejected']
            out=record(view(h,iid,tokens),'result')['output'];assert out['selected']==candidate and out['totalVotes']==(voted=='accepted')
            assert out['basis']==('most_votes' if voted=='accepted' else 'random_no_votes')
            h.restart();assert record(view(h,iid,tokens),'result')['output']==out
    finally:h.stop()
    print(kind+': all default/explicit no-vote and empty policies, unseeded random membership/durability, dependent blocking, exclusive deadlines and close/vote races pass',flush=True)

def negotiation(kind,directory):
    for missing in ['artifact_pool@3','vote@2','tally@3','select@2','present@2','reveal_ballots@2','contribution_inputs@1','policy:random_candidate@1','policy:retain_input@1']:
        h=Host(kind,directory/(kind+'-missing-'+missing.replace(':','-').replace('@','-')+'.sqlite'),disabled=missing)
        try:
            seed(h);p=package('creative-retained-source' if missing=='policy:retain_input@1' else 'creative-continuation-input')
            if missing=='reveal_ballots@2':p['runbook']['steps'].append(dict(id='ballots',op='reveal_ballots@2',source='vote'));p['requires'].append(missing)
            result,_=create(h,p,'unsupported',{'starting_piece':dict(instance='seed',source='piece',itemId='opening')})
            assert result=={'outcome':'unsupported','missing':[missing]},(kind,missing,result)
            assert h.request('/instances/unsupported/status')=={'outcome':'not_found'}
            discovery=h.request('/support');assert missing not in discovery['operations']+discovery['capabilities']
        finally:h.stop()
    print(kind+': every new operation, input capability and no-vote policy negotiates separately and rejects before target creation',flush=True)

def held_out_transfer(directory):
    p=package('supplied-brief-workshop');people=list('abcd');snapshots=[];identities=[];digest=None
    for kind in ['python','node']:
        h=Host(kind,directory/(kind+'-supplied-workshop.sqlite'))
        try:
            source,_,_,_=seed(h,people=people)
            imported=h.request('/packages',{'package':p});exported=h.request('/packages/'+p['id']+'/'+p['version'])
            assert exported['package']==p and imported['digest']==exported['digest']
            if digest is None:digest=exported['digest']
            else:assert digest==exported['digest']
            controls={'proposals':control(people,0,10),'vote':control(people,10,20),'plans':control(people,20,30)}
            created,_=create(h,p,'workshop',{'brief':dict(instance='seed',source='piece',itemId='opening')},controls,people)
            assert created['outcome']=='created',created
            tokens=created['tokens'];inp=record(view(h,'workshop',tokens),'proposals')['input'];binding=dict(candidate=inp['candidate'],via=inp['via'])
            events=[]
            def event(i,a,at,sid,payload,typ='submit'):return dict(eventId=i,actor=a,at=at,step=sid,payload=payload,type=typ)
            def tick(at):return event('tick-'+str(at),'system',at,None,{},'tick')
            for a in 'ab':events.append(event('proposal-'+a,a,0,'proposals',dict(itemId=a,value=dict(kind='text',text='Proposal '+a))))
            events.append(tick(10))
            for a in 'abc':events.append(event('vote-'+a,a,10,'vote',dict(candidate=dict(instance=created['instanceIdentity'],source='proposals',itemId='b'))))
            events.append(tick(20))
            for a in people:events.append(event('plan-'+a,a,20,'plans',dict(itemId=a,value=dict(kind='text',text='First step '+a))))
            events.append(tick(30))
            for a in 'ac':events.append(event('exercise-'+a,a,30,'exercise',dict(text='Experiment '+a)))
            events.append(tick(60030))
            reference=run(dict(package=p,participants=people,organizer='organizer',startedAt=0,instanceId=created['instanceIdentity'],inputBindings={'brief':binding},trustedInputs=[dict(binding=binding,viewers=people+['organizer'],ready=True)],hostInputs=controls,events=events))
            assert reference['outcomes']==['accepted']*len(events),reference.get('outcomes',reference)
            for i,e in enumerate(events):
                h.clock(e['at'])
                if e['type']!='tick':assert h.request('/instances/workshop/events',{k:e[k] for k in ['eventId','type','step','payload']},tokens[e['actor']])['outcome']=='accepted'
                h.restart()
                actual={a:view(h,'workshop',tokens,a) for a in tokens}
                assert actual==reference['views'][i],(kind,i,actual,reference['views'][i])
            assert record(actual['a'],'plans')['input']['candidate']['ref']==dict(instance=created['instanceIdentity'],source='proposals',itemId='b')
            assert record(actual['b'],'exercise')['entries']==[{'actor':'a','value':{'text':'Experiment a'}}]
            assert record(actual['d'],'exercise')['entries']==[{'actor':'c','value':{'text':'Experiment c'}}]
            assert record(actual['organizer'],'exercise')['entries']==[] and record(actual['organizer'],'vote')['entries']==[]
            identifiers={source['instanceIdentity']:'source-identity',created['instanceIdentity']:'workshop-identity'}
            def normalize(value):
                if type(value) is dict:return {k:normalize(v) for k,v in value.items()}
                if type(value) is list:return [normalize(v) for v in value]
                return identifiers.get(value,value) if type(value) is str else value
            snapshots.append(normalize(actual));identities.append(created['instanceIdentity'])
        finally:h.stop()
    assert snapshots[0]==snapshots[1] and identities[0]!=identities[1]
    print('Held-out supplied-brief selection/planning/pair composition transfers identical package bytes and agrees with exact engine views at every durable restart; host UUIDs stay distinct',flush=True)

def check(directory):
    for kind in ['python','node']:
        authority(kind,directory)
        for media_kind in ['text','image','audio']:continuation(kind,directory,media_kind)
        actor_expansion(kind,directory)
        fallback_profiles(kind,directory)
        negotiation(kind,directory)
    held_out_transfer(directory)

if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='harmonomicon-022-inputs-') as name:check(Path(name))
