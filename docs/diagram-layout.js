/** Compact top-to-bottom geometry shared by the inspector and README previews. */
export const NODE_FONT_SIZE = 21;
export const EDGE_FONT_SIZE = 14;
export const NODE_HEIGHT = 61;

function nodeWidth(title) {
  // Arial bold at 21px averages about 10.5px per character for these labels.
  return Math.max(90, Math.ceil(title.length * 10.5 + 40));
}

export function edgeLabelWidth(label) {
  return Math.ceil(label.length * 7.2);
}

export function layoutDiagram(diagram) {
  const main = diagram.nodes.filter(node => node.row === 0).sort((a,b) => a.column - b.column);
  const branches = diagram.nodes.filter(node => node.row !== 0);
  const mainWidth = Math.max(...main.map(node => nodeWidth(node.title)));
  const mainX = 20 + mainWidth / 2;
  const placed = new Map();
  main.forEach((node,index) => {
    placed.set(node.id,{...node,x:mainX,y:20+NODE_HEIGHT/2+index*(NODE_HEIGHT+70),width:nodeWidth(node.title),height:NODE_HEIGHT});
  });
  const byId = new Map(diagram.nodes.map(node => [node.id,node]));
  const branchEdges = diagram.edges.filter(edge => byId.get(edge.target)?.row !== 0);
  const branchGap = branchEdges.length ? Math.max(90,...branchEdges.map(edge => Math.max(...edge.label.split(' · ').map(part => edgeLabelWidth(part)))+28)) : 0;
  const branchX = 20 + mainWidth + branchGap + Math.max(0,...branches.map(node => nodeWidth(node.title))) / 2;
  const siblingCount = new Map();
  for (const node of branches) {
    const sourceId = branchEdges.find(edge => edge.target === node.id)?.source;
    const source = placed.get(sourceId);
    const siblingIndex = siblingCount.get(sourceId) || 0;
    siblingCount.set(sourceId,siblingIndex+1);
    placed.set(node.id,{...node,x:branchX,y:(source?.y || 20+NODE_HEIGHT/2)+siblingIndex*(NODE_HEIGHT+15),width:nodeWidth(node.title),height:NODE_HEIGHT});
  }
  const nodes = diagram.nodes.map(node => placed.get(node.id));
  const mainLabelRight = Math.max(0,...diagram.edges.filter(edge => byId.get(edge.target)?.row === 0).map(edge => mainX+24+edgeLabelWidth(edge.label)));
  const nodeRight = Math.max(...nodes.map(node => node.x+node.width/2));
  const nodeBottom = Math.max(...nodes.map(node => node.y+node.height/2));
  return {nodes,width:Math.ceil(Math.max(mainLabelRight,nodeRight)+20),height:Math.ceil(nodeBottom+20)};
}
