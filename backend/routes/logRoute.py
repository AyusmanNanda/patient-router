from flask import Blueprint, jsonify
from pathlib import Path
from services.logService import get_logs

logs_bp = Blueprint('logs', __name__)
LOG_FILE = Path(__file__).parent.parent / "logs" / "predictions.jsonl"
@logs_bp.route('/logs', methods=['GET'])
def logs():
    data = get_logs()
    return jsonify({
        "total_predictions": len(data),
        "total_emergencies": sum(log["emergency"] for log in data),
        "total_fallbacks": sum(log["fallback_used"] for log in data),
        "logs": data
    })

@logs_bp.route("/logs/clear", methods=["GET"])
def clear_logs():
    LOG_FILE.write_text("", encoding="utf-8")
    return jsonify({"message": "Logs cleared"})