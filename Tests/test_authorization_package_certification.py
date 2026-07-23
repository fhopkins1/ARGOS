from pathlib import Path
import hashlib
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

from argos.authorization_package_certification import (  # noqa: E402
    PackageCertificationStatus,
    build_candidate_manifest,
    run_full_certification,
    run_package_bound_certification,
)


def _write_candidate_zip(zip_path: Path, files: dict[str, bytes] | None = None) -> None:
    source_files = files or {
        "src/argos/authorization_package_certification.py": (REPOSITORY_ROOT / "src/argos/authorization_package_certification.py").read_bytes(),
        "src/argos/authorization_certify.py": (REPOSITORY_ROOT / "src/argos/authorization_certify.py").read_bytes(),
        "src/argos/control_panel/authorization_implementation_closure.py": (REPOSITORY_ROOT / "src/argos/control_panel/authorization_implementation_closure.py").read_bytes(),
        "Tests/test_authorization_implementation_closure.py": (REPOSITORY_ROOT / "Tests/test_authorization_implementation_closure.py").read_bytes(),
        "Tests/test_trade_execution_office.py": (REPOSITORY_ROOT / "Tests/test_trade_execution_office.py").read_bytes(),
        "Documentation/AUTH-IC-001-001_TO_010_IMPLEMENTATION_CLOSURE_EVIDENCE.md": (
            REPOSITORY_ROOT / "Documentation/AUTH-IC-001-001_TO_010_IMPLEMENTATION_CLOSURE_EVIDENCE.md"
        ).read_bytes(),
    }
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in sorted(source_files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)


class AuthorizationPackageCertificationTests(unittest.TestCase):
    def test_candidate_identity_is_repository_zip_digest_and_manifest_covers_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate = Path(temp_dir) / "candidate.zip"
            _write_candidate_zip(candidate)

            manifest = build_candidate_manifest(candidate)
            archive_digest = hashlib.sha256(candidate.read_bytes()).hexdigest()

        self.assertEqual(manifest.archive_digest, archive_digest)
        self.assertEqual(manifest.candidate_identifier, f"AUTH-CANDIDATE-ZIP-{manifest.archive_digest[:16].upper()}")
        self.assertEqual(manifest.total_file_entries, len(manifest.entries))
        self.assertFalse(manifest.findings)
        self.assertTrue(all("\\" not in entry.canonical_path for entry in manifest.entries))

    def test_package_bound_single_run_uses_explicit_candidate_and_writes_compile_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate = Path(temp_dir) / "candidate.zip"
            output = Path(temp_dir) / "out"
            _write_candidate_zip(candidate)

            result, compilation, manifest = run_package_bound_certification(candidate, output)
            archive_digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            compile_log = (output / "compileall.log").read_text(encoding="utf-8")

        self.assertEqual(result.final_verdict, PackageCertificationStatus.PASS)
        self.assertEqual(result.candidate_digest, archive_digest)
        self.assertEqual(result.candidate_identifier, manifest.candidate_identifier)
        self.assertTrue(result.candidate_inventory_complete)
        self.assertTrue(result.focused_tests_pass)
        self.assertTrue(result.regression_tests_pass)
        self.assertEqual(compilation.status, PackageCertificationStatus.PASS)
        self.assertTrue(compile_log.strip())

    def test_cli_rejects_implicit_cwd_candidate_and_accepts_explicit_zip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate = Path(temp_dir) / "candidate.zip"
            output = Path(temp_dir) / "out"
            _write_candidate_zip(candidate)
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(SRC_ROOT)

            missing_candidate = subprocess.run(
                [sys.executable, "-m", "argos.authorization_certify", "--output", str(output)],
                cwd=str(temp_dir),
                env=environment,
                text=True,
                capture_output=True,
                timeout=30,
            )
            explicit_candidate = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "argos.authorization_certify",
                    "--candidate",
                    str(candidate),
                    "--output",
                    str(output),
                    "--single-run",
                ],
                cwd=str(temp_dir),
                env=environment,
                text=True,
                capture_output=True,
                timeout=60,
            )
            result_file_exists = (output / "certification_result.json").exists()

        self.assertNotEqual(missing_candidate.returncode, 0)
        self.assertEqual(explicit_candidate.returncode, 0, explicit_candidate.stderr)
        self.assertTrue(result_file_exists)

    def test_full_certification_uses_two_subprocess_clean_rooms_and_compares_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate = Path(temp_dir) / "candidate.zip"
            output = Path(temp_dir) / "evidence"
            _write_candidate_zip(candidate)

            final = run_full_certification(candidate, output)
            candidate_manifest_exists = (output / "00_identity/candidate_manifest.json").exists()
            run_one_summary_exists = (output / "02_clean_room/run_001/execution_summary.json").exists()
            comparison_exists = (output / "03_comparison/normalized_comparison.json").exists()

        self.assertEqual(final.final_status, PackageCertificationStatus.PASS)
        self.assertEqual(final.final_reconciliation["normalized_clean_room_comparison"], "IDENTICAL")
        self.assertEqual(final.final_reconciliation["unresolved_findings"], 0)
        self.assertEqual(final.clean_room_run_1.execution_identifier, "run_001")
        self.assertEqual(final.clean_room_run_2.execution_identifier, "run_002")
        self.assertNotEqual(final.clean_room_run_1.output_root, final.clean_room_run_2.output_root)
        self.assertTrue(candidate_manifest_exists)
        self.assertTrue(run_one_summary_exists)
        self.assertTrue(comparison_exists)

    def test_bad_archive_paths_fail_closed_with_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate = Path(temp_dir) / "bad.zip"
            output = Path(temp_dir) / "out"
            with zipfile.ZipFile(candidate, "w") as archive:
                archive.writestr("../escape.py", b"print('escape')\n")
                archive.writestr("src/argos/control_panel/authorization_implementation_closure.py", b"")

            result, _compilation, manifest = run_package_bound_certification(candidate, output)

        self.assertEqual(result.final_verdict, PackageCertificationStatus.FAIL)
        self.assertTrue(manifest.findings)
        self.assertTrue(result.findings)

    def test_missing_required_artifacts_are_explicit_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate = Path(temp_dir) / "partial.zip"
            output = Path(temp_dir) / "out"
            _write_candidate_zip(
                candidate,
                files={
                    "src/argos/control_panel/authorization_implementation_closure.py": b"AUTHORIZATION_MARKER = True\n",
                },
            )

            result, _compilation, _manifest = run_package_bound_certification(candidate, output)

        self.assertEqual(result.final_verdict, PackageCertificationStatus.FAIL)
        self.assertIn("focused Authorizations test artifact missing", result.findings)
        self.assertIn("regression test artifact missing", result.findings)


if __name__ == "__main__":
    unittest.main()
