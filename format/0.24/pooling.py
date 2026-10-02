"""Independent typed pooling, per-item sharing, voting and linked responses."""
import copy
import artifacts
import continuation
import voting

OPS = {'pool@2','for_items@2','assign_item@2','acknowledge@2','reveal_item@2','vote@3','tally@4','select@3','present@3','reveal_ballots@3','assign_artifacts@2','artifact_response@2','reveal_artifact_responses@2'}
WINDOWS = {'pool@2','vote@3','artifact_response@2'}
SOURCES = {'artifact_pool@1','artifact_pool@2','artifact_pool@3','pool@2'}
POLICIES = {'policy:next_nonself_item@1'}


def validate(step,known,used,nested,rounds,declared,consumed,in_items):
    demand,exact,text=artifacts.demand,artifacts.exact,artifacts.text
    op=step['op']
    if op in ['assign_item@2','acknowledge@2','reveal_item@2']:
        demand(in_items=='typed')
        if op=='assign_item@2':
            demand(exact(step,['id','op','policy','prompt','afterMs']) and step['policy']=='policy:claim_reader@1' and text(step['prompt']))
            demand(step['afterMs'] is None or artifacts.integer(step['afterMs']) and 1<=step['afterMs']<=86400000)
            used.add(step['policy'])
        elif op=='acknowledge@2':
            demand(exact(step,['id','op','source','prompt','afterMs']) and type(step['source']) is str and known.get(step['source'],{}).get('op')=='assign_item@2' and text(step['prompt']))
            demand(step['afterMs'] is None or artifacts.integer(step['afterMs']) and 1<=step['afterMs']<=86400000)
        else:demand(exact(step,['id','op','source']) and type(step['source']) is str and known.get(step['source'],{}).get('op')=='acknowledge@2')
        known[step['id']]=step
        return
    demand(not nested)
    if op=='pool@2':
        demand(exact(step,['id','op','prompt','kinds','perActor','visibility']+(['round'] if 'round' in step else [])+(['input'] if 'input' in step else [])))
        demand(text(step['prompt']) and artifacts.kinds(step['kinds']) and artifacts.integer(step['perActor']) and 1<=step['perActor']<=8 and step['visibility'] in ['private','group'])
        if step.get('round') is not None:
            demand(voting.name(step['round']) and step['round'] not in rounds);rounds.add(step['round'])
        source=step.get('input')
        if source is not None:
            if exact(source,['binding']):
                demand(type(source['binding']) is str and source['binding'] in declared);consumed.add(source['binding'])
            else:demand(exact(source,['result']) and type(source['result']) is str and known.get(source['result'],{}).get('op') in ['select@2','select@3'])
        used.add('host_controls@1')
        for kind in step['kinds']:
            if kind!='text':used.add(kind+'_contributions@1')
    elif op=='for_items@2':
        demand(exact(step,['id','op','source','policy','steps']) and type(step['source']) is str and known.get(step['source'],{}).get('op') in SOURCES)
        demand(step['policy']=='policy:pool_order@1');used.add(step['policy'])
        return
    elif op=='vote@3':
        demand(exact(step,['id','op','prompt','candidates','changes','ballots']) and text(step['prompt']) and step['changes'] in ['allowed','forbidden'] and step['ballots'] in ['private','group'])
        demand(exact(step['candidates'],['source']) and type(step['candidates']['source']) is str and known.get(step['candidates']['source'],{}).get('op') in SOURCES)
        used.add('host_controls@1')
    elif op=='tally@4':demand(exact(step,['id','op','source']) and type(step['source']) is str and known.get(step['source'],{}).get('op')=='vote@3')
    elif op=='select@3':
        demand(exact(step,['id','op','source','policy','ties']+(['noVotes'] if 'noVotes' in step else [])))
        demand(type(step['source']) is str and known.get(step['source'],{}).get('op')=='tally@4' and step['policy']=='policy:most_votes@1' and step['ties'] in ['unresolved','random'])
        used.add(step['policy'])
        if step['ties']=='random':used.add('policy:random_tie@1')
        fallback=step.get('noVotes','unresolved');demand(fallback in ['unresolved','random','retain_input'])
        if fallback=='random':used.add('policy:random_candidate@1')
        elif fallback=='retain_input':
            pool=continuation.selected_pool(step,known)
            demand(pool.get('op') in ['pool@2','artifact_pool@3'] and pool.get('input') is not None);used.add('policy:retain_input@1')
    elif op=='present@3':demand(exact(step,['id','op','source','prompt','audience']) and type(step['source']) is str and known.get(step['source'],{}).get('op') in ['tally@4','select@3'] and text(step['prompt']) and step['audience']=='group')
    elif op=='reveal_ballots@3':demand(exact(step,['id','op','source']) and type(step['source']) is str and known.get(step['source'],{}).get('op')=='vote@3')
    elif op=='assign_artifacts@2':
        demand(exact(step,['id','op','source','policy','recipients','cardinality','reuse','unmatched']) and type(step['source']) is str and known.get(step['source'],{}).get('op') in SOURCES)
        demand(step['policy'] in ['policy:next_nonself_item@1','policy:seeded_nonself_source@1'] and step['recipients'] in ['contributors','effective'] and step['cardinality']=='one' and step['reuse']=='allowed' and step['unmatched']=='skip')
        used.add(step['policy'])
        if step['policy']=='policy:seeded_nonself_source@1':used.add('seeded_assignment@1')
    elif op=='artifact_response@2':
        demand(exact(step,['id','op','source','prompt','kinds']) and type(step['source']) is str and known.get(step['source'],{}).get('op')=='assign_artifacts@2' and text(step['prompt']) and artifacts.kinds(step['kinds']))
        used.add('host_controls@1')
        for kind in step['kinds']:
            if kind!='text':used.add(kind+'_contributions@1')
    else:demand(exact(step,['id','op','source']) and type(step['source']) is str and known.get(step['source'],{}).get('op')=='artifact_response@2')
    known[step['id']]=step


