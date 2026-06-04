from flask import Blueprint, jsonify
from services.evalutationService import get_evaluation

evaluation_bp = Blueprint('evaluation', __name__)
@evaluation_bp.route('/evaluation', methods=['GET'])
def evaluation():
    return jsonify(get_evaluation())