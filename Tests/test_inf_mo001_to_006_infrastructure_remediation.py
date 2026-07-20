from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.infrastructure import (  # noqa: E402
    CanonicalBridgeAsset,
    CanonicalBridgeInfrastructureCertification,
    CheckpointCertificationRecord,
    INFMOFailure,
    INFMOStatus,
    ImmutableCandidateInfrastructure,
    ImmutableCandidateRecord,
    InfrastructureConstitutionalCertificationEngine,
    InfrastructureConstitutionalCertificationPackage,
    InfrastructurePersistenceReplayCertifier,
    InfrastructureSyntheticTruthEliminator,
    InfrastructureVerificationCompletionEngine,
    RecoveryReplayRecord,
    TruthFlowRecord,
    VerificationActivity,
    VerificationOutcome,
)


def candidate(**overrides) -> ImmutableCandidateRecord:
    data = {
        "candidate_id": "CAND-INFMO",
        "repository_commit": "0f26549826be2ea010b3d44d285c93843a98f81c",
        "repository_tree": "tree-1",
        "dependency_fingerprint": "deps-1",
        "doctrine_fingerprint": "doctrine-1",
        "schema_fingerprint": "schema-1",
        "bridge_fingerprint": "bridge-1",
        "runtime_fingerprint": "runtime-1",
        "certification_timestamp": "2026-07-20T12:00:00Z",
        "candidate_sequence_id": "SEQ-1",
        "snapshot_fingerprint": "sha256:snapshot",
        "workspace_fingerprint": "sha256:workspace",
        "manifest_fingerprint": "sha256:manifest",
        "provenance_fingerprint": "sha256:provenance",
        "repository_clean": True,
        "staged_changes": False,
        "unstaged_changes": False,
        "untracked_constitutional_files": False,
        "hermetic_workspace": True,
        "evidence_candidate_ids": ("CAND-INFMO",),
        "reproducible_inputs": True,
        "immutable": True,
    }
    data.update(overrides)
    return ImmutableCandidateRecord(**data)


def bridge(**overrides) -> CanonicalBridgeAsset:
    data = {
        "bridge_id": "BR-INFMO",
        "source_component": "candidate-service",
        "destination_component": "certification-service",
        "bridge_owner": "Infrastructure",
        "authority_owner": "Infrastructure",
        "schema_version": "1",
        "dependency_classification": "mandatory",
        "runtime_direction": "unidirectional",
        "certification_state": "CERTIFIED",
        "schema_certified": True,
        "dependencies_certified": True,
        "traversal_evidence": "sha256:traversal",
    }
    data.update(overrides)
    return CanonicalBridgeAsset(**data)


def truth_flow(**overrides) -> TruthFlowRecord:
    data = {
        "datum_id": "DATUM-1",
        "candidate_id": "CAND-INFMO",
        "source_id": "candidate-service",
        "destination_id": "certification-service",
        "bridge_id": "BR-INFMO",
        "authority_id": "AUTH-INFMO",
        "source_hash": "sha256:value",
        "transport_hash": "sha256:value",
        "persistence_hash": "sha256:value",
        "delivery_hash": "sha256:value",
        "cache_fresh": True,
        "cache_authoritative": False,
        "fallback_used": False,
        "synthetic_indicator": False,
        "transformation_authorized": True,
        "recovery_reconstructed": False,
        "evidence_hash": "sha256:evidence",
    }
    data.update(overrides)
    return TruthFlowRecord(**data)


def checkpoint(**overrides) -> CheckpointCertificationRecord:
    data = {
        "checkpoint_id": "CHK-INFMO",
        "immutable": True,
        "certified": True,
        "integrity_verified": True,
        "completeness_verified": True,
        "schema_compatible": True,
        "bridge_compatible": True,
        "workflow_consistent": True,
        "authority_consistent": True,
        "candidate_id": "CAND-INFMO",
        "evidence_complete": True,
    }
    data.update(overrides)
    return CheckpointCertificationRecord(**data)