def source_items(e,sid,frame):
    source=e.source(sid,frame)
    return source,[continuation.qualified(e,source,entry) for entry in source['entries'] if entry['actor'] in source['effective']['actors']]


def starting_input(e,step,frame):
    value=step.get('input')
    if value is None:return {'status':'none','predecessorRound':None,'candidate':None,'via':None}
    if 'binding' in value:
        binding=e.state['inputBindings'][value['binding']]
        return {'status':'initial','predecessorRound':binding['via']['round'],'candidate':copy.deepcopy(binding['candidate']),'via':copy.deepcopy(binding['via'])}
    output=e.source(value['result'],frame)['output'];pool=continuation.selected_pool(e.find_step(value['result']),e.definitions)
    return {'status':output['status'],'predecessorRound':pool.get('round'),'candidate':copy.deepcopy(output['selected']),'via':{'instance':e.state['instanceId'],'result':value['result'],'round':pool.get('round')}}


def loop_context(e,frame):
    frozen=e.state['typedItems'][frame['itemLoop']]
    candidate=next(item for item in frozen['items'] if item['ref']==frame['item'])
    return frozen,candidate


def settle(e,frame,now):
    step=frame['step'];op=step['op']
    if op=='for_items@2':
        source,items=source_items(e,step['source'],frame)
        e.state.setdefault('typedItems',{})[step['id']]={'items':copy.deepcopy(items),'actors':source['effective']['actors'][:]}
        frames=[]
        for index,item in enumerate(items):
            body=e.expand(step['steps'],None,index,copy.deepcopy(item['ref']))
            for child in body:child['itemLoop']=step['id']
            frames.extend(body)
        e.plan[e.state['pc']:e.state['pc']+1]=frames
        return 'advance'
    record=e.record(frame)
    if op in WINDOWS:
        record['effective']=copy.deepcopy(artifacts.control(e,frame))
        if op=='pool@2':
            if 'input' not in record:
                record['round']=step.get('round');record['input']=starting_input(e,step,frame);record['blocked']=record['input']['status'] not in ['none','initial','selected']
            if record['blocked']:record['closed']=True;e.next(e.state['openedAt']);return 'advance'
        elif op=='vote@3':
            if 'candidates' not in record:record['candidates']=source_items(e,step['candidates']['source'],frame)[1]
            if not record['candidates']:record['closed']=True;e.next(e.state['openedAt']);return 'advance'
        else:
            record['assignments']=copy.deepcopy(e.source(step['source'],frame)['assignments'])
            if not record['assignments']:record['closed']=True;e.next(e.state['openedAt']);return 'advance'
        deadline=record['effective']['closesAt']
        if deadline is not None and now>=deadline:record['closed']=True;e.next(max(deadline,e.state['openedAt']));return 'advance'
        return 'wait'
    if op=='assign_item@2':
        if 'reader' not in record:
            frozen,candidate=loop_context(e,frame);record['candidate']=copy.deepcopy(candidate);record['readers']=[actor for actor in frozen['actors'] if actor!=candidate['actor']];record['reader']=None
        if not record['readers']:record['closed']=True;e.next(e.state['openedAt']);return 'advance'
    elif op=='acknowledge@2':
        record['reader']=e.source(step['source'],frame)['reader'];record.setdefault('acknowledged',False)
        if record['reader'] is None:record['closed']=True;e.next(e.state['openedAt']);return 'advance'
    if op in ['assign_item@2','acknowledge@2']:
        deadline=e.deadline(frame)
        if deadline is not None and now>=deadline:record['closed']=True;e.next(max(deadline,e.state['openedAt']));return 'advance'
        return 'wait'
    if not record['closed']:
        if op=='reveal_item@2':
            ack=e.source(step['source'],frame)
            record['candidate']=copy.deepcopy(loop_context(e,frame)[1]) if ack['acknowledged'] else None
        elif op=='assign_artifacts@2':
            source,items=source_items(e,step['source'],frame);roster=source['effective']['actors']
            record['recipients']=[actor for actor in roster if step['recipients']=='effective' or any(item['actor']==actor for item in items)]
            record['assignments']=[];record['unmatched']=[]
            for actor in record['recipients']:
                candidates=[item for item in items if item['actor']!=actor]
                if not candidates:record['unmatched'].append(actor);continue
                if step['policy']=='policy:next_nonself_item@1':
                    next_author=min({item['actor'] for item in candidates},key=lambda author:(roster.index(author)-roster.index(actor))%len(roster))
                    chosen=next(item for item in candidates if item['actor']==next_author)
                else:chosen=candidates[0] if len(candidates)==1 else candidates[e.random_index(len(candidates))]
                record['assignments'].append({'actor':actor,'candidate':copy.deepcopy(chosen)})
        elif op=='tally@4':
            vote=e.source(step['source'],frame);ballots=[entry for entry in vote['entries'] if entry['actor'] in vote['effective']['actors']]
            record['output']={'counts':[{'candidate':copy.deepcopy(candidate),'count':sum(entry['candidate']==candidate['ref'] for entry in ballots)} for candidate in vote['candidates']],'totalVotes':len(ballots)}
        elif op=='select@3':record['output']=continuation.outcome(e,step,frame)
        elif op=='present@3':record['output']=copy.deepcopy(e.source(step['source'],frame)['output'])
        else:e.source(step['source'],frame)['revealed']=True
        record['closed']=True
    e.next(e.state['openedAt']);return 'advance'


