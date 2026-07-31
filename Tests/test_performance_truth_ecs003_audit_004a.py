from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from audit_reproduce import (
    EXIT_DISCOVERY,
    EXIT_INPUT,
    EXIT_VALIDATION,
    _discover_performance_truth,
    _phase_result,
    reproduce,
    resolve_repository_relative_input,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _zip_tree(source: Path, target: Path) -> None:
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            archive.write(path, path.relative_to(source).as_posix())


class PerformanceTruthAudit004AHarnessTests(unittest.TestCase):
    def test_repository_relative_input_resolution_rejects_developer_paths(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write(root / "AUDITOR_README.md", "ok")
            self.assertEqual(resolve_repository_relative_input(root, "AUDITOR_README.md"), root / "AUDITOR_README.md")
            for candidate in (
                r"C:\Users\Fletc\.codex\attachments\8b57da45-406a-4e10-a43a-fa76ff327f2d\pasted-text.txt",
                "/home/fletc/pasted-text.txt",
                "~/pasted-text.txt",
                "../outside.txt",
            ):
                with self.assertRaises((ValueError, FileNotFoundError), msg=candidate):
                    resolve_repository_relative_input(root, candidate)

    def test_missing_required_repository_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            candidate_root = temp / "candidate"
            _write(candidate_root / "AUDITOR_README.md", "Performance Truth")
            _write(candidate_root / "audit_reproduce.py", "print('entrypoint')")
            zip_path = temp / "candidate.zip"
            output = temp / "output"
            _zip_tree(candidate_root, zip_path)
            self.assertEqual(reproduce(zip_path, output), EXIT_INPUT)
            findings = json.loads((output / "findings.json").read_text(encoding="utf-8"))
            self.assertTrue(any("performance_truth_ecs003_audit_003.py" in row.get("error", "") for row in findings))

    def test_zero_collected_runtime_tests_cause_discovery_failure(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            candidate_root = temp / "candidate"
            _write(candidate_root / "AUDITOR_README.md", "Performance Truth")
            _write(candidate_root / "audit_reproduce.py", "print('entrypoint')")
            _write(candidate_root / "Scripts" / "performance_truth_ecs003_audit_003.py", "print('audit')")
            _write(candidate_root / "src" / "argos" / "control_panel" / "performance_truth_engine.py", "x=1")
            zip_path = temp / "candidate.zip"
            output = temp / "output"
            _zip_tree(candidate_root, zip_path)
            self.assertEqual(reproduce(zip_path, output), EXIT_DISCOVERY)
            findings = json.loads((output / "findings.json").read_text(encoding="utf-8"))
            self.assertTrue(any("No Performance Truth runtime tests" in row.get("error", "") for row in findings))

    def test_runtime_test_failure_blocks_dependent_pass_artifacts(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            candidate_root = temp / "candidate"
            _write(candidate_root / "AUDITOR_README.md", "Performance Truth")
            _write(candidate_root / "audit_reproduce.py", "print('entrypoint')")
            _write(candidate_root / "src" / "argos" / "control_panel" / "performance_truth_engine.py", "x=1")
            _write(candidate_root / "Scripts" / "performance_truth_ecs003_audit_003.py", "print('audit should not run after failed tests')")
            _write(
                candidate_root / "Tests" / "test_performance_truth_runtime_failure.py",
                "import unittest\nfrom argos.control_panel.performance_truth_engine import PerformanceTruthEngine\nclass PerformanceTruthRuntimeFailure(unittest.TestCase):\n    def test_fails(self):\n        self.fail('boom')\n",
            )
            zip_path = temp / "candidate.zip"
            output = temp / "output"
            _zip_tree(candidate_root, zip_path)
            self.assertEqual(reproduce(zip_path, output), EXIT_VALIDATION)
            summary = json.loads((output / "execution_summary.json").read_text(encoding="utf-8"))
            behavior = json.loads((output / "behavioral_results.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "FAIL")
            self.assertIn(behavior["disposition"], {"FAIL", "NOT_EXECUTED"})
            self.assertNotEqual(behavior["disposition"], "PASS")

    def test_discovery_is_repository_based_and_stable_with_exclusions(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write(root / "src" / "argos" / "control_panel" / "performance_truth_engine.py", "x=1")
            _write(root / "Tests" / "test_performance_truth_runtime.py", "from argos.control_panel.performance_truth_engine import PerformanceTruthEngine\n")
            _write(root / "Tests" / "test_performance_truth_ecs003_audit_004.py", "print('audit report test')\n")
            first = _discover_performance_truth(root)
            second = _discover_performance_truth(root)
            self.assertEqual(first, second)
            self.assertEqual(first["test_modules"], ["Tests/test_performance_truth_runtime.py"])
            self.assertEqual(first["excluded_test_modules"][0]["test_module"], "Tests/test_performance_truth_ecs003_audit_004.py")

    def test_failed_controlling_execution_never_emits_pass_phase(self):
        phase = _phase_result(
            output_name="replay_results.json",
            source_name="deterministic_replay_report.json",
            source_dir=Path("missing"),
            controlling_command={"command_id": "runtime-audit-003", "returncode": 1, "status": "FAIL"},
            upstream_failed=False,
            run_id="RUN",
            candidate_hash="abc",
            root_manifest_hash="def",
        )
        self.assertEqual(phase["disposition"], "FAIL")
        self.assertNotEqual(phase["disposition"], "PASS")
        self.assertEqual(phase["derivation_chain"]["raw_result"]["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
