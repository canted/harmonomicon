import fs from 'node:fs';
import path from 'node:path';

const clone = value => JSON.parse(JSON.stringify(value));
const own = (obj, key) => Object.hasOwn(obj, key);

function assignmentScore(roundId, userId, artifactId) {
  let value = (roundId * 73856093) ^ (userId * 19349663) ^ (artifactId * 83492791);
  value ^= value >>> 16;
  return value >>> 0;
}

function initial(definition) {
  if (definition.kind === 'competitive_relay') {
    const c = definition.config;
    if (!Array.isArray(c.mediaByStep) || c.mediaByStep.length !== c.routes?.length ||
        !c.routes.every(attempts => Array.isArray(attempts) && attempts.length &&
          attempts.every(pair => Array.isArray(pair) && pair.length === 2 && pair[0] !== pair[1]))) {
      throw Error('invalid relay configuration');
    }
    return { phase: 'ready', step: 0, attempt: 0, deadline: null, offers: [],
      chain: [clone(c.initial)], acceptedRequests: {} };
  }
  if (definition.kind === 'cover_response') {
    const c = definition.config;
    if (!Number.isInteger(c.roundId) || !Number.isInteger(c.minimumCovers) ||
        !Number.isInteger(c.coverDeadline) || !Number.isInteger(c.responseDeadline) ||
        c.responseDeadline <= c.coverDeadline || !Array.isArray(c.participants)) {
      throw Error('invalid cover-response configuration');
    }
    return { phase: 'collecting_covers', covers: {}, offers: {}, responses: {} };
  }
  throw Error(`unknown flow: ${definition.kind}`);
}

function relayEvent(s, e, c, role) {
  const p = e.payload ?? {};
  if (e.type === 'open' && role === 'system' && s.phase === 'ready' &&
      Number.isInteger(e.at) && Number.isInteger(p.deadline) && p.deadline > e.at) {
    s.offers = [...c.routes[s.step][s.attempt]];
    s.deadline = p.deadline;
    s.phase = 'open';
    return 'accepted';
  }
  if (e.type === 'submit' && role === 'participant' && typeof p.requestId === 'string' && p.requestId) {
    if (own(s.acceptedRequests, p.requestId)) {
      const prior = s.acceptedRequests[p.requestId];
      return prior.actor === e.actor && prior.step === p.step && prior.attempt === p.attempt &&
        prior.media === p.media && prior.artifact === p.artifact ? 'replayed' : 'rejected';
    }
    if (s.phase !== 'open' || !s.offers.includes(e.actor) || p.step !== s.step ||
        p.attempt !== s.attempt || !Number.isInteger(e.at) || e.at > s.deadline ||
        p.media !== c.mediaByStep[s.step] || typeof p.artifact !== 'string' || !p.artifact) return 'rejected';
    s.chain.push({ actor: e.actor, media: p.media, artifact: p.artifact });
    Object.defineProperty(s.acceptedRequests, p.requestId, { value: { actor: e.actor, step: p.step,
      attempt: p.attempt, media: p.media, artifact: p.artifact }, enumerable: true,
    writable: true, configurable: true });
    s.step += 1;
    s.attempt = 0;
    s.deadline = null;
    s.offers = [];
    s.phase = s.step === c.mediaByStep.length ? 'done' : 'ready';
    return 'accepted';
  }
  if (e.type === 'timeout' && role === 'system' && s.phase === 'open' &&
      Number.isInteger(e.at) && e.at >= s.deadline && p.step === s.step && p.attempt === s.attempt) {
    s.attempt += 1;
    s.deadline = null;
    s.offers = [];
    s.phase = s.attempt < c.routes[s.step].length ? 'ready' : 'stalled';
    return 'accepted';
  }
  return 'rejected';
}

function coverPhase(s, c, at) {
  if (s.phase === 'complete' || at >= c.responseDeadline) return 'complete';
  return at >= c.coverDeadline && Object.keys(s.covers).length >= c.minimumCovers
    ? 'collecting_responses' : 'collecting_covers';
}

