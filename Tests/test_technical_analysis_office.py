from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.audit import AuditService, AuditEventType  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptPassport, PromptRepository  # noqa: E402
from argos.seeker import MarketObservation, TechnicalAnalysisOffice, TechnicalScreener  # noqa: E402


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
            prompt_id="PROMPT-019",
            title="Technical COR Prompt",
            owner_group_id="DEP-003",
            author_staff_id="STF-021",
            purpose="Generate deterministic technical COR scaffolds.",
            allowed_environments=("development",),
            input_contract_types=("TECHNICAL_OBSERVATIONS",),
            output_contract_types=("COR",),
            dependencies=("EO-019",),
            safety_notes="No trade recommendations.",
        ),
        "1.0.0",
        "Create descriptive technical COR only.",
    )
    return repository


def observations() -> tuple[MarketObservation, ...]:
    return (
        MarketObservation(close=100, high=101, low=99, volume=1000),
        MarketObservation(close=102, high=103, low=100, volume=1200),
        MarketObservation(close=105, high=107, low=103, volume=2000),
    )


def office() -> TechnicalAnalysisOffice:
    return TechnicalAnalysisOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class TechnicalAnalysisOfficeTests(unittest.TestCase):
    def test_signal_generation_and_indicator_calculations(self) -> None:
        signals = TechnicalScreener().screen(observations())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(by_name["trend"].signal, "uptrend")
        self.assertEqual(by_name["trend"].value, 5)
        self.assertEqual(by_name["momentum"].signal, "positive")
        self.assertEqual(by_name["volatility"].signal, "elevated")
        self.assertEqual(by_name["volume"].signal, "volume_expansion")

    def test_cor_generation_persists_technical_signals(self) -> None:
        technical = office()

        cor = technical.generate_cor(observations(), "CF-001", "TC-001", 301, "PROMPT-019")

        self.assertEqual(cor.contract_id, "DOC-301")
        self.assertEqual(cor.contract_type, "COR")
        self.assertEqual(cor.machine_payload["candidate_status"], "technical_candidate_unanalysed")
        self.assertEqual(len(cor.machine_payload["technical_signals"]), 6)
        self.assertIsNotNone(
            technical.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-301")
        )

    def test_office_routing_uses_courier(self) -> None:
        technical = office()
        cor = technical.generate_cor(observations(), "CF-001", "TC-001", 302, "PROMPT-019")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = technical.route_cor(cor, executive_inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-302"), cor)
        self.assertEqual(technical.office.routed_reports, 1)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        technical = office()
        cor = technical.generate_cor(observations(), "CF-001", "TC-001", 303, "PROMPT-019")
        technical.route_cor(cor, IncomingMailbox("STF-002", "DEP-002"))

        panel = technical.instrument_panel()

        self.assertEqual(panel.office_id, "SEEKER-OFFICE-001")
        self.assertEqual(panel.metrics.reports_generated, 1)
        self.assertEqual(panel.metrics.routed_reports, 1)
        self.assertEqual(panel.health.status, "healthy")

    def test_courier_routing_generates_audit_events(self) -> None:
        technical = office()
        cor = technical.generate_cor(observations(), "CF-001", "TC-001", 304, "PROMPT-019")
        technical.route_cor(cor, IncomingMailbox("STF-002", "DEP-002"))

        event_types = [event.event_type for event in technical.department.audit_service.audit_log.events]

        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_screener_requires_two_observations(self) -> None:
        with self.assertRaises(ValueError):
            TechnicalScreener().screen((MarketObservation(100, 101, 99, 1000),))


if __name__ == "__main__":
    unittest.main()

