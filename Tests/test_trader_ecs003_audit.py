from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.trader_ecs003_audit import (  # noqa: E402
    _classify_repository_finding,
    _module_execution_record,
    _parse_structured_module_result,
    _proof_report,
    build_test_inventory,
    run_test_module,
)
from argos.trader.requirement_verifier import build_behavioral_proof_package  # noqa: E402


class TraderECS003AuditTests(unittest.TestCase):
    def test_inventory_discovers_repository_tests(self) -> None:
        inventory = build_test_inventory(REPOSITORY_ROOT / "Tests")

        self.assertGreater(inventory["total_tests"], 0)
        self.assertTrue(any(record["test_identifier"].startswith("test_trader_requirement_verifier.") for record in inventory["records"]))
        self.assertEqual(inventory["total_tests"], len(inventory["records"]))

    def test_module_runner_assigns_final_dispositions(self) -> None:
        result = run_test_module("Tests.test_trader_requirement_verifier")
        dispositions = {record["disposition"] for record in result["records"]}

        self.assertTrue(result["successful"])
        self.assertEqual(dispositions, {"PASS"})
        self.assertEqual(result["disposition_counts"]["PASS"], len(result["records"]))

    def test_parser_accepts_result_file_and_rejects_stale_execution_id(self) -> None:
        result_path = REPOSITORY_ROOT / "_tmp_ecs003_result.json"
        try:
            result_path.write_text('{"execution_id":"expected","records":[]}', encoding="utf-8")
            payload, parser_result, detail = _parse_structured_module_result(
                module="Tests.test_trader_requirement_verifier",
                stdout="ordinary log output\n",
                result_file=result_path,
                expected_execution_id="expected",
            )
            self.assertEqual("VALID", parser_result)
            self.assertEqual("expected", payload["execution_id"])

            result_path.write_text('{"execution_id":"stale","records":[]}', encoding="utf-8")
            payload, parser_result, detail = _parse_structured_module_result(
                module="Tests.test_trader_requirement_verifier",
                stdout="ordinary log output\n",
                result_file=result_path,
                expected_execution_id="expected",
            )
            self.assertIsNone(payload)
            self.assertEqual("STALE_OR_WRONG_EXECUTION_ID", parser_result)
            self.assertIn("execution identifier", detail)
        finally:
            result_path.unlink(missing_ok=True)

    def test_outer_execution_record_survives_missing_child_json(self) -> None:
        segment_dir = REPOSITORY_ROOT / "_tmp_ecs003_segments"
        segment_dir.mkdir(exist_ok=True)
        stdout_path = segment_dir / "module.stdout.log"
        stderr_path = segment_dir / "module.stderr.log"
        structured_path = segment_dir / "module.result.json"
        stdout_path.write_text("traceback without framed json", encoding="utf-8")
        stderr_path.write_text("error", encoding="utf-8")
        try:
            execution_record, records = _module_execution_record(
                module="Tests.test_missing_json",
                expected_tests=1,
                inventory_records=({"test_identifier": "Tests.test_missing_json.Case.test_one"},),
                candidate_digest="candidate",
                command=(sys.executable, "-m", "argos.trader_ecs003_audit"),
                cwd=REPOSITORY_ROOT,
                env={"PYTHONPATH": str(SRC_ROOT), "TRADER_ECS003_CANDIDATE_DIGEST": "candidate"},
                execution_id="exec-1",
                started_at="2026-07-24T00:00:00Z",
                completed_at="2026-07-24T00:00:01Z",
                elapsed_seconds=1.0,
                return_code=1,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                structured_path=structured_path,
                output_root=REPOSITORY_ROOT,
                stdout="traceback without framed json",
                stderr="error",
                payload=None,
                parser_result="MISSING",
                parser_detail="no json",
            )
            self.assertEqual("trader-ecs003-module-execution-record/v1", execution_record["schema_version"])
            self.assertEqual("RUNNER_ERROR", execution_record["execution_disposition"])
            self.assertEqual("ERROR", records[0]["disposition"])
            self.assertIn("MISSING", records[0]["details"])
        finally:
            stdout_path.unlink(missing_ok=True)
            stderr_path.unlink(missing_ok=True)
            structured_path.unlink(missing_ok=True)
            segment_dir.rmdir()

    def test_repository_findings_are_classified_and_reintegrated_into_proofs(self) -> None:
        direct = _classify_repository_finding(
            {
                "test_identifier": "test_argos_control_panel_dashboard.Case.test_position",
                "disposition": "ERROR",
                "details": "authoritative fill id required for position mutation",
            }
        )
        dependency = _classify_repository_finding(
            {
                "test_identifier": "test_authorization_operational_readiness.Case.test_auth",
                "disposition": "FAIL",
                "details": "authorization dependency failed",
            }
        )
        self.assertEqual("TRADER_DIRECT_FIXTURE_SCOPE", direct["scope_classification"])
        self.assertEqual("TRADER_DEPENDENCY_DERIVED_AUTHORIZATIONS_SCOPE", dependency["scope_classification"])

        campaign = {
            "execution_records": (
                {"test_identifier": "test_argos_control_panel_dashboard.Case.test_position", "disposition": "ERROR", "details": "authoritative fill id required"},
                {"test_identifier": "test_trader_requirement_verifier.Case.test_ok", "disposition": "PASS", "details": ""},
            ),
            "campaign_digest": "campaign",
        }
        proof_report = _proof_report(build_behavioral_proof_package("candidate-digest"), campaign)

        self.assertEqual("FAIL", proof_report["status"])
        self.assertEqual(1, proof_report["repository_scope_classification"]["total_nonpassing_records"])
        self.assertTrue(any(proof["proof_id"] == "TRADER-PROOF-ECS003-REPOSITORY-EXECUTION-FINDINGS" for proof in proof_report["proof_object_registry"]))
        self.assertGreater(proof_report["totals"]["open_findings"], 0)


if __name__ == "__main__":
    unittest.main()
