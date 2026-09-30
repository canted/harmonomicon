/** Summaries of reusable operation settings, never activity-specific templates. */
export function stepLines(step) {
  const lines = [step.op];
  if (step.prompt) lines.push(`“${step.prompt}”`);
  if (step.actors) lines.push(`Actors: ${{participants:'participants',turn:'current participant',others:'other participants'}[step.actors] ?? step.actors}`);
  for (const [name,field] of Object.entries(step.fields ?? {})) {
    let value = field.type;
    if (field.options) {
      const label = name === field.type ? name : `${name} (${field.type})`;
      lines.push(`${label}: ${field.options.join(' · ')} · ${field.visibility}`);
      continue;
    }
    if (field.count !== undefined) value += ` (${field.count} items)`;
    if (field.indexOf) value += ` → ${field.indexOf}`;
    lines.push(`${name}: ${value} · ${field.visibility}`);
  }
  if (step.sources) lines.push(`Sources: ${step.sources.join(', ')}`);
  if (step.source) lines.push(`Source: ${step.source}${step.field ? '.'+step.field : ''}`);
  if (step.policy) lines.push(`Policy: ${step.policy}`);
  if (step.perActor !== undefined) lines.push(`Items per participant: ${step.perActor}`);
  const ends = [];
  if (step.close) ends.push(({all:'all eligible submissions',organizer:'organizer advances',turn:'current participant advances',deadline:'deadline'})[step.close] ?? step.close);
  if (step.op === 'append@1') { lines.push('Actor: current participant'); ends.push('text submitted'); }
  if (typeof step.afterMs === 'number') {
    const seconds = step.afterMs / 1000;
    ends.push(seconds % 60 === 0 ? `${seconds/60} min passes` : `${seconds} sec passes`);
  }
  if (ends.length) lines.push(`Closes: ${ends.join(' OR ')}`);
  if (step.afterMs === null) lines.push('No timeout');
  return lines;
}
export function containerLabel(step) {
  if (step.op === 'for_each@1') return `Repeat for each ${step.over === 'participants' ? 'participant' : step.over} · roster order`;
  if (step.op === 'for_items@1') return `Repeat for each item from ${step.source}`;
  return `Nested steps · ${step.op}`;
}
