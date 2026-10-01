import {buildDiagram} from './model.js';
import {renderSvg} from './diagram-svg.js';
import {layoutDiagram, titleCase} from './diagram-layout.js';

const $ = id => document.getElementById(id);
let current = null;
let graph = null;


function setStatus(message, error = false, announceOnly = false) {
  $('status').textContent = message;
  $('status').classList.toggle('error', error);
  $('status').classList.toggle('visually-hidden', announceOnly);
}
function unique(items) { return [...new Set(items.filter(Boolean))]; }
function setText(id, value) { $(id).textContent = value; }
function addDetail(parent, title, items) {
  if (!items || !items.length) return;
  const section = document.createElement('section');
  section.className = 'detail-section';
  const h = document.createElement('h4'); h.textContent = title;
  const list = document.createElement('ul');
  for (const item of items) {
    const li = document.createElement('li'); li.textContent = item;
    list.append(li);
  }
  section.append(h,list); parent.append(section);
}
function selectStage(id, focus = true) {
  if (!current) return;
  const stage = current.nodes.find(n => n.id === id);
  if (!stage) return;
  setText('inspector-title',titleCase(stage.title));
  setText('inspector-subtitle',stage.subtitle || '');
  setText('inspector-description',stage.description || 'This step has no prompt property.');
  const panel = $('inspector-sections'); panel.replaceChildren();
  addDetail(panel,'JSON location',[stage.pointer]);
  for (const [key,value] of stage.properties) addDetail(panel,key,[typeof value === 'string' ? value : JSON.stringify(value)]);
  const raw = document.createElement('pre'); raw.textContent = JSON.stringify(stage.step,null,2);
  panel.append(raw);
  for (const button of $('stage-buttons').querySelectorAll('button')) {
    button.setAttribute('aria-pressed',String(button.dataset.stage === id));
  }
  if (graph && focus) {
    const node = graph.nodes.find(n => n.id === id);
    $('diagram-scroll').scrollTo({top:Math.max(0,node.y-node.height/2-20),left:0,behavior:'smooth'});
  }
}
function renderGraph(diagram) {
  graph = layoutDiagram(diagram);
  $('diagram').innerHTML = renderSvg(diagram);
  $('diagram').style.width = `${graph.width}px`;
  $('diagram').style.height = `${graph.height}px`;
  $('diagram-scroll').scrollTo({left:0,top:0});
  $('graph-fallback').hidden = true;
  for (const group of $('diagram').querySelectorAll('[data-step]')) {
    group.addEventListener('click', event => { event.stopPropagation(); selectStage(group.dataset.step); });
    group.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); event.stopPropagation(); selectStage(group.dataset.step); }
    });
  }
}

function render(diagram) {
  current = diagram;
  setText('package-title',diagram.title);
  setText('package-summary',diagram.summary);
  setText('package-contract',diagram.format);
  setText('package-identity',`${diagram.id} · ${diagram.version}`);
  const buttons = $('stage-buttons'); buttons.replaceChildren();
  for (const stage of diagram.nodes) {
    const button = document.createElement('button');
    button.type = 'button'; button.dataset.stage = stage.id;
    button.textContent = titleCase(stage.title);
    button.addEventListener('click',() => selectStage(stage.id));
    buttons.append(button);
  }
  setText('layer-prompt',diagram.prompt);
  setText('layer-participants',`${diagram.participants.min}–${diagram.participants.max} participants`);
  setText('layer-setup',(diagram.content.setup ?? 'Not declared') + Object.entries(diagram.settings).map(([key,value]) => ` ${key}: ${value.type}${Object.hasOwn(value,'default') ? ' (default: '+value.default+')' : ' (required)'}`).join(';'));
  setText('layer-events',unique(diagram.nodes.map(n=>n.subtitle)).join(' · '));
  setText('layer-views',diagram.content.access ?? 'Not declared');
  setText('layer-requires',diagram.requires.join(' · '));
  renderGraph(diagram);
  selectStage(diagram.nodes[0].id, false);
}
function openPackage(pkg) {
  try {
    const diagram = buildDiagram(pkg);
    render(diagram);
    setStatus(`${diagram.title} loaded.`, false, true);
  } catch (error) {
    setStatus(error instanceof Error ? error.message : 'Could not read this package.',true);
  }
}
async function loadExample(file) {
  try {
    setStatus('Loading example…');
    const response = await fetch(file);
    if (!response.ok) throw new Error(`Example could not be loaded (${response.status}).`);
    openPackage(await response.json());
  } catch (error) {
    setStatus('Example could not be loaded. Serve the docs folder over HTTP, or open a local JSON file.',true);
  }
}
$('example-select').addEventListener('change',event=>loadExample(event.target.value));
$('open-file-button').addEventListener('click',()=> $('file-input').click());
$('file-input').addEventListener('change',async event=>{
  const file=event.target.files?.[0];
  if (!file) return;
  if (file.size>1_500_000) { setStatus('This file is too large for the viewer.',true); return; }
  try { openPackage(JSON.parse(await file.text())); }
  catch { setStatus('The selected file is not valid JSON.',true); }
});
$('fit-button').addEventListener('click',()=> $('diagram-scroll').scrollTo({left:0,top:0}));
$('png-button').addEventListener('click',async()=>{
  if (!current) return;
  const url = URL.createObjectURL(new Blob([renderSvg(current)],{type:'image/svg+xml'}));
  try {
    const img = new Image(); img.src = url; await img.decode();
    const canvas = document.createElement('canvas'); canvas.width=img.width*2; canvas.height=img.height*2;
    canvas.getContext('2d').drawImage(img,0,0,canvas.width,canvas.height);
    const anchor=document.createElement('a'); anchor.href=canvas.toDataURL('image/png');
    anchor.download=`${current.id.split('.').pop()}-diagram.png`; anchor.click();
  } catch { setStatus('Could not export this diagram as PNG.',true); }
  finally { URL.revokeObjectURL(url); }
});
async function loadCatalog() {
  try {
    const response = await fetch('examples.json');
    if (!response.ok) throw new Error('Could not load example catalog.');
    const catalog = await response.json();
    const select = $('example-select'); select.replaceChildren();
    for (const entry of catalog) {
      const option = document.createElement('option'); option.value = entry.file; option.textContent = entry.title;
      select.append(option);
    }
    if (catalog.length) await loadExample(catalog[0].file);
  } catch { setStatus('Could not load examples. You can still open a local package JSON file.',true); }
}
loadCatalog();