def event(e,frame,event):
    step=frame['step'];op=step['op'];record=e.record(frame);payload=event['payload'];actor=event['actor'];now=event['at']
    if op=='assign_item@2':
        if event['type']=='claim' and payload=={} and actor in record['readers']:
            record['reader']=actor;record['closed']=True;e.next(now);return True
        return False
    if op=='acknowledge@2':
        if event['type']=='advance' and payload=={} and actor==record['reader']:
            record['acknowledged']=True;record['closed']=True;e.next(now);return True
        return False
    control=artifacts.control(e,frame)
    if actor=='system' and event['type']=='configure':
        if not artifacts.safe_control(e,payload) or payload['closesAt'] is not None and payload['closesAt']<=now:return False
        bound=list(dict.fromkeys(artifacts.bindings(e)+payload['actors']))
        if len(bound)>256:return False
        e.state['controls'][step['id']]=copy.deepcopy(payload);e.state['hostActors']=bound;record['effective']=copy.deepcopy(payload);return True
    if actor=='system' and event['type']=='close' and payload=={}:record['closed']=True;e.next(now);return True
    if event['type']!='submit' or actor not in control['actors'] or now<artifacts.opening(e,frame):return False
    previous=next((entry for entry in record['entries'] if entry['actor']==actor),None)
    if op=='pool@2':
        if sum(entry['actor']==actor for entry in record['entries'])>=step['perActor'] or not artifacts.exact(payload,['itemId','value']) or not artifacts.text(payload['itemId']):return False
        if any(entry['itemId']==payload['itemId'] for entry in record['entries']) or not artifacts.valid_value(e,actor,payload['value'],step['kinds']):return False
        record['entries'].append({'actor':actor,'itemId':payload['itemId'],'value':copy.deepcopy(payload['value'])});return True
    if op=='artifact_response@2':
        assigned=next((assignment['candidate'] for assignment in record['assignments'] if assignment['actor']==actor),None)
        if previous is not None or assigned is None or not artifacts.exact(payload,['candidate','value']) or payload['candidate']!=assigned['ref'] or not artifacts.valid_value(e,actor,payload['value'],step['kinds']):return False
        record['entries'].append({'actor':actor,'source':copy.deepcopy(assigned),'value':copy.deepcopy(payload['value'])});return True
    if previous is not None and step['changes']=='forbidden':return False
    if not artifacts.exact(payload,['candidate']) or not artifacts.exact(payload['candidate'],['instance','source','itemId']) or not any(candidate['ref']==payload['candidate'] for candidate in record['candidates']):return False
    ballot={'actor':actor,'candidate':copy.deepcopy(payload['candidate'])}
    if previous is None:record['entries'].append(ballot)
    else:record['entries'][record['entries'].index(previous)]=ballot
    return True


def can_claim(e,record,actor):
    active=e.plan[e.state['pc']] if e.state['pc']<len(e.plan) else None
    return active is not None and active['key']==record['key'] and not record['closed'] and record['reader'] is None and actor in record['readers']


def projection(e,record,item,actor):
    op=record['op'];definition=e.find_step(record['step'])
    if op=='pool@2':
        own=sum(entry['actor']==actor for entry in record['entries'])
        item.update(round=record['round'],input=copy.deepcopy(record['input']),blocked=record['blocked'],count=len(record['entries']),perActor=definition['perActor'],ownCount=own,remaining=max(0,definition['perActor']-own),eligible=actor in record['effective']['actors'],opensAt=record['effective']['opensAt'],closesAt=record['effective']['closesAt'])
        item['entries']=[continuation.qualified(e,record,entry) for entry in record['entries'] if entry['actor']==actor or definition['visibility']=='group']
    elif op=='assign_item@2':
        item['reader']=record['reader'];item['canClaim']=can_claim(e,record,actor);item['assignment']=copy.deepcopy(record['candidate']) if actor==record['reader'] else None
    elif op=='acknowledge@2':item.update(reader=record['reader'],acknowledged=record['acknowledged'])
    elif op=='reveal_item@2':item['candidate']=copy.deepcopy(record['candidate'])
    elif op=='assign_artifacts@2':
        item['eligible']=actor in record['recipients'];item['unmatched']=actor in record['unmatched'];item['assignment']=next((copy.deepcopy(assignment['candidate']) for assignment in record['assignments'] if assignment['actor']==actor),None)
    elif op=='artifact_response@2':
        assignment=next((copy.deepcopy(assignment['candidate']) for assignment in record['assignments'] if assignment['actor']==actor),None)
        item.update(count=len(record['entries']),eligible=actor in record['effective']['actors'] and assignment is not None,opensAt=record['effective']['opensAt'],closesAt=record['effective']['closesAt'],assignment=assignment)
        item['entries']=[copy.deepcopy(entry) for entry in record['entries'] if record['revealed'] or entry['actor']==actor]
    elif op=='vote@3':
        item.update(candidates=copy.deepcopy(record['candidates']),eligible=actor in record['effective']['actors'],submitted=any(entry['actor']==actor for entry in record['entries']),opensAt=record['effective']['opensAt'],closesAt=record['effective']['closesAt'])
        item['entries']=[copy.deepcopy(entry) for entry in record['entries'] if entry['actor']==actor or record['revealed'] or definition['ballots']=='group']
    elif op=='present@3':item['output']=copy.deepcopy(record['output'])
