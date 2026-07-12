# OR-006 Entity Identity Model

Stable identities are enforced by object type plus object ID plus version.

Examples:

- `canonical-workflows`
- `canonical-missions`
- `paper-broker`
- `position-registry`
- `performance-truth-paper`
- `doctrine-policy`

New authoritative identities can be required unique. Duplicate new identities fail closed with `DUPLICATE_IDENTITY_REJECTED`.
