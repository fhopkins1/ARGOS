from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.infrastructure import (  # noqa: E402
    AuthorityDefinition,
    BridgeDefinition,
    BridgeDirection,
    BuildIdentity,
    CandidateIdentity,
    ExecutionChain,
    ExecutionIdentity,
    ExecutionTruthFailure,
    ExecutionTruthStatus,
    InfrastructureAuthorityBridgeCertifier,
    InfrastructureCertificationDoctrineEngine,
    InfrastructureCertificationEvidence,
    InfrastructureCertificationFailure,
    InfrastructureCertificationLifecycleState,
    InfrastructureCertificationPhase,
    InfrastructureGraphFailure,
    InfrastructureGraphStatus,
    InfrastructureTestCategory,
    InfrastructureTruthExecutionValidator,
    RepositoryIdentity,
    RuntimeDependency,
    RuntimeIdentity,
    RuntimeInfrastructureGraph,
)


def repository() -> RepositoryIdentity:
    return RepositoryIdentity(
        repository_id="REPO-ARGOS",
        origin="https://github.com/fhopkins1/ARGOS.git",
        canonical_branch="main",
        commit_hash="edba9a7ba1e663814038a5ea72bd37064f9e2889",
        lineage=("887521b", "edba9a7"),
        certification_history=("INF-001",),
    )


def candidate(**overrides) -> CandidateIdentity:
    data = {
        "candidate_id": "CAND-1",
        "repository_id": "REPO-ARGOS",
        "commit_hash": "edba9a7ba1e663814038a5ea72bd37064f9e2889",
        "branch": "main",
        "build_id": "BUILD-1",
        "runtime_id": "RUNTIME-1",
        "creation_timestamp": "2026-07-20T12:00:00Z",
        "certification_cycle": "INF",
        "certification_authority": "Infrastructure",
        "certification_status": "UNDER_REVIEW",
    }
    data.update(overrides)
    return CandidateIdentity(**data)


def build(**overrides) -> BuildIdentity:
    data = {
        "build_id": "BUILD-1",
        "compiler_version": "python-3.14",
        "dependency_versions": {"stdlib": "3.14"},
        "package_manifest_hash": "sha256:manifest",
        "lock_file_hashes": ("sha256:lock",),
        "environment_configuration_hash": "sha256:env",
        "build_parameters_hash": "sha256:params",
        "build_timestamp": "2026-07-20T12:01:00Z",
        "build_host": "cert-host",
        "artifact_checksum": "sha256:artifact",
        "reproducible": True,
    }
    data.update(overrides)
    return BuildIdentity(**data)


def runtime(**overrides) -> RuntimeIdentity:
    data = {
        "runtime_id": "RUNTIME-1",
        "candidate_id": "CAND-1",
        "build_id": "BUILD-1",
        "runtime_configuration_hash": "sha256:runtime-config",
        "startup_timestamp": "2026-07-20T12:02:00Z",
        "runtime_version": "runtime-1",
        "infrastructure_version": "INF-002/1.0.0",
        "configuration_hash": "sha256:config",
        "operating_environment": "cert-lab",
        "execution_mode": "paper",
        "deterministic": True,
    }
    data.update(overrides)
    return RuntimeIdentity(**data)


def chain(**overrides) -> ExecutionChain:
    data = {
        "repository": repository(),
        "candidate": candidate(),
        "build": build(),
        "runtime": runtime(),
        "bridge_certification_id": "BRIDGE-CERT-1",
        "execution_token_id": "TOKEN-1",
        "workflow_id": "WF-1",
        "infrastructure_evidence_id": "EVIDENCE-1",
        "infrastructure_proof_id": "PROOF-1",
        "certification_id": "CERT-1",
    }
    data.update(overrides)
    return ExecutionChain(**data)


