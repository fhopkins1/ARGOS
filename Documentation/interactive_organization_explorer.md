# Interactive Organization Explorer

The Interactive Organization Explorer (IOE) is the Commander navigation interface for the ARGOS Deterministic Cognitive Enterprise.

## Hierarchy

IOE supports deterministic exploration through:

- Enterprise
- Organization
- Office
- Workflow
- Task
- Case File
- Evidence
- Historical Record
- Audit Trail

## Displayed Object Fields

Every explorer object includes:

- Identifier
- Status
- Current activity
- Dependencies
- Relationships
- Supporting evidence
- Historical context
- Audit information

## Commander Actions

IOE supports:

- Inspect
- Search
- Filter
- Bookmark
- Follow
- Compare
- Export
- Monitor

Every explorer action emits an Enterprise Activity Bus navigation event.

## Filters

Commander filters include:

- Organization
- Office
- Asset
- Workflow
- Case file
- Priority
- Status
- Time
- Object type
- Text search

## Synchronization

The current implementation constructs a deterministic read model from:

- Enterprise Command Center
- Enterprise Activity Bus
- Commander Notification & Alert Center
- Office Operating Modes & Scheduling
- Audit event counts

The IOE is a navigation read model, not a separate source of truth.
