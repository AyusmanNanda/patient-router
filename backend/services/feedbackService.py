import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
data_path = BASE_DIR / "data" / "data.csv"

def save_feedback(data):
    symptoms = data.get("symptoms", "").strip()
    vitals = (data.get("vitals") or "normal").strip()
    age = data.get("age")
    duration = data.get("duration")
    correct_dept = data.get("correct_department")
    priority = data.get("priority", "low")
    gender = data.get("gender", "male")
    history = data.get("history", "").strip()

    if not correct_dept:
        raise ValueError("Correct department is required")

    try:
        with open(data_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([age, duration, symptoms, vitals, history, gender, priority, correct_dept])

        return {
            "message": "Feedback successfully saved to training data."
        }

    except IOError as e:
        raise IOError("Error: failed to save data") from e