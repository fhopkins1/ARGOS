"""ARGOS runtime environment management."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Environment(str, Enum):
    """Supported ARGOS runtime environments."""

    DEVELOPMENT = "development"
    PAPER_TRADING = "paper_trading"
    HISTORICAL_REPLAY = "historical_replay"
    INTEGRATION_TESTING = "integration_testing"
    STAGING = "staging"
    PRODUCTION = "production"


ARGOS_ENVIRONMENTS: tuple[Environment, ...] = (
    Environment.DEVELOPMENT,
    Environment.PAPER_TRADING,
    Environment.HISTORICAL_REPLAY,
    Environment.INTEGRATION_TESTING,
    Environment.STAGING,
    Environment.PRODUCTION,
)


@dataclass
class EnvironmentManager:
    """Manage the active ARGOS environment."""

    active_environment: Environment

    @classmethod
    def from_value(cls, value: str | Environment) -> "EnvironmentManager":
        """Create an Environment Manager from a string or enum value."""
        return cls(_normalize_environment(value))

    def switch(self, value: str | Environment) -> Environment:
        """Switch to a supported environment."""
        self.active_environment = _normalize_environment(value)
        return self.active_environment

    def is_production(self) -> bool:
        """Return whether the active environment is production."""
        return self.active_environment == Environment.PRODUCTION


def _normalize_environment(value: str | Environment) -> Environment:
    if isinstance(value, Environment):
        return value
    try:
        return Environment(value)
    except ValueError as exc:
        allowed = ", ".join(environment.value for environment in ARGOS_ENVIRONMENTS)
        raise ValueError(f"unsupported ARGOS environment: {value}; expected one of {allowed}") from exc

