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
from argos.seeker import CryptocurrencyObservation, CryptocurrencyOffice, CryptocurrencyScreener  # noqa: E402


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
            prompt_id="PROMPT-024",
            title="Cryptocurrency Report Prompt",
            owner_group_id="DEP-003",
            author_staff_id="STF-026",
            purpose="Generate deterministic cryptocurrency reports.",
            allowed_environments=("development",),
            input_contract_types=("CRYPTOCURRENCY_OBSERVATION",),
            output_contract_types=("COR", "CXR", "CTR", "IGR"),
            dependencies=("EO-024",),
            safety_notes="No trade recommendations, sizing, execution, or Risk Office bypass.",
        ),
        "1.0.0",
        "Create descriptive cryptocurrency reports only.",
    )
    return repository


def active_observation() -> CryptocurrencyObservation:
    return CryptocurrencyObservation(
        price_change=0.08,
        trend_strength=0.75,
        transaction_count_change=0.12,
        active_address_change=0.18,
        stablecoin_net_flow=250_000_000,
        exchange_net_flow=-120_000_000,
        whale_transaction_count=14,
        institutional_flow=80_000_000,
        defi_total_value_locked_change=0.05,
        nft_volume_change=-0.2,
        on_chain_risk_score=0.82,
    )


def unknown_observation() -> CryptocurrencyObservation:
    return CryptocurrencyObservation(
        price_change=None,
        trend_strength=None,
        transaction_count_change=None,
        active_address_change=None,
        stablecoin_net_flow=None,
        exchange_net_flow=None,
        whale_transaction_count=None,
        institutional_flow=None,
        defi_total_value_locked_change=None,
        nft_volume_change=None,
        on_chain_risk_score=None,
    )


def office() -> CryptocurrencyOffice:
    return CryptocurrencyOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class CryptocurrencyOfficeTests(unittest.TestCase):
    def test_blockchain_data_ingestion_generates_nine_crypto_signals(self) -> None:
        signals = CryptocurrencyScreener().monitor(active_observation())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(len(signals), 9)
        self.assertEqual(by_name["price_structure"].signal, "price_structure_positive")
        self.assertEqual(by_name["blockchain_activity"].signal, "blockchain_activity_expanding")
        self.assertEqual(by_name["stablecoin_flow"].signal, "stablecoin_inflow")
        self.assertEqual(by_name["defi"].signal, "defi_tvl_expanding")
        self.assertEqual(by_name["on_chain_analytics"].signal, "on_chain_risk_elevated")

    def test_exchange_flow_analysis_and_whale_detection_are_deterministic(self) -> None:
        signals = CryptocurrencyScreener().monitor(active_observation())
        by_name = {signal.seeker: signal for signal in signals}

        self.assertEqual(by_name["exchange_flow"].signal, "exchange_outflow_accumulation")
        self.assertEqual(by_name["exchange_flow"].report_hint, "blockchain_activity")
        self.assertEqual(by_name["wallet_activity"].signal, "whale_activity_detected")
        self.assertEqual(by_name["wallet_activity"].value, 14)

    def test_report_generation_persists_all_crypto_report_types(self) -> None:
        crypto = office()

        cor = crypto.generate_cor(active_observation(), "CF-001", "TC-001", 801, "PROMPT-024")
        activity = crypto.generate_blockchain_activity_report(active_observation(), "CF-001", "TC-001", 802, "PROMPT-024")
        threat = crypto.generate_threat_report(active_observation(), "CF-001", "TC-001", 803, "PROMPT-024")
        gap = crypto.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 804, "PROMPT-024")

        self.assertEqual(cor.contract_type, "COR")
        self.assertEqual(activity.contract_type, "CXR")
        self.assertEqual(threat.contract_type, "CTR")
        self.assertEqual(gap.contract_type, "IGR")
        self.assertEqual(activity.machine_payload["report_status"], "blockchain_activity_identified")
        self.assertEqual(threat.machine_payload["report_status"], "crypto_threat_identified")
        self.assertEqual(gap.machine_payload["report_status"], "crypto_information_gap")
        self.assertIsNotNone(crypto.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-804"))

    def test_threat_detection_documents_crypto_risks(self) -> None:
        crypto = office()

        threat = crypto.generate_threat_report(active_observation(), "CF-001", "TC-001", 805, "PROMPT-024")
        signals = {signal["signal"] for signal in threat.machine_payload["cryptocurrency_signals"]}

        self.assertIn("nft_activity_contracting", signals)
        self.assertIn("on_chain_risk_elevated", signals)

    def test_unknown_detection_documents_missing_blockchain_data(self) -> None:
        crypto = office()

        gap = crypto.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 806, "PROMPT-024")
        signals = {signal["signal"] for signal in gap.machine_payload["cryptocurrency_signals"]}

        self.assertIn("price_structure_unknown", signals)
        self.assertIn("blockchain_activity_unknown", signals)
        self.assertIn("exchange_flow_unknown", signals)

    def test_courier_routing_uses_deterministic_interfaces(self) -> None:
        crypto = office()
        report = crypto.generate_blockchain_activity_report(active_observation(), "CF-001", "TC-001", 807, "PROMPT-024")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = crypto.route_report(report, executive_inbox)

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-807"), report)
        self.assertEqual(crypto.office.routed_reports, 1)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        crypto = office()
        cor = crypto.generate_cor(active_observation(), "CF-001", "TC-001", 808, "PROMPT-024")
        activity = crypto.generate_blockchain_activity_report(active_observation(), "CF-001", "TC-001", 809, "PROMPT-024")
        threat = crypto.generate_threat_report(active_observation(), "CF-001", "TC-001", 810, "PROMPT-024")
        gap = crypto.generate_information_gap_report(unknown_observation(), "CF-001", "TC-001", 811, "PROMPT-024")
        crypto.route_report(cor, IncomingMailbox("STF-002", "DEP-002"))
        crypto.route_report(activity, IncomingMailbox("STF-002", "DEP-002"))
        crypto.route_report(threat, IncomingMailbox("STF-002", "DEP-002"))
        crypto.route_report(gap, IncomingMailbox("STF-002", "DEP-002"))

        panel = crypto.instrument_panel()

        self.assertEqual(panel.office_id, "SEEKER-OFFICE-006")
        self.assertEqual(panel.metrics.reports_generated, 4)
        self.assertEqual(panel.metrics.routed_reports, 4)
        self.assertEqual(panel.health.status, "healthy")

    def test_routing_generates_audit_events_and_payload_preserves_boundaries(self) -> None:
        crypto = office()
        report = crypto.generate_cor(active_observation(), "CF-001", "TC-001", 812, "PROMPT-024")
        crypto.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        event_types = [event.event_type for event in crypto.department.audit_service.audit_log.events]

        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)
        self.assertTrue(report.machine_payload["risk_doctrine_required"])
        self.assertNotIn("trade_recommendation", report.machine_payload)
        self.assertNotIn("position_size", report.machine_payload)
        self.assertNotIn("execution_instruction", report.machine_payload)


if __name__ == "__main__":
    unittest.main()
