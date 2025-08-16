from flask import Flask, request, redirect, url_for, render_template, render_template_string, flash, session, jsonify
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
    print("DEBUG session:", dict(session))

    user = ""
    if not session.get('name'):
        currentuser = "User"
    else:
        currentuser = session["name"]
    currentuname = session.get("username")
    print("Welcome", currentuser)
    query = c.execute("SELECT * FROM eventdetail")
    edetailslist = c.fetchall()
    treeplant, blooddonate, cleandrive = [], [], []
    for x in edetailslist:
        if x['category'] == 'Tree Plantation':
            treeplant.append(x)
        elif x['category'] == 'Blood Donation':
            blooddonate.append(x)
        else:
            cleandrive.append(x)
    fv = []
    fi = ["eventname", "email", "starttime", "endtime", "eventdate", "location", "category", "description"]
    for x in fi:
        fv.append(session.get(x, ""))
    isadmin = False
    if currentuname:
        ud = c.execute("SELECT * FROM userdetails WHERE username=?", (currentuname, )).fetchone()
        if ud and ud["role"] == "admin":
            isadmin = True

    if request.args.get("api"):
        return jsonify({"user": currentuser, "username": currentuname, "is_admin": isadmin, "events": [dict(r) for r in edetailslist], "favorites": fv})
    return render_template("index.html",treeplantation=treeplant, blooddonation=blooddonate, cleanlinesdrive=cleandrive, fullname=currentuser, fvalues=fv, c_user=str(currentuname).strip(), isadmin=bool(isadmin))

@app.route("/signup", methods=["GET", "POST"])
@sqldb
def signup(c):
    if request.method == "POST":
        username = request.form.get("username").lower()
        password = request.form.get("password")
        cpassword = request.form.get("cpassword")
        name = request.form.get("nameofuser")
        c.execute("SELECT * FROM userdetails where username=?", (username,))
        if c.fetchone():
            if request.args.get("api"):
                return jsonify({"error": "User already exists"})
            return render_template("signup.html", alreadyexists=True, password=password, username=username)
        elif password != cpassword:
            if request.args.get("api"):
                return jsonify({"error": "Passwords do not match"})
            return render_template("signup.html", wrongpass=True, password=password, username=username)
        else:
            c.execute("INSERT INTO userdetails(username, password, name) VALUES(?, ?, ?)", (username, password, name))
            session.permanent = True
            session["username"] = username
            session["name"] = name
            print("DEBUG after singup:", dict(session))
            if request.args.get("api"):
                return jsonify({"success": True, "username": username, "name": name})
            return redirect(url_for("home"))
    if request.args.get("api"):
        return jsonify({"form": "signup"})
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
@sqldb
def login(c):
    if request.method == "POST":
        username = request.form.get("loginusername").lower()
        password = request.form.get("loginpassword")
        c.execute("SELECT * FROM userdetails where username=?", (username,))
        fetched = c.fetchone()
        if not fetched:
            if request.args.get("api"):
                return jsonify({"error": "User does not exist"})
            return render_template("signup.html", usernotexists=True, username=username)
        elif password != fetched["password"]:
            if request.args.get("api"):
                return jsonify({"error": "Wrong password"})
            return render_template("signup.html", loginwrongpass=True, loginuname=username)
        else:
            session.permanent = True
            session["username"] = fetched["username"]
            session["name"] = fetched["name"]
            print("DEBUG after login:", dict(session))
            if request.args.get("api"):
                return jsonify({"success": True, "username": fetched["username"], "name": fetched["name"]})
            return redirect(url_for("home"))
    if request.args.get("api"):
        return jsonify({"form": "login"})
    return render_template("signup.html")
        
@app.route("/index2")
@sqldb
def home2(c):
    mylist = []
    for row in c.execute("SELECT * FROM eventdetail"):
        mylist.append(f"ID: {row[0]} Name: {row[1]}")
    if request.args.get("api"):
        return jsonify({"mylist": mylist})
    return render_template("index2.html", mylist=mylist)

