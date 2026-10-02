// Independent typed input, qualified continuation and fallback semantics.
import {control,opening,validControl,bindings} from './artifacts.mjs';
export const CONTINUATION_OPS=['artifact_pool@3','vote@2','tally@3','select@2','present@2','reveal_ballots@2'];
export const CONTINUATION_WINDOWS=['artifact_pool@3','vote@2'];
export const CONTINUATION_POLICIES=['policy:random_candidate@1','policy:retain_input@1'];
const clone=x=>structuredClone(x),object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x),exact=(x,keys)=>object(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
const text=x=>typeof x==='string'&&x.length>0&&!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(x);
const name=x=>typeof x==='string'&&/^[a-z][a-z0-9_]{0,47}$(?![\s\S])/.test(x);
const integer=x=>Number.isSafeInteger(x)&&x>=0;
const demand=x=>{if(!x)throw new Error('invalid_package');};
export const validInstanceId=x=>typeof x==='string'&&/^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$(?![\s\S])/.test(x);
const kinds=x=>Array.isArray(x)&&x.length>=1&&x.length<=3&&x.every(k=>['text','image','audio'].includes(k))&&new Set(x).size===x.length;
const validRound=x=>x===null||name(x);
const ref=x=>exact(x,['instance','source','itemId'])&&validInstanceId(x.instance)&&name(x.source)&&text(x.itemId);
const sameRef=(a,b)=>a.instance===b.instance&&a.source===b.source&&a.itemId===b.itemId;
export function validContribution(candidate){
 if(!exact(candidate,['ref','actor','value','round'])||!ref(candidate.ref)||!text(candidate.actor)||candidate.actor==='system'||!validRound(candidate.round))return false;
 const value=candidate.value;
 if(!object(value))return false;
 return value.kind==='text'?exact(value,['kind','text'])&&text(value.text):['image','audio'].includes(value.kind)&&exact(value,['kind','ref'])&&text(value.ref)&&[...value.ref].length<=256;
}
export function validBinding(binding){
 if(!exact(binding,['candidate','via'])||!validContribution(binding.candidate))return false;
 const via=binding.via,candidate=binding.candidate;
 if(exact(via,['instance','source','itemId','round']))return ref({instance:via.instance,source:via.source,itemId:via.itemId})&&validRound(via.round)&&sameRef(via,candidate.ref)&&via.round===candidate.round;
 return exact(via,['instance','result','round'])&&validInstanceId(via.instance)&&name(via.result)&&validRound(via.round);
}
function selectionPool(id,known){
 const select=known.get(id),tally=known.get(select?.source),vote=known.get(tally?.source),pool=known.get(vote?.candidates?.source);
 return select?.op==='select@2'&&tally?.op==='tally@3'&&vote?.op==='vote@2'&&pool?.op==='artifact_pool@3'?pool:null;
}
export function validateInputs(p,used){
 if(!Object.hasOwn(p,'inputs'))return;
 demand(object(p.inputs)&&Object.keys(p.inputs).length<=8&&Object.keys(p.inputs).every(name));
 for(const declaration of Object.values(p.inputs)){
  demand(exact(declaration,['type','kinds'])&&declaration.type==='contribution'&&kinds(declaration.kinds));
  for(const kind of declaration.kinds)if(kind!=='text')used.add(kind+'_contributions@1');
 }
 if(Object.keys(p.inputs).length)used.add('contribution_inputs@1');
}
export function validateContinuation(s,known,used,nested,rounds,inputs,consumed){
 demand(!nested);
 if(s.op==='artifact_pool@3'){
  demand(exact(s,['id','op','prompt','kinds','visibility','round','input'])&&text(s.prompt)&&kinds(s.kinds)&&['private','group'].includes(s.visibility)&&name(s.round)&&!rounds.has(s.round));
  if(s.input!==null){
   if(exact(s.input,['binding'])){demand(name(s.input.binding)&&Object.hasOwn(inputs,s.input.binding));consumed.add(s.input.binding);}
   else demand(exact(s.input,['result'])&&text(s.input.result)&&selectionPool(s.input.result,known)!==null);
  }
  rounds.add(s.round);used.add('host_controls@1');
  for(const kind of s.kinds)if(kind!=='text')used.add(kind+'_contributions@1');
 }else if(s.op==='vote@2'){
  demand(exact(s,['id','op','prompt','candidates','changes','ballots'])&&text(s.prompt)&&exact(s.candidates,['source'])&&known.get(s.candidates.source)?.op==='artifact_pool@3'&&['allowed','forbidden'].includes(s.changes)&&['private','group'].includes(s.ballots));used.add('host_controls@1');
 }else if(s.op==='tally@3')demand(exact(s,['id','op','source'])&&known.get(s.source)?.op==='vote@2');
 else if(s.op==='select@2'){
  demand(exact(s,['id','op','source','policy','ties',...(Object.hasOwn(s,'noVotes')?['noVotes']:[])])&&known.get(s.source)?.op==='tally@3'&&s.policy==='policy:most_votes@1'&&['unresolved','random'].includes(s.ties));
  const fallback=Object.hasOwn(s,'noVotes')?s.noVotes:'unresolved';demand(['unresolved','random','retain_input'].includes(fallback));
  used.add(s.policy);if(s.ties==='random')used.add('policy:random_tie@1');
  if(fallback==='random')used.add('policy:random_candidate@1');
  if(fallback==='retain_input'){const pool=selectionPool(s.id,new Map([...known,[s.id,s]]));demand(pool!==null&&pool.input!==null);used.add('policy:retain_input@1');}
 }else if(s.op==='present@2')demand(exact(s,['id','op','source','prompt','audience'])&&['tally@3','select@2'].includes(known.get(s.source)?.op)&&text(s.prompt)&&s.audience==='group');
 else demand(exact(s,['id','op','source'])&&known.get(s.source)?.op==='vote@2');
 known.set(s.id,s);
}
const needsIdentity=e=>Object.keys(e.package.inputs??{}).length>0||[...e.definitions.values()].some(s=>CONTINUATION_OPS.includes(s.op));
function attested(e,binding,viewers){
 try{return typeof e.authorizeInput==='function'&&e.authorizeInput(clone(binding),[...viewers])===true;}catch{return false;}
}
export function initializeContinuation(e,instanceId,inputBindings,authorizeInput,chooseTie,restored){
 e.authorizeInput=authorizeInput;
 if(!needsIdentity(e)){demand(inputBindings===null||exact(inputBindings,[]));return;}
 const identity=restored&&instanceId===null?e.state.instanceId:instanceId;
 demand(validInstanceId(identity));
 const supplied=restored&&inputBindings===null?e.state.inputBindings:inputBindings??{};
 demand(exact(supplied,Object.keys(e.package.inputs??{})));
 for(const [key,binding] of Object.entries(supplied))demand(validBinding(binding)&&e.package.inputs[key].kinds.includes(binding.candidate.value.kind));
 if(restored)demand(identity===e.state.instanceId&&e.canonical(supplied)===e.canonical(e.state.inputBindings));
 else{
  demand(Object.values(supplied).every(binding=>attested(e,binding,bindings(e))));
  e.state.instanceId=identity;e.state.inputBindings=clone(supplied);
 }
 if([...e.definitions.values()].some(s=>s.op==='select@2'&&(s.ties==='random'||s.noVotes==='random'))){
  demand(chooseTie===null||typeof chooseTie==='function');
  if(!restored&&!Object.hasOwn(e.state,'tieDraws'))e.state.tieDraws=0;
  demand(integer(e.state.tieDraws));
 }
}
export function authorizeNewViewers(e,payload){
 if(!validControl(payload)||![payload.opensAt,payload.closesAt].every(t=>t===null||t+e.timingBudget<=Number.MAX_SAFE_INTEGER))return false;
 const current=bindings(e),viewers=[...new Set([...current,...payload.actors])];
 if(viewers.length>256)return false;
 if(!Object.keys(e.state.inputBindings??{}).length)return true;
 if(viewers.length===current.length)return true;
 return Object.values(e.state.inputBindings).every(binding=>attested(e,binding,viewers));
}
function poolInput(e,s,f){
 if(s.input===null)return {status:'none',predecessorRound:null,candidate:null,via:null};
 if(exact(s.input,['binding'])){
  const binding=e.state.inputBindings[s.input.binding];return {status:'initial',predecessorRound:binding.via.round,candidate:clone(binding.candidate),via:clone(binding.via)};
 }
 const result=e.source(s.input.result,f).output,pool=selectionPool(s.input.result,e.definitions),via={instance:e.state.instanceId,result:s.input.result,round:pool.round};
 return {status:result.status,predecessorRound:pool.round,candidate:clone(result.selected),via};
}
function candidateSnapshot(e,pool,entry){return {ref:{instance:e.state.instanceId,source:pool.step,itemId:entry.itemId},actor:entry.actor,value:clone(entry.value),round:e.findStep(pool.step).round};}
function choose(e,values){
 if(values.length===1)return clone(values[0]);
 demand(integer(e.state.tieDraws)&&e.state.tieDraws<Number.MAX_SAFE_INTEGER);
 const index=e.chooseTie(values.length,e.state.tieDraws);demand(integer(index)&&index<values.length);e.state.tieDraws++;return clone(values[index]);
}
export function settleContinuation(e,f,now){
 const s=f.step,r=e.record(f);
 if(CONTINUATION_WINDOWS.includes(s.op)){
  r.effective=clone(control(e,f));
  if(s.op==='artifact_pool@3'){
   if(!Object.hasOwn(r,'input')){r.round=s.round;r.input=poolInput(e,s,f);r.blocked=!['none','initial','selected'].includes(r.input.status);}
   if(r.blocked){r.closed=true;e.next(e.state.openedAt);return 'advance';}
  }else{
   if(!Object.hasOwn(r,'candidates')){const pool=e.source(s.candidates.source,f);r.candidates=pool.entries.filter(x=>pool.effective.actors.includes(x.actor)).map(x=>candidateSnapshot(e,pool,x));}
   if(!r.candidates.length){r.closed=true;e.next(e.state.openedAt);return 'advance';}
  }
  if(r.effective.closesAt!==null&&now>=r.effective.closesAt){r.closed=true;e.next(Math.max(r.effective.closesAt,e.state.openedAt));return 'advance';}
  return 'wait';
 }
 if(!r.closed){
  if(s.op==='tally@3'){
   const vote=e.source(s.source,f),entries=vote.entries.filter(x=>vote.effective.actors.includes(x.actor));
   r.output={counts:vote.candidates.map(candidate=>({candidate:clone(candidate),count:entries.filter(x=>sameRef(x.candidate,candidate.ref)).length})),totalVotes:entries.length};
  }else if(s.op==='select@2'){
   const totals=clone(e.source(s.source,f).output);
   r.output={...totals,status:totals.counts.length?'no_votes':'no_candidates',selected:null,tied:[],basis:null};
   if(totals.counts.length){
    if(totals.totalVotes){
     const high=Math.max(...totals.counts.map(x=>x.count)),top=totals.counts.filter(x=>x.count===high).map(x=>clone(x.candidate));
     if(top.length===1)Object.assign(r.output,{status:'selected',selected:top[0],basis:'most_votes'});
     else if(s.ties==='random')Object.assign(r.output,{status:'selected',selected:choose(e,top),tied:top,basis:'random_tie'});
     else Object.assign(r.output,{status:'tie',tied:top});
    }else if(s.noVotes==='random')Object.assign(r.output,{status:'selected',selected:choose(e,totals.counts.map(x=>x.candidate)),basis:'random_no_votes'});
    else if(s.noVotes==='retain_input'){
     const pool=selectionPool(s.id,e.definitions),input=e.source(pool.id,f).input;
     if(input.candidate!==null&&['initial','selected'].includes(input.status))Object.assign(r.output,{status:'selected',selected:clone(input.candidate),basis:'retained_input'});
    }
   }
  }else if(s.op==='present@2')r.output=clone(e.source(s.source,f).output);
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
export function continuationEvent(e,f,event){
 const s=f.step,r=e.record(f),c=control(e,f),payload=event.payload;
 if(!CONTINUATION_WINDOWS.includes(s.op))return false;
 if(event.actor==='system'&&event.type==='configure'){
  if(!safeControl(e,payload)||payload.closesAt!==null&&payload.closesAt<=event.at)return false;
  const bound=[...new Set([...bindings(e),...payload.actors])];if(bound.length>256)return false;
  Object.defineProperty(e.state.controls,s.id,{value:clone(payload),enumerable:true,writable:true,configurable:true});e.state.hostActors=bound;r.effective=clone(payload);return true;
 }
 if(event.actor==='system'&&event.type==='close'&&exact(payload,[])){r.closed=true;e.next(event.at);return true;}
 if(event.type!=='submit'||!c.actors.includes(event.actor)||event.at<opening(e,f))return false;
 const index=r.entries.findIndex(x=>x.actor===event.actor);
 if(s.op==='artifact_pool@3'){
  if(index!==-1||!exact(payload,['itemId','value'])||!text(payload.itemId)||r.entries.some(x=>x.itemId===payload.itemId)||!validValue(e,event.actor,payload.value,s.kinds))return false;
  r.entries.push({actor:event.actor,itemId:payload.itemId,value:clone(payload.value)});return true;
 }
 if(!exact(payload,['candidate'])||!ref(payload.candidate)||!r.candidates.some(x=>sameRef(x.ref,payload.candidate))||index!==-1&&s.changes==='forbidden')return false;
 const ballot={actor:event.actor,candidate:clone(payload.candidate)};if(index===-1)r.entries.push(ballot);else r.entries[index]=ballot;return true;
}
export function projectContinuation(e,r,item,actor){
 if(r.op==='artifact_pool@3'){
  item.count=r.entries.length;item.eligible=r.effective.actors.includes(actor);item.opensAt=r.effective.opensAt;item.closesAt=r.effective.closesAt;item.entries=r.entries.filter(x=>x.actor===actor||e.findStep(r.step).visibility==='group').map(clone);
  item.round=r.round;item.input=clone(r.input);item.blocked=r.blocked;
 }else if(r.op==='vote@2'){
  item.candidates=clone(r.candidates);item.eligible=r.effective.actors.includes(actor);item.submitted=r.entries.some(x=>x.actor===actor);item.opensAt=r.effective.opensAt;item.closesAt=r.effective.closesAt;item.entries=r.entries.filter(x=>x.actor===actor||r.revealed||e.findStep(r.step).ballots==='group').map(clone);
 }else if(r.op==='present@2')item.output=clone(r.output);
}
