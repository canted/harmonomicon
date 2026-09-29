import fs from 'node:fs';
import path from 'node:path';

const MISSING = Symbol('missing');
const clone = value => structuredClone(value);

function at(root, dotted) {
  let current = root;
  for (const key of dotted.split('.')) {
    if (current === null || typeof current !== 'object' || !Object.hasOwn(current, key)) return MISSING;
    current = current[key];
  }
  return current;
}

function value(expr, state, event) {
  if (expr && typeof expr === 'object' && !Array.isArray(expr) && Object.keys(expr).length === 1 && Object.hasOwn(expr, 'ref')) {
    const [root, ...rest] = expr.ref.split('.');
    if (!rest.length || !['state', 'event'].includes(root)) return MISSING;
    return at(root === 'state' ? state : event, rest.join('.'));
  }
  return expr;
}

function equal(a, b) {
  if (a === b) return true;
  if (a === null || b === null || typeof a !== typeof b) return false;
  if (Array.isArray(a) || Array.isArray(b)) return Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.every((x, i) => equal(x, b[i]));
  if (typeof a === 'object') {
    const ak = Object.keys(a).sort();
    const bk = Object.keys(b).sort();
    return equal(ak, bk) && ak.every(k => equal(a[k], b[k]));
  }
  return false;
}

function condition(rule, state, event) {
  const left = value(rule.left, state, event);
  const right = value(rule.right, state, event);
  if (left === MISSING || right === MISSING) return false;
  switch (rule.op) {
    case 'eq': return equal(left, right);
    case 'ne': return !equal(left, right);
    case 'lt': return typeof left === 'number' && typeof right === 'number' && left < right;
    case 'lte': return typeof left === 'number' && typeof right === 'number' && left <= right;
    case 'gt': return typeof left === 'number' && typeof right === 'number' && left > right;
    case 'gte': return typeof left === 'number' && typeof right === 'number' && left >= right;
    case 'has_key': return left !== null && !Array.isArray(left) && typeof left === 'object' && typeof right === 'string' && Object.hasOwn(left, right);
    case 'lacks_key': return left !== null && !Array.isArray(left) && typeof left === 'object' && typeof right === 'string' && !Object.hasOwn(left, right);
    case 'length_eq': return Array.isArray(left) && typeof right === 'number' && left.length === right;
    case 'length_lt': return Array.isArray(left) && typeof right === 'number' && left.length < right;
    case 'length_gte': return Array.isArray(left) && typeof right === 'number' && left.length >= right;
    default: return false;
  }
}

function destination(state, dotted) {
  const keys = dotted.split('.');
  const key = keys.pop();
  const parent = keys.length ? at(state, keys.join('.')) : state;
  if (parent === MISSING || parent === null || Array.isArray(parent) || typeof parent !== 'object' || !Object.hasOwn(parent, key)) throw Error('invalid path');
  return [parent, key];
}

function apply(action, state, event, actors) {
  const [parent, key] = destination(state, action.path);
  const operand = value(action.value, state, event);
  if (operand === MISSING) throw Error('missing value');
  switch (action.op) {
    case 'set': parent[key] = clone(operand); break;
    case 'add':
      if (typeof parent[key] !== 'number' || typeof operand !== 'number') throw Error('numeric add');
      parent[key] += operand;
      break;
    case 'append':
      if (!Array.isArray(parent[key])) throw Error('array append');
      parent[key].push(clone(operand));
      break;
    case 'put': {
      const mapKey = value(action.key, state, event);
      if (parent[key] === null || Array.isArray(parent[key]) || typeof parent[key] !== 'object' || typeof mapKey !== 'string') throw Error('object put');
      Object.defineProperty(parent[key], mapKey, { value: clone(operand), enumerable: true, configurable: true, writable: true });
      break;
    }
    case 'partition': {
      if (operand === null || Array.isArray(operand) || typeof operand !== 'object' || !Array.isArray(action.sizes)) throw Error('invalid partition');
      const actual = Object.values(operand).flat();
      const expected = Object.keys(actors).filter(id => actors[id] === 'participant');
      if (Object.values(operand).some(group => !Array.isArray(group) || !action.sizes.includes(group.length)) ||
          actual.length !== expected.length || new Set(actual).size !== actual.length ||
          actual.some(id => !expected.includes(id))) throw Error('partition mismatch');
      parent[key] = clone(operand);
      break;
    }
    default: throw Error('unknown action');
  }
}

function run(fixturePath) {
  const fixture = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
  const definition = JSON.parse(fs.readFileSync(path.resolve(path.dirname(fixturePath), fixture.definition), 'utf8'));
  const missing = definition.requires.filter(cap => !fixture.capabilities.includes(cap)).sort();
  if (missing.length) return { status: 'unsupported', missing };
  let state = clone(definition.initial);
  const outcomes = [];
  for (const event of fixture.events) {
    const role = Object.hasOwn(definition.actors, event.actor) ? definition.actors[event.actor] : undefined;
    const matches = definition.transitions.filter(t => t.on === event.type && t.by.includes(role) &&
      (t.if || []).every(c => condition(c, state, event)));
    if (matches.length !== 1) { outcomes.push('rejected'); continue; }
    const draft = clone(state);
    try {
      for (const action of matches[0].do) apply(action, draft, event, definition.actors);
      state = draft;
      outcomes.push('accepted');
    } catch { outcomes.push('rejected'); }
  }
  const views = {};
  for (const actor of fixture.viewActors || []) {
    const role = Object.hasOwn(definition.actors, actor) ? definition.actors[actor] : undefined;
    if (!role) { views[actor] = 'unknown_actor'; continue; }
    const context = { actor };
    const projection = {};
    for (const rule of definition.views) {
      if (rule.by.includes(role) && (rule.if || []).every(c => condition(c, state, context))) {
        projection[rule.field] = clone(state[rule.field]);
      }
    }
    views[actor] = projection;
  }
  return { status: 'ok', state, outcomes, views };
}

if (process.argv.length !== 3) throw Error('usage: node run.mjs fixture.json');
process.stdout.write(JSON.stringify(run(path.resolve(process.argv[2]))) + '\n');