@app.route("/index3")
@sqldb
def home3(c):
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
    if request.args.get("api"):
        return jsonify({"events": [dict(r) for r in edetailslist]})
    return render_template("index3.html", edetailslist=edetailslist, treeplantation=treeplant, blooddonation=blooddonate, cleanlinesdrive=cleandrive)

@app.route("/addevent", methods=["GET", "POST"])
@sqldb
def addevent(c):
    if request.method == "POST":
        field = ["eventname", "email", "starttime", "endtime", "eventdate", "location", "category", "description", "username"] 
        event_values = [request.form.get(y) for y in field]
        check = c.execute("SELECT * FROM eventdetail WHERE eventname=(?)", (event_values[0],))
        fetchall = check.fetchall()
        for ab in fetchall:
            if all(ab[x] == y for x,y in zip(field, event_values)):
                if request.args.get("api"):
                    return jsonify({"error": "Event Already Exists"})
                return "Event Already Exists"
        tuple_all, tuple_event_values = ", ".join(field), tuple(event_values)
        vals = ", ".join(["?"] * len(event_values))
        c.execute(f"INSERT INTO eventdetail({tuple_all}) VALUES ({vals})", tuple_event_values)
        lastid = c.execute("SELECT eventid FROM eventdetail ORDER BY eventid DESC LIMIT 1").fetchone()
        c.execute("DELETE FROM eventreq WHERE eventid=(?)", lastid)
        uud = c.execute("SELECT events FROM userdetails WHERE username=?", (field[-1], )).fetchone()
        if not uud or not uud["events"]:
            fe = []
        else:
            fe = uud["events"].split()
        fe.append(str(lastid["eventid"]))
        joint = " ".join(fe)
        c.execute("UPDATE userdetails SET events=? WHERE username=?", (joint, event_values[-1]))
        checkleft = c.execute("SELECT * FROM eventreq")
        if checkleft.fetchone():
            if request.args.get("api"):
                return jsonify({"redirect": "pendingevents"})
            return redirect(url_for("pendingevents"))
        else:
            if request.args.get("api"):
                return jsonify({"redirect": "home"})
            return redirect(url_for("home"))
    if request.args.get("api"):
        return jsonify({"form": "addevent"})
    return render_template("addevent.html")

@app.route("/addeventreq", methods=["GET", "POST"])
@sqldb
def addeventreq(c):
    if request.method == "POST":
        uuname = session.get("username")
        field = ["eventname", "email", "starttime", "endtime", "eventdate", "location", "category", "description", "username"] 
        event_values = [request.form.get(y) for y in field]
        event_values[-1] = uuname
        check = c.execute("SELECT * FROM eventdetail WHERE eventname=(?)", (event_values[0],))
        fetchall = check.fetchall()
        for ab in fetchall:
            if all(ab[x] == y for x,y in zip(field, event_values)):
                if request.args.get("api"):
                    return jsonify({"error": "Event Already Exists"})
                return "Event Already Exists"
        fetchall2 = c.execute("SELECT * FROM eventreq WHERE eventname=(?)", (event_values[0],)).fetchall()
        for ab in fetchall2:
            if all(ab[x] == y for x,y in zip(field, event_values)):
                if request.args.get("api"):
                    return jsonify({"error": "Event Already Submitted"})
                return "Event Already Submitted! Please Wait For Approval"
        efields = ", ".join(field)
        vals = ", ".join(["?"] * len(event_values))
        if not uuname:
            if request.args.get("api"):
                return jsonify({"error": "Please Login First To Add Event."})
            return "Please Login First To Add Event."
        c.execute(f"INSERT INTO eventreq({efields}) VALUES ({vals})", tuple(event_values))
        for x in field:
            if x != "username":
                session.pop(x)
        if request.args.get("api"):
            return jsonify({"success": True})
        return "Event Registered ✅. Kindly wait for approval!"
    if request.args.get("api"):
        return jsonify({"form": "addeventreq"})
    return render_template("addeventreq.html")

