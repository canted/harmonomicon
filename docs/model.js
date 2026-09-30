/** Render declared JSON structure; no activity templates or runtime inference. */
export const FORMAT = 'harmonomicon.activity-package/0.14';
export function buildDiagram(pkg) {
  if (pkg?.format !== FORMAT) throw new Error(`This viewer supports ${FORMAT}.`);
  if (!pkg.content?.title || !pkg.id || !pkg.version || !pkg.participants || !Array.isArray(pkg.requires)) {
    throw new Error('Package needs identity, content.title, participants, and requires.');
  }
  const nodes = [], edges = [], ids = new Set();
  function sequence(steps, path, depth = 0, parent = null) {
    if (!Array.isArray(steps) || !steps.length) throw new Error(`${path} must be a nonempty step array.`);
    let previous = null;
    steps.forEach((step, index) => {
      const pointer = `${path}/${index}`;
      if (!step || typeof step.id !== 'string' || !step.id || typeof step.op !== 'string' || !step.op) {
        throw new Error(`${pointer} needs id and op strings.`);
      }
      if (ids.has(step.id)) throw new Error(`Duplicate step id: ${step.id}`);
      ids.add(step.id);
      nodes.push({id:step.id, title:step.id, subtitle:step.op, description:step.prompt ?? '',
        column:nodes.length, row:0, depth, parent, pointer, step,
        properties:Object.entries(step).filter(([key]) => !['id','op','steps'].includes(key))});
      if (previous) edges.push({id:`edge-${edges.length}`, source:previous, target:step.id, label:'next', kind:'sequence'});
      else if (parent) edges.push({id:`edge-${edges.length}`, source:parent, target:step.id, label:'steps', kind:'nested'});
      if (Object.hasOwn(step, 'steps')) sequence(step.steps, `${pointer}/steps`, depth + 1, step.id);
      previous = step.id;
    });
  }
  sequence(pkg.runbook?.steps, '/runbook/steps');
  return {title:pkg.content.title, summary:pkg.content.summary ?? '', id:pkg.id, version:pkg.version,
    format:pkg.format, participants:pkg.participants, requires:pkg.requires,
    content:pkg.content, prompt:pkg.content.prompt ?? '', nodes, edges};
}
