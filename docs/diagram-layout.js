import {stepLines, containerLabel} from './step-labels.js';
export const NODE_FONT_SIZE = 18;
export const EDGE_FONT_SIZE = 14;
export const NODE_HEIGHT = 56;
export function titleCase(value) { return value.replaceAll('_',' ').replace(/\b\w/g, letter => letter.toUpperCase()); }
export function edgeLabelWidth(label) { return Math.ceil(label.length * 7.2); }
function wrap(text, limit = 42) {
  const lines = [];
  let line = '';
  for (const word of text.split(/\s+/)) {
    if (line && (line+' '+word).length > limit) { lines.push(line); line = ''; }
    line += (line ? ' ' : '') + word;
  }
  lines.push(line); return lines;
}
export function layoutDiagram(diagram) {
  const placed = new Map();
  function sequence(parent, left, top) {
    let y = top, width = 0;
    const children = diagram.nodes.filter(n => n.parent === parent);
    for (const node of children) {
      const container = Object.hasOwn(node.step, 'steps');
      const displayTitle = titleCase(node.title);
      const lines = (container ? [containerLabel(node.step)] : stepLines(node.step).slice(1)).flatMap(text => wrap(text));
      let w = Math.max(180, displayTitle.length*10 + node.subtitle.length*8 + 64, ...[displayTitle,...lines].map(line => line.length * 8 + 40));
      let h = 44 + lines.length * 21 + 16;
      const headerHeight = h;
      if (container) {
        const body = sequence(node.id, left + 20, y + headerHeight);
        w = Math.max(w, body.width + 40); h += body.height + 20;
      }
      placed.set(node.id,{...node,displayTitle,container,lines,headerHeight,x:left+w/2,y:y+h/2,width:w,height:h});
      width = Math.max(width,w); y += h + 48;
    }
    // Center siblings in their sequence, moving enclosed descendants with them.
    for (const node of children) {
      const box = placed.get(node.id), shift = (width-box.width)/2;
      box.x += shift;
      for (const candidate of placed.values()) {
        if (candidate.pointer.startsWith(node.pointer+'/steps/')) candidate.x += shift;
      }
    }
    return {width,height:y-top-48};
  }
  const size = sequence(null,20,20);
  return {nodes:diagram.nodes.map(n => placed.get(n.id)),edges:diagram.edges.filter(e => e.kind === 'sequence'),width:size.width+40,height:size.height+40};
}
