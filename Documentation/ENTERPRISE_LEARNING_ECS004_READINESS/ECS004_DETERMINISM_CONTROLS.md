# ECS-004 Determinism Controls

Randomness: fixed seed `42`.
Timestamps: evidence generator uses fixed timestamp constants.
Ordering: JSON is written with sorted keys; inventories are sorted.
Concurrency: no concurrent behavior is required.
Floating point: fixture metrics are explicit constants and compared exactly.
Locale/timezone: output identity does not depend on host locale or timezone.
Filesystem ordering: file inventories are sorted before hashing.
External services: none permitted.
Permitted volatile fields: final ZIP file names and host-specific Desktop paths only.
