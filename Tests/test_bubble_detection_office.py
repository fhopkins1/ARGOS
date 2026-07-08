from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import OrganizationalBeliefState  # noqa: E402
from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptPassport, PromptRepository  # noqa: E402
from argos.risk import BubbleDetectionOffice, BubbleDetectionOfficeChief, BubbleMarketObservation  # noqa: E402


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
            prompt_id="PROMPT-048",
            title="Bubble Detection Report Prompt",
            owner_group_id="DEP-005",
            author_staff_id="STF-048",
            purpose="Generate deterministic bubble detection reports.",
            allowed_environments=("development",),
            input_contract_types=("OBS", "MARKET_DATA"),
            output_contract_types=("RAR",),
            dependencies=("EO-048",),
            safety_notes="No exact peak forecast, investment recommendation, execution, Organizational Belief State modification, or Command Decision.",
        ),
        "1.0.0",
        "Create deterministic Bubble Assessment Report only.",
    )
    return repository


def belief_state() -> OrganizationalBeliefState:
    return OrganizationalBeliefState(
        "OBS-001",
        "risk_elevated",
        0.56,
        0.75,
        0.75,
        ("DOC-2601", "DOC-2602"),
    )


def observation() -> BubbleMarketObservation:
    return BubbleMarketObservation(
        "MKT-BUB-001",
        "ARGOS_TEST",
        2.4,
        0.18,
        0.82,
        0.78,
        0.72,
        0.86,
        0.74,
        0.68,
        0.62,
        ("dot_com_marker", "retail_leverage_marker"),
    )


def office() -> BubbleDetectionOffice:
    return BubbleDetectionOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class BubbleDetectionOfficeTests(unittest.TestCase):
    def test_valuation_speculation_narrative_and_liquidity_are_deterministic(self) -> None:
        review = BubbleDetectionOfficeChief().evaluate(belief_state(), observation())

        self.assertEqual(review["valuation_divergence_assessment"], {"divergence": 1.4, "state": "valuation_extreme"})
        self.assertEqual(review["speculative_behavior_assessment"], {"speculation_score": 0.731, "state": "speculation_extreme"})
        self.assertEqual(review["narrative_dominance_report"], {"narrative_dominance_score": 0.812, "state": "narrative_dominant"})
        self.assertEqual(review["liquidity_expansion_report"], {"liquidity_expansion_score": 0.653, "state": "liquidity_expansion_aggressive"})

    def test_bubble_progression_and_historical_analogs_are_identified(self) -> None:
        review = BubbleDetectionOfficeChief().evaluate(belief_state(), observation())

        self.assertEqual(review["bubble_progression_report"], {"report_id": "BPR-001", "stage": "mania", "stage_score": 0.9364})
        self.assertEqual(review["historical_bubble_analog_report"]["closest_analog"], {"analog_id": "HBA-2000", "name": "Dot-Com Bubble", "similarity": 0.9326})
        self.assertEqual(len(review["historical_bubble_analog_report"]["analogs"]), 3)

    def test_collapse_vulnerability_warning_archive_and_confidence_are_reproducible(self) -> None:
        review = BubbleDetectionOfficeChief().evaluate(belief_state(), observation())

        self.assertEqual(review["collapse_vulnerability_assessment"], {"assessment_id": "CVA-001", "vulnerability_score": 0.7154, "vulnerability_state": "collapse_vulnerability_high"})
        self.assertEqual(review["executive_bubble_warning"]["severity"], "high")
        self.assertEqual(review["bubble_episode_archive"], {"archive_id": "BEA-001", "asset": "ARGOS_TEST", "stage": "mania", "stage_score": 0.9364, "vulnerability_score": 0.7154, "historical_markers": ("dot_com_marker", "retail_leverage_marker")})
        self.assertEqual(review["confidence_adjustment_record"], {"record_id": "BCAR-001", "prior_confidence": 0.56, "adjusted_confidence": 0.4135, "adjustment": -0.1465})

    def test_bubble_report_contains_required_artifacts_and_boundaries(self) -> None:
        bubble = office()

        report = bubble.generate_bubble_risk_report(belief_state(), observation(), "CF-001", "TC-001", 3401, "PROMPT-048")

        self.assertEqual(report.contract_type, "RAR")
        self.assertEqual(report.machine_payload["risk_id"], "BUB-003401")
        self.assertEqual(report.machine_payload["bubble_assessment_report"]["report_id"], "BAR-001")
        self.assertEqual(report.machine_payload["bubble_assessment_report"]["sustainability_focus"], True)
        self.assertFalse(report.machine_payload["bubble_assessment_report"]["exact_peak_forecast_attempted"])
        self.assertEqual(report.machine_payload["bubble_progression_report"]["stage"], "mania")
        self.assertEqual(report.machine_payload["executive_bubble_warning"]["warning_id"], "EBW-001")
        self.assertEqual(report.machine_payload["bubble_episode_archive"]["archive_id"], "BEA-001")
        self.assertFalse(report.machine_payload["organizational_belief_state_modified"])
        self.assertFalse(report.machine_payload["opaque_reasoning_used"])
        self.assertIsNone(report.machine_payload["investment_recommendation"])
        self.assertIsNone(report.machine_payload["execution_instruction"])
        self.assertIsNone(report.machine_payload["command_decision"])
        self.assertIsNotNone(bubble.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-3401"))

    def test_bubble_detection_requires_organizational_belief_state(self) -> None:
        with self.assertRaises(TypeError):
            BubbleDetectionOfficeChief().evaluate({"state_id": "OBS-001"}, observation())

    def test_courier_routing_generates_audit_events(self) -> None:
        bubble = office()
        report = bubble.generate_bubble_risk_report(belief_state(), observation(), "CF-001", "TC-001", 3402, "PROMPT-048")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = bubble.route_report(report, executive_inbox)
        event_types = [event.event_type for event in bubble.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-3402"), report)
        self.assertIn(AuditEventType.DOCUMENT_CREATED, event_types)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_displays_bubble_values(self) -> None:
        bubble = office()
        report = bubble.generate_bubble_risk_report(belief_state(), observation(), "CF-001", "TC-001", 3403, "PROMPT-048")
        bubble.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        panel = bubble.instrument_panel()

        self.assertEqual(panel.base_panel.office_id, "RISK-OFFICE-008")
        self.assertEqual(panel.base_panel.metrics.reports_generated, 1)
        self.assertEqual(panel.base_panel.metrics.routed_reports, 1)
        self.assertEqual(panel.latest_stage, "mania")
        self.assertEqual(panel.valuation_divergence, 1.4)
        self.assertEqual(panel.collapse_vulnerability, 0.7154)
        self.assertEqual(panel.archived_episodes, 1)


if __name__ == "__main__":
    unittest.main()
