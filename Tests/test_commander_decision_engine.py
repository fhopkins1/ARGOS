from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.executive import (  # noqa: E402
    CommanderDecision,
    CommanderDecisionEngine,
    CommanderOffice,
    ExecutiveBriefingPacket,
)
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import (  # noqa: E402
    InMemoryPersistenceRepository,
    ObjectType,
    canonical_schemas,
)
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
            prompt_id="PROMPT-012",
            title="Commander Decision Prompt",
            owner_group_id="DEP-002",
            author_staff_id="STF-002",
            purpose="Guide deterministic Commander decisions from EBPs.",
            allowed_environments=("development", "paper_trading"),
            input_contract_types=("EBP",),
            output_contract_types=("CDR",),
            dependencies=("EO-012",),
            safety_notes="No trade execution authority.",
        ),
        "1.0.0",
        "Evaluate only the provided EBP and produce a CDR decision.",
    )
    return repository


def commander_engine() -> tuple[CommanderDecisionEngine, CommanderOffice]:
    office = CommanderOffice(
        configuration_service=configuration_service(),
        persistence_repository=InMemoryPersistenceRepository(canonical_schemas()),
    )
    return CommanderDecisionEngine(office, prompt_repository(), "PROMPT-012"), office


def ebp(resize_factor: float | None = None) -> ExecutiveBriefingPacket:
    return ExecutiveBriefingPacket(
        ebp_id="EBP-001",
        case_file_id="CF-001",
        trade_cycle_id="TC-001",
        produced_by_staff_id="STF-005",
        produced_by_group_id="DEP-005",
        risk_recommendation_document_id="DOC-005",
        evidence_reference_ids=("DOC-006", "DOC-007"),
        summary="Risk-reviewed executive briefing.",
        recommended_action="approve",
        requested_resize_factor=resize_factor,
    )


class CommanderDecisionEngineTests(unittest.TestCase):
    def test_commander_rejects_non_ebp_input(self) -> None:
        engine, _ = commander_engine()

        with self.assertRaises(TypeError):
            engine.decide(  # type: ignore[arg-type]
                {"not": "an ebp"},
                CommanderDecision.APPROVE,
                "Approve based on evidence.",
                31,
                "DEP-005",
            )

    def test_each_supported_decision_path_generates_cdr(self) -> None:
        decisions = (
            CommanderDecision.APPROVE,
            CommanderDecision.REJECT,
            CommanderDecision.RESIZE,
            CommanderDecision.DEFER,
            CommanderDecision.REQUEST_MORE_ANALYSIS,
        )

        for offset, decision in enumerate(decisions, start=1):
            with self.subTest(decision=decision.value):
                engine, office = commander_engine()
                outcome = engine.decide(
                    ebp(resize_factor=0.5),
                    decision,
                    f"Deterministic rationale for {decision.value}.",
                    30 + offset,
                    "DEP-005",
                    resize_factor=0.5 if decision == CommanderDecision.RESIZE else None,
                )
                cdr_id = f"DOC-{30 + offset:03d}"
                latest = office.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, cdr_id)

                self.assertEqual(outcome.decision, decision)
                self.assertEqual(outcome.cdr_contract_id, cdr_id)
                self.assertIsNotNone(latest)
                self.assertEqual(latest.payload["contract_type"], "CDR")
                self.assertEqual(latest.payload["machine_payload"]["decision_type"], decision.value)
                self.assertIn("DOC-006", latest.payload["source_reference_ids"])
                self.assertIn("PS-000001", latest.payload["machine_payload"]["prompt_snapshot_id"])

    def test_resize_requires_positive_resize_factor(self) -> None:
        engine, _ = commander_engine()

        with self.assertRaises(ValueError):
            engine.decide(
                ebp(),
                CommanderDecision.RESIZE,
                "Resize without factor.",
                40,
                "DEP-005",
            )

    def test_prompt_snapshot_is_linked_to_case_file(self) -> None:
        engine, _ = commander_engine()

        outcome = engine.decide(
            ebp(),
            CommanderDecision.DEFER,
            "Defer pending additional timing evidence.",
            41,
            "DEP-005",
        )
        snapshots = engine.prompt_snapshot_service.search_by_case_file_id("CF-001")

        self.assertEqual(outcome.prompt_snapshot_id, "PS-000001")
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].prompt_id, "PROMPT-012")

    def test_ebp_requires_evidence_and_risk_reference(self) -> None:
        with self.assertRaises(ValueError):
            ExecutiveBriefingPacket(
                ebp_id="EBP-002",
                case_file_id="CF-001",
                trade_cycle_id="TC-001",
                produced_by_staff_id="STF-005",
                produced_by_group_id="DEP-005",
                risk_recommendation_document_id="BAD-005",
                evidence_reference_ids=("DOC-006",),
                summary="Bad risk reference.",
                recommended_action="approve",
            )
        with self.assertRaises(ValueError):
            ExecutiveBriefingPacket(
                ebp_id="EBP-003",
                case_file_id="CF-001",
                trade_cycle_id="TC-001",
                produced_by_staff_id="STF-005",
                produced_by_group_id="DEP-005",
                risk_recommendation_document_id="DOC-005",
                evidence_reference_ids=(),
                summary="Missing evidence.",
                recommended_action="approve",
            )


if __name__ == "__main__":
    unittest.main()

