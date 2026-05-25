from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
import sys
import os
import csv
from flask_cors import CORS

load_dotenv()

ML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ml")
sys.path.insert(0, ML_DIR)

from predict import predict_case

app = Flask(__name__)
CORS(app)

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    if not data:
        return jsonify({"error": "Request body is required."}), 400

    symptoms = data.get("symptoms", "").strip()
    vitals   = data.get("vitals", "").strip()
    age      = data.get("age")
    duration = data.get("duration")

    if not symptoms:
        return jsonify({"error": "Symptoms are required."}), 400

    if age is None or duration is None:
        return jsonify({"error": "Age and duration are required."}), 400

    try:
        result = predict_case(
            symptoms=symptoms,
            vitals=vitals,
            age=int(age),
            duration=int(duration)
        )
        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.json

    if not data:
        return jsonify({"error": "Request body is required."}), 400

    symptoms = data.get("symptoms", "").strip()
    vitals = data.get("vitals", "normal").strip()
    age = data.get("age")
    duration = data.get("duration")
    correct_dept = data.get("correct_department")
    priority = data.get("priority", "low")

    gender = "unknown"

    if not correct_dept:
        return jsonify({"error": "Correct department is required."}), 400

    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "data.csv")

    try:
        with open(data_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([age, duration, symptoms, vitals, gender, priority, correct_dept])

        return jsonify({"message": "Feedback successfully saved to training data."}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to save data: {str(e)}"}), 500


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug)