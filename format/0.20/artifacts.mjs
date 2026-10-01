// Typed contribution semantics, independent JavaScript implementation.
export const ARTIFACT_OPS=['artifact_pool@1','assign_artifacts@1','artifact_response@1','reveal_artifact_responses@1'];
export const WINDOWS=['artifact_pool@1','artifact_response@1'];
const clone=x=>structuredClone(x),object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x),exact=(x,k)=>object(x)&&Object.keys(x).length===k.length&&k.every(n=>Object.hasOwn(x,n));
const text=x=>typeof x==='string'&&x.length>0&&!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(x);
const integer=x=>Number.isSafeInteger(x)&&x>=0;
const demand=x=>{if(!x)throw new Error('invalid_package');};
const actors=x=>Array.isArray(x)&&x.length<=100&&x.every(a=>text(a)&&a!=='system')&&new Set(x).size===x.length;
const kinds=x=>Array.isArray(x)&&x.length>=1&&x.length<=3&&x.every(k=>['text','image','audio'].includes(k))&&new Set(x).size===x.length;
export function validateArtifact(s,known,used,nested){
 demand(!nested);used.add('host_controls@1');
 if(s.op==='artifact_pool@1')demand(exact(s,['id','op','prompt','kinds','visibility'])&&text(s.prompt)&&kinds(s.kinds)&&['private','group'].includes(s.visibility));
 else if(s.op==='assign_artifacts@1'){
  demand(exact(s,['id','op','source','policy','recipients','cardinality','reuse','unmatched'])&&known.get(s.source)?.op==='artifact_pool@1');
  demand(['policy:next_nonself_source@1','policy:seeded_nonself_source@1'].includes(s.policy)&&['contributors','effective'].includes(s.recipients)&&s.cardinality==='one'&&s.reuse==='allowed'&&s.unmatched==='skip');used.add(s.policy);if(s.policy==='policy:seeded_nonself_source@1')used.add('seeded_assignment@1');
 }else if(s.op==='artifact_response@1')demand(exact(s,['id','op','source','prompt','kinds'])&&known.get(s.source)?.op==='assign_artifacts@1'&&text(s.prompt)&&kinds(s.kinds));
 else demand(exact(s,['id','op','source'])&&known.get(s.source)?.op==='artifact_response@1');
 for(const kind of s.kinds??[])if(kind!=='text')used.add(kind+'_contributions@1');
 known.set(s.id,s);
}
export const validControl=c=>exact(c,['actors','opensAt','closesAt'])&&actors(c.actors)&&(c.opensAt===null||integer(c.opensAt))&&(c.closesAt===null||integer(c.closesAt))&&(c.opensAt===null||c.closesAt===null||c.closesAt>c.opensAt);
const safeControl=(e,c)=>validControl(c)&&[c.opensAt,c.closesAt].every(t=>t===null||t+e.timingBudget<=Number.MAX_SAFE_INTEGER);
export const bindings=e=>e.state.hostActors??[...new Set([...e.participants,e.organizer])];
export function initialize(e,inputs){
 if(!e.package.requires.includes('host_controls@1')){demand(inputs===null||exact(inputs,[]));return;}
 if(Object.hasOwn(e.state,'hostInputs')){demand(inputs===null||e.canonical(inputs)===e.canonical(e.state.hostInputs));return;}
 const supplied=inputs??{};demand(object(supplied)&&Object.entries(supplied).every(([id,c])=>WINDOWS.includes(e.definitions.get(id)?.op)&&safeControl(e,c)));
 const bound=[...new Set([...e.participants,e.organizer,...Object.values(supplied).flatMap(c=>c.actors)])];demand(bound.length<=256);
 e.state.hostInputs=clone(supplied);e.state.controls=clone(supplied);e.state.hostActors=bound;
}
export function control(e,f){
 if(!Object.hasOwn(e.state.controls,f.step.id))Object.defineProperty(e.state.controls,f.step.id,{value:{actors:[...e.participants],opensAt:null,closesAt:null},enumerable:true,writable:true,configurable:true});
 return e.state.controls[f.step.id];
}
export const opening=(e,f)=>control(e,f).opensAt??e.state.openedAt;
function validValue(e,actor,v,allowed){
 if(!object(v)||!allowed.includes(v.kind))return false;
 if(v.kind==='text')return exact(v,['kind','text'])&&text(v.text);
 return exact(v,['kind','ref'])&&text(v.ref)&&[...v.ref].length<=256&&typeof e.authorizeArtifact==='function'&&e.authorizeArtifact(actor,v.ref,v.kind)===true;
}
export function settleArtifact(e,f,now){
 const s=f.step,r=e.record(f);
 if(WINDOWS.includes(s.op)){
  const c=control(e,f);r.effective=clone(c);
  if(s.op==='artifact_response@1'){r.assignments=clone(e.source(s.source,f).assignments);if(!r.assignments.length){r.closed=true;e.next(e.state.openedAt);return 'advance';}}
  if(c.closesAt!==null&&now>=c.closesAt){r.closed=true;e.next(Math.max(c.closesAt,e.state.openedAt));return 'advance';}
  return 'wait';
 }
 if(s.op==='assign_artifacts@1'){
  const pool=e.source(s.source,f),roster=pool.effective.actors,entries=pool.entries.filter(x=>roster.includes(x.actor));
  r.recipients=roster.filter(a=>s.recipients==='effective'||entries.some(x=>x.actor===a));r.assignments=[];r.unmatched=[];
  for(const actor of r.recipients){
   const eligible=entries.filter(x=>x.actor!==actor);if(!eligible.length){r.unmatched.push(actor);continue;}
   let chosen;
   if(s.policy==='policy:next_nonself_source@1'){
    const distance=x=>(roster.indexOf(x.actor)-roster.indexOf(actor)+roster.length)%roster.length;chosen=eligible.reduce((best,x)=>distance(x)<distance(best)?x:best);
   }else chosen=eligible.length===1?eligible[0]:eligible[e.randomIndex(eligible.length)];
   r.assignments.push({actor,sourceActor:chosen.actor,itemId:chosen.itemId,value:clone(chosen.value)});
  }
 }else e.source(s.source,f).revealed=true;
 r.closed=true;e.next(e.state.openedAt);return 'advance';
}
export function artifactEvent(e,f,ev){
 const s=f.step,r=e.record(f),c=control(e,f),payload=ev.payload;
 if(ev.actor==='system'&&ev.type==='configure'){
  if(!safeControl(e,payload)||payload.closesAt!==null&&payload.closesAt<=ev.at)return false;
  const bound=[...new Set([...bindings(e),...payload.actors])];if(bound.length>256)return false;
  e.state.controls[s.id]=clone(payload);e.state.hostActors=bound;r.effective=clone(payload);return true;
 }
 if(ev.actor==='system'&&ev.type==='close'&&exact(payload,[])){r.closed=true;e.next(ev.at);return true;}
 if(ev.type!=='submit'||!c.actors.includes(ev.actor)||ev.at<opening(e,f)||r.entries.some(x=>x.actor===ev.actor))return false;
 if(s.op==='artifact_pool@1'){
  if(!exact(payload,['itemId','value'])||!text(payload.itemId)||r.entries.some(x=>x.itemId===payload.itemId)||!validValue(e,ev.actor,payload.value,s.kinds))return false;
  r.entries.push({actor:ev.actor,itemId:payload.itemId,value:clone(payload.value)});return true;
 }
 const assigned=r.assignments.find(a=>a.actor===ev.actor);
 if(!assigned||!exact(payload,['itemId','value'])||payload.itemId!==assigned.itemId||!validValue(e,ev.actor,payload.value,s.kinds))return false;
 r.entries.push({actor:ev.actor,source:{actor:assigned.sourceActor,itemId:assigned.itemId,value:clone(assigned.value)},value:clone(payload.value)});return true;
}
export function projectArtifact(e,r,item,actor){
 if(r.op==='artifact_pool@1'){
  item.count=r.entries.length;item.eligible=r.effective.actors.includes(actor);item.opensAt=r.effective.opensAt;item.closesAt=r.effective.closesAt;item.entries=r.entries.filter(x=>x.actor===actor||e.findStep(r.step).visibility==='group').map(clone);
 }else if(['assign_artifacts@1','artifact_response@1'].includes(r.op)){
  const a=r.assignments.find(x=>x.actor===actor);item.assignment=a?{itemId:a.itemId,value:clone(a.value)}:null;
  if(r.op==='assign_artifacts@1'){item.eligible=r.recipients.includes(actor);item.unmatched=r.unmatched.includes(actor);}
  else{
   item.count=r.entries.length;item.eligible=r.effective.actors.includes(actor)&&a!==undefined;item.opensAt=r.effective.opensAt;item.closesAt=r.effective.closesAt;
   item.entries=r.entries.filter(x=>r.revealed||x.actor===actor).map(x=>r.revealed?clone(x):{actor,source:{itemId:x.source.itemId,value:clone(x.source.value)},value:clone(x.value)});
  }
 }
}
