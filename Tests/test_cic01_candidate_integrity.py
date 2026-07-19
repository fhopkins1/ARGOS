from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.candidate_integrity import (  # noqa: E402
    CIC01FailureCode,
    CIC01Rejection,
    bind_artifact_identity,
    build_cic01_candidate_contract,
    detect_candidate_mutation,
    generate_cic01_evidence,
    validate_artifact_binding,
    validate_cic01_contract,
    validate_mixed_candidate_package,
)


class DeterministicGitRepo:
    def __enter__(self):
        self.path = Path(tempfile.mkdtemp(prefix="argos-cic01-fixture-"))
        self.git("init", "-b", "main")
        self.git("config", "user.name", "ARGOS Fixture")
        self.git("config", "user.email", "argos.fixture@example.test")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.autocrlf", "false")
        self.git("config", "core.filemode", "false")
        (self.path / "src").mkdir()
        (self.path / "src" / "candidate.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.path / "pyproject.toml").write_text("[project]\nname='fixture'\nversion='1.0'\n", encoding="utf-8")
        self.git("add", ".")
        env = {
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
        }
        self.git("commit", "-m", "initial", extra_env=env)
        return self

    def __exit__(self, exc_type, exc, tb):
        shutil.rmtree(self.path, ignore_errors=True)

    def git(self, *args, extra_env=None):
        env = None
        if extra_env:
            import os

            env = {**os.environ, **extra_env}
        result = subprocess.run(("git", *args), cwd=self.path, text=True, capture_output=True, check=False, env=env)
        if result.returncode != 0:
            raise AssertionError(result.stderr)
        return result.stdout.strip()


class CIC01CandidateIntegrityTests(unittest.TestCase):
    def test_clean_candidate_contract_is_deterministic_and_valid(self) -> None:
        with DeterministicGitRepo() as repo:
            first = build_cic01_candidate_contract(repo.path)
            second = build_cic01_candidate_contract(repo.path)

        self.assertEqual(first["candidateContractDigest"], second["candidateContractDigest"])
        self.assertEqual("PASS", first["status"])
        self.assertTrue(validate_cic01_contract(first)["valid"])
        self.assertEqual(40, len(first["candidateIdentity"]["repositoryCommit"]))

    def test_modified_tracked_and_relevant_untracked_files_are_rejected(self) -> None:
        with DeterministicGitRepo() as repo:
            (repo.path / "src" / "candidate.py").write_text("VALUE = 2\n", encoding="utf-8")
            with self.assertRaises(CIC01Rejection) as modified:
                build_cic01_candidate_contract(repo.path)
            self.assertTrue(
                {
                    CIC01FailureCode.TRACKED_STATE_DIRTY.value,
                    CIC01FailureCode.INDEX_STATE_DIRTY.value,
                }
                & set(modified.exception.details["failureCodes"])
            )

        with DeterministicGitRepo() as repo:
            (repo.path / "src" / "new_module.py").write_text("VALUE = 3\n", encoding="utf-8")
            with self.assertRaises(CIC01Rejection) as untracked:
                build_cic01_candidate_contract(repo.path)
            self.assertIn(CIC01FailureCode.RELEVANT_UNTRACKED_STATE_DIRTY.value, untracked.exception.details["failureCodes"])

    def test_evidence_generation_outside_worktree_does_not_mutate_candidate(self) -> None:
        with DeterministicGitRepo() as repo:
            out = Path(tempfile.mkdtemp(prefix="argos-cic01-evidence-"))
            try:
                manifest = generate_cic01_evidence(repo.path, out)
                manifest_exists = (out / "cic01_evidence_manifest.json").exists()
                contract = build_cic01_candidate_contract(repo.path)
                mutation = detect_candidate_mutation(repo.path, contract, stage="test_post_generation")
            finally:
                shutil.rmtree(out, ignore_errors=True)

        self.assertEqual("PASS", manifest["verdict"])
        self.assertEqual("PASS", mutation["verdict"])
        self.assertTrue(manifest_exists)

    def test_artifact_binding_detects_tampering_and_mixed_candidates(self) -> None:
        with DeterministicGitRepo() as repo:
            contract = build_cic01_candidate_contract(repo.path)
            artifact = {"verdict": "PASS"}
            binding = bind_artifact_identity(artifact, contract, artifact_type="unit", producer="test")
            self.assertTrue(validate_artifact_binding(artifact, binding, contract)["valid"])
            self.assertFalse(validate_artifact_binding({"verdict": "FAIL"}, binding, contract)["valid"])

            other = dict(binding)
            other["repositoryCommit"] = "1" * 40
            mixed = validate_mixed_candidate_package((binding, other))

        self.assertFalse(mixed["valid"])
        self.assertIn(CIC01FailureCode.MIXED_CANDIDATE_PACKAGE.value, mixed["failureCodes"])


if __name__ == "__main__":
    unittest.main()
