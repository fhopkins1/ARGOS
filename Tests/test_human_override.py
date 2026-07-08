from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.executive import (  # noqa: E402
    HumanAuthority,
    HumanAuthorityPanel,
    HumanOverrideService,
    OverrideAction,
    OverrideLevel,
)
from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402


def service() -> HumanOverrideService:
    return HumanOverrideService(AuditService(), InMemoryPersistenceRepository(canonical_schemas()))


def authority(level: OverrideLevel = OverrideLevel.LEVEL_6_EMERGENCY_LIQUIDATION) -> HumanAuthority:
    return HumanAuthority("AUTH-001", "STF-001", level)


class HumanOverrideTests(unittest.TestCase):
    def test_override_authorization_blocks_unauthorized_level(self) -> None:
        overrides = service()

        with self.assertRaises(PermissionError):
            overrides.apply_override(
                OverrideAction.ORGANIZATION_LOCKDOWN,
                authority(OverrideLevel.LEVEL_1_EXECUTIVE_PAUSE),
                "Insufficient authority.",
            )

    def test_executive_pause_and_resume(self) -> None:
        overrides = service()
        panel = HumanAuthorityPanel(overrides, authority())

        panel.trigger(OverrideAction.EXECUTIVE_PAUSE, "Pause Executive decisions.")
        self.assertTrue(overrides.executive_paused)
        with self.assertRaises(PermissionError):
            overrides.assert_commander_allowed()

        panel.resume("Resume Executive decisions.")
        self.assertFalse(overrides.executive_paused)
        overrides.assert_commander_allowed()

    def test_trading_pause_and_emergency_liquidation_flags(self) -> None:
        overrides = service()
        overrides.apply_override(OverrideAction.TRADING_PAUSE, authority(), "Pause trading.")
        self.assertTrue(overrides.trading_paused)

        overrides.resume(authority(), "Recover.")
        overrides.apply_override(
            OverrideAction.EMERGENCY_LIQUIDATION,
            authority(),
            "Activate emergency liquidation control.",
        )
        self.assertTrue(overrides.emergency_liquidation_active)
        self.assertEqual(overrides.current_level, OverrideLevel.LEVEL_6_EMERGENCY_LIQUIDATION)

    def test_organization_lockdown_blocks_courier(self) -> None:
        overrides = service()
        overrides.apply_override(OverrideAction.ORGANIZATION_LOCKDOWN, authority(), "Lockdown.")

        with self.assertRaises(PermissionError):
            overrides.assert_courier_allowed()

    def test_replay_and_read_only_modes_block_writes(self) -> None:
        overrides = service()
        overrides.apply_override(OverrideAction.REPLAY_MODE, authority(), "Replay only.")
        with self.assertRaises(PermissionError):
            overrides.assert_persistence_write_allowed()

        overrides.resume(authority(), "Recover.")
        overrides.apply_override(OverrideAction.READ_ONLY_MODE, authority(), "Read only.")
        with self.assertRaises(PermissionError):
            overrides.assert_persistence_write_allowed()
        with self.assertRaises(PermissionError):
            overrides.assert_commander_allowed()

    def test_override_records_are_append_only_and_persisted(self) -> None:
        overrides = service()
        first = overrides.apply_override(OverrideAction.EXECUTIVE_PAUSE, authority(), "Pause.")
        second = overrides.resume(authority(), "Resume.")

        self.assertEqual([record.override_id for record in overrides.records], ["OVR-000001", "OVR-000002"])
        self.assertEqual(first.action, OverrideAction.EXECUTIVE_PAUSE)
        self.assertEqual(second.action, OverrideAction.RESUME)
        self.assertIsNotNone(
            overrides.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-000001")
        )
        self.assertIsNotNone(
            overrides.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-000002")
        )

    def test_override_actions_generate_audit_events_and_preserve_integrity(self) -> None:
        overrides = service()
        overrides.apply_override(OverrideAction.READ_ONLY_MODE, authority(), "Read only.")

        event_types = [event.event_type for event in overrides.audit_service.audit_log.events]
        self.assertIn(AuditEventType.STAFF_DECISION, event_types)
        self.assertTrue(overrides.audit_service.audit_log.verify_integrity())
        self.assertTrue(overrides.persistence_repository.validate_integrity())

    def test_recovery_after_override_restores_normal_state(self) -> None:
        overrides = service()
        overrides.apply_override(OverrideAction.ORGANIZATION_LOCKDOWN, authority(), "Lockdown.")
        overrides.resume(authority(), "Recover.")

        self.assertEqual(overrides.current_level, OverrideLevel.LEVEL_0_NORMAL)
        overrides.assert_commander_allowed()
        overrides.assert_courier_allowed()
        overrides.assert_persistence_write_allowed()


if __name__ == "__main__":
    unittest.main()

