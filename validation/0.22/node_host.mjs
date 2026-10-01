// Independent Node/SQLite app host for candidate 0.22.
import {inflateSync} from 'node:zlib';
import {createServer} from 'node:http';
import {createHash,randomBytes,randomUUID,timingSafeEqual} from 'node:crypto';
import {DatabaseSync} from 'node:sqlite';
import {bindings} from '../../format/0.22/artifacts.mjs';
import {validBinding,validContribution} from '../../format/0.22/continuation.mjs';
import {Engine,validate,canonical,FORMAT,OPS,CAPS} from '../../format/0.22/runtime.mjs';
const argv=process.argv.slice(2),option=name=>argv[argv.indexOf(name)+1];
const disabled=argv.flatMap((v,i)=>v==='--disable'?[argv[i+1]]:[]),supported=new Set([...OPS,...CAPS].filter(x=>!disabled.includes(x)));
const db=new DatabaseSync(option('--db')),adminToken=option('--admin-token');
db.exec(`PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS meta(id INTEGER PRIMARY KEY,clock INTEGER NOT NULL);
INSERT OR IGNORE INTO meta VALUES(1,0);
CREATE TABLE IF NOT EXISTS packages(id TEXT,version TEXT,body TEXT NOT NULL,digest TEXT NOT NULL,PRIMARY KEY(id,version));
CREATE TABLE IF NOT EXISTS instances(id TEXT PRIMARY KEY,package_id TEXT,package_version TEXT,participants TEXT,organizer TEXT,started_at INTEGER,state TEXT,identity TEXT);
CREATE TABLE IF NOT EXISTS tokens(instance TEXT,hash TEXT,actor TEXT,PRIMARY KEY(instance,hash));
CREATE TABLE IF NOT EXISTS media(instance TEXT,actor TEXT,ref TEXT,kind TEXT,ready INTEGER,media_type TEXT,bytes BLOB,PRIMARY KEY(instance,actor,ref));
CREATE TABLE IF NOT EXISTS input_grants(destination TEXT,actor TEXT,origin TEXT,owner TEXT,ref TEXT,kind TEXT,PRIMARY KEY(destination,actor,origin,owner,ref,kind));`);
if(!db.prepare('PRAGMA table_info(instances)').all().some(x=>x.name==='identity'))db.exec('ALTER TABLE instances ADD COLUMN identity TEXT');
for(const {id} of db.prepare('SELECT id FROM instances WHERE identity IS NULL').all())db.prepare('UPDATE instances SET identity=? WHERE id=?').run('urn:uuid:'+randomUUID(),id);
db.exec('CREATE UNIQUE INDEX IF NOT EXISTS instance_identity ON instances(identity)');
const sha=x=>createHash('sha256').update(x).digest('hex');
const assignmentSeed=()=>{if(argv.includes('--assignment-seed'))return Number(option('--assignment-seed'));let seed=0;while(seed===0)seed=randomBytes(4).readUInt32BE(0);return seed;};
const chooseTie=argv.includes('--tie-choice')?count=>Number(option('--tie-choice')):null;
const now=()=>db.prepare('SELECT clock FROM meta').get().clock;
const exact=(x,keys)=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
function transaction(fn){db.exec('BEGIN IMMEDIATE');try{const result=fn();db.exec('COMMIT');return result;}catch(e){db.exec('ROLLBACK');throw e;}}
function engine(id){
  const row=db.prepare('SELECT * FROM instances WHERE id=?').get(id);
  if(!row)throw new Error('not_found');
  const packageRow=db.prepare('SELECT body FROM packages WHERE id=? AND version=?').get(row.package_id,row.package_version);
  return new Engine(JSON.parse(packageRow.body),JSON.parse(row.participants),row.organizer,row.started_at,JSON.parse(row.state),null,null,(actor,ref)=>authorized(id,actor,ref),null,(actor,ref,kind)=>authorized(id,actor,ref,kind),chooseTie,row.identity,null,authorizeBinding);
}
const persist=(id,e)=>db.prepare('UPDATE instances SET state=? WHERE id=?').run(canonical(e.state),id);
setInterval(()=>transaction(()=>{for(const {id} of db.prepare('SELECT id FROM instances').all()){const e=engine(id);e.settle(now());persist(id,e);}}),20).unref();
const MAX_IMAGE_BYTES = 524288;
function crc32(buffer) {
  let crc = 0xFFFFFFFF;
  for (const byte of buffer) {
    crc ^= byte;
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xEDB88320 : 0);
  }
  return (crc ^ 0xFFFFFFFF) >>> 0;
}
function validPng(data) {
  if (!Buffer.isBuffer(data) || data.length < 8 || data.length > MAX_IMAGE_BYTES
      || !data.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) return false;
  let pos = 8, width = null, height = null, channels = null, sawIend = false, idatFinished = false;
  const idat = [];
  while (pos + 12 <= data.length) {
    const length = data.readUInt32BE(pos), end = pos + 12 + length;
    if (length > MAX_IMAGE_BYTES || end > data.length) return false;
    const kind = data.subarray(pos + 4, pos + 8);
    // Validate raw bytes before ascii decoding, which clears high bits.
    if (![...kind].every(c => c >= 65 && c <= 90 || c >= 97 && c <= 122)
        || kind[2] < 65 || kind[2] > 90) return false;
    const body = data.subarray(pos + 8, pos + 8 + length);
    if (crc32(Buffer.concat([kind, body])) !== data.readUInt32BE(pos + 8 + length)) return false;
    const name = kind.toString('ascii');
    if (width === null) {
      if (name !== 'IHDR' || length !== 13) return false;
      width = body.readUInt32BE(0); height = body.readUInt32BE(4);
      if (width < 1 || width > 1024 || height < 1 || height > 1024 || body[8] !== 8
          || ![2, 6].includes(body[9]) || body[10] !== 0 || body[11] !== 0 || body[12] !== 0) return false;
      channels = body[9] === 2 ? 3 : 4;
    } else if (name === 'IDAT') {
      if (idatFinished) return false;
      idat.push(body);
    }
    else if (name === 'IEND') {
      if (length !== 0 || idat.length === 0 || end !== data.length) return false;
      sawIend = true; break;
    } else if (name === 'IHDR' || kind[0] < 97 || kind[0] > 122 || kind[2] < 65 || kind[2] > 90
      || ![...kind].every(c => c >= 65 && c <= 90 || c >= 97 && c <= 122)) return false;
    if (idat.length && name !== 'IDAT') idatFinished = true;
    pos = end;
  }
  if (!sawIend) return false;
  const stride = 1 + width * channels, expected = stride * height;
  try {
    const compressed = Buffer.concat(idat);
    const decoded = inflateSync(compressed, { maxOutputLength: expected + 1, info: true });
    const pixels = decoded.buffer;
    return decoded.engine.bytesWritten === compressed.length && pixels.length === expected
      && Array.from({ length: height }, (_, row) => pixels[row * stride]).every(x => x <= 4);
  } catch { return false; }
}
function authorized(id,actor,ref,kind='image'){return !!db.prepare("SELECT 1 FROM media WHERE instance=? AND actor=? AND ref=? AND kind=? AND ready=1").get(id,actor,ref,kind);}
function visibleRef(value,ref){if(Array.isArray(value))return value.some(v=>visibleRef(v,ref));if(value&&typeof value==='object')return (exact(value,['ref'])||exact(value,['kind','ref']))&&value.ref===ref||Object.values(value).some(v=>visibleRef(v,ref));return false;}
const typedPools=['artifact_pool@1','artifact_pool@2','artifact_pool@3'];
const localIdentity=id=>db.prepare('SELECT identity FROM instances WHERE id=?').get(id)?.identity;
const localInstance=identity=>db.prepare('SELECT id FROM instances WHERE identity=?').get(identity)?.id;
function containsSnapshot(value,snapshot){
  if(value===null||typeof value!=='object')return false;
  if(!Array.isArray(value)&&canonical(value)===canonical(snapshot))return true;
  return Object.values(value).some(child=>containsSnapshot(child,snapshot));
}
function qualify(id,candidate){
  if(validContribution(candidate))return structuredClone(candidate);
  if(!exact(candidate,['ref','actor','value','round'])||!exact(candidate.ref,['source','itemId']))throw new Error('invalid_setup');
  const result={...structuredClone(candidate),ref:{instance:localIdentity(id),...candidate.ref}};
  if(!validContribution(result))throw new Error('invalid_setup');return result;
}
function actualOrigin(candidate){
  if(!validContribution(candidate))throw new Error('invalid_setup');
  const id=localInstance(candidate.ref.instance);if(id===undefined)throw new Error('invalid_setup');
  const source=engine(id);source.settle(now());persist(id,source);
  const definition=source.findStep(candidate.ref.source),record=source.state.records.find(r=>r.step===candidate.ref.source);
  if(!typedPools.includes(definition?.op)||!record?.closed||!record.effective.actors.includes(candidate.actor))throw new Error('invalid_setup');
  const entry=record.entries.find(x=>x.itemId===candidate.ref.itemId);
  if(!entry)throw new Error('invalid_setup');
  const expected={ref:{instance:localIdentity(id),source:record.step,itemId:entry.itemId},actor:entry.actor,value:entry.value,round:definition.round??null};
  if(canonical(expected)!==canonical(candidate))throw new Error('invalid_setup');
  if(candidate.value.kind!=='text'&&!authorized(id,candidate.actor,candidate.value.ref,candidate.value.kind))throw new Error('invalid_setup');
  return id;
}
function visibleCandidate(source,actor,candidate){
  const view=source.view(actor);
  if(containsSnapshot(view,candidate))return true;
  const legacy={...candidate,ref:{source:candidate.ref.source,itemId:candidate.ref.itemId}};
  if(containsSnapshot(view,legacy))return true;
  const pool=view.records.find(r=>r.step===candidate.ref.source&&typedPools.includes(r.op));
  return pool?.entries?.some(entry=>canonical(entry)===canonical({actor:candidate.actor,itemId:candidate.ref.itemId,value:candidate.value}))??false;
}
function selectedSourceRound(source,selection){
  const tally=source.findStep(selection.source),vote=source.findStep(tally?.source),pool=source.findStep(vote?.candidates?.source);
  if(!typedPools.includes(pool?.op))throw new Error('invalid_setup');return pool.round??null;
}
function resolvePointer(pointer,viewers){
  const direct=exact(pointer,['instance','source','itemId']),selected=exact(pointer,['instance','result']);
  if((!direct&&!selected)||typeof pointer.instance!=='string'||!pointer.instance.length)throw new Error('invalid_setup');
  const id=pointer.instance,source=engine(id);source.settle(now());persist(id,source);
  let candidate,via;
  if(direct){
    if(typeof pointer.source!=='string'||typeof pointer.itemId!=='string')throw new Error('invalid_setup');
    const definition=source.findStep(pointer.source),record=source.state.records.find(r=>r.step===pointer.source),entry=record?.entries.find(x=>x.itemId===pointer.itemId);
    if(!typedPools.includes(definition?.op)||!record?.closed||!entry||!record.effective.actors.includes(entry.actor))throw new Error('invalid_setup');
    candidate={ref:{instance:localIdentity(id),source:pointer.source,itemId:entry.itemId},actor:entry.actor,value:structuredClone(entry.value),round:definition.round??null};
    via={instance:localIdentity(id),source:pointer.source,itemId:entry.itemId,round:definition.round??null};
    if(viewers!==null&&!viewers.every(actor=>visibleCandidate(source,actor,candidate)))throw new Error('invalid_setup');
  }else{
    if(typeof pointer.result!=='string')throw new Error('invalid_setup');
    const definition=source.findStep(pointer.result),record=source.state.records.find(r=>r.step===pointer.result);
    if(!['select@1','select@2'].includes(definition?.op)||!record?.closed||record.output.status!=='selected')throw new Error('invalid_setup');
    candidate=qualify(id,record.output.selected);via={instance:localIdentity(id),result:pointer.result,round:selectedSourceRound(source,definition)};
    const presentations=source.state.records.filter(r=>['present@1','present@2'].includes(r.op)&&source.findStep(r.step).source===pointer.result&&r.closed);
    if(!presentations.length)throw new Error('invalid_setup');
    if(viewers!==null&&!viewers.every(actor=>{
      const projected=source.view(actor);
      return presentations.some(p=>{
        const visible=projected.records.find(r=>r.key===p.key);
        return visible?.output?.status==='selected'&&canonical(qualify(id,visible.output.selected))===canonical(candidate);
      });
    }))throw new Error('invalid_setup');
  }
  const normalized={candidate,via};if(!validBinding(normalized))throw new Error('invalid_setup');actualOrigin(candidate);return normalized;
}
function authorizeBinding(binding,viewers){
  try{
    if(!validBinding(binding)||!Array.isArray(viewers))return false;
    const id=localInstance(binding.via.instance);if(id===undefined)return false;
    const pointer=Object.hasOwn(binding.via,'result')?{instance:id,result:binding.via.result}:{instance:id,source:binding.via.source,itemId:binding.via.itemId};
    return canonical(resolvePointer(pointer,viewers))===canonical(binding);
  }catch{return false;}
}
function saveInputGrants(id,e){
  for(const binding of Object.values(e.state.inputBindings??{})){
    const candidate=binding.candidate,value=candidate.value;if(value.kind==='text')continue;
    const origin=localInstance(candidate.ref.instance);if(origin===undefined)throw new Error('invalid_setup');
    for(const actor of bindings(e))db.prepare('INSERT OR IGNORE INTO input_grants VALUES(?,?,?,?,?,?)').run(id,actor,origin,candidate.actor,value.ref,value.kind);
  }
}
function grantedMedia(id,actor,ref,e,view){
  for(const binding of Object.values(e.state.inputBindings??{})){
    const candidate=binding.candidate,value=candidate.value;
    if(value.kind==='text'||value.ref!==ref||!containsSnapshot(view,candidate))continue;
    const origin=localInstance(candidate.ref.instance);if(origin===undefined)continue;
    const granted=db.prepare('SELECT 1 FROM input_grants WHERE destination=? AND actor=? AND origin=? AND owner=? AND ref=? AND kind=?').get(id,actor,origin,candidate.actor,ref,value.kind);
    if(granted){const row=db.prepare('SELECT media_type,bytes FROM media WHERE instance=? AND actor=? AND ref=? AND kind=? AND ready=1').get(origin,candidate.actor,ref,value.kind);if(row)return row;}
  }
  return null;
}

