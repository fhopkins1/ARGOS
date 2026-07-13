# EO-DD Participant and Acknowledgment Model

Participants are durable authorities such as Paper Broker, Position Registry, Performance Truth, Closed Position Truth, Historian, and Transaction Coordinator.

Each participant record includes authority, required action, dependency order, current state, evidence reference, output version, acknowledgment count, and failure code. Acknowledgments are idempotent by acknowledgment key and preserve evidence references; duplicate acknowledgments return the original acknowledgment.

Participant states include pending, ready, in progress, applied, acknowledged, failed, retry pending, reconciliation required, quarantined, rolled forward, superseded, and not applicable.

