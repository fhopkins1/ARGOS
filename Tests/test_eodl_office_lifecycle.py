from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import (  # noqa: E402
    CanonicalBridgeExecutor,
    OfficeActivationAuthority,
    OfficeClassification,
    OfficeDefinition,
    OfficeLifecycleController,
    OfficeLifecycleState,
    OfficeRejectionCode,
    OfficeRegistry,
    default_office_definitions,
    duplicate_role_analysis,
    office_component_inventory,
)


def office(office_id: str = "Seeker", *, classification: OfficeClassification = OfficeClassification.CORE_PRODUCTION, ownership: bool = True, ingress: tuple[str, ...] = ("BRIDGE-WORKFLOW-OFFICE-001",), egress: tuple[str, ...] = ("BRIDGE-SEEKER-ANALYST-001",), authorities: tuple[OfficeActivationAuthority, ...] = (OfficeActivationAuthority.CANONICAL_BRIDGE, OfficeActivationAuthority.COMMANDER), enabled: bool | None = None) -> OfficeDefinition:
    return OfficeDefinition(
        office_id,
        office_id,
        "test",
        "tests",
        classification,
        "test office role",
        ("paper",),
        ("PAPER",),
        ownership,
        authorities,
        ingress,
        egress,
        (),
        (),
        True,
        True,
        OfficeLifecycleState.DORMANT,
        "no background work",
        "singleton",
        classification not in {OfficeClassification.RETIRED, OfficeClassification.PROHIBITED, OfficeClassification.FUTURE_RESERVED} if enabled is None else enabled,
        classification == OfficeClassification.CORE_PRODUCTION,
    )


class EODLOfficeLifecycleTests(unittest.TestCase):
    def test_registry_rejects_duplicate_and_enabled_prohibited_offices(self) -> None:
        with self.assertRaises(ValueError):
            OfficeRegistry((office("A"), office("A")))
        with self.assertRaises(ValueError):
            OfficeRegistry((office("Bad", classification=OfficeClassification.PROHIBITED, enabled=True),))

    def test_activation_requires_authority_and_token_for_ownership_office(self) -> None:
        controller = OfficeLifecycleController(registry=OfficeRegistry((office("Seeker"),)))
        missing = controller.activate("Seeker", authority=OfficeActivationAuthority.CANONICAL_BRIDGE, workflow_id="WF-1", current_owner="Seeker")
        self.assertEqual(missing.rejection_code, OfficeRejectionCode.OFFICE_TOKEN_REQUIRED)
        accepted = controller.activate("Seeker", authority=OfficeActivationAuthority.CANONICAL_BRIDGE, workflow_id="WF-1", token_id="TOK-1", current_owner="Seeker")
        self.assertTrue(accepted.accepted)
        self.assertEqual(controller.state("Seeker").state, OfficeLifecycleState.ACTIVE)

    def test_dormant_office_cannot_mutate_workflow_state(self) -> None:
        controller = OfficeLifecycleController(registry=OfficeRegistry((office("Risk"),)))
        result = controller.reject_dormant_mutation("Risk", "create a decision")
        self.assertFalse(result.accepted)
        self.assertEqual(result.rejection_code, OfficeRejectionCode.OFFICE_DORMANT_MUTATION_REJECTED)

    def test_information_delivery_does_not_activate_ownership(self) -> None:
        controller = OfficeLifecycleController(registry=OfficeRegistry((office("Historian", classification=OfficeClassification.INFORMATION_ONLY, ownership=False, ingress=("BRIDGE-PT-HISTORIAN-001",), egress=()),)))
        result = controller.deliver_information("Historian", workflow_id="WF-2", artifact_id="PT-1", payload={"pt": "1"})
        self.assertTrue(result.accepted)
        self.assertEqual(controller.state("Historian").state, OfficeLifecycleState.DORMANT)

    def test_handoff_returns_source_to_dormant(self) -> None:
        executor = CanonicalBridgeExecutor(runtime_instance_id="R1")
        executor.ownership.establish("WF-3", "Seeker", "TOK-3")
        controller = OfficeLifecycleController(registry=OfficeRegistry((office("Seeker"),)), bridge_executor=executor)
        controller.activate("Seeker", authority=OfficeActivationAuthority.CANONICAL_BRIDGE, workflow_id="WF-3", token_id="TOK-3", current_owner="Seeker")
        result = controller.handoff_to_dormant("Seeker", bridge_id="BRIDGE-SEEKER-ANALYST-001", workflow_id="WF-3", token_id="TOK-3", next_owner="Analyst", artifact_id="SEEK-1", payload={"artifact": "seeker report"})
        self.assertTrue(result.accepted)
        self.assertEqual(controller.state("Seeker").state, OfficeLifecycleState.DORMANT)
        self.assertEqual(executor.ownership.owner("WF-3"), "Analyst")

    def test_future_reserved_and_retired_offices_reject_activation(self) -> None:
        future = office("Future", classification=OfficeClassification.FUTURE_RESERVED)
        retired = office("Retired", classification=OfficeClassification.RETIRED)
        controller = OfficeLifecycleController(registry=OfficeRegistry((future, retired)))
        self.assertEqual(controller.activate("Future", authority=OfficeActivationAuthority.COMMANDER, workflow_id="WF").rejection_code, OfficeRejectionCode.OFFICE_FUTURE_RESERVED)
        self.assertEqual(controller.activate("Retired", authority=OfficeActivationAuthority.COMMANDER, workflow_id="WF").rejection_code, OfficeRejectionCode.OFFICE_RETIRED)

    def test_lifecycle_transition_rules_and_read_side_are_nonmutating(self) -> None:
        controller = OfficeLifecycleController(registry=OfficeRegistry((office("Analyst"),)))
        before = controller.read_only_snapshot()
        after = controller.read_only_snapshot()
        self.assertEqual(before, after)
        self.assertFalse(controller.transition("Analyst", OfficeLifecycleState.ACTIVE).accepted)
        self.assertTrue(controller.transition("Analyst", OfficeLifecycleState.ACTIVATION_PENDING).accepted)

    def test_orphan_and_duplicate_role_analysis_are_machine_readable(self) -> None:
        definitions = (
            office("NoIngress", ingress=(), authorities=(OfficeActivationAuthority.CANONICAL_BRIDGE,)),
            office("NoEgress", egress=()),
        )
        controller = OfficeLifecycleController(registry=OfficeRegistry(definitions))
        orphaned = {row["office_id"]: row for row in controller.orphan_analysis()}
        self.assertTrue(orphaned["NoIngress"]["orphan"])
        self.assertTrue(orphaned["NoEgress"]["orphan"])
        self.assertIsInstance(duplicate_role_analysis(definitions), tuple)
        self.assertTrue(office_component_inventory(REPOSITORY_ROOT))

    def test_default_office_definitions_are_classified(self) -> None:
        definitions = default_office_definitions()
        self.assertTrue(definitions)
        self.assertTrue(all(definition.classification for definition in definitions))


if __name__ == "__main__":
    unittest.main()
