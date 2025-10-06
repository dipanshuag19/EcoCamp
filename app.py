from flask import Flask, request, redirect, url_for, render_template, render_template_string, flash, session, jsonify
#import sqlite3 as sq
import os, requests, datetime, time, threading, zoneinfo, random
import sqlitecloud as sq
from functools import wraps

app = Flask(__name__)
app.secret_key = "ecocamp.fp"
ist = zoneinfo.ZoneInfo("Asia/Kolkata")

def sendlog(message):
    link = f"https://api.telegram.org/bot{os.environ.get('TGBOTTOKEN')}/sendMessage"
    parameters = {"chat_id": "-1002945250812", "text": f'ㅤㅤㅤ\n🗓️ {datetime.datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")}\n{message}\nㅤㅤㅤ'}
    requests.get(link, params=parameters)

def sendmail(receiver, subject, message):
    import smtplib, ssl, random
    sender = "dipanshuashokagarwal@gmail.com"
    password = os.environ.get("MAIL_APP_PASS")
    context = ssl.create_default_context()
    msg = f"Subject: {subject}\n\n{message}"
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, receiver, msg)
        sendlog(f"Email sent to {receiver}")

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

def del_event(c, eventid):
    try:
        edetail = c.execute("SELECT * FROM eventdetail WHERE eventid=?", (eventid,)).fetchone()
        details = c.execute("SELECT * FROM userdetails WHERE username=?", (edetail["username"],)).fetchone()
        c.execute("DELETE FROM eventdetail where eventid=?", (eventid,))
        events = details["events"].split(",")
        if str(eventid) in events:
            events.remove(str(eventid))
            new = ",".join(events)
            if events == []:
                c.execute("UPDATE userdetails SET events=NULL WHERE username=?", (details["username"], ))
            else:
                c.execute("UPDATE userdetails SET events=? WHERE username=?", (new, details["username"]))
    except Exception as e:
        sendlog(f"Error Deleting Event {eventid}: {e}")
        print(f"Error Deleting Event {eventid}: {e}")

@app.route("/sendsignupotp", methods=["POST", "GET"])
@sqldb
def sendotp(c):
    if request.method == "POST":
        otp = random.randint(1111,9999)
        session.permanent = True
        session["signupotp"] = otp
        email = request.form.get("email")
        checkexists = c.execute("SELECT * FROM userdetails where email=?", (email,)).fetchone()
        if checkexists:
            return "Email already exists! Please try different email."
        sendmail(email, "Signup OTP", f"Your signup OTP is {otp}.")
        print(f"Session OTP: {session.get('signupotp')}")
        print(f"Generated OTP: {otp}")
        return f"OTP Sent to {email}! Please check spam folder if cant find it."
    
@app.template_filter("datetimeformat")
def datetimeformat(value):
    return datetime.datetime.strptime(value, "%Y-%m-%d").strftime("%d %B %Y")

def detailsformat(details):
    id = details["eventid"]
    name = details["eventname"]
    email = details["email"]
    stime = details["starttime"]
    etime = details["endtime"]
    edate = details["eventdate"]
    enddate = details["enddate"]
    location = details["location"]
    category = details["category"]
    description = details["description"]
    username = details["username"]
    text = f"Event ID: {id}\nEvent Name: {name}\nEmail: {email}\nStart Time: {stime}\nEnd Time: {etime}\nEvent Date: {edate}\nEnd Date: {enddate}\nLocation: {location}\nCategory: {category}\nDescription: {description}\nUsername: {username}"
    return text

