import fs from 'node:fs';

const copy = value => structuredClone(value);
const stage = (definition, state) => definition.stages[state.stage] ?? null;

function score(roundId, userId, artifactId) {
  let value = ((roundId * 73856093) ^ (userId * 19349663) ^ (artifactId * 83492791)) >>> 0;
  return (value ^ (value >>> 16)) >>> 0;
}

function advance(definition, state) {
  state.stage++;
  state.status = 'idle';
  state.attempt = 0;
  state.deadline = null;
  state.assignees = [];
  const next = stage(definition, state);
  state.phase = next ? next.idlePhase : definition.donePhase;
  if (!next) state.status = 'done';
}

function finish(definition, state) {
  state.stage = definition.stages.length;
  state.status = 'done';
  state.phase = definition.donePhase;
  state.deadline = null;
  state.assignees = [];
}

function synchronizeTime(definition, state, at) {
  if (!Number.isInteger(at) || ['done', 'stalled'].includes(state.status)) return;
  if (Number.isInteger(definition.finalDeadline) && at >= definition.finalDeadline) {
    finish(definition, state);
    return;
  }
  const current = stage(definition, state);
  if (current?.type === 'collection' && at >= current.deadline &&
      Object.keys(state.collections[current.pool]).length >= current.minimum) advance(definition, state);
}

function initialize(definition) {
  const collections = Object.create(null), outputs = Object.create(null);
  for (const current of definition.stages) {
    if (current.type === 'collection') collections[current.pool] = Object.create(null);
    if (current.type === 'work' && current.commit.mode === 'per_actor')
      outputs[current.commit.target] = Object.create(null);
  }
  return {stage: 0, status: 'idle', phase: definition.stages[0].idlePhase,
    attempt: 0, deadline: null, assignees: [], chain: copy(definition.initialChain),
    collections, assignments: Object.create(null), outputs,
    acceptedRequests: Object.create(null), skips: 0};
}

function collect(definition, state, current, event, role) {
  if (current?.type !== 'collection' || role !== 'participant') return 'rejected';
  const id = event.payload[current.idField], artifact = event.payload[current.artifactField];
  if (!Number.isInteger(id) || typeof artifact !== 'string' || !artifact) return 'rejected';
  const pool = state.collections[current.pool];
  if (Object.values(pool).some(item => item.id === id && item.actor !== event.actor)) return 'rejected';
  pool[event.actor] = {id, actor: event.actor, artifact};
  synchronizeTime(definition, state, event.at);
  return 'accepted';
}

function remove(state, current, event, role) {
  if (current?.type !== 'collection' || role !== 'host' || event.at >= current.removeBefore) return 'rejected';
  const id = event.payload[current.idField];
  if (!Number.isInteger(id)) return 'rejected';
  const pool = state.collections[current.pool];
  for (const [actor, item] of Object.entries(pool)) {
    if (item.id === id) { delete pool[actor]; return 'accepted'; }
  }
  return 'rejected';
}

function assign(state, current, event, role) {
  if (current?.type !== 'work') return 'rejected';
  const setting = current.assignment;
  if (setting.policy === 'fixed_recipients') {
    const deadline = event.payload.deadline;
    if (role !== 'system' || state.status !== 'idle' || !Number.isInteger(deadline) || deadline <= event.at)
      return 'rejected';
    state.assignees = [...setting.routes[state.attempt]];
    state.deadline = deadline;
    state.status = 'active';
    state.phase = current.activePhase;
    return 'accepted';
  }
  if (setting.policy === 'queue_lease') {
    if (role !== 'participant' || state.status !== 'idle') return 'rejected';
    state.assignees = [event.actor];
    state.status = 'active';
    state.phase = current.activePhase;
    return 'accepted';
  }
  if (setting.policy === 'balanced_artifacts') {
    if (setting.tie !== 'cover_offer_score_v1')
      throw new Error(`unsupported assignment tie-breaker: ${setting.tie}`);
    const pool = state.collections[setting.pool], actor = event.actor;
    if (role !== 'participant' || !Object.hasOwn(pool, actor)) return 'rejected';
    if (Object.hasOwn(state.assignments, actor)) return 'accepted';
    const counts = {};
    for (const offer of Object.values(state.assignments))
      for (const id of offer.options) counts[id] = (counts[id] ?? 0) + 1;
    const candidates = Object.values(pool).filter(item => !setting.excludeSelf || item.actor !== actor);
    if (candidates.length < setting.count) return 'rejected';
    candidates.sort((a, b) => (counts[a.id] ?? 0) - (counts[b.id] ?? 0) ||
      score(setting.roundId, Number(actor), a.id) - score(setting.roundId, Number(actor), b.id));
    state.assignments[actor] = {options: candidates.slice(0, setting.count).map(item => item.id), chosen: null};
    return 'accepted';
  }
  throw new Error(`unsupported assignment policy: ${setting.policy}`);
}

