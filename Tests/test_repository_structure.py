from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from Scripts.verify_repository_structure import (
    REQUIRED_DIRECTORIES,
    REQUIRED_FILES,
    missing_directories,
    missing_files,
    prohibited_files_present,
    verify,
)


class RepositoryStructureTests(unittest.TestCase):
    def test_required_directories_exist(self) -> None:
        self.assertEqual(missing_directories(REPOSITORY_ROOT), [])

    def test_required_files_exist(self) -> None:
        self.assertEqual(missing_files(REPOSITORY_ROOT), [])

    def test_verifier_reports_no_violations(self) -> None:
        self.assertEqual(verify(REPOSITORY_ROOT), [])

    def test_no_prohibited_trading_runtime_files_exist(self) -> None:
        self.assertEqual(prohibited_files_present(REPOSITORY_ROOT), [])

    def test_structure_contract_lists_have_unique_entries(self) -> None:
        self.assertEqual(len(REQUIRED_DIRECTORIES), len(set(REQUIRED_DIRECTORIES)))
        self.assertEqual(len(REQUIRED_FILES), len(set(REQUIRED_FILES)))


if __name__ == "__main__":
    unittest.main()
