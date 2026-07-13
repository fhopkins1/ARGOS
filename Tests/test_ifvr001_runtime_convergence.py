import inspect
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import (  # noqa: E402
    CanonicalEnterpriseRuntime,
    RuntimeProviderError,
    create_runtime,
    create_runtime_provider_for_tests,
    get_server_runtime_provider,
    reset_server_runtime_provider_for_tests,
)
from argos.control_panel import server  # noqa: E402


class IFVR001RuntimeConvergenceTests(unittest.TestCase):
    def tearDown(self) -> None:
        reset_server_runtime_provider_for_tests()

    def test_server_provider_is_single_canonical_runtime_for_process(self) -> None:
        first = get_server_runtime_provider()
        second = get_server_runtime_provider()

        self.assertIs(first, second)
        self.assertIsInstance(first.runtime, CanonicalEnterpriseRuntime)
        self.assertFalse(first.runtime.live_trading_enabled)
        self.assertEqual(first.status().runtime_identity, id(first.runtime))

    def test_repeated_start_and_halt_are_idempotent(self) -> None:
        provider = create_runtime_provider_for_tests()

        first_start = provider.start()
        second_start = provider.start()
        first_halt = provider.halt(reason="IFVR test halt")
        second_halt = provider.halt(reason="IFVR repeated halt")

        self.assertEqual(1, first_start["startCount"])
        self.assertEqual(1, second_start["startCount"])
        self.assertEqual("halted", first_halt["mode"])
        self.assertEqual("halted", second_halt["mode"])
        self.assertFalse(provider.status().started)

    def test_legacy_runtime_uses_canonical_stateful_authorities(self) -> None:
        runtime = create_runtime()
        canonical = runtime.canonical_runtime.components

        self.assertIs(runtime.workflow_orchestrator, canonical.workflow_orchestrator)
        self.assertIs(runtime.performance_truth_engine, canonical.performance_truth)
        self.assertIs(runtime.position_monitoring_network, canonical.position_monitoring)
        self.assertIs(runtime.enterprise_communications_bus, canonical.communications_bus)
        self.assertIs(runtime.enterprise_cost_governor, canonical.cost_governor)
        self.assertIs(runtime.enterprise_doctrine_policy_manager, canonical.doctrine_policy)

    def test_read_only_snapshot_does_not_mutate_canonical_runtime(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        runtime.start()
        before = runtime.read_only_digest()

        for _ in range(5):
            runtime.read_only_snapshot()

        self.assertEqual(before, runtime.read_only_digest())

    def test_provider_rejects_live_runtime_injection(self) -> None:
        with self.assertRaises(RuntimeProviderError):
            create_runtime_provider_for_tests(CanonicalEnterpriseRuntime(live_trading_enabled=True))

    def test_server_source_does_not_eagerly_construct_legacy_runtime(self) -> None:
        source = inspect.getsource(server.run)

        self.assertIn("get_server_runtime_provider()", source)
        self.assertNotIn("runtime = create_runtime()", source)
        self.assertIn("_CompatibilityRuntimeProxy()", source)

    def test_stateful_authority_diagnostics_are_unique(self) -> None:
        runtime = CanonicalEnterpriseRuntime()
        runtime.start()

        diagnostics = runtime.stateful_authority_diagnostics()

        self.assertTrue(diagnostics)
        self.assertEqual((), runtime.stateful_authority_duplicates())
        self.assertFalse(any(item.duplicate for item in diagnostics))


if __name__ == "__main__":
    unittest.main()
