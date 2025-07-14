from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allows frontend to call this API

@app.route("/api/message")
def get_message():
    return jsonify({"message": "Hello from Flask on Koyeb!"})
