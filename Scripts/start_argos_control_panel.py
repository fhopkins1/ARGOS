"""Start the local ARGOS Control Panel dashboard."""

from __future__ import annotations

from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel.server import main  # noqa: E402


if __name__ == "__main__":
    main()
