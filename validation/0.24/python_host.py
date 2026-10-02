#!/usr/bin/env python3
"""Local Python/SQLite app host for candidate 0.24; controlled trusted test clock."""
import sys
import argparse
import base64
import zlib
import struct
import hashlib
import importlib.util
import json
import secrets
import sqlite3
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'format/0.24'))
spec=importlib.util.spec_from_file_location('runbook_runtime',Path(__file__).resolve().parents[2]/'format/0.24/runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
args=argparse.ArgumentParser();args.add_argument('--db',required=True);args.add_argument('--admin-token',required=True);args.add_argument('--port',type=int,default=0);args.add_argument('--disable',action='append',default=[])
args.add_argument('--assignment-seed',type=int);args.add_argument('--tie-choice',type=int);opts=args.parse_args();lock=threading.RLock()
db=sqlite3.connect(opts.db,check_same_thread=False,isolation_level=None)
db.executescript('''PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS meta (id INTEGER PRIMARY KEY, clock INTEGER NOT NULL);
INSERT OR IGNORE INTO meta VALUES(1,0);
CREATE TABLE IF NOT EXISTS packages(id TEXT, version TEXT, body TEXT NOT NULL, digest TEXT NOT NULL, PRIMARY KEY(id,version));
CREATE TABLE IF NOT EXISTS instances(id TEXT PRIMARY KEY, package_id TEXT, package_version TEXT, participants TEXT, organizer TEXT, started_at INTEGER, state TEXT);
CREATE TABLE IF NOT EXISTS tokens(instance TEXT, hash TEXT, actor TEXT, PRIMARY KEY(instance,hash));
CREATE TABLE IF NOT EXISTS media(instance TEXT,actor TEXT,ref TEXT,kind TEXT,ready INTEGER,media_type TEXT,bytes BLOB,PRIMARY KEY(instance,actor,ref));''')
if 'identity' not in [row[1] for row in db.execute('PRAGMA table_info(instances)')]: db.execute('ALTER TABLE instances ADD COLUMN identity TEXT')
for iid, in db.execute('SELECT id FROM instances WHERE identity IS NULL').fetchall():
    db.execute('UPDATE instances SET identity=? WHERE id=?',('urn:uuid:'+str(uuid.uuid4()),iid))
db.executescript('''CREATE UNIQUE INDEX IF NOT EXISTS instance_identity ON instances(identity);
CREATE TABLE IF NOT EXISTS input_grants(destination TEXT,actor TEXT,origin TEXT,owner TEXT,ref TEXT,kind TEXT,PRIMARY KEY(destination,actor,origin,owner,ref,kind));''')
db.executescript('''CREATE TABLE IF NOT EXISTS queue_consumptions(source_instance TEXT,source TEXT,destination TEXT,PRIMARY KEY(source_instance,source));
CREATE TABLE IF NOT EXISTS relay_creations(id TEXT PRIMARY KEY,request TEXT,identity TEXT,digest TEXT);''')
supported=(runtime.CAPS|runtime.OPS)-set(opts.disable)
def digest(x):return hashlib.sha256(x.encode()).hexdigest()
def now():return db.execute('SELECT clock FROM meta').fetchone()[0]
def engine(iid):
    row=db.execute('SELECT package_id,package_version,participants,organizer,started_at,state,identity FROM instances WHERE id=?',(iid,)).fetchone()
    if row is None:raise KeyError('not_found')
    pid,version,people,organizer,start,state,identity=row
    package=json.loads(db.execute('SELECT body FROM packages WHERE id=? AND version=?',(pid,version)).fetchone()[0])
    return runtime.Engine(package,json.loads(people),organizer,start,json.loads(state),authorize_image=lambda actor,ref: authorized(iid,actor,ref),authorize_artifact=lambda actor,ref,kind: authorized(iid,actor,ref,kind),choose_tie=(lambda count: opts.tie_choice) if opts.tie_choice is not None else None,instance_id=identity,authorize_input=authorize_binding)
def persist(iid,e):db.execute('UPDATE instances SET state=? WHERE id=?',(runtime.canonical(e.state),iid))
MAX_IMAGE_BYTES = 524288
def valid_png(data):
    if not isinstance(data, bytes) or not (8 <= len(data) <= MAX_IMAGE_BYTES) or data[:8] != b"\x89PNG\r\n\x1a\n":
        return False
    pos, width, height, channels, idat = 8, None, None, None, []
    saw_iend = False
    idat_finished = False
    while pos + 12 <= len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        end = pos + 12 + length
        if length > MAX_IMAGE_BYTES or end > len(data):
            return False
        kind = data[pos + 4:pos + 8]
        # PNG names are raw ASCII letters; reserved third byte must be uppercase.
        if not (all(65 <= c <= 90 or 97 <= c <= 122 for c in kind) and 65 <= kind[2] <= 90): return False
        body = data[pos + 8:pos + 8 + length]
        crc = int.from_bytes(data[pos + 8 + length:end], "big")
        if zlib.crc32(kind + body) & 0xffffffff != crc:
            return False
        if width is None:
            if kind != b"IHDR" or length != 13:
                return False
            width = int.from_bytes(body[:4], "big")
            height = int.from_bytes(body[4:8], "big")
            if not (1 <= width <= 1024 and 1 <= height <= 1024 and body[8] == 8
                    and body[9] in (2, 6) and body[10:] == b"\0\0\0"):
                return False
            channels = 3 if body[9] == 2 else 4
        elif kind == b"IDAT":
            if idat_finished: return False
            idat.append(body)
        elif kind == b"IEND":
            if length != 0 or not idat or end != len(data):
                return False
            saw_iend = True
            break
        elif kind == b"IHDR" or not (len(kind) == 4 and 97 <= kind[0] <= 122
                                            and 65 <= kind[2] <= 90 and all(65 <= c <= 90 or 97 <= c <= 122 for c in kind)):
            return False
        if idat and kind != b"IDAT": idat_finished = True
        pos = end
    if not saw_iend:
        return False
    expected = height * (1 + width * channels)
    try:
        decoder = zlib.decompressobj()
        pixels = decoder.decompress(b"".join(idat), expected + 1)
        # max_length bounds actual output. flush(length) only sizes its initial
        # buffer and can decode an unbounded remainder; never call it here.
        # A valid stream fitting the budget reaches EOF in this one call.
    except zlib.error:
        return False
    return (decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail and len(pixels) == expected
            and all(pixels[row * (1 + width * channels)] <= 4 for row in range(height)))


def authorized(iid,actor,ref,kind='image'):
    return db.execute("SELECT 1 FROM media WHERE instance=? AND actor=? AND ref=? AND kind=? AND ready=1",(iid,actor,ref,kind)).fetchone() is not None
def visible_ref(value,ref):
    if type(value) is dict:return (set(value) in [{'ref'},{'kind','ref'}] and value['ref']==ref) or any(visible_ref(v,ref) for v in value.values())
    return type(value) is list and any(visible_ref(v,ref) for v in value)

def local_instance(identity):
    row=db.execute('SELECT id FROM instances WHERE identity=?',(identity,)).fetchone()
    if row is None:raise ValueError('unknown_origin')
    return row[0]

def instance_identity(iid):
    row=db.execute('SELECT identity FROM instances WHERE id=?',(iid,)).fetchone()
    if row is None:raise ValueError('unknown_origin')
    return row[0]

def origin_candidate(iid,source,item_id):
    e=engine(iid);e.settle(now());persist(iid,e)
    definition=e.definitions.get(source,{})
    if definition.get('op') not in ['artifact_pool@1','artifact_pool@2','artifact_pool@3','pool@2','first_valid@1']:raise ValueError('invalid_source')
    record=next((record for record in e.state['records'] if record['step']==source),None)
    if record is None or not record['closed']:raise ValueError('unsettled_source')
    entry=next((entry for entry in record['entries'] if entry['itemId']==item_id),None)
    if entry is None or entry['actor'] not in record['effective']['actors']:raise ValueError('ineligible_source')
    return {'ref':{'instance':instance_identity(iid),'source':source,'itemId':item_id},'actor':entry['actor'],'value':entry['value'],'round':definition.get('round')}

def authoritative_origin(candidate):
    if not runtime.continuation.valid_candidate(candidate,['text','image','audio']):return False
    ref=candidate['ref'];iid=local_instance(ref['instance'])
    if origin_candidate(iid,ref['source'],ref['itemId'])!=candidate:return False
    value=candidate['value']
    return value['kind']=='text' or authorized(iid,candidate['actor'],value['ref'],value['kind'])

def candidate_visible(e,iid,actor,candidate):
    try:view=e.view(actor)
    except ValueError:return False
    identity=instance_identity(iid)
    def contains(value):
        if type(value) is list:return any(contains(item) for item in value)
        if type(value) is not dict:return False
        if runtime.obj(value,['ref','actor','value','round']):
            normalized=dict(value)
            if runtime.obj(value['ref'],['source','itemId']):normalized['ref']=dict(value['ref'],instance=identity)
            if normalized==candidate:return True
        return any(contains(item) for item in value.values())
    if contains(view):return True
    if candidate['ref']['instance']!=identity:return False
    for record in view['records']:
        if record['step']==candidate['ref']['source']:
            if any(runtime.obj(entry,['actor','itemId','value']) and entry['actor']==candidate['actor'] and entry['itemId']==candidate['ref']['itemId'] and entry['value']==candidate['value'] for entry in record.get('entries',[])):return True
    return False

def resolve_binding(pointer,viewers):
    if not (runtime.obj(pointer,['instance','source','itemId']) or runtime.obj(pointer,['instance','result'])):raise ValueError('invalid_pointer')
    if not runtime.artifacts.text(pointer['instance']):raise ValueError('invalid_pointer')
    iid=pointer['instance'];identity=instance_identity(iid);e=engine(iid);e.settle(now());persist(iid,e)
    if 'source' in pointer:
        if not runtime.name(pointer['source']) or not runtime.artifacts.text(pointer['itemId']):raise ValueError('invalid_pointer')
        candidate=origin_candidate(iid,pointer['source'],pointer['itemId'])
        via=dict(candidate['ref'],round=candidate['round'])
    else:
        if not runtime.name(pointer['result']):raise ValueError('invalid_pointer')
        definition=e.definitions.get(pointer['result'],{})
        if definition.get('op') not in ['select@1','select@2','select@3']:raise ValueError('invalid_result')
        record=next((record for record in e.state['records'] if record['step']==pointer['result']),None)
        if record is None or not record['closed'] or record['output']['status']!='selected':raise ValueError('unsettled_result')
        shown=any(record['closed'] and record['op'] in ['present@1','present@2','present@3'] and e.find_step(record['step'])['source']==pointer['result'] for record in e.state['records'])
        if not shown:raise ValueError('private_result')
        candidate=json.loads(runtime.canonical(record['output']['selected']))
        if runtime.obj(candidate.get('ref'),['source','itemId']):candidate['ref']['instance']=identity
        if not runtime.continuation.valid_candidate(candidate,['text','image','audio']):raise ValueError('invalid_result')
        pool=(runtime.continuation.selected_pool if definition['op'] in ['select@2','select@3'] else runtime.voting.contribution_source)(definition,e.definitions)
        via={'instance':identity,'result':pointer['result'],'round':pool.get('round')}
    if not authoritative_origin(candidate) or not all(candidate_visible(e,iid,actor,candidate) for actor in viewers):raise ValueError('input_authority')
    return {'candidate':candidate,'via':via}

def authorize_binding(binding,viewers):
    try:
        if not runtime.continuation.valid_binding(binding,['text','image','audio']):return False
        via=binding['via'];iid=local_instance(via['instance'])
        pointer={'instance':iid,'source':via['source'],'itemId':via['itemId']} if 'source' in via else {'instance':iid,'result':via['result']}
        return resolve_binding(pointer,viewers)==binding
    except (ValueError,TypeError,KeyError):return False

def resolve_queue(pointer,viewers):
    if not runtime.obj(pointer,['instance','source']) or not runtime.artifacts.text(pointer['instance']) or not runtime.name(pointer['source']):raise ValueError('invalid_queue')
    e=engine(pointer['instance']);e.settle(now());persist(pointer['instance'],e)
    record=next((r for r in e.state['records'] if r['step']==pointer['source']),None)
    if record is None or record['op']!='first_valid@1' or not record['closed'] or not runtime.relay.valid_queue(record.get('queue')):raise ValueError('unsettled_queue')
    if not all(actor in runtime.artifacts.bindings(e) for actor in viewers):raise ValueError('queue_authority')
    return json.loads(runtime.canonical(record['queue']))

def authorize_queue(queue,viewers):
    try:return resolve_queue({'instance':local_instance(queue['ref']['instance']),'source':queue['ref']['source']},viewers)==queue
    except (ValueError,TypeError,KeyError):return False

def save_grants(iid,e):
    for binding in e.state.get('inputBindings',{}).values():
        candidate=binding['candidate'];value=candidate['value']
        if value['kind']=='text':continue
        origin=local_instance(candidate['ref']['instance'])
        for actor in runtime.artifacts.bindings(e):
            db.execute('INSERT OR IGNORE INTO input_grants VALUES(?,?,?,?,?,?)',(iid,actor,origin,candidate['actor'],value['ref'],value['kind']))

def resolve_host_bindings(package,pointers,viewers):
    declared=package.get('inputs',{})
    supplied={} if pointers is None else pointers
    if type(supplied) is not dict or set(supplied)!=set(declared):raise ValueError('invalid_bindings')
    return {key:resolve_binding(pointer,viewers) for key,pointer in supplied.items()}
def image_package(e):return bool({'image_contributions@1','audio_contributions@1'} & set(e.package['requires']))
def media_support():return {k:{'kind':kind,'uploadMediaTypes':[mime]} for k,kind,mime in [('image_contributions@1','image','image/png'),('audio_contributions@1','audio','audio/wav')] if k in supported}
def valid_wav(data):
    if not isinstance(data,bytes) or not 44<len(data)<=524288:return False
    riff,size,wave,fmt,fmt_size,encoding,channels,rate,byte_rate,align,bits,body,body_size=struct.unpack('<4sI4s4sIHHIIHH4sI',data[:44])
    return (riff==b'RIFF' and size==len(data)-8 and wave==b'WAVE' and fmt==b'fmt ' and fmt_size==16 and encoding==1 and channels in [1,2] and 8000<=rate<=48000 and bits==16 and align==channels*2 and byte_rate==rate*align and body==b'data' and body_size==len(data)-44 and body_size%align==0)

def worker():
    while True:
        time.sleep(.02)
        with lock:
            db.execute('BEGIN IMMEDIATE')
            try:
                for iid, in db.execute('SELECT id FROM instances').fetchall():
                    e=engine(iid);e.settle(now());persist(iid,e)
                db.execute('COMMIT')
            except Exception:
                db.execute('ROLLBACK')
                raise
threading.Thread(target=worker,daemon=True).start()
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_GET(self):self.handle_request()
    def do_POST(self):self.handle_request()
    def handle_request(self):
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>1100000:raise ValueError('invalid_package')
            data=json.loads(self.rfile.read(length)) if length else {}
            if type(data) is not dict:raise ValueError('invalid_request')
            token=self.headers.get('Authorization','').removeprefix('Bearer ')
            path=self.path.split('/')
            admin=secrets.compare_digest(token,opts.admin_token)
            with lock:
                db.execute('BEGIN IMMEDIATE')
                try:result=self.route(path,data,token,admin);db.execute('COMMIT')
                except Exception:db.execute('ROLLBACK');raise
            status=200
        except PermissionError:status,result=403,{'outcome':'unauthorized'}
        except KeyError:status,result=404,{'outcome':'not_found'}
        except (ValueError,TypeError,IndexError):status,result=400,{'outcome':'invalid_request'}
        body=json.dumps(result,ensure_ascii=True).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def route(self,path,data,token,admin):
        if path==['','support'] and self.command=='GET':
            return {'format':runtime.FORMAT,'operations':sorted(runtime.OPS&supported),'capabilities':sorted(runtime.CAPS&supported),'media':media_support()}
        if path==['','clock'] and self.command=='POST':
            if not admin:raise PermissionError()
            if not runtime.obj(data,['at']) or not runtime.integer(data['at']) or data['at']<now():raise ValueError()
            db.execute('UPDATE meta SET clock=?',(data['at'],));return {'outcome':'accepted'}
        if path==['','packages'] and self.command=='POST':
            if not admin:raise PermissionError()
            p=data.get('package')
            try:runtime.validate(p)
            except (ValueError,TypeError,KeyError):return {'outcome':'invalid_package'}
            body=runtime.canonical(p);sha=digest(body)
            old=db.execute('SELECT digest FROM packages WHERE id=? AND version=?',(p['id'],p['version'])).fetchone()
            if old:return {'outcome':'existing' if old[0]==sha else 'package_conflict','digest':old[0]}
            db.execute('INSERT INTO packages VALUES(?,?,?,?)',(p['id'],p['version'],body,sha));return {'outcome':'imported','digest':sha}
        if len(path)==4 and path[1]=='packages' and self.command=='GET':
            if not admin:raise PermissionError()
            row=db.execute('SELECT body,digest FROM packages WHERE id=? AND version=?',(path[2],path[3])).fetchone()
            if not row:raise KeyError()
            return {'package':json.loads(row[0]),'digest':row[1]}
        if path==['','instances'] and self.command=='POST':
            if not admin:raise PermissionError()
            if not runtime.obj(data,['id','packageId','version','participants','organizer'] + (['settings'] if 'settings' in data else []) + (['hostInputs'] if 'hostInputs' in data else []) + (['hostBindings'] if 'hostBindings' in data else []) + (['hostQueues'] if 'hostQueues' in data else [])) or not runtime.text(data['id']):raise ValueError()
            row=db.execute('SELECT body,digest FROM packages WHERE id=? AND version=?',(data['packageId'],data['version'])).fetchone()
            if not row:return {'outcome':'invalid_package'}
            p=json.loads(row[0]);missing=sorted(set(p['requires'])-supported)
            if missing:return {'outcome':'unsupported','missing':missing}
            if db.execute('SELECT id FROM instances WHERE id=?',(data['id'],)).fetchone():
                receipt=db.execute('SELECT request,identity,digest FROM relay_creations WHERE id=?',(data['id'],)).fetchone()
                if receipt and receipt[0]==runtime.canonical(data):return {'outcome':'existing','id':data['id'],'instanceIdentity':receipt[1],'digest':receipt[2]}
                return {'outcome':'instance_conflict'}
            if 'settings' in data and type(data['settings']) is not dict:return {'outcome':'invalid_setup'}
            try:
                controls=data.get('hostInputs',{})
                runtime.require(type(data['participants']) is list and type(controls) is dict and all(runtime.artifacts.valid_control(control) for control in controls.values()))
                viewers=list(dict.fromkeys(data['participants']+[data['organizer']]+[actor for control in controls.values() for actor in control['actors']]))
                bindings=resolve_host_bindings(p,data.get('hostBindings'),viewers)
                requested_queues=data.get('hostQueues',{})
                if type(requested_queues) is not dict or set(requested_queues)!=set(p.get('queueInputs',{})):raise ValueError('invalid_queues')
                queues={key:resolve_queue(pointer,viewers) for key,pointer in requested_queues.items()}
                identity='urn:uuid:'+str(uuid.uuid4())
                e=runtime.Engine(p,data['participants'],data['organizer'],now(),settings=data.get('settings'),seed=opts.assignment_seed if opts.assignment_seed is not None else secrets.randbelow(4294967295)+1,host_inputs=data.get('hostInputs'),authorize_image=lambda actor,ref: authorized(data['id'],actor,ref),authorize_artifact=lambda actor,ref,kind: authorized(data['id'],actor,ref,kind),choose_tie=(lambda count: opts.tie_choice) if opts.tie_choice is not None else None,instance_id=identity,input_bindings=bindings,authorize_input=authorize_binding,queue_bindings=queues,authorize_queue=authorize_queue)
            except (ValueError,TypeError,KeyError):return {'outcome':'invalid_setup'}
            for queue in queues.values():
                consumed=db.execute('SELECT destination FROM queue_consumptions WHERE source_instance=? AND source=?',(queue['ref']['instance'],queue['ref']['source'])).fetchone()
                if consumed:return {'outcome':'queue_consumed','destination':consumed[0]}
            for queue in queues.values():
                db.execute('INSERT INTO queue_consumptions VALUES(?,?,?)',(queue['ref']['instance'],queue['ref']['source'],data['id']))
            db.execute('INSERT INTO instances(id,package_id,package_version,participants,organizer,started_at,state,identity) VALUES(?,?,?,?,?,?,?,?)',(data['id'],p['id'],p['version'],runtime.canonical(data['participants']),data['organizer'],now(),runtime.canonical(e.state),identity))
            save_grants(data['id'],e)
            tokens={}
            for actor in runtime.artifacts.bindings(e):
                value=secrets.token_hex(24);tokens[actor]=value
                db.execute('INSERT INTO tokens VALUES(?,?,?)',(data['id'],digest(value),actor))
            if any(step['op'] in runtime.relay.OPS for step in e.definitions.values()):db.execute('INSERT INTO relay_creations VALUES(?,?,?,?)',(data['id'],runtime.canonical(data),identity,row[1]))
            return {'outcome':'created','tokens':tokens,'digest':row[1],'instanceIdentity':identity}
        if len(path)==4 and path[1]=='instances' and path[3] in ['control','bindings']:
            if not admin:raise PermissionError()
            iid=path[2];e=engine(iid)
            if path[3]=='bindings':
                if self.command!='POST' or not runtime.obj(data,['actor','token']) or data['actor'] not in runtime.artifacts.bindings(e) or not runtime.text(data['token']):raise ValueError()
                previous=db.execute('SELECT actor FROM tokens WHERE instance=? AND hash=?',(iid,digest(data['token']))).fetchone()
                if previous and previous[0]!=data['actor']:raise ValueError()
                db.execute('INSERT OR IGNORE INTO tokens VALUES(?,?,?)',(iid,digest(data['token']),data['actor']));return {'outcome':'bound'}
            if self.command!='POST' or not runtime.obj(data,['eventId','type','step','payload']) or data['type'] not in ['configure','close','roster']:return {'outcome':'rejected'}
            result={'outcome':e.event(dict(data,actor='system',at=now()))}
            if result['outcome']=='accepted' and data['type'] in ['configure','roster']:save_grants(iid,e)
            persist(iid,e);return result
        if len(path) in [4,5] and path[1]=='instances' and path[3]=='media':
            iid=path[2];row=db.execute('SELECT actor FROM tokens WHERE instance=? AND hash=?',(iid,digest(token))).fetchone()
            if not row:raise PermissionError()
            actor=row[0];e=engine(iid)
            if not image_package(e):raise PermissionError()
            if len(path)==4 and self.command=='POST':
                if actor not in (runtime.artifacts.bindings(e) if 'host_controls@1' in e.package['requires'] else e.participants):raise PermissionError()
                if not runtime.obj(data,['mediaType','data']) or data['mediaType'] not in ['image/png','audio/wav'] or type(data['data']) is not str or len(data['data'])>700000:return {'outcome':'invalid_media'}
                try:blob=base64.b64decode(data['data'],validate=True)
                except ValueError:return {'outcome':'invalid_media'}
                kind='image' if data['mediaType']=='image/png' else 'audio'
                if kind+'_contributions@1' not in e.package['requires'] or base64.b64encode(blob).decode()!=data['data'] or not (valid_png(blob) if kind=='image' else valid_wav(blob)):return {'outcome':'invalid_media'}
                ref='sha256:'+hashlib.sha256(blob).hexdigest()
                db.execute('INSERT OR IGNORE INTO media VALUES(?,?,?,?,?,?,?)',(iid,actor,ref,kind,1,data['mediaType'],blob))
                return {'outcome':'ready','ref':ref}
            if len(path)==5 and self.command=='GET':
                ref=path[4];e.settle(now());persist(iid,e)
                owns=authorized(iid,actor,ref) or authorized(iid,actor,ref,'audio')
                if not owns and not visible_ref(e.view(actor),ref):raise PermissionError()
                row=db.execute("SELECT media_type,bytes FROM media WHERE instance=? AND ref=? AND kind IN ('image','audio') AND ready=1 LIMIT 1",(iid,ref)).fetchone()
                if row is None:
                    row=db.execute('''SELECT media.media_type,media.bytes FROM input_grants JOIN media ON media.instance=input_grants.origin AND media.actor=input_grants.owner AND media.ref=input_grants.ref AND media.kind=input_grants.kind WHERE input_grants.destination=? AND input_grants.actor=? AND input_grants.ref=? AND media.ready=1 LIMIT 1''',(iid,actor,ref)).fetchone()
                if not row:raise KeyError()
                return {'ref':ref,'mediaType':row[0],'data':base64.b64encode(row[1]).decode()}
            raise KeyError()
        if len(path)==4 and path[1]=='instances':
            iid,action=path[2:]
            if action=='status' and self.command=='GET':
                if not admin:raise PermissionError()
                e=engine(iid);return {'pc':e.state['pc'],'clock':e.state['clock'],'phase':'complete' if e.state['pc']==len(e.plan) else 'active'}
            row=db.execute('SELECT actor FROM tokens WHERE instance=? AND hash=?',(iid,digest(token))).fetchone()
            if not row:raise PermissionError()
            actor=row[0];e=engine(iid)
            if action=='view' and self.command=='GET':result={'view':e.view(actor,now())}
            elif action=='events' and self.command=='POST':
                if not runtime.obj(data,['eventId','type','step','payload']) or data['type'] in ['tick','configure','close','roster']:return {'outcome':'rejected'}
                result={'outcome':e.event(dict(data,actor=actor,at=now()))}
            else:raise KeyError()
            persist(iid,e);return result
        raise KeyError()
server=ThreadingHTTPServer(('127.0.0.1',opts.port),Handler)
print(json.dumps({'port':server.server_port}),flush=True);server.serve_forever()
