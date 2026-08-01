from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Scripts.historian_rm004_reproducibility_readiness import run_clean_room_auditor  # noqa: E402


if __name__ == "__main__":
    result = run_clean_room_auditor()
    print(json.dumps(result, indent=2, sort_keys=True))
