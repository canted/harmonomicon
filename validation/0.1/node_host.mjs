#!/usr/bin/env node
// Local 0.1 host: Node HTTP server, independent SQLite state, and deadline worker.
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { DatabaseSync } from 'node:sqlite';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const packageDir = join(ROOT, 'format/0.1/examples');
const packageFiles = readdirSync(packageDir).filter(n => n.endsWith('.json')).map(name => join(packageDir, name));
const packages = new Map();
const packageHashes = new Map();
for (const file of packageFiles) {
  const bytes = readFileSync(file);
  const value = JSON.parse(bytes.toString('utf8'));
  packages.set(value.id, value);
  packageHashes.set(value.id, createHash('sha256').update(bytes).digest('hex'));
}
const CAPABILITIES = new Set(['identity@1', 'serial_events@1', 'durable_state@1', 'private_views@1', 'clock@1', 'text@1']);
const CONTRACTS = new Set(['timed_collection@1', 'sequential_handoff@1']);
const SAFE_MAX = Number.MAX_SAFE_INTEGER;
const args = process.argv.slice(2);
function option(name, fallback = null) {
  const i = args.indexOf(name);
  return i < 0 ? fallback : args[i + 1];
}
function options(name) {
  return args.flatMap((item, i) => item === name ? [args[i + 1]] : []);
}
const dbPath = resolve(option('--db'));
const port = Number(option('--port', '0'));
const adminToken = option('--admin-token');
const disabledCapabilities = new Set(options('--disable-capability'));
const disabledContracts = new Set(options('--disable-contract'));
const db = new DatabaseSync(dbPath);
db.exec('PRAGMA journal_mode=WAL');
db.exec(`
  CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
  INSERT OR IGNORE INTO meta(key,value) VALUES ('clock','0');
  CREATE TABLE IF NOT EXISTS instances (
    id TEXT PRIMARY KEY, package_id TEXT NOT NULL, state_json TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS tokens (
    instance_id TEXT NOT NULL, token_hash TEXT NOT NULL, actor TEXT NOT NULL,
    PRIMARY KEY(instance_id,token_hash)
  );
  CREATE TABLE IF NOT EXISTS event_log (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, instance_id TEXT NOT NULL,
    event_id TEXT, type TEXT NOT NULL, actor TEXT NOT NULL,
    at INTEGER NOT NULL, payload_json TEXT NOT NULL,
    UNIQUE(instance_id,event_id)
  );
`);
for (const row of db.prepare('SELECT package_id,state_json FROM instances').all()) {
  const pkg = packages.get(row.package_id);
  const state = JSON.parse(row.state_json);
  if (!pkg || state.packageVersion !== pkg.version || state.packageHash !== packageHashes.get(row.package_id)) {
    throw new Error('persisted instance package changed without a new version');
  }
}

