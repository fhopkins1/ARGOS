from __future__ import annotations

from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.candidate_integrity import cic01_main  # noqa: E402


if __name__ == "__main__":
    default_output = REPOSITORY_ROOT.parent / "ARGOS_CIC01_EVIDENCE"
    argv = sys.argv[1:] or ["--repo-root", str(REPOSITORY_ROOT), "--evidence-output", str(default_output)]
    raise SystemExit(cic01_main(argv))
