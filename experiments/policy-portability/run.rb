# frozen_string_literal: true

# Ruby implementation of balanced_artifacts_exact32@1.
require 'json'

ROOT = File.dirname(File.expand_path(__FILE__))
MASK = (1 << 32) - 1
MAX_ID = (1 << 64) - 1

def read_json(file)
  JSON.parse(File.read(file))
end

def valid_id?(value)
  value.is_a?(String) && /\A(?:0|[1-9][0-9]*)\z/.match?(value) && Integer(value, 10) <= MAX_ID
end

def score(round_id, recipient, artifact)
  value = ((round_id * 73_856_093) & MASK) ^
          ((Integer(recipient, 10) * 19_349_663) & MASK) ^
          ((Integer(artifact, 10) * 83_492_791) & MASK)
  value ^ (value >> 16)
end

def load_policy
  manifest = read_json(File.join(ROOT, 'policy.json'))
  plan = read_json(File.expand_path(manifest.fetch('basePlan'), ROOT))
  setting = plan.fetch('stages').filter_map do |stage|
    stage['assignment'] if stage['type'] == 'work' && stage.dig('assignment', 'policy') == 'balanced_artifacts'
  end.first
  raise 'incompatible base assignment' unless setting && setting['tie'] == 'cover_offer_score_v1' &&
                                             setting['excludeSelf'] == true &&
                                             setting['roundId'].is_a?(Integer) &&
                                             setting['roundId'].between?(0, MAX_ID)

  [manifest, setting]
end

def validate_covers(covers)
  raise 'covers must have canonical unsigned IDs' unless covers.is_a?(Array) && covers.all? do |item|
    item.is_a?(Hash) && valid_id?(item['id']) && valid_id?(item['owner'])
  end
  raise 'artifact IDs and owners must be unique' unless covers.map { |item| item['id'] }.uniq.size == covers.size &&
                                                        covers.map { |item| item['owner'] }.uniq.size == covers.size
end

def request_offer(state, covers, setting, event)
  return { 'status' => 'rejected' } unless event.is_a?(Hash) && event['requestId'].is_a?(String) &&
                                         !event['requestId'].empty? && valid_id?(event['recipient'])

  request_id = event['requestId']
  recipient = event['recipient']
  ledger = state['requestLedger']
  offers = state['offers']
  if ledger.key?(request_id)
    return { 'status' => 'rejected' } unless ledger[request_id] == recipient

    return { 'status' => 'replayed', 'options' => offers.fetch(recipient).dup }
  end
  if offers.key?(recipient)
    ledger[request_id] = recipient
    return { 'status' => 'existing', 'options' => offers.fetch(recipient).dup }
  end
  return { 'status' => 'rejected' } unless covers.any? { |item| item['owner'] == recipient }

  candidates = covers.reject { |item| item['owner'] == recipient }
  return { 'status' => 'rejected' } if candidates.size < setting['count']

  exposure = Hash.new(0)
  offers.each_value { |saved| saved.each { |artifact| exposure[artifact] += 1 } }
  sorted = candidates.sort_by do |item|
    [exposure[item['id']], score(setting['roundId'], recipient, item['id']), Integer(item['id'], 10)]
  end
  options = sorted.first(setting['count']).map { |item| item['id'] }
  offers[recipient] = options
  ledger[request_id] = recipient
  { 'status' => 'accepted', 'options' => options.dup }
end

def run(case_path, snapshot_path = nil, stop_at = nil)
  fixture = read_json(case_path)
  manifest, setting = load_policy
  missing = manifest.fetch('requires').reject { |item| fixture.fetch('capabilities').include?(item) }.sort
  return { 'status' => 'unsupported', 'missing' => missing } unless missing.empty?

  covers = fixture.fetch('covers')
  validate_covers(covers)
  snapshot = snapshot_path && read_json(snapshot_path)
  raise 'checkpoint policy mismatch' if snapshot && snapshot['policy'] != manifest['policy']

  state = snapshot ? snapshot.fetch('state') : { 'offers' => {}, 'requestLedger' => {} }
  outcomes = snapshot ? snapshot.fetch('outcomes') : []
  start_at = snapshot ? snapshot.fetch('nextIndex') : 0
  requests = fixture.fetch('requests')
  end_at = stop_at || requests.size
  raise 'invalid checkpoint index' unless start_at.is_a?(Integer) && end_at.is_a?(Integer) &&
                                          start_at.between?(0, end_at) && end_at <= requests.size

  requests[start_at...end_at].each { |event| outcomes << request_offer(state, covers, setting, event) }
  if stop_at
    return { 'status' => 'checkpoint', 'policy' => manifest['policy'], 'nextIndex' => end_at,
             'state' => state, 'outcomes' => outcomes }
  end
  { 'status' => 'ok', 'state' => state, 'outcomes' => outcomes }
end

raise 'usage: ruby run.rb case.json [snapshot.json|-] [stopAt]' unless ARGV.size.between?(1, 3)

snapshot_arg = ARGV[1] unless ARGV[1] == '-'
stop_arg = Integer(ARGV[2], 10) if ARGV[2]
puts JSON.generate(run(ARGV[0], snapshot_arg, stop_arg))
