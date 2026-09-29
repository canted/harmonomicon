import fs from 'node:fs';
import path from 'node:path';

function run(casePath) {
  const fixture = JSON.parse(fs.readFileSync(casePath, 'utf8'));
  const definition = JSON.parse(fs.readFileSync(path.resolve(path.dirname(casePath), fixture.definition), 'utf8'));
  const missing = definition.requires.filter(x => !fixture.capabilities.includes(x)).sort();
  if (missing.length) return { status: 'unsupported', missing };
  const { actors, config, kind } = definition;
  if (kind === 'handoff') {
    if (!Array.isArray(config.participants) || !config.participants.includes(config.start) ||
        !Number.isInteger(config.steps) || config.steps < 1 ||
        !((config.mode === 'contribute' && config.reveal === 'end') ||
          (config.mode === 'unlock' && config.reveal === 'each' &&
           Array.isArray(config.items) && config.items.length === config.steps))) throw Error('unsupported handoff configuration');
  } else if (kind === 'collection') {
    if (!Array.isArray(config.participants) || !['daily', 'one_shot'].includes(config.schedule) ||
        !['after_own', 'at_close'].includes(config.viewGate) ||
        !['mark', 'accept', 'reject'].includes(config.latePolicy)) throw Error('unsupported collection configuration');
  }
  let state;
  if (kind === 'handoff') {
    state = { phase: 'active', current: config.start, index: 0, entries: [], guide: '' };
  } else if (kind === 'collection') {
    state = { phase: 'waiting', occurrence: 0, nextOccurrence: 1, deadline: 0, posts: {}, late: {} };
  } else throw Error(`unknown mechanism: ${kind}`);
  const outcomes = [];
  for (const event of fixture.events) {
    const role = Object.hasOwn(actors, event.actor) ? actors[event.actor] : undefined;
    const p = event.payload;
    let accepted = false;
    if (kind === 'handoff' && event.type === 'advance' && role === 'participant' &&
        state.phase === 'active' && event.actor === state.current) {
      const last = state.index === config.steps - 1;
      const nextOK = last || (typeof p.next === 'string' && config.participants.includes(p.next) && p.next !== event.actor);
      const itemOK = config.mode === 'unlock' || typeof p.item === 'string';
      const guideOK = config.mode === 'unlock' || last || typeof p.guide === 'string';
      if (nextOK && itemOK && guideOK) {
        const item = config.mode === 'unlock' ? config.items[state.index] : p.item;
        state.entries.push(item);
        state.index += 1;
        state.guide = last ? '' : config.mode === 'contribute' ? p.guide : '';
        state.current = last ? null : p.next;
        if (last) state.phase = 'done';
        accepted = true;
      }
    } else if (kind === 'collection') {
      if (event.type === 'open' && ['host', 'system'].includes(role) &&
          Number.isInteger(p.occurrence) && Number.isInteger(p.deadline) &&
          p.occurrence === state.nextOccurrence && (config.schedule === 'daily' || p.occurrence === 1)) {
        state = { phase: 'open', occurrence: p.occurrence, nextOccurrence: p.occurrence + 1,
          deadline: p.deadline, posts: {}, late: {} };
        accepted = true;
      } else if (event.type === 'submit' && role === 'participant' && config.participants.includes(event.actor) &&
          state.phase === 'open' && !Object.hasOwn(state.posts, event.actor) &&
          typeof p.artifact === 'string' && Number.isInteger(event.at)) {
        const late = event.at > state.deadline;
        if (!late || config.latePolicy !== 'reject') {
          Object.defineProperty(state.posts, event.actor, { value: p.artifact, enumerable: true, configurable: true, writable: true });
          Object.defineProperty(state.late, event.actor, { value: late, enumerable: true, configurable: true, writable: true });
          accepted = true;
        }
      } else if (event.type === 'close' && ['host', 'system'].includes(role) && state.phase === 'open') {
        state.phase = 'closed';
        accepted = true;
      }
    }
    outcomes.push(accepted ? 'accepted' : 'rejected');
  }
  const views = {};
  for (const actor of fixture.viewActors) {
    const role = Object.hasOwn(actors, actor) ? actors[actor] : undefined;
    if (!role) { views[actor] = 'unknown_actor'; continue; }
    if (kind === 'handoff') {
      const view = { phase: state.phase, current: state.current, index: state.index };
      if (config.mode === 'contribute' && state.phase === 'active' && actor === state.current && state.index > 0) view.guide = state.guide;
      if (config.reveal === 'each' || state.phase === 'done') view.entries = [...state.entries];
      views[actor] = view;
    } else {
      const view = { phase: state.phase, occurrence: state.occurrence };
      const allowed = ['host', 'system'].includes(role) ||
        (role === 'participant' && config.participants.includes(actor) &&
          ((config.viewGate === 'after_own' && Object.hasOwn(state.posts, actor)) ||
           (config.viewGate === 'at_close' && state.phase === 'closed')));
      if (allowed) { view.posts = structuredClone(state.posts); view.late = structuredClone(state.late); }
      views[actor] = view;
    }
  }
  return { status: 'ok', state, outcomes, views };
}

if (process.argv.length !== 3) throw Error('usage: node run.mjs case.json');
process.stdout.write(JSON.stringify(run(path.resolve(process.argv[2]))) + '\n');
