from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.sentinel import (  # noqa: E402
    BridgeCertificationState,
    BridgeClass,
    BridgeGovernanceEngine,
    BridgeInvocationRequest,
    BridgeRejectionCode,
    CanonicalBridgeRecord,
    CanonicalBridgeRegistry,
    CertificationCandidate,
    CertificationVerdict,
    GovernanceDecision,
    IndependentCertificationAuthority,
    OperatingMode,
    RegistryVersion,
    SourceProvenance,
    TransformationLineage,
    TruthClassification,
    TruthDomain,
    TruthFailure,
    TruthGovernanceEngine,
    TruthRecord,
    WorkflowTokenEvidence,
)


def registry() -> CanonicalBridgeRegistry:
    bridge = CanonicalBridgeRecord(
        bridge_id="SENTINEL-COMMANDER-BRIDGE",
        bridge_name="Sentinel to Commander Notification Bridge",
        bridge_class=BridgeClass.NOTIFICATION,
        source="Sentinel",
        destination="Commander",
        governing_doctrine="SENT-GOV-019",
        governing_modification_order="SENT-MO-002",
        transferred_object_types=("CommanderNotification", "ObservationEvidence"),
        transferred_authority="notification_only",
        permitted_workflow_states=("OBSERVED", "EVIDENCE_READY"),
        permitted_operating_modes=(OperatingMode.PAPER_OBSERVED, OperatingMode.DEGRADED_NO_MARKET_TRUTH),
        workflow_token_required=True,
        rejection_conditions=tuple(BridgeRejectionCode),
        evidence_requirements=("bridge_trace", "workflow_token", "authority", "rejection_record"),
        certification_requirements=("registry_validity", "authority", "token_continuity", "negative_tests"),
        certification_state=BridgeCertificationState.CERTIFIED,
        production_eligible=True,
        version_id="bridge/1.0.0",
        immutable_content_hash="sha256:bridge",
    )
    version = RegistryVersion(
        registry_id="sentinel-bridge-registry",
        version_id="bridge-registry/1.0.0",
        governing_doctrine="SENT-GOV-019",
        creation_timestamp="2026-07-20T12:00:00Z",
        schema_version="1.0.0",
        supersedes=None,
        content_hash="sha256:registry",
    )
    return CanonicalBridgeRegistry(version, (bridge,))


def token(**overrides) -> WorkflowTokenEvidence:
    data = {
        "token_id": "TOKEN-1",
        "workflow_id": "WF-1",
        "current_owner": "Sentinel",
        "next_owner": "Commander",
        "authentic": True,
    }
    data.update(overrides)
    return WorkflowTokenEvidence(**data)


def invocation(**overrides) -> BridgeInvocationRequest:
    data = {
        "bridge_id": "SENTINEL-COMMANDER-BRIDGE",
        "workflow_id": "WF-1",
        "source": "Sentinel",
        "destination": "Commander",
        "operating_mode": OperatingMode.PAPER_OBSERVED,
        "transferred_object_type": "CommanderNotification",
        "transferred_object_id": "OBS-1",
        "input_hash": "sha256:input",
        "output_hash": "sha256:output",
        "invocation_timestamp": "2026-07-20T12:00:01Z",
        "completion_timestamp": "2026-07-20T12:00:02Z",
        "sequence_number": 1,
        "candidate_identity": "commit:abc",
        "workflow_token": token(),
    }
    data.update(overrides)
    return BridgeInvocationRequest(**data)


def provenance(**overrides) -> SourceProvenance:
    data = {
        "source_id": "SRC-AUTH",
        "provider_id": "approved-provider",
        "source_authority": True,
        "acquisition_method": "approved_poll",
        "request_id": "REQ-1",
        "response_id": "RESP-1",
        "source_timestamp": "2026-07-20T12:00:00Z",
        "receipt_timestamp": "2026-07-20T12:00:01Z",
        "effective_timestamp": "2026-07-20T12:00:00Z",
        "raw_payload_hash": "sha256:raw",
        "chain_of_custody": ("sha256:raw",),
    }
    data.update(overrides)
    return SourceProvenance(**data)


