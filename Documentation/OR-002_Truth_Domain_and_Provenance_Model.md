# OR-002 Truth Domain and Provenance Model

## Runtime Modes

ARGOS now recognizes these truth domains in code and documentation:

- `TEST`: automated tests and fixtures only.
- `PROOF`: workflow/UI/LAW VII/credit-accounting smoke tests; not operational truth.
- `SIMULATION`: replay, stress testing, Monte Carlo, black-swan, counterfactual, and laboratory analysis.
- `PAPER`: provisional or certified paper-broker operation.
- `LIVE`: disabled and fail-closed.

The central implementation is `src/argos/control_panel/truth_domain.py`.

## Record Metadata

Operationally significant records may carry:

- `environment`
- `executionMode`
- `truthClassification`
- `sourceSystem`
- `sourceRecordIds`
- `workflowId`
- `decisionObjectId`
- `officeAuthority`
- `createdAt`
- `deterministicId`
- `provenanceStatus`
- `certificationStatus`
- `commanderTruthLabel`

## Decision Object Provenance

`DecisionObjectSchemaRegistry.freeze` now attaches provenance metadata and an `operationalProvenanceValidation` block. Runtime/proof objects are labeled:

- `executionMode`: `PROOF`
- `truthClassification`: `PROOF_ONLY`
- `provenanceStatus`: `REJECTED`
- `certificationStatus`: `PROOF_MODE_NOT_ACTIONABLE`

PAPER-actionable Decision Objects must not contain placeholder, proof, simulation, runtime-authored, missing-risk, missing-trader, missing-market, or uncertified fields.

## Rejection Codes

The shared validator can emit:

- `MISSING_PROVENANCE`
- `UNAUTHORIZED_PRODUCER`
- `PLACEHOLDER_VALUE`
- `SIMULATION_VALUE_IN_OPERATIONAL_PATH`
- `MISSING_RISK_AUTHORITY`
- `MISSING_TRADER_AUTHORITY`
- `UNCERTIFIED_DECISION_OBJECT`
- `PROOF_MODE_NOT_ACTIONABLE`
- `LIVE_DISABLED`

## Performance Truth Boundary

`PerformanceTruthEngine.record_completed_workflow` validates the latest Decision Object before creating orders, fills, positions, trades, valuations, outcomes, workflow attribution, or office attribution.

Invalid workflow products are recorded only in `rejectedTruthRecords`. They do not mutate operational ledgers.

## Dashboard Labels

The Command Bridge now distinguishes:

- `PAPER - CERTIFIED OPERATIONAL RECORD`
- `PROOF MODE - NOT OPERATIONAL TRUTH`
- `SIMULATION - NO BROKER ORDER`

Proof records do not populate certified equity curves, trade history, open positions, closed trades, or performance metrics.