def execution(**overrides) -> ExecutionIdentity:
    data = {
        "execution_id": "EXEC-1",
        "runtime_id": "RUNTIME-1",
        "workflow_id": "WF-1",
        "candidate_id": "CAND-1",
        "repository_id": "REPO-ARGOS",
        "build_id": "BUILD-1",
        "execution_token_id": "TOKEN-1",
        "certification_context_id": "CERT-CTX-1",
    }
    data.update(overrides)
    return ExecutionIdentity(**data)


def bridge(**overrides) -> BridgeDefinition:
    data = {
        "bridge_id": "BRIDGE-1",
        "source_component": "workflow-engine",
        "destination_component": "authority-service",
        "bridge_type": "authority_validation",
        "constitutional_objects": ("workflow_token", "authority_record"),
        "authority_requirements": ("AUTH-1",),
        "certification_status": "CERTIFIED",
        "version": "1",
        "evidence_package": "sha256:bridge",
        "approval_history": ("approved",),
        "certification_timestamp": "2026-07-20T12:03:00Z",
        "owner": "Infrastructure",
        "direction": BridgeDirection.UNIDIRECTIONAL,
    }
    data.update(overrides)
    return BridgeDefinition(**data)


def authority(**overrides) -> AuthorityDefinition:
    data = {
        "authority_id": "AUTH-1",
        "authority_name": "Workflow Authority Validation",
        "owner": "Infrastructure",
        "authorized_operations": ("validate_authority",),
        "required_preconditions": ("token_valid",),
        "revocation_conditions": ("token_corruption",),
        "certification_status": "CERTIFIED",
        "evidence": "sha256:authority",
        "version": "1",
    }
    data.update(overrides)
    return AuthorityDefinition(**data)


def graph() -> RuntimeInfrastructureGraph:
    return RuntimeInfrastructureGraph(
        services=("workflow-engine", "authority-service"),
        workers=(),
        queues=(),
        state_managers=(),
        repositories=(),
        event_infrastructure=(),
        audit_infrastructure=("audit-log",),
        storage_infrastructure=(),
        proof_infrastructure=("proof-engine",),
        recovery_infrastructure=(),
    )


def dependency(**overrides) -> RuntimeDependency:
    data = {
        "producer": "workflow-engine",
        "consumer": "authority-service",
        "bridge_id": "BRIDGE-1",
        "required_authority": "AUTH-1",
        "required_objects": ("workflow_token",),
        "certification_status": "CERTIFIED",
        "version": "1",
        "evidence": "sha256:dependency",
    }
    data.update(overrides)
    return RuntimeDependency(**data)


def certification_evidence() -> tuple[InfrastructureCertificationEvidence, ...]:
    records = []
    for phase in InfrastructureCertificationPhase:
        for category in InfrastructureTestCategory:
            records.append(
                InfrastructureCertificationEvidence(
                    evidence_id=f"EVIDENCE-{phase.name}-{category.name}",
                    phase=phase,
                    test_category=category,
                    immutable=True,
                    proof_id=f"PROOF-{phase.name}-{category.name}",
                    proof_reproducible=True,
                    fail_closed_exercised=True,
                    passed=True,
                )
            )
    return tuple(records)


