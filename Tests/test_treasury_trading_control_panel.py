from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.executive import (  # noqa: E402
    ARGOSControlPanel,
    ControlAction,
    ControlActionStatus,
    HumanAuthority,
    HumanOverrideService,
    OverrideLevel,
    RealWorldTradingGate,
)
from argos.foundation.audit import AuditEventType, AuditService  # noqa: E402
from argos.foundation.configuration import ConfigurationService  # noqa: E402
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType, canonical_schemas  # noqa: E402


def config() -> ConfigurationService:
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


def authority() -> HumanAuthority:
    return HumanAuthority("AUTH-001", "STF-001", OverrideLevel.LEVEL_6_EMERGENCY_LIQUIDATION)


def panel() -> ARGOSControlPanel:
    audit = AuditService()
    persistence = InMemoryPersistenceRepository(canonical_schemas())
    override = HumanOverrideService(audit, persistence)
    return ARGOSControlPanel(config(), persistence, audit, override)


class TreasuryTradingControlPanelTests(unittest.TestCase):
    def test_initiate_and_halt_paper_trading_for_self_training(self) -> None:
        control = panel()

        start = control.initiate_paper_trading_self_training(authority(), "Start self-training.")
        halt = control.halt_paper_trading_self_training(authority(), "Halt paper trading.")

        self.assertEqual(start.action, ControlAction.INITIATE_PAPER_TRADING)
        self.assertEqual(start.status, ControlActionStatus.APPLIED)
        self.assertEqual(control.configuration_service.configuration.environment.value, "paper_trading")
        self.assertEqual(halt.action, ControlAction.HALT_PAPER_TRADING)
        self.assertFalse(control.paper_trading_active)
        self.assertTrue(control.override_service.trading_paused)

    def test_deposit_and_halt_user_funds_into_active_treasury(self) -> None:
        control = panel()

        deposit = control.deposit_user_funds_to_active_treasury(authority(), "USER-001", 2500.125, "Fund active treasury.")
        halt = control.halt_user_funds_into_active_treasury(authority(), "Stop treasury deposits.")
        denied = control.deposit_user_funds_to_active_treasury(authority(), "USER-001", 10.0, "Should be blocked.")

        self.assertEqual(deposit.status, ControlActionStatus.APPLIED)
        self.assertEqual(control.active_treasury_balance_usd, 2500.12)
        self.assertEqual(halt.action, ControlAction.HALT_USER_FUNDS)
        self.assertTrue(control.user_funds_halted)
        self.assertEqual(denied.status, ControlActionStatus.DENIED)
        self.assertIn("user_funds_deposits_halted", denied.denial_reasons)

    def test_initiate_real_world_trading_control_exists_but_is_denied_by_default(self) -> None:
        control = panel()
        control.deposit_user_funds_to_active_treasury(authority(), "USER-001", 1000.0, "Fund treasury.")
        gates = RealWorldTradingGate(
            user_approval=True,
            broker_controls_verified=True,
            risk_certification_verified=True,
            treasury_funded=True,
            human_override_clear=True,
            live_trading_configuration_authorized=True,
        )

        record = control.initiate_real_world_trading_from_active_treasury(authority(), gates, "Request live trading.")

        self.assertEqual(record.action, ControlAction.INITIATE_REAL_WORLD_TRADING)
        self.assertEqual(record.status, ControlActionStatus.DENIED)
        self.assertFalse(control.real_world_trading_active)
        self.assertIn("configuration_live_trading_disabled", record.denial_reasons)

    def test_halt_real_world_trading_control_uses_trading_pause(self) -> None:
        control = panel()
        control.real_world_trading_active = True

        record = control.halt_real_world_trading(authority(), "Emergency halt.")

        self.assertEqual(record.action, ControlAction.HALT_REAL_WORLD_TRADING)
        self.assertEqual(record.status, ControlActionStatus.APPLIED)
        self.assertFalse(control.real_world_trading_active)
        self.assertTrue(control.override_service.trading_paused)

    def test_visible_snapshot_is_immediately_user_visible(self) -> None:
        control = panel()
        control.initiate_paper_trading_self_training(authority(), "Start self-training.")
        control.deposit_user_funds_to_active_treasury(authority(), "USER-001", 500.0, "Fund treasury.")

        snapshot = control.visible_snapshot()

        self.assertTrue(snapshot.visible_to_user)
        self.assertTrue(snapshot.paper_trading_active)
        self.assertEqual(snapshot.active_treasury_balance_usd, 500.0)
        self.assertEqual(snapshot.latest_action_id, "CPA-000002")

    def test_control_actions_are_persisted_and_audited(self) -> None:
        control = panel()

        record = control.deposit_user_funds_to_active_treasury(authority(), "USER-001", 100.0, "Fund treasury.")

        self.assertIsNotNone(control.persistence_repository.latest(ObjectType.OPERATIONAL_DOCUMENT, "DOC-8701"))
        self.assertEqual(control.actions[-1].action_id, record.action_id)
        event_types = tuple(event.event_type for event in control.audit_service.audit_log.events)
        self.assertIn(AuditEventType.STAFF_DECISION, event_types)
        self.assertTrue(control.audit_service.audit_log.verify_integrity())


if __name__ == "__main__":
    unittest.main()
