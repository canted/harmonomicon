#!/usr/bin/env node
// Local 0.4 host: Node HTTP server, independent SQLite state, and deadline worker.
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { DatabaseSync } from 'node:sqlite';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const packages = new Map();
const packageHashes = new Map();
const packageKey = (id, version) => JSON.stringify([id, version]);
const CAPABILITIES = new Set(['identity@1', 'serial_events@1', 'durable_state@1', 'private_views@1', 'clock@1', 'text@1', 'policy:balanced_artifacts_exact32@1']);
const CONTRACTS = new Set(['timed_collection@1', 'sequential_handoff@1', 'repeated_collection@1', 'offered_response@1']);
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
  CREATE TABLE IF NOT EXISTS packages (
    id TEXT NOT NULL, version TEXT NOT NULL, body_json TEXT NOT NULL, digest TEXT NOT NULL,
    PRIMARY KEY(id,version)
  );
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
for (const row of db.prepare('SELECT id,version,body_json,digest FROM packages').all()) {
  const key = packageKey(row.id, row.version);
  const pkg = JSON.parse(row.body_json);
  if (createHash('sha256').update(row.body_json).digest('hex') !== row.digest) throw new Error('stored package digest mismatch');
  packages.set(key, pkg);
  packageHashes.set(key, row.digest);
}
for (const row of db.prepare('SELECT package_id,state_json FROM instances').all()) {
  const state = JSON.parse(row.state_json);
  const key = packageKey(row.package_id, state.packageVersion);
  if (!packages.has(key) || state.packageHash !== packageHashes.get(key)) {
    throw new Error('persisted instance package changed without a new version');
  }
}

