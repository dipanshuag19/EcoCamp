from flask import Flask, jsonify
from flask_cors import CORS
from flask import render_template

app = Flask(__name__, template_folder=".")
CORS(app)  # allows frontend to call this API


@app.route("/")
def get_message():
    return render_template("index.html")
