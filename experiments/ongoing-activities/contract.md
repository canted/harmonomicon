# Ongoing-activity contract 0.1

This is a deliberately narrow comparison, not an adopted package format. A JSON definition declares actors, required host capabilities, event-to-operation bindings, one calendar kind, and visibility options. The host supplies an authoritative serial event order, trusted integer `at` values, authenticated actor IDs, and opaque artifact references. A missing capability rejects the package as `unsupported`. Rejected events do not apply their operation. For known events in the `windows` calendar, time and phase still advance before the operation is checked.

## Windowed jam

`registrationEnds`, `submissionsEnd`, and `reviewsEnd` are increasing integer boundaries. The phases are `[0, registrationEnds)` registration, `[registrationEnds, submissionsEnd)` making, `[submissionsEnd, reviewsEnd)` review, and `[reviewsEnd, ∞)` reveal. `register_team` is host-only in registration. Each participant belongs to at most one team. Team registration by a host is authoritative in this experiment; the engine does not collect member consent.

During making, a team member may `post_progress` any number of unique posts with an allowed audience, `respond` to a post they can see, and `submit_final` once per team. Posts are append-only; responses inherit the parent post's audience. A team-only post is never exposed to other teams. A final submission is visible to its own team during making, to participants during review and reveal. During review, a participant can review another team's submitted final. The author sees their own review immediately; all participants see reviews at reveal. No ranking or winner is calculated. `tick` is a system event that can expose a time boundary without other participant action.

## Daily practice

`open_day` is system-only and must open the next integer day with a future deadline. Each participant may `submit_day` one opaque artifact before the deadline. `close_day` is system-only at or after the deadline and marks remaining participants `missed`. Opening the next day retains earlier entries and statuses. A private definition exposes each artifact only to its author; a public definition exposes artifacts to all participants as soon as submitted. Both expose completion status to participants. Host/system views may see all artifact references. This is visibility within the interpreter's output, not an API or storage access-control proof.

## Boundaries

The package does not schedule its own ticks or daily opens, send messages, prove media or word counts, validate team consent, store artifacts, moderate discussion, or implement real database concurrency. It does not model edit/delete, changing team membership, or per-comment audience changes. The interpreters branch on calendar kind and named operation, never on package ID. Definitions are source-constrained test configurations, not canonical rules for Global Game Jam, itch.io, 750 Words, or Jamuary.
