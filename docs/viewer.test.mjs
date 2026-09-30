import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildDiagram,CONTRACTS} from './model.js';
const here=path.dirname(fileURLToPath(import.meta.url));
const source=path.join(here,'../format/0.12/examples');
const read=file=>JSON.parse(fs.readFileSync(file,'utf8'));

test('every 0.12 example has a connected diagram with known nodes',()=>{
  const files=fs.readdirSync(source).filter(name=>name.endsWith('.json'));
  assert.ok(files.length > 0);
  const observed=new Set();
  for(const file of files){
    const diagram=buildDiagram(read(path.join(source,file)));
    observed.add(diagram.contract);
    assert.ok(diagram.nodes.length>=2,file);
    assert.ok(diagram.edges.length>=1,file);
    const ids=new Set(diagram.nodes.map(node=>node.id));
    assert.equal(ids.size,diagram.nodes.length,file);
    for(const edge of diagram.edges){assert.ok(ids.has(edge.source),file);assert.ok(ids.has(edge.target),file);}
  }
  assert.deepEqual([...observed].sort(),[...CONTRACTS].sort());
});

test('copied samples match the normative examples',()=>{
  for(const name of ['group-check-in','image-caption-vote']){
    assert.deepEqual(read(path.join(here,'examples',`${name}.json`)),read(path.join(source,`${name}.json`)));
  }
});

test('check-in shows private collection and deadline reveal',()=>{
  const diagram=buildDiagram(read(path.join(source,'group-check-in.json')));
  assert.deepEqual(diagram.nodes.map(n=>n.id),['waiting','open','closed']);
  assert.deepEqual(diagram.edges.map(e=>e.label),['opensAt','closesAt']);
  assert.match(diagram.nodes[1].view.join(' '),/own entry only/);
  assert.match(diagram.nodes[2].view.join(' '),/ordered entries/);
});

test('caption contest shows saved offers, voting, and insufficient-source branch',()=>{
  const diagram=buildDiagram(read(path.join(source,'image-caption-vote.json')));
  assert.ok(diagram.nodes.some(n=>n.id==='insufficient'));
  assert.ok(diagram.nodes.some(n=>n.id==='voting'));
  assert.ok(diagram.edges.some(e=>e.target==='insufficient' && e.label.includes('<3')));
  assert.match(diagram.nodes.find(n=>n.id==='responses').events.join(' '),/request_offer/);
  assert.match(diagram.nodes.find(n=>n.id==='complete').view.join(' '),/tied/);
});

test('unknown behavior and wrong format do not receive an inferred diagram',()=>{
  const original=read(path.join(source,'group-check-in.json'));
  assert.throws(()=>buildDiagram({...original,behavior:{contract:'imagined@1'}}),/Unsupported behavior/);
  assert.throws(()=>buildDiagram({...original,format:'harmonomicon.activity-package/2.0'}),/supports/);
});
