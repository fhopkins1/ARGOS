import inspect
import unittest

from argos.control_panel.long_duration_operations_lab import (
    AdmissionEnvironment,
    CampaignDefinition,
    DurationMode,
    EnduranceCampaignType,
    EnduranceFailureClass,
    EndurancePassCriteria,
    EnduranceStage,
    EnduranceVerdict,
    LongDurationOperationsLaboratory,
    TelemetrySample,
    long_duration_campaign_catalog,
)


def environment(**overrides):
    base = {
        "branch": "main",
        "full_commit_sha": "d80d6ab4fc3d4fb753efc73cd3a09b3b41be77e6",
        "git_status": "",
        "python_version": "Python 3.14.5",
        "node_version": "v24.16.0",
        "operating_system": "Windows",
        "persistence_backend": "DurableEnterprisePersistenceStore",
        "runtime_configuration": "paper",
        "truth_domain_configuration": "PAPER",
        "policy_version": "EO-DF-policy-1",
        "doctrine_version": "EO-DF-doctrine-1",
        "active_paper_broker": "DeterministicPaperBrokerage",
        "live_trading_enabled": False,
        "available_hardware_resources": {"cpu": 1, "memory": 1024},
        "expected_campaign_environment": "local deterministic test",
        "existing_resource_limits": {"queue": 4, "threads": 1},
    }
    base.update(overrides)
    return AdmissionEnvironment(**base)


def definition(**overrides):
    base = {
        "campaign_id": "EO-DF-CAMPAIGN-001",
        "campaign_type": EnduranceCampaignType.IDLE_STABILITY,
        "stage": EnduranceStage.STAGE_0_SHAKEDOWN,
        "duration_mode": DurationMode.WALL_CLOCK,
        "intended_duration_seconds": 4,
        "accelerated_event_seconds": 0,
        "segment_target_count": 1,
        "metric_interval_seconds": 1,
        "repository_commit": "d80d6ab4fc3d4fb753efc73cd3a09b3b41be77e6",
        "configuration_hash": "config-hash",
        "policy_version": "EO-DF-policy-1",
        "doctrine_version": "EO-DF-doctrine-1",
        "truth_domain": "PAPER",
        "fixture_version": "EO-DF-fixture-1",
        "deterministic_seed": "stable",
        "runtime_mode": "paper",
        "expected_workload": "idle/no opportunity",
        "pass_criteria": EndurancePassCriteria(),
        "evidence_root": "Documentation/EO-DF-evidence",
    }
    base.update(overrides)
    return CampaignDefinition(**base)


