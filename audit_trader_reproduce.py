"""Convenience wrapper for TRADER-IC-000 independent audit reproduction."""

from __future__ import annotations

from pathlib import Path
import sys


def _configure_package_path() -> None:
    repository_root = Path(__file__).resolve().parent
    source_root = repository_root / "src"
    package_root = source_root / "argos"
    if not source_root.is_dir():
        raise RuntimeError(f"Required package source directory is missing: {source_root}")
    if not package_root.is_dir():
        raise RuntimeError(f"Required package directory is missing: {package_root}")
    sys.path.insert(0, str(source_root))


_configure_package_path()

from argos.trader_audit import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
