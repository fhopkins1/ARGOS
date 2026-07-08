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
from argos.risk import RiskFusionInput, RiskFusionOffice, RiskFusionOfficeChief  # noqa: E402


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
            prompt_id="PROMPT-050",
            title="Risk Fusion Report Prompt",
            owner_group_id="DEP-005",
            author_staff_id="STF-050",
            purpose="Generate deterministic organizational risk assessments.",
            allowed_environments=("development",),
            input_contract_types=("RAR",),
            output_contract_types=("RAR",),
            dependencies=("EO-050",),
            safety_notes="Preserve subordinate office independence; no investment recommendation, execution, opaque reasoning, or Command Decision.",
        ),
        "1.0.0",
        "Create deterministic Risk Fusion Report only.",
    )
    return repository


def fusion_inputs() -> tuple[RiskFusionInput, ...]:
    return (
        RiskFusionInput("RISK-OFFICE-001", "DOC-2901", "position", 0.52, 0.62, 5000, "reduce_single_position_limit", ("EV-1",)),
        RiskFusionInput("RISK-OFFICE-002", "DOC-3001", "portfolio", 0.65, 0.54, 10000, "reduce_enterprise_risk", ("EV-2",)),
        RiskFusionInput("RISK-OFFICE-005", "DOC-3201", "volatility", 0.72, 0.47, 7000, "reduce_risk_limit_moderately", ("EV-3",)),
        RiskFusionInput("RISK-OFFICE-006", "DOC-3301", "tail", 0.82, 0.38, 9000, "reduce_tail_exposure_and_raise_liquidity_reserve", ("EV-4",)),
        RiskFusionInput("RISK-OFFICE-009", "DOC-3501", "recovery", 0.44, 0.56, 3000, "increase_recovery_validation_threshold", ("EV-5",)),
    )


def office() -> RiskFusionOffice:
    return RiskFusionOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class RiskFusionOfficeTests(unittest.TestCase):
    def test_all_risk_reports_are_integrated_deterministically(self) -> None:
        review = RiskFusionOfficeChief().evaluate(fusion_inputs())

        self.assertEqual(len(review["aggregated_risk_reports"]), 5)
        self.assertTrue(review["subordinate_independence_preserved"])
        self.assertEqual(review["organizational_risk_assessment"], {"assessment_id": "ORA-001", "integrated_risk_score": 0.6453, "posture": "elevated_risk_posture", "source_report_ids": ("DOC-2901", "DOC-3001", "DOC-3201", "DOC-3301", "DOC-3501")})

    def test_cross_risk_interactions_and_conflicts_are_documented(self) -> None:
        review = RiskFusionOfficeChief().evaluate(fusion_inputs())

        interactions = review["cross_risk_interaction_report"]["interactions"]
        self.assertEqual(len(interactions), 10)
        self.assertIn({"domains": ("portfolio", "volatility"), "interaction": "risk_reinforcement"}, interactions)
        self.assertEqual(review["enterprise_mitigation_plan"]["steps"][0]["action"], "reduce_enterprise_risk")

    def test_emergent_risks_exposure_priorities_and_posture_are_generated(self) -> None:
        review = RiskFusionOfficeChief().evaluate(fusion_inputs())

        self.assertEqual(len(review["emergent_risk_register"]["emergent_risks"]), 2)
        self.assertEqual(review["organizational_exposure_assessment"], {"assessment_id": "OEA-001", "enterprise_exposure": 34000, "exposure_weighted_risk": 0.6718})
        self.assertEqual(review["executive_risk_priority_list"][0], {"rank": 1, "risk_domain": "tail", "source_report_id": "DOC-3301", "risk_score": 0.82})
        self.assertEqual(review["organizational_risk_posture_record"], {"record_id": "ORPR-001", "posture": "elevated_risk_posture", "integrated_risk_score": 0.6453})

    def test_archive_and_integrated_confidence_are_reproducible(self) -> None:
        review = RiskFusionOfficeChief().evaluate(fusion_inputs())

        self.assertEqual(review["enterprise_risk_archive"], {"archive_id": "ERA-001", "assessment_id": "ORA-001", "posture": "elevated_risk_posture", "source_report_ids": ("DOC-2901", "DOC-3001", "DOC-3201", "DOC-3301", "DOC-3501")})
        self.assertEqual(review["integrated_confidence_assessment"], {"assessment_id": "ICA-001", "organizational_confidence": 0.434, "contributing_reports": ("DOC-2901", "DOC-3001", "DOC-3201", "DOC-3301", "DOC-3501")})

    def test_risk_fusion_report_contains_required_artifacts_and_boundaries(self) -> None:
        fusion = office()

        report = fusion.generate_risk_fusion_report(fusion_inputs(), "CF-001", "TC-001", 3601, "PROMPT-050")

        self.assertEqual(report.contract_type, "RAR")
        self.assertEqual(report.machine_payload["risk_id"], "FUS-003601")
        self.assertEqual(report.machine_payload["organizational_risk_assessment"]["assessment_id"], "ORA-001")
        self.assertEqual(report.machine_payload["executive_risk_summary"]["summary_id"], "ERS-001")
        self.assertEqual(report.machine_payload["cross_risk_interaction_report"]["report_id"], "CRIR-001")
        self.assertEqual(report.machine_payload["emergent_risk_register"]["register_id"], "ERR-001")
        self.assertEqual(report.machine_payload["enterprise_mitigation_plan"]["plan_id"], "EMP-001")
        self.assertEqual(report.machine_payload["enterprise_risk_archive"]["archive_id"], "ERA-001")
        self.assertFalse(report.machine_payload["subordinate_reports_modified"])
        self.assertFalse(report.machine_payload["opaque_reasoning_used"])
        self.assertIsNone(report.machine_payload["investment_recommendation"])
        self.assertIsNone(report.machine_payload["execution_instruction"])
        self.assertIsNone(report.machine_payload["command_decision"])
        self.assertIsNotNone(fusion.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-3601"))

    def test_risk_fusion_requires_reports(self) -> None:
        with self.assertRaises(ValueError):
            RiskFusionOfficeChief().evaluate(())

    def test_courier_routing_generates_audit_events(self) -> None:
        fusion = office()
        report = fusion.generate_risk_fusion_report(fusion_inputs(), "CF-001", "TC-001", 3602, "PROMPT-050")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = fusion.route_report(report, executive_inbox)
        event_types = [event.event_type for event in fusion.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-3602"), report)
        self.assertIn(AuditEventType.DOCUMENT_CREATED, event_types)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_displays_fusion_values(self) -> None:
        fusion = office()
        report = fusion.generate_risk_fusion_report(fusion_inputs(), "CF-001", "TC-001", 3603, "PROMPT-050")
        fusion.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        panel = fusion.instrument_panel()

        self.assertEqual(panel.base_panel.office_id, "RISK-OFFICE-010")
        self.assertEqual(panel.base_panel.metrics.reports_generated, 1)
        self.assertEqual(panel.base_panel.metrics.routed_reports, 1)
        self.assertEqual(panel.integrated_reports, 5)
        self.assertEqual(panel.enterprise_exposure, 34000)
        self.assertEqual(panel.integrated_risk_score, 0.6453)
        self.assertEqual(panel.priority_count, 5)
        self.assertEqual(panel.emergent_risks, 2)


if __name__ == "__main__":
    unittest.main()
