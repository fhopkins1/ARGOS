import asyncio
import inspect
import unittest

from argos.control_panel.read_only_integrity import (
    ReadCertificationStatus,
    ReadCounterSnapshot,
    ReadFindingClass,
    ReadIntegrityStatus,
    ReadOnlyIntegrityGuard,
    ReadSurfaceDefinition,
    ReadSurfaceRegistry,
    ReadSurfaceType,
    SemanticDigestEngine,
    protected_state_registry,
    read_surface_registry,
    semantic_digest_profiles,
)


def authoritative_state(**overrides):
    state = {
        "runtime": {"mode": "paper", "started": False, "requestCount": 1},
        "workflows": ({"workflow_id": "wf-1", "token": {"owner": "Trader", "status": "Active"}},),
        "broker": {"orders": (), "fills": (), "cash": 100000.0},
        "positions": {"open": (), "closed": (), "history": ()},
        "truth": {"performanceTruth": (), "closedPositionTruth": (), "promotionDecisions": ()},
        "transactions": {"intents": (), "journal": (), "outbox": ()},
        "governance": {"policy": "policy-1", "doctrine": "doctrine-1"},
        "cost": {"apiCalls": 0, "totalCost": 0.0},
        "assurance": {"violations": (), "faultCampaigns": (), "enduranceCampaigns": ()},
    }
    state.update(overrides)
    return state


