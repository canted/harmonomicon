# Named-mechanism contract 0.1

**Experimental only.** A definition has `format: "activity-named-mechanisms/0.1"`, `id`, `kind`, `requires`, `actors`, `content`, and `config`. Actor roles are `host`, `system`, or `participant`. Event envelopes have `type`, `actor`, integer `at`, and object `payload`. A missing required capability returns `unsupported`; an invalid event returns `rejected` with no state change. Definitions do not contain executable code.

## `handoff`

Configuration: `participants` (ordered IDs), `start` (one of those IDs), `steps` (positive integer), `mode` (`contribute` or `unlock`), `reveal` (`end` or `each`), and `items` (required for `unlock`, with exactly `steps` entries). This first experiment only permits `contribute` with `end` and `unlock` with `each`; unsupported combinations reject at load time.

An `advance` event must come from the current participant. In `contribute` mode its payload contains a string `item` and, except on the last step, a string `guide`. In `unlock` mode the app takes the next item from the package. Except on the last step, `payload.next` must name a different participant. Each accepted event appends one item, increments `index`, and transfers `current` or ends. A participant view contains phase, current, and index; the current actor alone sees the latest guide; entries are shown to all at the configured reveal time. This is a digital handoff algorithm, not physical possession detection.

## `collection`

Configuration: `participants`, `schedule` (`daily` or `one_shot`), `viewGate` (`after_own` or `at_close`), and `latePolicy` (`mark`, `accept`, or `reject`). An `open` event from a `system` or `host` actor supplies `occurrence` (the next positive integer) and `deadline` (integer milliseconds). It clears prior submissions and opens the occurrence. A `one_shot` package permits only occurrence 1. The host is responsible for when to send `open`; this definition does not prove a calendar schedule.

A participant may `submit` one string `artifact` reference in an open occurrence. For an event after `deadline`, `reject` refuses it; `mark` or `accept` accepts it and records `late: true`. A `close` event from `system` or `host` closes the occurrence. Participant views always contain phase and occurrence; posts and late flags are visible after that actor submits for `after_own`, or after close for `at_close`. Host/system views show submissions throughout. Only named participants can submit or receive participant views.

Both mechanisms treat `artifact` strings as opaque references. Identity, storage, delivery, media rendering, and the truth of any offline action remain host responsibilities. The contract's claim is deterministic app state and visibility for these narrow configurations.