class INF002ToINF005InfrastructureDoctrineTests(unittest.TestCase):
    def test_inf002_accepts_complete_immutable_execution_chain(self) -> None:
        record = InfrastructureTruthExecutionValidator().certify(chain(), execution())

        self.assertEqual(record.status, ExecutionTruthStatus.CONSTITUTIONALLY_VALID)
        self.assertEqual((), record.failures)
        self.assertTrue(record.chain_digest.startswith("sha256:"))

    def test_inf002_rejects_placeholder_inferred_and_non_reproducible_truth(self) -> None:
        broken = chain(
            candidate=candidate(candidate_id="placeholder", inferred=True),
            build=build(reproducible=False),
            runtime=runtime(deterministic=False),
            infrastructure_proof_id="unknown",
        )

        record = InfrastructureTruthExecutionValidator().certify(broken, execution(candidate_id="placeholder"))

        self.assertEqual(record.status, ExecutionTruthStatus.INVALID_FAIL_CLOSED)
        self.assertIn(ExecutionTruthFailure.PLACEHOLDER_IDENTIFIER, record.failures)
        self.assertIn(ExecutionTruthFailure.INFERRED_IDENTITY, record.failures)
        self.assertIn(ExecutionTruthFailure.NON_REPRODUCIBLE_BUILD, record.failures)
        self.assertIn(ExecutionTruthFailure.NON_DETERMINISTIC_RUNTIME, record.failures)
        self.assertIn(ExecutionTruthFailure.MISSING_CHAIN_LINK, record.failures)

    def test_inf003_certifies_canonical_bridge_authority_and_topology(self) -> None:
        record = InfrastructureAuthorityBridgeCertifier().certify((bridge(),), (authority(),), (dependency(),), graph())

        self.assertEqual(record.status, InfrastructureGraphStatus.CERTIFIED)
        self.assertEqual((), record.failures)

    def test_inf003_rejects_dynamic_direct_or_uncertified_dependencies(self) -> None:
        record = InfrastructureAuthorityBridgeCertifier().certify(
            (bridge(certification_status="REVOKED"),),
            (authority(certification_status="CERTIFIED"),),
            (dependency(dynamic=True, direct_communication=True, certification_status="PENDING"),),
            graph(),
        )

        self.assertEqual(record.status, InfrastructureGraphStatus.FAIL_CLOSED)
        self.assertIn(InfrastructureGraphFailure.UNCERTIFIED_BRIDGE, record.failures)
        self.assertIn(InfrastructureGraphFailure.UNCERTIFIED_DEPENDENCY, record.failures)
        self.assertIn(InfrastructureGraphFailure.DYNAMIC_DEPENDENCY, record.failures)
        self.assertIn(InfrastructureGraphFailure.DIRECT_COMMUNICATION, record.failures)

    def test_inf005_all_phases_and_categories_are_required_for_constitutional_certification(self) -> None:
        record = InfrastructureCertificationDoctrineEngine().certify(certification_evidence())

        self.assertEqual(record.state, InfrastructureCertificationLifecycleState.CONSTITUTIONALLY_CERTIFIED)
        self.assertTrue(record.operational_certification_allowed)
        self.assertFalse(record.dependent_operational_certifications_suspended)

    def test_inf005_rejects_partial_or_assumption_based_certification(self) -> None:
        evidence = tuple(
            item
            for item in certification_evidence()
            if item.phase != InfrastructureCertificationPhase.CONSTITUTIONAL_ACCEPTANCE
            and item.test_category != InfrastructureTestCategory.CROSS_OFFICE_DEPENDENCY
        )

        record = InfrastructureCertificationDoctrineEngine().certify(evidence, provisional_requested=True)

        self.assertEqual(record.state, InfrastructureCertificationLifecycleState.NOT_CERTIFIED)
        self.assertFalse(record.operational_certification_allowed)
        self.assertIn(InfrastructureCertificationFailure.MISSING_PHASE, record.failures)
        self.assertIn(InfrastructureCertificationFailure.MISSING_TEST_CATEGORY, record.failures)
        self.assertIn(InfrastructureCertificationFailure.PARTIAL_CERTIFICATION_ATTEMPT, record.failures)

    def test_inf005_revocation_suspends_dependent_operational_certification(self) -> None:
        record = InfrastructureCertificationDoctrineEngine().certify(
            certification_evidence(),
            discovered_violations=("runtime_nondeterminism",),
        )

        self.assertEqual(record.state, InfrastructureCertificationLifecycleState.CERTIFICATION_REVOKED)
        self.assertFalse(record.operational_certification_allowed)
        self.assertTrue(record.dependent_operational_certifications_suspended)
        self.assertIn(InfrastructureCertificationFailure.REVOCATION_TRIGGER, record.failures)


if __name__ == "__main__":
    unittest.main()
