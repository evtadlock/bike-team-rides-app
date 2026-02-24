import sqlite3
import os
import uuid

DB = "data/teamugly.sqlite"


def connect():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB)


def init_db():
    con = connect()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rides(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_name TEXT,
            ride_date TEXT,
            start_time TEXT,
            meeting_point TEXT,
            route_link TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS signups(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id INTEGER,
            full_name TEXT,
            confirm_code TEXT
        )
    """)
    con.commit()
    con.close()


# ---------- RIDES ----------

def create_ride(name, date, time, loc, route):
    con = connect()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO rides
        (ride_name, ride_date, start_time, meeting_point, route_link)
        VALUES (?,?,?,?,?)
    """, (name, date, time, loc, route))
    con.commit()
    con.close()


def list_rides():
    con = connect()
    cur = con.cursor()
    rows = cur.execute("""
        SELECT id, ride_name, ride_date
        FROM rides
        ORDER BY ride_date
    """).fetchall()
    con.close()
    return rows


def get_ride_details(ride_id):
    con = connect()
    cur = con.cursor()
    row = cur.execute("""
        SELECT ride_name, ride_date, start_time,
               meeting_point, route_link
        FROM rides
        WHERE id=?
    """, (ride_id,)).fetchone()
    con.close()
    return row


def delete_ride(ride_id):
    con = connect()
    cur = con.cursor()
    cur.execute("DELETE FROM signups WHERE ride_id=?", (ride_id,))
    cur.execute("DELETE FROM rides WHERE id=?", (ride_id,))
    con.commit()
    con.close()


# ---------- SIGNUP ----------

def signup(ride_id, full_name):
    code = str(uuid.uuid4())[:8].upper()
    con = connect()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO signups
        (ride_id, full_name, confirm_code)
        VALUES (?,?,?)
    """, (ride_id, full_name, code))
    con.commit()
    con.close()
    return code


def cancel_signup(code):
    con = connect()
    cur = con.cursor()
    cur.execute("""
        DELETE FROM signups
        WHERE confirm_code=?
    """, (code,))
    removed = cur.rowcount
    con.commit()
    con.close()
    return removed


def roster():
    con = connect()
    cur = con.cursor()
    rows = cur.execute("""
        SELECT r.ride_name,
               r.ride_date,
               s.full_name
        FROM signups s
        JOIN rides r
        ON s.ride_id = r.id
        ORDER BY r.ride_date
    """).fetchall()
    con.close()
    return rows