@app.route("/")
@sqldb
def home(c):
    user = ""
    currentuser = session.get("name", "User")
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
    fv = {}
    fi = ["eventname", "email", "starttime", "endtime", "eventdate", "enddate", "location", "category", "description"]
    for x in fi:
        fv[x] = session.get(x, "")
    isadmin = False
    userdetails = {}
    if currentuname:
        ud = c.execute("SELECT * FROM userdetails WHERE username=?", (currentuname, )).fetchone()
        if ud and ud["role"] == "admin":
            isadmin = True
        userdetails = ud if ud else {}
    ve = session.pop("viewyourevents", False)
    sortby = session.get("sortby", "eventdate")
    pendingevents = c.execute("SELECT * FROM eventreq").fetchall()
    if not pendingevents:
        pendingevents = []
    return render_template("index.html", pendingevents=pendingevents, sortby=sortby, viewyourevents=ve ,edetailslist=edetailslist, treeplantation=treeplant, blooddonation=blooddonate, cleanlinesdrive=cleandrive, fullname=currentuser, fvalues=fv, c_user=str(currentuname).strip(), isadmin=bool(isadmin), userdetails=userdetails)

@app.route("/viewyourevents", methods=["GET", "POST"])
def viewyourevents():
    if request.method == "POST":
        if session.get("username"):
            session["viewyourevents"] = True
            return "View your events"

@app.route("/setsortby/<path:sortby>", methods=["GET", "POST"])
def setsortby(sortby):
    if request.method == "POST":
        session["sortby"] = sortby
        return "Sort by set"
        
@app.route("/signup", methods=["GET", "POST"])
@sqldb
def signup(c):
    if request.method == "POST":
        username = request.form.get("username").lower()
        password = request.form.get("password")
        cpassword = request.form.get("cpassword")
        name = request.form.get("nameofuser")
        email = request.form.get("email")
        otp = request.form.get("signupotp")
        c.execute("SELECT * FROM userdetails where username=?", (username,))
        if c.fetchone():
            return "Username Already Exists"
        if c.execute("SELECT * FROM userdetails where email=?", (email,)).fetchone():
            return "Email Already Exists"
        if str(session.get("signupotp")) != str(otp).strip():
            return "Wrong Signup OTP"
        elif password != cpassword:
            return "Wrong Confirm Password"
        elif len(password) < 8:
            return "Password must be at least 8 characters long"
        else:
            c.execute("INSERT INTO userdetails(username, password, name, email) VALUES(?, ?, ?, ?)", (username, password, name, email))
            session.permanent = True
            session["username"] = username
            session["name"] = name
            session["email"] = email
            session.pop("signupotp", None)
            sendlog(f"New Signup: {name} ({username})")
            return "Signup Success ✅"

@app.route("/login", methods=["GET", "POST"])
@sqldb
def login(c):
    if request.method == "POST":
        username = request.form.get("loginusername").lower()
        password = request.form.get("loginpassword")
        c.execute("SELECT * FROM userdetails where username=? or email=?", (username, username))
        fetched = c.fetchone()
        if not fetched:
            return "No username found"
        elif password != fetched["password"]:
            return "Wrong Password"
        else:
            session.permanent = True
            session["username"] = fetched["username"]
            session["name"] = fetched["name"]
            session["email"] = fetched["email"]
            sendlog(f"User Login: {fetched['name']} ({fetched['username']})")
            return "Login Success ✅"
        
