from pathlib import Path
import json

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORT_FILE = REPORTS_DIR / "evaluation_metrics.json"
COMPARISON_FILE = REPORTS_DIR / "model_comparison.json"

def get_evaluation():
    if not REPORT_FILE.exists():
        return {
            "error" : "Evaluation report not found"
        }
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_comparison():
    if not COMPARISON_FILE.exists():
        return {
            "error" : "Comparison report not found"
        }
    with open(COMPARISON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_confusion_matrix():
    return REPORTS_DIR / "confusion_matrix.png"

def get_report_image():
    return REPORTS_DIR / "evaluation_report.png"

def get_comparison_image():
    return REPORTS_DIR / "model_comparison.png"