const validTime = x => Number.isSafeInteger(x) && x >= 0 && x <= SAFE_MAX;
const validText = x => typeof x === 'string' && x.length > 0;
const hash = x => createHash('sha256').update(x).digest('hex');
const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
function sameKeys(object, keys) {
  return object && typeof object === 'object' && !Array.isArray(object)
    && Object.keys(object).length === keys.length && keys.every(key => own(object, key));
}
function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
  return JSON.stringify(value);
}
function transaction(fn) {
  db.exec('BEGIN IMMEDIATE');
  try {
    const result = fn();
    db.exec('COMMIT');
    return result;
  } catch (error) {
    db.exec('ROLLBACK');
    throw error;
  }
}
const clock = () => Number(db.prepare("SELECT value FROM meta WHERE key='clock'").get().value);
function writeState(id, state) {
  db.prepare('UPDATE instances SET state_json=? WHERE id=?').run(JSON.stringify(state), id);
}
function appendEvent(id, eventId, type, actor, at, payload) {
  db.prepare('INSERT INTO event_log(instance_id,event_id,type,actor,at,payload_json) VALUES (?,?,?,?,?,?)')
    .run(id, eventId, type, actor, at, canonical(payload));
}
function reconcile(id, state, now) {
  if (state.contract !== 'timed_collection@1') return;
  let changed = false;
  if (state.phase === 'waiting' && now >= state.opensAt) {
    state.phase = 'open';
    appendEvent(id, null, 'tick', 'system', state.opensAt, {});
    changed = true;
  }
  if (state.phase === 'open' && now >= state.closesAt) {
    state.phase = 'closed';
    appendEvent(id, null, 'tick', 'system', state.closesAt, {});
    changed = true;
  }
  if (changed) writeState(id, state);
}
function semanticView(state, actor) {
  const entries = state.entries;
  let view;
  if (state.contract === 'timed_collection@1') {
    view = { phase: state.phase, submissionCount: entries.length };
  } else {
    view = { phase: state.phase, step: Math.min(state.index + 1, state.route.length),
      currentActor: state.phase === 'complete' ? null : state.route[state.index] };
  }
  if (state.participants.includes(actor)) {
    const entry = entries.find(x => x.actor === actor);
    if (entry) view.own = entry;
  }
  if (state.contract === 'timed_collection@1') {
    if (state.phase === 'closed') view.entries = entries;
  } else if (state.phase === 'complete') {
    view.entries = entries;
  } else if (actor === state.route[state.index]) {
    view.input = state.index === 0 ? state.prompt : entries.at(-1).value;
  }
  return view;
}
function createInstance(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)
      || !['instanceId', 'packageId', 'organizer', 'participants', 'tokens'].every(k => own(body, k))) {
    return [400, { status: 'invalid_instance' }];
  }
  const pkg = packages.get(body.packageId);
  if (!pkg || pkg.format !== 'harmonomicon.activity-package/0.1') return [400, { status: 'invalid_package' }];
  const contract = pkg.behavior.contract;
  const missing = pkg.requires.filter(cap => !CAPABILITIES.has(cap) || disabledCapabilities.has(cap));
  if (!CONTRACTS.has(contract) || disabledContracts.has(contract)) missing.push('behavior:' + contract);
  if (missing.length) return [200, { status: 'unsupported', missing: missing.sort() }];
  const { instanceId, organizer, participants, tokens } = body;
  const bounds = pkg.participants;
  if (!validText(instanceId) || !validText(organizer) || organizer === 'system'
      || !Array.isArray(participants) || participants.length < bounds.min || participants.length > bounds.max
      || !participants.every(x => validText(x) && x !== 'system')
      || new Set(participants).size !== participants.length || participants.includes(organizer)
      || !tokens || typeof tokens !== 'object' || Array.isArray(tokens)
      || Object.keys(tokens).length !== participants.length + 1
      || ![organizer, ...participants].every(x => own(tokens, x) && validText(tokens[x]))
      || new Set(Object.values(tokens)).size !== Object.values(tokens).length) {
    return [400, { status: 'invalid_instance' }];
  }
  const now = clock();
  const prompt = own(body, 'prompt') ? body.prompt : pkg.content.prompt;
  if (!validText(prompt) || (own(body, 'prompt') && !pkg.behavior.allowPromptOverride)) {
    return [400, { status: 'invalid_instance' }];
  }
  const state = { packageVersion: pkg.version, packageHash: packageHashes.get(pkg.id),
    contract, medium: pkg.behavior.medium, organizer, participants, prompt,
    entries: [], index: 0, lastAt: now };
  if (contract === 'timed_collection@1') {
    if (!validTime(body.opensAt) || !validTime(body.closesAt) || now > body.opensAt || body.opensAt >= body.closesAt) {
      return [400, { status: 'invalid_instance' }];
    }
    Object.assign(state, { opensAt: body.opensAt, closesAt: body.closesAt,
      phase: now < body.opensAt ? 'waiting' : 'open' });
  } else {
    const route = body.route;
    if (!Array.isArray(route) || route.length !== pkg.behavior.steps || new Set(route).size !== route.length
        || route.some(x => !participants.includes(x))) return [400, { status: 'invalid_instance' }];
    Object.assign(state, { route, phase: 'active' });
  }
  if (db.prepare('SELECT id FROM instances WHERE id=?').get(instanceId)) return [409, { status: 'already_exists' }];
  db.prepare('INSERT INTO instances(id,package_id,state_json) VALUES (?,?,?)').run(instanceId, pkg.id, JSON.stringify(state));
  const insertToken = db.prepare('INSERT INTO tokens(instance_id,token_hash,actor) VALUES (?,?,?)');
  for (const [actor, token] of Object.entries(tokens)) insertToken.run(instanceId, hash(token), actor);
  return [201, { status: 'created', instanceId }];
}
function actorFor(id, authorization) {
  if (!authorization?.startsWith('Bearer ')) return null;
  const token = authorization.slice(7);
  return db.prepare('SELECT actor FROM tokens WHERE instance_id=? AND token_hash=?').get(id, hash(token))?.actor ?? null;
}
function submitEvent(id, actor, body) {
  const row = db.prepare('SELECT state_json FROM instances WHERE id=?').get(id);
  if (!row) return [404, { status: 'not_found' }];
  const state = JSON.parse(row.state_json);
  const now = clock();
  if (now < state.lastAt) return [400, { status: 'invalid_time' }];
  reconcile(id, state, now);
  state.lastAt = now;
  if (!sameKeys(body, ['eventId', 'type', 'payload'])) {
    writeState(id, state);
    return [200, { outcome: 'rejected' }];
  }
  const { eventId, type, payload } = body;
  if (!validText(eventId) || !validText(type) || !payload || typeof payload !== 'object' || Array.isArray(payload)) {
    writeState(id, state);
    return [200, { outcome: 'rejected' }];
  }
  const prior = db.prepare('SELECT type,actor,payload_json FROM event_log WHERE instance_id=? AND event_id=?').get(id, eventId);
  if (prior) {
    const outcome = prior.type === type && prior.actor === actor && prior.payload_json === canonical(payload) ? 'replayed' : 'rejected';
    writeState(id, state);
    return [200, { outcome }];
  }
  const value = sameKeys(payload, ['value']) ? payload.value : null;
  const validValue = validText(value) && state.medium === 'text';
  if (type !== 'submit' || !state.participants.includes(actor) || !validValue) {
    writeState(id, state);
    return [200, { outcome: 'rejected' }];
  }
  const allowed = state.contract === 'timed_collection@1'
    ? state.phase === 'open' && !state.entries.some(x => x.actor === actor)
    : state.phase === 'active' && actor === state.route[state.index];
  if (!allowed) {
    writeState(id, state);
    return [200, { outcome: 'rejected' }];
  }
  state.entries.push({ actor, value });
  if (state.contract === 'sequential_handoff@1') {
    state.index++;
    if (state.index === state.route.length) state.phase = 'complete';
  }
  appendEvent(id, eventId, type, actor, now, payload);
  writeState(id, state);
  return [200, { outcome: 'accepted' }];
}
function respond(res, status, value) {
  const bytes = Buffer.from(JSON.stringify(value));
  res.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': bytes.length });
  res.end(bytes);
}
async function readBody(req) {
  const parts = [];
  let total = 0;
  for await (const part of req) {
    total += part.length;
    if (total > 1000000) throw new Error('body too large');
    parts.push(part);
  }
  return JSON.parse(Buffer.concat(parts).toString('utf8'));
}
const server = createServer(async (req, res) => {
  const path = new URL(req.url, 'http://localhost').pathname;
  try {
    if (req.method === 'GET' && path === '/health') return respond(res, 200, { status: 'ok' });
    if (req.method === 'GET' && /^\/instances\/[^/]+\/view$/.test(path)) {
      const id = path.split('/')[2];
      const result = transaction(() => {
        const actor = actorFor(id, req.headers.authorization);
        if (!actor) return [401, { status: 'unauthorized' }];
        const row = db.prepare('SELECT state_json FROM instances WHERE id=?').get(id);
        if (!row) return [404, { status: 'not_found' }];
        const state = JSON.parse(row.state_json);
        reconcile(id, state, clock());
        return [200, semanticView(state, actor)];
      });
      return respond(res, ...result);
    }
    if (req.method !== 'POST') return respond(res, 404, { status: 'not_found' });
    let body;
    try { body = await readBody(req); }
    catch { return respond(res, 400, { status: 'invalid_json' }); }
    if (path === '/admin/clock') {
      if (req.headers['x-admin-token'] !== adminToken) return respond(res, 401, { status: 'unauthorized' });
      const result = transaction(() => {
        const at = body && typeof body === 'object' ? body.at : null;
        if (!validTime(at) || at < clock()) return [400, { status: 'invalid_time' }];
        db.prepare("UPDATE meta SET value=? WHERE key='clock'").run(String(at));
        return [200, { at }];
      });
      return respond(res, ...result);
    }
    if (path === '/admin/instances') {
      if (req.headers['x-admin-token'] !== adminToken) return respond(res, 401, { status: 'unauthorized' });
      return respond(res, ...transaction(() => createInstance(body)));
    }
    if (/^\/instances\/[^/]+\/events$/.test(path)) {
      const id = path.split('/')[2];
      const result = transaction(() => {
        const actor = actorFor(id, req.headers.authorization);
        if (!actor) return [401, { status: 'unauthorized' }];
        return submitEvent(id, actor, body);
      });
      return respond(res, ...result);
    }
    return respond(res, 404, { status: 'not_found' });
  } catch (error) {
    console.error(error);
    return respond(res, 500, { status: 'host_error' });
  }
});
setInterval(() => {
  try {
    transaction(() => {
      const now = clock();
      for (const row of db.prepare('SELECT id,state_json FROM instances').all()) {
        reconcile(row.id, JSON.parse(row.state_json), now);
      }
    });
  } catch (error) { console.error('worker error:', error); }
}, 25);
server.listen(port, '127.0.0.1', () => console.log(`READY ${server.address().port}`));