const validTime = x => Number.isSafeInteger(x) && x >= 0 && x <= SAFE_MAX;
const validText = x => typeof x === 'string' && x.length > 0;
const MAX_U64 = 18446744073709551615n;
const MOD32 = 1n << 32n;
const canonicalU64 = x => typeof x === 'string' && x.length <= 20 && /^(0|[1-9][0-9]*)$/.test(x) && BigInt(x) <= MAX_U64;
function offerPhase(state, now) {
  if (now < state.opensAt) return 'waiting';
  if (now < state.sourceDeadline) return 'sources_open';
  if (state.sources.length < 3) return 'insufficient_sources';
  return now < state.responseDeadline ? 'responses_open' : 'complete';
}
function chooseOffer(state, actor) {
  const exposed = new Map(state.sources.map(source => [source.actor, 0]));
  for (const offer of Object.values(state.offers)) {
    for (const sourceId of offer) exposed.set(sourceId, exposed.get(sourceId) + 1);
  }
  const r = BigInt(state.roundId);
  const u = BigInt(actor);
  function score(sourceId) {
    const a = BigInt(sourceId);
    const x = ((r * 73856093n) % MOD32) ^ ((u * 19349663n) % MOD32) ^ ((a * 83492791n) % MOD32);
    return Number(x ^ (x >> 16n));
  }
  return state.sources.filter(source => source.actor !== actor).sort((a, b) => {
    const count = exposed.get(a.actor) - exposed.get(b.actor);
    if (count !== 0) return count;
    const scored = score(a.actor) - score(b.actor);
    if (scored !== 0) return scored;
    const ai = BigInt(a.actor), bi = BigInt(b.actor);
    return ai < bi ? -1 : ai > bi ? 1 : 0;
  }).slice(0, 2).map(source => source.actor);
}
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
function scalarString(value) {
  for (let i = 0; i < value.length; i++) {
    const unit = value.charCodeAt(i);
    if (unit >= 0xD800 && unit <= 0xDBFF) {
      const next = value.charCodeAt(++i);
      if (!(next >= 0xDC00 && next <= 0xDFFF)) return false;
    } else if (unit >= 0xDC00 && unit <= 0xDFFF) return false;
  }
  return true;
}
function scalarJson(value) {
  if (typeof value === 'string') return scalarString(value);
  if (Array.isArray(value)) return value.every(scalarJson);
  if (value && typeof value === 'object') return Object.entries(value).every(([key, item]) => scalarString(key) && scalarJson(item));
  return true;
}
function validPackage(pkg) {
  if (!scalarJson(pkg) || !sameKeys(pkg, ['format', 'id', 'version', 'content', 'provenance', 'participants', 'requires', 'behavior'])) return false;
  if (pkg.format !== 'harmonomicon.activity-package/0.4'
      || typeof pkg.id !== 'string' || !/^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+$/.test(pkg.id)
      || typeof pkg.version !== 'string' || !/^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$/.test(pkg.version)) return false;
  if (!sameKeys(pkg.content, ['language', 'title', 'summary', 'setup', 'prompt', 'participant', 'completion', 'access'])
      || !Object.values(pkg.content).every(validText)) return false;
  const prov = pkg.provenance;
  if (!prov || typeof prov !== 'object' || Array.isArray(prov)
      || !['kind', 'credit', 'rights'].every(k => own(prov, k))
      || Object.keys(prov).some(k => !['kind', 'credit', 'rights', 'sourceUrl'].includes(k))
      || !['original', 'adaptation'].includes(prov.kind) || !validText(prov.credit) || !validText(prov.rights)
      || (own(prov, 'sourceUrl') && (!validText(prov.sourceUrl) || !/^https?:\/\//.test(prov.sourceUrl)))
      || (prov.kind === 'adaptation' && !own(prov, 'sourceUrl'))) return false;
  const bounds = pkg.participants;
  if (!sameKeys(bounds, ['min', 'max']) || !Number.isSafeInteger(bounds.min)
      || !Number.isSafeInteger(bounds.max) || bounds.min < 2 || bounds.max < bounds.min) return false;
  const req = pkg.requires;
  const allowed = new Set(['identity@1', 'serial_events@1', 'durable_state@1', 'private_views@1',
    'clock@1', 'text@1', 'image_ref@1', 'policy:balanced_artifacts_exact32@1']);
  if (!Array.isArray(req) || new Set(req).size !== req.length || !req.every(x => allowed.has(x))) return false;
  const needed = new Set(['identity@1', 'serial_events@1', 'durable_state@1', 'private_views@1']);
  const b = pkg.behavior;
  if (!b || typeof b !== 'object' || Array.isArray(b) || typeof b.contract !== 'string') return false;
  if (b.contract === 'timed_collection@1' || b.contract === 'sequential_handoff@1' || b.contract === 'repeated_collection@1') {
    const keys = ['contract', 'medium', 'allowPromptOverride'];
    if (b.contract === 'sequential_handoff@1') keys.push('steps');
    if (b.contract === 'repeated_collection@1') keys.push('intervalMs', 'windowMs', 'occurrences', 'visibility');
    if (!sameKeys(b, keys) || !['text', 'image_ref'].includes(b.medium)
        || typeof b.allowPromptOverride !== 'boolean') return false;
    needed.add(b.medium === 'text' ? 'text@1' : 'image_ref@1');
    if (b.contract !== 'sequential_handoff@1') needed.add('clock@1');
    if (b.contract === 'sequential_handoff@1' && (!Number.isSafeInteger(b.steps) || b.steps < 2
        || b.steps !== bounds.min || b.steps !== bounds.max)) return false;
    if (b.contract === 'repeated_collection@1' && (!Number.isSafeInteger(b.intervalMs)
        || !Number.isSafeInteger(b.windowMs) || b.intervalMs < 1 || b.intervalMs > SAFE_MAX
        || b.windowMs < 1 || b.windowMs > b.intervalMs || !Number.isSafeInteger(b.occurrences)
        || b.occurrences < 2 || b.occurrences > 366
        || !['private', 'group_after_close', 'group_immediate'].includes(b.visibility))) return false;
  } else if (b.contract === 'offered_response@1') {
    if (!sameKeys(b, ['contract', 'sourceMedium', 'allowPromptOverride', 'assignmentPolicy'])
        || !['text', 'image_ref'].includes(b.sourceMedium) || typeof b.allowPromptOverride !== 'boolean'
        || b.assignmentPolicy !== 'policy:balanced_artifacts_exact32@1' || bounds.min < 3) return false;
    needed.add('clock@1'); needed.add('text@1');
    needed.add(b.sourceMedium === 'text' ? 'text@1' : 'image_ref@1');
    needed.add('policy:balanced_artifacts_exact32@1');
  } else return false;
  if (b.contract !== 'offered_response@1' && req.includes('policy:balanced_artifacts_exact32@1')) return false;
  return [...needed].every(x => req.includes(x));
}
function importPackage(body) {
  if (!sameKeys(body, ['package']) || !validPackage(body.package)) return [400, { status: 'invalid_package' }];
  const pkg = body.package;
  const payload = canonical(pkg);
  if (Buffer.byteLength(payload, 'utf8') > 1000000) return [400, { status: 'invalid_package' }];
  const digest = hash(payload);
  const key = packageKey(pkg.id, pkg.version);
  const existing = db.prepare('SELECT digest FROM packages WHERE id=? AND version=?').get(pkg.id, pkg.version);
  if (existing) return existing.digest === digest
    ? [200, { status: 'existing', sha256: digest }] : [409, { status: 'package_conflict' }];
  db.prepare('INSERT INTO packages(id,version,body_json,digest) VALUES (?,?,?,?)')
    .run(pkg.id, pkg.version, payload, digest);
  packages.set(key, pkg);
  packageHashes.set(key, digest);
  return [201, { status: 'imported', sha256: digest }];
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
function repeatedPhase(state, now) {
  if (now < state.startsAt) return ['waiting', null, 0];
  const index = Math.min(Math.floor((now - state.startsAt) / state.intervalMs), state.occurrenceCount - 1);
  const opened = index + 1;
  const closesAt = state.startsAt + index * state.intervalMs + state.windowMs;
  if (now < closesAt) return ['open', opened, opened];
  return [index === state.occurrenceCount - 1 ? 'complete' : 'between', null, opened];
}
function repeatedBoundary(state, boundaryIndex) {
  const occurrence = Math.floor(boundaryIndex / 2);
  const opensAt = state.startsAt + occurrence * state.intervalMs;
  return boundaryIndex % 2 === 0 ? opensAt : opensAt + state.windowMs;
}
function reconcile(id, state, now) {
  if (state.contract === 'offered_response@1') {
    const boundaries = [state.opensAt, state.sourceDeadline, state.responseDeadline];
    const limit = now >= state.sourceDeadline && state.sources.length < 3 ? 2 : 3;
    let changed = false;
    while (state.nextBoundary < limit && boundaries[state.nextBoundary] <= now) {
      const at = boundaries[state.nextBoundary];
      appendEvent(id, null, 'tick', 'system', at, {});
      state.nextBoundary++;
      changed = true;
    }
    const phase = offerPhase(state, now);
    if (state.phase !== phase) {
      state.phase = phase;
      changed = true;
    }
    if (changed) writeState(id, state);
    return;
  }
  if (state.contract === 'repeated_collection@1') {
    let changed = false;
    while (state.nextBoundary < state.occurrenceCount * 2) {
      const at = repeatedBoundary(state, state.nextBoundary);
      if (at > now) break;
      appendEvent(id, null, 'tick', 'system', at, {});
      state.nextBoundary++;
      changed = true;
    }
    const [phase, current] = repeatedPhase(state, now);
    if (state.phase !== phase || state.currentOccurrence !== current) {
      state.phase = phase;
      state.currentOccurrence = current;
      changed = true;
    }
    if (changed) writeState(id, state);
    return;
  }
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
function semanticView(state, actor, now) {
  if (state.contract === 'offered_response@1') {
    const phase = offerPhase(state, now);
    const view = { phase, sourceCount: state.sources.length, responseCount: state.responses.length };
    if (state.participants.includes(actor)) {
      const ownSource = state.sources.find(source => source.actor === actor);
      if (ownSource) view.ownSource = ownSource;
      if (own(state.offers, actor)) {
        const byActor = new Map(state.sources.map(source => [source.actor, source]));
        view.offer = state.offers[actor].map(sourceId => byActor.get(sourceId));
      }
      const ownResponse = state.responses.find(response => response.actor === actor);
      if (ownResponse) view.ownResponse = ownResponse;
    }
    if (phase === 'complete') {
      view.sources = state.sources;
      view.responses = state.responses;
    }
    return view;
  }
  const entries = state.entries;
  if (state.contract === 'repeated_collection@1') {
    const [phase, current, opened] = repeatedPhase(state, now);
    const view = { phase, currentOccurrence: current, occurrences: [] };
    for (let index = 0; index < opened; index++) {
      const number = index + 1;
      const closesAt = state.startsAt + index * state.intervalMs + state.windowMs;
      const itemPhase = now >= closesAt ? 'closed' : 'open';
      const groupEntries = entries[index];
      const submitted = new Set(groupEntries.map(entry => entry.actor));
      const item = { number, phase: itemPhase, submissionCount: groupEntries.length,
        statuses: state.participants.map(person => ({ actor: person,
          status: submitted.has(person) ? 'complete' : itemPhase === 'open' ? 'pending' : 'missed' })) };
      if (state.participants.includes(actor)) {
        const ownEntry = groupEntries.find(entry => entry.actor === actor);
        if (ownEntry) item.own = ownEntry;
      }
      if (state.visibility === 'group_immediate' || (state.visibility === 'group_after_close' && itemPhase === 'closed')) {
        item.entries = groupEntries;
      }
      view.occurrences.push(item);
    }
    return view;
  }
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
  if (!validText(body.packageId) || !validText(body.packageVersion)) return [400, { status: 'invalid_instance' }];
  const key = packageKey(body.packageId, body.packageVersion);
  const pkg = packages.get(key);
  if (!pkg || pkg.format !== 'harmonomicon.activity-package/0.4') return [400, { status: 'invalid_package' }];
  const contract = pkg.behavior.contract;
  const requiredFields = ['instanceId', 'packageId', 'packageVersion', 'organizer', 'participants', 'tokens',
    ...(contract === 'timed_collection@1' ? ['opensAt', 'closesAt']
      : contract === 'repeated_collection@1' ? ['startsAt']
      : contract === 'offered_response@1' ? ['opensAt', 'sourceDeadline', 'responseDeadline', 'roundId'] : ['route'])];
  if (!requiredFields.every(key => own(body, key)) || Object.keys(body).some(key => !requiredFields.includes(key) && key !== 'prompt')) {
    return [400, { status: 'invalid_instance' }];
  }
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
  if (contract === 'offered_response@1' && !participants.every(canonicalU64)) return [400, { status: 'invalid_instance' }];
  const now = clock();
  const prompt = own(body, 'prompt') ? body.prompt : pkg.content.prompt;
  if (!validText(prompt) || (own(body, 'prompt') && !pkg.behavior.allowPromptOverride)) {
    return [400, { status: 'invalid_instance' }];
  }
  const state = { packageVersion: pkg.version, packageHash: packageHashes.get(key),
    contract, medium: pkg.behavior.medium ?? null, organizer, participants, prompt,
    entries: [], index: 0, lastAt: now };
  if (contract === 'timed_collection@1') {
    if (!validTime(body.opensAt) || !validTime(body.closesAt) || now > body.opensAt || body.opensAt >= body.closesAt) {
      return [400, { status: 'invalid_instance' }];
    }
    Object.assign(state, { opensAt: body.opensAt, closesAt: body.closesAt,
      phase: now < body.opensAt ? 'waiting' : 'open' });
  } else if (contract === 'offered_response@1') {
    if (![body.opensAt, body.sourceDeadline, body.responseDeadline].every(validTime)
        || now > body.opensAt || body.opensAt >= body.sourceDeadline
        || body.sourceDeadline >= body.responseDeadline || !canonicalU64(body.roundId)) {
      return [400, { status: 'invalid_instance' }];
    }
    Object.assign(state, { opensAt: body.opensAt, sourceDeadline: body.sourceDeadline,
      responseDeadline: body.responseDeadline, roundId: body.roundId,
      sourceMedium: pkg.behavior.sourceMedium, sources: [], offers: {}, responses: [], nextBoundary: 0,
      phase: now < body.opensAt ? 'waiting' : 'sources_open' });
  } else if (contract === 'repeated_collection@1') {
    const { intervalMs, windowMs, occurrences, visibility } = pkg.behavior;
    if (!validTime(body.startsAt) || now > body.startsAt
        || body.startsAt + (occurrences - 1) * intervalMs + windowMs > SAFE_MAX) {
      return [400, { status: 'invalid_instance' }];
    }
    Object.assign(state, { startsAt: body.startsAt, intervalMs, windowMs,
      occurrenceCount: occurrences, visibility, entries: Array.from({ length: occurrences }, () => []), nextBoundary: 0 });
    [state.phase, state.currentOccurrence] = repeatedPhase(state, now);
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
  if (state.contract === 'offered_response@1') {
    const phase = state.phase;
    if (type === 'submit_source' && phase === 'sources_open' && state.participants.includes(actor)
        && sameKeys(payload, ['value']) && validText(payload.value) && state.sourceMedium === 'text'
        && !state.sources.some(source => source.actor === actor)) {
      state.sources.push({ actor, value: payload.value });
      appendEvent(id, eventId, type, actor, now, payload);
      writeState(id, state);
      return [200, { outcome: 'accepted' }];
    }
    if (type === 'request_offer' && phase === 'responses_open' && state.participants.includes(actor)
        && sameKeys(payload, []) && state.sources.some(source => source.actor === actor)) {
      const outcome = own(state.offers, actor) ? 'existing' : 'accepted';
      if (outcome === 'accepted') state.offers[actor] = chooseOffer(state, actor);
      appendEvent(id, eventId, type, actor, now, payload);
      writeState(id, state);
      return [200, { outcome }];
    }
    if (type === 'submit_response' && phase === 'responses_open' && own(state.offers, actor)
        && sameKeys(payload, ['source', 'value']) && typeof payload.source === 'string'
        && state.offers[actor].includes(payload.source) && validText(payload.value)
        && !state.responses.some(response => response.actor === actor)) {
      state.responses.push({ actor, source: payload.source, value: payload.value });
      appendEvent(id, eventId, type, actor, now, payload);
      writeState(id, state);
      return [200, { outcome: 'accepted' }];
    }
    writeState(id, state);
    return [200, { outcome: 'rejected' }];
  }
  if (state.contract === 'repeated_collection@1') {
    const validPayload = sameKeys(payload, ['occurrence', 'value']);
    const occurrence = validPayload ? payload.occurrence : null;
    const value = validPayload ? payload.value : null;
    const allowed = type === 'submit' && state.participants.includes(actor)
      && Number.isInteger(occurrence) && state.phase === 'open'
      && occurrence === state.currentOccurrence && validText(value) && state.medium === 'text'
      && !state.entries[occurrence - 1].some(entry => entry.actor === actor);
    if (!allowed) {
      writeState(id, state);
      return [200, { outcome: 'rejected' }];
    }
    state.entries[occurrence - 1].push({ actor, value });
    appendEvent(id, eventId, type, actor, now, payload);
    writeState(id, state);
    return [200, { outcome: 'accepted' }];
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
    if (req.method === 'GET' && path === '/capabilities') return respond(res, 200, {
      format: 'harmonomicon.activity-package/0.4',
      behaviors: [...CONTRACTS].filter(x => !disabledContracts.has(x)).sort(),
      capabilities: [...CAPABILITIES].filter(x => !disabledCapabilities.has(x)).sort()
    });
    if (req.method === 'GET' && /^\/packages\/[^/]+\/[^/]+$/.test(path)) {
      const [, , id, version] = path.split('/');
      const key = packageKey(id, version);
      return packages.has(key) ? respond(res, 200, { package: packages.get(key), sha256: packageHashes.get(key) })
        : respond(res, 404, { status: 'not_found' });
    }
    if (req.method === 'GET' && /^\/instances\/[^/]+\/view$/.test(path)) {
      const id = path.split('/')[2];
      const result = transaction(() => {
        const actor = actorFor(id, req.headers.authorization);
        if (!actor) return [401, { status: 'unauthorized' }];
        const row = db.prepare('SELECT state_json FROM instances WHERE id=?').get(id);
        if (!row) return [404, { status: 'not_found' }];
        const state = JSON.parse(row.state_json);
        reconcile(id, state, clock());
        return [200, semanticView(state, actor, clock())];
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
    if (path === '/admin/packages/import') {
      if (req.headers['x-admin-token'] !== adminToken) return respond(res, 401, { status: 'unauthorized' });
      return respond(res, ...transaction(() => importPackage(body)));
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
