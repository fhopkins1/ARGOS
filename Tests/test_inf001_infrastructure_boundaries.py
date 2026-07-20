from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.infrastructure import (  # noqa: E402
    ConstitutionalLayer,
    InfrastructureAuthorityDomain,
    InfrastructureBoundaryRegistry,
    InfrastructureBoundaryValidator,
    InfrastructureCertificationPrerequisite,
    InfrastructureCertificationState,
    InfrastructureDependencyEdge,
    InfrastructureFailureReason,
    InfrastructureNonAuthority,
    InfrastructurePrerequisiteEvidence,
    InfrastructureServiceDeclaration,
    InfrastructureServiceType,
    InterfaceAccessRequest,
    InterfaceTarget,
    default_infrastructure_boundary,
)


def prerequisite(prerequisite_id: InfrastructureCertificationPrerequisite, satisfied: bool = True) -> InfrastructurePrerequisiteEvidence:
    return InfrastructurePrerequisiteEvidence(
        prerequisite=prerequisite_id,
        satisfied=satisfied,
        evidence_reference=f"sha256:{prerequisite_id.value}",
        certified_by="INF-001-TEST",
        checked_at="2026-07-20T12:00:00Z",
    )


def all_prerequisites() -> tuple[InfrastructurePrerequisiteEvidence, ...]:
    return tuple(prerequisite(item) for item in InfrastructureCertificationPrerequisite)


def infrastructure_service(**overrides) -> InfrastructureServiceDeclaration:
    data = {
        "service_id": "INF-SVC-1",
        "service_type": InfrastructureServiceType.IDENTITY_SERVICES,
        "authority_domain": InfrastructureAuthorityDomain.REPOSITORY_IDENTITY,
        "exposed_interface": "INF-CERT-REPOSITORY-REGISTRY",
        "evidence_references": ("sha256:service",),
    }
    data.update(overrides)
    return InfrastructureServiceDeclaration(**data)


def lawful_dependencies() -> tuple[InfrastructureDependencyEdge, ...]:
    return (
        InfrastructureDependencyEdge(
            edge_id="DEP-1",
            upstream=ConstitutionalLayer.CONSTITUTIONAL_DOCTRINE,
            downstream=ConstitutionalLayer.INFRASTRUCTURE_OFFICE,
            evidence_reference="sha256:dep-1",
        ),
        InfrastructureDependencyEdge(
            edge_id="DEP-2",
            upstream=ConstitutionalLayer.INFRASTRUCTURE_OFFICE,
            downstream=ConstitutionalLayer.SHARED_CONSTITUTIONAL_SERVICES,
            evidence_reference="sha256:dep-2",
        ),
        InfrastructureDependencyEdge(
            edge_id="DEP-3",
            upstream=ConstitutionalLayer.SHARED_CONSTITUTIONAL_SERVICES,
            downstream=ConstitutionalLayer.OPERATIONAL_OFFICES,
            evidence_reference="sha256:dep-3",
        ),
        InfrastructureDependencyEdge(
            edge_id="DEP-4",
            upstream=ConstitutionalLayer.OPERATIONAL_OFFICES,
            downstream=ConstitutionalLayer.ENTERPRISE_WORKFLOWS,
            evidence_reference="sha256:dep-4",
        ),
    )


