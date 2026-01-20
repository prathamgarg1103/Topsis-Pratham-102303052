from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/topsis", methods=["GET", "POST"])
def topsis_api():
    print(">>> Request received")

    if request.method == "GET":
        print(">>> GET request")
        return jsonify({"status": "API running"})

    print(">>> POST request")
    print("Files:", request.files)
    print("Form:", request.form)

    return jsonify({"message": "POST reached backend"})
