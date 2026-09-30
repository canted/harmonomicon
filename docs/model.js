/** A descriptive diagram of a 0.12 contract, not a runtime interpreter. */
export const FORMAT = 'harmonomicon.activity-package/0.12';
export const CONTRACTS = [
  'timed_collection@1', 'sequential_handoff@1', 'repeated_collection@1',
  'offered_response@1', 'project_cycle@1', 'ongoing_space@1',
  'guided_rounds@1', 'competitive_handoff@1', 'offered_response_vote@1',
  'permissioned_dialogue@1'
];

function nonempty(value) { return typeof value === 'string' && value.length > 0; }
function invariant(ok, message) { if (!ok) throw new Error(message); }
function duration(ms) {
  if (!Number.isSafeInteger(ms) || ms <= 0) return 'configured duration';
  if (ms % 86400000 === 0) return `${ms / 86400000} day${ms === 86400000 ? '' : 's'} elapsed`;
  if (ms % 3600000 === 0) return `${ms / 3600000} hour${ms === 3600000 ? '' : 's'}`;
  if (ms % 60000 === 0) return `${ms / 60000} min`;
  return `${ms} ms`;
}

export function buildDiagram(pkg) {
  invariant(pkg && typeof pkg === 'object' && !Array.isArray(pkg), 'Choose a JSON object.');
  invariant(pkg.format === FORMAT, `This viewer supports ${FORMAT}.`);
  invariant(nonempty(pkg.id) && nonempty(pkg.version), 'Package id and version are required.');
  invariant(pkg.content && nonempty(pkg.content.title) && nonempty(pkg.content.prompt), 'Package content is incomplete.');
  invariant(pkg.participants && Number.isInteger(pkg.participants.min) && Number.isInteger(pkg.participants.max), 'Participant bounds are missing.');
  invariant(Array.isArray(pkg.requires), 'The requires list is missing.');
  invariant(pkg.behavior && nonempty(pkg.behavior.contract), 'The behavior contract is missing.');
  const b = pkg.behavior;
  invariant(CONTRACTS.includes(b.contract), `Unsupported behavior: ${b.contract}. No diagram was inferred.`);
  const nodes = [], edges = [];
  let column = 0;
  const add = (id, title, subtitle, info = {}, row = 0, at = null) => {
    nodes.push({id, title, subtitle, row, column: at ?? column++,
      events: info.events ?? [], view: info.view ?? [], rules: info.rules ?? [],
      setup: info.setup ?? [], description: info.description ?? ''});
    return id;
  };
  const edge = (source, target, label) => edges.push({id:`${source}-${target}-${edges.length}`, source, target, label});
  const chain = (steps) => {
    let previous;
    for (const [id, title, subtitle, info, trigger] of steps) {
      add(id, title, subtitle, info);
      if (previous) edge(previous, id, trigger);
      previous = id;
    }
  };
  const shared = {
    title: pkg.content.title, summary: pkg.content.summary ?? '', id: pkg.id,
    version: pkg.version, contract: b.contract, participants: pkg.participants,
    requires: pkg.requires, prompt: pkg.content.prompt, nodes, edges,
    note: 'This is a package blueprint. People, actual dates, assigned groups, and event outcomes belong to an instance or run.'
  };

  switch (b.contract) {
    case 'timed_collection@1':
      chain([
        ['waiting','Waiting','before opensAt',{setup:['opensAt', 'closesAt'], view:['Phase and submission count']},null],
        ['open','Open',`${b.medium} submissions`,{events:['submit {value}', 'system tick {}'],view:['Group: phase and submission count','Participant: own entry only'],rules:['One accepted submission per participant','Window is [opensAt, closesAt)']},'opensAt'],
        ['closed','Closed','group reveal',{view:['All bound actors: ordered entries'],rules:['Missing submissions do not delay closing']},'closesAt']
      ]);
      break;
    case 'sequential_handoff@1': {
      invariant(Number.isInteger(b.steps) && b.steps >= 2, 'Invalid handoff step count.');
      add('step-1','Step 1','current actor', {setup:['route: each participant exactly once'],events:['Current actor: submit {value}'],view:['First actor: package prompt','Others: phase and current actor'],rules:['No timeout or skip']});
      if (b.steps > 2) {
        add('middle',b.steps === 3 ? 'Step 2' : `Steps 2–${b.steps-1}`,'sequential handoff',{events:['Current actor: submit {value}'],view:['Current actor: immediate predecessor value only'],rules:['Fixed route; one contribution per step']});
        edge('step-1','middle','submit');
      }
      const finalId = `step-${b.steps}`;
      add(finalId,`Step ${b.steps}`,'last actor',{events:['Current actor: submit {value}'],view:['Immediate predecessor value only']});
      edge(b.steps > 2 ? 'middle' : 'step-1',finalId,'submit');
      add('complete','Complete','chain reveal',{view:['All bound actors: full ordered chain']});
      edge(finalId,'complete','submit');
      break;
    }
    case 'repeated_collection@1': {
      invariant(Number.isInteger(b.occurrences) && b.occurrences >= 2, 'Invalid occurrence count.');
      add('waiting','Waiting','before startsAt',{setup:['startsAt']});
      add('window','Collection window',`${b.occurrences} occurrences · ${duration(b.windowMs)}`,{
        events:['submit {occurrence, value}'],view:[`Visibility: ${b.visibility}`,'Group sees each participant’s completion status'],
        rules:[`Interval: ${duration(b.intervalMs)}`,'One accepted entry per participant per occurrence']});
      edge('waiting','window','startsAt');
      if (b.windowMs < b.intervalMs) {
        add('between','Between','gap between windows',{view:['Closed occurrence history and statuses']});
        edge('window','between','window closes');
        edge('between','window','next interval');
        add('complete','Complete','final window closed',{view:['Retained occurrence history']});
        edge('window','complete','after final window');
      } else {
        edge('window','window','next interval');
        add('complete','Complete','final window closed',{view:['Retained occurrence history']});
        edge('window','complete','after final window');
      }
      break;
    }
    case 'offered_response@1':
    case 'offered_response_vote@1': {
      const voting = b.contract === 'offered_response_vote@1';
      chain([
        ['waiting','Waiting','before opensAt',{setup:['opensAt','sourceDeadline','responseDeadline',...(voting ? ['voteDeadline'] : []),'roundId']},null],
        ['sources','Sources open',b.sourceMedium,{events:['submit_source {value}'],view:['Own source only; group sees source count'],rules:['One source per participant']},'opensAt'],
        ['responses','Responses open','saved two-source offers',{events:['request_offer {}','submit_response {source, value}'],view:['Requester: own two offered sources and own response','Others: counts only'],rules:['Only source contributors may request offers','Exact policy: balanced_artifacts_exact32@1','Offer is saved on first request']},'sourceDeadline · ≥3 sources']
      ]);
      add('insufficient','Insufficient sources','terminal · no group reveal',{view:['Own source only'],rules:['Fewer than 3 sources at sourceDeadline']},1,2);
      edge('sources','insufficient','sourceDeadline · <3');
      if (voting) {
        add('voting','Voting','reveal source-response pairs',{events:['submit_vote {responseActor}'],view:['Everyone: sources and responses','Voter: own ballot only','Group: vote count'],rules:['One vote per participant','Cannot vote for own caption']});
        edge('responses','voting','responseDeadline');
        add('complete','Complete','scores and winners',{view:['Group: scores and all tied positive winners'],rules:['No votes means no winner']});
        edge('voting','complete','voteDeadline');
      } else {
        add('complete','Complete','group reveal',{view:['Everyone: sources and responses']});
        edge('responses','complete','responseDeadline');
      }
      break;
    }
    case 'project_cycle@1':
      chain([
        ['waiting','Waiting','before opensAt',{setup:['teams','opensAt','submissionDeadline','reviewDeadline']},null],
        ['work','Work','team progress and final',{events:['post_progress','comment','submit_final'],view:['Progress follows its private/team audience','One final per team'],rules:['Teams fixed at instance creation']},'opensAt'],
        ['review','Review','peer text reviews',{events:['submit_review'],view:['Final submissions revealed; reviews remain private until reviewDeadline']},'submissionDeadline'],
        ['complete','Complete','reviews revealed',{view:['Bound actors see permitted final work and reviews']},'reviewDeadline']
      ]);
      break;
    case 'ongoing_space@1': {
      const series = b.schedule?.kind === 'fixed_prompt_series';
      invariant(b.schedule && (series || b.schedule.kind === 'open'), 'Unsupported ongoing-space schedule.');
      if (series) {
        add('waiting','Waiting','before startsAt',{setup:['startsAt']});
        add('open','Prompt window',`${b.schedule.prompts?.length ?? '?'} prompts · ${duration(b.schedule.windowMs)}`,{
          events:['post_entry {occurrence, audience, value}','comment {entryId, value}'],
          view:[`Completion status: ${b.schedule.statusVisibility}`,'Group entries shared; private entries visible only to author'],
          rules:[`Interval: ${duration(b.schedule.intervalMs)}`,'Comments allowed in gaps on group entries']});
        edge('waiting','open','startsAt');
        if (b.schedule.windowMs < b.schedule.intervalMs) {
          add('between','Between','prompt gap',{events:['comment on group entry'],view:['Retained entries and occurrence history']});
          edge('open','between','window closes'); edge('between','open','next interval');
          add('complete','Complete','final window closed'); edge('open','complete','after final window');
        } else {
          edge('open','open','next interval'); add('complete','Complete','final window closed'); edge('open','complete','after final window');
        }
      } else {
        chain([
          ['waiting','Waiting','before startsAt',{setup:['startsAt','endsAt']},null],
          ['open','Open space','entries and comments',{events:['post_entry {audience, value}','comment {entryId, value}'],view:['Group entries shared; private entries visible only to author'],rules:['Any number of entries while open']},'startsAt'],
          ['complete','Complete','posting closed',{view:['Retained permitted entries and comments']},'endsAt']
        ]);
      }
      break;
    }
    case 'guided_rounds@1': {
      invariant(Array.isArray(b.rounds) && b.rounds.length >= 2, 'Missing guided rounds.');
      add('waiting','Waiting','before startsAt',{setup:['startsAt','groupsByRound: all partitions fixed at creation']});
      let previous='waiting';
      b.rounds.forEach((round,index) => {
        const id=`round-${index+1}`;
        add(id,`Round ${index+1}: ${round.id}`,duration(round.durationMs),{
          description:round.prompt, events:[`submit {round: ${index+1}, value}`],
          view:[`Visibility: ${round.visibility}`],
          rules:[`Group size: ${round.groupMin}–${round.groupMax}`,'One optional text entry per participant']});
        edge(previous,id,index===0?'startsAt':'previous duration ends'); previous=id;
      });
      add('complete','Complete','last round ended'); edge(previous,'complete','final duration ends');
      break;
    }
    case 'competitive_handoff@1':
      chain([
        ['waiting','Waiting','before startsAt',{setup:['startsAt','routes','attemptMs']},null],
        ['attempt','Offered attempt',`${b.steps} steps · ${duration(b.attemptMs)} each`,{
          events:['offered actor: submit {step, attempt, value}','offered actor: decline {step, attempt}'],
          view:['Only current offered actors see immediate input'],rules:['First valid response wins','At most two attempts per step']},'startsAt'],
        ['complete','Complete','final step accepted',{view:['Group: full accepted chain']},'final submit']
      ]);
      add('fallback','Fallback attempt','after decline or timeout',{events:['submit or decline'],view:['Only newly offered actors see input']},1,1);
      edge('attempt','fallback','both decline or deadline'); edge('fallback','attempt','winning submit · next step'); edge('fallback','complete','winning final submit');
      edge('attempt','attempt','winning submit · next step');
      add('stalled','Stalled','no accepted response',{view:['Partial chain stays private']},1,2);
      edge('fallback','stalled','no attempt left'); edge('attempt','stalled','no attempt left');
      break;
    case 'permissioned_dialogue@1':
      chain([
        ['meaning','Meaning','responder statements',{description:b.phasePrompts?.meaning,setup:['maker'],events:['responder: post_meaning'],view:['Group-visible transcript']},null],
        ['maker-questions','Maker questions','maker asks; responders answer',{description:b.phasePrompts?.maker_questions,events:['maker: ask_question','responder: answer_question'],view:['Group-visible linked questions and answers']},'facilitator advance'],
        ['neutral-questions','Neutral questions','responders ask; maker answers',{description:b.phasePrompts?.neutral_questions,events:['responder: ask_neutral','maker: answer_neutral'],view:['Group-visible transcript'],rules:['App does not judge neutrality']},'facilitator advance'],
        ['opinions','Permissioned opinions','maker grants per request',{description:b.phasePrompts?.permissioned_opinions,events:['responder: request_permission','maker: decide_permission','granted responder: post_opinion'],view:['Group-visible requests, decisions, and granted opinions'],rules:['No opinion without its own grant']},'facilitator advance'],
        ['complete','Complete','dialogue closed',{view:['Group-visible transcript']},'facilitator advance']
      ]);
      break;
  }
  invariant(nodes.length > 0 && edges.every(e => nodes.some(n => n.id === e.source) && nodes.some(n => n.id === e.target)), 'Diagram construction failed.');
  return shared;
}
