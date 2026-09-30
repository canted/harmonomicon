import {buildDiagram} from './model.js';

const $ = id => document.getElementById(id);
const examples = {
  'group-check-in':'examples/group-check-in.json',
  'image-caption-vote':'examples/image-caption-vote.json'
};
let current = null;
let graph = null;

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
  setText('inspector-description',stage.description || 'Select another stage to compare what changes.');
  const panel = $('inspector-sections'); panel.replaceChildren();
  addDetail(panel,'Instance setup',stage.setup);
  addDetail(panel,'Allowed events',stage.events);
  addDetail(panel,'Audience view',stage.view);
  addDetail(panel,'Rules and boundaries',stage.rules);
  for (const button of $('stage-buttons').querySelectorAll('button')) {
    button.setAttribute('aria-pressed',String(button.dataset.stage === id));
  }
  if (graph) {
    graph.nodes().removeClass('selected');
    const node = graph.getElementById(id);
    node.addClass('selected');
    if (focus) graph.animate({center:{eles:node},duration:200});
  }
}
function renderGraph(diagram) {
  if (graph) { graph.destroy(); graph = null; }
  const fallback = $('graph-fallback');
  if (typeof window.cytoscape !== 'function') {
    fallback.hidden = false;
    $('diagram').setAttribute('aria-label','Graph unavailable; use the stage list below');
    return;
  }
  fallback.hidden = true;
  const elements = [
    ...diagram.nodes.map(n => ({data:{id:n.id,label:n.title,subtitle:n.subtitle,kind:n.id==='insufficient'||n.id==='stalled'?'branch':n.id==='complete'||n.id==='closed'?'terminal':'phase'},position:{x:125+n.column*245,y:155+n.row*155}})),
    ...diagram.edges.map(e => ({data:{id:e.id,source:e.source,target:e.target,label:e.label}}))
  ];
  graph = window.cytoscape({
    container:$('diagram'), elements, layout:{name:'preset',fit:true,padding:40},
    minZoom:0.25,maxZoom:2.5,
    style:[
      {selector:'node',style:{'shape':'round-rectangle','width':180,'height':72,'background-color':'#edf4ff','border-width':2,'border-color':'#285bd2','label':'data(label)','color':'#172238','font-size':13,'font-weight':'bold','font-family':'Arial, sans-serif','text-wrap':'wrap','text-max-width':158,'text-valign':'center','text-halign':'center','padding':'8px'}},
      {selector:'node[kind="terminal"]',style:{'background-color':'#f5f0ff','border-color':'#6842b9'}},
      {selector:'node[kind="branch"]',style:{'background-color':'#fff3e8','border-color':'#ad6e41'}},
      {selector:'node.selected',style:{'border-width':5,'border-color':'#172238'}},
      {selector:'edge',style:{'curve-style':'bezier','width':2,'line-color':'#8798b7','target-arrow-shape':'triangle','target-arrow-color':'#8798b7','arrow-scale':1.1,'label':'data(label)','font-size':10,'font-family':'Arial, sans-serif','color':'#48556d','text-rotation':'autorotate','text-background-color':'#ffffff','text-background-opacity':1,'text-background-padding':3,'text-margin-y':-8}},
    ]
  });
  graph.on('tap','node',event => selectStage(event.target.id()));
  graph.ready(() => graph.fit(undefined,40));
}
function render(diagram) {
  current = diagram;
  setText('package-title',diagram.title);
  setText('package-summary',diagram.summary);
  setText('package-contract',diagram.contract);
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
  setText('layer-participants',`${diagram.participants.min}–${diagram.participants.max} participants; organizer separate`);
  setText('layer-setup',unique(diagram.nodes.flatMap(n=>n.setup)).join(' · ') || 'Actor bindings and contract setup at creation');
  setText('layer-events',unique(diagram.nodes.flatMap(n=>n.events)).join(' · ') || 'See the selected stage');
  setText('layer-views','Each actor receives the contract’s audience-filtered view; select a stage for details.');
  setText('layer-requires',diagram.requires.join(' · '));
  renderGraph(diagram);
  selectStage(diagram.nodes[0].id, false);
}
function openPackage(pkg,label) {
  try {
    const diagram = buildDiagram(pkg);
    render(diagram);
    setStatus(`${label} loaded. The viewer summarizes known 0.12 rules; it is not a package conformance validator.`);
  } catch (error) {
    setStatus(error instanceof Error ? error.message : 'Could not read this package.',true);
  }
}
async function loadExample(key) {
  try {
    setStatus('Loading example…');
    const response = await fetch(examples[key]);
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
$('fit-button').addEventListener('click',()=>graph?.fit(undefined,40));
$('png-button').addEventListener('click',()=>{
  if (!graph) { setStatus('The graph library is unavailable; PNG export is disabled.',true); return; }
  const anchor=document.createElement('a');
  anchor.href=graph.png({full:true,scale:2,bg:'#ffffff'});
  anchor.download=`${current?.id?.split('.').pop() || 'activity'}-diagram.png`;
  anchor.click();
});
loadExample('group-check-in');