def recovery(**overrides) -> RecoveryReplayRecord:
    data = {
        "checkpoint": checkpoint(),
        "restored_objects": ("workflow_token", "authority", "audit_ledger"),
        "required_objects": ("workflow_token", "authority", "audit_ledger"),
        "authority_unchanged": True,
        "ledger_continuous": True,
        "replay_isolated": True,
        "replay_hashes": ("sha256:replay", "sha256:replay"),
        "production_mutation_attempted": False,
        "recovery_evidence": "sha256:recovery",
        "replay_evidence": "sha256:replay-evidence",
    }
    data.update(overrides)
    return RecoveryReplayRecord(**data)


def verification_activities() -> tuple[VerificationActivity, ...]:
    return tuple(
        VerificationActivity(
            activity_id=f"VER-{category}",
            category=category,
            outcome=VerificationOutcome.PASS,
            deterministic=True,
            timeout_defined=True,
            evidence_hash=f"sha256:{category}",
            traceability_refs=(f"INF-VC-{category}",),
        )
        for category in InfrastructureVerificationCompletionEngine.required_categories
    )


def final_package(**overrides) -> InfrastructureConstitutionalCertificationPackage:
    data = {
        "candidate": ImmutableCandidateInfrastructure().certify(candidate()),
        "bridges": CanonicalBridgeInfrastructureCertification().certify(
            (bridge(),),
            ("candidate-service", "certification-service"),
        ),
        "synthetic_truth": InfrastructureSyntheticTruthEliminator().certify((truth_flow(),)),
        "persistence_replay": InfrastructurePersistenceReplayCertifier().certify(recovery()),
        "verification": InfrastructureVerificationCompletionEngine().certify(verification_activities()),
        "category_reports": {
            "authority": "sha256:authority-report",
            "runtime": "sha256:runtime-report",
            "canonical_bridge": "sha256:bridge-report",
            "persistence": "sha256:persistence-report",
            "replay": "sha256:replay-report",
            "synthetic_truth": "sha256:synthetic-report",
            "certification_integrity": "sha256:cert-report",
            "pass_checklist": "sha256:pass-checklist",
        },
        "unresolved_findings": (),
        "freeze_declaration": "INFRASTRUCTURE-FREEZE-DECLARED",
        "sentinel_authorization": "SENTINEL-CERTIFICATION-AUTHORIZED",
    }
    data.update(overrides)
    return InfrastructureConstitutionalCertificationPackage(**data)


class INFMO001To006InfrastructureRemediationTests(unittest.TestCase):
    def test_inf_mo001_certifies_immutable_candidate_and_rejects_mixed_candidate(self) -> None:
        passed = ImmutableCandidateInfrastructure().certify(candidate())
        failed = ImmutableCandidateInfrastructure().certify(candidate(evidence_candidate_ids=("CAND-INFMO", "OTHER"), immutable=False))

        self.assertEqual(passed.status, INFMOStatus.PASS)
        self.assertEqual(failed.status, INFMOStatus.FAIL_CLOSED)
        self.assertIn(INFMOFailure.MIXED_CANDIDATE, failed.failures)
        self.assertIn(INFMOFailure.MUTABLE_REPOSITORY, failed.failures)

    def test_inf_mo002_rejects_uncertified_unauthorized_and_orphan_bridge_assets(self) -> None:
        record = CanonicalBridgeInfrastructureCertification().certify(
            (bridge(certification_state="PENDING", unauthorized_path=True),),
            ("candidate-service", "certification-service", "orphan-service"),
        )

        self.assertEqual(record.status, INFMOStatus.FAIL_CLOSED)
        self.assertIn(INFMOFailure.UNCERTIFIED_BRIDGE_ASSET, record.failures)
        self.assertIn(INFMOFailure.UNAUTHORIZED_BRIDGE_PATH, record.failures)
        self.assertIn(INFMOFailure.ORPHAN_INFRASTRUCTURE_COMPONENT, record.failures)

    def test_inf_mo003_rejects_fallback_cache_authority_and_reconstructed_truth(self) -> None:
        record = InfrastructureSyntheticTruthEliminator().certify(
            (truth_flow(cache_fresh=False, cache_authoritative=True, fallback_used=True, recovery_reconstructed=True),)
        )

        self.assertEqual(record.status, INFMOStatus.FAIL_CLOSED)
        self.assertIn(INFMOFailure.FALLBACK_VALUE, record.failures)
        self.assertIn(INFMOFailure.CACHE_AUTHORITY, record.failures)
        self.assertIn(INFMOFailure.RECOVERY_RECONSTRUCTION, record.failures)

    def test_inf_mo004_certifies_persistence_replay_and_rejects_contamination(self) -> None:
        passed = InfrastructurePersistenceReplayCertifier().certify(recovery())
        failed = InfrastructurePersistenceReplayCertifier().certify(
            recovery(
                authority_unchanged=False,
                ledger_continuous=False,
                production_mutation_attempted=True,
                replay_hashes=("sha256:left", "sha256:right"),
            )
        )

        self.assertEqual(passed.status, INFMOStatus.PASS)
        self.assertEqual(failed.status, INFMOStatus.FAIL_CLOSED)
        self.assertIn(INFMOFailure.AUTHORITY_MUTATION_DURING_RECOVERY, failed.failures)
        self.assertIn(INFMOFailure.LEDGER_DISCONTINUITY, failed.failures)
        self.assertIn(INFMOFailure.REPLAY_CONTAMINATION, failed.failures)
        self.assertIn(INFMOFailure.REPLAY_NONDETERMINISM, failed.failures)

    def test_inf_mo005_requires_full_denominator_without_skips_or_unknowns(self) -> None:
        activities = verification_activities()
        passed = InfrastructureVerificationCompletionEngine().certify(activities)
        failed = InfrastructureVerificationCompletionEngine().certify(
            activities[:-1]
            + (
                VerificationActivity(
                    activity_id="VER-SKIP",
                    category="failure",
                    outcome=VerificationOutcome.SKIPPED,
                    deterministic=False,
                    timeout_defined=False,
                    evidence_hash="",
                    traceability_refs=(),
                ),
            )
        )

        self.assertEqual(passed.status, INFMOStatus.PASS)
        self.assertTrue(passed.operational_readiness)
        self.assertEqual(failed.status, INFMOStatus.FAIL_CLOSED)
        self.assertIn(INFMOFailure.SKIPPED_VERIFICATION, failed.failures)
        self.assertIn(INFMOFailure.TIMEOUT_AMBIGUITY, failed.failures)
        self.assertIn(INFMOFailure.MISSING_TRACEABILITY, failed.failures)

    def test_inf_mo006_final_pass_enters_freeze_and_authorizes_sentinel(self) -> None:
        record = InfrastructureConstitutionalCertificationEngine().certify(final_package())

        self.assertEqual(record.status, INFMOStatus.CONSTITUTIONAL_FREEZE)
        self.assertTrue(record.sentinel_certification_authorized)
        self.assertTrue(record.package_digest.startswith("sha256:"))

    def test_inf_mo006_rejects_unresolved_findings_and_missing_authorization(self) -> None:
        record = InfrastructureConstitutionalCertificationEngine().certify(
            final_package(unresolved_findings=("bridge finding",), sentinel_authorization="")
        )

        self.assertEqual(record.status, INFMOStatus.FAIL_CLOSED)
        self.assertFalse(record.sentinel_certification_authorized)
        self.assertIn(INFMOFailure.UNRESOLVED_CERTIFICATION_FINDING, record.failures)
        self.assertIn(INFMOFailure.MISSING_SENTINEL_AUTHORIZATION, record.failures)


if __name__ == "__main__":
    unittest.main()
