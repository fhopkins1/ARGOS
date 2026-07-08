# EO-052 Trader Group Framework

The Trader Group is the deterministic execution organization for ARGOS. It converts certified Executive intent into auditable execution preparation artifacts without introducing discretionary investment decisions, broker actions, or live trading authority.

## Deterministic Responsibilities

- Receive Command Decision Records from the Executive Group.
- Verify Risk Office certification prerequisites.
- Enforce governance boundaries and human override constraints.
- Construct deterministic execution workflow definitions.
- Maintain append-only execution state records.
- Produce Execution Case Files for later Historian evaluation.
- Route Historian-facing records only through the Courier Framework.

## Trader Group Architecture

The Trader Group contains deterministic office templates for Trade Execution, Order Management, Broker Integration, Execution Quality, Position Management, Trade Monitoring, and Trader Fusion. EO-052 establishes the architecture and coordination layer only; later Engineering Orders implement the subordinate offices in detail.

Upstream interfaces are Executive Group authorizations, Risk Office certifications, Human Override controls, Configuration, Audit, Persistence, Prompt Repository, and Courier. Downstream interfaces are Historian-facing Execution Case Files and later subordinate Trader Office outputs.

## Execution Philosophy

Trader execution is governed by four principles:

- Faithfully execute approved organizational intent.
- Introduce no discretionary investment decisions.
- Preserve complete auditability.
- Respect Risk constraints and Human Override controls.

## Deterministic Execution Pipeline

The EO-052 pipeline is:

1. Executive authorization receipt.
2. Risk certification verification.
3. Governance validation.
4. Execution plan construction.
5. Order lifecycle preparation.
6. Subordinate office coordination.
7. Historian recording.

## Order Lifecycle Framework

EO-052 defines the lifecycle vocabulary used by future Trader offices:

- `authorized`
- `risk_certified`
- `planned`
- `staged`
- `submitted`
- `acknowledged`
- `partially_filled`
- `filled`
- `confirmed`
- `historian_recorded`
- `exception`

Terminal states are `confirmed`, `historian_recorded`, and `exception`. EO-052 does not submit orders; it defines the lifecycle contract and creates execution preparation records.

## Risk Coordination Framework

Trader execution preparation requires both an approved CDR and a certified Risk Office prerequisite addressed to the Trader Group. If Risk certification is absent, stale, uncertified, or misaddressed, the Trader Group produces an Execution Exception Report instead of advancing execution state.

## Execution Metrics Framework

EO-052 establishes these metrics for later collection:

- Authorization validation latency.
- Risk certification pass rate.
- Execution plan generation count.
- Order lifecycle exception count.
- Historian record delivery count.
- Audit event count.

## Audit Architecture

Every Trader artifact is an `OperationalContract`, persisted through the Foundation persistence layer and recorded through the Audit Service. Required event families are document creation, validation results, staff decisions, mailbox deposits, courier transfers, and document receipts.

Traceability keys are `case_file_id`, `trade_cycle_id`, `cdr_id`, `risk_certification_id`, and `execution_case_file_id`.

## Produced Artifacts

- Execution Readiness Report
- Execution Status Report
- Trader Group Summary
- Execution Case File
- Execution Exception Report
- Execution State Record
- Authorization Verification Record
- Execution Audit Log
- Trader Workflow Definition
- Trader Governance Record

## Governance

EO-052 does not grant live trading authority. Trader artifacts explicitly carry `live_trading_instruction`, `broker_instruction`, and `discretionary_decision` as null values. Trading pause, read-only mode, and organization lockdown block execution preparation and generate deterministic exception reports.

## Traceability

Every Trader artifact references the originating Command Decision Record and certified Risk Office prerequisite. Execution Case Files are addressed to the Historian Group and are ready for later institutional learning workflows.

## Trader Group System Prompt

You are the Trader Group of ARGOS. Execute approved investment decisions with deterministic precision, complete auditability, and rigorous adherence to organizational risk constraints. Manage the complete order lifecycle from executive approval through execution, position confirmation, and historical recording. Maintain comprehensive execution logs, monitor execution quality, coordinate with brokers through authorized interfaces only, and ensure every trade faithfully implements approved organizational intent while preserving complete traceability for future historical evaluation.
