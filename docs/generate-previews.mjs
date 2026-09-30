/** Static SVG snapshots from the same package-to-diagram model used by the viewer. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildDiagram} from './model.js';
import {palette, diagramFill} from './palette.js';
import {layoutDiagram, NODE_FONT_SIZE, EDGE_FONT_SIZE} from './diagram-layout.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const output = path.join(here, 'previews');
fs.mkdirSync(output, {recursive:true});
const escape = value => String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&apos;');

function render(diagram) {
  const layout = layoutDiagram(diagram);
  const offsetY = 100;
  const width = layout.width;
  const height = layout.height + 125;
  const byId = new Map(layout.nodes.map(node => [node.id,node]));
  const edges = diagram.edges.map(edge => {
    const from = byId.get(edge.source), to = byId.get(edge.target);
    const sx = from.x + from.width/2, sy = from.y + offsetY;
    const tx = to.x - to.width/2 - 5, ty = to.y + offsetY;
    const bend = Math.min(30,(tx-sx)/3);
    const d = `M ${sx} ${sy} C ${sx+bend} ${sy}, ${tx-bend} ${ty}, ${tx} ${ty}`;
    const lines = edge.label.split(' · ');
    const branch = from.row !== to.row;
    const lx = (sx+tx)/2 + (branch ? 70 : 0);
    const ly = branch ? sy+50 : sy-20-(lines.length-1)*8;
    const label = lines.map((line,index) => `<text x="${lx}" y="${ly+index*17}" text-anchor="middle" fill="#000000" font-size="${EDGE_FONT_SIZE}" font-family="Arial,sans-serif">${escape(line)}</text>`).join('');
    return `<path d="${d}" fill="none" stroke="#000000" stroke-width="2" marker-end="url(#arrow)"/>${label}`;
  }).join('');
  const nodes = layout.nodes.map(node => {
    const x = node.x-node.width/2, y = node.y+offsetY-node.height/2;
    return `<rect x="${x}" y="${y}" width="${node.width}" height="${node.height}" rx="8" fill="${diagramFill(node)}"/><text x="${node.x}" y="${node.y+offsetY+7}" text-anchor="middle" fill="#000000" font-family="Arial,sans-serif" font-size="${NODE_FONT_SIZE}" font-weight="700">${escape(node.title)}</text>`;
  }).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${escape(diagram.title)} package flow" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7" fill="#000000"/></marker></defs>
<rect width="100%" height="100%" fill="${palette.white}"/><text x="20" y="38" fill="#000000" font-family="Arial,sans-serif" font-size="28" font-weight="700">${escape(diagram.title)}</text><text x="20" y="66" fill="#000000" font-family="monospace" font-size="16">behavior: ${escape(diagram.contract)}</text>
${edges}${nodes}<text x="20" y="${height-16}" fill="#000000" font-family="Arial,sans-serif" font-size="13">Package blueprint · instance details supplied at start</text></svg>\n`;
}
for (const [name,target] of [['group-check-in','check-in.svg'],['image-caption-vote','caption-contest.svg']]) {
  const pkg = JSON.parse(fs.readFileSync(path.join(here,'examples',`${name}.json`),'utf8'));
  fs.writeFileSync(path.join(output,target),render(buildDiagram(pkg)));
  console.log(target);
}
