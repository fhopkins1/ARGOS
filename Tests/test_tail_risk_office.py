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
from argos.risk import TailRiskExposure, TailRiskObservation, TailRiskOffice, TailRiskOfficeChief  # noqa: E402


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
            prompt_id="PROMPT-046",
            title="Tail Risk Report Prompt",
            owner_group_id="DEP-005",
            author_staff_id="STF-046",
            purpose="Generate deterministic tail risk assessment reports.",
            allowed_environments=("development",),
            input_contract_types=("OBS", "RAR"),
            output_contract_types=("RAR",),
            dependencies=("EO-046",),
            safety_notes="No low-probability scenario discard, investment recommendation, execution, Organizational Belief State modification, or Command Decision.",
        ),
        "1.0.0",
        "Create deterministic Tail Risk Assessment Report only.",
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


def observation() -> TailRiskObservation:
    return TailRiskObservation(
        "TRO-001",
        (
            TailRiskExposure("EXP-1", "ALPHA", 5000, 1.2, 0.18, 1.6, "growth"),
            TailRiskExposure("EXP-2", "BETA", 3000, 1.1, 0.12, 1.4, "growth"),
            TailRiskExposure("EXP-3", "GAMMA", 2000, 0.9, 0.2, 1.8, "credit"),
        ),
        {"2008_credit_crisis": 3200, "2020_liquidity_shock": 2100, "2022_rate_shock": 1600},
        0.62,
    )


def office() -> TailRiskOffice:
    return TailRiskOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class TailRiskOfficeTests(unittest.TestCase):
    def test_tail_scenarios_are_generated_and_never_discarded(self) -> None:
        review = TailRiskOfficeChief().evaluate(belief_state(), observation())

        self.assertEqual(review["tail_risk_assessment_report"]["scenario_count"], 4)
        self.assertFalse(review["tail_risk_assessment_report"]["low_probability_scenarios_discarded"])
        self.assertEqual(review["extreme_scenario_report"]["scenarios"][0]["scenario_id"], "TS-001")
        self.assertEqual(review["extreme_scenario_report"]["tail_distribution"], {"tail_probability_mass": 0.31, "weighted_tail_shock": 0.0892})
        self.assertEqual(len(review["tail_scenario_archive"]), 4)

    def test_maximum_credible_loss_and_cascades_are_deterministic(self) -> None:
        review = TailRiskOfficeChief().evaluate(belief_state(), observation())

        self.assertEqual(review["maximum_credible_loss_record"], {"record_id": "MCL-001", "maximum_credible_loss": 6866.6, "maximum_loss_scenario": "TS-004", "loss_ratio": 0.6867})
        self.assertEqual(review["dependency_cascade_analysis"]["cascades"][0], {"dependency_group": "growth", "exposure_ids": ("EXP-1", "EXP-2"), "cascade_state": "cascade_possible"})

    def test_nonlinear_exposures_and_historical_analogs_are_available(self) -> None:
        review = TailRiskOfficeChief().evaluate(belief_state(), observation())

        nonlinear = review["nonlinear_exposure_assessment"]["exposures"]
        self.assertEqual(nonlinear[0]["nonlinear_state"], "nonlinear_elevated")
        self.assertEqual(nonlinear[1]["nonlinear_state"], "nonlinear_contained")
        self.assertEqual(review["historical_analog_report"]["closest_analog"]["crisis"], "2008_credit_crisis")
        self.assertEqual(review["historical_analog_report"]["closest_analog"]["relative_to_mcl"], 0.466)

    def test_resilience_mitigation_and_confidence_surface_are_reproducible(self) -> None:
        review = TailRiskOfficeChief().evaluate(belief_state(), observation())

        self.assertEqual(review["organizational_tail_exposure_summary"]["resilience"], {"organizational_resilience": 0.3197, "resilience_state": "resilience_weak"})
        self.assertEqual(review["organizational_tail_exposure_summary"]["organizational_confidence_surface"], 0.3816)
        self.assertEqual(review["mitigation_recommendation_record"]["action"], "reduce_tail_exposure_and_raise_liquidity_reserve")
        self.assertEqual(review["confidence_adjustment_record"], {"record_id": "TCAR-001", "prior_confidence": 0.56, "adjusted_confidence": 0.3816, "adjustment": -0.1784})

    def test_tail_risk_report_contains_required_artifacts_and_boundaries(self) -> None:
        tail = office()

        report = tail.generate_tail_risk_report(belief_state(), observation(), "CF-001", "TC-001", 3301, "PROMPT-046")

        self.assertEqual(report.contract_type, "RAR")
        self.assertEqual(report.machine_payload["risk_id"], "TAIL-003301")
        self.assertEqual(report.machine_payload["tail_risk_assessment_report"]["report_id"], "TRAR-001")
        self.assertEqual(report.machine_payload["extreme_scenario_report"]["report_id"], "ESR-001")
        self.assertEqual(report.machine_payload["maximum_credible_loss_record"]["record_id"], "MCL-001")
        self.assertEqual(report.machine_payload["mitigation_recommendation_record"]["record_id"], "MRR-001")
        self.assertEqual(len(report.machine_payload["tail_scenario_archive"]), 4)
        self.assertFalse(report.machine_payload["organizational_belief_state_modified"])
        self.assertFalse(report.machine_payload["opaque_reasoning_used"])
        self.assertIsNone(report.machine_payload["investment_recommendation"])
        self.assertIsNone(report.machine_payload["execution_instruction"])
        self.assertIsNone(report.machine_payload["command_decision"])
        self.assertIsNotNone(tail.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-3301"))

    def test_tail_risk_requires_organizational_belief_state(self) -> None:
        with self.assertRaises(TypeError):
            TailRiskOfficeChief().evaluate({"state_id": "OBS-001"}, observation())

    def test_courier_routing_generates_audit_events(self) -> None:
        tail = office()
        report = tail.generate_tail_risk_report(belief_state(), observation(), "CF-001", "TC-001", 3302, "PROMPT-046")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = tail.route_report(report, executive_inbox)
        event_types = [event.event_type for event in tail.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-3302"), report)
        self.assertIn(AuditEventType.DOCUMENT_CREATED, event_types)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_displays_tail_risk_values(self) -> None:
        tail = office()
        report = tail.generate_tail_risk_report(belief_state(), observation(), "CF-001", "TC-001", 3303, "PROMPT-046")
        tail.route_report(report, IncomingMailbox("STF-002", "DEP-002"))

        panel = tail.instrument_panel()

        self.assertEqual(panel.base_panel.office_id, "RISK-OFFICE-006")
        self.assertEqual(panel.base_panel.metrics.reports_generated, 1)
        self.assertEqual(panel.base_panel.metrics.routed_reports, 1)
        self.assertEqual(panel.modeled_scenarios, 4)
        self.assertEqual(panel.maximum_credible_loss, 6866.6)
        self.assertEqual(panel.dependency_cascades, 1)
        self.assertEqual(panel.nonlinear_exposures, 3)
        self.assertEqual(panel.archived_scenarios, 4)


if __name__ == "__main__":
    unittest.main()
