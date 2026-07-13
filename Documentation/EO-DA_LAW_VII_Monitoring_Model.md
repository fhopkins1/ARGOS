# EO-DA LAW VII Monitoring Model

`LawVIIMonitor` evaluates Workflow Orchestrator snapshots.

## Checks

- Workflow has exactly one token payload.
- Token workflow ID matches workflow ID.
- Token IDs are not duplicated.
- Active tokens have a current or next owner.
- Current owner belongs to workflow stages.
- Terminal workflows do not retain an owner.
- Non-dormant office state matches token owner.

The monitor reports violations only. It does not transfer tokens, wake offices, recover ownership, or mutate workflow state.

