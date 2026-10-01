// Independently implemented candidate 0.22 runbook interpreter.
import fs from 'node:fs';
import {ARTIFACT_OPS,WINDOWS,validateArtifact,initialize,bindings,control,settleArtifact,artifactEvent,projectArtifact} from './artifacts.mjs';
import {VOTING_OPS,VOTING_POLICIES,validateVoting,settleVoting,votingEvent,projectVoting,initializeVoting} from './voting.mjs';
import {CONTINUATION_OPS,CONTINUATION_POLICIES,CONTINUATION_WINDOWS,validateInputs,validateContinuation,initializeContinuation,settleContinuation,continuationEvent,projectContinuation,authorizeNewViewers} from './continuation.mjs';
WINDOWS.push(...CONTINUATION_WINDOWS);
export const FORMAT='harmonomicon.activity-package/0.22';
export const OPS=[...ARTIFACT_OPS,...VOTING_OPS,...CONTINUATION_OPS,'collect@1','reveal@1','append@1','tally@1','for_each@1','pool@1','for_items@1','assign_item@1','acknowledge@1','reveal_item@1','partition@1','collect_group@1','pause@1','wait_until@1','collect_until@1','route@1','rate@1','aggregate@1','publish_ranking@1','for_windows@1','collect_window@1','assign_sources@1','respond@1','reveal_responses@1'];
const BASE_CAPS=['identity@1','serial_events@1','durable_state@1','private_views@1','clock@1','text@1'];
export const POLICIES=[...VOTING_POLICIES,...CONTINUATION_POLICIES,'policy:pool_order@1','policy:claim_reader@1','policy:roster_chunks@1','policy:organizer_groups@1','policy:roster_offset@1','policy:sum_scores@1','policy:mean_scaled_scores@1','policy:competition_rank_all_ties@1','policy:next_nonself_source@1','policy:seeded_nonself_source@1'];
export const CAPS=[...BASE_CAPS,...POLICIES,'instance_settings@1','integer_values@1','completion_status@1','seeded_assignment@1','image_contributions@1','audio_contributions@1','host_controls@1','contribution_inputs@1'];
const MAX=Number.MAX_SAFE_INTEGER;
const clone=x=>structuredClone(x);
const object=x=>x!==null && typeof x==='object' && !Array.isArray(x);
const exact=(x,keys)=>object(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
const text=x=>typeof x==='string'&&x.length>0;
const integer=(x,lo=0,hi=MAX)=>Number.isSafeInteger(x)&&x>=lo&&x<=hi;
const name=x=>typeof x==='string'&&/^[a-z][a-z0-9_]{0,47}$(?![\s\S])/.test(x);
const demand=x=>{if(!x)throw new Error('invalid_package');};
function scalar(x){
  if(typeof x==='string')return !/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(x);
  if(Array.isArray(x))return x.every(scalar);
  if(object(x))return Object.entries(x).every(([k,v])=>scalar(k)&&scalar(v));
  return x===null||typeof x==='boolean'||integer(x);
}
export function canonical(x){
  if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';
  if(object(x))return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
  return JSON.stringify(x);
}
export function validate(p){
  demand(scalar(p)&&exact(p,['format','id','version','content','provenance','participants','requires','runbook','settings',...(object(p)&&Object.hasOwn(p,'inputs')?['inputs']:[])]));
  demand(p.format===FORMAT&&typeof p.id==='string'&&/^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$(?![\s\S])/.test(p.id));
  demand(typeof p.version==='string'&&/^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$(?![\s\S])/.test(p.version));
  demand(exact(p.content,['language','title','summary','setup','prompt','participant','completion','access'])&&Object.values(p.content).every(text));
  demand(object(p.provenance)&&['original','adaptation'].includes(p.provenance.kind));
  demand(exact(p.provenance,['kind','credit','rights',...(p.provenance.kind==='adaptation'?['sourceUrl']:[])])&&Object.values(p.provenance).every(text));
  if(p.provenance.kind==='adaptation')demand(/^https?:\/\/[^\s]+$(?![\s\S])/.test(p.provenance.sourceUrl));
  demand(exact(p.participants,['min','max'])&&integer(p.participants.min,p.requires?.includes('host_controls@1')?1:2,100)&&integer(p.participants.max,p.participants.min,100));
  demand(Array.isArray(p.requires)&&p.requires.length>=1&&p.requires.length<=64&&p.requires.every(text)&&new Set(p.requires).size===p.requires.length&&BASE_CAPS.every(c=>p.requires.includes(c)));
  demand(exact(p.runbook,['steps']));
  demand(object(p.settings)&&Object.keys(p.settings).length<=16&&Object.keys(p.settings).every(name));
  for(const d of Object.values(p.settings)){
    demand(object(d)&&['time','text'].includes(d.type)&&exact(d,['type',...(Object.hasOwn(d,'default')?['default']:[])]));
    if(Object.hasOwn(d,'default'))demand(d.type==='text'&&text(d.default));
  }
  if(Object.keys(p.settings).length)demand(p.requires.includes('instance_settings@1'));
  const settingValue=(v,kind)=>{
    if(exact(v,['setting']))demand(name(v.setting)&&Object.hasOwn(p.settings,v.setting)&&p.settings[v.setting].type===kind);
    else demand(kind==='time'?integer(v):text(v));
  };
  const ids=new Set(),used=new Set(),rounds=new Set(),offsets=new Set(),consumedInputs=new Set();
  validateInputs(p,used);
  function sequence(steps,known,turn=false,items=false,windows=false){
    demand(Array.isArray(steps)&&steps.length>=1&&steps.length<=32);
    const prior=new Map(known);
    for(let i=0;i<steps.length;i++){
      const s=steps[i];
      demand(object(s)&&name(s.id)&&!ids.has(s.id)&&OPS.includes(s.op));
      ids.add(s.id);used.add(s.op);
      if(windows)demand(['collect_window@1','reveal@1','tally@1'].includes(s.op));
      if(CONTINUATION_OPS.includes(s.op)){validateContinuation(s,prior,used,turn||items||windows,rounds,p.inputs??{},consumedInputs);continue;}
      if(VOTING_OPS.includes(s.op)){validateVoting(s,prior,used,turn||items||windows,rounds);continue;}
      if(ARTIFACT_OPS.includes(s.op)){validateArtifact(s,prior,used,turn||items||windows);continue;}
      if(s.op==='for_windows@1'){
        demand(!turn&&!items&&!windows&&exact(s,['id','op','startsAt','intervalMs','windowMs','occurrences','prompt','steps']));
        settingValue(s.startsAt,'time');settingValue(s.prompt,'text');
        demand(integer(s.intervalMs,1)&&integer(s.windowMs,1,s.intervalMs)&&integer(s.occurrences,1,366));
        demand(Array.isArray(s.steps)&&s.steps[0]?.op==='collect_window@1'&&s.steps.filter(x=>x.op==='collect_window@1').length===1);
        sequence(s.steps,new Map(),false,false,true);continue;
      }
      if(s.op==='for_each@1'){
        demand(!turn&&!items&&exact(s,['id','op','over','steps'])&&s.over==='participants');
        sequence(s.steps,prior,true);continue;
      }
      if(s.op==='for_items@1'){
        demand(!turn&&!items&&exact(s,['id','op','source','policy','steps'])&&prior.get(s.source)?.op==='pool@1'&&s.policy==='policy:pool_order@1');
        used.add(s.policy);sequence(s.steps,prior,false,true);continue;
      }
      if(s.op==='assign_sources@1'){
        const source=prior.get(s.source);
        demand(!turn&&!items&&!windows&&exact(s,['id','op','source','recipients','policy','cardinality','reuse','unmatched'])&&source?.op==='pool@1'&&source.perActor===1);
        demand(['participants','contributors'].includes(s.recipients)&&['policy:next_nonself_source@1','policy:seeded_nonself_source@1'].includes(s.policy));
        demand(s.cardinality==='one'&&s.reuse==='allowed'&&s.unmatched==='skip');used.add(s.policy);
        if(s.policy==='policy:seeded_nonself_source@1')used.add('seeded_assignment@1');prior.set(s.id,s);
      }else if(s.op==='respond@1'){
        demand(!turn&&!items&&!windows&&exact(s,['id','op','source','prompt','close','afterMs'])&&prior.get(s.source)?.op==='assign_sources@1'&&text(s.prompt));
        demand(['all','deadline'].includes(s.close)&&integer(s.afterMs,1,86400000));prior.set(s.id,s);
      }else if(s.op==='reveal_responses@1'){
        demand(!turn&&!items&&!windows&&exact(s,['id','op','source'])&&prior.get(s.source)?.op==='respond@1');
      }else if(s.op==='route@1'){
        const pool=prior.get(s.source);
        demand(!turn&&!items&&exact(s,['id','op','source','policy','round','offset'])&&pool?.op==='pool@1'&&pool.perActor===1);
        demand(s.policy==='policy:roster_offset@1'&&name(s.round)&&!rounds.has(s.round)&&integer(s.offset,1,p.participants.max-1)&&!offsets.has(s.source+':'+s.offset));
        rounds.add(s.round);offsets.add(s.source+':'+s.offset);used.add(s.policy);prior.set(s.id,s);
      }else if(s.op==='rate@1'){
        demand(!turn&&!items&&exact(s,['id','op','source','prompt','min','max','close','afterMs'])&&prior.get(s.source)?.op==='route@1'&&text(s.prompt));
        demand(integer(s.min,0,1000000)&&integer(s.max,s.min,1000000)&&['all','deadline'].includes(s.close)&&integer(s.afterMs,1,86400000));
        used.add('integer_values@1');prior.set(s.id,s);
      }else if(s.op==='aggregate@1'){
        demand(!turn&&!items&&exact(s,['id','op','sources','policy','targetCount'])&&Array.isArray(s.sources)&&s.sources.length>=1&&s.sources.length<=10&&new Set(s.sources).size===s.sources.length);
        demand(s.sources.every(id=>prior.get(id)?.op==='rate@1'));const rates=s.sources.map(id=>prior.get(id));
        demand(new Set(rates.map(x=>prior.get(x.source).source)).size===1&&new Set(rates.map(x=>x.source)).size===rates.length&&new Set(rates.map(x=>x.min+':'+x.max)).size===1);
        demand(['policy:sum_scores@1','policy:mean_scaled_scores@1'].includes(s.policy)&&(s.policy==='policy:sum_scores@1'?s.targetCount===null:integer(s.targetCount,1,100)));
        used.add(s.policy);prior.set(s.id,s);
      }else if(s.op==='publish_ranking@1'){
        demand(!turn&&!items&&exact(s,['id','op','source','limit','policy'])&&prior.get(s.source)?.op==='aggregate@1'&&integer(s.limit,1,100)&&s.policy==='policy:competition_rank_all_ties@1');
        demand(!steps.slice(0,i).some(old=>old.op==='publish_ranking@1'&&old.source===s.source));used.add(s.policy);
      }else if(s.op==='wait_until@1'){
        demand(!turn&&!items&&exact(s,['id','op','until','prompt']));settingValue(s.until,'time');settingValue(s.prompt,'text');
      }else if(s.op==='pool@1'){
        demand(!turn&&!items&&exact(s,['id','op','prompt','perActor','close','afterMs'])&&text(s.prompt)&&integer(s.perActor,1,8));
        demand(['all','organizer','deadline'].includes(s.close)&&(s.afterMs===null||integer(s.afterMs,1,86400000))&&(s.close!=='deadline'||s.afterMs!==null));
        prior.set(s.id,s);
      }else if(s.op==='assign_item@1'){
        demand(items&&exact(s,['id','op','policy','prompt','afterMs'])&&s.policy==='policy:claim_reader@1'&&text(s.prompt)&&(s.afterMs===null||integer(s.afterMs,1,86400000)));
        used.add(s.policy);prior.set(s.id,s);
      }else if(s.op==='acknowledge@1'){
        demand(items&&exact(s,['id','op','source','prompt','afterMs'])&&prior.get(s.source)?.op==='assign_item@1'&&text(s.prompt)&&(s.afterMs===null||integer(s.afterMs,1,86400000)));
        prior.set(s.id,s);
      }else if(s.op==='reveal_item@1'){
        demand(items&&exact(s,['id','op','source'])&&prior.get(s.source)?.op==='acknowledge@1');
      }else if(s.op==='partition@1'){
        demand(!turn&&!items&&exact(s,['id','op','policy','minSize','maxSize','prompt','afterMs']));
        demand(['policy:roster_chunks@1','policy:organizer_groups@1'].includes(s.policy)&&integer(s.minSize,1,100)&&integer(s.maxSize,s.minSize,p.participants.max)&&text(s.prompt)&&(s.afterMs===null||integer(s.afterMs,1,86400000)));
        if(s.policy==='policy:roster_chunks@1'){demand(s.minSize===s.maxSize&&s.afterMs===null);demand(Math.ceil(p.participants.min/s.minSize)*s.minSize<=p.participants.max);}
        used.add(s.policy);prior.set(s.id,s);
      }else if(s.op==='collect_group@1'){
        demand(!turn&&!items&&exact(s,['id','op','source','prompt','close','afterMs'])&&prior.get(s.source)?.op==='partition@1'&&text(s.prompt));
        demand(['all','organizer','deadline'].includes(s.close)&&(s.afterMs===null||integer(s.afterMs,1,86400000))&&(s.close!=='deadline'||s.afterMs!==null));
        prior.set(s.id,s);
      }else if(s.op==='pause@1'){
        demand(exact(s,['id','op','prompt','afterMs'])&&text(s.prompt)&&integer(s.afterMs,1,86400000));
      }else if(['collect@1','collect_until@1','collect_window@1'].includes(s.op)){
        if(s.op==='collect_window@1'){
          demand(windows&&exact(s,['id','op','actors','prompt','fields','completion'])&&s.actors==='participants'&&['none','group'].includes(s.completion));
          settingValue(s.prompt,'text');if(s.completion==='group')used.add('completion_status@1');
        }else if(s.op==='collect_until@1'){
          demand(!turn&&!items&&exact(s,['id','op','actors','prompt','fields','until'])&&s.actors==='participants');
          settingValue(s.until,'time');settingValue(s.prompt,'text');
        }else demand(exact(s,['id','op','actors','prompt','fields','close','afterMs']));
        demand((turn?['participants','turn','others']:['participants']).includes(s.actors));
        if(s.op==='collect@1'){
          demand((turn?['all','organizer','turn']:['all','organizer']).includes(s.close));
          demand(text(s.prompt)&&(s.afterMs===null||integer(s.afterMs,1,86400000)));
        }
        demand(object(s.fields)&&Object.keys(s.fields).length>=1&&Object.keys(s.fields).length<=8&&Object.keys(s.fields).every(name));
        for(const f of Object.values(s.fields)){
          demand(object(f)&&['group','private'].includes(f.visibility));
          if(f.type==='integer'){demand(exact(f,['type','visibility','min','max'])&&integer(f.min,0,1000000)&&integer(f.max,f.min,1000000));used.add('integer_values@1');}
          else if(f.type==='image_ref'){demand(exact(f,['type','visibility']));used.add('image_contributions@1');}
          else if(f.type==='text')demand(exact(f,['type','visibility']));
          else if(f.type==='text_list')demand(exact(f,['type','visibility','count'])&&integer(f.count,1,32));
          else if(f.type==='choice')demand(exact(f,['type','visibility','options'])&&Array.isArray(f.options)&&f.options.length>=2&&f.options.length<=32&&f.options.every(text)&&new Set(f.options).size===f.options.length);
          else if(f.type==='index'){
            demand(exact(f,['type','visibility','indexOf'])&&text(f.indexOf));
            const parts=f.indexOf.split('.');let source;
            if(parts.length===1)source=s.fields[parts[0]];
            else{
              const origin=prior.get(parts[0]);
              demand(parts.length===2&&origin?.op==='collect@1'&&origin.actors==='turn');
              source=origin.fields[parts[1]];demand(source?.visibility==='group');
            }
            demand(source?.type==='text_list');
          }else demand(false);
        }
        prior.set(s.id,s);
      }else if(s.op==='append@1'){
        demand(turn&&exact(s,['id','op','prompt','afterMs'])&&text(s.prompt)&&(s.afterMs===null||integer(s.afterMs,1,86400000)));
        prior.set(s.id,s);
      }else if(s.op==='reveal@1'){
        demand(exact(s,['id','op','sources'])&&Array.isArray(s.sources)&&s.sources.length>0&&s.sources.length<=32&&new Set(s.sources).size===s.sources.length);
        demand(s.sources.every(id=>['collect@1','collect_until@1','collect_window@1'].includes(prior.get(id)?.op)));
      }else if(s.op==='tally@1'){
        demand(exact(s,['id','op','source','field']));
        const origin=prior.get(s.source);
        demand(['collect@1','collect_until@1','collect_window@1'].includes(origin?.op)&&origin.fields[s.field]?.type==='choice');
        demand(steps.slice(0,i).some(old=>old.op==='reveal@1'&&old.sources.includes(s.source)));
      }
    }
  }
  sequence(p.runbook.steps,new Map());
  demand(Object.keys(p.inputs??{}).every(k=>consumedInputs.has(k)));
  demand(ids.size<=64&&[...used].every(op=>p.requires.includes(op))&&Buffer.byteLength(canonical(p))<=1000000);
  return p;
}
export class Engine{
  constructor(p,participants,organizer,startedAt=0,state=null,settings=null,seed=null,authorizeImage=null,hostInputs=null,authorizeArtifact=null,chooseTie=null,instanceId=null,inputBindings=null,authorizeInput=null){
    validate(p);
    this.authorizeImage=authorizeImage;this.authorizeArtifact=authorizeArtifact;this.canonical=canonical;
    demand(scalar(participants)&&Array.isArray(participants)&&participants.length>=p.participants.min&&participants.length<=p.participants.max&&participants.every(a=>text(a)&&a!=='system')&&new Set(participants).size===participants.length);
    demand(scalar(organizer)&&text(organizer)&&organizer!=='system'&&(p.requires.includes('host_controls@1')||!participants.includes(organizer))&&integer(startedAt));
    this.package=p;this.participants=[...participants];this.organizer=organizer;this.definitions=new Map();
    const supplied=state!==null&&settings===null?state.settings:settings??{};
    demand(object(supplied)&&scalar(supplied)&&Object.keys(supplied).every(k=>Object.hasOwn(p.settings,k)));
    this.settings={};
    for(const [k,d] of Object.entries(p.settings)){
      demand(Object.hasOwn(supplied,k)||Object.hasOwn(d,'default'));
      const v=Object.hasOwn(supplied,k)?supplied[k]:d.default;demand(d.type==='time'?integer(v):text(v));
      Object.defineProperty(this.settings,k,{value:clone(v),enumerable:true});
    }
    if(state!==null)demand(canonical(this.settings)===canonical(state.settings));
    const index=steps=>{for(const s of steps){this.definitions.set(s.id,s);if(s.steps)index(s.steps);}};
    index(p.runbook.steps);
    for(const s of this.definitions.values())if(s.op==='route@1')demand(s.offset<participants.length);
    for(const s of this.definitions.values())if(s.op==='partition@1'){
      demand(Math.ceil(participants.length/s.maxSize)<=Math.floor(participants.length/s.minSize));
      if(s.policy==='policy:roster_chunks@1')demand(participants.length%s.minSize===0);
    }
    const budget=steps=>steps.reduce((total,s)=>total+(s.op==='for_each@1'?participants.length*budget(s.steps):s.op==='for_items@1'?participants.length*this.definitions.get(s.source).perActor*budget(s.steps):s.afterMs??0),0);
    let boundary=startedAt,scheduled=false;
    for(const s of p.runbook.steps)if(s.op==='for_windows@1'){
      const first=this.resolve(s.startsAt);demand(scheduled?first>boundary:first>=boundary);
      const end=BigInt(first)+BigInt(s.occurrences-1)*BigInt(s.intervalMs)+BigInt(s.windowMs);demand(end<=BigInt(MAX));
      boundary=Number(end);scheduled=true;
    }else if(['wait_until@1','collect_until@1'].includes(s.op)){
      const until=this.resolve(s.until);demand(scheduled?until>boundary:until>=boundary);boundary=until;scheduled=true;
    }
    this.timingBudget=budget(p.runbook.steps);demand(boundary+this.timingBudget<=MAX);
    this.expand=(steps,turn=null,iteration=null,item=null)=>steps.flatMap(s=>{
      if(s.op==='for_windows@1')return Array.from({length:s.occurrences},(_,i)=>{
        const opening=this.resolve(s.startsAt)+i*s.intervalMs,window={container:s.id,index:i,opensAt:opening,closesAt:opening+s.windowMs};
        const wait={step:s,turn:null,iteration:i,key:`${s.id}:${i}`,window:clone(window)};
        const body=this.expand(s.steps,null,i).map(f=>({...f,window:clone(window)}));return [wait,...body];
      }).flat();
      if(s.op==='for_each@1')return participants.flatMap((a,i)=>this.expand(s.steps,a,i));
      const frame={step:s,turn,iteration,key:iteration===null?s.id:`${s.id}:${iteration}`};
      if(item!==null)frame.item=clone(item);
      return [frame];
    });
    this.state=state===null?{pc:0,clock:startedAt,openedAt:startedAt,records:[],ledger:{},plan:this.expand(p.runbook.steps),settings:clone(this.settings)}:clone(state);
    const needsSeed=[...this.definitions.values()].some(s=>['assign_sources@1','assign_artifacts@1'].includes(s.op)&&s.policy==='policy:seeded_nonself_source@1');
    if(needsSeed){
      const chosen=state!==null&&seed===null?state.assignmentSeed:seed;demand(integer(chosen,1,4294967295));
      if(state!==null)demand(chosen===state.assignmentSeed&&integer(state.randomState,1,4294967295));
      else{this.state.assignmentSeed=chosen;this.state.randomState=chosen;}
    }
    initialize(this,hostInputs);initializeVoting(this,chooseTie,state!==null);initializeContinuation(this,instanceId,inputBindings,authorizeInput,chooseTie,state!==null);
    this.plan=this.state.plan;
    this.settle(this.state.clock);
  }
  resolve(v){return object(v)?this.settings[v.setting]:v;}
  deadline(frame){
    const s=frame.step;if(s.op==='for_windows@1')return frame.window.opensAt;if(s.op==='collect_window@1')return frame.window.closesAt;
    if(WINDOWS.includes(s.op))return control(this,frame).closesAt;
    if(['wait_until@1','collect_until@1'].includes(s.op))return this.resolve(s.until);
    return s.afterMs===null||s.afterMs===undefined?null:Math.min(MAX,this.state.openedAt+s.afterMs);
  }
  actors(frame){
    switch(frame.step.actors??'turn'){
      case 'participants':return this.participants;
      case 'turn':return [frame.turn];
      default:return this.participants.filter(a=>a!==frame.turn);
    }
  }
  source(id,frame){return this.state.records.findLast(r=>r.step===id&&(r.iteration===null||r.iteration===frame.iteration));}
  record(frame){
    let r=this.state.records.find(r=>r.key===frame.key);
    if(!r){r={key:frame.key,step:frame.step.id,op:frame.step.op,iteration:frame.iteration,turn:frame.turn,entries:[],revealed:false,closed:false};if(frame.window)r.window=clone(frame.window);this.state.records.push(r);}
    return r;
  }
  next(at){this.state.pc++;this.state.openedAt=at;}
  findStep(id){return this.definitions.get(id);}
  poolItem(f){return this.source(f.item.source,f).entries.find(e=>e.itemId===f.item.itemId);}
  rank(source,limit){
    const compare=(a,b)=>Math.sign(b.score.numerator*a.score.denominator-a.score.numerator*b.score.denominator);
    const scored=source.results.filter(x=>x.score!==null).map(clone).sort(compare);let prior=null,rank=0;
    source.ranking=[];
    scored.forEach((row,i)=>{if(prior===null||compare(row,prior)!==0)rank=i+1;row.rank=rank;if(rank<=limit)source.ranking.push(row);prior=row;});
    source.unrated=source.results.filter(x=>x.score===null).map(clone);source.revealed=true;
  }
  randomIndex(count){
    const limit=4294967295-4294967295%count;
    for(;;){let x=this.state.randomState;x=(x^(x<<13))>>>0;x=(x^(x>>>17))>>>0;x=(x^(x<<5))>>>0;this.state.randomState=x;const value=x-1;if(value<limit)return value%count;}
  }
  distribute(s,pool){
    const recipients=this.participants.filter(a=>s.recipients==='participants'||pool.entries.some(e=>e.actor===a)),assignments=[],unmatched=[];
    for(const actor of recipients){
      const candidates=pool.entries.filter(e=>e.actor!==actor);
      if(!candidates.length){unmatched.push(actor);continue;}
      let chosen;
      if(s.policy==='policy:next_nonself_source@1'){
        const position=this.participants.indexOf(actor),distance=e=>(this.participants.indexOf(e.actor)-position+this.participants.length)%this.participants.length;
        chosen=candidates.reduce((best,e)=>distance(e)<distance(best)?e:best);
      }else chosen=candidates.length===1?candidates[0]:candidates[this.randomIndex(candidates.length)];
      assignments.push({actor,itemId:chosen.itemId,text:chosen.text,sourceActor:chosen.actor});
    }
    return {recipients,assignments,unmatched};
  }
  settle(now){
    const waiting=['collect@1','append@1','pool@1','assign_item@1','acknowledge@1','collect_group@1','pause@1','wait_until@1','collect_until@1','rate@1','for_windows@1','collect_window@1','respond@1'];
    while(this.state.pc<this.plan.length){
      const f=this.plan[this.state.pc],s=f.step;
      if(CONTINUATION_OPS.includes(s.op)){if(settleContinuation(this,f,now)==='wait')break;continue;}
      if(VOTING_OPS.includes(s.op)){if(settleVoting(this,f,now)==='wait')break;continue;}
      if(ARTIFACT_OPS.includes(s.op)){if(settleArtifact(this,f,now)==='wait')break;continue;}
      if(s.op==='for_items@1'){
        const frames=this.source(s.source,f).entries.flatMap((entry,i)=>this.expand(s.steps,null,i,{source:s.source,itemId:entry.itemId}));
        this.plan.splice(this.state.pc,1,...frames);continue;
      }
      if(s.op==='assign_sources@1'){
        const r=this.record(f);if(!r.closed){Object.assign(r,this.distribute(s,this.source(s.source,f)));r.closed=true;}this.next(this.state.openedAt);continue;
      }
      if(s.op==='respond@1'){
        const r=this.record(f);r.assignments=clone(this.source(s.source,f).assignments);
        if(!r.assignments.length){r.closed=true;this.next(this.state.openedAt);continue;}
      }
      if(s.op==='route@1'){
        const r=this.record(f),pool=this.source(s.source,f);r.round=s.round;
        r.assignments=pool.entries.map(item=>({actor:this.participants[(this.participants.indexOf(item.actor)+s.offset)%this.participants.length],itemId:item.itemId,text:item.text}));
        r.closed=true;this.next(this.state.openedAt);continue;
      }
      if(s.op==='rate@1'){
        const r=this.record(f),route=this.source(s.source,f);r.round=route.round;r.assignments=clone(route.assignments);
        if(!r.assignments.length){r.closed=true;this.next(this.state.openedAt);continue;}
      }
      if(s.op==='partition@1'){
        const r=this.record(f);
        if(s.policy==='policy:roster_chunks@1'){
          r.groups=[];for(let i=0;i<this.participants.length;i+=s.minSize)r.groups.push(this.participants.slice(i,i+s.minSize));
          r.closed=true;this.next(this.state.openedAt);continue;
        }
        r.groups??=[];
      }
      if(s.op==='pool@1')this.record(f).published??=[];
      if(s.op==='assign_item@1')this.record(f).reader??=null;
      if(s.op==='acknowledge@1'){
        const r=this.record(f),source=this.source(s.source,f);r.acknowledged??=false;r.reader=source.reader;
        if(source.reader===null){r.closed=true;this.next(this.state.openedAt);continue;}
      }
      if(s.op==='collect_group@1'){
        const r=this.record(f);r.groups=clone(this.source(s.source,f).groups);
        if(!r.groups.length){r.closed=true;this.next(this.state.openedAt);continue;}
      }
      if(waiting.includes(s.op)||s.op==='partition@1'){
        const r=this.record(f),deadline=this.deadline(f);
        if(deadline!==null&&now>=deadline){r.closed=true;this.next(Math.max(deadline,this.state.openedAt));continue;}
        break;
      }
      if(s.op==='aggregate@1'){
        const r=this.record(f),ratings=s.sources.map(id=>this.source(id,f));
        const route=this.findStep(this.findStep(s.sources[0]).source),pool=this.source(route.source,f);
        const gcd=(a,b)=>{while(b){[a,b]=[b,a%b];}return a;};
        r.results=pool.entries.map(item=>{
          const scores=ratings.flatMap(rate=>rate.entries.filter(e=>e.value.itemId===item.itemId).map(e=>e.value.score));
          const count=scores.length,total=scores.reduce((a,b)=>a+b,0);let score=null;
          if(count){const numerator=s.policy==='policy:sum_scores@1'?total:total*s.targetCount,denominator=s.policy==='policy:sum_scores@1'?1:count,d=gcd(numerator,denominator);score={numerator:numerator/d,denominator:denominator/d};}
          return {itemId:item.itemId,text:item.text,count,total,score};
        });r.closed=true;
      }
      if(s.op==='publish_ranking@1')this.rank(this.source(s.source,f),s.limit);
      if(s.op==='reveal_responses@1')this.source(s.source,f).revealed=true;
      if(s.op==='reveal@1')s.sources.forEach(id=>{this.source(id,f).revealed=true;});
      if(s.op==='reveal_item@1'){
        const ack=this.source(s.source,f);
        if(ack.acknowledged){const pool=this.source(f.item.source,f);if(!pool.published.includes(f.item.itemId))pool.published.push(f.item.itemId);}
      }
      if(s.op==='tally@1'){
        const source=this.source(s.source,f),r=this.record(f);
        const options=this.findStep(source.step).fields[s.field].options;
        r.counts=options.map(value=>({value,count:source.entries.filter(e=>e.value[s.field]===value).length}));
        r.revealed=r.closed=true;
      }
      this.next(this.state.openedAt);
    }
    this.state.clock=now;
  }
  validFields(step,payload,frame,actor){
    if(!exact(payload,Object.keys(step.fields)))return false;
    return Object.entries(step.fields).every(([key,s])=>{
      const v=payload[key];
      if(s.type==='image_ref')return exact(v,['ref'])&&text(v.ref)&&[...v.ref].length<=256&&typeof this.authorizeImage==='function'&&this.authorizeImage(actor,v.ref)===true;
      if(s.type==='integer')return integer(v,s.min,s.max);
      if(s.type==='text')return text(v);
      if(s.type==='text_list')return Array.isArray(v)&&v.length===s.count&&v.every(text);
      if(s.type==='choice')return s.options.includes(v);
      const parts=s.indexOf.split('.');
      const items=parts.length===1?payload[parts[0]]:this.source(parts[0],frame).entries[0]?.value[parts[1]]??[];
      return Array.isArray(items)&&integer(v,0,items.length-1);
    });
  }
  event(e){
    if(!exact(e,['eventId','type','actor','at','step','payload'])||!scalar(e)||!text(e.eventId)||!integer(e.at)||e.at<this.state.clock||!object(e.payload)||![...bindings(this),'system'].includes(e.actor))return 'rejected';
    this.settle(e.at);
    const identity={type:e.type,actor:e.actor,step:e.step,payload:e.payload};
    if(Object.hasOwn(this.state.ledger,e.eventId))return canonical(this.state.ledger[e.eventId])===canonical(identity)?'replayed':'rejected';
    let accepted=false;
    if(e.type==='tick')accepted=e.actor==='system'&&e.step===null&&exact(e.payload,[]);
    else if(this.state.pc<this.plan.length){
      const f=this.plan[this.state.pc],s=f.step,r=this.record(f);
      if(e.step!==f.key)return 'rejected';
      if(e.actor==='system'&&e.type==='configure'&&WINDOWS.includes(s.op)&&!authorizeNewViewers(this,e.payload))return 'rejected';
      if(CONTINUATION_OPS.includes(s.op)){accepted=continuationEvent(this,f,e);}
      else if(VOTING_OPS.includes(s.op)){accepted=votingEvent(this,f,e);}
      else if(WINDOWS.includes(s.op)){accepted=artifactEvent(this,f,e);}
      else if(s.op==='respond@1'){
        const assigned=r.assignments.find(a=>a.actor===e.actor);
        if(e.type==='submit'&&assigned&&exact(e.payload,['itemId','text'])&&e.payload.itemId===assigned.itemId&&text(e.payload.text)&&!r.entries.some(x=>x.actor===e.actor)){
          r.entries.push({actor:e.actor,source:{actor:assigned.sourceActor,itemId:assigned.itemId,text:assigned.text},text:e.payload.text});accepted=true;
          if(s.close==='all'&&r.entries.length===r.assignments.length){r.closed=true;this.next(e.at);}
        }
      }else if(s.op==='rate@1'){
        const assigned=r.assignments.find(a=>a.actor===e.actor);
        if(e.type==='submit'&&assigned&&exact(e.payload,['itemId','round','score'])&&e.payload.itemId===assigned.itemId&&e.payload.round===r.round&&integer(e.payload.score,s.min,s.max)&&!r.entries.some(x=>x.actor===e.actor)){
          r.entries.push({actor:e.actor,value:clone(e.payload)});accepted=true;
          if(s.close==='all'&&r.entries.length===r.assignments.length){r.closed=true;this.next(e.at);}
        }
      }else if(s.op==='pool@1'){
        if(e.type==='submit'&&this.participants.includes(e.actor)&&exact(e.payload,['itemId','text'])){
          if(text(e.payload.itemId)&&text(e.payload.text)&&!r.entries.some(x=>x.itemId===e.payload.itemId)&&r.entries.filter(x=>x.actor===e.actor).length<s.perActor){
            r.entries.push({actor:e.actor,itemId:e.payload.itemId,text:e.payload.text});accepted=true;
            if(s.close==='all'&&r.entries.length===this.participants.length*s.perActor){r.closed=true;this.next(e.at);}
          }
        }else if(e.type==='advance'&&e.actor===this.organizer&&s.close==='organizer'&&exact(e.payload,[])){r.closed=true;this.next(e.at);accepted=true;}
      }else if(s.op==='assign_item@1'){
        if(e.type==='claim'&&exact(e.payload,[])&&this.participants.includes(e.actor)&&e.actor!==this.poolItem(f).actor){r.reader=e.actor;r.closed=true;this.next(e.at);accepted=true;}
      }else if(s.op==='acknowledge@1'){
        if(e.type==='advance'&&exact(e.payload,[])&&e.actor===r.reader){r.acknowledged=true;r.closed=true;this.next(e.at);accepted=true;}
      }else if(s.op==='partition@1'){
        if(e.type==='partition'&&e.actor===this.organizer&&exact(e.payload,['groups'])){
          const groups=e.payload.groups;
          if(Array.isArray(groups)&&groups.length&&groups.every(g=>Array.isArray(g)&&g.length>=s.minSize&&g.length<=s.maxSize&&g.every(a=>typeof a==='string'))){
            const flat=groups.flat();
            if(flat.length===this.participants.length&&new Set(flat).size===flat.length&&flat.every(a=>this.participants.includes(a))){r.groups=clone(groups);r.closed=true;this.next(e.at);accepted=true;}
          }
        }
      }else if(s.op==='collect_group@1'){
        if(e.type==='submit'&&this.participants.includes(e.actor)&&exact(e.payload,['text'])&&text(e.payload.text)&&!r.entries.some(x=>x.actor===e.actor)){
          r.entries.push({actor:e.actor,value:clone(e.payload)});accepted=true;
          if(s.close==='all'&&r.entries.length===this.participants.length){r.closed=true;this.next(e.at);}
        }else if(e.type==='advance'&&e.actor===this.organizer&&s.close==='organizer'&&exact(e.payload,[])){r.closed=true;this.next(e.at);accepted=true;}
      }else if(['collect@1','collect_until@1','collect_window@1','append@1'].includes(s.op)&&e.type==='submit'&&this.actors(f).includes(e.actor)&&!r.entries.some(x=>x.actor===e.actor)){
        const valid=['collect@1','collect_until@1','collect_window@1'].includes(s.op)?this.validFields(s,e.payload,f,e.actor):exact(e.payload,['text'])&&text(e.payload.text);
        if(valid){
          r.entries.push({actor:e.actor,value:clone(e.payload)});accepted=true;
          if(s.op==='append@1'||s.close==='all'&&r.entries.length===this.actors(f).length){r.closed=true;this.next(e.at);}
        }
      }else if(e.type==='advance'&&s.op==='collect@1'&&exact(e.payload,[])){
        const authority=s.close==='organizer'?this.organizer:s.close==='turn'?f.turn:null;
        if(authority!==null&&e.actor===authority){r.closed=true;this.next(e.at);accepted=true;}
      }
    }
    if(accepted){Object.defineProperty(this.state.ledger,e.eventId,{value:clone(identity),enumerable:true,writable:true,configurable:true});this.settle(e.at);}
    return accepted?'accepted':'rejected';
  }
  view(actor,now=null){
    if(!bindings(this).includes(actor))throw new Error('unauthorized');
    if(now!==null){demand(integer(now)&&now>=this.state.clock);this.settle(now);}
    const active=this.plan[this.state.pc]??null;
    const result={phase:active?'active':'complete',step:active?.key??null,turn:active?.turn??null,prompt:active?this.resolve(active.step.prompt):null,openedAt:active?this.state.openedAt:null,deadline:active?this.deadline(active):null,records:[],story:[]};
    if(active?.window)result.window=clone(active.window);
    if(active?.step.op==='assign_item@1')result.canClaim=this.participants.includes(actor)&&actor!==this.poolItem(active).actor;
    if(active?.step.op==='acknowledge@1')result.turn=this.source(active.step.source,active).reader;
    for(const r of this.state.records){
      const item=Object.fromEntries(['key','step','op','turn','closed','revealed'].map(k=>[k,clone(r[k])]));
      if(r.window)item.window=clone(r.window);
      if(CONTINUATION_OPS.includes(r.op)){projectContinuation(this,r,item,actor);}
      else if(VOTING_OPS.includes(r.op)){projectVoting(this,r,item,actor);}
      else if(ARTIFACT_OPS.includes(r.op)){projectArtifact(this,r,item,actor);}
      else if(r.op==='assign_sources@1'){
        item.eligible=r.recipients.includes(actor);item.unmatched=r.unmatched.includes(actor);
        const assignment=r.assignments.find(a=>a.actor===actor);item.assignment=assignment?{itemId:assignment.itemId,text:assignment.text}:null;
      }else if(r.op==='respond@1'){
        item.count=r.entries.length;const assignment=r.assignments.find(a=>a.actor===actor);item.assignment=assignment?{itemId:assignment.itemId,text:assignment.text}:null;
        item.entries=r.entries.filter(e=>r.revealed||e.actor===actor).map(e=>r.revealed?clone(e):{actor,source:{itemId:e.source.itemId,text:e.source.text},text:e.text});
      }else if(r.op==='route@1'){
        item.round=r.round;item.assignments=r.assignments.filter(a=>a.actor===actor).map(a=>({itemId:a.itemId,text:a.text}));
      }else if(r.op==='rate@1'){
        item.round=r.round;item.count=r.entries.length;item.entries=r.entries.filter(e=>e.actor===actor).map(clone);
        item.assignments=r.assignments.filter(a=>a.actor===actor).map(a=>({itemId:a.itemId,text:a.text}));
      }else if(r.op==='aggregate@1'){
        if(r.revealed){item.ranking=clone(r.ranking);item.unrated=clone(r.unrated);}
      }else if(r.op==='pool@1'){
        item.count=r.entries.length;item.entries=r.entries.filter(e=>e.actor===actor||r.published.includes(e.itemId)).map(e=>({itemId:e.itemId,text:e.text}));
      }else if(r.op==='assign_item@1'){
        item.reader=r.reader;
        if(actor===r.reader){const entry=this.poolItem(this.plan.find(f=>f.key===r.key));item.item={itemId:entry.itemId,text:entry.text};}
      }else if(r.op==='acknowledge@1'){
        item.reader=r.reader;item.acknowledged=r.acknowledged;
      }else if(r.op==='partition@1'){
        item.groups=clone(actor===this.organizer?r.groups:r.groups.filter(g=>g.includes(actor)));
      }else if(r.op==='collect_group@1'){
        item.members=[...(r.groups.find(g=>g.includes(actor))??[])];
        item.entries=clone(r.entries.filter(e=>item.members.includes(e.actor)));item.count=item.entries.length;
      }else if(['pause@1','wait_until@1','for_windows@1'].includes(r.op)){
        // The common step status and timing are its entire projection.
      }else if(['collect@1','collect_until@1','collect_window@1'].includes(r.op)){
        const definition=this.findStep(r.step),fields=definition.fields;
        if(r.op==='collect_window@1'&&definition.completion==='group')item.statuses=this.participants.map(a=>({actor:a,status:r.entries.some(e=>e.actor===a)?'complete':r.closed?'missed':'pending'}));
        item.count=r.entries.length;item.entries=[];
        for(const e of r.entries){
          const value=Object.fromEntries(Object.entries(e.value).filter(([k])=>r.revealed||e.actor===actor||fields[k].visibility==='group').map(([k,v])=>[k,clone(v)]));
          if(Object.keys(value).length)item.entries.push({actor:e.actor,value});
        }
      }else if(r.op==='append@1'){
        item.entries=clone(r.entries);result.story.push(...clone(r.entries));
      }else item.counts=clone(r.counts);
      result.records.push(item);
    }
    return result;
  }
}
export function run(request){
  if(request.action==='validate'){
    try{validate(request.package);return {outcome:'valid'};}catch{return {outcome:'invalid_package'};}
  }
  validate(request.package);
  const missing=request.package.requires.filter(x=>![...OPS,...CAPS].includes(x)).sort();
  if(missing.length)return {outcome:'unsupported',missing};
  let engine;
  try{
    if(Object.hasOwn(request,'settings'))demand(object(request.settings));
    if(Object.hasOwn(request,'tieChoices'))demand(Array.isArray(request.tieChoices)&&request.tieChoices.every(x=>integer(x)));
    engine=new Engine(request.package,request.participants,request.organizer,request.startedAt??0,request.state??null,request.settings??null,request.seed??null,(actor,ref)=>(request.trustedMedia??[]).some(m=>exact(m,['actor','ref','kind','ready'])&&m.actor===actor&&m.ref===ref&&m.kind==='image'&&m.ready===true),request.hostInputs??null,(actor,ref,kind)=>(request.trustedMedia??[]).some(m=>exact(m,['actor','ref','kind','ready'])&&m.actor===actor&&m.ref===ref&&m.kind===kind&&m.ready===true),Object.hasOwn(request,'tieChoices')?((count,draw)=>request.tieChoices[draw]):null,request.instanceId??null,request.inputBindings??null,(binding,viewers)=>(request.trustedInputs??[]).some(x=>exact(x,['binding','viewers','ready'])&&x.ready===true&&Array.isArray(x.viewers)&&x.viewers.every(text)&&viewers.every(a=>x.viewers.includes(a))&&canonical(x.binding)===canonical(binding)));
  }catch{return {outcome:'invalid_setup'};}
  const outcomes=[],views=[];
  for(const event of request.events??[]){outcomes.push(engine.event(event));views.push(Object.fromEntries(bindings(engine).map(a=>[a,engine.view(a)])));}
  return {outcomes,views,state:engine.state};
}
if(process.argv[1]&&new URL(import.meta.url).pathname===process.argv[1]){
  try{console.log(JSON.stringify(run(JSON.parse(fs.readFileSync(0,'utf8')))));}catch{console.log(JSON.stringify({outcome:'invalid_package'}));}
}
