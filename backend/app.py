from flask import Flask
from dotenv import load_dotenv
import os
from flask_cors import CORS

from routes.predictRoute import predict_bp
from routes.feedbackRoute import feedback_bp
from routes.logRoute import logs_bp
from routes.homeRoute import home_bp
from routes.healthRoute import health_bp

load_dotenv()
frontend_url = os.getenv("FRONTEND_URL")
if not frontend_url:
    raise RuntimeError("FRONTEND_URL and PRODUCTION_FRONTEND_URL must be set")
app = Flask(__name__)
CORS(app,
     origins=
     [frontend_url],
     supports_credentials=True
)

app.register_blueprint(predict_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(logs_bp)
app.register_blueprint(home_bp)
app.register_blueprint(health_bp)

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug)