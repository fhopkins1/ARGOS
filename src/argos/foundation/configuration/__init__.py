"""Foundation-owned deterministic configuration framework."""

from .environment import ARGOS_ENVIRONMENTS, Environment, EnvironmentManager
from .service import (
    Configuration,
    ConfigurationError,
    ConfigurationService,
    ConfigurationSnapshot,
    FeatureFlag,
    SecretReference,
)

__all__ = [
    "ARGOS_ENVIRONMENTS",
    "Configuration",
    "ConfigurationError",
    "ConfigurationService",
    "ConfigurationSnapshot",
    "Environment",
    "EnvironmentManager",
    "FeatureFlag",
    "SecretReference",
]

