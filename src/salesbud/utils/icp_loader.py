import json
from pathlib import Path
from typing import Any, Dict, Optional

import salesbud.utils.logger as logger


def load_icp_config() -> Optional[Dict[str, Any]]:
    """Load ICP configuration from icp.toon or icp.json"""
    cwd = Path.cwd()
    icp_toon = cwd / "icp.toon"
    icp_json = cwd / "icp.json"

    if icp_toon.exists():
        try:
            with open(icp_toon, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.print_text(f"[Warning] Failed to parse icp.toon: {e}")

    if icp_json.exists():
        try:
            with open(icp_json, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.print_text(f"[Warning] Failed to parse icp.json: {e}")

    return None
