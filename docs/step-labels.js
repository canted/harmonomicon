/** Summaries of reusable operation settings, never activity-specific templates. */
function inputLabel(value) {
  if (value === null) return 'none (null)';
  if (value?.binding) return `host binding: ${value.binding}`;
  if (value?.result) return `step result: ${value.result}`;
  return JSON.stringify(value);
}
export function stepLines(step) {
  const lines = [step.op];
  if (typeof step.prompt === 'string') lines.push(`“${step.prompt}”`);
  else if (step.prompt?.setting) lines.push(`Prompt from instance setting: ${step.prompt.setting}`);
  if (Object.hasOwn(step,'until')) lines.push(`${step.op === 'wait_until@1' ? 'Waits until' : 'Closes at'}: ${typeof step.until === 'object' ? 'instance setting '+step.until.setting : step.until+' Unix ms'}`);
  if (step.actors) lines.push(`Actors: ${{participants:'participants',turn:'current participant',others:'other participants'}[step.actors] ?? step.actors}`);
  for (const [name,field] of Object.entries(step.fields ?? {})) {
    let value = field.type;
    if (field.options) {
      const label = name === field.type ? name : `${name} (${field.type})`;
      lines.push(`${label}: ${field.options.join(' · ')} · ${field.visibility}`);
      continue;
    }
    if (field.type === 'integer') value += ` (${field.min}–${field.max})`;
    if (field.count !== undefined) value += ` (${field.count} items)`;
    if (field.indexOf) value += ` → ${field.indexOf}`;
    lines.push(`${name}: ${value} · ${field.visibility}`);
  }
  if (step.sources) lines.push(`Sources: ${step.sources.join(', ')}`);
  if (step.source) lines.push(`Source: ${step.source}${step.field ? '.'+step.field : ''}`);
  if (step.policy) lines.push(`Policy: ${step.policy}`);
  if (step.perActor !== undefined) lines.push(`Items per participant: ${step.perActor}`);
  if (step.round) lines.push(`Round: ${step.round}`);
  if (Object.hasOwn(step,'input')) lines.push(`Contribution input: ${inputLabel(step.input)}`);
  if (Object.hasOwn(step,'queueInput')) lines.push(`Invitation queue input: ${inputLabel(step.queueInput)}`);
  if (step.candidates?.source) lines.push(`Candidates from: ${step.candidates.source}`);
  if (step.candidates?.options) lines.push(`Candidate options: ${step.candidates.options.map(option => `${option.id}: ${option.label}`).join(' · ')}`);
  if (step.changes) lines.push(`Ballot changes: ${step.changes}`);
  if (step.ballots) lines.push(`Ballot visibility: ${step.ballots}`);
  if (step.ties) lines.push(`Ties: ${step.ties}`);
  if (step.noVotes) lines.push(`No votes: ${step.noVotes}`);
  if (step.audience) lines.push(`Audience: ${step.audience}`);
  if (step.op === 'first_valid@1') {
    lines.push(`Invitation window: ${step.windowMs} ms`);
    lines.push(`Failed-pass retry delay: ${step.retryAfterMs} ms`);
  }
  if (step.offset !== undefined) lines.push(`Roster offset: ${step.offset}`);
  if (step.op === 'rate@1') lines.push(`Rating: ${step.min}–${step.max} · private`);
  if (step.targetCount !== undefined && step.targetCount !== null) lines.push(`Scale mean to ${step.targetCount} ratings`);
  if (step.limit !== undefined) lines.push(`Publish ranks through ${step.limit}, including all cutoff ties`);
  if (step.op === 'for_windows@1') {
    lines.push(`First opening: ${typeof step.startsAt === 'object' ? 'instance setting '+step.startsAt.setting : step.startsAt+' Unix ms'}`);
    lines.push(`${step.occurrences} windows · every ${step.intervalMs} ms · open ${step.windowMs} ms`);
  }
  if (step.op === 'collect_window@1') lines.push(`Closes: fixed window deadline · completion status: ${step.completion}`);
  if (['assign_sources@1','assign_artifacts@1','assign_artifacts@2'].includes(step.op)) {
    lines.push(`Recipients: ${step.recipients} · self excluded`);
    lines.push(`Cardinality: ${step.cardinality} · source reuse: ${step.reuse} · unmatched: ${step.unmatched}`);
  }
  if (['respond@1','artifact_response@1','artifact_response@2'].includes(step.op)) lines.push('Independent responses · assigned source ID required');
  if (['reveal_responses@1','reveal_artifact_responses@1','reveal_artifact_responses@2'].includes(step.op)) lines.push('Publish accepted source-response pairs with attribution');
  if (step.kinds) lines.push(`Contribution kinds: ${step.kinds.join(' · ')}`);
  if (step.visibility) lines.push(`Visibility: ${step.visibility}`);
  if (['artifact_pool@1','artifact_pool@2','artifact_pool@3','artifact_response@1','artifact_response@2','pool@2','vote@1','vote@2','vote@3'].includes(step.op)) lines.push('Actors/dates: trusted host inputs · closes by date or host control');
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
  if (['for_items@1','for_items@2'].includes(step.op)) return `Repeat for each item from ${step.source}${step.policy ? ' · '+step.policy : ''}`;
  if (step.op === 'for_windows@1') return `Repeat ${step.occurrences} fixed windows · ${step.intervalMs} ms interval`;
  return `Nested steps · ${step.op}`;
}