class INF001InfrastructureBoundariesTests(unittest.TestCase):
    def test_boundary_exhaustively_defines_authority_and_non_authority(self) -> None:
        boundary = default_infrastructure_boundary()

        self.assertEqual(set(boundary.authority_domains), set(InfrastructureAuthorityDomain))
        self.assertEqual(set(boundary.non_authorities), set(InfrastructureNonAuthority))
        self.assertIn(InfrastructureAuthorityDomain.BRIDGE_CERTIFICATION, boundary.authority_domains)
        self.assertIn(InfrastructureAuthorityDomain.LAW_VII_ENFORCEMENT_INFRASTRUCTURE, boundary.authority_domains)
        self.assertIn(InfrastructureNonAuthority.TRADE_APPROVAL, boundary.non_authorities)
        self.assertIn(InfrastructureNonAuthority.RISK_CALCULATION, boundary.non_authorities)
        self.assertIn(InfrastructureNonAuthority.HISTORICAL_TRUTH_MODIFICATION, boundary.non_authorities)

    def test_operational_logic_in_infrastructure_service_fails_closed(self) -> None:
        validator = InfrastructureBoundaryValidator()
        service = infrastructure_service(
            contains_operational_logic=True,
            performs_operational_decision=True,
            asserted_non_authorities=(InfrastructureNonAuthority.TRADE_APPROVAL,),
        )

        record = validator.certify(all_prerequisites(), (service,), lawful_dependencies())

        self.assertEqual(record.state, InfrastructureCertificationState.SUSPENDED_DOWNSTREAM_CERTIFICATION)
        self.assertFalse(record.downstream_certification_allowed)
        self.assertIn(InfrastructureFailureReason.OPERATIONAL_LOGIC_PRESENT, record.failure_reasons)
        self.assertIn(InfrastructureFailureReason.OPERATIONAL_DECISION_PRESENT, record.failure_reasons)
        self.assertIn(InfrastructureFailureReason.NON_AUTHORITY_DECLARED, record.failure_reasons)

    def test_all_prerequisites_are_required_before_downstream_certification(self) -> None:
        validator = InfrastructureBoundaryValidator()
        evidence = tuple(
            prerequisite(item, item != InfrastructureCertificationPrerequisite.PROOF_INFRASTRUCTURE_CERTIFIED)
            for item in InfrastructureCertificationPrerequisite
        )

        record = validator.certify(evidence, (infrastructure_service(),), lawful_dependencies())

        self.assertEqual(record.state, InfrastructureCertificationState.SUSPENDED_DOWNSTREAM_CERTIFICATION)
        self.assertFalse(record.downstream_certification_allowed)
        self.assertIn(InfrastructureFailureReason.EVIDENCE_INCOMPLETE, record.failure_reasons)
        self.assertIn(InfrastructureFailureReason.PROOF_GENERATION_FAILED, record.failure_reasons)

    def test_valid_infrastructure_certification_allows_downstream_certification(self) -> None:
        validator = InfrastructureBoundaryValidator()
        service = infrastructure_service(service_id="INF-SVC-PROOF", service_type=InfrastructureServiceType.PROOF_SERVICES)

        record = validator.certify(all_prerequisites(), (service,), lawful_dependencies())

        self.assertEqual(record.state, InfrastructureCertificationState.PASS)
        self.assertTrue(record.downstream_certification_allowed)
        self.assertEqual((), record.failure_reasons)
        self.assertTrue(record.record_digest.startswith("sha256:"))

    def test_reverse_and_circular_dependencies_are_rejected(self) -> None:
        validator = InfrastructureBoundaryValidator()
        dependencies = (
            InfrastructureDependencyEdge(
                edge_id="BAD-1",
                upstream=ConstitutionalLayer.OPERATIONAL_OFFICES,
                downstream=ConstitutionalLayer.INFRASTRUCTURE_OFFICE,
                evidence_reference="sha256:bad-1",
            ),
            InfrastructureDependencyEdge(
                edge_id="BAD-2",
                upstream=ConstitutionalLayer.INFRASTRUCTURE_OFFICE,
                downstream=ConstitutionalLayer.OPERATIONAL_OFFICES,
                evidence_reference="sha256:bad-2",
            ),
        )

        record = validator.certify(all_prerequisites(), (infrastructure_service(),), dependencies)

        self.assertEqual(record.state, InfrastructureCertificationState.SUSPENDED_DOWNSTREAM_CERTIFICATION)
        self.assertIn(InfrastructureFailureReason.REVERSE_DEPENDENCY, record.failure_reasons)
        self.assertIn(InfrastructureFailureReason.DEPENDENCY_CYCLE, record.failure_reasons)

    def test_operational_offices_must_use_certified_interfaces(self) -> None:
        validator = InfrastructureBoundaryValidator()
        direct_access = InterfaceAccessRequest(
            requesting_layer=ConstitutionalLayer.OPERATIONAL_OFFICES,
            target=InterfaceTarget.BRIDGE_REGISTRY,
            interface_id="INF-CERT-BRIDGE-REGISTRY",
            direct_internal_access=True,
        )
        undocumented_access = InterfaceAccessRequest(
            requesting_layer=ConstitutionalLayer.OPERATIONAL_OFFICES,
            target=InterfaceTarget.AUTHORITY_REGISTRY,
            interface_id="RAW-AUTHORITY-TABLE",
            direct_internal_access=False,
        )

        record = validator.certify(
            all_prerequisites(),
            (infrastructure_service(),),
            lawful_dependencies(),
            (direct_access, undocumented_access),
        )

        self.assertEqual(record.state, InfrastructureCertificationState.SUSPENDED_DOWNSTREAM_CERTIFICATION)
        self.assertIn(InfrastructureFailureReason.DIRECT_INTERFACE_ACCESS, record.failure_reasons)
        self.assertIn(InfrastructureFailureReason.UNDOCUMENTED_INTERFACE, record.failure_reasons)

    def test_boundary_registry_exposes_only_certified_interface_targets(self) -> None:
        registry = InfrastructureBoundaryRegistry()

        self.assertEqual(registry.certified_interfaces["INF-CERT-RUNTIME-INTERNALS"], InterfaceTarget.RUNTIME_INTERNALS)
        self.assertEqual(registry.certified_interfaces["INF-CERT-REPLAY-ENGINE"], InterfaceTarget.REPLAY_ENGINE)
        with self.assertRaises(TypeError):
            registry.certified_interfaces["UNDECLARED"] = InterfaceTarget.AUDIT_REGISTRY


if __name__ == "__main__":
    unittest.main()
