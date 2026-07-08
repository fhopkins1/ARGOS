# EO-002 Deterministic Identity Framework

ARGOS persistent objects must have globally unique, human-readable identifiers.
Foundation owns identifier generation and validation. Operational groups consume
the Foundation identity package and must not define duplicate formats.

## Identifier Format

Runtime identifiers use the PB-006 `PREFIX-NNN` convention:

- Department: `DEP-NNN`
- Staff member: `STF-NNN`
- Trade cycle: `TC-NNN`
- Case file: `CF-NNN`
- Operational document: `DOC-NNN`

Sequences are one-based integers padded to at least three digits. Identifiers do
not depend on storage location and must not change after assignment.

## Foundation Package

The identity framework lives at:

`src/argos/foundation/identity`

Primary functions:

- `generate_department_id(sequence)`
- `generate_staff_id(sequence)`
- `generate_trade_cycle_id(sequence)`
- `generate_case_file_id(sequence)`
- `generate_document_id(sequence)`
- `validate_identifier(identifier)`
- `parse_identifier(identifier)`

## Department Registry

`DEPARTMENT_ID_REGISTRY` assigns deterministic Department IDs to ARGOS enterprise
groups and offices.

## Doctrine Note

PB-006 defines `DEP`, `STF`, `CF`, and `DOC`, but does not define a trade-cycle
prefix. EO-002 requires Trade Cycle ID generation, so Foundation reserves `TC` as
the current trade-cycle prefix pending explicit Project Bible confirmation.

