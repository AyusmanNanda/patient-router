from flask import Blueprint, jsonify, request
from services.feedbackService import save_feedback

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/feedback', methods=['POST'])
def feedback():
    data = request.json

    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    try:
        result = save_feedback(data)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except IOError as e:
        return jsonify({'error': str(e)}), 500
