/** Static SVG snapshots from the same package-to-diagram model used by the viewer. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildDiagram} from './model.js';
import {palette, tint} from './palette.js';

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
  const nodeW = 260, nodeH = 116, step = 390;
  const x = node => 80 + node.column * step;
  const y = node => 230 + node.row * 260;
  const maxCol = Math.max(...diagram.nodes.map(node => node.column));
  const hasBranch = diagram.nodes.some(node => node.row > 0);
  const width = x({column:maxCol}) + nodeW + 80;
  const height = hasBranch ? 690 : 440;
  const byId = new Map(diagram.nodes.map(node => [node.id,node]));
  const edges = diagram.edges.map(edge => {
    const from = byId.get(edge.source), to = byId.get(edge.target);
    const sx = x(from) + nodeW, sy = y(from) + nodeH/2;
    const tx = x(to) - 12, ty = y(to) + nodeH/2;
    const d = `M ${sx} ${sy} C ${sx+45} ${sy}, ${tx-45} ${ty}, ${tx} ${ty}`;
    const lines = edge.label.split(' · ');
    const lx = (sx+tx)/2;
    const ly = from.row === to.row ? sy-75-(lines.length-1)*12 : (sy+ty)/2-12;
    const label = lines.map((line,index) => `<text x="${lx}" y="${ly+index*24}" text-anchor="middle" fill="${palette.cyanDark}" font-size="20" font-family="Arial,sans-serif">${escape(line)}</text>`).join('');
    return `<path d="${d}" fill="none" stroke="${palette.cyan}" stroke-width="4" marker-end="url(#arrow)"/>${label}`;
  }).join('');
  const nodes = diagram.nodes.map(node => {
    const terminal = ['complete','closed'].includes(node.id);
    const branch = ['insufficient','stalled'].includes(node.id);
    const color = branch ? palette.pink : terminal ? palette.purple : palette.blue;
    const dark = branch ? palette.pinkDark : terminal ? palette.purpleDark : palette.blueDark;
    const lines = wrap(node.title);
    const top = y(node) + (lines.length === 1 ? 67 : 51);
    const label = lines.map((line,index) => `<text x="${x(node)+nodeW/2}" y="${top+index*30}" text-anchor="middle" fill="${dark}" font-family="Arial,sans-serif" font-size="26" font-weight="700">${escape(line)}</text>`).join('');
    return `<rect x="${x(node)}" y="${y(node)}" width="${nodeW}" height="${nodeH}" rx="12" fill="${tint(color)}" stroke="${color}" stroke-width="4"/>${label}`;
  }).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${escape(diagram.title)} package flow" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0 0L10 5L0 10" fill="${palette.cyan}"/></marker></defs>
<rect width="100%" height="100%" fill="${palette.white}"/><text x="80" y="72" fill="${palette.blueDark}" font-family="Arial,sans-serif" font-size="48" font-weight="700">${escape(diagram.title)}</text><text x="80" y="125" fill="${palette.purpleDark}" font-family="monospace" font-size="24">behavior: ${escape(diagram.contract)}</text>
${edges}${nodes}<text x="80" y="${height-35}" fill="${palette.cyanDark}" font-family="Arial,sans-serif" font-size="22">Package blueprint · times and participants are supplied when an instance starts</text></svg>\n`;
}
for (const [name,target] of [['group-check-in','check-in.svg'],['image-caption-vote','caption-contest.svg']]) {
  const pkg = JSON.parse(fs.readFileSync(path.join(here,'examples',`${name}.json`),'utf8'));
  fs.writeFileSync(path.join(output,target),render(buildDiagram(pkg)));
  console.log(target);
}