def truth_record(**overrides) -> TruthRecord:
    data = {
        "record_id": "TRUTH-1",
        "record_version": "1",
        "subject_identity": "SPY",
        "value_hash": "sha256:value",
        "primary_classification": TruthClassification.OBSERVED,
        "operating_mode": OperatingMode.PAPER_OBSERVED,
        "truth_domain": TruthDomain.CURRENT_OBSERVED_PAPER,
        "source_id": "SRC-AUTH",
        "freshness_status": "CURRENT",
        "provenance": provenance(),
        "transformation_lineage": None,
        "parent_record_ids": (),
        "workflow_id": "WF-1",
        "office_id": "Sentinel",
        "bridge_id": "SENTINEL-COMMANDER-BRIDGE",
        "conflict_status": "NONE",
        "independence_status": "PROVEN",
        "recovery_status": "ORIGINAL",
        "reconstruction_status": "NONE",
        "quarantine_status": "CLEAR",
        "integrity_evidence": "sha256:integrity",
        "persistence_evidence": "sha256:persistence",
        "certification_eligible": True,
        "learning_eligible": False,
        "performance_eligible": True,
    }
    data.update(overrides)
    return TruthRecord(**data)


def candidate(**overrides) -> CertificationCandidate:
    data = {
        "repository_revision": "commit:abc",
        "doctrine_revision": "sentinel-doctrine/1",
        "configuration_hash": "sha256:config",
        "dependency_hash": "sha256:deps",
        "requirement_registry_hash": "sha256:req",
        "evidence_registry_hash": "sha256:evidence-reg",
        "evidence_package_hash": "sha256:package",
        "execution_environment_hash": "sha256:env",
        "certification_scope": ("deterministic observation", "Commander-first notification"),
        "excluded_scope": ("live brokerage",),
        "requirement_results": {"SENT-GOV-019": True, "SENT-GOV-020": True, "SENT-GOV-021": True},
        "evidence_results": {"bridge_evidence": True, "truth_evidence": True, "verdict_record": True},
        "deterministic_rerun": True,
        "repository_integrity_verified": True,
        "audit_independent": True,
        "implementation_self_certified": False,
    }
    data.update(overrides)
    return CertificationCandidate(**data)


