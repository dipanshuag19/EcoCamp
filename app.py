# https://dipanshuag19.dipanshuag19.publicvm.com/

from flask import Flask, request, redirect, url_for, render_template, jsonify, render_template_string
#import sqlite3 as sq
import os
import sqlitecloud as sq
from functools import wraps

app = Flask(__name__)

def sqldb(function):
    @wraps(function)
    def wrapper():
        db = sq.connect(os.environ.get("SQLITECLOUD"))
        db.row_factory = sq.Row
        c = db.cursor()
        final = function(c)
        db.commit()
        db.close()
        return final
    return wrapper

@app.route("/")
@sqldb
def home(c):
    mylist = []
    for row in c.execute("SELECT * FROM eventdetail"):
        mylist.append(f"ID: {row[0]} Name: {row[1]}")
    return render_template("index.html", mylist=mylist)


@app.route("/index2")
@sqldb
def home2(c):
    mylist = []
    for row in c.execute("SELECT * FROM eventdetail"):
        mylist.append(f'ID: {row["eventid"]} Name: {row["eventname"]}')
    return render_template("index2.html", mylist=mylist)

@app.route("/addevent", methods=["GET", "POST"])
@sqldb
def addevent(c):
    if request.method == "POST":
        field = ["eventname", "email", "starttime", "endtime", "date", "location"] 
        event_values = [request.form.get(y) for y in field]
        check = c.execute("SELECT * FROM eventdetail WHERE eventname=(?)", (event_values[0],))
        fetchall = check.fetchall()
        zipped = zip(field, event_values)
        for ab in fetchall:
                if all(ab[x] == y for x,y in zipped):
                    return "edit_from_id"
        tuple_all, tuple_event_values = tuple(field), tuple(event_values)
        c.execute(f"INSERT INTO eventdetail{tuple_all} VALUES {tuple_event_values}")
        return redirect(url_for("home"))
    return render_template("addevent.html")

@app.route("/deleteevent", methods=["GET", "POST"])
@sqldb
def deleteevent(c):
    if request.method == "POST":
        event_id = request.form.get("eventid")
        try:
            c.execute("DELETE FROM eventdetail WHERE id=(?)", event_id)
            return redirect(url_for("home"))
        except Exception as e:
            return f"Error: {e}"
    html_code = """<html><head><title>Delete event</title></head>
    <body><form onsubmit='/deleteevent' method='POST'>
    Enter event id to delete: <input type='number' name='eventid'><br><br> <button type='submit'>Delete Event</button></body></html>
    """
    return render_template_string(html_code)
        
