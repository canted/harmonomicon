// Independent first-completed-contribution collection and invitation queue.
import {bindings,validControl,validValue} from './artifacts.mjs';
import {authorizeNewViewers} from './continuation.mjs';
export const RELAY_OPS=['first_valid@1'],RELAY_POLICIES=['policy:rolling_pair@1'],RELAY_CAPS=['invitation_queue@1'];
const qualifiedContribution=(e,r,x)=>({ref:{instance:e.state.instanceId,source:r.step,itemId:x.itemId},actor:x.actor,value:structuredClone(x.value),round:null});
const clone=structuredClone,MAX=Number.MAX_SAFE_INTEGER;
const exact=(x,keys)=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
const name=x=>typeof x==='string'&&/^[a-z][a-z0-9_]{0,47}$(?![\s\S])/.test(x);
const text=x=>typeof x==='string'&&x.length>0&&!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(x);
const integer=x=>Number.isSafeInteger(x)&&x>=0;
const uuid=x=>typeof x==='string'&&/^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$(?![\s\S])/.test(x);
const demand=x=>{if(!x)throw new Error('invalid_package');};
export function validateQueues(p,used){
  const q=Object.hasOwn(p,'queueInputs')?p.queueInputs:{};demand(q!==null&&typeof q==='object'&&!Array.isArray(q)&&Object.keys(q).length<=8&&Object.keys(q).every(name));
  demand(Object.values(q).every(d=>exact(d,['type'])&&d.type==='invitation_queue'));
  if(Object.keys(q).length)used.add('invitation_queue@1');
}
export function validateRelay(s,prior,used,nested,p,inputs,queues){
  demand(!nested&&exact(s,['id','op','prompt','kinds','policy','windowMs','retryAfterMs','input','queueInput']));
  demand(text(s.prompt)&&Array.isArray(s.kinds)&&s.kinds.length>0&&s.kinds.length<=3&&s.kinds.every(k=>['text','image','audio'].includes(k))&&new Set(s.kinds).size===s.kinds.length&&s.policy==='policy:rolling_pair@1');
  demand(integer(s.windowMs)&&s.windowMs>=1&&s.windowMs<=604800000&&integer(s.retryAfterMs)&&s.retryAfterMs>=1&&s.retryAfterMs<=604800000);
  for(const [key,declared,consumed] of [['input',p.inputs??{},inputs],['queueInput',p.queueInputs??{},queues]]){
    const v=s[key];demand(v===null||exact(v,['binding'])&&typeof v.binding==='string'&&Object.hasOwn(declared,v.binding));
    if(v!==null){if(key==='queueInput')demand(!consumed.has(v.binding));consumed.add(v.binding);}
  }
  for(const cap of [...RELAY_POLICIES,...RELAY_CAPS,'host_controls@1','seeded_assignment@1'])used.add(cap);
  for(const k of s.kinds)if(k!=='text')used.add(k+'_contributions@1');prior.set(s.id,s);
}
const validRef=r=>exact(r,['instance','source','itemId'])&&uuid(r.instance)&&name(r.source)&&text(r.itemId);
export function validQueue(q){
  return exact(q,['ref','order','canonical','notBefore'])&&exact(q.ref,['instance','source'])&&uuid(q.ref.instance)&&name(q.ref.source)&&Array.isArray(q.order)&&q.order.length<=100&&q.order.every(a=>text(a)&&a!=='system')&&new Set(q.order).size===q.order.length&&(q.canonical===null||validRef(q.canonical))&&(q.notBefore===null||integer(q.notBefore));
}
export function initializeRelay(e,q,authorize,restored){
  const supplied=restored&&q===null?e.state.queueBindings??{}:q??{},declared=e.package.queueInputs??{};
  demand(supplied!==null&&typeof supplied==='object'&&!Array.isArray(supplied)&&Object.keys(supplied).length===Object.keys(declared).length&&Object.keys(declared).every(k=>Object.hasOwn(supplied,k))&&Object.values(supplied).every(validQueue));
  demand(new Set(Object.values(supplied).map(q=>e.canonical(q.ref))).size===Object.keys(supplied).length);
  if(restored)demand(e.canonical(supplied)===e.canonical(e.state.queueBindings??{}));
  for(const s of e.definitions.values())if(RELAY_OPS.includes(s.op)&&s.queueInput!==null){
    const queue=supplied[s.queueInput.binding],candidate=s.input===null?null:e.state.inputBindings[s.input.binding].candidate;
    demand(e.canonical(queue.canonical)===e.canonical(candidate===null?null:candidate.ref));
    if(!restored){demand(queue.notBefore!==null&&e.state.clock>=queue.notBefore&&typeof authorize==='function');let valid=false;try{valid=authorize(clone(queue),bindings(e))===true;}catch{}demand(valid);}
  }
  if(Object.keys(declared).length||[...e.definitions.values()].some(s=>RELAY_OPS.includes(s.op)))if(!restored)e.state.queueBindings=clone(supplied);
}
const eligible=r=>r.order.filter(a=>a!==r.previousAuthor);
function rotate(r,actors){r.order=[...r.order.filter(a=>!actors.includes(a)),...actors.filter(a=>r.order.includes(a))];}
function finish(e,f,r,status,now,reason=null){
  if(status!=='selected'&&(status==='clock_exhausted'||BigInt(now)+BigInt(f.step.retryAfterMs)>BigInt(MAX))){status='clock_exhausted';reason='clock_limit';}
  r.status=status;r.reason=reason;r.closed=true;r.revealed=true;r.offer=null;
  r.queue={ref:{instance:e.state.instanceId,source:f.step.id},order:[...r.order],canonical:r.canonical===null?null:clone(r.canonical.ref),notBefore:status==='clock_exhausted'?null:status==='selected'?now:now+f.step.retryAfterMs};
  r.output={status,reason,selected:status==='selected'?clone(r.canonical):null,canonical:clone(r.canonical),queue:clone(r.queue)};e.next(now);
}
function offer(e,f,r,now,survivors=null,deadline=null){
  const choices=eligible(r);
  if(deadline===null&&BigInt(now)+BigInt(f.step.windowMs)+BigInt(f.step.retryAfterMs)>BigInt(MAX)){finish(e,f,r,'clock_exhausted',now,'clock_limit');return;}
  if(choices.length<2){finish(e,f,r,'paused',now,'insufficient_members');return;}
  if(r.failures>=100){finish(e,f,r,'exhausted',now,'failure_budget');return;}
  if(choices.every(a=>r.attempted.includes(a))){finish(e,f,r,'exhausted',now,'pass_complete');return;}
  const people=survivors===null?[]:survivors.filter(a=>choices.includes(a));
  const candidates=choices.filter(a=>!people.includes(a));candidates.sort((a,b)=>Number(r.attempted.includes(a))-Number(r.attempted.includes(b)));people.push(...candidates.slice(0,2-people.length));
  const prior=r.offer?.invitations??[],tickets=people.map(actor=>{
    const old=survivors!==null&&survivors.includes(actor)?prior.find(t=>t.actor===actor):null;
    if(old)return clone(old);return {actor,key:++r.nextKey,opensAt:now};
  });
  r.offer={generation:++r.generation,actors:people,invitations:tickets,opensAt:now,closesAt:deadline??now+f.step.windowMs};
}
export function settleRelay(e,f,now){
  const r=e.record(f),s=f.step;
  if(!Object.hasOwn(r,'order')){
    const candidate=s.input===null?null:clone(e.state.inputBindings[s.input.binding].candidate);let order;
    if(s.queueInput===null){order=[...e.participants];for(let i=order.length-1;i>0;i--){const j=e.randomIndex(i+1);[order[i],order[j]]=[order[j],order[i]];}}
    else{const saved=e.state.queueBindings[s.queueInput.binding].order;order=[...saved.filter(a=>e.participants.includes(a)),...e.participants.filter(a=>!saved.includes(a))];}
    Object.assign(r,{order,canonical:candidate,previousAuthor:candidate?.actor??null,attempted:[],failures:0,generation:0,nextKey:0,offer:null,status:'open',reason:null,effective:{actors:[...order],opensAt:now,closesAt:null}});offer(e,f,r,now);
  }
  if(r.closed)return 'advance';
  if(now>=r.offer.closesAt){const people=r.offer.actors;rotate(r,people);r.attempted=[...new Set([...r.attempted,...people])];r.failures++;offer(e,f,r,now);}
  return r.closed?'advance':'wait';
}
export function relayEvent(e,f,ev){
  const r=e.record(f),s=f.step,p=ev.payload,actor=ev.actor,now=ev.at;
  if(actor==='system'&&ev.type==='roster'){
    if(!exact(p,['actors'])||!validControl({actors:p.actors,opensAt:null,closesAt:null})||!authorizeNewViewers(e,{actors:p.actors,opensAt:null,closesAt:null}))return false;
    const old=r.order,current=r.offer,survivors=current.actors.filter(a=>p.actors.includes(a));
    r.order=[...old.filter(a=>p.actors.includes(a)),...p.actors.filter(a=>!old.includes(a))];e.state.hostActors=[...new Set([...bindings(e),...p.actors])];r.effective.actors=[...r.order];
    if(survivors.length!==2){r.attempted=[...new Set([...r.attempted,...current.actors.filter(a=>!survivors.includes(a))])];r.failures++;offer(e,f,r,now,survivors,current.closesAt);}return true;
  }
  const current=r.offer,ref=r.canonical?.ref??null,ticket=current.invitations.find(t=>t.actor===actor);
  if(!ticket||p.invitation!==ticket.key||e.canonical(p.predecessor)!==e.canonical(ref))return false;
  if(ev.type==='decline'&&exact(p,['invitation','predecessor'])){rotate(r,[actor]);r.attempted=[...new Set([...r.attempted,actor])];r.failures++;offer(e,f,r,now,current.actors.filter(a=>a!==actor),current.closesAt);return true;}
  if(ev.type!=='submit'||!exact(p,['invitation','predecessor','itemId','value'])||!text(p.itemId)||!validValue(e,actor,p.value,s.kinds))return false;
  const entry={actor,itemId:p.itemId,value:clone(p.value)};r.entries.push(entry);r.canonical=qualifiedContribution(e,r,entry);
  const loser=current.actors.find(a=>a!==actor);r.order=[loser,...r.order.filter(a=>a!==loser&&a!==actor),actor];finish(e,f,r,'selected',now);return true;
}
export function projectRelay(e,r,item,actor){
  Object.assign(item,{status:r.status,reason:r.reason,offer:clone(r.offer),canonical:clone(r.canonical),eligible:r.offer!==null&&r.offer.actors.includes(actor),entries:r.entries.map(x=>qualifiedContribution(e,r,x))});
  if(r.closed)item.output=clone(r.output);
}
