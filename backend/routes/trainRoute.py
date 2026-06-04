from flask import Blueprint, jsonify
from services.trainService import train_model

train_bp = Blueprint("train", __name__)

@train_bp.route("/train", methods=["POST"])
def train():
    return jsonify(train_model())