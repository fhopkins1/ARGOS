from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.configuration import (  # noqa: E402
    ARGOS_ENVIRONMENTS,
    ConfigurationError,
    ConfigurationService,
    Environment,
    EnvironmentManager,
    SecretReference,
)


def raw_config(environment: str = "development") -> dict[str, object]:
    return {
        "environment": environment,
        "config_version": "1.0.0",
        "schema_version": "1.0.0",
        "log_level": "INFO",
        "live_trading_enabled": False,
        "feature_flags": {
            "audit_replay": {"enabled": True, "description": "Replay audit logs."},
            "experimental_ui": False,
        },
        "secret_references": [
            {
                "name": "example",
                "provider": "environment_variable",
                "key": "ARGOS_EXAMPLE_SECRET",
                "required": True,
            }
        ],
    }


class ConfigurationFrameworkTests(unittest.TestCase):
    def test_configuration_loads_deterministically(self) -> None:
        environ = {"ARGOS_EXAMPLE_SECRET": "not-stored"}
        first = ConfigurationService.load(raw_config(), environ)
        second = ConfigurationService.load(raw_config(), environ)

        self.assertEqual(first.configuration.to_snapshot_dict(), second.configuration.to_snapshot_dict())
        self.assertEqual(first.configuration.environment, Environment.DEVELOPMENT)

    def test_every_supported_environment_validates(self) -> None:
        environ = {"ARGOS_EXAMPLE_SECRET": "not-stored"}

        for environment in ARGOS_ENVIRONMENTS:
            with self.subTest(environment=environment.value):
                service = ConfigurationService.load(raw_config(environment.value), environ)
                self.assertEqual(service.configuration.environment, environment)

    def test_invalid_configuration_cannot_start_system(self) -> None:
        config = raw_config()
        config["live_trading_enabled"] = True

        with self.assertRaises(ConfigurationError) as context:
            ConfigurationService.load(config, {"ARGOS_EXAMPLE_SECRET": "not-stored"})

        self.assertIn("live trading cannot be enabled", str(context.exception))

    def test_missing_required_secret_fails_validation(self) -> None:
        with self.assertRaises(ConfigurationError) as context:
            ConfigurationService.load(raw_config(), {})

        self.assertIn("required secret is missing: example", str(context.exception))

    def test_secret_reference_resolves_without_snapshot_exposure(self) -> None:
        service = ConfigurationService.load(raw_config(), {"ARGOS_EXAMPLE_SECRET": "super-secret"})
        reference = service.configuration.secret_references[0]
        snapshot = service.snapshot_for_case_file("CF-001", "TC-001")

        self.assertIsInstance(reference, SecretReference)
        self.assertEqual(reference.resolve({"ARGOS_EXAMPLE_SECRET": "super-secret"}), "super-secret")
        self.assertEqual(
            snapshot.configuration["secret_references"][0]["value"],
            "<redacted>",
        )
        self.assertNotIn("super-secret", str(snapshot.configuration))

    def test_feature_flags_are_supported(self) -> None:
        service = ConfigurationService.load(raw_config(), {"ARGOS_EXAMPLE_SECRET": "not-stored"})

        self.assertTrue(service.is_feature_enabled("audit_replay"))
        self.assertFalse(service.is_feature_enabled("experimental_ui"))
        self.assertFalse(service.is_feature_enabled("missing_flag"))

    def test_version_validation_rejects_non_semver(self) -> None:
        config = raw_config()
        config["config_version"] = "v1"

        with self.assertRaises(ConfigurationError) as context:
            ConfigurationService.load(config, {"ARGOS_EXAMPLE_SECRET": "not-stored"})

        self.assertIn("config_version", str(context.exception))

    def test_snapshotting_is_deterministic_and_bound_to_case_file(self) -> None:
        service = ConfigurationService.load(raw_config(), {"ARGOS_EXAMPLE_SECRET": "not-stored"})

        first = service.snapshot_for_case_file("CF-001", "TC-001")
        second = service.snapshot_for_case_file("CF-001", "TC-001")

        self.assertEqual(first.case_file_id, "CF-001")
        self.assertEqual(first.trade_cycle_id, "TC-001")
        self.assertEqual(first.config_hash, second.config_hash)
        self.assertEqual(len(first.config_hash), 64)

    def test_snapshot_rejects_malformed_identifiers(self) -> None:
        service = ConfigurationService.load(raw_config(), {"ARGOS_EXAMPLE_SECRET": "not-stored"})

        with self.assertRaises(ConfigurationError):
            service.snapshot_for_case_file("DOC-001", "TC-001")
        with self.assertRaises(ConfigurationError):
            service.snapshot_for_case_file("CF-001", "DOC-001")

    def test_environment_switching_revalidates_configuration(self) -> None:
        service = ConfigurationService.load(raw_config(), {"ARGOS_EXAMPLE_SECRET": "not-stored"})

        switched = service.switch_environment("paper_trading")

        self.assertEqual(switched.environment, Environment.PAPER_TRADING)
        self.assertEqual(service.environment_manager.active_environment, Environment.PAPER_TRADING)

    def test_environment_manager_rejects_unknown_environment(self) -> None:
        with self.assertRaises(ValueError):
            EnvironmentManager.from_value("sandbox")


if __name__ == "__main__":
    unittest.main()

