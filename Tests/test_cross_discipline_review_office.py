from pathlib import Path
import hashlib
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.analyst import (  # noqa: E402
    CrossDisciplineReviewOffice,
    CrossDisciplineReviewOfficeChief,
    DisciplineAssessment,
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
            prompt_id="PROMPT-037",
            title="Cross-Discipline Review AAR Prompt",
            owner_group_id="DEP-004",
            author_staff_id="STF-038",
            purpose="Generate deterministic peer review across Analyst disciplines.",
            allowed_environments=("development",),
            input_contract_types=("AAR",),
            output_contract_types=("AAR",),
            dependencies=("EO-037",),
            safety_notes="No trade recommendation, analysis modification, disagreement suppression, forced consensus, or Command Decision.",
        ),
        "1.0.0",
        "Create deterministic cross-discipline review assessment only.",
    )
    return repository


def assessments() -> tuple[DisciplineAssessment, ...]:
    return (
        DisciplineAssessment("statistical", "DOC-901", "risk_elevated", ("EV-1", "EV-2", "COMMON"), ("claim:risk", "statistical_claim"), ("timing_unknown", "sample_unknown"), ("shared_assumption", "stat_assumption"), 0.72),
        DisciplineAssessment("technical", "DOC-902", "trend_persistent", ("EV-1", "EV-3", "COMMON"), ("claim:risk", "technical_claim"), ("timing_unknown", "pattern_unknown"), ("shared_assumption", "tech_assumption"), 0.66),
        DisciplineAssessment("fundamental", "DOC-903", "trend_persistent", ("EV-2", "EV-4", "COMMON"), ("claim:risk", "fundamental_claim"), ("timing_unknown", "valuation_unknown"), ("shared_assumption", "fund_assumption"), 0.64),
        DisciplineAssessment("macroeconomic", "DOC-904", "macro_regime_conflict", ("EV-5", "COMMON"), ("claim:risk", "macro_claim"), ("timing_unknown", "policy_unknown"), ("shared_assumption", "macro_assumption"), 0.58),
        DisciplineAssessment("derivatives", "DOC-905", "risk_elevated", ("EV-1", "EV-6", "COMMON"), ("claim:risk", "derivatives_claim"), ("timing_unknown", "dealer_unknown"), ("shared_assumption", "deriv_assumption"), 0.7),
        DisciplineAssessment("behavioral", "DOC-906", "risk_elevated", ("EV-7", "COMMON"), ("claim:risk", "behavioral_claim"), ("timing_unknown", "sentiment_unknown"), ("shared_assumption", "behav_assumption"), 0.69),
        DisciplineAssessment("risk_interaction", "DOC-907", "risk_elevated", ("EV-8", "COMMON"), ("claim:risk", "risk_interaction_claim"), ("timing_unknown", "stress_unknown"), ("shared_assumption", "risk_assumption"), 0.55),
    )


def source_report(contract_id: str, staff_id: str) -> OperationalContract:
    created = utc_timestamp()
    payload = {"source": contract_id, "assessment_status": "analytical_assessment"}
    signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return OperationalContract(
        contract_id=contract_id,
        contract_type="AAR",
        contract_version="1.0.0",
        schema_version="1.0.0",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        parent_contract_ids=(),
        produced_by_staff_id=staff_id,
        produced_by_group_id="DEP-004",
        intended_consumer_group_id="DEP-002",
        created_timestamp_utc=created,
        updated_timestamp_utc=created,
        validation_status="valid",
        validation_errors=(),
        human_summary="Synthetic Analyst source.",
        machine_payload=payload,
        signature_hash=signature_hash,
        source_reference_ids=(),
    )


def source_reports() -> tuple[OperationalContract, ...]:
    return (
        source_report("DOC-901", "STF-031"),
        source_report("DOC-902", "STF-032"),
        source_report("DOC-903", "STF-033"),
        source_report("DOC-904", "STF-034"),
        source_report("DOC-905", "STF-035"),
        source_report("DOC-906", "STF-036"),
        source_report("DOC-907", "STF-037"),
    )


def office() -> CrossDisciplineReviewOffice:
    return CrossDisciplineReviewOffice(
        configuration_service(),
        InMemoryPersistenceRepository(canonical_schemas()),
        AuditService(),
        prompt_repository(),
    )


