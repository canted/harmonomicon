// Contribution choices, private current ballots, outcomes and linked rounds.
// Independently implemented JavaScript semantics for candidate 0.22.
import {randomInt} from 'node:crypto';
import {control,opening,validControl,bindings} from './artifacts.mjs';
export const VOTING_OPS=['artifact_pool@2','vote@1','tally@2','select@1','present@1','reveal_ballots@1'];
export const VOTING_POLICIES=['policy:most_votes@1','policy:random_tie@1'];
const clone=x=>structuredClone(x),object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x),exact=(x,keys)=>object(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
const text=x=>typeof x==='string'&&x.length>0&&!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(x);
const name=x=>typeof x==='string'&&/^[a-z][a-z0-9_]{0,47}$(?![\s\S])/.test(x);
const integer=x=>Number.isSafeInteger(x)&&x>=0;
const demand=x=>{if(!x)throw new Error('invalid_package');};
const kinds=x=>Array.isArray(x)&&x.length>=1&&x.length<=3&&x.every(k=>['text','image','audio'].includes(k))&&new Set(x).size===x.length;
const ref=x=>exact(x,['source','itemId'])&&text(x.source)&&text(x.itemId);
const sameRef=(a,b)=>a.source===b.source&&a.itemId===b.itemId;
const typedPool=x=>['artifact_pool@1','artifact_pool@2'].includes(x?.op);
function selectedPool(id,known){
 const select=known.get(id),tally=known.get(select?.source),vote=known.get(tally?.source);
 if(select?.op!=='select@1'||tally?.op!=='tally@2'||vote?.op!=='vote@1'||!exact(vote.candidates,['source']))return null;
 const pool=known.get(vote.candidates.source);return typedPool(pool)?pool:null;
}
export function validateVoting(s,known,used,nested,rounds){
 demand(!nested);
 if(s.op==='artifact_pool@2'){
  demand(exact(s,['id','op','prompt','kinds','visibility','round','input'])&&text(s.prompt)&&kinds(s.kinds)&&['private','group'].includes(s.visibility)&&name(s.round)&&!rounds.has(s.round));
  const input=s.input;
  demand(input===null||exact(input,['value'])&&exact(input.value,['kind','text'])&&input.value.kind==='text'&&text(input.value.text)||exact(input,['result'])&&text(input.result)&&selectedPool(input.result,known)!==null);
  rounds.add(s.round);used.add('host_controls@1');
  for(const kind of s.kinds)if(kind!=='text')used.add(kind+'_contributions@1');
 }else if(s.op==='vote@1'){
  demand(exact(s,['id','op','prompt','candidates','changes','ballots'])&&text(s.prompt)&&['allowed','forbidden'].includes(s.changes)&&['private','group'].includes(s.ballots));
  const c=s.candidates;
  demand(exact(c,['source'])&&typedPool(known.get(c.source))||exact(c,['options'])&&Array.isArray(c.options)&&c.options.length>=2&&c.options.length<=32&&c.options.every(o=>exact(o,['id','label'])&&text(o.id)&&text(o.label))&&new Set(c.options.map(o=>o.id)).size===c.options.length);
  used.add('host_controls@1');
 }else if(s.op==='tally@2')demand(exact(s,['id','op','source'])&&known.get(s.source)?.op==='vote@1');
 else if(s.op==='select@1'){
  demand(exact(s,['id','op','source','policy','ties'])&&known.get(s.source)?.op==='tally@2'&&s.policy==='policy:most_votes@1'&&['unresolved','random'].includes(s.ties));
  used.add(s.policy);if(s.ties==='random')used.add('policy:random_tie@1');
 }else if(s.op==='present@1')demand(exact(s,['id','op','source','prompt','audience'])&&['tally@2','select@1'].includes(known.get(s.source)?.op)&&text(s.prompt)&&s.audience==='group');
 else demand(exact(s,['id','op','source'])&&known.get(s.source)?.op==='vote@1');
 known.set(s.id,s);
}
export function initializeVoting(e,chooseTie,restored){
 e.chooseTie=typeof chooseTie==='function'?chooseTie:count=>randomInt(count);
 if([...e.definitions.values()].some(s=>s.op==='select@1'&&s.ties==='random')){
  demand(chooseTie===null||typeof chooseTie==='function');
  if(!restored)e.state.tieDraws=0;
  demand(integer(e.state.tieDraws));
 }
}
function sourceCandidates(e,s,f){
 if(exact(s.candidates,['options']))return s.candidates.options.map(o=>({ref:{source:s.id,itemId:o.id},label:o.label}));
 const pool=e.source(s.candidates.source,f),definition=e.findStep(pool.step);
 return pool.entries.filter(x=>pool.effective.actors.includes(x.actor)).map(x=>({ref:{source:pool.step,itemId:x.itemId},actor:x.actor,value:clone(x.value),round:definition.op==='artifact_pool@2'?definition.round:null}));
}
function poolInput(e,s,f){
 if(s.input===null)return {status:'none',predecessorRound:null,candidate:null};
 if(exact(s.input,['value']))return {status:'initial',predecessorRound:null,candidate:{value:clone(s.input.value)}};
 const output=e.source(s.input.result,f).output;
 const pool=selectedPool(s.input.result,e.definitions);
 return {status:output.status,predecessorRound:pool.op==='artifact_pool@2'?pool.round:null,candidate:clone(output.selected)};
}
export function settleVoting(e,f,now){
 const s=f.step,r=e.record(f);
 if(['artifact_pool@2','vote@1'].includes(s.op)){
  r.effective=clone(control(e,f));
  if(s.op==='artifact_pool@2'){
   if(!Object.hasOwn(r,'input')){r.round=s.round;r.input=poolInput(e,s,f);r.blocked=!['none','initial','selected'].includes(r.input.status);}
   if(r.blocked){r.closed=true;e.next(e.state.openedAt);return 'advance';}
  }else{
   if(!Object.hasOwn(r,'candidates'))r.candidates=sourceCandidates(e,s,f);
   if(!r.candidates.length){r.closed=true;e.next(e.state.openedAt);return 'advance';}
  }
  if(r.effective.closesAt!==null&&now>=r.effective.closesAt){r.closed=true;e.next(Math.max(r.effective.closesAt,e.state.openedAt));return 'advance';}
  return 'wait';
 }
 if(!r.closed){
  if(s.op==='tally@2'){
   const vote=e.source(s.source,f),entries=vote.entries.filter(x=>vote.effective.actors.includes(x.actor));
   r.output={counts:vote.candidates.map(candidate=>({candidate:clone(candidate),count:entries.filter(x=>sameRef(x.candidate,candidate.ref)).length})),totalVotes:entries.length};
  }else if(s.op==='select@1'){
   const totals=clone(e.source(s.source,f).output);
   r.output={...totals,status:'no_candidates',selected:null,tied:[]};
   if(totals.counts.length){
    r.output.status='no_votes';
    if(totals.totalVotes){
     const highest=Math.max(...totals.counts.map(x=>x.count)),top=totals.counts.filter(x=>x.count===highest).map(x=>clone(x.candidate));
     if(top.length===1){r.output.status='selected';r.output.selected=top[0];}
     else{
      r.output.status='tie';r.output.tied=top;
      if(s.ties==='random'){
       const draw=e.chooseTie(top.length,e.state.tieDraws);demand(integer(draw)&&draw<top.length);
       e.state.tieDraws++;r.output.status='selected';r.output.selected=clone(top[draw]);
      }
     }
    }
   }
  }else if(s.op==='present@1')r.output=clone(e.source(s.source,f).output);
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
export function votingEvent(e,f,event){
 const s=f.step,r=e.record(f),c=control(e,f),payload=event.payload;
 if(!['artifact_pool@2','vote@1'].includes(s.op))return false;
 if(event.actor==='system'&&event.type==='configure'){
  if(!safeControl(e,payload)||payload.closesAt!==null&&payload.closesAt<=event.at)return false;
  const bound=[...new Set([...bindings(e),...payload.actors])];if(bound.length>256)return false;
  Object.defineProperty(e.state.controls,s.id,{value:clone(payload),enumerable:true,writable:true,configurable:true});e.state.hostActors=bound;r.effective=clone(payload);return true;
 }
 if(event.actor==='system'&&event.type==='close'&&exact(payload,[])){r.closed=true;e.next(event.at);return true;}
 if(event.type!=='submit'||!c.actors.includes(event.actor)||event.at<opening(e,f))return false;
 const index=r.entries.findIndex(x=>x.actor===event.actor);
 if(s.op==='artifact_pool@2'){
  if(index!==-1||!exact(payload,['itemId','value'])||!text(payload.itemId)||r.entries.some(x=>x.itemId===payload.itemId)||!validValue(e,event.actor,payload.value,s.kinds))return false;
  r.entries.push({actor:event.actor,itemId:payload.itemId,value:clone(payload.value)});return true;
 }
 if(!exact(payload,['candidate'])||!ref(payload.candidate)||!r.candidates.some(x=>sameRef(x.ref,payload.candidate))||index!==-1&&s.changes==='forbidden')return false;
 const ballot={actor:event.actor,candidate:clone(payload.candidate)};
 if(index===-1)r.entries.push(ballot);else r.entries[index]=ballot;
 return true;
}
export function projectVoting(e,r,item,actor){
 if(r.op==='artifact_pool@2'){
  item.count=r.entries.length;item.eligible=r.effective.actors.includes(actor);item.opensAt=r.effective.opensAt;item.closesAt=r.effective.closesAt;item.entries=r.entries.filter(x=>x.actor===actor||e.findStep(r.step).visibility==='group').map(clone);
  item.round=r.round;item.input=clone(r.input);item.blocked=r.blocked;
 }else if(r.op==='vote@1'){
  item.candidates=clone(r.candidates);item.eligible=r.effective.actors.includes(actor);item.submitted=r.entries.some(x=>x.actor===actor);item.opensAt=r.effective.opensAt;item.closesAt=r.effective.closesAt;
  item.entries=r.entries.filter(x=>x.actor===actor||r.revealed||e.findStep(r.step).ballots==='group').map(clone);
 }else if(r.op==='present@1')item.output=clone(r.output);
}
