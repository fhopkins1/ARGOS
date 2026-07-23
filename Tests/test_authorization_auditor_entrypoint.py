from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _write_zip_from_repo(zip_path: Path) -> None:
    required = (
        "AUDITOR_README.md",
        "audit_reproduce.py",
        "authorization_environment_lock.json",
        "src/argos/__init__.py",
        "src/argos/authorization_certify.py",
        "src/argos/authorization_independent_certify.py",
        "src/argos/authorization_package_certification.py",
        "src/argos/control_panel/authorization_implementation_closure.py",
        "Tests/test_authorization_implementation_closure.py",
        "Tests/test_trade_execution_office.py",
    )
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in required:
            info = zipfile.ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (REPOSITORY_ROOT / relative).read_bytes())


def _extract_candidate(candidate_zip: Path, destination: Path) -> None:
    with zipfile.ZipFile(candidate_zip, "r") as archive:
        archive.extractall(destination)


def _clean_env() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    return environment


class AuthorizationAuditorEntrypointTests(unittest.TestCase):
    def test_exact_readme_command_passes_without_pythonpath_from_candidate_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            candidate = base / "candidate.zip"
            extraction = base / "candidate"
            output = base / "out"
            _write_zip_from_repo(candidate)
            _extract_candidate(candidate, extraction)

            completed = subprocess.run(
                [sys.executable, "audit_reproduce.py", "--candidate", str(candidate), "--output", str(output)],
                cwd=str(extraction),
                env=_clean_env(),
                text=True,
                capture_output=True,
                timeout=180,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads((output / "06_final/independent_certification_decision.json").read_text(encoding="utf-8"))
            self.assertEqual(decision["decision"], "UNCONDITIONAL_INDEPENDENT_AUTHORIZATIONS_OFFICE_CERTIFICATION_PASS")

    def test_non_root_invocation_passes_without_pythonpath(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            candidate = base / "candidate.zip"
            extraction = base / "candidate"
            outside = base / "outside"
            output = base / "out"
            outside.mkdir()
            _write_zip_from_repo(candidate)
            _extract_candidate(candidate, extraction)

            completed = subprocess.run(
                [sys.executable, str(extraction / "audit_reproduce.py"), "--candidate", str(candidate), "--output", str(output)],
                cwd=str(outside),
                env=_clean_env(),
                text=True,
                capture_output=True,
                timeout=180,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_external_argos_shadowing_does_not_override_candidate_local_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            candidate = base / "candidate.zip"
            extraction = base / "candidate"
            shadow = base / "shadow"
            output = base / "out"
            (shadow / "argos").mkdir(parents=True)
            (shadow / "argos" / "__init__.py").write_text("raise RuntimeError('external argos loaded')\n", encoding="utf-8")
            _write_zip_from_repo(candidate)
            _extract_candidate(candidate, extraction)
            environment = _clean_env()
            environment["PYTHONPATH"] = str(shadow)

            completed = subprocess.run(
                [sys.executable, str(extraction / "audit_reproduce.py"), "--candidate", str(candidate), "--output", str(output)],
                cwd=str(base),
                env=environment,
                text=True,
                capture_output=True,
                timeout=180,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_missing_src_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            candidate = base / "candidate.zip"
            extraction = base / "candidate"
            output = base / "out"
            _write_zip_from_repo(candidate)
            _extract_candidate(candidate, extraction)
            shutil.move(str(extraction / "src"), str(extraction / "src_missing"))

            completed = subprocess.run(
                [sys.executable, str(extraction / "audit_reproduce.py"), "--candidate", str(candidate), "--output", str(output)],
                cwd=str(extraction),
                env=_clean_env(),
                text=True,
                capture_output=True,
                timeout=30,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Required package source directory is missing", completed.stderr)

    def test_missing_argos_package_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            candidate = base / "candidate.zip"
            extraction = base / "candidate"
            output = base / "out"
            _write_zip_from_repo(candidate)
            _extract_candidate(candidate, extraction)
            shutil.move(str(extraction / "src" / "argos"), str(extraction / "src" / "argos_missing"))

            completed = subprocess.run(
                [sys.executable, str(extraction / "audit_reproduce.py"), "--candidate", str(candidate), "--output", str(output)],
                cwd=str(extraction),
                env=_clean_env(),
                text=True,
                capture_output=True,
                timeout=30,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Required package directory is missing", completed.stderr)


if __name__ == "__main__":
    unittest.main()