class ReadOnlyIntegrityTests(unittest.TestCase):
    def test_digest_equivalent_state_normalizes_order_and_ignores_ephemeral_metadata(self):
        engine = SemanticDigestEngine()
        first = {
            "positions": [{"position_id": "p2", "quantity": 1.0000000001}, {"position_id": "p1", "quantity": 2.0}],
            "timestampUtc": "now",
            "requestCount": 10,
        }
        second = {
            "requestCount": 99,
            "positions": [{"quantity": 2.0, "position_id": "p1"}, {"quantity": 1.0000000002, "position_id": "p2"}],
            "timestampUtc": "later",
        }

        self.assertEqual(engine.digest(first), engine.digest(second))

    def test_authoritative_mutation_changes_digest_and_cross_domain_profiles_are_separate(self):
        engine = SemanticDigestEngine()
        before = authoritative_state()
        after = authoritative_state(broker={"orders": ({"order_id": "o1"},), "fills": (), "cash": 100000.0})

        self.assertNotEqual(engine.digest(before), engine.digest(after))
        self.assertNotEqual(engine.digest(before, "DIGEST-BROKER"), engine.digest(after, "DIGEST-BROKER"))
        self.assertEqual(engine.digest(before, "DIGEST-POSITION"), engine.digest(after, "DIGEST-POSITION"))

    def test_surface_registry_loads_requires_consistency_and_rejects_duplicates(self):
        registry = ReadSurfaceRegistry()
        surfaces = registry.all()

        self.assertGreaterEqual(len(surfaces), 10)
        self.assertTrue(all(surface.consistency_level for surface in surfaces))
        self.assertTrue(all(surface.prohibited_effects for surface in surfaces))
        with self.assertRaisesRegex(ValueError, "duplicate read surface id"):
            registry.register(surfaces[0])

    def test_protected_state_and_digest_profiles_cover_required_domains(self):
        profile_ids = {profile.profile_id for profile in semantic_digest_profiles()}
        domain_ids = {domain.domain_id for domain in protected_state_registry()}

        self.assertIn("DIGEST-ALL-AUTHORITATIVE", profile_ids)
        self.assertIn("DIGEST-TRANSACTION", profile_ids)
        self.assertIn("STATE-RUNTIME", domain_ids)
        self.assertIn("STATE-TRADING", domain_ids)
        self.assertIn("STATE-POSITIONS", domain_ids)
        self.assertIn("STATE-TRUTH", domain_ids)
        self.assertIn("STATE-TRANSACTIONS", domain_ids)
        self.assertIn("STATE-COST", domain_ids)

    def test_guarded_read_passes_for_pure_snapshot_and_preserves_evidence(self):
        state = authoritative_state()
        guard = ReadOnlyIntegrityGuard()

        response, result = guard.guard_read("READ-API-STATUS-001", lambda: {"status": "ready"}, lambda: state)

        self.assertEqual(response["status"], "ready")
        self.assertEqual(result.result, ReadIntegrityStatus.PASS)
        self.assertEqual(result.changed_domains, ())
        self.assertEqual(len(guard.evidence_store.records), 1)
        self.assertTrue(guard.evidence_store.records[0].stored_separately_from_financial_truth)

    def test_guarded_read_detects_authoritative_mutation_and_quarantines_surface(self):
        state = authoritative_state()
        guard = ReadOnlyIntegrityGuard()

        def mutating_read():
            state["broker"] = {"orders": ({"order_id": "o1"},), "fills": (), "cash": 100000.0}
            return {"orders": 1}

        _, result = guard.guard_read("READ-BROKER-SUMMARY-001", mutating_read, lambda: state)
        read_model = guard.commander_read_model()

        self.assertEqual(result.result, ReadIntegrityStatus.FAIL)
        self.assertIn("DIGEST-ALL-AUTHORITATIVE", result.changed_domains)
        self.assertIn("READ-BROKER-SUMMARY-001", read_model["quarantinedSurfaces"])

    def test_counter_changes_detect_api_cost_office_token_broker_persistence_and_transaction_mutation(self):
        state = authoritative_state()
        counters = [ReadCounterSnapshot(), ReadCounterSnapshot(api_calls=1, cost_total_units=0.01, office_wake_count=1, token_transfer_count=1, broker_event_count=1, persistence_sequence=1, transaction_journal_size=1)]
        guard = ReadOnlyIntegrityGuard()

        _, result = guard.guard_read("READ-DASHBOARD-001", lambda: {"view": "dashboard"}, lambda: state, counters_provider=lambda: counters.pop(0))

        self.assertEqual(result.result, ReadIntegrityStatus.FAIL)
        self.assertIn("api_calls", result.prohibited_differences)
        self.assertIn("cost_total_units", result.prohibited_differences)
        self.assertIn("office_wake_count", result.prohibited_differences)
        self.assertIn("token_transfer_count", result.prohibited_differences)
        self.assertIn("broker_event_count", result.prohibited_differences)
        self.assertIn("persistence_sequence", result.prohibited_differences)
        self.assertIn("transaction_journal_size", result.prohibited_differences)

    def test_async_streaming_and_polling_guards_are_nonmutating(self):
        state = authoritative_state()
        guard = ReadOnlyIntegrityGuard()

        async def async_read():
            return {"async": True}

        async_response, async_result = asyncio.run(guard.guard_async_read("READ-API-STATUS-001", async_read, lambda: state))
        stream_response, stream_result = guard.guard_streaming_read("READ-DASHBOARD-001", lambda: iter(({"row": 1}, {"row": 2})), lambda: state)
        poll_response, poll_result = guard.guard_polling_read("READ-DASHBOARD-001", lambda: {"status": "same"}, lambda: state, repetitions=1000)

        self.assertTrue(async_response["async"])
        self.assertEqual(async_result.result, ReadIntegrityStatus.PASS)
        self.assertEqual(len(stream_response), 2)
        self.assertEqual(stream_result.result, ReadIntegrityStatus.PASS)
        self.assertEqual(len(poll_response), 1000)
        self.assertEqual(poll_result.result, ReadIntegrityStatus.PASS)

    def test_guard_rejects_unregistered_live_or_wrong_domain_reads(self):
        guard = ReadOnlyIntegrityGuard()

        with self.assertRaisesRegex(KeyError, "unregistered read surface"):
            guard.guard_read("READ-MISSING", lambda: {}, lambda: authoritative_state())
        with self.assertRaisesRegex(ValueError, "truth domain not permitted"):
            guard.guard_read("READ-API-STATUS-001", lambda: {}, lambda: authoritative_state(), truth_domain="LIVE")
        guard.live_trading_enabled = True
        with self.assertRaisesRegex(ValueError, "live trading must remain disabled"):
            guard.guard_read("READ-API-STATUS-001", lambda: {}, lambda: authoritative_state())

    def test_mutating_command_falsely_exposed_as_read_is_rejected(self):
        base = read_surface_registry()[0]
        mutating = ReadSurfaceDefinition(**{**base.__dict__, "surface_id": "READ-BAD-001", "surface_type": ReadSurfaceType.MUTATING_COMMAND_FALSELY_EXPOSED_AS_READ})
        guard = ReadOnlyIntegrityGuard(ReadSurfaceRegistry((mutating,)))

        with self.assertRaisesRegex(ValueError, "mutating command"):
            guard.guard_read("READ-BAD-001", lambda: {}, lambda: authoritative_state())

    def test_server_route_audit_registers_get_routes_and_separates_post_commands(self):
        guard = ReadOnlyIntegrityGuard()
        report = guard.audit_server_routes("src/argos/control_panel/server.py")

        self.assertIn("/api/state", report.get_routes)
        self.assertIn("/api/paper/start", report.command_routes)
        self.assertFalse(any(finding.method == "GET" and finding.finding_class == ReadFindingClass.GET_ROUTE for finding in report.findings))
        self.assertTrue(all(route.startswith("/api/") for route in report.get_routes))

    def test_commander_read_model_cannot_certify_failed_surface_or_enable_live(self):
        guard = ReadOnlyIntegrityGuard()
        read_model = guard.commander_read_model()

        self.assertFalse(read_model["commanderControls"]["mayMarkFailedSurfaceCertified"])
        self.assertFalse(read_model["commanderControls"]["mayEditDigestResults"])
        self.assertFalse(read_model["commanderControls"]["mayEraseEvidence"])
        self.assertFalse(read_model["commanderControls"]["mayEnableLiveTrading"])
        self.assertFalse(read_model["financialMutationAuthority"])
        self.assertFalse(read_model["liveTradingEnabled"])

    def test_eodg_package_export_is_available(self):
        from argos.control_panel import EODGReadOnlyIntegrityGuard

        self.assertIs(EODGReadOnlyIntegrityGuard, ReadOnlyIntegrityGuard)

    def test_static_architecture_boundaries_do_not_create_financial_authorities(self):
        import argos.control_panel.read_only_integrity as module

        source = inspect.getsource(module)

        self.assertNotIn("live_trading_enabled = True", source)
        self.assertNotIn(".submit_order(", source)
        self.assertNotIn(".create_from_execution(", source)
        self.assertNotIn(".record_broker_authoritative_order(", source)
        self.assertNotIn(".acknowledge_participant(", source)
        self.assertIn("ConstitutionalInvariantEngine", source)

    def test_certified_read_only_surfaces_are_not_commands(self):
        certified = [surface for surface in read_surface_registry() if surface.certification_status == ReadCertificationStatus.CERTIFIED_READ_ONLY]

        self.assertTrue(certified)
        self.assertTrue(all(surface.surface_type != ReadSurfaceType.MUTATING_COMMAND_FALSELY_EXPOSED_AS_READ for surface in certified))
        self.assertTrue(all("transaction advancement" in surface.prohibited_effects for surface in certified))


if __name__ == "__main__":
    unittest.main()
