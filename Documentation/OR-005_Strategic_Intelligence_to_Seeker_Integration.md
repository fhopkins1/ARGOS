# OR-005 Strategic Intelligence to Seeker Integration

## Mandate Schema

Runtime stores strategic mandates with mandate ID, subject, decision, expiration, source Strategic Intelligence report IDs, authority, and a `runtime_authored` flag.

## Runtime Path

`create_strategic_mandate()` invokes `StrategicIntelligenceCommand` and records an advisory mandate. `request_seeker_work()` rejects Seeker work unless a valid mandate exists.

## Authority Separation

Runtime does not invent market opportunities. Strategic Intelligence provides the mandate; Seeker work remains blocked without it.

## No-Opportunity Behavior

Mandates with `avoid` or `no_search` decisions are non-actionable for Seeker admission.

## Part 2 Work

Part 2 must connect this mandate gate into the full Seeker discovery workflow and doctrine policy.
