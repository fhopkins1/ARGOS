from __future__ import annotations

from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.semantic_drift_engine import cic06_main  # noqa: E402


if __name__ == "__main__":
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPOSITORY_ROOT / "outputs" / "cic06_semantic_drift"
    raise SystemExit(cic06_main(["--repo-root", str(REPOSITORY_ROOT), "--output", str(output)]))

