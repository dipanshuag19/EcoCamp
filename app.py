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
        session.permanent = True # Flask permanent session dont remove
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

@app.route("/signup", methods=["GET", "POST"])
@sqldb
def signup(c):
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        cpassword = request.form.get("cpassword")
        name = request.form.get("nameofuser")
        c.execute("SELECT * FROM userdetails where username=?", (username,))
        if c.fetchone():
            return render_template("signup.html", alreadyexists=True, password=password, username=username)
        elif password != cpassword:
            return render_template("signup.html", wrongpass=True, password=password, username=username)
        else:
            c.execute("INSERT INTO userdetails(username, password, name) VALUES(?, ?, ?)", (username, password, name))
            session["username"] = username
            session["name"] = name
            return redirect(url_for("home"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
@sqldb
def login(c):
    if request.method == "POST":
        username = request.form.get("loginusername")
        password = request.form.get("loginpassword")
        c.execute("SELECT * FROM userdetails where username=?", (username,))
        fetched = c.fetchone()
        if not fetched:
            return render_template("signup.html", usernotexists=True)
        elif password != fetched["password"]:
            return render_template("signup.html", loginwrongpass=True, username=username)
        else:
            session["username"] = username
            session["name"] = fetched["name"]
            return redirect(url_for("home"))
    return render_template("signup.html")
        
@app.route("/index2")
@sqldb
def home2(c):
    user = ""
    if not session.get('name'):
        currentuser = "User"
    else:
        currentuser = session["name"]
    print("Welcome", user)
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
    return render_template("index2.html", edetailslist=edetailslist, treeplantation=treeplant, blooddonation=blooddonate, cleanlinesdrive=cleandrive, fullname=currentuser)

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
        lastid = c.execute("SELECT eventid from eventdetail ORDER BY eventid DESC LIMIT 1").fetchone()
        c.execute("DELETE FROM eventreq WHERE eventid=(?)", lastid)
        checkleft = c.execute("SELECT * FROM eventreq")
        if checkleft.fetchall():
            return redirect(url_for("pendingevents"))
        else:
            return redirect(url_for("home"))

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
                    
        fetchall2 = c.execute("SELECT * FROM eventreq WHERE eventname=(?)", (event_values[0],)).fetchall()
        for ab in fetchall2:
                if all(ab[x] == y for x,y in zipped):
                    return "Event Already Submitted! Please Wait For Approval"
                    
        tuple_all, tuple_event_values = ", ".join(field), tuple(event_values)
        vals = ", ".join(["?"] * len(event_values))
        c.execute(f"INSERT INTO eventreq({tuple_all}) VALUES ({vals})", tuple_event_values)
        return "Event Registered ✅. Kindly wait for approval!"

@app.route("/pendingevents", methods=["GET", "POST"])
@sqldb
def pendingevents(c):
    c.execute("SELECT * FROM eventreq")
    allpending = c.fetchall()
    if not allpending:
        return "No Events Pending For Approval"
    return render_template("pendingevents.html", pendingevents=allpending)
        

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
        
