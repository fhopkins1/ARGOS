from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptPassport, PromptRepository  # noqa: E402
from argos.seeker import FundamentalObservation, FundamentalResearchOffice, FundamentalScreener  # noqa: E402


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
            prompt_id="PROMPT-020",
            title="Fundamental COR Prompt",
            owner_group_id="DEP-003",
            author_staff_id="STF-022",
            purpose="Generate deterministic fundamental COR scaffolds.",
            allowed_environments=("development",),
            input_contract_types=("FUNDAMENTAL_OBSERVATION",),
            output_contract_types=("COR",),
            dependencies=("EO-020",),
            safety_notes="No trade recommendations, sizing, execution, or technical analysis.",
        ),
        "1.0.0",
        "Create descriptive fundamental COR only.",
    )
    return repository


def observation() -> FundamentalObservation:
    return FundamentalObservation(
        revenue_growth=0.12,
        earnings_growth=0.18,
        pe_ratio=22,
        debt_to_equity=0.4,
        current_ratio=1.8,
        free_cash_flow_positive=True,
        insider_activity_score=1.0,
        institutional_ownership_change=0.05,
        analyst_revision_score=0.7,
    )


def office() -> FundamentalResearchOffice:
    return FundamentalResearchOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class FundamentalResearchOfficeTests(unittest.TestCase):
    def test_financial_screening_generates_expected_fundamental_signals(self) -> None:
        signals = FundamentalScreener().screen(observation())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(by_name["financial_statement"].signal, "expanding_revenue")
        self.assertEqual(by_name["earnings"].signal, "earnings_growth")
        self.assertEqual(by_name["valuation"].signal, "reasonable_valuation")
        self.assertEqual(by_name["growth"].signal, "growth_profile_positive")
        self.assertEqual(by_name["balance_sheet"].signal, "balance_sheet_resilient")
        self.assertEqual(by_name["cash_flow"].signal, "positive_free_cash_flow")
        self.assertEqual(by_name["insider_activity"].signal, "insider_supportive")
        self.assertEqual(by_name["institutional_ownership"].signal, "institutional_accumulation")
        self.assertEqual(by_name["analyst_revision"].signal, "positive_revisions")

    def test_opportunity_generation_persists_fundamental_cor(self) -> None:
        fundamental = office()

        cor = fundamental.generate_cor(observation(), "CF-001", "TC-001", 401, "PROMPT-020")

        self.assertEqual(cor.contract_id, "DOC-401")
        self.assertEqual(cor.contract_type, "COR")
        self.assertEqual(cor.machine_payload["candidate_status"], "fundamental_candidate_unanalysed")
        self.assertEqual(len(cor.machine_payload["fundamental_signals"]), 9)
        self.assertIsNotNone(
            fundamental.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-401")
        )

    def test_cor_generation_does_not_create_trade_recommendation_fields(self) -> None:
        fundamental = office()

        cor = fundamental.generate_cor(observation(), "CF-001", "TC-001", 402, "PROMPT-020")

        self.assertNotIn("trade_recommendation", cor.machine_payload)
        self.assertNotIn("position_size", cor.machine_payload)
        self.assertNotIn("execution_instruction", cor.machine_payload)
        self.assertNotIn("technical_signals", cor.machine_payload)

    def test_courier_routing_uses_deterministic_interfaces(self) -> None:
        fundamental = office()
        cor = fundamental.generate_cor(observation(), "CF-001", "TC-001", 403, "PROMPT-020")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = fundamental.route_cor(cor, executive_inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-403"), cor)
        self.assertEqual(fundamental.office.routed_reports, 1)

    def test_instrument_panel_updates_and_reports_healthy_office(self) -> None:
        fundamental = office()
        cor = fundamental.generate_cor(observation(), "CF-001", "TC-001", 404, "PROMPT-020")
        fundamental.route_cor(cor, IncomingMailbox("STF-002", "DEP-002"))

        panel = fundamental.instrument_panel()

        self.assertEqual(panel.office_id, "SEEKER-OFFICE-002")
        self.assertEqual(panel.metrics.reports_generated, 1)
        self.assertEqual(panel.metrics.routed_reports, 1)
        self.assertEqual(panel.health.status, "healthy")

    def test_courier_routing_generates_audit_events(self) -> None:
        fundamental = office()
        cor = fundamental.generate_cor(observation(), "CF-001", "TC-001", 405, "PROMPT-020")
        fundamental.route_cor(cor, IncomingMailbox("STF-002", "DEP-002"))

        event_types = [event.event_type for event in fundamental.department.audit_service.audit_log.events]

        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)


if __name__ == "__main__":
    unittest.main()
