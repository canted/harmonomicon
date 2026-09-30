import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildDiagram, FORMAT} from './model.js';
import {layoutDiagram} from './diagram-layout.js';
const here = path.dirname(fileURLToPath(import.meta.url));
const source = path.join(here,'../format/0.14/examples');
const read = file => JSON.parse(fs.readFileSync(file,'utf8'));
const files = fs.readdirSync(source).filter(file => file.endsWith('.json')).sort();
const base = {format:FORMAT,id:'example.custom',version:'1',content:{title:'Custom'},participants:{min:2,max:4},requires:[]};

function flatten(steps) { return steps.flatMap(step => [step, ...flatten(step.steps ?? [])]); }

test('every source step appears exactly once, unchanged, with valid structural edges', () => {
  assert.ok(files.length > 0);
  for (const file of files) {
    const pkg = read(path.join(source,file));
    const diagram = buildDiagram(pkg);
    assert.deepEqual(diagram.nodes.map(n => n.step), flatten(pkg.runbook.steps), file);
    const ids = new Set(diagram.nodes.map(n => n.id));
    assert.equal(ids.size, diagram.nodes.length);
    for (const edge of diagram.edges) {
      assert.ok(ids.has(edge.source)); assert.ok(ids.has(edge.target));
    }
    for (const node of layoutDiagram(diagram).nodes) {
      assert.ok(Number.isFinite(node.x) && Number.isFinite(node.y));
    }
  }
});

test('catalog, bundled files, and generated previews match all source examples', () => {
  const catalog = read(path.join(here,'examples.json'));
  assert.deepEqual(catalog.map(e => path.basename(e.file)),files);
  assert.deepEqual(fs.readdirSync(path.join(here,'examples')).filter(f => f.endsWith('.json')).sort(),files);
  for (const entry of catalog) {
    const sourcePkg = read(path.join(source,path.basename(entry.file)));
    assert.equal(entry.title,sourcePkg.content.title);
    assert.deepEqual(read(path.join(here,entry.file)),sourcePkg);
    const svg = fs.readFileSync(path.join(here,'previews',path.basename(entry.file,'.json')+'.svg'),'utf8');
    for (const step of flatten(sourcePkg.runbook.steps)) assert.ok(svg.includes(`>${step.id}</text>`));
  }
});

test('arbitrary operations, renamed steps, settings, and reordered sequences come only from JSON', () => {
  const steps = [{id:'zebra',op:'unrecognized@99',custom:{mode:'new'},afterMs:17}, {id:'apple',op:'another@2'}];
  const pkg = {...base,runbook:{steps}};
  const original = JSON.stringify(pkg);
  const diagram = buildDiagram(pkg);
  assert.deepEqual(diagram.nodes.map(n => n.title),['zebra','apple']);
  assert.equal(diagram.nodes[0].subtitle,'unrecognized@99');
  assert.deepEqual(diagram.nodes[0].properties,[['custom',{mode:'new'}],['afterMs',17]]);
  assert.deepEqual(diagram.edges.map(e => [e.source,e.target,e.label]),[['zebra','apple','next']]);
  assert.equal(JSON.stringify(pkg),original);
  assert.deepEqual(buildDiagram({...pkg,runbook:{steps:[...steps].reverse()}}).edges.map(e => [e.source,e.target]),[['apple','zebra']]);
});

test('nested arrays are rendered as bodies without expanding iterations or inventing terminal nodes', () => {
  const diagram = buildDiagram({...base,runbook:{steps:[
    {id:'outer',op:'arbitrary@1',steps:[{id:'inner',op:'other@1'},{id:'second',op:'other@1'}]},
    {id:'after',op:'final@1'}]}});
  assert.deepEqual(diagram.nodes.map(n => [n.id,n.depth,n.pointer]),[
    ['outer',0,'/runbook/steps/0'],['inner',1,'/runbook/steps/0/steps/0'],
    ['second',1,'/runbook/steps/0/steps/1'],['after',0,'/runbook/steps/1']]);
  assert.deepEqual(diagram.edges.map(e => [e.source,e.target,e.label]),[
    ['outer','inner','steps'],['inner','second','next'],['outer','after','next']]);
  const layout = layoutDiagram(diagram);
  assert.ok(layout.nodes[1].x > layout.nodes[0].x);
  assert.equal(layout.nodes[3].x,layout.nodes[0].x);
});

test('malformed structure fails without falling back to an activity template', () => {
  assert.throws(() => buildDiagram({...base,format:'harmonomicon.activity-package/0.12'}),/supports/);
  assert.throws(() => buildDiagram(base),/nonempty step array/);
  assert.throws(() => buildDiagram({...base,runbook:{steps:[{id:'x'}]}}),/id and op/);
  assert.throws(() => buildDiagram({...base,runbook:{steps:[{id:'x',op:'a'},{id:'x',op:'b'}]}}),/Duplicate/);
  assert.throws(() => buildDiagram({...base,runbook:{steps:[{id:'x',op:'a',steps:[]}]}}),/nonempty/);
});
