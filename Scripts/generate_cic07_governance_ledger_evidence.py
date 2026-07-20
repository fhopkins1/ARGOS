from __future__ import annotations

from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.certification_governance_ledger import cic07_main  # noqa: E402


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raise SystemExit(cic07_main(sys.argv[1:]))
    output = REPOSITORY_ROOT / "outputs" / "cic07_governance_ledger"
    raise SystemExit(cic07_main(["--output", str(output), "--repo-root", str(REPOSITORY_ROOT)]))
