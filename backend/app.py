from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
import sys
import os
import csv
from flask_cors import CORS
from ml.constants import MODEL_VERSION

from routes.predictRoute import predict_bp
from routes.homeRoute import home_bp
from routes.healthRoute import health_bp

load_dotenv()
app = Flask(__name__)
CORS(app,
     origins=
     ["http://localhost:5173",
      "https://patient-router.vercel.app"],
     supports_credentials=True
)

app.register_blueprint(predict_bp)
app.register_blueprint(home_bp)
app.register_blueprint(health_bp)

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
    gender=data.get("gender", "male")

    if not correct_dept:
        return jsonify({"error": "Correct department is required."}), 400

    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "", "data", "data.csv")

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