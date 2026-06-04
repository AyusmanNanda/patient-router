from flask import Blueprint, jsonify
from services.logService import get_logs
from services.logService import clear_logs

logs_bp = Blueprint('logs', __name__)
@logs_bp.route('/logs', methods=['GET'])
def logs():
    data = get_logs()
    return jsonify({
        "total_predictions": len(data),
        "total_emergencies": sum(log["emergency"] for log in data),
        "total_fallbacks": sum(log["fallback_used"] for log in data),
        "logs": data
    })

@logs_bp.route("/logs/clear", methods=["POST"])
def clear():
    clear_logs()
    return jsonify({"message" : "Logs cleared"})