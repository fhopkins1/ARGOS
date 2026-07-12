# EO-CH - Workflow Delta Engine

EO-CH adds the Workflow Delta Engine, the deterministic authority for comparing a validated prior workflow state against current state and producing the smallest justified revision package.

## Boundary

The engine compares, classifies, traces impact, and emits delta packages. It does not wake offices, start workflows, create missions, authorize missions, authorize expenditure, call AI, submit broker orders, mutate positions, or overwrite prior products. EO-CD remains mission-planning authority, EO-CF remains freshness authority, and EO-CG remains memory authority.

## Implemented Components

- `src/argos/control_panel/workflow_delta_engine.py`
  - `WorkflowDeltaEngine`
  - `DeltaBaseline`
  - `DeltaAnalysisRequest`
  - `FieldChange`
  - `SectionChange`
  - `EvidenceChange`
  - `ProductImpact`
  - `OfficeImpact`
  - `DependencyImpact`
  - `WorkflowNodeDelta`
  - `DeltaPackage`

## Capabilities

- Validated baseline construction with content hashing.
- Baseline integrity validation, including corrupt-hash rejection and subject/environment mismatch denial.
- Deterministic structured comparison for scalar, numeric, collection, policy, workflow, market, position, broker, and portfolio-like fields.
- Field-level and section-level delta output.
- Evidence added/removed/unchanged classification.
- Contextual materiality scoring.
- Product impact and reusable-scope preservation.
- Office impact matrix with excluded offices and deterministic-service substitutions.
- Dependency impact and propagation boundaries.
- Workflow graph comparison without marking nodes as executing.
- EO-CF freshness decision references.
- EO-CG prior-product retrieval references.
- EO-CD mission planner feed with minimum revision scope.
- Cost-reduction evidence without claiming unmeasured savings.
- Restart recovery from snapshot with duplicate package suppression.
- Safe Commander controls for export, replay, validation review, materiality review, broader/narrower comparison review, and full reassessment review.
- Commander-visible alerts for denied or unsafe delta requests.

## Runtime and API

Runtime state exposes `workflowDeltaEngine`.

Routes:

- `GET /api/workflow-delta/state`
- `POST /api/workflow-delta/baseline`
- `POST /api/workflow-delta/analyze`
- `POST /api/workflow-delta/recover`
- `POST /api/workflow-delta/export`
- `POST /api/workflow-delta/replay`
- `POST /api/workflow-delta/review`

## Control Panel Bridge

The Workflow Delta Bridge displays:

- delta requests
- change summary
- field and section delta
- product impact matrix
- office impact matrix
- dependency impact map
- workflow graph comparison
- reuse and work reduction
- EO-CD mission planner feed
- safe Commander review, replay, and export controls

## Known Limitations

- Persistence is runtime snapshot/in-memory until a durable repository is added.
- Semantic document comparison is intentionally absent; routine comparison is deterministic only.
- EO-CD integration is a structured feed, not automatic mission creation.
