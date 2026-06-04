from flask import Blueprint, jsonify, send_file
from services.evalutationService import get_evaluation
from services.evalutationService import get_report_image
from services.evalutationService import get_confusion_matrix

evaluation_bp = Blueprint('evaluation', __name__)
@evaluation_bp.route('/evaluation', methods=['GET'])
def evaluation():
    return jsonify(get_evaluation())

@evaluation_bp.route('/evaluation/report-image', methods=['GET'])
def report_image():
    return send_file(get_report_image(), mimetype='image/png')

@evaluation_bp.route('/evaluation/confusion-matrix', methods=['GET'])
def confusion_matrix():
    return send_file(get_confusion_matrix(), mimetype='image/png')