class SentinelGovernanceTests(unittest.TestCase):
    def test_bridge_registry_hash_and_discovery_are_deterministic(self) -> None:
        reg = registry()
        replay = registry()
        report = reg.discovered_call_path_report(("SENTINEL-COMMANDER-BRIDGE", "BYPASS-PATH"))

        self.assertEqual(reg.registry_hash, replay.registry_hash)
        self.assertEqual(report["matched_declared_bridge"], ("SENTINEL-COMMANDER-BRIDGE",))
        self.assertEqual(report["undeclared_call_path"], ("BYPASS-PATH",))

    def test_bridge_invocation_enforces_authority_token_and_duplicate_evidence(self) -> None:
        engine = BridgeGovernanceEngine(registry(), "commit:abc")
        passed = engine.invoke(invocation())
        duplicate = engine.invoke(invocation(sequence_number=2))
        rejected = engine.invoke(
            invocation(
                transferred_object_id="OBS-2",
                source="Risk",
                workflow_token=token(current_owner="Risk", stale=True),
            )
        )

        self.assertEqual(passed.decision, GovernanceDecision.PASS)
        self.assertEqual(duplicate.decision, GovernanceDecision.FAIL_CLOSED)
        self.assertIn(BridgeRejectionCode.DUPLICATE_MUTATION_PREVENTED, duplicate.rejection_codes)
        self.assertIn(BridgeRejectionCode.SOURCE_UNAUTHORIZED, rejected.rejection_codes)
        self.assertIn(BridgeRejectionCode.WORKFLOW_TOKEN_STALE, rejected.rejection_codes)
        self.assertEqual(3, len(engine.evidence))
        self.assertTrue(all(item.evidence_hash.startswith("sha256:") for item in engine.evidence))

    def test_bridge_certification_is_conjunctive_and_blocks_self_attestation(self) -> None:
        engine = BridgeGovernanceEngine(registry(), "commit:abc")
        mandatory = ("registry_validity", "authority", "token_continuity", "negative_tests")
        passed = engine.certify_bridge("SENTINEL-COMMANDER-BRIDGE", {item: True for item in mandatory}, mandatory, True, True, True)
        failed = engine.certify_bridge(
            "SENTINEL-COMMANDER-BRIDGE",
            {"registry_validity": True, "authority": False, "token_continuity": True, "negative_tests": True},
            mandatory,
            negative_tests_complete=False,
            restart_tests_complete=True,
            recovery_tests_complete=True,
            self_attested=True,
        )

        self.assertEqual(passed.state.name, "CERTIFIED")
        self.assertEqual(failed.decision, GovernanceDecision.FAIL_CLOSED)
        self.assertIn("authority", failed.failed_dimensions)
        self.assertIn("negative_tests_incomplete", failed.failed_dimensions)
        self.assertIn("self_attestation_prohibited", failed.failed_dimensions)

    def test_truth_governance_rejects_synthetic_promotion_and_domain_contamination(self) -> None:
        engine = TruthGovernanceEngine({TruthDomain.CURRENT_OBSERVED_PAPER: ("SRC-AUTH",)})
        valid = engine.validate(truth_record())
        contaminated = engine.validate(
            truth_record(
                primary_classification=TruthClassification.SYNTHETIC,
                truth_domain=TruthDomain.CURRENT_OBSERVED_PAPER,
                certification_eligible=False,
            )
        )
        transition = engine.classify_transition(TruthClassification.SYNTHETIC, TruthClassification.OBSERVED, True)

        self.assertEqual(valid.decision, GovernanceDecision.PASS)
        self.assertEqual(contaminated.decision, GovernanceDecision.FAIL_CLOSED)
        self.assertIn(TruthFailure.SYNTHETIC_PROMOTION_ATTEMPT, contaminated.failures)
        self.assertIn(TruthFailure.SYNTHETIC_PROMOTION_ATTEMPT, transition.failures)

    def test_truth_governance_requires_lineage_and_quarantines_corruption(self) -> None:
        engine = TruthGovernanceEngine({TruthDomain.CURRENT_OBSERVED_PAPER: ("SRC-AUTH",)})
        derived = truth_record(
            primary_classification=TruthClassification.DERIVED,
            transformation_lineage=TransformationLineage(
                transformation_id="NORMALIZE",
                transformation_version="1",
                input_record_ids=("TRUTH-0",),
                input_truth_classes=(TruthClassification.OBSERVED,),
                parameters_hash="sha256:params",
                output_hash="sha256:derived",
                reproducible=False,
            ),
            integrity_evidence="",
        )

        result = engine.validate(derived)

        self.assertEqual(result.decision, GovernanceDecision.FAIL_CLOSED)
        self.assertTrue(result.quarantine_required)
        self.assertIn(TruthFailure.LINEAGE_MISSING, result.failures)
        self.assertIn(TruthFailure.CORRUPTED_EVIDENCE, result.failures)

    def test_independent_certification_verdicts_are_deterministic_and_fail_closed(self) -> None:
        authority = IndependentCertificationAuthority()
        passed = authority.assess(candidate())
        failed = authority.assess(candidate(requirement_results={"SENT-GOV-019": False}))
        indeterminate = authority.assess(candidate(evidence_results={"bridge_evidence": False}))
        invalid = authority.assess(candidate(repository_revision="", implementation_self_certified=True))

        self.assertEqual(passed.verdict, CertificationVerdict.PASS)
        self.assertEqual(failed.verdict, CertificationVerdict.FAIL)
        self.assertEqual(indeterminate.verdict, CertificationVerdict.INDETERMINATE)
        self.assertEqual(invalid.verdict, CertificationVerdict.INVALID_AUDIT)
        self.assertEqual(passed.certification_record_hash, authority.assess(candidate()).certification_record_hash)


if __name__ == "__main__":
    unittest.main()