function choose(state, current, event, role) {
  if (current?.type !== 'work' || role !== 'participant') return 'rejected';
  const offer = state.assignments[event.actor], chosen = event.payload[current.assignment.choiceField];
  if (!offer || !offer.options.includes(chosen)) return 'rejected';
  offer.chosen = chosen;
  return 'accepted';
}

function commit(definition, state, current, event, role) {
  const payload = event.payload, requestId = payload.requestId;
  if (typeof requestId === 'string' && Object.hasOwn(state.acceptedRequests, requestId)) {
    const prior = state.acceptedRequests[requestId];
    return JSON.stringify(prior) === JSON.stringify({actor: event.actor, step: payload.step,
      attempt: payload.attempt, media: payload.media, artifact: payload.artifact}) ? 'replayed' : 'rejected';
  }
  if (current?.type !== 'work' || role !== 'participant') return 'rejected';
  const setting = current.commit;
  const allowed = Array.isArray(setting.media) ? setting.media : [setting.media];
  if (!allowed.includes(payload.media) || typeof payload.artifact !== 'string' || !payload.artifact)
    return 'rejected';
  const actor = event.actor;
  if (setting.mode === 'first') {
    if (state.status !== 'active' || !state.assignees.includes(actor)) return 'rejected';
    if (setting.stepAttempt && (payload.step !== state.stage || payload.attempt !== state.attempt ||
        event.at > state.deadline)) return 'rejected';
    if (setting.requestId && (typeof requestId !== 'string' || !requestId)) return 'rejected';
    state.chain.push({actor, media: payload.media, artifact: payload.artifact});
    if (setting.requestId) state.acceptedRequests[requestId] = {actor, step: payload.step,
      attempt: payload.attempt, media: payload.media, artifact: payload.artifact};
    advance(definition, state);
    return 'accepted';
  }
  if (setting.mode === 'per_actor') {
    const offer = state.assignments[actor], id = payload[setting.idField];
    if (!offer || offer.chosen === null || typeof id !== 'string' || !id) return 'rejected';
    const choice = offer.chosen;
    if (!Object.values(state.collections).some(pool => Object.values(pool).some(item => item.id === choice)))
      return 'rejected';
    state.outputs[setting.target][actor] = {id, actor, [setting.linkField]: choice,
      media: payload.media, artifact: payload.artifact};
    return 'accepted';
  }
  throw new Error(`unsupported completion mode: ${setting.mode}`);
}

function expire(definition, state, current, event, role) {
  if (current?.type !== 'work' || current.assignment.policy !== 'fixed_recipients' ||
      role !== 'system' || state.status !== 'active' || event.at < state.deadline ||
      event.payload.step !== state.stage || event.payload.attempt !== state.attempt) return 'rejected';
  state.attempt++;
  state.deadline = null;
  state.assignees = [];
  if (state.attempt < current.assignment.routes.length) {
    state.status = 'idle';
    state.phase = current.idlePhase;
  } else {
    state.status = 'stalled';
    state.phase = definition.stalledPhase;
  }
  return 'accepted';
}

function release(state, current, event, role) {
  if (current?.type !== 'work' || current.assignment.policy !== 'queue_lease' ||
      role !== 'participant' || state.status !== 'active' ||
      state.assignees.length !== 1 || state.assignees[0] !== event.actor) return 'rejected';
  state.assignees = [];
  state.status = 'idle';
  state.phase = current.idlePhase;
  state.skips++;
  return 'accepted';
}

