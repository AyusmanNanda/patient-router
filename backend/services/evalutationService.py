from pathlib import Path
import json

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORT_FILE = REPORTS_DIR / "evaluation_metrics.json"

def get_evaluation():
    if not REPORT_FILE.exists():
        return {
            "error" : "Evaluation report not found"
        }
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)