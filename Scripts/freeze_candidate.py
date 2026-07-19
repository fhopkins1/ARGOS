from __future__ import annotations

from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.candidate_identity import freeze_candidate_main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(freeze_candidate_main())
