from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
import sys
import os

load_dotenv()

# add ml directory to path so predict_case can be imported
ML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ml")
sys.path.insert(0, ML_DIR)

from predict import predict_case

app = Flask(__name__)

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


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug)