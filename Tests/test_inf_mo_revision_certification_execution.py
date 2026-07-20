from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.infrastructure import (  # noqa: E402
    CertificationSessionInput,
    CertificationTimeoutRecord,
    EnduranceCycleRecord,
    INFMOFailure,
    INFMOStatus,
    InfrastructureCertificationExecutionEngine,
    InfrastructureTestRegistration,
    RepeatabilityRunRecord,
)


def test_registration(test_id: str, **overrides) -> InfrastructureTestRegistration:
    data = {
        "test_id": test_id,
        "category": "infrastructure",
        "executable": True,
        "disabled": False,
        "orphaned": False,
    }
    data.update(overrides)
    return InfrastructureTestRegistration(**data)


def endurance_cycle(**overrides) -> EnduranceCycleRecord:
    data = {
        "cycle_id": "END-1",
        "runtime_validated": True,
        "startup_validated": True,
        "shutdown_validated": True,
        "persistence_validated": True,
        "replay_validated": True,
        "workflow_validated": True,
        "authority_validated": True,
        "repository_validated": True,
        "evidence_hash": "sha256:endurance",
    }
    data.update(overrides)
    return EnduranceCycleRecord(**data)


def repeatability_run(run_id: str, **overrides) -> RepeatabilityRunRecord:
    data = {
        "run_id": run_id,
        "execution_order_hash": "sha256:order",
        "evidence_hash": "sha256:evidence",
        "candidate_hash": "sha256:candidate",
        "repository_hash": "sha256:repository",
        "persistence_hash": "sha256:persistence",
        "replay_hash": "sha256:replay",
        "authority_hash": "sha256:authority",
    }
    data.update(overrides)
    return RepeatabilityRunRecord(**data)


def pass_inputs(**overrides) -> dict[str, bool]:
    data = {name: True for name in InfrastructureCertificationExecutionEngine.required_pass_inputs}
    data.update(overrides)
    return data


def session(**overrides) -> CertificationSessionInput:
    expected = ("test_authority", "test_bridge", "test_persistence")
    data = {
        "session_id": "INF-MO-004-SESSION",
        "candidate_id": "CAND-INFMO-REV",
        "repository_id": "REPO-ARGOS",
        "certification_id": "CERT-INFMO-REV",
        "expected_tests": expected,
        "registered_tests": tuple(test_registration(test_id) for test_id in expected),
        "denominator_hash_before": "sha256:denominator",
        "denominator_hash_after": "sha256:denominator",
        "approved_concurrency": False,
        "execution_order": tuple(sorted(expected)),
        "timeout_records": (),
        "endurance_cycles": (endurance_cycle(),),
        "repeatability_runs": (repeatability_run("RUN-1"), repeatability_run("RUN-2")),
        "immutable_evidence_hash": "sha256:immutable-evidence",
        "audit_package_hash": "sha256:audit-package",
        "pass_inputs": pass_inputs(),
    }
    data.update(overrides)
    return CertificationSessionInput(**data)


class INFMORevisionCertificationExecutionTests(unittest.TestCase):
    def test_inf_mo004_certification_engine_passes_complete_deterministic_session(self) -> None:
        record = InfrastructureCertificationExecutionEngine().execute(session())

        self.assertEqual(record.status, INFMOStatus.PASS)
        self.assertEqual((), record.failures)
        self.assertEqual(("test_authority", "test_bridge", "test_persistence"), record.deterministic_order)
        self.assertTrue(record.result_digest.startswith("sha256:"))

    def test_inf_mo004_rejects_denominator_mutation_duplicate_disabled_orphan_tests(self) -> None:
        record = InfrastructureCertificationExecutionEngine().execute(
            session(
                registered_tests=(
                    test_registration("test_authority"),
                    test_registration("test_authority"),
                    test_registration("test_bridge", disabled=True),
                    test_registration("test_persistence", orphaned=True),
                ),
                denominator_hash_after="sha256:changed",
            )
        )

        self.assertEqual(record.status, INFMOStatus.FAIL_CLOSED)
        self.assertIn(INFMOFailure.DENOMINATOR_MUTATION, record.failures)
        self.assertIn(INFMOFailure.DUPLICATE_TEST, record.failures)
        self.assertIn(INFMOFailure.DISABLED_TEST, record.failures)
        self.assertIn(INFMOFailure.ORPHAN_TEST, record.failures)

    def test_inf_mo004_rejects_timeout_endurance_and_repeatability_uncertainty(self) -> None:
        record = InfrastructureCertificationExecutionEngine().execute(
            session(
                execution_order=("test_persistence", "test_bridge", "test_authority"),
                timeout_records=(
                    CertificationTimeoutRecord(
                        test_id="test_bridge",
                        elapsed_seconds=31.0,
                        configured_timeout_seconds=30.0,
                        system_state="collecting evidence",
                        candidate_id="CAND-INFMO-REV",
                        workflow_id="WF-INFMO",
                        stack_reference="sha256:stack",
                        failure_classification="Timeout Failure",
                    ),
                ),
                endurance_cycles=(endurance_cycle(replay_validated=False),),
                repeatability_runs=(repeatability_run("RUN-1"), repeatability_run("RUN-2", replay_hash="sha256:drift")),
                pass_inputs=pass_inputs(replay=False),
            )
        )

        self.assertEqual(record.status, INFMOStatus.FAIL_CLOSED)
        self.assertIn(INFMOFailure.NON_DETERMINISTIC_SCHEDULING, record.failures)
        self.assertIn(INFMOFailure.TIMEOUT_AMBIGUITY, record.failures)
        self.assertIn(INFMOFailure.ENDURANCE_FAILURE, record.failures)
        self.assertIn(INFMOFailure.REPEATABILITY_DIVERGENCE, record.failures)
        self.assertIn(INFMOFailure.UNRESOLVED_CERTIFICATION_FINDING, record.failures)


if __name__ == "__main__":
    unittest.main()