function apply(definition, state, event) {
  const role = Object.hasOwn(definition.actors, event.actor) ? definition.actors[event.actor] : null;
  const operation = Object.hasOwn(definition.bindings, event.type) ? definition.bindings[event.type] : null;
  if (!role || !operation || !Number.isInteger(event.at) ||
      typeof event.payload !== 'object' || event.payload === null || Array.isArray(event.payload))
    return 'rejected';
  synchronizeTime(definition, state, event.at);
  const current = stage(definition, state);
  switch (operation) {
    case 'advance': return role === 'system' ? 'accepted' : 'rejected';
    case 'collect': return collect(definition, state, current, event, role);
    case 'remove': return remove(state, current, event, role);
    case 'assign': return assign(state, current, event, role);
    case 'choose': return choose(state, current, event, role);
    case 'commit': return commit(definition, state, current, event, role);
    case 'expire': return expire(definition, state, current, event, role);
    case 'release': return release(state, current, event, role);
    default: throw new Error(`unknown operation: ${operation}`);
  }
}

function view(definition, state, actor) {
  const role = Object.hasOwn(definition.actors, actor) ? definition.actors[actor] : null;
  if (!role) return 'unknown_actor';
  const result = {phase: state.phase, stage: state.stage, attempt: state.attempt};
  for (const item of definition.stages) {
    if (item.type !== 'collection') continue;
    const pool = state.collections[item.pool];
    if (item.countViewField) result[item.countViewField] = Object.keys(pool).length;
    if (role === 'participant' && Object.hasOwn(pool, actor)) result[item.viewField] = copy(pool[actor]);
  }
  if (['host', 'system'].includes(role)) {
    result.assignees = copy(state.assignees);
    result.chain = copy(state.chain);
    result.collections = copy(state.collections);
    result.assignments = copy(state.assignments);
    result.outputs = copy(state.outputs);
  } else {
    const current = stage(definition, state);
    if (current?.type === 'work' && state.status === 'active' &&
        state.assignees.includes(actor) && state.chain.length) {
      result.input = copy(state.chain.at(-1));
      result.media = current.commit.media;
      if (state.deadline !== null) result.deadline = state.deadline;
    }
    if (Object.hasOwn(state.assignments, actor)) {
      const offer = state.assignments[actor];
      for (const item of definition.stages) {
        if (item.type !== 'work' || item.assignment.policy !== 'balanced_artifacts') continue;
        const setting = item.assignment, pool = state.collections[setting.pool];
        result[setting.viewField] = offer.options.map(id => copy(Object.values(pool).find(entry => entry.id === id)));
        if (offer.chosen !== null) result[setting.choiceViewField] = offer.chosen;
      }
    }
    for (const item of definition.stages) {
      if (item.type !== 'work' || item.commit.mode !== 'per_actor') continue;
      const setting = item.commit;
      if (Object.hasOwn(state.outputs[setting.target], actor))
        result[setting.viewField] = copy(state.outputs[setting.target][actor]);
    }
  }
  if (state.status === 'done') {
    if (definition.reveal?.chain === 'on_done') result.chain = copy(state.chain);
    if (definition.reveal?.outputs === 'on_done')
      result.results = Object.values(state.outputs).flatMap(pool => Object.values(pool).map(copy));
  }
  return result;
}

function run(casePath, definitionPath) {
  const fixture = JSON.parse(fs.readFileSync(casePath, 'utf8'));
  const definition = JSON.parse(fs.readFileSync(definitionPath, 'utf8'));
  const missing = definition.requires.filter(capability => !fixture.capabilities.includes(capability)).sort();
  if (missing.length) return {status: 'unsupported', missing};
  const state = initialize(definition);
  const outcomes = fixture.events.map(event => apply(definition, state, event));
  const views = Object.fromEntries(fixture.viewActors.map(actor => [actor, view(definition, state, actor)]));
  return {status: 'ok', state, outcomes, views};
}

if (process.argv.length !== 4) throw new Error('usage: node run.mjs source-case.json composed-definition.json');
console.log(JSON.stringify(run(process.argv[2], process.argv[3])));
