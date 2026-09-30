// Independent Node/SQLite app host for candidate 0.15.
import {createServer} from 'node:http';
import {createHash,randomBytes,timingSafeEqual} from 'node:crypto';
import {DatabaseSync} from 'node:sqlite';
import {Engine,validate,canonical,FORMAT,OPS,CAPS} from '../../format/0.15/runtime.mjs';
const argv=process.argv.slice(2),option=name=>argv[argv.indexOf(name)+1];
const disabled=argv.flatMap((v,i)=>v==='--disable'?[argv[i+1]]:[]),supported=new Set([...OPS,...CAPS].filter(x=>!disabled.includes(x)));
const db=new DatabaseSync(option('--db')),adminToken=option('--admin-token');
db.exec(`PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS meta(id INTEGER PRIMARY KEY,clock INTEGER NOT NULL);
INSERT OR IGNORE INTO meta VALUES(1,0);
CREATE TABLE IF NOT EXISTS packages(id TEXT,version TEXT,body TEXT NOT NULL,digest TEXT NOT NULL,PRIMARY KEY(id,version));
CREATE TABLE IF NOT EXISTS instances(id TEXT PRIMARY KEY,package_id TEXT,package_version TEXT,participants TEXT,organizer TEXT,started_at INTEGER,state TEXT);
CREATE TABLE IF NOT EXISTS tokens(instance TEXT,hash TEXT,actor TEXT,PRIMARY KEY(instance,hash));`);
const sha=x=>createHash('sha256').update(x).digest('hex');
const now=()=>db.prepare('SELECT clock FROM meta').get().clock;
const exact=(x,keys)=>x!==null&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
function transaction(fn){db.exec('BEGIN IMMEDIATE');try{const result=fn();db.exec('COMMIT');return result;}catch(e){db.exec('ROLLBACK');throw e;}}
function engine(id){
  const row=db.prepare('SELECT * FROM instances WHERE id=?').get(id);
  if(!row)throw new Error('not_found');
  const packageRow=db.prepare('SELECT body FROM packages WHERE id=? AND version=?').get(row.package_id,row.package_version);
  return new Engine(JSON.parse(packageRow.body),JSON.parse(row.participants),row.organizer,row.started_at,JSON.parse(row.state));
}
const persist=(id,e)=>db.prepare('UPDATE instances SET state=? WHERE id=?').run(canonical(e.state),id);
setInterval(()=>transaction(()=>{for(const {id} of db.prepare('SELECT id FROM instances').all()){const e=engine(id);e.settle(now());persist(id,e);}}),20).unref();
function route(method,path,data,token){
  const a=Buffer.from(token),b=Buffer.from(adminToken),admin=a.length===b.length&&timingSafeEqual(a,b);
  const requireAdmin=()=>{if(!admin)throw new Error('unauthorized');};
  if(path==='/support'&&method==='GET')return {format:FORMAT,operations:OPS.filter(x=>supported.has(x)).sort(),capabilities:CAPS.filter(x=>supported.has(x)).sort()};
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
    requireAdmin();if(!exact(data,['id','packageId','version','participants','organizer',...(Object.hasOwn(data,'settings')?['settings']:[])])||typeof data.id!=='string'||!data.id.length)throw new Error('invalid_request');
    const row=db.prepare('SELECT body,digest FROM packages WHERE id=? AND version=?').get(data.packageId,data.version);
    if(!row)return {outcome:'invalid_package'};
    const p=JSON.parse(row.body),missing=p.requires.filter(x=>!supported.has(x)).sort();
    if(missing.length)return {outcome:'unsupported',missing};
    if(db.prepare('SELECT id FROM instances WHERE id=?').get(data.id))return {outcome:'instance_conflict'};
    if(Object.hasOwn(data,'settings')&&!exact(data.settings,Object.keys(data.settings??{})))return {outcome:'invalid_setup'};
    let e;try{e=new Engine(p,data.participants,data.organizer,now(),null,data.settings??null);}catch{return {outcome:'invalid_setup'};}
    db.prepare('INSERT INTO instances VALUES(?,?,?,?,?,?,?)').run(data.id,p.id,p.version,canonical(data.participants),data.organizer,now(),canonical(e.state));
    const tokens=Object.fromEntries([...data.participants,data.organizer].map(actor=>[actor,randomBytes(24).toString('hex')]));
    for(const [actor,value] of Object.entries(tokens))db.prepare('INSERT INTO tokens VALUES(?,?,?)').run(data.id,sha(value),actor);
    return {outcome:'created',tokens,digest:row.digest};
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
      if(!exact(data,['eventId','type','step','payload'])||data.type==='tick')return {outcome:'rejected'};
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
