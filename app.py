from flask import Flask, request, redirect, url_for, render_template, jsonify
import sqlite3 as sq

app = Flask(__name__)
db = sq.connect("hi.db", check_same_thread=False)
c = db.cursor()

# Create table
c.execute("CREATE TABLE IF NOT EXISTS hi(id INT, name VARCHAR(30))")

@app.route("/")
def get_message():
    mylist = []
    for row in c.execute("SELECT * FROM hi"):
        mylist.append(f"ID: {row[0]} Name: {row[1]}")
    return render_template("index.html", mylist=mylist)

@app.route("/addevent", methods=["GET", "POST"])
def addevent():
    if request.method == "POST":
        event_id = request.form.get("eventid")
        event_name = request.form.get("eventname")
        if event_id and event_name:
            c.execute("INSERT INTO hi(id, name) VALUES (?, ?)", (event_id, event_name))
            db.commit()
            return redirect(url_for("get_message"))
        return "Missing data", 400
    return render_template("addevent.html")
