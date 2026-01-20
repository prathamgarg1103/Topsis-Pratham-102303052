from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/topsis", methods=["GET", "POST"])
def topsis_api():
    if request.method == "GET":
        return jsonify({"status": "TOPSIS API running"})

    # POST request
    file = request.files.get("file")
    weights = request.form.get("weights")
    impacts = request.form.get("impacts")
    email = request.form.get("email")

    if not file or not weights or not impacts or not email:
        return jsonify({"message": "Missing input"}), 400

    return jsonify({"message": "File received successfully"})
