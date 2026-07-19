from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

from argos.candidate_identity import (
    build_candidate_identity,
    freeze_candidate,
    mixed_candidate_scan,
    run_preflight,
    verify_archive,
)


class CR1CandidateIdentityTests(unittest.TestCase):
    def test_full_commit_is_captured_from_git(self) -> None:
        with temporary_repo() as repo:
            payload = build_candidate_identity(repo)

            commit = payload["candidate_identity"]["repository_commit"]
            self.assertEqual(len(commit), 40)
            self.assertEqual(git(repo, "cat-file", "-t", commit), "commit")

    def test_dirty_states_are_rejected(self) -> None:
        with temporary_repo() as repo:
            (repo / "untracked.txt").write_text("new", encoding="utf-8")
            result = run_preflight(repo, certification=True)
            self.assertEqual(result["preflight_result"]["verdict"], "FAIL")
            self.assertEqual(result["preflight_result"]["rejections"][0]["code"], "CANDIDATE_DIRTY_UNTRACKED")

        with temporary_repo() as repo:
            (repo / "src" / "argos" / "sample.py").write_text("VALUE = 2\n", encoding="utf-8")
            result = run_preflight(repo, certification=True)
            self.assertEqual(result["preflight_result"]["rejections"][0]["code"], "CANDIDATE_DIRTY_TRACKED")

        with temporary_repo() as repo:
            (repo / "src" / "argos" / "sample.py").write_text("VALUE = 3\n", encoding="utf-8")
            git(repo, "add", "src/argos/sample.py")
            result = run_preflight(repo, certification=True)
            self.assertEqual(result["preflight_result"]["rejections"][0]["code"], "CANDIDATE_DIRTY_STAGED")

    def test_stable_identity_hash_ignores_timestamp_only_regeneration(self) -> None:
        with temporary_repo() as repo:
            first = build_candidate_identity(repo)["candidate_identity"]
            second = build_candidate_identity(repo)["candidate_identity"]

            self.assertEqual(first["stable_identity_hash"], second["stable_identity_hash"])
            self.assertEqual(first["source_tree_hash"], second["source_tree_hash"])

    def test_domain_hashes_change_on_domain_changes(self) -> None:
        with temporary_repo() as repo:
            base = build_candidate_identity(repo)["candidate_identity"]
            mutate_and_commit(repo, "src/argos/sample.py", "VALUE = 99\n")
            source_changed = build_candidate_identity(repo)["candidate_identity"]
            self.assertNotEqual(base["source_tree_hash"], source_changed["source_tree_hash"])

        with temporary_repo() as repo:
            base = build_candidate_identity(repo)["candidate_identity"]
            mutate_and_commit(repo, "pyproject.toml", repo.joinpath("pyproject.toml").read_text(encoding="utf-8") + "\n# dep\n")
            dependency_changed = build_candidate_identity(repo)["candidate_identity"]
            self.assertNotEqual(base["dependency_hash"], dependency_changed["dependency_hash"])

        for path, key in (
            ("config/runtime.json", "configuration_hash"),
            ("src/argos/authority_policy.py", "policy_hash"),
            ("src/argos/decision_schema.py", "schema_hash"),
        ):
            with self.subTest(path=path):
                with temporary_repo() as repo:
                    base = build_candidate_identity(repo)["candidate_identity"]
                    mutate_and_commit(repo, path, repo.joinpath(path).read_text(encoding="utf-8") + "\n# changed\n")
                    changed = build_candidate_identity(repo)["candidate_identity"]
                    self.assertNotEqual(base[key], changed[key])

    def test_mixed_candidate_scan_rejects_descendant_or_ancestor_commits(self) -> None:
        with temporary_repo() as repo:
            old_commit = git(repo, "rev-parse", "HEAD")
            mutate_and_commit(repo, "src/argos/sample.py", "VALUE = 4\n")
            new_commit = git(repo, "rev-parse", "HEAD")
            evidence = repo / "Documentation" / "active_report.md"
            evidence.write_text(f"old commit {old_commit}\n", encoding="utf-8")
            git(repo, "add", "Documentation/active_report.md")
            git(repo, "commit", "-m", "add mixed report")

            scan = mixed_candidate_scan(repo, git(repo, "rev-parse", "HEAD"))
            self.assertTrue(scan["active_mixed_candidate_rejected"])
            self.assertNotEqual(old_commit, new_commit)

    def test_freeze_excludes_historical_archives_and_verifies_manifest(self) -> None:
        with temporary_repo() as repo:
            historical = repo / "Documentation" / "EO-OLD_Evidence"
            historical.mkdir(parents=True, exist_ok=True)
            (historical / "old.json").write_text(json.dumps({"repositoryCommit": "0" * 40}), encoding="utf-8")
            (repo / "ARGOS_REPOSITORY_old.zip").write_bytes(b"old archive")
            git(repo, "add", "Documentation/EO-OLD_Evidence/old.json", "ARGOS_REPOSITORY_old.zip")
            git(repo, "commit", "-m", "add historical artifacts")
            with tempfile.TemporaryDirectory() as out:
                result = freeze_candidate(repo, out)
                archive_path = Path(result["freeze_result"]["archive"])

                self.assertTrue(result["freeze_result"]["verification"]["verified"])
                with zipfile.ZipFile(archive_path, "r") as archive:
                    names = "\n".join(archive.namelist())
                    self.assertNotIn("EO-OLD_Evidence", names)
                    self.assertNotIn("ARGOS_REPOSITORY_old.zip", names)
                    self.assertIn("src/argos/sample.py", names)

    def test_archive_tampering_is_detected(self) -> None:
        with temporary_repo() as repo:
            with tempfile.TemporaryDirectory() as out:
                result = freeze_candidate(repo, out)
                archive_path = Path(result["freeze_result"]["archive"])
                commit = result["candidate_identity"]["repository_commit"]
                with zipfile.ZipFile(archive_path, "a") as archive:
                    archive.writestr(f"ARGOS-{commit}/tampered.txt", "tampered")

                verification = verify_archive(
                    archive_path,
                    result["candidate_manifest"]["entries"],
                    commit,
                )
                self.assertFalse(verification["verified"])
                self.assertTrue(verification["extra"])


