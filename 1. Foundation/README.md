# 1. Foundation

Foundational architecture, deterministic contracts, repository governance, configuration standards, and shared primitives.

## EO-002 Identity Framework

Foundation owns deterministic identity generation and validation. See `src/argos/foundation/identity` and `Documentation/identity_framework.md`.

## EO-003 Canonical Data Contract Framework

Foundation owns the shared contract envelope for operational and infrastructure records. See `src/argos/foundation/contracts` and `Documentation/canonical_data_contract_framework.md`.

## EO-004 Deterministic Communication and Courier Framework

Foundation owns mailbox-mediated contract movement. See `src/argos/foundation/communication` and `Documentation/deterministic_communication_courier_framework.md`.

## EO-005 Audit and Traceability Framework

Foundation owns immutable audit events, append-only audit logs, and Case File replay. See `src/argos/foundation/audit` and `Documentation/audit_traceability_framework.md`.

## EO-006 Configuration and Environment Framework

Foundation owns configuration loading, startup validation, environment switching, feature flags, secret references, and Case File configuration snapshots. See `src/argos/foundation/configuration` and `Documentation/configuration_environment_framework.md`.

## EO-007 Database and Persistence Foundation

Foundation owns deterministic persistence schemas, migrations, append-only object versioning, replay/search, and backup/restore interfaces. See `src/argos/foundation/persistence` and `Documentation/database_persistence_foundation.md`.

## EO-008 Prompt and Specification Repository

Foundation owns prompt passports, prompt revision history, prompt snapshots, specification repositories, and dependency graph links. See `src/argos/foundation/prompts` and `Documentation/prompt_specification_repository.md`.

## EO-009 Foundation Testing Framework

Foundation owns deterministic test suite registration, execution, and compliance reporting. See `src/argos/foundation/testing` and `Documentation/foundation_testing_framework.md`.

## EO-010 Foundation Operational Readiness

Foundation owns operational readiness verification and completion reporting before Group 2 begins. See `src/argos/foundation/readiness` and `Documentation/foundation_operational_readiness.md`.
