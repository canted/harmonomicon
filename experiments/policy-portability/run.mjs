// JavaScript implementation of balanced_artifacts_exact32@1.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const MASK = (1n << 32n) - 1n;
const MAX_ID = (1n << 64n) - 1n;
const empty = () => Object.create(null);
const has = (object, key) => Object.hasOwn(object, key);
const read = filename => JSON.parse(fs.readFileSync(filename, 'utf8'));

function validId(value) {
  return typeof value === 'string' && /^(0|[1-9][0-9]*)$/.test(value) && BigInt(value) <= MAX_ID;
}

function score(roundId, recipient, artifact) {
  const x = ((BigInt(roundId) * 73856093n) & MASK) ^
    ((BigInt(recipient) * 19349663n) & MASK) ^
    ((BigInt(artifact) * 83492791n) & MASK);
  return x ^ (x >> 16n);
}

function loadPolicy() {
  const manifest = read(path.join(ROOT, 'policy.json'));
  const plan = read(path.resolve(ROOT, manifest.basePlan));
  const setting = plan.stages.find(item => item.type === 'work' &&
    item.assignment.policy === 'balanced_artifacts')?.assignment;
  if (!setting || setting.tie !== 'cover_offer_score_v1' || setting.excludeSelf !== true ||
      !Number.isSafeInteger(setting.roundId) || setting.roundId < 0) {
    throw new Error('incompatible base assignment');
  }
  return { manifest, setting };
}

function validateCovers(covers) {
  if (!Array.isArray(covers) || covers.some(item => !item || !validId(item.id) || !validId(item.owner))) {
    throw new Error('covers must have canonical unsigned IDs');
  }
  if (new Set(covers.map(item => item.id)).size !== covers.length ||
      new Set(covers.map(item => item.owner)).size !== covers.length) {
    throw new Error('artifact IDs and owners must be unique');
  }
}

function request(state, covers, setting, event) {
  if (!event || typeof event.requestId !== 'string' || !event.requestId ||
      !validId(event.recipient)) return { status: 'rejected' };
  const { requestId, recipient } = event;
  const { offers, requestLedger } = state;
  if (has(requestLedger, requestId)) {
    if (requestLedger[requestId] !== recipient) return { status: 'rejected' };
    return { status: 'replayed', options: [...offers[recipient]] };
  }
  if (has(offers, recipient)) {
    requestLedger[requestId] = recipient;
    return { status: 'existing', options: [...offers[recipient]] };
  }
  if (!covers.some(item => item.owner === recipient)) return { status: 'rejected' };
  const candidates = covers.filter(item => item.owner !== recipient);
  if (candidates.length < setting.count) return { status: 'rejected' };
  const counts = empty();
  for (const saved of Object.values(offers)) {
    for (const artifact of saved) counts[artifact] = (counts[artifact] ?? 0) + 1;
  }
  candidates.sort((a, b) => {
    const countDifference = (counts[a.id] ?? 0) - (counts[b.id] ?? 0);
    if (countDifference) return countDifference;
    const left = score(setting.roundId, recipient, a.id);
    const right = score(setting.roundId, recipient, b.id);
    if (left !== right) return left < right ? -1 : 1;
    const leftId = BigInt(a.id), rightId = BigInt(b.id);
    return leftId < rightId ? -1 : leftId > rightId ? 1 : 0;
  });
  const options = candidates.slice(0, setting.count).map(item => item.id);
  offers[recipient] = options;
  requestLedger[requestId] = recipient;
  return { status: 'accepted', options: [...options] };
}

function run(casePath, snapshotPath = null, stopAt = null) {
  const fixture = read(casePath);
  const { manifest, setting } = loadPolicy();
  const missing = manifest.requires.filter(item => !fixture.capabilities.includes(item)).sort();
  if (missing.length) return { status: 'unsupported', missing };
  validateCovers(fixture.covers);
  const snapshot = snapshotPath ? read(snapshotPath) : null;
  if (snapshot && snapshot.policy !== manifest.policy) throw new Error('checkpoint policy mismatch');
  const state = snapshot ? snapshot.state : { offers: empty(), requestLedger: empty() };
  const outcomes = snapshot ? snapshot.outcomes : [];
  const start = snapshot ? snapshot.nextIndex : 0;
  const end = stopAt === null ? fixture.requests.length : stopAt;
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 0 ||
      start > end || end > fixture.requests.length) throw new Error('invalid checkpoint index');
  for (const event of fixture.requests.slice(start, end)) {
    outcomes.push(request(state, fixture.covers, setting, event));
  }
  if (stopAt !== null) {
    return { status: 'checkpoint', policy: manifest.policy, nextIndex: end, state, outcomes };
  }
  return { status: 'ok', state, outcomes };
}

if (process.argv.length < 3 || process.argv.length > 5) {
  throw new Error('usage: node run.mjs case.json [snapshot.json|-] [stopAt]');
}
const snapshotArg = process.argv[3] && process.argv[3] !== '-' ? process.argv[3] : null;
const stopArg = process.argv[4] === undefined ? null : Number(process.argv[4]);
process.stdout.write(JSON.stringify(run(process.argv[2], snapshotArg, stopArg)));