@app.route("/addevent", methods=["GET", "POST"])
@sqldb
def addevent(c):
    if request.method == "POST":
        field = ["eventname", "email", "starttime", "endtime", "eventdate", "enddate", "location", "category", "description", "username"] 
        event_values = [request.form.get(y) for y in field]
        check = c.execute("SELECT * FROM eventdetail WHERE eventname=(?)", (event_values[0],))
        fetchall = check.fetchall()
        for ab in fetchall:
                if all(ab[x] == y for x,y in zip(field, event_values)):
                    return "Event Already Exists"
                    
        tuple_all, tuple_event_values = ", ".join(field), tuple(event_values)
        vals = ", ".join(["?"] * len(event_values))
        c.execute(f"INSERT INTO eventdetail({tuple_all}) VALUES ({vals})", tuple_event_values)
        lastid = c.execute("SELECT eventid FROM eventdetail ORDER BY eventid DESC LIMIT 1").fetchone()
        c.execute("DELETE FROM eventreq WHERE eventid=(?)", (lastid["eventid"], ))
        uud = c.execute("SELECT events FROM userdetails WHERE username=?", (event_values[-1], )).fetchone()
        if not uud or not uud["events"]:
            fe = []
        else:
            fe = uud["events"].split(",")
        fe.append(str(lastid["eventid"]))
        joint = ",".join(fe)
        c.execute("UPDATE userdetails SET events=? WHERE username=?", (joint, event_values[-1]))
        eventdetails = c.execute("SELECT * FROM eventdetail WHERE eventid=?", (lastid["eventid"], )).fetchone()
        details = detailsformat(eventdetails)
        sendmail(event_values[1], "Event Approved", f'Congragulations\n\nYour Event is approved and now visible on Campaigns Page.\n\nEvent Details:\n\n{details}\n\nThank You!')
        sendlog(f"#EventAdd \nNew Event Added:\n{details}")
        return redirect(url_for("home"))

@app.route("/addeventreq", methods=["GET", "POST"])
@sqldb
def addeventreq(c):
    if request.method == "POST":
        uuname, uemail = session.get("username"), session.get("email")
        field = ["eventname", "email", "starttime", "endtime", "eventdate", "enddate", "location", "category", "description", "username"] 
        event_values = [request.form.get(y) for y in field]
        event_values[-1], event_values[1] = uuname, uemail
        check = c.execute("SELECT * FROM eventdetail WHERE eventname=(?)", (event_values[0],))
        fetchall = check.fetchall()
        for ab in fetchall:
                if all(ab[x] == y for x,y in zip(field, event_values)):
                    return "Event Already Exists"
                    
        fetchall2 = c.execute("SELECT * FROM eventreq WHERE eventname=(?)", (event_values[0],)).fetchall()
        for ab in fetchall2:
                if all(ab[x] == y for x,y in zip(field, event_values)):
                    return "Event Already Submitted! Please Wait For Approval"

        efields = ", ".join(field)
        vals = ", ".join(["?"] * len(event_values))
        if not uuname:
            return "Please Login First To Add Event."
        c.execute(f"INSERT INTO eventreq({efields}) VALUES ({vals})", tuple(event_values))
        for x in field:
            if x not in ("email", "username"):
                session.pop(x, None)
        sendlog(f"#EventRequst \nNew Event Request: {event_values} by {uuname}")
        return "Event Registered ✅. Kindly wait for approval!"

# @app.route("/pendingevents", methods=["GET", "POST"])
# @sqldb
# def pendingevents(c):
#     uname = session.get("username")
#     if not uname:
#         return "Login First"
#     f = c.execute("SELECT * FROM userdetails WHERE username=?", (uname, )).fetchone()
#     if f["role"] == "admin":
#         c.execute("SELECT * FROM eventreq")
#         allpending = c.fetchall()
#         return render_template("pendingevents.html", pendingevents=allpending)
#     else:
#         return redirect(url_for("home"))

@app.route("/deleteevent/<int:eventid>")
@sqldb
def deleteevent(c, eventid):
    uname = session.get("username")
    if not uname:
        return "Login First"
    c.execute("SELECT * FROM eventdetail WHERE eventid=?", (eventid,))
    fe = c.fetchone()
    extra = c.execute("SELECT * FROM userdetails WHERE username=?", (fe["username"], )).fetchone()
    c.execute("SELECT * FROM userdetails WHERE username=?", (uname,))
    fe2 = c.fetchone()
    if fe["username"] == uname or fe2["role"]=="admin":
        try:
            del_event(c, eventid)
            details = detailsformat(fe)
            sendmail(extra["email"], "Event Deleted", f"Hey {extra['name']}! Your event was deleted by {uname}.\n\nEvent Details:\n\n{details}\n\nThank You!")
            sendlog(f"#EventDelete \nEvent Deleted by {uname}.\nEvent Details:\n\n{details}")
            return redirect(url_for("home"))
        except Exception as e:
            sendlog(f"Error Deleting Event {eventid}: {e}")
            return f"Error: {e}"
    else:
        return redirect(url_for("home"))