function coverEvent(s, e, c, role) {
  const p = e.payload ?? {};
  if (!Number.isInteger(e.at)) return 'rejected';
  s.phase = coverPhase(s, c, e.at);
  if (e.type === 'tick' && role === 'system') return 'accepted';
  if (e.type === 'submit_cover' && role === 'participant' && c.participants.includes(e.actor) &&
      s.phase === 'collecting_covers' && Number.isInteger(p.coverId) &&
      typeof p.artifact === 'string' && p.artifact) {
    if (Object.values(s.covers).some(cover => cover.id === p.coverId && cover.actor !== e.actor)) return 'rejected';
    s.covers[e.actor] = { id: p.coverId, actor: e.actor, artifact: p.artifact };
    s.phase = coverPhase(s, c, e.at);
    return 'accepted';
  }
  if (e.type === 'remove_cover' && role === 'host' && e.at < c.coverDeadline &&
      Number.isInteger(p.coverId)) {
    const actor = Object.keys(s.covers).find(a => s.covers[a].id === p.coverId);
    if (!actor) return 'rejected';
    delete s.covers[actor];
    return 'accepted';
  }
  if (e.type === 'request_offer' && role === 'participant' &&
      s.phase === 'collecting_responses' && own(s.covers, e.actor)) {
    if (own(s.offers, e.actor)) return 'accepted';
    const counts = {};
    for (const offer of Object.values(s.offers)) for (const id of offer.options) counts[id] = (counts[id] ?? 0) + 1;
    const candidates = Object.values(s.covers).filter(cover => cover.actor !== e.actor);
    if (candidates.length < 2) return 'rejected';
    candidates.sort((a, b) => (counts[a.id] ?? 0) - (counts[b.id] ?? 0) ||
      assignmentScore(c.roundId, Number(e.actor), a.id) - assignmentScore(c.roundId, Number(e.actor), b.id));
    s.offers[e.actor] = { options: [candidates[0].id, candidates[1].id], chosen: null };
    return 'accepted';
  }
  if (e.type === 'choose_cover' && role === 'participant' &&
      s.phase === 'collecting_responses' && own(s.offers, e.actor) &&
      s.offers[e.actor].options.includes(p.coverId)) {
    s.offers[e.actor].chosen = p.coverId;
    return 'accepted';
  }
  if (e.type === 'submit_response' && role === 'participant' &&
      s.phase === 'collecting_responses' && own(s.offers, e.actor) &&
      s.offers[e.actor].chosen !== null && c.responseMedia.includes(p.media) &&
      typeof p.responseId === 'string' && p.responseId && typeof p.artifact === 'string' && p.artifact) {
    const coverId = s.offers[e.actor].chosen;
    if (!Object.values(s.covers).some(cover => cover.id === coverId)) return 'rejected';
    s.responses[e.actor] = { id: p.responseId, actor: e.actor, coverId, media: p.media, artifact: p.artifact };
    return 'accepted';
  }
  return 'rejected';
}

function view(definition, s, actor) {
  const role = definition.actors[actor];
  if (!role) return 'unknown_actor';
  if (definition.kind === 'competitive_relay') {
    const v = { phase: s.phase, step: s.step, attempt: s.attempt };
    if (role === 'system') { v.chain = clone(s.chain); v.offers = [...s.offers]; }
    if (s.phase === 'open' && s.offers.includes(actor)) {
      v.input = clone(s.chain.at(-1)); v.media = definition.config.mediaByStep[s.step]; v.deadline = s.deadline;
    }
    if (s.phase === 'done' && role === 'participant') v.chain = clone(s.chain);
    return v;
  }
  const v = { phase: s.phase, coverCount: Object.keys(s.covers).length };
  if (role === 'host' || role === 'system') {
    v.covers = clone(s.covers); v.offers = clone(s.offers); v.responses = clone(s.responses);
  } else if (role === 'participant') {
    if (own(s.covers, actor)) v.cover = clone(s.covers[actor]);
    if (own(s.offers, actor)) {
      v.offeredCovers = s.offers[actor].options.map(id => clone(Object.values(s.covers).find(cover => cover.id === id)));
      if (s.offers[actor].chosen !== null) v.chosenCoverId = s.offers[actor].chosen;
    }
    if (own(s.responses, actor)) v.response = clone(s.responses[actor]);
  }
  if (s.phase === 'complete') v.results = clone(Object.values(s.responses));
  return v;
}

function run(casePath, { stopAt = null, resumePath = null } = {}) {
  const fixture = JSON.parse(fs.readFileSync(casePath, 'utf8'));
  const definition = JSON.parse(fs.readFileSync(path.resolve(path.dirname(casePath), fixture.definition), 'utf8'));
  const missing = definition.requires.filter(x => !fixture.capabilities.includes(x)).sort();
  if (missing.length) return { status: 'unsupported', missing };
  const snapshot = resumePath ? JSON.parse(fs.readFileSync(resumePath, 'utf8')) : null;
  const startAt = snapshot ? snapshot.nextIndex : 0;
  if (!Number.isInteger(startAt) || startAt < 0 || startAt > fixture.events.length ||
      (stopAt !== null && (!Number.isInteger(stopAt) || stopAt < startAt || stopAt > fixture.events.length))) {
    throw Error('invalid event range');
  }
  const state = snapshot ? snapshot.state : initial(definition);
  const outcomes = snapshot ? snapshot.outcomes : [];
  if (!Array.isArray(outcomes) || outcomes.length !== startAt) throw Error('invalid snapshot');
  const endAt = stopAt ?? fixture.events.length;
  for (let index = startAt; index < endAt; index++) {
    const event = fixture.events[index];
    const role = own(definition.actors, event.actor) ? definition.actors[event.actor] : undefined;
    outcomes.push(definition.kind === 'competitive_relay'
      ? relayEvent(state, event, definition.config, role)
      : coverEvent(state, event, definition.config, role));
  }
  if (stopAt !== null) return { status: 'checkpoint', nextIndex: endAt, state, outcomes };
  const views = {};
  for (const actor of fixture.viewActors) views[actor] = view(definition, state, actor);
  return { status: 'ok', state, outcomes, views };
}

if (process.argv.length !== 3 && process.argv.length !== 5) {
  throw Error('usage: node run.mjs case.json [--prefix count | --resume snapshot.json]');
}
let options = {};
if (process.argv.length === 5) {
  if (process.argv[3] === '--prefix') options = { stopAt: Number(process.argv[4]) };
  else if (process.argv[3] === '--resume') options = { resumePath: path.resolve(process.argv[4]) };
  else throw Error('unknown option');
}
process.stdout.write(JSON.stringify(run(path.resolve(process.argv[2]), options)) + '\n');
