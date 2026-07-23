"""Convenience wrapper for AUTH-IOC-001 independent reproduction.

The repository uses a ``src/`` layout.  This script is intentionally runnable
from a clean candidate extraction without manually setting ``PYTHONPATH``.
"""

from __future__ import annotations

from pathlib import Path
import sys


def _configure_package_path() -> Path:
    repository_root = Path(__file__).resolve().parent
    source_root = repository_root / "src"
    package_root = source_root / "argos"
    if not source_root.is_dir():
        raise RuntimeError(f"Required package source directory is missing: {source_root}")
    if not package_root.is_dir():
        raise RuntimeError(f"Required package directory is missing: {package_root}")
    source_root_text = str(source_root)
    if source_root_text not in sys.path:
        sys.path.insert(0, source_root_text)
    return package_root.resolve()


_EXPECTED_PACKAGE_ROOT = _configure_package_path()

import argos  # noqa: E402
from argos.authorization_independent_certify import main  # noqa: E402


def _validate_candidate_local_import() -> None:
    package_file = Path(argos.__file__ or "").resolve()
    if _EXPECTED_PACKAGE_ROOT != package_file.parent and _EXPECTED_PACKAGE_ROOT not in package_file.parents:
        raise RuntimeError(
            "Imported argos package is not candidate-local: "
            f"{package_file} is outside {_EXPECTED_PACKAGE_ROOT}"
        )


_validate_candidate_local_import()


if __name__ == "__main__":
    raise SystemExit(main())
