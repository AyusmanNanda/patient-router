import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
data_path = BASE_DIR / "data" / "data.csv"

def save_feedback(data):
    symptoms = (data.get("symptoms") or "").strip()
    vitals = (data.get("vitals") or "normal").strip()
    age = data.get("age")
    duration = data.get("duration")
    correct_dept = data.get("correct_department")
    priority = data.get("priority") or "low"
    gender = data.get("gender") or "male"
    history = (data.get("history") or "").strip()

    if not correct_dept:
        raise ValueError("Correct department is required")
    if age is None or duration is None:
        raise ValueError("Age and duration are required")

    try:
        with open(data_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow([age, duration, symptoms, vitals, history, gender, priority, correct_dept])

        return {
            "message": "Feedback successfully saved to training data."
        }

    except IOError as e:
        raise IOError("Error: failed to save data") from e