from flask import Flask, jsonify
from flask_cors import CORS
from flask import render_template

app = Flask(__name__)
CORS(app)  # allows frontend to call this API

@app.route("/")
def get_message():
    mylist = []
    for x in range(100):
        mylist.append(f"Index {x}")
    return render_template("index.html", mylist=mylist)
