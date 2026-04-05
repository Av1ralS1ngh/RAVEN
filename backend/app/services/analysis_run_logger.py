"""Best-effort persistence of analyze runs for offline ML training.

Each /api/blast/analyze response is appended as one JSON object line.
The logger never raises to callers; failures are intentionally swallowed.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# File lives at: backend/app/services/analysis_run_logger.py
# parents[0] -> services/
# parents[1] -> app/
# parents[2] -> backend/
# parents[3] -> recruitgraph/
_PROJECT_ROOT = Path(__file__).parents[3]
_LOG_DIR = _PROJECT_ROOT / "tmp" / "ml_data"
_LOG_FILE = _LOG_DIR / "analyze_runs.jsonl"


def log_analyze_run(
    recruiter_url: str,
    github_username: str,
    analyze_result: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append one analyze run payload as JSONL for downstream training jobs.

    This function is intentionally resilient and non-blocking from the API
    perspective. Any failure is logged and ignored.
    """
    payload = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "recruiter_url": recruiter_url,
        "github_username": github_username,
        "metadata": metadata or {},
        "result": analyze_result,
    }

    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        with _LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=True))
            fh.write("\n")
    except Exception as exc:
        logger.warning("Analyze run logging skipped: %s", exc)
