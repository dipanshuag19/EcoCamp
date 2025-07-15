from flask import Flask, request, redirect, url_for, render_template, jsonify, render_template_engine
#import sqlite3 as sq
import os
import sqlitecloud as sq

app = Flask(__name__)
db = sq.connect(os.environ.get("SQLITECLOUD"))
c = db.cursor()

# Create table
c.execute("CREATE TABLE IF NOT EXISTS hi(id INT primary key, name VARCHAR(30))")

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
            return redirect(url_for("home"))
        return "Missing data or Wrong ID"
    return render_template("addevent.html")

@app.route("/deleteevent", methods=["GET", "POST"])
def deleteevent():
    if request.method == "POST":
        event_id = request.form.get("eventid")
        try:
            c.execute("DELETE FROM hi WHERE id=(?)", event_id))
            db.commit()
            return redirect(url_for("home")) 
        except Exception as e:
            return f"Error: {e}"
    html_code = """<html>
    <head><title>Delete event</title></head>
    <body>
    <form onsubmit='/deleteevent' method='POST'>
    Enter event id to delete: <input type='number' name='eventid'><br><br>
    <button type='submit'></button></body></html>
    """
    return render_template_engine(html_code)
        
