// Independent JavaScript interpreter for two experimental ongoing-activity shapes.
import fs from 'node:fs';

const copy = value => JSON.parse(JSON.stringify(value));
const empty = () => Object.create(null);
const validId = value => typeof value === 'string' && value.length > 0;
const has = (object, key) => Object.hasOwn(object, key);

function phase(definition, at) {
  const calendar = definition.calendar;
  if (at < calendar.registrationEnds) return 'registration';
  if (at < calendar.submissionsEnd) return 'making';
  if (at < calendar.reviewsEnd) return 'review';
  return 'reveal';
}

function initialize(definition) {
  if (definition.calendar.kind === 'windows') {
    return { now: 0, phase: phase(definition, 0), teams: empty(), progress: [],
      responses: [], finals: empty(), reviews: [] };
  }
  return { now: 0, phase: 'waiting', day: 0, deadline: null, history: empty() };
}

function teamOf(state, actor) {
  return Object.entries(state.teams).find(([, members]) => members.includes(actor))?.[0] ?? null;
}

function jamEvent(definition, state, event, operation, role) {
  const { actor, payload } = event;
  if (operation === 'tick') return role === 'system' ? 'accepted' : 'rejected';
  if (operation === 'register_team') {
    const { team: name, members } = payload;
    if (role !== 'host' || state.phase !== 'registration' || !validId(name) || has(state.teams, name) ||
        !Array.isArray(members) || members.length === 0 || members.some(member => !validId(member)) ||
        new Set(members).size !== members.length ||
        members.some(member => !has(definition.actors, member) ||
          definition.actors[member] !== 'participant' || teamOf(state, member))) {
      return 'rejected';
    }
    state.teams[name] = [...members];
    return 'accepted';
  }
  const team = teamOf(state, actor);
  if (role !== 'participant' || team === null) return 'rejected';
  if (operation === 'post_progress') {
    const { id, artifact, audience } = payload;
    if (state.phase !== 'making' || !validId(id) || !validId(artifact) ||
        !definition.progressAudiences.includes(audience) || state.progress.some(post => post.id === id)) {
      return 'rejected';
    }
    state.progress.push({ id, actor, team, artifact, audience });
    return 'accepted';
  }
  if (operation === 'respond') {
    const { id, postId, text } = payload;
    const post = state.progress.find(item => item.id === postId);
    if (state.phase !== 'making' || !validId(id) || !validId(text) || !post ||
        (post.audience === 'team' && post.team !== team) ||
        state.responses.some(item => item.id === id)) return 'rejected';
    state.responses.push({ id, postId, actor, text });
    return 'accepted';
  }
  if (operation === 'submit_final') {
    const { artifact } = payload;
    if (state.phase !== 'making' || !validId(artifact) || has(state.finals, team)) return 'rejected';
    state.finals[team] = { team, actor, artifact };
    return 'accepted';
  }
  if (operation === 'review') {
    const { id, team: target, text } = payload;
    if (state.phase !== 'review' || !validId(id) || !validId(target) || !validId(text) ||
        !has(state.finals, target) ||
        target === team || state.reviews.some(item => item.id === id)) return 'rejected';
    state.reviews.push({ id, team: target, actor, text });
    return 'accepted';
  }
  return 'rejected';
}

function dailyEvent(definition, state, event, operation, role) {
  const { actor, payload, at } = event;
  if (operation === 'open_day') {
    const { day, deadline } = payload;
    if (role !== 'system' || state.phase !== 'waiting' || !Number.isSafeInteger(day) ||
        day !== state.day + 1 || !Number.isSafeInteger(deadline) || deadline <= at) return 'rejected';
    state.day = day;
    state.deadline = deadline;
    state.phase = 'open';
    const status = empty();
    for (const [name, kind] of Object.entries(definition.actors)) {
      if (kind === 'participant') status[name] = 'pending';
    }
    state.history[day] = { status, entries: empty() };
    return 'accepted';
  }
  if (operation === 'submit_day') {
    const { artifact } = payload;
    if (role !== 'participant' || state.phase !== 'open' || at >= state.deadline || !validId(artifact)) {
      return 'rejected';
    }
    const current = state.history[state.day];
    if (has(current.entries, actor)) return 'rejected';
    current.entries[actor] = { actor, artifact };
    current.status[actor] = 'complete';
    return 'accepted';
  }
  if (operation === 'close_day') {
    if (role !== 'system' || state.phase !== 'open' || at < state.deadline) return 'rejected';
    const current = state.history[state.day];
    for (const [name, status] of Object.entries(current.status)) {
      if (status === 'pending') current.status[name] = 'missed';
    }
    state.phase = 'waiting';
    state.deadline = null;
    return 'accepted';
  }
  return 'rejected';
}

function apply(definition, state, event) {
  if (!event || !Number.isSafeInteger(event.at) || event.at < state.now ||
      !validId(event.actor) || !validId(event.type) || !event.payload ||
      typeof event.payload !== 'object' || Array.isArray(event.payload)) return 'rejected';
  const role = has(definition.actors, event.actor) ? definition.actors[event.actor] : null;
  const operation = has(definition.bindings, event.type) ? definition.bindings[event.type] : null;
  if (!role || !operation) return 'rejected';
  state.now = event.at;
  if (definition.calendar.kind === 'windows') {
    state.phase = phase(definition, event.at);
    return jamEvent(definition, state, event, operation, role);
  }
  return dailyEvent(definition, state, event, operation, role);
}

function view(definition, state, actor) {
  const role = has(definition.actors, actor) ? definition.actors[actor] : null;
  if (!role) return 'unknown_actor';
  if (definition.calendar.kind === 'daily') {
    const history = empty();
    for (const [day, item] of Object.entries(state.history)) {
      let entries;
      if (role === 'system' || role === 'host' || definition.contentAudience === 'participants') {
        entries = item.entries;
      } else {
        entries = has(item.entries, actor) ? { [actor]: item.entries[actor] } : empty();
      }
      history[day] = { status: copy(item.status), entries: copy(entries) };
    }
    return { phase: state.phase, day: state.day, history };
  }
  if (role === 'system' || role === 'host') return copy(state);
  const team = teamOf(state, actor);
  const progress = state.progress.filter(post => post.audience === 'participants' || post.team === team);
  const postIds = new Set(progress.map(post => post.id));
  const finals = empty();
  for (const [name, item] of Object.entries(state.finals)) {
    if (state.phase === 'review' || state.phase === 'reveal' || name === team) finals[name] = item;
  }
  const reviews = state.reviews.filter(item => state.phase === 'reveal' || item.actor === actor);
  return { phase: state.phase, teams: copy(state.teams), progress: copy(progress),
    responses: copy(state.responses.filter(item => postIds.has(item.postId))),
    finals: copy(finals), reviews: copy(reviews) };
}

function run(casePath, definitionPath) {
  const fixture = JSON.parse(fs.readFileSync(casePath, 'utf8'));
  const definition = JSON.parse(fs.readFileSync(definitionPath, 'utf8'));
  const missing = definition.requires.filter(capability => !fixture.capabilities.includes(capability)).sort();
  if (missing.length) return { status: 'unsupported', missing };
  const state = initialize(definition);
  const outcomes = fixture.events.map(event => apply(definition, state, event));
  const views = empty();
  for (const actor of fixture.viewActors) views[actor] = view(definition, state, actor);
  return { status: 'ok', state, outcomes, views };
}

if (process.argv.length !== 4) throw new Error('usage: node run.mjs case.json definition.json');
process.stdout.write(JSON.stringify(run(process.argv[2], process.argv[3])));