def temporary_repo():
    context = tempfile.TemporaryDirectory()
    repo = Path(context.__enter__())
    git(repo, "init")
    git(repo, "config", "user.email", "cr1@example.invalid")
    git(repo, "config", "user.name", "CR1 Tests")
    git(repo, "config", "core.autocrlf", "false")
    (repo / "src" / "argos").mkdir(parents=True)
    (repo / "Tests").mkdir()
    (repo / "Scripts").mkdir()
    (repo / "Documentation").mkdir()
    (repo / "config").mkdir()
    (repo / "src" / "argos" / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "src" / "argos" / "authority_policy.py").write_text("POLICY = 'strict'\n", encoding="utf-8")
    (repo / "src" / "argos" / "decision_schema.py").write_text("SCHEMA = {'v': 1}\n", encoding="utf-8")
    (repo / "Tests" / "test_sample.py").write_text("def test_sample():\n    assert True\n", encoding="utf-8")
    (repo / "Scripts" / "run.py").write_text("print('run')\n", encoding="utf-8")
    (repo / "config" / "runtime.json").write_text('{"mode": "paper"}\n', encoding="utf-8")
    (repo / "pyproject.toml").write_text('[project]\nname = "tmp"\nversion = "0.1.0"\ndependencies = []\n', encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "initial")

    class RepoContext:
        def __enter__(self):
            return repo

        def __exit__(self, exc_type, exc, tb):
            return context.__exit__(exc_type, exc, tb)

    return RepoContext()


def mutate_and_commit(repo: Path, rel_path: str, content: str) -> None:
    path = repo / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    git(repo, "add", rel_path)
    git(repo, "commit", "-m", f"mutate {rel_path}")


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=repo, text=True, capture_output=True, check=True)
    return result.stdout.strip()


if __name__ == "__main__":
    unittest.main()
