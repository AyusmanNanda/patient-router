from flask import Blueprint, jsonify, request
from services.dataService import generate_data
from services.dataService import get_data_stats

data_bp = Blueprint("data", __name__)

@data_bp.route("/data", methods=["GET"])
def data():
    return jsonify(get_data_stats())

@data_bp.route("/data/generate", methods=["POST"])
def generate():
    rows = request.json.get("rows", 50000)
    return jsonify(
        generate_data(rows)
    )