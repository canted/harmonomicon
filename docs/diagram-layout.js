/** Compact geometry shared by the interactive graph and README previews. */
export const NODE_FONT_SIZE = 21;
export const EDGE_FONT_SIZE = 14;
export const NODE_HEIGHT = 61;

function nodeWidth(title) {
  // Arial bold at 21px averages about 10.5px per character for these labels.
  return Math.max(90, Math.ceil(title.length * 10.5 + 40));
}

function edgeLabelWidth(label) {
  return Math.max(...label.split(' · ').map(part => part.length * 7.2));
}

export function layoutDiagram(diagram) {
  const maxColumn = Math.max(...diagram.nodes.map(node => node.column));
  const columnWidths = Array.from({length:maxColumn + 1}, () => 90);
  const gaps = Array.from({length:maxColumn}, () => 66);
  const byId = new Map(diagram.nodes.map(node => [node.id, node]));
  for (const node of diagram.nodes) {
    columnWidths[node.column] = Math.max(columnWidths[node.column], nodeWidth(node.title));
  }
  for (const edge of diagram.edges) {
    const source = byId.get(edge.source);
    const target = byId.get(edge.target);
    if (target.column === source.column + 1) {
      gaps[source.column] = Math.max(gaps[source.column], Math.ceil(edgeLabelWidth(edge.label) + 28));
    }
  }
  const centers = [];
  let cursor = 20;
  for (let column = 0; column <= maxColumn; column++) {
    centers[column] = cursor + columnWidths[column] / 2;
    cursor += columnWidths[column] + (gaps[column] || 0);
  }
  const nodes = diagram.nodes.map(node => ({
    ...node,
    x: centers[node.column],
    y: 53 + node.row * 115,
    width: nodeWidth(node.title),
    height: NODE_HEIGHT
  }));
  return {nodes, width:cursor + 20, height:diagram.nodes.some(node => node.row > 0) ? 220 : 106};
}
