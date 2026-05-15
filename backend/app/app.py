from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
import os

DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    #dummy response
    return jsonify({
        "department" : "cardiology",
        "confidence" : 0.85,
        "fallback" : False
    })

if __name__ == '__main__':
    app.run(debug=True)