from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import (  # noqa: E402
    ProbabilityAnalyst,
    RegressionAnalyst,
    StatisticalAnalysisOffice,
    StatisticalDataset,
    StatisticalOfficeChief,
)
from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.communication import IncomingMailbox  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.contracts import OperationalContract, utc_timestamp  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402
from argos.foundation.prompts import PromptPassport, PromptRepository  # noqa: E402


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
            prompt_id="PROMPT-030",
            title="Statistical AAR Prompt",
            owner_group_id="DEP-004",
            author_staff_id="STF-031",
            purpose="Generate deterministic Statistical Analytical Assessment Reports.",
            allowed_environments=("development",),
            input_contract_types=("SEEKER_REPORT",),
            output_contract_types=("AAR",),
            dependencies=("EO-030",),
            safety_notes="No trade recommendations, execution, source modification, command decisions, or Risk Office override.",
        ),
        "1.0.0",
        "Create deterministic statistical assessment only.",
    )
    return repository


def dataset() -> StatisticalDataset:
    return StatisticalDataset(
        observations=(1, 2, 3, 4, 5),
        predictors=(1, 2, 3, 4),
        outcomes=(2, 4, 6, 8),
        scenario_payoffs=(-10, 5, 20),
        scenario_probabilities=(0.2, 0.5, 0.3),
    )


def source_report() -> OperationalContract:
    created = utc_timestamp()
    payload = {"office_id": "SEEKER-OFFICE-009", "report_status": "multi_office_intelligence_fused"}
    signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id="DOC-401",
        contract_type="MIR",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id="STF-029",
        produced_by_group_id="DEP-003",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Synthetic MIR source.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def office() -> StatisticalAnalysisOffice:
    return StatisticalAnalysisOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class StatisticalAnalysisOfficeTests(unittest.TestCase):
    def test_probability_calculation_is_reproducible(self) -> None:
        probability = ProbabilityAnalyst().estimate(dataset().outcomes, 5)

        self.assertEqual(probability, 0.5)

    def test_regression_analysis_is_reproducible(self) -> None:
        regression = RegressionAnalyst().regress(dataset().predictors, dataset().outcomes)

        self.assertEqual(regression["slope"], 2.0)
        self.assertEqual(regression["intercept"], 0.0)
        self.assertEqual(regression["r_squared"], 1.0)

    def test_confidence_intervals_expected_value_and_sensitivity(self) -> None:
        analysis = StatisticalOfficeChief().analyze(dataset())

        self.assertEqual(analysis["expected_value"], 6.5)
        self.assertEqual(analysis["confidence_interval"], {"lower": 1.7604, "upper": 4.2396, "confidence_level": 0.95})
        self.assertEqual(analysis["sensitivity"], {"downside": 5.85, "base": 6.5, "upside": 7.15})
        self.assertEqual(analysis["model_comparison"]["selected_model"], "linear_regression")

    def test_statistical_aar_contains_argument_maps_for_conclusions(self) -> None:
        statistical = office()

        aar = statistical.generate_statistical_aar(dataset(), (source_report(),), "CF-001", "TC-001", 1801, "PROMPT-030")

        self.assertEqual(aar.contract_type, "AAR")
        self.assertEqual(aar.machine_payload["assessment_status"], "statistical_analytical_assessment")
        self.assertEqual(len(aar.machine_payload["argument_maps"]), 1)
        self.assertEqual(aar.machine_payload["argument_maps"][0]["conclusion_id"], "CONCLUSION-001")
        self.assertIn("statistical_analysis", aar.machine_payload)
        self.assertIsNotNone(statistical.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-1801"))

    def test_statistical_aar_preserves_boundaries_and_source_reports(self) -> None:
        statistical = office()
        source = source_report()
        before = source.to_json()

        aar = statistical.generate_statistical_aar(dataset(), (source,), "CF-001", "TC-001", 1802, "PROMPT-030")

        self.assertEqual(source.to_json(), before)
        self.assertFalse(aar.machine_payload["seeker_reports_modified"])
        self.assertFalse(aar.machine_payload["risk_office_override"])
        self.assertNotIn("trade_recommendation", aar.machine_payload)
        self.assertNotIn("execution_instruction", aar.machine_payload)
        self.assertNotIn("command_decision", aar.machine_payload)

    def test_courier_routing_generates_audit_events(self) -> None:
        statistical = office()
        aar = statistical.generate_statistical_aar(dataset(), (source_report(),), "CF-001", "TC-001", 1803, "PROMPT-030")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = statistical.route_aar(aar, executive_inbox)
        event_types = [event.event_type for event in statistical.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-1803"), aar)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        statistical = office()
        aar = statistical.generate_statistical_aar(dataset(), (source_report(),), "CF-001", "TC-001", 1804, "PROMPT-030")
        statistical.route_aar(aar, IncomingMailbox("STF-002", "DEP-002"))

        panel = statistical.instrument_panel()

        self.assertEqual(panel.office_id, "ANALYST-OFFICE-001")
        self.assertEqual(panel.metrics.reports_generated, 1)
        self.assertEqual(panel.metrics.routed_reports, 1)
        self.assertEqual(panel.health.status, "healthy")


if __name__ == "__main__":
    unittest.main()
