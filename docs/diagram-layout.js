/** Compact vertical sequences; nested bodies are indented to the side. */
export const NODE_FONT_SIZE = 16;
export const EDGE_FONT_SIZE = 14;
export const NODE_HEIGHT = 56;
export function edgeLabelWidth(label) { return Math.ceil(label.length * 7.2); }
export function layoutDiagram(diagram) {
  const widthFor = title => Math.max(80, Math.ceil(title.length * 8 + 40));
  const mainWidth = Math.max(...diagram.nodes.map(node => widthFor(node.title)));
  const nodes = diagram.nodes.map((node, index) => ({...node,
    x:20 + mainWidth / 2 + node.depth * (mainWidth + 60),
    y:20 + NODE_HEIGHT / 2 + index * (NODE_HEIGHT + 60),
    width:widthFor(node.title), height:NODE_HEIGHT}));
  return {nodes, width:Math.ceil(Math.max(...nodes.map(n => n.x + n.width/2 + 80))),
    height:Math.ceil(Math.max(...nodes.map(n => n.y + n.height/2)) + 20)};
}
