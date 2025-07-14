from flask import Flask, jsonify, request, redirect, url_for
from flask_cors import CORS
from flask import render_template
import sqlite3 as sq

db = sq.connect("hi.db")
c = db.cursor()

app = Flask(__name__)
CORS(app)  # allows frontend to call this API

c.execute("CREATE TABLE IF NOT EXISTS hi(id int primary key, name varchar(30))")

@app.route("/")
def get_message():
    mylist = []
    events__ = c.execute("SELECT * FROM hi")
    for x, y in events__:
        mylist.append(f"ID: {x} Name: {y}")
    return render_template("index.html", mylist=mylist)

@app.route("/addevent", methods=["POST"])
def addevent():
        id = request.form.get("eventid")
        name = request.form.get("eventname")
        if id and name:
            c.execute(f"INSERT INTO hi(id, name) VALUES ({id}, '{name}')")
            db.commit()
            return "Event added... Redirect to home page", redirect(url_for("get_message"))
        else:
            return "Cant add.."
