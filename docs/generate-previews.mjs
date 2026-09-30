/** Static SVG snapshots from the same package-to-diagram model used by the viewer. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildDiagram} from './model.js';
import {palette, diagramFill} from './palette.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const output = path.join(here, 'previews');
fs.mkdirSync(output, {recursive:true});
const escape = value => String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&apos;');
function wrap(value, max = 18) {
  const lines = [''];
  for (const word of value.split(/\s+/)) {
    const last = lines.length - 1;
    if ((lines[last] + ' ' + word).trim().length > max && lines[last]) lines.push(word);
    else lines[last] = (lines[last] + ' ' + word).trim();
  }
  return lines.slice(0,2);
}
function render(diagram) {
  const nodeW = 260, nodeH = 105, step = 450;
  const x = node => 80 + node.column * step;
  const y = node => 145 + node.row * 220;
  const maxCol = Math.max(...diagram.nodes.map(node => node.column));
  const hasBranch = diagram.nodes.some(node => node.row > 0);
  const width = x({column:maxCol}) + nodeW + 80;
  const height = hasBranch ? 580 : 330;
  const byId = new Map(diagram.nodes.map(node => [node.id,node]));
  const edges = diagram.edges.map(edge => {
    const from = byId.get(edge.source), to = byId.get(edge.target);
    const sx = x(from) + nodeW, sy = y(from) + nodeH/2;
    const tx = x(to) - 10, ty = y(to) + nodeH/2;
    const d = `M ${sx} ${sy} C ${sx+50} ${sy}, ${tx-50} ${ty}, ${tx} ${ty}`;
    const lines = edge.label.split(' · ');
    const lx = (sx+tx)/2 + (from.row === to.row ? 0 : 100);
    const ly = from.row === to.row ? sy-65-(lines.length-1)*10 : sy+100;
    const label = lines.map((line,index) => `<text x="${lx}" y="${ly+index*22}" text-anchor="middle" fill="#000000" font-size="18" font-family="Arial,sans-serif">${escape(line)}</text>`).join('');
    return `<path d="${d}" fill="none" stroke="#000000" stroke-width="2" marker-end="url(#arrow)"/>${label}`;
  }).join('');
  const nodes = diagram.nodes.map(node => {
    const lines = wrap(node.title, 20);
    const top = y(node) + (lines.length === 1 ? 60 : 46);
    const label = lines.map((line,index) => `<text x="${x(node)+nodeW/2}" y="${top+index*26}" text-anchor="middle" fill="#000000" font-family="Arial,sans-serif" font-size="21" font-weight="700">${escape(line)}</text>`).join('');
    return `<rect x="${x(node)}" y="${y(node)}" width="${nodeW}" height="${nodeH}" rx="12" fill="${diagramFill(node)}"/>${label}`;
  }).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${escape(diagram.title)} package flow" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="11" refY="6" orient="auto"><path d="M0 0L12 6L0 12" fill="#000000"/></marker></defs>
<rect width="100%" height="100%" fill="${palette.white}"/><text x="80" y="55" fill="#000000" font-family="Arial,sans-serif" font-size="36" font-weight="700">${escape(diagram.title)}</text><text x="80" y="88" fill="#000000" font-family="monospace" font-size="18">behavior: ${escape(diagram.contract)}</text>
${edges}${nodes}<text x="80" y="${height-24}" fill="#000000" font-family="Arial,sans-serif" font-size="16">Package blueprint · times and participants are supplied when an instance starts</text></svg>\n`;
}
for (const [name,target] of [['group-check-in','check-in.svg'],['image-caption-vote','caption-contest.svg']]) {
  const pkg = JSON.parse(fs.readFileSync(path.join(here,'examples',`${name}.json`),'utf8'));
  fs.writeFileSync(path.join(output,target),render(buildDiagram(pkg)));
  console.log(target);
}
