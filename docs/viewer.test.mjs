import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildDiagram, FORMAT} from './model.js';
import {layoutDiagram, titleCase} from './diagram-layout.js';
import {stepLines, containerLabel} from './step-labels.js';
import {renderSvg} from './diagram-svg.js';
const here = path.dirname(fileURLToPath(import.meta.url));
const source = path.join(here,'../format/0.17/examples');
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
    for (const step of flatten(sourcePkg.runbook.steps)) assert.ok(svg.includes(`>${titleCase(step.id)}</text>`));
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
  const outer = layout.nodes[0];
  assert.equal(outer.container,true);
  for (const child of layout.nodes.slice(1,3)) {
    assert.ok(child.x-child.width/2 >= outer.x-outer.width/2+20);
    assert.ok(child.x+child.width/2 <= outer.x+outer.width/2-20);
    assert.ok(child.y-child.height/2 >= outer.y-outer.height/2+outer.headerHeight);
    assert.ok(child.y+child.height/2 <= outer.y+outer.height/2-20);
  }
  assert.ok(layout.nodes[3].y-layout.nodes[3].height/2 > outer.y+outer.height/2);
  assert.equal(layout.edges.some(e => e.kind === 'nested'),false);
});

test('malformed structure fails without falling back to an activity template', () => {
  assert.throws(() => buildDiagram({...base,format:'harmonomicon.activity-package/0.12'}),/supports/);
  assert.throws(() => buildDiagram(base),/nonempty step array/);
  assert.throws(() => buildDiagram({...base,runbook:{steps:[{id:'x'}]}}),/id and op/);
  assert.throws(() => buildDiagram({...base,runbook:{steps:[{id:'x',op:'a'},{id:'x',op:'b'}]}}),/Duplicate/);
  assert.throws(() => buildDiagram({...base,runbook:{steps:[{id:'x',op:'a',steps:[]}]}}),/nonempty/);
});

test('summaries expose declared options, privacy, prompts, actors and alternative close triggers', () => {
  const step = {id:'custom',op:'collect@1',prompt:'Choose something.',actors:'others',
    fields:{pick:{type:'choice',options:['One','Two'],visibility:'private'}},close:'organizer',afterMs:60000};
  const text = stepLines(step).join('\n');
  assert.match(text,/Choose something/); assert.match(text,/other participants/);
  assert.match(text,/One · Two/); assert.match(text,/private/);
  assert.match(text,/organizer advances OR 1 min passes/);
  assert.match(containerLabel({op:'for_each@1',over:'participants'}),/Repeat for each participant/);
  assert.match(containerLabel({op:'for_items@1',source:'my_pool'}),/item from my_pool/);
  const svg = renderSvg(buildDiagram({...base,runbook:{steps:[step]}}));
  assert.ok(svg.includes('One · Two')); assert.ok(svg.includes('Choose something.'));
});

test('shared renderer escapes package strings and never turns choices into flow branches', () => {
  const pkg = {...base,runbook:{steps:[{id:'answer',op:'collect@1',prompt:'<script>alert(1)</script>',
    fields:{choice:{type:'choice',options:['<one>','two'],visibility:'private'}}}]}};
  const diagram = buildDiagram(pkg);
  assert.equal(diagram.nodes.length,1); assert.equal(diagram.edges.length,0);
  const svg = renderSvg(diagram);
  assert.ok(svg.includes('&lt;script&gt;')); assert.ok(!svg.includes('<script>'));
});


test('black text on every diagram stage fill meets WCAG AA 4.5:1', async () => {
  const {diagramFill} = await import('./palette.js');
  for (let column=0;column<6;column++) {
    const hex = diagramFill({column});
    const rgb = hex.slice(1).match(/../g).map(channel => parseInt(channel,16)/255)
      .map(value => value<=0.04045 ? value/12.92 : ((value+0.055)/1.055)**2.4);
    const luminance = rgb[0]*0.2126 + rgb[1]*0.7152 + rgb[2]*0.0722;
    const ratio = (luminance+0.05)/0.05;
    assert.ok(ratio>=4.5, `${hex}: ${ratio.toFixed(2)}:1`);
  }
});


test('scheduled references and declared settings remain visible without invented instance values', () => {
  const pkg=read(path.join(source,'scheduled-check-in.json'));
  const diagram=buildDiagram(pkg);
  assert.deepEqual(diagram.settings,pkg.settings);
  assert.match(diagram.nodes[0].description,/instance setting: question/);
  const lines=stepLines(pkg.runbook.steps[1]).join('\n');
  assert.match(lines,/Closes at: instance setting closes_at/);
  const svg=renderSvg(diagram);
  assert.ok(svg.includes('instance setting opens_at'));
  assert.ok(svg.includes('instance setting closes_at'));
  assert.ok(!svg.includes('[object Object]'));
});


test('rating routes, numeric bounds, exact aggregation and cutoff settings come from package JSON', () => {
  const pkg=read(path.join(source,'crowd-scoring.json'));
  assert.match(stepLines(pkg.runbook.steps[1]).join('\n'),/Roster offset: 1/);
  assert.match(stepLines(pkg.runbook.steps[2]).join('\n'),/Rating: 1–5 · private/);
  assert.match(stepLines(pkg.runbook.steps[11]).join('\n'),/Scale mean to 5 ratings/);
  assert.match(stepLines(pkg.runbook.steps[12]).join('\n'),/including all cutoff ties/);
  assert.match(stepLines({op:'collect@1',fields:{value:{type:'integer',min:0,max:100,visibility:'private'}}}).join('\n'),/integer \(0–100\)/);
  const svg=renderSvg(buildDiagram(pkg));
  assert.ok(svg.includes('Rating: 1–5'));assert.ok(svg.includes('Roster offset: 5'));
});


test('recurring windows show declared schedule and status without expanding runtime occurrences', () => {
  const pkg=read(path.join(source,'daily-reveal.json'));
  const graph=buildDiagram(pkg);
  assert.equal(graph.nodes.length,3);
  assert.match(stepLines(pkg.runbook.steps[0]).join('\n'),/First opening: instance setting starts_at/);
  assert.match(stepLines(pkg.runbook.steps[0]).join('\n'),/3 windows · every 86400000 ms · open 72000000 ms/);
  assert.match(stepLines(pkg.runbook.steps[0].steps[0]).join('\n'),/completion status: group/);
  assert.ok(renderSvg(graph).includes('Repeat 3 fixed windows'));
});
