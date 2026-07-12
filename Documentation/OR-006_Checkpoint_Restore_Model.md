# OR-006 Checkpoint Restore Model

Checkpoints are persisted as `enterprise_runtime_checkpoint`.

Restore rule:

Checkpoint state may speed continuity only after authoritative mission, workflow, broker, position, and truth records are evaluated. If checkpoint and authoritative truth disagree, authoritative truth wins.
