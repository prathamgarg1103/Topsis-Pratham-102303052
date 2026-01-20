from flask import Flask, request, jsonify
import pandas as pd
import numpy as np

app = Flask(__name__)

@app.route("/")
def home():
    return "TOPSIS Backend Running"

@app.route("/topsis", methods=["POST"])
def topsis_api():
    file = request.files.get("file")
    weights = request.form.get("weights")
    impacts = request.form.get("impacts")
    email = request.form.get("email")

    if not file or not weights or not impacts or not email:
        return jsonify({"message": "Missing input"}), 400

    return jsonify({"message": "Backend reached successfully"})
