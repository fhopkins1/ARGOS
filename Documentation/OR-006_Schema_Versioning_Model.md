# OR-006 Schema Versioning Model

Every enterprise persisted envelope includes:

- `schema_version`
- `truth_domain`
- `serialization_version`
- `creation_sequence`
- `modification_sequence`
- `payload_hash`
- `idempotency_key`
- migration compatibility metadata

Enterprise object families are added to foundation `ObjectType` and `canonical_schemas()`.