@app.route("/logout")
def logout():
    u = session.pop('username')
    n = session.pop('name')
    e = session.pop('email')
    sendlog(f"User Logout: {n} ({u}) {e}")
    return redirect(url_for("home"))

@app.route("/save_draft", methods=["POST"])
def save_draft():
    field = request.form.get("field")
    value = request.form.get("value")
    if value and value.strip():
        session.permanent = True
        session[field] = value.strip()
    return "DRAFT"

@app.route("/decline_event/<int:eventid>/<path:reason>")
@sqldb
def decline_event(c, eventid, reason):
    u = session.get("username")
    if u:
        c.execute("SELECT * FROM userdetails WHERE username=?", (u, ))
        f = c.fetchone()
        if f["role"] == "admin":
            email = c.execute("SELECT * from eventreq WHERE eventid=?", (eventid, )).fetchone()
            c.execute("DELETE FROM eventreq WHERE eventid=?", (eventid, ))
            seq = c.execute("SELECT * FROM sqlite_sequence WHERE name=?", ("eventreq",)).fetchone()
            c.execute("UPDATE sqlite_sequence SET seq=? WHERE name=?", (seq["seq"], "eventdetail"))
            details = detailsformat(email)
            sendmail(email['email'], "Event Declined", f"We sorry to inform to you that your event was declined for following reason:\n{reason}.\n\nEvent Details:\n\n{details}\n\nThank You!")
            sendlog(f"#EventDecline \nEvent Declined by {u}\nReason: {reason}.\nEvent Details:\n\n{details}")
            
    if c.execute("SELECT eventid FROM eventreq").fetchone():
        return redirect(url_for("pendingevents"))
    else:
        return redirect(url_for("home"))
        
@app.route("/clearsession")
def clearsession():
    c = session.clear()
    sendlog(f"Session Cleared {c}")
    return redirect(url_for("home"))

@app.route("/api")
@sqldb
def api(c):
    events = [dict(row) for row in c.execute("SELECT * FROM eventdetail").fetchall()]
    user = dict(session)
    user_details = "No user logged in"
    if user.get("username"):
        user_details = c.execute("SELECT * FROM userdetails WHERE username=?", (user["username"],)).fetchone()
        user_details = dict(user_details)
    toreturn = {"active events": events, "current session including draft add event values": user, "current user": user_details}
    return jsonify(toreturn)

@app.route("/checkeventloop")
@sqldb
def checkevent(c):
        ch = c.execute("SELECT * FROM eventdetail").fetchall()
        ist = zoneinfo.ZoneInfo("Asia/Kolkata")
        for x in ch:
            etime = datetime.datetime.strptime(f"{x['enddate']} {x['endtime']}", "%Y-%m-%d %H:%M").replace(tzinfo=ist)
            if etime <= datetime.datetime.now(ist):
                del_event(c, x["eventid"])
                details = detailsformat(x)
                sendmail(x["username"], "Event Ended", f"Hey there your event was ended, so it has been deleted!\n\nEvent Details:\n\n{details}\n\nThank You!")
                sendlog(f"#EventEnd \nEvent Ended at {etime.strftime('%Y-%m-%d %H:%M:%S')}.\nEvent Details:\n\n{details}")
        return "<h1>CHECK EVENT LOOP COMPLETED</h1>"

# @app.route("/checkeventloop")
# def checkeventloop():
#     checkevent()
#     return "CHECK EVENT LOOP COMPLETED"
    
# if __name__ == "__main__":
# #     # threading.Thread(target=checkeventloop, name="CheckEventExist", daemon=True).start()
#     app.run(debug=True, port=8000)