class LongDurationOperationsLaboratoryTests(unittest.TestCase):
    def test_campaign_catalog_registers_required_campaign_types(self):
        catalog = long_duration_campaign_catalog()
        types = {entry.campaign_type for entry in catalog}

        self.assertEqual(len(catalog), 10)
        self.assertIn(EnduranceCampaignType.IDLE_STABILITY, types)
        self.assertIn(EnduranceCampaignType.CONTROLLED_ACTIVE_PAPER, types)
        self.assertIn(EnduranceCampaignType.MIXED_OPERATIONAL, types)
        self.assertIn(EnduranceCampaignType.RESTART_ENDURANCE, types)
        self.assertIn(EnduranceCampaignType.DASHBOARD_READ_ONLY_LOAD, types)
        self.assertTrue(all(not entry.may_create_trading_activity for entry in catalog))

    def test_valid_campaign_admits_and_duplicate_id_is_rejected_after_run(self):
        lab = LongDurationOperationsLaboratory()
        campaign = definition()
        env = environment()

        report = lab.run_campaign(campaign, env)
        duplicate = lab.register_campaign(campaign, env)

        self.assertEqual(report.verdict, EnduranceVerdict.PASS)
        self.assertFalse(duplicate.admitted)
        self.assertIn("DUPLICATE_CAMPAIGN_ID", duplicate.reason_codes)

    def test_invalid_duration_missing_commit_dirty_tree_and_live_mode_block_admission(self):
        lab = LongDurationOperationsLaboratory()

        self.assertIn("INVALID_DURATION", lab.register_campaign(definition(intended_duration_seconds=0), environment()).reason_codes)
        self.assertIn("COMMIT_REQUIRED", lab.register_campaign(definition(campaign_id="EO-DF-CAMPAIGN-002", repository_commit=""), environment()).reason_codes)
        self.assertIn("WORKTREE_DIRTY", lab.register_campaign(definition(campaign_id="EO-DF-CAMPAIGN-003"), environment(git_status=" M file.py")).reason_codes)
        self.assertIn("LIVE_TRADING_DISABLED_REQUIRED", lab.register_campaign(definition(campaign_id="EO-DF-CAMPAIGN-004", live_trading_enabled=True), environment()).reason_codes)

    def test_admission_blocks_failed_eoda_eodc_eodd_and_persistence(self):
        lab = LongDurationOperationsLaboratory()
        campaign = definition(campaign_id="EO-DF-CAMPAIGN-005")

        result = lab.register_campaign(
            campaign,
            environment(
                eoda_critical_pass=False,
                eodc_operational=False,
                eodd_journal_healthy=False,
                persistence_available=False,
            ),
        )

        self.assertFalse(result.admitted)
        self.assertIn("EO_DA_CRITICAL_INVARIANT_FAILED", result.reason_codes)
        self.assertIn("EO_DC_UNHEALTHY", result.reason_codes)
        self.assertIn("EO_DD_JOURNAL_UNHEALTHY", result.reason_codes)
        self.assertIn("PERSISTENCE_UNAVAILABLE", result.reason_codes)

    def test_metrics_capture_all_required_domains_and_evidence_hash_is_present(self):
        lab = LongDurationOperationsLaboratory()
        report = lab.run_campaign(definition(), environment())
        sample = report.segments[0].samples[-1]

        self.assertGreater(sample.resident_memory_units, 0)
        self.assertGreaterEqual(sample.scheduler_obligations, 0)
        self.assertGreaterEqual(sample.workflow_tokens, 0)
        self.assertGreaterEqual(sample.eodd_journal_size, 0)
        self.assertGreaterEqual(sample.dashboard_request_count, 0)
        self.assertTrue(report.evidence_hash)
        self.assertTrue(report.segments[0].evidence.storage_isolated_from_financial_truth)
        self.assertEqual(report.segments[0].evidence.manifest["repositoryCommit"], report.segments[0].evidence.manifest["repositoryCommit"])

    def test_bounded_workload_passes_and_memory_leak_duplicate_loop_queue_growth_fail(self):
        lab = LongDurationOperationsLaboratory()

        stable = lab.run_campaign(definition(campaign_id="EO-DF-STABLE"), environment())
        leak = lab.run_campaign(definition(campaign_id="EO-DF-LEAK", deterministic_seed="memory_leak"), environment())
        duplicate_loop = lab.run_campaign(definition(campaign_id="EO-DF-LOOP", deterministic_seed="duplicate_loop"), environment())
        queue_growth = lab.run_campaign(definition(campaign_id="EO-DF-QUEUE", deterministic_seed="queue_growth"), environment())

        self.assertEqual(stable.verdict, EnduranceVerdict.PASS)
        self.assertEqual(leak.verdict, EnduranceVerdict.FAIL)
        self.assertEqual(duplicate_loop.verdict, EnduranceVerdict.FAIL)
        self.assertEqual(queue_growth.verdict, EnduranceVerdict.FAIL)
        self.assertEqual(leak.critical_findings[0].failure_class, EnduranceFailureClass.MEMORY)

    def test_restart_endurance_and_recovery_campaign_record_safe_recovery_without_duplication(self):
        lab = LongDurationOperationsLaboratory()
        restart = lab.run_campaign(
            definition(
                campaign_id="EO-DF-RESTART",
                campaign_type=EnduranceCampaignType.RESTART_ENDURANCE,
                expected_workload="restart cycles",
            ),
            environment(),
        )
        recovery = lab.run_campaign(
            definition(
                campaign_id="EO-DF-RECOVERY",
                campaign_type=EnduranceCampaignType.RECOVERY_ENDURANCE,
                expected_workload="recovery faults",
            ),
            environment(eode_fault_hooks_disabled=False),
        )

        self.assertEqual(restart.verdict, EnduranceVerdict.PASS)
        self.assertEqual(restart.segments[0].samples[-1].recovery_attempts, 1)
        self.assertEqual(recovery.verdict, EnduranceVerdict.PASS)
        self.assertTrue(recovery.eode_integration["active"])

    def test_read_only_endurance_records_polling_without_mutation_or_cost(self):
        lab = LongDurationOperationsLaboratory()
        report = lab.run_campaign(
            definition(
                campaign_id="EO-DF-READONLY",
                campaign_type=EnduranceCampaignType.DASHBOARD_READ_ONLY_LOAD,
                expected_workload="read-only polling",
            ),
            environment(),
        )
        sample = report.segments[0].samples[-1]

        self.assertEqual(report.verdict, EnduranceVerdict.PASS)
        self.assertGreater(sample.dashboard_request_count, 0)
        self.assertEqual(sample.read_side_mutations, 0)
        self.assertEqual(sample.api_calls, 0)
        self.assertEqual(sample.total_cost, 0.0)

    def test_read_only_mutation_and_live_truth_domain_fail_closed(self):
        lab = LongDurationOperationsLaboratory()
        mutation = lab.run_campaign(
            definition(
                campaign_id="EO-DF-READ-MUTATION",
                campaign_type=EnduranceCampaignType.DASHBOARD_READ_ONLY_LOAD,
                deterministic_seed="read_mutation",
            ),
            environment(),
        )
        live = lab.run_campaign(definition(campaign_id="EO-DF-LIVE", truth_domain="LIVE"), environment())

        self.assertEqual(mutation.verdict, EnduranceVerdict.FAIL)
        self.assertEqual(mutation.critical_findings[0].failure_class, EnduranceFailureClass.READ_ONLY)
        self.assertFalse(live.admission.admitted)
        self.assertIn("TRUTH_DOMAIN_INVALID", live.admission.reason_codes)

    def test_transaction_and_reconciliation_endurance_track_journal_and_state(self):
        lab = LongDurationOperationsLaboratory()
        report = lab.run_campaign(
            definition(
                campaign_id="EO-DF-RECON",
                campaign_type=EnduranceCampaignType.RECONCILIATION_ENDURANCE,
                expected_workload="reconciliation cycles",
            ),
            environment(),
        )

        self.assertEqual(report.verdict, EnduranceVerdict.PASS)
        self.assertTrue(report.eodd_integration["active"])
        self.assertGreaterEqual(report.eodd_integration["journalSize"], 0)
        self.assertTrue(any(event["event"] == "eodd_reconciliation" for event in report.segments[0].evidence.events))

    def test_accelerated_event_time_is_distinguished_from_wall_clock(self):
        lab = LongDurationOperationsLaboratory()
        report = lab.run_campaign(
            definition(
                campaign_id="EO-DF-ACCEL",
                stage=EnduranceStage.STAGE_1_ACCELERATED_24H,
                duration_mode=DurationMode.ACCELERATED_EVENT_TIME,
                intended_duration_seconds=4,
                accelerated_event_seconds=86400,
            ),
            environment(),
        )

        self.assertEqual(report.verdict, EnduranceVerdict.PASS)
        self.assertEqual(report.accelerated_event_seconds, 86400)
        self.assertLess(report.actual_duration_seconds, report.accelerated_event_seconds)

    def test_resumable_campaign_preserves_cumulative_and_uninterrupted_duration(self):
        lab = LongDurationOperationsLaboratory()
        first = lab.run_campaign(definition(campaign_id="EO-DF-RESUME", segment_target_count=1), environment())
        resumed = lab.resume_campaign(first, additional_segments=2)

        self.assertEqual(resumed.campaign_id, first.campaign_id)
        self.assertEqual(resumed.segment_count, 3)
        self.assertEqual(resumed.cumulative_segmented_duration_seconds, first.actual_duration_seconds + 8)
        self.assertEqual(resumed.longest_uninterrupted_duration_seconds, first.longest_uninterrupted_duration_seconds)
        self.assertTrue(resumed.evidence_hash)

    def test_repeated_identical_campaigns_have_matching_determinism_signatures(self):
        lab = LongDurationOperationsLaboratory()
        first = lab.run_campaign(definition(campaign_id="EO-DF-DET-1"), environment())
        second = lab.run_campaign(definition(campaign_id="EO-DF-DET-2"), environment())

        self.assertEqual(first.determinism_signature, second.determinism_signature)

    def test_commander_can_request_and_halt_but_cannot_edit_results_or_fabricate_duration(self):
        lab = LongDurationOperationsLaboratory()
        report = lab.commander_request_campaign(definition(campaign_id="EO-DF-COMMANDER"), environment())
        halt = lab.halt_campaign(report.campaign_id)
        read_model = lab.commander_read_model()

        self.assertFalse(halt["resultsAltered"])
        self.assertFalse(read_model["commanderControls"]["mayEditMetricHistory"])
        self.assertFalse(read_model["commanderControls"]["mayMarkFailedCampaignPassed"])
        self.assertFalse(read_model["commanderControls"]["mayFabricateDuration"])
        self.assertFalse(read_model["commanderControls"]["mayEnableLiveTrading"])

    def test_ci_architecture_boundaries_prevent_live_financial_mutation_and_certification(self):
        import argos.control_panel.long_duration_operations_lab as module

        source = inspect.getsource(module)

        self.assertNotIn("live_trading_enabled = True", source)
        self.assertNotIn(".submit_order(", source)
        self.assertNotIn(".create_from_execution(", source)
        self.assertNotIn("certifies_continuous_paper_trading = True", source)
        self.assertIn("FaultInjectionRecoveryLaboratory", source)

    def test_package_exports_lab(self):
        from argos.control_panel import LongDurationOperationsLaboratory as ExportedLaboratory

        self.assertIs(ExportedLaboratory, LongDurationOperationsLaboratory)

    def test_missing_metric_series_is_reported_as_evidence_failure(self):
        lab = LongDurationOperationsLaboratory()

        finding = lab.evaluate_boundedness((), EndurancePassCriteria())[0]

        self.assertEqual(finding.failure_class, EnduranceFailureClass.EVIDENCE)
        self.assertTrue(finding.blocks_campaign)


if __name__ == "__main__":
    unittest.main()
