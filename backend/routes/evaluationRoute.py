from flask import Blueprint, jsonify, send_file
from services.evaluationService import get_evaluation, get_comparison_image
from services.evaluationService import get_report_image
from services.evaluationService import get_confusion_matrix
from services.evaluationService import get_comparison

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

@evaluation_bp.route('/evaluation/comparison', methods=['GET'])
def comparison():
    return jsonify(get_comparison())

@evaluation_bp.route('/evaluation/comparison-image', methods=['GET'])
def comparison_image():
    return send_file(get_comparison_image(), mimetype='image/png')