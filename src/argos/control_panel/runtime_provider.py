"""Canonical production runtime provider for ARGOS server entry points."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from threading import RLock
from typing import Any

from argos.foundation.contracts import utc_timestamp

from .canonical_enterprise_runtime import CanonicalEnterpriseRuntime, CanonicalRuntimeMode


class RuntimeProviderError(RuntimeError):
    """Raised when a non-canonical runtime is supplied to a production entry point."""


@dataclass(frozen=True)
class RuntimeProviderStatus:
    provider_id: str
    created_at_utc: str
    runtime_identity: int
    runtime_class: str
    mode: str
    truth_domain: str
    health: str
    canonical_singleton_for_process: bool
    started: bool
    halt_in_progress: bool
    live_trading_enabled: bool


class CanonicalRuntimeProvider:
    """Owns the single production authority graph for one server process."""

    def __init__(self, runtime: CanonicalEnterpriseRuntime | None = None) -> None:
        self._lock = RLock()
        self.created_at_utc = utc_timestamp()
        self.provider_id = f"IFVR-RUNTIME-PROVIDER-{self.created_at_utc}"
        self._runtime = runtime or CanonicalEnterpriseRuntime()
        self._assert_runtime_allowed(self._runtime)

    @property
    def runtime(self) -> CanonicalEnterpriseRuntime:
        return self._runtime

    def start(self) -> dict[str, Any]:
        with self._lock:
            return self._runtime.start()

    def halt(self, *, reason: str = "Server runtime provider halt requested.") -> dict[str, Any]:
        with self._lock:
            return self._runtime.halt(reason=reason)

    def status(self) -> RuntimeProviderStatus:
        snapshot = self._runtime.read_only_snapshot()
        mode = str(snapshot.get("mode", "unknown"))
        return RuntimeProviderStatus(
            provider_id=self.provider_id,
            created_at_utc=self.created_at_utc,
            runtime_identity=id(self._runtime),
            runtime_class=self._runtime.__class__.__name__,
            mode=mode,
            truth_domain=str(snapshot.get("truthDomain", "UNKNOWN")),
            health="READY" if not self._runtime.stateful_authority_duplicates() else "FAULTED",
            canonical_singleton_for_process=True,
            started=bool(snapshot.get("loopStarted", False)),
            halt_in_progress=mode == CanonicalRuntimeMode.HALTING.value,
            live_trading_enabled=bool(self._runtime.live_trading_enabled),
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "provider": asdict(self.status()),
            "runtime": self._runtime.read_only_snapshot(),
            "runtimeStatus": self._runtime.runtime_status(),
        }

    @staticmethod
    def _assert_runtime_allowed(runtime: CanonicalEnterpriseRuntime) -> None:
        if not isinstance(runtime, CanonicalEnterpriseRuntime):
            raise RuntimeProviderError("PRODUCTION_RUNTIME_MUST_BE_CANONICAL")
        if runtime.live_trading_enabled:
            raise RuntimeProviderError("LIVE_TRADING_DISABLED")


_SERVER_RUNTIME_PROVIDER: CanonicalRuntimeProvider | None = None
_SERVER_PROVIDER_LOCK = RLock()


def get_server_runtime_provider() -> CanonicalRuntimeProvider:
    """Return the one canonical production runtime provider for this process."""
    global _SERVER_RUNTIME_PROVIDER
    with _SERVER_PROVIDER_LOCK:
        if _SERVER_RUNTIME_PROVIDER is None:
            _SERVER_RUNTIME_PROVIDER = CanonicalRuntimeProvider()
        return _SERVER_RUNTIME_PROVIDER


def reset_server_runtime_provider_for_tests() -> None:
    """Reset the process provider for isolated tests only."""
    global _SERVER_RUNTIME_PROVIDER
    with _SERVER_PROVIDER_LOCK:
        _SERVER_RUNTIME_PROVIDER = None


def create_runtime_provider_for_tests(runtime: CanonicalEnterpriseRuntime | None = None) -> CanonicalRuntimeProvider:
    """Create an isolated canonical provider without mutating the server singleton."""
    return CanonicalRuntimeProvider(runtime)
