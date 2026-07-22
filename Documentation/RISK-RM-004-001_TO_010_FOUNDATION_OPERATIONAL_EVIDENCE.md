# RISK-RM-004-001 to RISK-RM-004-010 Foundation Operational Evidence

## Scope

This evidence record executes the first RISK-RM-004 certification completion packet:

- RISK-RM-004-001 Candidate Class Registry
- RISK-RM-004-002 Canonical Identity Normalization Tables
- RISK-RM-004-003 Constitutional Evaluation Rule Registry
- RISK-RM-004-004 Certification Threshold Doctrine
- RISK-RM-004-005 Constitutional Certification Test Registry
- RISK-RM-004-006 Identity Collision Resolution Doctrine
- RISK-RM-004-007 Constitutional Metrics Registry
- RISK-RM-004-008 Certification Manifest Schema
- RISK-RM-004-009 Constitutional Identifier Registry
- RISK-RM-004-010 Version Compatibility Matrix

## Implementation

The implementation adds `RiskRm004FoundationOperationalSupport`, which builds a deterministic operational registry package for the first RM-004 tranche.

Each record includes:

- required certification registry domains;
- implemented registry domains;
- deterministic guards;
- registry evidence;
- audit requirements;
- fail-closed findings;
- deterministic digest.

The package links registries through:

- candidate to identity;
- rules to thresholds to tests;
- identity to collision handling;
- metrics to manifest;
- identifiers to version compatibility.

## Fail-Closed Coverage

The test suite verifies that records fail closed when mandatory domains are omitted from:

- candidate classes;
- identity normalization;
- evaluation rules;
- thresholds;
- certification tests;
- collision resolution;
- metrics;
- manifest schema;
- identifier registry;
- version compatibility.

The suite also verifies guardrails that reject unregistered candidates, rules, tests, and implementation-defined compatibility.

## Verification

Commands executed:

```text
python -m unittest Tests.test_risk_rm004_foundation_operational
python -m compileall src\argos\risk\rm004_foundation_operational.py src\argos\risk\__init__.py Tests\test_risk_rm004_foundation_operational.py
python -m unittest Tests.test_risk_rm002_completion Tests.test_risk_rm003_specification Tests.test_risk_rm003_object_foundation Tests.test_risk_rm003_state_operational Tests.test_risk_rm003_closure_operational Tests.test_risk_rm004_certification_completion Tests.test_risk_rm004_foundation_operational Tests.test_risk_m4_operational_certification Tests.test_risk_office_framework Tests.test_risk_readiness Tests.test_risk_fusion_office Tests.test_risk_interaction_office Tests.test_tail_risk_office Tests.test_volatility_risk_office
```

## Outcome

RISK-RM-004-001 through RISK-RM-004-010 are represented as deterministic, replay-stable, fail-closed foundation certification registry evidence for independent audit.
