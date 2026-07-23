from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.trader_audit import build_candidate_manifest, run_trader_audit  # noqa: E402


def _write_candidate(zip_path: Path) -> None:
    files = set(
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in (REPOSITORY_ROOT / "src" / "argos").rglob("*.py")
    )
    files.update([
        "audit_trader_reproduce.py",
        "TRADER_AUDITOR_README.md",
        "Tests/test_trader_readiness.py",
        "Tests/test_trader_group_framework.py",
        "Tests/test_trade_execution_office.py",
        "Tests/test_trade_monitoring_office.py",
        "Tests/test_trader_fusion_office.py",
        "Tests/test_trader_constitutional_governance.py",
        "Tests/test_trader_rm002_constitution.py",
        "Tests/test_trader_rm002a_publication.py",
        "Tests/test_trader_requirement_proof.py",
        "Tests/test_trader_requirement_verifier.py",
    ])
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in files:
            info = zipfile.ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (REPOSITORY_ROOT / relative).read_bytes())


class TraderAuditEnablementTests(unittest.TestCase):
    def test_candidate_manifest_is_complete_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate = Path(temp_dir) / "candidate.zip"
            _write_candidate(candidate)
            manifest = build_candidate_manifest(candidate)

        self.assertTrue(manifest["candidate_identifier"].startswith("TRADER-CANDIDATE-ZIP-"))
        self.assertGreater(manifest["total_non_directory_entries"], 0)
        self.assertFalse(manifest["findings"])

    def test_package_bound_single_run_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate = Path(temp_dir) / "candidate.zip"
            output = Path(temp_dir) / "out"
            _write_candidate(candidate)
            result = run_trader_audit(candidate, output)

        self.assertEqual(result["final_status"], "PASS")
        self.assertEqual(result["constitutional_closure"]["unresolved_artifacts"], 0)
        self.assertEqual(result["traceability"]["status"], "PASS")
        self.assertEqual(result["operational_verification"]["status"], "PASS")

    def test_auditor_command_runs_without_pythonpath_from_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            candidate = base / "candidate.zip"
            extraction = base / "candidate"
            output = base / "out"
            _write_candidate(candidate)
            with zipfile.ZipFile(candidate, "r") as archive:
                archive.extractall(extraction)
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            completed = subprocess.run(
                [sys.executable, "audit_trader_reproduce.py", "--candidate", str(candidate), "--output", str(output), "--single-run"],
                cwd=str(extraction),
                env=env,
                text=True,
                capture_output=True,
                timeout=240,
            )
            result = json.loads((output / "certification_result.json").read_text(encoding="utf-8"))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(result["final_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
