# OR-006 Runtime Checkpoint Model

Runtime checkpoints are continuity aids only.

They may contain:

- runtime mode,
- admission count,
- scheduler progress,
- background continuity metadata.

They may not contain or replace:

- broker fills,
- positions,
- Performance Truth,
- Closed Position Truth,
- policy authority.

The OR-006 test suite proves a checkpoint with a fake position count does not create position truth.
