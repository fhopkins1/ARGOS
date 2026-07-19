from __future__ import annotations

from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.proof_based_certification import cic04_main  # noqa: E402


if __name__ == "__main__":
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPOSITORY_ROOT / "outputs" / "cic04_proof_certification"
    raise SystemExit(cic04_main(["--repo-root", str(REPOSITORY_ROOT), "--output", str(output)]))
