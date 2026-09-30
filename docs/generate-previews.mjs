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
function wrapTitle(title) {
  const lines = [''];
  for (const word of title.split(' ')) {
    const last = lines.length-1;
    if ((lines[last]+' '+word).trim().length > 22 && lines[last]) lines.push(word);
    else lines[last] = (lines[last]+' '+word).trim();
  }
  return lines;
}
function render(diagram) {
  const layout = layoutDiagram(diagram);
  const titleLines = wrapTitle(diagram.title);
  const metadata = `${diagram.format}`;
  const metadataY = titleLines.length > 1 ? 92 : 64;
  const offsetY = metadataY + 32;
  const width = Math.ceil(Math.max(layout.width, 40+Math.max(...titleLines.map(line => line.length*15)), 40+metadata.length*9));
  const offsetX = (width-layout.width)/2;
  const height = offsetY + layout.height + 20;
  const byId = new Map(layout.nodes.map(node => [node.id,node]));
  const edges = diagram.edges.map(edge => {
    const from = byId.get(edge.source), to = byId.get(edge.target);
    const branch = edge.kind === 'nested';
    let d, lx, ly, anchor, lines;
    if (branch) {
      const sx = from.x+from.width/2+offsetX, sy = from.y+offsetY;
      const tx = to.x-to.width/2+offsetX-5, ty = to.y+offsetY;
      d = `M ${sx} ${sy} L ${tx} ${ty}`;
      lines = edge.label.split(' · ');
      lx = (sx+tx)/2; ly = sy-(lines.length > 1 ? 23 : 14); anchor = 'middle';
    } else {
      const sx = from.x+offsetX, sy = from.y+from.height/2+offsetY;
      const tx = to.x+offsetX, ty = to.y-to.height/2+offsetY-5;
      d = to.column > from.column + 1
        ? `M ${sx-from.width/2} ${from.y+offsetY} H ${sx-from.width/2-15} V ${to.y+offsetY} H ${tx-to.width/2-5}`
        : `M ${sx} ${sy} L ${tx} ${ty}`;
      lines = [edge.label];
      lx = sx+24; ly = (sy+ty)/2+5; anchor = 'start';
    }
    const label = lines.map((line,index) => `<text x="${lx}" y="${ly+index*16}" text-anchor="${anchor}" fill="#000000" font-size="${EDGE_FONT_SIZE}" font-family="Arial,sans-serif">${escape(line)}</text>`).join('');
    return `<path d="${d}" fill="none" stroke="#000000" stroke-width="2" marker-end="url(#arrow)"/>${label}`;
  }).join('');
  const nodes = layout.nodes.map(node => {
    const x = node.x-node.width/2+offsetX, y = node.y+offsetY-node.height/2;
    return `<rect x="${x}" y="${y}" width="${node.width}" height="${node.height}" rx="8" fill="${diagramFill(node)}"/><text x="${node.x+offsetX}" y="${node.y+offsetY+5}" text-anchor="middle" fill="#000000" font-family="Arial,sans-serif" font-size="${NODE_FONT_SIZE}" font-weight="700">${escape(node.title)}</text>`;
  }).join('');
  const title = titleLines.map((line,index) => `<text x="20" y="${38+index*28}" fill="#000000" font-family="Arial,sans-serif" font-size="28" font-weight="700">${escape(line)}</text>`).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${escape(diagram.title)} package flow" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7" fill="#000000"/></marker></defs>
<rect width="100%" height="100%" fill="${palette.white}"/>${title}<text x="20" y="${metadataY}" fill="#000000" font-family="monospace" font-size="16">${escape(metadata)}</text>
${edges}${nodes}</svg>\n`;
}
const catalog = JSON.parse(fs.readFileSync(path.join(here,'examples.json'),'utf8'));
const targets = new Set(catalog.map(entry => path.basename(entry.file, '.json') + '.svg'));
for (const file of fs.readdirSync(output)) {
  if (file.endsWith('.svg') && !targets.has(file)) fs.unlinkSync(path.join(output,file));
}
for (const entry of catalog) {
  const pkg = JSON.parse(fs.readFileSync(path.join(here,entry.file),'utf8'));
  const target = path.basename(entry.file,'.json') + '.svg';
  fs.writeFileSync(path.join(output,target),render(buildDiagram(pkg)));
  console.log(target);
}