@app.route("/pendingevents", methods=["GET", "POST"])
@sqldb
def pendingevents(c):
    uname = session.get("username")
    if not uname:
        if request.args.get("api"):
            return jsonify({"error": "Login First"})
        return "Login First"
    f = c.execute("SELECT * FROM userdetails WHERE username=?", (uname, )).fetchone()
    if f["role"] == "admin":
        c.execute("SELECT * FROM eventreq")
        allpending = c.fetchall()
        if not allpending:
            if request.args.get("api"):
                return jsonify({"message": "No Events Pending"})
            return "No Events Pending For Approval"
        if request.args.get("api"):
            return jsonify({"pending": [dict(r) for r in allpending]})
        return render_template("pendingevents.html", pendingevents=allpending)
    else:
        if request.args.get("api"):
            return jsonify({"redirect": "home"})
        return redirect(url_for("home"))

@app.route("/deleteevent/<int:eventid>")
@sqldb
def deleteevent(c, eventid):
    uname = session.get("username")
    if not uname:
        if request.args.get("api"):
            return jsonify({"error": "Login First"})
        return "Login First"
    c.execute("SELECT * FROM eventdetail WHERE eventid=?", (eventid,))
    fe = c.fetchone()
    c.execute("SELECT * FROM userdetails WHERE username=?", (uname,))
    fe2 = c.fetchone()
    if fe["username"] == uname or fe2["role"]=="admin":
        try:
            c.execute("DELETE FROM eventdetail WHERE eventid=(?)", (eventid,))
            ok = c.execute("SELECT events FROM userdetails WHERE username=?", (uname, )).fetchone()
            ev = ok["events"].split(" ")
            if str(eventid) in ev:
                ev.remove(str(eventid))
                repl = " ".join(ev)
                c.execute("UPDATE userdetails SET events=? WHERE username=?", (repl, uname))
            if request.args.get("api"):
                return jsonify({"success": True})
            return redirect(url_for("home"))
        except Exception as e:
            if request.args.get("api"):
                return jsonify({"error": str(e)})
            return f"Error: {e}"
    else:
        if request.args.get("api"):
            return jsonify({"redirect": "home"})
        return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.pop('username')
    session.pop('name')
    if request.args.get("api"):
        return jsonify({"success": True})
    return redirect(url_for("home"))

@app.route("/save_draft", methods=["POST"])
def save_draft():
    field = request.form.get("field")
    value = request.form.get("value")
    if value and value.strip():
        session.permanent = True
        session[field] = value.strip()
    if request.args.get("api"):
        return jsonify({"draft_saved": True, "field": field, "value": value})
    return "DRAFT"

@app.route("/decline_event/<int:eventid>")
@sqldb
def decline_event(c, eventid):
    u = session.get("username")
    if u:
        c.execute("SELECT * FROM userdetails WHERE username=?", (u, ))
        f = c.fetchone()
        if f["role"] == "admin":
            c.execute("DELETE FROM eventreq WHERE eventid=?", (eventid, ))
            seq = c.execute("SELECT * FROM sqlite_sequence WHERE name=?", ("eventreq",)).fetchone()
            c.execute("UPDATE sqlite_sequence SET seq=? WHERE name=?", (seq["seq"], "eventdetail"))
    if c.execute("SELECT eventid FROM eventreq").fetchone():
        if request.args.get("api"):
            return jsonify({"redirect": "pendingevents"})
        return redirect(url_for("pendingevents"))
    else:
        if request.args.get("api"):
            return jsonify({"redirect": "home"})
        return redirect(url_for("home"))
        
@app.route("/clearsession")
def clearsession():
    session.clear()
    if request.args.get("api"):
        return jsonify({"cleared": True})
    return redirect(url_for("home"))
