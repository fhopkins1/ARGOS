# ECS-004 Auditor Execution Runbook

Authoritative single-command workflow:

1. `python Scripts\enterprise_learning_ecs004_final_certification.py`

The command performs repository verification, dependency verification, behavioral regeneration, evidence generation, schema validation, deterministic comparison, mutation execution, Behavioral Completion Review, and certification report generation.

Fallback diagnostic command sequence:

1. `python Scripts\enterprise_learning_rm002_behavioral_implementation.py`
2. `python Scripts\enterprise_learning_ecs004_readiness_package.py`
3. `python Scripts\enterprise_learning_rm002a_behavioral_completion.py`
4. `python -m unittest Tests.test_enterprise_learning_rm002a_behavioral_completion Tests.test_enterprise_learning_rm002_runtime Tests.test_enterprise_learning_mo001_architecture_hardening Tests.test_enterprise_learning_rm001_constitutional_baseline Tests.test_learning_integration_office`

Expected result: all tests pass, RM-002 evidence regenerates, ECS-004 readiness manifests regenerate, and no network or external service is used.

Interpretation:

* A missing dependency, missing file, schema mismatch, hash mismatch, or unexpected mutation pass is `FAIL`.
* An interrupted or incomplete run is `INCOMPLETE`.
* This package does not declare ECS-004 certification. It supplies materials for independent assessment.
