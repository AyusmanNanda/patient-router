import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def log_prediction(filename: str, prediction: dict):
    with open(LOGS_DIR / filename, "a") as f:
        f.write(json.dumps(prediction) + "\n")