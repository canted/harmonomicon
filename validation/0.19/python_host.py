#!/usr/bin/env python3
"""Local Python/SQLite app host for candidate 0.19; controlled trusted test clock."""
import argparse
import base64
import zlib
import hashlib
import importlib.util
import json
import secrets
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

spec=importlib.util.spec_from_file_location('runbook_runtime',Path(__file__).resolve().parents[2]/'format/0.19/runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
args=argparse.ArgumentParser();args.add_argument('--db',required=True);args.add_argument('--admin-token',required=True);args.add_argument('--port',type=int,default=0);args.add_argument('--disable',action='append',default=[])
args.add_argument('--assignment-seed',type=int);opts=args.parse_args();lock=threading.RLock()
db=sqlite3.connect(opts.db,check_same_thread=False,isolation_level=None)
db.executescript('''PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS meta (id INTEGER PRIMARY KEY, clock INTEGER NOT NULL);
INSERT OR IGNORE INTO meta VALUES(1,0);
CREATE TABLE IF NOT EXISTS packages(id TEXT, version TEXT, body TEXT NOT NULL, digest TEXT NOT NULL, PRIMARY KEY(id,version));
CREATE TABLE IF NOT EXISTS instances(id TEXT PRIMARY KEY, package_id TEXT, package_version TEXT, participants TEXT, organizer TEXT, started_at INTEGER, state TEXT);
CREATE TABLE IF NOT EXISTS tokens(instance TEXT, hash TEXT, actor TEXT, PRIMARY KEY(instance,hash));
CREATE TABLE IF NOT EXISTS media(instance TEXT,actor TEXT,ref TEXT,kind TEXT,ready INTEGER,media_type TEXT,bytes BLOB,PRIMARY KEY(instance,actor,ref));''')
supported=(runtime.CAPS|runtime.OPS)-set(opts.disable)
def digest(x):return hashlib.sha256(x.encode()).hexdigest()
def now():return db.execute('SELECT clock FROM meta').fetchone()[0]
def engine(iid):
    row=db.execute('SELECT package_id,package_version,participants,organizer,started_at,state FROM instances WHERE id=?',(iid,)).fetchone()
    if row is None:raise KeyError('not_found')
    pid,version,people,organizer,start,state=row
    package=json.loads(db.execute('SELECT body FROM packages WHERE id=? AND version=?',(pid,version)).fetchone()[0])
    return runtime.Engine(package,json.loads(people),organizer,start,json.loads(state),authorize_image=lambda actor,ref: authorized(iid,actor,ref))
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


def authorized(iid,actor,ref):
    return db.execute("SELECT 1 FROM media WHERE instance=? AND actor=? AND ref=? AND kind='image' AND ready=1",(iid,actor,ref)).fetchone() is not None
def visible_ref(value,ref):
    if type(value) is dict:return (set(value)=={'ref'} and value['ref']==ref) or any(visible_ref(v,ref) for v in value.values())
    return type(value) is list and any(visible_ref(v,ref) for v in value)
def image_package(e):return 'image_contributions@1' in e.package['requires']

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
            return {'format':runtime.FORMAT,'operations':sorted(runtime.OPS&supported),'capabilities':sorted(runtime.CAPS&supported),'media':{'image_contributions@1':{'kind':'image','uploadMediaTypes':['image/png']}} if 'image_contributions@1' in supported else {}}
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
            if not runtime.obj(data,['id','packageId','version','participants','organizer'] + (['settings'] if 'settings' in data else [])) or not runtime.text(data['id']):raise ValueError()
            row=db.execute('SELECT body,digest FROM packages WHERE id=? AND version=?',(data['packageId'],data['version'])).fetchone()
            if not row:return {'outcome':'invalid_package'}
            p=json.loads(row[0]);missing=sorted(set(p['requires'])-supported)
            if missing:return {'outcome':'unsupported','missing':missing}
            if db.execute('SELECT id FROM instances WHERE id=?',(data['id'],)).fetchone():return {'outcome':'instance_conflict'}
            if 'settings' in data and type(data['settings']) is not dict:return {'outcome':'invalid_setup'}
            try:e=runtime.Engine(p,data['participants'],data['organizer'],now(),settings=data.get('settings'),seed=opts.assignment_seed if opts.assignment_seed is not None else secrets.randbelow(4294967295)+1)
            except (ValueError,TypeError):return {'outcome':'invalid_setup'}
            db.execute('INSERT INTO instances VALUES(?,?,?,?,?,?,?)',(data['id'],p['id'],p['version'],runtime.canonical(data['participants']),data['organizer'],now(),runtime.canonical(e.state)))
            tokens={}
            for actor in data['participants']+[data['organizer']]:
                value=secrets.token_hex(24);tokens[actor]=value
                db.execute('INSERT INTO tokens VALUES(?,?,?)',(data['id'],digest(value),actor))
            return {'outcome':'created','tokens':tokens,'digest':row[1]}
        if len(path) in [4,5] and path[1]=='instances' and path[3]=='media':
            iid=path[2];row=db.execute('SELECT actor FROM tokens WHERE instance=? AND hash=?',(iid,digest(token))).fetchone()
            if not row:raise PermissionError()
            actor=row[0];e=engine(iid)
            if not image_package(e):raise PermissionError()
            if len(path)==4 and self.command=='POST':
                if actor not in e.participants:raise PermissionError()
                if not runtime.obj(data,['mediaType','data']) or data['mediaType']!='image/png' or type(data['data']) is not str or len(data['data'])>700000:return {'outcome':'invalid_media'}
                try:blob=base64.b64decode(data['data'],validate=True)
                except ValueError:return {'outcome':'invalid_media'}
                if base64.b64encode(blob).decode()!=data['data'] or not valid_png(blob):return {'outcome':'invalid_media'}
                ref='sha256:'+hashlib.sha256(blob).hexdigest()
                db.execute('INSERT OR IGNORE INTO media VALUES(?,?,?,?,?,?,?)',(iid,actor,ref,'image',1,'image/png',blob))
                return {'outcome':'ready','ref':ref}
            if len(path)==5 and self.command=='GET':
                ref=path[4];e.settle(now());persist(iid,e)
                if not authorized(iid,actor,ref) and not visible_ref(e.view(actor),ref):raise PermissionError()
                row=db.execute("SELECT media_type,bytes FROM media WHERE instance=? AND ref=? AND kind='image' AND ready=1 LIMIT 1",(iid,ref)).fetchone()
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
                if not runtime.obj(data,['eventId','type','step','payload']) or data['type']=='tick':return {'outcome':'rejected'}
                result={'outcome':e.event(dict(data,actor=actor,at=now()))}
            else:raise KeyError()
            persist(iid,e);return result
        raise KeyError()
server=ThreadingHTTPServer(('127.0.0.1',opts.port),Handler)
print(json.dumps({'port':server.server_port}),flush=True);server.serve_forever()
