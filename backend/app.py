from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
from flask_cors import CORS

from routes.predictRoute import predict_bp
from routes.feedbackRoute import feedback_bp
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
app.register_blueprint(feedback_bp)
app.register_blueprint(home_bp)
app.register_blueprint(health_bp)

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug)