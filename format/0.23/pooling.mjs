// Independently implemented typed pooling, item sharing and consumer extensions.
import {control,opening,validControl,bindings} from './artifacts.mjs';
import {validInstanceId} from './continuation.mjs';
export const POOLING_OPS=['pool@2','for_items@2','assign_item@2','acknowledge@2','reveal_item@2','vote@3','tally@4','select@3','present@3','reveal_ballots@3','assign_artifacts@2','artifact_response@2','reveal_artifact_responses@2'];
export const POOLING_WINDOWS=['pool@2','vote@3','artifact_response@2'];
export const POOLING_POLICIES=['policy:next_nonself_item@1'];
const clone=x=>structuredClone(x),object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x),exact=(x,keys)=>object(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
const text=x=>typeof x==='string'&&x.length>0&&!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(x);
const name=x=>typeof x==='string'&&/^[a-z][a-z0-9_]{0,47}$(?![\s\S])/.test(x);
const integer=(x,low=0,high=Number.MAX_SAFE_INTEGER)=>Number.isSafeInteger(x)&&x>=low&&x<=high;
const demand=x=>{if(!x)throw new Error('invalid_package');};
const kinds=x=>Array.isArray(x)&&x.length>=1&&x.length<=3&&x.every(k=>['text','image','audio'].includes(k))&&new Set(x).size===x.length;
export const typedPool=s=>['artifact_pool@1','artifact_pool@2','artifact_pool@3','pool@2'].includes(s?.op);
const ref=x=>exact(x,['instance','source','itemId'])&&validInstanceId(x.instance)&&name(x.source)&&text(x.itemId);
const sameRef=(a,b)=>a.instance===b.instance&&a.source===b.source&&a.itemId===b.itemId;
function selectedPool(id,known){
 const select=known.get(id),tally=known.get(select?.source),vote=known.get(tally?.source),pool=known.get(vote?.candidates?.source);
 return select?.op==='select@2'&&tally?.op==='tally@3'&&vote?.op==='vote@2'&&pool?.op==='artifact_pool@3'||select?.op==='select@3'&&tally?.op==='tally@4'&&vote?.op==='vote@3'&&typedPool(pool)?pool:null;
}
const qualifiedInputPool=s=>s?.op==='artifact_pool@3'||s?.op==='pool@2';
const after=x=>x===null||integer(x,1,86400000);
export function validatePooling(s,known,used,nested,inItems,rounds,inputs,consumed){
 if(['assign_item@2','acknowledge@2','reveal_item@2'].includes(s.op))demand(inItems);else demand(!nested);
 if(s.op==='pool@2'){
  demand(exact(s,['id','op','prompt','kinds','perActor','visibility',...(Object.hasOwn(s,'round')?['round']:[]),...(Object.hasOwn(s,'input')?['input']:[])])&&text(s.prompt)&&kinds(s.kinds)&&integer(s.perActor,1,8)&&['private','group'].includes(s.visibility));
  if(Object.hasOwn(s,'round')&&s.round!==null){demand(name(s.round)&&!rounds.has(s.round));rounds.add(s.round);}
  const input=s.input??null;
  if(input!==null){
   if(exact(input,['binding'])){demand(name(input.binding)&&Object.hasOwn(inputs,input.binding));consumed.add(input.binding);}
   else demand(exact(input,['result'])&&text(input.result)&&selectedPool(input.result,known)!==null);
  }
  used.add('host_controls@1');
  for(const kind of s.kinds)if(kind!=='text')used.add(kind+'_contributions@1');
 }else if(s.op==='for_items@2'){
  demand(exact(s,['id','op','source','policy','steps'])&&typedPool(known.get(s.source))&&s.policy==='policy:pool_order@1');used.add(s.policy);
 }else if(s.op==='assign_item@2'){
  demand(exact(s,['id','op','policy','prompt','afterMs'])&&s.policy==='policy:claim_reader@1'&&text(s.prompt)&&after(s.afterMs));used.add(s.policy);
 }else if(s.op==='acknowledge@2')demand(exact(s,['id','op','source','prompt','afterMs'])&&known.get(s.source)?.op==='assign_item@2'&&text(s.prompt)&&after(s.afterMs));
 else if(s.op==='reveal_item@2')demand(exact(s,['id','op','source'])&&known.get(s.source)?.op==='acknowledge@2');
 else if(s.op==='vote@3'){
  demand(exact(s,['id','op','prompt','candidates','changes','ballots'])&&text(s.prompt)&&exact(s.candidates,['source'])&&typedPool(known.get(s.candidates.source))&&['allowed','forbidden'].includes(s.changes)&&['private','group'].includes(s.ballots));used.add('host_controls@1');
 }else if(s.op==='tally@4')demand(exact(s,['id','op','source'])&&known.get(s.source)?.op==='vote@3');
 else if(s.op==='select@3'){
  demand(exact(s,['id','op','source','policy','ties',...(Object.hasOwn(s,'noVotes')?['noVotes']:[])])&&known.get(s.source)?.op==='tally@4'&&s.policy==='policy:most_votes@1'&&['unresolved','random'].includes(s.ties));
  const fallback=Object.hasOwn(s,'noVotes')?s.noVotes:'unresolved';demand(['unresolved','random','retain_input'].includes(fallback));
  used.add(s.policy);if(s.ties==='random')used.add('policy:random_tie@1');
  if(fallback==='random')used.add('policy:random_candidate@1');
  if(fallback==='retain_input'){
   const pool=selectedPool(s.id,new Map([...known,[s.id,s]]));demand(qualifiedInputPool(pool)&&pool.input!==undefined&&pool.input!==null);used.add('policy:retain_input@1');
  }
 }else if(s.op==='present@3')demand(exact(s,['id','op','source','prompt','audience'])&&['tally@4','select@3'].includes(known.get(s.source)?.op)&&text(s.prompt)&&s.audience==='group');
 else if(s.op==='reveal_ballots@3')demand(exact(s,['id','op','source'])&&known.get(s.source)?.op==='vote@3');
 else if(s.op==='assign_artifacts@2'){
  demand(exact(s,['id','op','source','policy','recipients','cardinality','reuse','unmatched'])&&typedPool(known.get(s.source)));
  demand(['policy:next_nonself_item@1','policy:seeded_nonself_source@1'].includes(s.policy)&&['contributors','effective'].includes(s.recipients)&&s.cardinality==='one'&&s.reuse==='allowed'&&s.unmatched==='skip');
  used.add(s.policy);used.add('host_controls@1');if(s.policy==='policy:seeded_nonself_source@1')used.add('seeded_assignment@1');
 }else if(s.op==='artifact_response@2'){
  demand(exact(s,['id','op','source','prompt','kinds'])&&known.get(s.source)?.op==='assign_artifacts@2'&&text(s.prompt)&&kinds(s.kinds));used.add('host_controls@1');
  for(const kind of s.kinds)if(kind!=='text')used.add(kind+'_contributions@1');
 }else demand(exact(s,['id','op','source'])&&known.get(s.source)?.op==='artifact_response@2');
 if(s.op!=='for_items@2')known.set(s.id,s);
}
export function snapshot(e,pool,entry){return {ref:{instance:e.state.instanceId,source:pool.step,itemId:entry.itemId},actor:entry.actor,value:clone(entry.value),round:e.findStep(pool.step).round??null};}
function input(e,s,f){
 if(s.input===null||s.input===undefined)return {status:'none',predecessorRound:null,candidate:null,via:null};
 if(exact(s.input,['binding'])){const bound=e.state.inputBindings[s.input.binding];return {status:'initial',predecessorRound:bound.via.round,candidate:clone(bound.candidate),via:clone(bound.via)};}
 const result=e.source(s.input.result,f).output,pool=selectedPool(s.input.result,e.definitions),round=pool.round??null;
 return {status:result.status,predecessorRound:round,candidate:clone(result.selected),via:{instance:e.state.instanceId,result:s.input.result,round}};
}
function currentItem(e,f){return e.state.typedItems[f.itemLoop].items.find(x=>sameRef(x.ref,f.item));}
export function canClaimItem(e,r,actor){return e.plan[e.state.pc]?.key===r.key&&!r.closed&&r.reader===null&&r.readers.includes(actor);}
function draw(e,candidates){
 if(candidates.length===1)return clone(candidates[0]);
 demand(integer(e.state.tieDraws)&&e.state.tieDraws<Number.MAX_SAFE_INTEGER);
 const index=e.chooseTie(candidates.length,e.state.tieDraws);demand(integer(index,0,candidates.length-1));e.state.tieDraws++;return clone(candidates[index]);
}
export function settlePooling(e,f,now){
 const s=f.step;
 if(s.op==='for_items@2'){
  const pool=e.source(s.source,f),actors=clone(pool.effective.actors),items=pool.entries.filter(x=>actors.includes(x.actor)).map(x=>snapshot(e,pool,x));
  e.state.typedItems??={};Object.defineProperty(e.state.typedItems,s.id,{value:{items,actors},enumerable:true,writable:true,configurable:true});
  const frames=items.flatMap((candidate,i)=>e.expand(s.steps,null,i,candidate.ref).map(frame=>({...frame,itemLoop:s.id})));
  e.plan.splice(e.state.pc,1,...frames);return 'advance';
 }
 const r=e.record(f);
 if(POOLING_WINDOWS.includes(s.op)){
  r.effective=clone(control(e,f));
  if(s.op==='pool@2'){
   if(!Object.hasOwn(r,'input')){r.round=s.round??null;r.input=input(e,s,f);r.blocked=!['none','initial','selected'].includes(r.input.status);}
   if(r.blocked){r.closed=true;e.next(e.state.openedAt);return 'advance';}
  }else if(s.op==='vote@3'){
   if(!Object.hasOwn(r,'candidates')){const pool=e.source(s.candidates.source,f);r.candidates=pool.entries.filter(x=>pool.effective.actors.includes(x.actor)).map(x=>snapshot(e,pool,x));}
   if(!r.candidates.length){r.closed=true;e.next(e.state.openedAt);return 'advance';}
  }else{
   r.assignments=clone(e.source(s.source,f).assignments);if(!r.assignments.length){r.closed=true;e.next(e.state.openedAt);return 'advance';}
  }
  if(r.effective.closesAt!==null&&now>=r.effective.closesAt){r.closed=true;e.next(Math.max(r.effective.closesAt,e.state.openedAt));return 'advance';}
  return 'wait';
 }
 if(s.op==='assign_item@2'||s.op==='acknowledge@2'){
  if(s.op==='assign_item@2'){
   if(!Object.hasOwn(r,'candidate')){r.candidate=clone(currentItem(e,f));r.readers=e.state.typedItems[f.itemLoop].actors.filter(a=>a!==r.candidate.actor);r.reader=null;}
   if(!r.readers.length){r.closed=true;e.next(e.state.openedAt);return 'advance';}
  }else{
   r.reader=e.source(s.source,f).reader;r.acknowledged??=false;
   if(r.reader===null){r.closed=true;e.next(e.state.openedAt);return 'advance';}
  }
  const deadline=e.deadline(f);if(deadline!==null&&now>=deadline){r.closed=true;e.next(Math.max(deadline,e.state.openedAt));return 'advance';}
  return 'wait';
 }
 if(!r.closed){
  if(s.op==='reveal_item@2')r.candidate=e.source(s.source,f).acknowledged?clone(currentItem(e,f)):null;
  else if(s.op==='assign_artifacts@2'){
   const pool=e.source(s.source,f),actors=pool.effective.actors,items=pool.entries.filter(x=>actors.includes(x.actor));
   r.recipients=actors.filter(a=>s.recipients==='effective'||items.some(x=>x.actor===a));r.assignments=[];r.unmatched=[];
   for(const actor of r.recipients){
    const eligible=items.filter(x=>x.actor!==actor);if(!eligible.length){r.unmatched.push(actor);continue;}
    let chosen;
    if(s.policy==='policy:next_nonself_item@1'){
     const distance=x=>(actors.indexOf(x.actor)-actors.indexOf(actor)+actors.length)%actors.length;
     chosen=eligible.reduce((best,x)=>distance(x)<distance(best)?x:best);
    }else chosen=eligible.length===1?eligible[0]:eligible[e.randomIndex(eligible.length)];
    r.assignments.push({actor,candidate:snapshot(e,pool,chosen)});
   }
  }else if(s.op==='reveal_artifact_responses@2')e.source(s.source,f).revealed=true;
  else if(s.op==='tally@4'){
   const vote=e.source(s.source,f),ballots=vote.entries.filter(x=>vote.effective.actors.includes(x.actor));
   r.output={counts:vote.candidates.map(candidate=>({candidate:clone(candidate),count:ballots.filter(x=>sameRef(x.candidate,candidate.ref)).length})),totalVotes:ballots.length};
  }else if(s.op==='select@3'){
   const totals=clone(e.source(s.source,f).output);r.output={...totals,status:totals.counts.length?'no_votes':'no_candidates',selected:null,tied:[],basis:null};
   if(totals.counts.length){
    if(totals.totalVotes){
     const high=Math.max(...totals.counts.map(x=>x.count)),top=totals.counts.filter(x=>x.count===high).map(x=>clone(x.candidate));
     if(top.length===1)Object.assign(r.output,{status:'selected',selected:top[0],basis:'most_votes'});
     else if(s.ties==='random')Object.assign(r.output,{status:'selected',selected:draw(e,top),tied:top,basis:'random_tie'});
     else Object.assign(r.output,{status:'tie',tied:top});
    }else if(s.noVotes==='random')Object.assign(r.output,{status:'selected',selected:draw(e,totals.counts.map(x=>x.candidate)),basis:'random_no_votes'});
    else if(s.noVotes==='retain_input'){
     const pool=selectedPool(s.id,e.definitions),source=e.source(pool.id,f).input;
     if(source.candidate!==null&&['initial','selected'].includes(source.status))Object.assign(r.output,{status:'selected',selected:clone(source.candidate),basis:'retained_input'});
    }
   }
  }else if(s.op==='present@3')r.output=clone(e.source(s.source,f).output);
  else e.source(s.source,f).revealed=true;
  r.closed=true;
 }
 e.next(e.state.openedAt);return 'advance';
}
const safeControl=(e,c)=>validControl(c)&&[c.opensAt,c.closesAt].every(t=>t===null||t+e.timingBudget<=Number.MAX_SAFE_INTEGER);
function validValue(e,actor,value,allowed){
 if(!object(value)||!allowed.includes(value.kind))return false;
 if(value.kind==='text')return exact(value,['kind','text'])&&text(value.text);
 return exact(value,['kind','ref'])&&text(value.ref)&&[...value.ref].length<=256&&typeof e.authorizeArtifact==='function'&&e.authorizeArtifact(actor,value.ref,value.kind)===true;
}
export function poolingEvent(e,f,event){
 const s=f.step,r=e.record(f),payload=event.payload;
 if(s.op==='assign_item@2'){
  if(event.type!=='claim'||!exact(payload,[])||!canClaimItem(e,r,event.actor))return false;r.reader=event.actor;r.closed=true;e.next(event.at);return true;
 }
 if(s.op==='acknowledge@2'){
  if(event.type!=='advance'||!exact(payload,[])||r.reader===null||event.actor!==r.reader)return false;r.acknowledged=true;r.closed=true;e.next(event.at);return true;
 }
 if(!POOLING_WINDOWS.includes(s.op))return false;
 const c=control(e,f);
 if(event.actor==='system'&&event.type==='configure'){
  if(!safeControl(e,payload)||payload.closesAt!==null&&payload.closesAt<=event.at)return false;
  const bound=[...new Set([...bindings(e),...payload.actors])];if(bound.length>256)return false;
  Object.defineProperty(e.state.controls,s.id,{value:clone(payload),enumerable:true,writable:true,configurable:true});e.state.hostActors=bound;r.effective=clone(payload);return true;
 }
 if(event.actor==='system'&&event.type==='close'&&exact(payload,[])){r.closed=true;e.next(event.at);return true;}
 if(event.type!=='submit'||!c.actors.includes(event.actor)||event.at<opening(e,f))return false;
 const own=r.entries.findIndex(x=>x.actor===event.actor);
 if(s.op==='pool@2'){
  if(!exact(payload,['itemId','value'])||!text(payload.itemId)||r.entries.some(x=>x.itemId===payload.itemId)||r.entries.filter(x=>x.actor===event.actor).length>=s.perActor||!validValue(e,event.actor,payload.value,s.kinds))return false;
  r.entries.push({actor:event.actor,itemId:payload.itemId,value:clone(payload.value)});return true;
 }
 if(s.op==='artifact_response@2'){
  const assignment=r.assignments.find(x=>x.actor===event.actor);
  if(own!==-1||!assignment||!exact(payload,['candidate','value'])||!ref(payload.candidate)||!sameRef(payload.candidate,assignment.candidate.ref)||!validValue(e,event.actor,payload.value,s.kinds))return false;
  r.entries.push({actor:event.actor,source:clone(assignment.candidate),value:clone(payload.value)});return true;
 }
 if(!exact(payload,['candidate'])||!ref(payload.candidate)||!r.candidates.some(x=>sameRef(x.ref,payload.candidate))||own!==-1&&s.changes==='forbidden')return false;
 const ballot={actor:event.actor,candidate:clone(payload.candidate)};if(own===-1)r.entries.push(ballot);else r.entries[own]=ballot;return true;
}
export function projectPooling(e,r,item,actor){
 if(r.op==='pool@2'){
  const definition=e.findStep(r.step),ownCount=r.entries.filter(x=>x.actor===actor).length;
  item.round=r.round;item.input=clone(r.input);item.blocked=r.blocked;item.count=r.entries.length;item.perActor=definition.perActor;item.ownCount=ownCount;item.remaining=definition.perActor-ownCount;
  item.eligible=r.effective.actors.includes(actor);item.opensAt=r.effective.opensAt;item.closesAt=r.effective.closesAt;
  item.entries=r.entries.filter(x=>x.actor===actor||definition.visibility==='group').map(x=>snapshot(e,r,x));
 }else if(r.op==='assign_item@2'){
  item.reader=r.reader;item.canClaim=canClaimItem(e,r,actor);item.assignment=actor===r.reader?clone(r.candidate):null;
 }else if(r.op==='acknowledge@2'){item.reader=r.reader;item.acknowledged=r.acknowledged;}
 else if(r.op==='reveal_item@2')item.candidate=clone(r.candidate);
 else if(r.op==='vote@3'){
  item.candidates=clone(r.candidates);item.eligible=r.effective.actors.includes(actor);item.submitted=r.entries.some(x=>x.actor===actor);item.opensAt=r.effective.opensAt;item.closesAt=r.effective.closesAt;
  item.entries=r.entries.filter(x=>x.actor===actor||r.revealed||e.findStep(r.step).ballots==='group').map(clone);
 }else if(r.op==='present@3')item.output=clone(r.output);
 else if(r.op==='assign_artifacts@2'){
  const assignment=r.assignments.find(x=>x.actor===actor);item.eligible=r.recipients.includes(actor);item.unmatched=r.unmatched.includes(actor);item.assignment=assignment?clone(assignment.candidate):null;
 }else if(r.op==='artifact_response@2'){
  const assignment=r.assignments.find(x=>x.actor===actor);item.assignment=assignment?clone(assignment.candidate):null;
  item.count=r.entries.length;item.eligible=r.effective.actors.includes(actor)&&assignment!==undefined;item.opensAt=r.effective.opensAt;item.closesAt=r.effective.closesAt;
  item.entries=r.entries.filter(x=>r.revealed||x.actor===actor).map(clone);
 }
}