function mediaSupport(){return Object.fromEntries([['image_contributions@1','image','image/png'],['audio_contributions@1','audio','audio/wav']].filter(([cap])=>supported.has(cap)).map(([cap,kind,mime])=>[cap,{kind,uploadMediaTypes:[mime]}]));}
function validWav(data){
 if(!Buffer.isBuffer(data)||data.length<=44||data.length>524288)return false;
 if(!data.subarray(0,4).equals(Buffer.from('RIFF'))||data.readUInt32LE(4)!==data.length-8||!data.subarray(8,12).equals(Buffer.from('WAVE'))||!data.subarray(12,16).equals(Buffer.from('fmt '))||data.readUInt32LE(16)!==16||data.readUInt16LE(20)!==1||!data.subarray(36,40).equals(Buffer.from('data')))return false;
 const channels=data.readUInt16LE(22),rate=data.readUInt32LE(24),align=data.readUInt16LE(32),body=data.readUInt32LE(40);
 return [1,2].includes(channels)&&rate>=8000&&rate<=48000&&data.readUInt16LE(34)===16&&align===channels*2&&data.readUInt32LE(28)===rate*align&&body===data.length-44&&body%align===0;
}
function route(method,path,data,token){
  const a=Buffer.from(token),b=Buffer.from(adminToken),admin=a.length===b.length&&timingSafeEqual(a,b);
  const requireAdmin=()=>{if(!admin)throw new Error('unauthorized');};
  if(path==='/support'&&method==='GET')return {format:FORMAT,operations:OPS.filter(x=>supported.has(x)).sort(),capabilities:CAPS.filter(x=>supported.has(x)).sort(),media:mediaSupport()};
  if(path==='/clock'&&method==='POST'){
    requireAdmin();if(!exact(data,['at'])||!Number.isSafeInteger(data.at)||data.at<now()||data.at>Number.MAX_SAFE_INTEGER)throw new Error('invalid_request');
    db.prepare('UPDATE meta SET clock=?').run(data.at);return {outcome:'accepted'};
  }
  if(path==='/packages'&&method==='POST'){
    requireAdmin();const p=data.package;
    try{validate(p);}catch{return {outcome:'invalid_package'};}
    const body=canonical(p),digest=sha(body),old=db.prepare('SELECT digest FROM packages WHERE id=? AND version=?').get(p.id,p.version);
    if(old)return {outcome:old.digest===digest?'existing':'package_conflict',digest:old.digest};
    db.prepare('INSERT INTO packages VALUES(?,?,?,?)').run(p.id,p.version,body,digest);return {outcome:'imported',digest};
  }
  const parts=path.split('/');
  if(parts.length===4&&parts[1]==='packages'&&method==='GET'){
    requireAdmin();const row=db.prepare('SELECT body,digest FROM packages WHERE id=? AND version=?').get(parts[2],parts[3]);
    if(!row)throw new Error('not_found');return {package:JSON.parse(row.body),digest:row.digest};
  }
  if(path==='/instances'&&method==='POST'){
    requireAdmin();if(!exact(data,['id','packageId','version','participants','organizer',...(Object.hasOwn(data,'settings')?['settings']:[]),...(Object.hasOwn(data,'hostInputs')?['hostInputs']:[]),...(Object.hasOwn(data,'hostBindings')?['hostBindings']:[])])||typeof data.id!=='string'||!data.id.length)throw new Error('invalid_request');
    const row=db.prepare('SELECT body,digest FROM packages WHERE id=? AND version=?').get(data.packageId,data.version);
    if(!row)return {outcome:'invalid_package'};
    const p=JSON.parse(row.body),missing=p.requires.filter(x=>!supported.has(x)).sort();
    if(missing.length)return {outcome:'unsupported',missing};
    if(db.prepare('SELECT id FROM instances WHERE id=?').get(data.id))return {outcome:'instance_conflict'};
    if(Object.hasOwn(data,'settings')&&!exact(data.settings,Object.keys(data.settings??{})))return {outcome:'invalid_setup'};
    const identity='urn:uuid:'+randomUUID();
    let e;try{
      const declared=Object.keys(p.inputs??{}),requested=data.hostBindings??{};
      if(!exact(requested,declared))throw new Error('invalid_setup');
      const normalized=Object.fromEntries(Object.entries(requested).map(([name,pointer])=>[name,resolvePointer(pointer,null)]));
      e=new Engine(p,data.participants,data.organizer,now(),null,data.settings??null,assignmentSeed(),null,data.hostInputs??null,null,chooseTie,identity,normalized,authorizeBinding);
    }catch{return {outcome:'invalid_setup'};}
    db.prepare('INSERT INTO instances(id,package_id,package_version,participants,organizer,started_at,state,identity) VALUES(?,?,?,?,?,?,?,?)').run(data.id,p.id,p.version,canonical(data.participants),data.organizer,now(),canonical(e.state),identity);
    saveInputGrants(data.id,e);
    const tokens=Object.fromEntries(bindings(e).map(actor=>[actor,randomBytes(24).toString('hex')]));
    for(const [actor,value] of Object.entries(tokens))db.prepare('INSERT INTO tokens VALUES(?,?,?)').run(data.id,sha(value),actor);
    return {outcome:'created',tokens,digest:row.digest,instanceIdentity:identity};
  }
  if(parts.length===4&&parts[1]==='instances'&&['control','bindings'].includes(parts[3])){
    requireAdmin();const id=parts[2],e=engine(id);
    if(parts[3]==='bindings'){
      if(method!=='POST'||!exact(data,['actor','token'])||!bindings(e).includes(data.actor)||typeof data.token!=='string'||!data.token.length)throw new Error('invalid_request');
      const old=db.prepare('SELECT actor FROM tokens WHERE instance=? AND hash=?').get(id,sha(data.token));if(old&&old.actor!==data.actor)throw new Error('invalid_request');
      db.prepare('INSERT OR IGNORE INTO tokens VALUES(?,?,?)').run(id,sha(data.token),data.actor);return {outcome:'bound'};
    }
    if(method!=='POST'||!exact(data,['eventId','type','step','payload'])||!['configure','close'].includes(data.type))return {outcome:'rejected'};
    const result={outcome:e.event({...data,actor:'system',at:now()})};persist(id,e);if(result.outcome==='accepted'&&data.type==='configure')saveInputGrants(id,e);return result;
  }
  if([4,5].includes(parts.length)&&parts[1]==='instances'&&parts[3]==='media'){
    const id=parts[2],identity=db.prepare('SELECT actor FROM tokens WHERE instance=? AND hash=?').get(id,sha(token));
    if(!identity)throw new Error('unauthorized');const actor=identity.actor,e=engine(id);
    if(!e.package.requires.some(c=>['image_contributions@1','audio_contributions@1'].includes(c)))throw new Error('unauthorized');
    if(parts.length===4&&method==='POST'){
      if(!(e.package.requires.includes('host_controls@1')?bindings(e):e.participants).includes(actor))throw new Error('unauthorized');
      if(!exact(data,['mediaType','data'])||!['image/png','audio/wav'].includes(data.mediaType)||typeof data.data!=='string'||data.data.length>700000)return {outcome:'invalid_media'};
      const blob=Buffer.from(data.data,'base64'),kind=data.mediaType==='image/png'?'image':'audio';if(!e.package.requires.includes(kind+'_contributions@1')||blob.toString('base64')!==data.data||!(kind==='image'?validPng(blob):validWav(blob)))return {outcome:'invalid_media'};
      const ref='sha256:'+sha(blob);db.prepare('INSERT OR IGNORE INTO media VALUES(?,?,?,?,?,?,?)').run(id,actor,ref,kind,1,data.mediaType,blob);
      return {outcome:'ready',ref};
    }
    if(parts.length===5&&method==='GET'){
      const ref=parts[4];e.settle(now());persist(id,e);
      const projected=e.view(actor),readable=authorized(id,actor,ref)||authorized(id,actor,ref,'audio')||visibleRef(projected,ref);let row=null;
      if(readable)row=db.prepare("SELECT media_type,bytes FROM media WHERE instance=? AND ref=? AND kind IN ('image','audio') AND ready=1 LIMIT 1").get(id,ref);
      if(!row)row=grantedMedia(id,actor,ref,e,projected);
      if(!row)throw new Error(readable?'not_found':'unauthorized');return {ref,mediaType:row.media_type,data:Buffer.from(row.bytes).toString('base64')};
    }throw new Error('not_found');
  }
  if(parts.length===4&&parts[1]==='instances'){
    const [, ,id,action]=parts;
    if(action==='status'&&method==='GET'){
      requireAdmin();const e=engine(id);return {pc:e.state.pc,clock:e.state.clock,phase:e.state.pc===e.plan.length?'complete':'active'};
    }
    const identity=db.prepare('SELECT actor FROM tokens WHERE instance=? AND hash=?').get(id,sha(token));
    if(!identity)throw new Error('unauthorized');const e=engine(id);let result;
    if(action==='view'&&method==='GET')result={view:e.view(identity.actor,now())};
    else if(action==='events'&&method==='POST'){
      if(!exact(data,['eventId','type','step','payload'])||['tick','configure','close'].includes(data.type))return {outcome:'rejected'};
      result={outcome:e.event({...data,actor:identity.actor,at:now()})};
    }else throw new Error('not_found');
    persist(id,e);return result;
  }
  throw new Error('not_found');
}
const server=createServer(async(req,res)=>{
  let status=200,result;
  try{
    const chunks=[];let length=0;
    for await(const chunk of req){length+=chunk.length;if(length>1100000)throw new Error('invalid_request');chunks.push(chunk);}
    const data=length?JSON.parse(Buffer.concat(chunks).toString('utf8')):{};
    if(!exact(data,Object.keys(data)))throw new Error('invalid_request');
    result=transaction(()=>route(req.method,req.url,data,(req.headers.authorization??'').replace(/^Bearer /,'')));
  }catch(e){const code=['unauthorized','not_found'].includes(e.message)?e.message:'invalid_request';status=code==='unauthorized'?403:code==='not_found'?404:400;result={outcome:code};}
  res.writeHead(status,{'content-type':'application/json'});res.end(JSON.stringify(result));
});
server.listen(Number(option('--port')??0),'127.0.0.1',()=>console.log(JSON.stringify({port:server.address().port})));
