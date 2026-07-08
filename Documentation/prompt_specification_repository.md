# EO-008 Prompt and Specification Repository

ARGOS prompts and specifications are Foundation-controlled repository artifacts.
Prompt revisions are append-only, versioned, validated, and snapshot-linked to
Case Files.

## Prompt Repository

`PromptRepository` stores immutable prompt revisions. Prompts cannot be used
outside the repository because snapshots are created from registered records.

Prompt passports include:

- prompt ID
- title
- owner group
- author staff
- purpose
- allowed environments
- input contract types
- output contract types
- dependencies
- safety notes

## Specification Repositories

EO-008 creates append-only repositories for:

- Staff Specifications (`SP`)
- Interface Specifications (`IF`)
- Database Specifications (`DB`)
- API Specifications (`API`)
- Test Specifications (`TS`)

## Prompt Snapshots

`PromptSnapshotService` links a registered prompt revision to a Case File and
Trade Cycle. Snapshots store prompt metadata and hashes, not uncontrolled prompt
text outside the repository.

## Dependency Graph

`DependencyGraph` links PB, EO, SP, IF, DB, API, TS, prompt, and Case File nodes.
The graph supports direct dependency lookup, reverse dependent lookup,
transitive dependency traversal, and search.

