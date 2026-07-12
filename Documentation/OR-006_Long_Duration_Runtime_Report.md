# OR-006 Long Duration Runtime Report

OR-006 introduces bounded checkpoint and backup persistence primitives, but no long-duration unattended certification is claimed.

Current bounded behavior:

- no duplicate runtime loop from OR-005,
- idempotent recovery does not duplicate missions/workflows,
- checkpoints do not create truth,
- recovery audit is append-only.

OR-007 must perform continuous runtime certification.
