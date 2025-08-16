from flask import Flask, request, redirect, url_for, render_template, jsonify, session
import os, uuid
import sqlitecloud as sq
from functools import wraps

app = Flask(__name__)
app.secret_key = "ecocamp.fp"

def sqldb(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        session.permanent = True
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
    user = ""
    currentuser = session.get("name", "User")
    currentuname = session.get("username")
    query = c.execute("SELECT * FROM eventdetail")
    edetailslist = c.fetchall()
    treeplant = [x for x in edetailslist if x['category']=="Tree Plantation"]
    blooddonate = [x for x in edetailslist if x['category']=="Blood Donation"]
    cleandrive = [x for x in edetailslist if x['category'] not in ("Tree Plantation","Blood Donation")]
    fv = [session.get(x, "") for x in ["eventname", "email", "starttime", "endtime", "eventdate", "location", "category", "description"]]
    isadmin = False
    if currentuname:
        ud = c.execute("SELECT * FROM userdetails WHERE username=?", (currentuname,)).fetchone()
        if ud and ud["role"]=="admin": isadmin=True
    if request.args.get("api"):
        return jsonify({"user": currentuser, "username": currentuname, "is_admin": isadmin, "events": edetailslist, "favorites": fv})
    return render_template("index.html", treeplantation=treeplant, blooddonation=blooddonate, cleanlinesdrive=cleandrive, fullname=currentuser, fvalues=fv, c_user=str(currentuname).strip(), isadmin=bool(isadmin))

@app.route("/signup", methods=["GET","POST"])
@sqldb
def signup(c):
    if request.method=="POST":
        username=request.form.get("username").lower()
        password=request.form.get("password")
        cpassword=request.form.get("cpassword")
        name=request.form.get("nameofuser")
        c.execute("SELECT * FROM userdetails where username=?",(username,))
        if c.fetchone():
            if request.args.get("api"):
                return jsonify({"error":"User Already Exists","username":username})
            return render_template("signup.html", alreadyexists=True, password=password, username=username)
        elif password!=cpassword:
            if request.args.get("api"):
                return jsonify({"error":"Password Mismatch","username":username})
            return render_template("signup.html", wrongpass=True, password=password, username=username)
        else:
            c.execute("INSERT INTO userdetails(username,password,name) VALUES(?,?,?)",(username,password,name))
            session["username"]=username; session["name"]=name
            if request.args.get("api"):
                return jsonify({"message":"Signup Success","username":username,"name":name})
            return redirect(url_for("home"))
    if request.args.get("api"):
        return jsonify({"form":"signup"})
    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
@sqldb
def login(c):
    if request.method=="POST":
        username=request.form.get("loginusername").lower()
        password=request.form.get("loginpassword")
        c.execute("SELECT * FROM userdetails where username=?",(username,))
        fetched=c.fetchone()
        if not fetched:
            if request.args.get("api"):
                return jsonify({"error":"User Not Exists","username":username})
            return render_template("signup.html", usernotexists=True, username=username)
        elif password!=fetched["password"]:
            if request.args.get("api"):
                return jsonify({"error":"Wrong Password","username":username})
            return render_template("signup.html", loginwrongpass=True, loginuname=username)
        else:
            session["username"]=fetched["username"]
            session["name"]=fetched["name"]
            if request.args.get("api"):
                return jsonify({"message":"Login Success","username":fetched["username"],"name":fetched["name"]})
            return redirect(url_for("home"))
    if request.args.get("api"):
        return jsonify({"form":"login"})
    return render_template("signup.html")

@app.route("/index2")
@sqldb
def home2(c):
    mylist=[f"ID:{row[0]} Name:{row[1]}" for row in c.execute("SELECT * FROM eventdetail")]
    if request.args.get("api"):
        return jsonify({"mylist":mylist})
    return render_template("index2.html", mylist=mylist)

@app.route("/index3")
@sqldb
def home3(c):
    edetailslist=c.execute("SELECT * FROM eventdetail").fetchall()
    treeplant=[x for x in edetailslist if x['category']=="Tree Plantation"]
    blooddonate=[x for x in edetailslist if x['category']=="Blood Donation"]
    cleandrive=[x for x in edetailslist if x['category'] not in ("Tree Plantation","Blood Donation")]
    if request.args.get("api"):
        return jsonify({"events":edetailslist,"treeplantation":treeplant,"blooddonation":blooddonate,"cleandrive":cleandrive})
    return render_template("index3.html", edetailslist=edetailslist, treeplantation=treeplant, blooddonation=blooddonate, cleanlinesdrive=cleandrive)

@app.route("/addevent", methods=["GET","POST"])
@sqldb
def addevent(c):
    if request.method=="POST":
        field=["eventname","email","starttime","endtime","eventdate","location","category","description","username"]
        event_values=[request.form.get(y) for y in field]
        check=c.execute("SELECT * FROM eventdetail WHERE eventname=?",(event_values[0],))
        for ab in check.fetchall():
            if all(ab[x]==y for x,y in zip(field,event_values)):
                if request.args.get("api"):
                    return jsonify({"error":"Event Already Exists","event":event_values})
                return "Event Already Exists"
        c.execute(f"INSERT INTO eventdetail({', '.join(field)}) VALUES ({', '.join(['?']*len(event_values))})",tuple(event_values))
        lastid=c.execute("SELECT eventid FROM eventdetail ORDER BY eventid DESC LIMIT 1").fetchone()
        c.execute("DELETE FROM eventreq WHERE eventid=?",(lastid["eventid"],))
        uud=c.execute("SELECT events FROM userdetails WHERE username=?",(event_values[-1],)).fetchone()
        fe=[] if not uud or not uud["events"] else uud["events"].split()
        fe.append(str(lastid["eventid"]))
        c.execute("UPDATE userdetails SET events=? WHERE username=?",(" ".join(fe),event_values[-1]))
        if request.args.get("api"):
            return jsonify({"message":"Event Added","eventid":lastid["eventid"],"event":event_values})
        if c.execute("SELECT * FROM eventreq").fetchone():
            return redirect(url_for("pendingevents"))
        else:
            return redirect(url_for("home"))
    if request.args.get("api"):
        return jsonify({"form":"addevent"})
    return render_template("addevent.html")

@app.route("/addeventreq", methods=["GET","POST"])
@sqldb
def addeventreq(c):
    if request.method=="POST":
        uuname=session.get("username")
        field=["eventname","email","starttime","endtime","eventdate","location","category","description","username"]
        event_values=[request.form.get(y) for y in field]
        event_values[-1]=uuname
        if not uuname:
            if request.args.get("api"):
                return jsonify({"error":"Login Required"})
            return "Please Login First To Add Event."
        check=c.execute("SELECT * FROM eventdetail WHERE eventname=?",(event_values[0],)).fetchall()
        for ab in check:
            if all(ab[x]==y for x,y in zip(field,event_values)):
                if request.args.get("api"):
                    return jsonify({"error":"Event Already Exists"})
                return "Event Already Exists"
        check2=c.execute("SELECT * FROM eventreq WHERE eventname=?",(event_values[0],)).fetchall()
        for ab in check2:
            if all(ab[x]==y for x,y in zip(field,event_values)):
                if request.args.get("api"):
                    return jsonify({"error":"Event Already Submitted"})
                return "Event Already Submitted! Please Wait For Approval"
        c.execute(f"INSERT INTO eventreq({', '.join(field)}) VALUES ({', '.join(['?']*len(event_values))})",tuple(event_values))
        for x in field:
            if x!="username": session.pop(x,None)
        if request.args.get("api"):
            return jsonify({"message":"Event Requested","event":event_values})
        return "Event Registered ✅. Kindly wait for approval!"
    if request.args.get("api"):
        return jsonify({"form":"addeventreq"})
    return render_template("addeventreq.html")

@app.route("/pendingevents", methods=["GET","POST"])
@sqldb
def pendingevents(c):
    uname=session.get("username")
    if not uname:
        if request.args.get("api"):
            return jsonify({"error":"Login Required"})
        return "Login First"
    f=c.execute("SELECT * FROM userdetails WHERE username=?",(uname,)).fetchone()
    if f["role"]=="admin":
        allpending=c.execute("SELECT * FROM eventreq").fetchall()
        if not allpending:
            if request.args.get("api"):
                return jsonify({"message":"No Events Pending"})
            return "No Events Pending For Approval"
        if request.args.get("api"):
            return jsonify({"pendingevents":allpending})
        return render_template("pendingevents.html", pendingevents=allpending)
    return redirect(url_for("home"))

@app.route("/deleteevent/<int:eventid>")
@sqldb
def deleteevent(c,eventid):
    uname=session.get("username")
    if not uname:
        if request.args.get("api"):
            return jsonify({"error":"Login Required"})
        return "Login First"
    fe=c.execute("SELECT * FROM eventdetail WHERE eventid=?",(eventid,)).fetchone()
    fe2=c.execute("SELECT * FROM userdetails WHERE username=?",(uname,)).fetchone()
    if fe["username"]==uname or fe2["role"]=="admin":
        c.execute("DELETE FROM eventdetail WHERE eventid=?",(eventid,))
        ok=c.execute("SELECT events FROM userdetails WHERE username=?",(uname,)).fetchone()
        ev=ok["events"].split(" ") if ok and ok["events"] else []
        if str(eventid) in ev:
            ev.remove(str(eventid))
            c.execute("UPDATE userdetails SET events=? WHERE username=?",(" ".join(ev),uname))
        if request.args.get("api"):
            return jsonify({"message":"Event Deleted","eventid":eventid})
        return redirect(url_for("home"))
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.pop("username",None)
    session.pop("name",None)
    if request.args.get("api"):
        return jsonify({"message":"Logged Out"})
    return redirect(url_for("home"))

@app.route("/save_draft", methods=["POST"])
def save_draft():
    field=request.form.get("field")
    value=request.form.get("value")
    if value and value.strip(): session[field]=value.strip()
    if request.args.get("api"):
        return jsonify({"message":"Draft Saved","field":field,"value":value})
    return "DRAFT"

@app.route("/decline_event/<int:eventid>")
@sqldb
def decline_event(c,eventid):
    u=session.get("username")
    if u:
        f=c.execute("SELECT * FROM userdetails WHERE username=?",(u,)).fetchone()
        if f["role"]=="admin":
            c.execute("DELETE FROM eventreq WHERE eventid=?",(eventid,))
    nextp=c.execute("SELECT eventid FROM eventreq").fetchone()
    if request.args.get("api"):
        return jsonify({"message":"Declined","eventid":eventid,"pending_exists":bool(nextp)})
    if nextp:
        return redirect(url_for("pendingevents"))
    else:
        return redirect(url_for("home"))

@app.route("/clearsession")
def clearsession():
    session.clear()
    if request.args.get("api"):
        return jsonify({"message":"Session Cleared"})
    return redirect(url_for("home"))
