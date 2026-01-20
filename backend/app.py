from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "TOPSIS Backend Running"

@app.route("/topsis", methods=["POST"])
def topsis_api():
    file = request.files.get("file")
    weights = request.form.get("weights")
    impacts = request.form.get("impacts")
    email = request.form.get("email")

    # call your TOPSIS logic here

    return jsonify({
        "message": "Result will be sent to your email"
    })

if __name__ == "__main__":
    app.run()
