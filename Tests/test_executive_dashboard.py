from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.executive import (  # noqa: E402
    CHIEF_OF_STAFF_ID,
    ChiefOfStaffService,
    CommanderDecision,
    CommanderDecisionEngine,
    CommanderOffice,
    ExecutiveBriefingPacket,
    ExecutiveDashboard,
    ExecutiveDocumentManifest,
)
from argos.foundation.audit import AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptPassport, PromptRepository  # noqa: E402


HASH_A = "a" * 64
HASH_B = "b" * 64


def configuration_service() -> ConfigurationService:
    return ConfigurationService.load(
        {
            "environment": "development",
            "config_version": "1.0.0",
            "schema_version": "1.0.0",
            "log_level": "INFO",
            "live_trading_enabled": False,
            "feature_flags": {},
            "secret_references": [],
        },
        {},
    )


def prompt_repository() -> PromptRepository:
    repository = PromptRepository()
    repository.register(
        PromptPassport(
            prompt_id="PROMPT-015",
            title="Dashboard Fixture Prompt",
            owner_group_id="DEP-002",
            author_staff_id="STF-002",
            purpose="Support dashboard fixture decisions.",
            allowed_environments=("development",),
            input_contract_types=("EBP",),
            output_contract_types=("CDR",),
            dependencies=("EO-015",),
            safety_notes="No trading authority.",
        ),
        "1.0.0",
        "Use validated packets only.",
    )
    return repository


def packet(ebp_id: str = "EBP-301", evidence=("DOC-311", "DOC-312")) -> ExecutiveBriefingPacket:
    return ExecutiveBriefingPacket(
        ebp_id=ebp_id,
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        produced_by_staff_id=CHIEF_OF_STAFF_ID,
        produced_by_group_id="DEP-002",
        risk_recommendation_document_id="DOC-310",
        evidence_reference_ids=evidence,
        summary="Dashboard packet.",
        recommended_action="approve",
        document_signature_hash=HASH_A,
        configuration_snapshot_hash=HASH_B,
        prompt_snapshot_id="PS-000001",
        model_snapshot_id="MS-000001",
    )


def manifests() -> dict[str, ExecutiveDocumentManifest]:
    return {
        "DOC-310": ExecutiveDocumentManifest("DOC-310", "risk", HASH_A, HASH_B, 1),
        "DOC-311": ExecutiveDocumentManifest("DOC-311", "evidence", HASH_A, HASH_B, 1, "trend", "positive"),
        "DOC-312": ExecutiveDocumentManifest("DOC-312", "evidence", HASH_A, HASH_B, 1, "liquidity", "adequate"),
    }


def dashboard_fixture() -> ExecutiveDashboard:
    config = configuration_service()
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    audit = AuditService()
    office = CommanderOffice(config, persistence, audit_service=audit)
    engine = CommanderDecisionEngine(office, prompt_repository(), "PROMPT-015")
    chief = ChiefOfStaffService(engine, config, persistence, audit)

    chief.process_packet(
        packet(),
        manifests(),
        CommanderDecision.APPROVE,
        "Accepted dashboard fixture.",
        91,
        "DEP-005",
        IncomingMailbox("STF-005", "DEP-005"),
    )
    bad_packet = packet("EBP-302", evidence=("DOC-311",))
    chief.process_packet(
        bad_packet,
        {"DOC-310": manifests()["DOC-310"]},
        CommanderDecision.REJECT,
        "Rejected dashboard fixture.",
        92,
        "DEP-005",
        IncomingMailbox("STF-005", "DEP-005"),
    )
    return ExecutiveDashboard(office, chief, persistence, audit)


class ExecutiveDashboardTests(unittest.TestCase):
    def test_dashboard_refresh_projects_current_state(self) -> None:
        dashboard = dashboard_fixture()

        snapshot = dashboard.refresh()

        self.assertEqual(snapshot.refresh_sequence, 1)
        self.assertEqual(snapshot.executive_clock.value, 2)
        self.assertEqual(len(snapshot.pending_packets), 1)
        self.assertEqual(len(snapshot.rejected_packets), 1)
        self.assertTrue(snapshot.pending_packets[0].source.startswith("persistence:"))

    def test_auto_refresh_advances_refresh_sequence(self) -> None:
        dashboard = dashboard_fixture()

        snapshot = dashboard.auto_refresh(cycles=3)

        self.assertEqual(snapshot.refresh_sequence, 3)

    def test_metric_calculation_and_health_reporting(self) -> None:
        snapshot = dashboard_fixture().refresh()

        self.assertEqual(snapshot.metrics.queue_depth, 0)
        self.assertEqual(snapshot.metrics.decision_throughput, 1)
        self.assertGreater(snapshot.metrics.utilization, 0)
        self.assertEqual(snapshot.health.status, "attention")
        self.assertIn("rejections_present", snapshot.health.reasons)

    def test_command_table_rendering(self) -> None:
        dashboard = dashboard_fixture()

        rows = dashboard.render_command_table()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].decision_type, "approve")
        self.assertEqual(rows[0].cdr_contract_id, "DOC-091")
        self.assertTrue(rows[0].source.startswith("decision_registry:"))

    def test_dashboard_filtering(self) -> None:
        dashboard = dashboard_fixture()

        approve = dashboard.filter_recent_decisions("approve")
        reject = dashboard.filter_recent_decisions("reject")

        self.assertEqual(len(approve), 1)
        self.assertEqual(len(reject), 0)

    def test_dashboard_sorting(self) -> None:
        dashboard = dashboard_fixture()

        ascending = dashboard.sort_recent_decisions()
        descending = dashboard.sort_recent_decisions(descending=True)

        self.assertEqual(ascending[0].value["decision_id"], descending[0].value["decision_id"])

    def test_dashboard_interactions_generate_audit_events(self) -> None:
        dashboard = dashboard_fixture()
        before = len(dashboard.audit_service.audit_log.events)

        dashboard.refresh()
        dashboard.filter_recent_decisions("approve")
        dashboard.sort_recent_decisions()

        self.assertGreater(len(dashboard.audit_service.audit_log.events), before)


if __name__ == "__main__":
    unittest.main()

