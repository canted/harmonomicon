import {buildDiagram} from './model.js';
import {diagramFill} from './palette.js';
import {layoutDiagram, edgeLabelWidth, NODE_FONT_SIZE, EDGE_FONT_SIZE} from './diagram-layout.js';

const $ = id => document.getElementById(id);
let current = null;
let graph = null;
let graphOriginX = 0;

function setStatus(message, error = false) {
  $('status').textContent = message;
  $('status').classList.toggle('error', error);
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
  setText('inspector-title',stage.title);
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
  if (graph) {
    graph.nodes().removeClass('selected');
    const node = graph.getElementById(id);
    node.addClass('selected');
    if (focus) {
      const viewport = $('diagram-scroll');
      viewport.scrollTo({left:Math.max(0,node.renderedPosition().x-viewport.clientWidth/2),top:Math.max(0,node.renderedPosition().y-viewport.clientHeight/2),behavior:'smooth'});
    }
  }
}
function renderGraph(diagram) {
  if (graph) { graph.destroy(); graph = null; }
  const fallback = $('graph-fallback');
  if (typeof window.cytoscape !== 'function') {
    fallback.hidden = false;
    $('diagram').setAttribute('aria-label','Graph unavailable; use the step list below');
    return;
  }
  fallback.hidden = true;
  const layout = layoutDiagram(diagram);
  $('diagram').style.width = `${Math.max($('diagram-scroll').clientWidth, layout.width)}px`;
  $('diagram').style.height = `${layout.height}px`;
  graphOriginX = Math.max(0, ($('diagram-scroll').clientWidth - layout.width) / 2);
  $('diagram-scroll').scrollTo({left:0,top:0});
  const elements = [
    ...layout.nodes.map(node => ({data:{id:node.id,label:node.title,fill:diagramFill(node),width:node.width,height:node.height},position:{x:node.x,y:node.y}})),
    ...diagram.edges.map(edge => ({data:{id:edge.id,source:edge.source,target:edge.target,label:edge.label,kind:edge.kind === 'nested' ? 'branch' : 'main',labelOffsetX:24+edgeLabelWidth(edge.label)/2}}))
  ];
  graph = window.cytoscape({
    container:$('diagram'), elements, layout:{name:'preset',fit:false},
    minZoom:1,maxZoom:2.5,userPanningEnabled:false,userZoomingEnabled:false,
    style:[
      {selector:'node',style:{'shape':'round-rectangle','width':'data(width)','height':'data(height)','background-color':'data(fill)','border-width':0,'label':'data(label)','color':'#000000','font-size':NODE_FONT_SIZE,'font-weight':'bold','font-family':'Arial, sans-serif','text-wrap':'none','text-valign':'center','text-halign':'center','padding':'0px'}},
      {selector:'edge',style:{'curve-style':'bezier','width':2,'line-color':'#000000','target-arrow-shape':'triangle','target-arrow-color':'#000000','arrow-scale':1,'label':'data(label)','font-size':EDGE_FONT_SIZE,'font-family':'Arial, sans-serif','color':'#000000','text-rotation':'none','text-background-color':'#ffffff','text-background-opacity':1,'text-background-padding':2,'text-margin-x':'data(labelOffsetX)'}},
      {selector:'edge[kind="branch"]',style:{'text-margin-x':0,'text-margin-y':-18}},
    ]
  });
  graph.on('tap','node',event => selectStage(event.target.id()));
  graph.ready(() => { graph.zoom(1); graph.pan({x:graphOriginX,y:0}); $('diagram-scroll').scrollTo({left:0,top:0}); });
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
    button.textContent = stage.title;
    button.addEventListener('click',() => selectStage(stage.id));
    buttons.append(button);
  }
  setText('layer-prompt',diagram.prompt);
  setText('layer-participants',`${diagram.participants.min}–${diagram.participants.max} participants`);
  setText('layer-setup',diagram.content.setup ?? 'Not declared');
  setText('layer-events',unique(diagram.nodes.map(n=>n.subtitle)).join(' · '));
  setText('layer-views',diagram.content.access ?? 'Not declared');
  setText('layer-requires',diagram.requires.join(' · '));
  renderGraph(diagram);
  selectStage(diagram.nodes[0].id, false);
}
function openPackage(pkg,label) {
  try {
    const diagram = buildDiagram(pkg);
    render(diagram);
    setStatus(`${label} loaded. The diagram shows declared runbook structure; it does not execute or validate operation rules.`);
  } catch (error) {
    setStatus(error instanceof Error ? error.message : 'Could not read this package.',true);
  }
}
async function loadExample(file) {
  try {
    setStatus('Loading example…');
    const response = await fetch(file);
    if (!response.ok) throw new Error(`Example could not be loaded (${response.status}).`);
    openPackage(await response.json(),'Example');
  } catch (error) {
    setStatus('Example could not be loaded. Serve the docs folder over HTTP, or open a local JSON file.',true);
  }
}
$('example-select').addEventListener('change',event=>loadExample(event.target.value));
$('file-input').addEventListener('change',async event=>{
  const file=event.target.files?.[0];
  if (!file) return;
  if (file.size>1_500_000) { setStatus('This file is too large for the viewer.',true); return; }
  try { openPackage(JSON.parse(await file.text()),file.name); }
  catch { setStatus('The selected file is not valid JSON.',true); }
});
$('fit-button').addEventListener('click',()=>{ graph?.zoom(1); graph?.pan({x:graphOriginX,y:0}); $('diagram-scroll').scrollTo({left:0,top:0}); });
$('png-button').addEventListener('click',()=>{
  if (!graph) { setStatus('The graph library is unavailable; PNG export is disabled.',true); return; }
  const anchor=document.createElement('a');
  anchor.href=graph.png({full:true,scale:2,bg:'#ffffff'});
  anchor.download=`${current?.id?.split('.').pop() || 'activity'}-diagram.png`;
  anchor.click();
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
