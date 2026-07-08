# EO-014 Chief of Staff

The Chief of Staff validates every Executive Briefing Packet before it can reach
the Commander. Rejected packets are returned through Foundation Courier Service.

## Validation Scope

- Document integrity verification
- Signature verification
- Evidence verification
- Configuration snapshot verification
- Prompt snapshot verification
- Model snapshot verification
- Contradiction detection
- Missing document detection
- Duplicate detection
- Stale report detection

## Routing

Accepted EBPs are routed to the Commander Decision Engine. Rejected EBPs produce
an `EBP_REJECTION` operational contract and are returned through Courier.

Every action records audit events through Courier or Commander services and
persists validation records through Foundation Persistence.

