from pathlib import Path
import json

LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "predictions.jsonl"

def get_logs():
    if not LOG_FILE.exists():
        return []
    logs = []
    with open(LOG_FILE, "r", encoding="utf-8") as log_file:
        for line in log_file:
            logs.append(json.loads(line))

    return logs[::-1] #newest first
