from flask import Flask, request, redirect, url_for, render_template, jsonify, render_template_string
#import sqlite3 as sq
import os
import sqlitecloud as sq
from functools import wraps

app = Flask(__name__)
db = sq.connect(os.environ.get("SQLITECLOUD"))
c = db.cursor()

def sqldb(function):
    @wraps(function)
    def wrapper():
        db = sq.connect(os.environ.get("SQLITECLOUD"))
        c = db.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS hi(id INT primary key, name VARCHAR(30))")
        final = function(c)
        db.commit()
        db.close()
        return final
    return wrapper

@app.route("/")
@sqldb
def home(c):
    mylist = []
    for row in c.execute("SELECT * FROM hi"):
        mylist.append(f"ID: {row[0]} Name: {row[1]}")
    return render_template("index.html", mylist=mylist)

@app.route("/addevent", methods=["GET", "POST"])
@sqldb
def addevent(c):
    if request.method == "POST":
        event_id = request.form.get("eventid")
        event_name = request.form.get("eventname")
        if event_id and event_name:
            c.execute("INSERT INTO hi(id, name) VALUES (?, ?)", (event_id, event_name))
            return redirect(url_for("home"))
        return "Missing data or Wrong ID"
    return render_template("addevent.html")

@app.route("/deleteevent", methods=["GET", "POST"])
@sqldb
def deleteevent(c):
    if request.method == "POST":
        event_id = request.form.get("eventid")
        try:
            c.execute("DELETE FROM hi WHERE id=(?)", event_id)
            return redirect(url_for("home"))
        except Exception as e:
            return f"Error: {e}"
    html_code = """<html><head><title>Delete event</title></head>
    <body><form onsubmit='/deleteevent' method='POST'>
    Enter event id to delete: <input type='number' name='eventid'><br><br> <button type='submit'>Delete Event</button></body></html>
    """
    return render_template_string(html_code)
        
