"""Convenience wrapper for final Trader ECS-003 audit package generation."""

from __future__ import annotations

from pathlib import Path
import sys


def _configure_package_path() -> None:
    repository_root = Path(__file__).resolve().parent
    source_root = repository_root / "src"
    if not (source_root / "argos").is_dir():
        raise RuntimeError(f"Required package source directory is missing: {source_root}")
    sys.path.insert(0, str(source_root))


_configure_package_path()

from argos.trader_ecs003_audit import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
