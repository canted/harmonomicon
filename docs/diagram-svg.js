import {layoutDiagram, NODE_FONT_SIZE, EDGE_FONT_SIZE} from './diagram-layout.js';
import {diagramFill} from './palette.js';
const escape = value => String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&apos;');
/** Shared SVG rendering for the browser and repository previews. */
export function renderSvg(diagram, preview = false) {
  const layout = layoutDiagram(diagram);
  const offset = preview ? 94 : 0;
  const width = Math.max(layout.width, preview ? Math.max(440,diagram.title.length*14+40) : 0), height = layout.height + offset;
  const byId = new Map(layout.nodes.map(n => [n.id,n]));
  const nodeFill = node => node.container ? '#eef3fb' : diagramFill(node);
  const markers = layout.edges.map((edge,index) => `<marker id="arrow-${index}" markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" refX="0" refY="7" orient="auto"><path d="M0 0L14 7L0 14Z" fill="${nodeFill(byId.get(edge.source))}"/></marker>`).join('');
  const groups = layout.nodes.map(node => {
    const x = node.x-node.width/2, y = node.y-node.height/2+offset;
    const rect = `<rect x="${x}" y="${y}" width="${node.width}" height="${node.height}" rx="8" fill="${nodeFill(node)}"/>`;
    const title = `<text x="${x+20}" y="${y+29}" font-weight="700" font-size="${NODE_FONT_SIZE}">${escape(node.displayTitle)}</text>`;
    const operation = `<text x="${x+node.width-20}" y="${y+29}" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="13">${escape(node.subtitle)}</text>`;
    const text = node.lines.map((line,i) => `<text x="${x+20}" y="${y+52+i*21}" font-size="14">${escape(line)}</text>`).join('');
    return `<g data-step="${escape(node.id)}" tabindex="0" role="button" aria-label="${escape(node.title+' '+node.subtitle)}"><title>${escape(node.pointer)}</title>${rect}${title}${operation}${text}</g>`;
  }).join('');
  const edges = layout.edges.map((edge,index) => {
    const a=byId.get(edge.source), b=byId.get(edge.target);
    const x=a.x, y=a.y+a.height/2+offset, tx=b.x, ty=b.y-b.height/2+offset-19;
    return `<path d="M ${x} ${y} L ${tx} ${ty}" fill="none" stroke="${nodeFill(a)}" stroke-width="5" marker-end="url(#arrow-${index})"/><text x="${x+16}" y="${(y+ty)/2+5}" font-size="${EDGE_FONT_SIZE}">next</text>`;
  }).join('');
  const heading = preview ? `<text x="20" y="32" font-size="24" font-weight="700">${escape(diagram.title)}</text><text x="20" y="59" font-size="14">${escape(diagram.format)}</text>` : '';
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" aria-label="${escape(diagram.title)} runbook" style="font-family:Arial,sans-serif;fill:black"><defs>${markers}</defs><rect width="100%" height="100%" fill="white"/>${heading}${groups}${edges}</svg>`;
}
