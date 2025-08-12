# https://dipanshuag19.dipanshuag19.publicvm.com/

from flask import Flask, request, redirect, url_for, render_template, render_template_string, flash, session
#import sqlite3 as sq
import os,uuid
import sqlitecloud as sq
from functools import wraps

app = Flask(__name__)
app.secret_key = "ecocamp.fp"

def sqldb(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        db = sq.connect(os.environ.get("SQLITECLOUD"))
        db.row_factory = sq.Row
        c = db.cursor()
        final = function(c, *args, **kwargs)
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
    if not session.get('username'):
        randomuuid = uuid.uuid4()
        session["username"] = randomuuid
    print("Welcome", session["username"])
    # eid,ename,email,desc,stime,etime,edate,location,category in edetailslist
    c.execute("SELECT * FROM eventdetail")
    edetailslist = c.fetchall()
    treeplant, blooddonate, cleandrive = [], [], []
    for x in edetailslist:
        if x['category'] == 'Tree Plantation':
            treeplant.append(x)
        elif x['category'] == 'Blood Donation':
            blooddonate.append(x)
        else:
            cleandrive.append(x)
    return render_template("index2.html", edetailslist=edetailslist, treeplantation=treeplant, blooddonation=blooddonate, cleanlinesdrive=cleandrive)

@app.route("/index3")
@sqldb
def home3(c):
    # eid,ename,email,desc,stime,etime,edate,location,category in edetailslist
    c.execute("SELECT * FROM eventdetail")
    edetailslist = c.fetchall()
    treeplant, blooddonate, cleandrive = [], [], []
    for x in edetailslist:
        if x['category'] == 'Tree Plantation':
            treeplant.append(x)
        elif x['category'] == 'Blood Donation':
            blooddonate.append(x)
        else:
            cleandrive.append(x)
    return render_template("index3.html", edetailslist=edetailslist, treeplantation=treeplant, blooddonation=blooddonate, cleanlinesdrive=cleandrive)

@app.route("/addevent", methods=["GET", "POST"])
@sqldb
def addevent(c):
    if request.method == "POST":
        field = ["eventname", "email", "starttime", "endtime", "eventdate", "location", "category", "description", "username"] 
        event_values = [request.form.get(y) for y in field]
        check = c.execute("SELECT * FROM eventdetail WHERE eventname=(?)", (event_values[0],))
        fetchall = check.fetchall()
        zipped = zip(field, event_values)
        for ab in fetchall:
                if all(ab[x] == y for x,y in zipped):
                    return "Event Already Exists"
        tuple_all, tuple_event_values = ", ".join(field), tuple(event_values)
        vals = ", ".join(["?"] * len(event_values))
        c.execute(f"INSERT INTO eventdetail({tuple_all}) VALUES ({vals})", tuple_event_values)
        return "Event Registered ✅. Kindly wait for approval!"

@app.route("/addeventreq", methods=["GET", "POST"])
@sqldb
def addeventreq(c):
    if request.method == "POST":
        field = ["eventname", "email", "starttime", "endtime", "eventdate", "location", "category", "description", "username"] 
        event_values = [request.form.get(y) for y in field]
        check = c.execute("SELECT * FROM eventdetail WHERE eventname=(?)", (event_values[0],))
        fetchall = check.fetchall()
        zipped = zip(field, event_values)
        for ab in fetchall:
                if all(ab[x] == y for x,y in zipped):
                    return "Event Already Exists"
        tuple_all, tuple_event_values = ", ".join(field), tuple(event_values)
        vals = ", ".join(["?"] * len(event_values))
        c.execute(f"INSERT INTO eventdetail({tuple_all}) VALUES ({vals})", tuple_event_values)
        return "Event Registered ✅. Kindly wait for approval!"

@app.route("/pendingevents", methods=["GET", "POST"])
@sqldb
def approveevent(c, eventid):
    if session.get("username") == "dipanshuag19":
        return f"ok, event ID {eventid}"
    else:
        return f"not ok, event ID {eventid}"

        

@app.route("/deleteevent", methods=["GET", "POST"])
@sqldb
def deleteevent(c):
    if request.method == "POST":
        event_id = request.form.get("eventid")
        try:
            c.execute("DELETE FROM eventdetail WHERE eventid=(?)", event_id)
            return redirect(url_for("home"))
        except Exception as e:
            return f"Error: {e}"
    html_code = """<html><head><title>Delete event</title></head>
    <body><form onsubmit='/deleteevent' method='POST'>
    Enter event id to delete: <input type='number' name='eventid'><br><br> <button type='submit'>Delete Event</button></body></html>
    """
    return render_template_string(html_code)
        