class CrossDisciplineReviewOfficeTests(unittest.TestCase):
    def test_consensus_generation_preserves_disagreement(self) -> None:
        reasoning = CrossDisciplineReviewOfficeChief().analyze(assessments())
        consensus = reasoning["consensus_report"]
        disagreement = reasoning["disagreement_report"]

        self.assertEqual(consensus["consensus_conclusion"], "risk_elevated")
        self.assertEqual(consensus["supporting_disciplines"], ("statistical", "derivatives", "behavioral", "risk_interaction"))
        self.assertEqual(consensus["consensus_state"], "consensus_with_disagreement")
        self.assertEqual(len(disagreement["disagreement_groups"]), 2)

    def test_conflict_detection_documents_conflicting_assumptions(self) -> None:
        reasoning = CrossDisciplineReviewOfficeChief().analyze(assessments())
        conflict = reasoning["analytical_conflict_report"]

        self.assertEqual(conflict["report_id"], "ACR-001")
        self.assertEqual(conflict["conflicting_conclusions"], ("macro_regime_conflict", "trend_persistent"))
        self.assertEqual(conflict["conflict_state"], "analytical_conflict_present")
        self.assertIn("macro_assumption", conflict["conflicting_assumptions"])

    def test_reasoning_and_evidence_comparison_scores_are_deterministic(self) -> None:
        reasoning = CrossDisciplineReviewOfficeChief().analyze(assessments())
        review = reasoning["cross_discipline_review_report"]

        self.assertEqual(review["agreement_score"], 0.5714)
        self.assertEqual(review["conflict_score"], 0.2857)
        self.assertEqual(review["evidence_comparison_score"], 0.1111)
        self.assertEqual(review["reasoning_comparison_score"], 0.125)
        self.assertEqual(review["unknown_comparison_score"], 0.125)

    def test_reviewer_outputs_cover_all_disciplines(self) -> None:
        reasoning = CrossDisciplineReviewOfficeChief().analyze(assessments())
        reviewer_results = reasoning["reviewer_results"]

        self.assertEqual(len(reviewer_results), 7)
        self.assertEqual(tuple(result["discipline"] for result in reviewer_results), ("statistical", "technical", "fundamental", "macroeconomic", "derivatives", "behavioral", "risk_interaction"))

    def test_reasoning_graph_generation_references_consensus(self) -> None:
        chief = CrossDisciplineReviewOfficeChief()
        reasoning = chief.analyze(assessments())

        graphs = chief.reasoning_graphs(reasoning, tuple(report.contract_id for report in source_reports()))

        self.assertEqual(len(graphs), 1)
        self.assertEqual(graphs[0]["conclusion_id"], "CROSS-DISCIPLINE-CONCLUSION-001")
        self.assertIn("claim:cross_discipline_consensus", graphs[0]["nodes"])

    def test_cross_discipline_aar_generation_persists_review_payload(self) -> None:
        cross_review = office()

        aar = cross_review.generate_cross_discipline_aar(assessments(), source_reports(), "CF-001", "TC-001", 2501, "PROMPT-037")

        self.assertEqual(aar.contract_type, "AAR")
        self.assertEqual(aar.machine_payload["assessment_status"], "cross_discipline_review_analytical_assessment")
        self.assertEqual(aar.machine_payload["consensus_report"]["report_id"], "CR-001")
        self.assertEqual(aar.machine_payload["analytical_conflict_report"]["report_id"], "ACR-001")
        self.assertIsNotNone(cross_review.department.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-2501"))

    def test_cross_discipline_aar_preserves_boundaries_and_source_analyses(self) -> None:
        cross_review = office()
        reports = source_reports()
        before = tuple(report.to_json() for report in reports)

        aar = cross_review.generate_cross_discipline_aar(assessments(), reports, "CF-001", "TC-001", 2502, "PROMPT-037")

        self.assertEqual(tuple(report.to_json() for report in reports), before)
        self.assertFalse(aar.machine_payload["analyses_modified"])
        self.assertFalse(aar.machine_payload["disagreement_suppressed"])
        self.assertFalse(aar.machine_payload["forced_consensus"])
        self.assertNotIn("trade_recommendation", aar.machine_payload)
        self.assertNotIn("command_decision", aar.machine_payload)

    def test_courier_routing_generates_audit_events(self) -> None:
        cross_review = office()
        aar = cross_review.generate_cross_discipline_aar(assessments(), source_reports(), "CF-001", "TC-001", 2503, "PROMPT-037")
        executive_inbox = IncomingMailbox("STF-002", "DEP-002")

        result = cross_review.route_aar(aar, executive_inbox)
        event_types = [event.event_type for event in cross_review.department.audit_service.audit_log.events]

        self.assertTrue(result.delivered)
        self.assertEqual(executive_inbox.get("DOC-2503"), aar)
        self.assertIn(AuditEventType.COURIER_TRANSFER, event_types)

    def test_instrument_panel_updates_after_generation_and_routing(self) -> None:
        cross_review = office()
        aar = cross_review.generate_cross_discipline_aar(assessments(), source_reports(), "CF-001", "TC-001", 2504, "PROMPT-037")
        cross_review.route_aar(aar, IncomingMailbox("STF-002", "DEP-002"))

        panel = cross_review.instrument_panel()

        self.assertEqual(panel.office_id, "ANALYST-OFFICE-008")
        self.assertEqual(panel.metrics.reports_generated, 1)
        self.assertEqual(panel.metrics.routed_reports, 1)
        self.assertEqual(panel.health.status, "healthy")


if __name__ == "__main__":
    unittest.main()
