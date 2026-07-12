# OR-006 Corruption Detection Model

Detected corruption includes:

- backup hash mismatch,
- persistent record hash mismatch,
- payload hash mismatch,
- broken hash chains,
- broken version sequences,
- duplicate new identity attempts,
- workflow token/workflow mismatch during recovery.

Critical corruption fails closed and prevents paper operation.
