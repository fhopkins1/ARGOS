"""Deterministic configuration loading, validation, and snapshotting."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import os
import re
from types import MappingProxyType
from typing import Mapping

from argos.foundation.identity import IdentifierKind, validate_identifier

from .environment import Environment, EnvironmentManager


SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class ConfigurationError(ValueError):
    """Raised when configuration cannot safely start ARGOS."""


class SecretProvider(str, Enum):
    """Supported secret provider references."""

    ENVIRONMENT_VARIABLE = "environment_variable"
    SECURE_PROVIDER = "secure_provider"


@dataclass(frozen=True)
class SecretReference:
    """Reference to a secret without storing the secret value."""

    name: str
    provider: SecretProvider
    key: str
    required: bool = True

    def resolve(self, environ: Mapping[str, str] | None = None) -> str | None:
        """Resolve a secret through an environment source."""
        source = os.environ if environ is None else environ
        if self.provider == SecretProvider.ENVIRONMENT_VARIABLE:
            return source.get(self.key)
        return source.get(self.key)

    def redacted(self) -> dict[str, object]:
        """Return snapshot-safe secret metadata."""
        return {
            "name": self.name,
            "provider": self.provider.value,
            "key": self.key,
            "required": self.required,
            "value": "<redacted>",
        }


@dataclass(frozen=True)
class FeatureFlag:
    """Deterministic feature flag."""

    name: str
    enabled: bool
    description: str = ""


@dataclass(frozen=True)
class Configuration:
    """Validated ARGOS configuration."""

    environment: Environment
    config_version: str
    schema_version: str
    log_level: str
    live_trading_enabled: bool
    feature_flags: Mapping[str, FeatureFlag] = field(default_factory=dict)
    secret_references: tuple[SecretReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.environment, Environment):
            object.__setattr__(self, "environment", Environment(self.environment))
        object.__setattr__(self, "feature_flags", MappingProxyType(dict(self.feature_flags)))
        object.__setattr__(self, "secret_references", tuple(self.secret_references))

    def to_snapshot_dict(self) -> dict[str, object]:
        """Return deterministic, secret-safe configuration data."""
        return {
            "config_version": self.config_version,
            "environment": self.environment.value,
            "feature_flags": {
                name: {
                    "description": flag.description,
                    "enabled": flag.enabled,
                    "name": flag.name,
                }
                for name, flag in sorted(self.feature_flags.items())
            },
            "live_trading_enabled": self.live_trading_enabled,
            "log_level": self.log_level,
            "schema_version": self.schema_version,
            "secret_references": [reference.redacted() for reference in self.secret_references],
        }


@dataclass(frozen=True)
class ConfigurationSnapshot:
    """Case File configuration snapshot."""

    case_file_id: str
    trade_cycle_id: str
    config_hash: str
    configuration: Mapping[str, object]


@dataclass
class ConfigurationService:
    """Foundation-owned configuration service."""

    environment_manager: EnvironmentManager
    configuration: Configuration
    environ: Mapping[str, str] = field(default_factory=lambda: os.environ)

    @classmethod
    def load(
        cls,
        raw_config: Mapping[str, object],
        environ: Mapping[str, str] | None = None,
    ) -> "ConfigurationService":
        """Load and validate configuration deterministically."""
        source = os.environ if environ is None else environ
        environment_manager = EnvironmentManager.from_value(str(raw_config["environment"]))
        configuration = Configuration(
            environment=environment_manager.active_environment,
            config_version=str(raw_config["config_version"]),
            schema_version=str(raw_config["schema_version"]),
            log_level=str(raw_config["log_level"]),
            live_trading_enabled=_bool_value(raw_config["live_trading_enabled"]),
            feature_flags=_load_feature_flags(raw_config.get("feature_flags", {})),
            secret_references=_load_secret_references(raw_config.get("secret_references", ())),
        )
        service = cls(environment_manager, configuration, source)
        service.validate_startup()
        return service

    def validate_startup(self) -> None:
        """Validate configuration before startup."""
        errors: list[str] = []
        if not SEMVER_PATTERN.fullmatch(self.configuration.config_version):
            errors.append("config_version must use Major.Minor.Revision semantic versioning")
        if not SEMVER_PATTERN.fullmatch(self.configuration.schema_version):
            errors.append("schema_version must use Major.Minor.Revision semantic versioning")
        if self.configuration.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            errors.append("log_level is unsupported")
        if self.configuration.live_trading_enabled:
            errors.append("live trading cannot be enabled by EO-006 configuration")

        for reference in self.configuration.secret_references:
            if reference.required and not reference.resolve(self.environ):
                errors.append(f"required secret is missing: {reference.name}")

        if errors:
            raise ConfigurationError("; ".join(errors))

    def switch_environment(self, value: str | Environment) -> Configuration:
        """Switch environment and revalidate startup."""
        environment = self.environment_manager.switch(value)
        self.configuration = Configuration(
            environment=environment,
            config_version=self.configuration.config_version,
            schema_version=self.configuration.schema_version,
            log_level=self.configuration.log_level,
            live_trading_enabled=self.configuration.live_trading_enabled,
            feature_flags=self.configuration.feature_flags,
            secret_references=self.configuration.secret_references,
        )
        self.validate_startup()
        return self.configuration

    def is_feature_enabled(self, name: str) -> bool:
        """Return whether a feature flag is enabled."""
        return self.configuration.feature_flags.get(name, FeatureFlag(name, False)).enabled

    def snapshot_for_case_file(self, case_file_id: str, trade_cycle_id: str) -> ConfigurationSnapshot:
        """Create a deterministic, secret-safe configuration snapshot."""
        _require_identifier_kind(case_file_id, IdentifierKind.CASE_FILE)
        _require_identifier_kind(trade_cycle_id, IdentifierKind.TRADE_CYCLE)
        snapshot_data = self.configuration.to_snapshot_dict()
        encoded = json.dumps(snapshot_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return ConfigurationSnapshot(
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            config_hash=hashlib.sha256(encoded).hexdigest(),
            configuration=MappingProxyType(snapshot_data),
        )


def _load_feature_flags(raw_flags: object) -> dict[str, FeatureFlag]:
    if not isinstance(raw_flags, Mapping):
        raise ConfigurationError("feature_flags must be a mapping")
    flags: dict[str, FeatureFlag] = {}
    for name, raw_flag in raw_flags.items():
        if isinstance(raw_flag, FeatureFlag):
            flags[str(name)] = raw_flag
            continue
        if isinstance(raw_flag, bool):
            flags[str(name)] = FeatureFlag(str(name), raw_flag)
            continue
        if not isinstance(raw_flag, Mapping):
            raise ConfigurationError(f"feature flag must be bool or mapping: {name}")
        flags[str(name)] = FeatureFlag(
            name=str(raw_flag.get("name", name)),
            enabled=_bool_value(raw_flag["enabled"]),
            description=str(raw_flag.get("description", "")),
        )
    return flags


def _load_secret_references(raw_references: object) -> tuple[SecretReference, ...]:
    if not isinstance(raw_references, (list, tuple)):
        raise ConfigurationError("secret_references must be a list")
    references: list[SecretReference] = []
    for raw_reference in raw_references:
        if isinstance(raw_reference, SecretReference):
            references.append(raw_reference)
            continue
        if not isinstance(raw_reference, Mapping):
            raise ConfigurationError("secret reference must be a mapping")
        references.append(
            SecretReference(
                name=str(raw_reference["name"]),
                provider=SecretProvider(str(raw_reference["provider"])),
                key=str(raw_reference["key"]),
                required=_bool_value(raw_reference.get("required", True)),
            )
        )
    return tuple(references)


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    raise ConfigurationError(f"expected boolean value, got {value!r}")


def _require_identifier_kind(identifier: str, expected_kind: IdentifierKind) -> None:
    result = validate_identifier(identifier)
    if not result.is_valid or result.kind != expected_kind:
        raise ConfigurationError(f"invalid {expected_kind.value} identifier: {identifier}")

