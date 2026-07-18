# EO-DK Canonical Bridge Execution Fabric

EO-DK introduces `CanonicalBridgeExecutor`, the canonical runtime fabric for constitutionally significant handoffs. The fabric uses the existing EO-DB bridge IDs and enforces bridge identity, proof domain, artifact hash integrity, idempotency, destination acceptance, durable intent where required, and Workflow Execution Token ownership transfer.

Bridge definitions now distinguish requirement classification, implementation status, certification status, and transfer class. Event publication alone is not completion; a bridge result is accepted only after destination acceptance and, for ownership-transfer bridges, successful owner transfer.

The communications bus remains a transport/notification mechanism. It is not the bridge authority. The bridge registry defines the transition contract, the executor governs execution, token ownership governs LAW VII, and audit events preserve request/result evidence.

EO-DK evidence is generated under `Documentation/EO-DK_Evidence/`. The current formal verdict is `PASS` for the canonical bridge fabric.
