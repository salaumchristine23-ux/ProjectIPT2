import os, re, secrets, sqlite3, sys, functools
from datetime import datetime, timedelta, date
from flask import Flask, g, session, request, redirect, flash, render_template, abort
from jinja2 import DictLoader
from markupsafe import Markup
from werkzeug.security import generate_password_hash, check_password_hash
import db as D, sms
from pages import PAGES

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1", PERMANENT_SESSION_LIFETIME=timedelta(hours=8))
app.jinja_loader = DictLoader(PAGES)
app.jinja_env.globals["CSRF"] = lambda: Markup(f'<input type=hidden name=csrf value="{session.setdefault("csrf", secrets.token_hex(16))}">')
FMT = "%Y-%m-%d %H:%M"
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WDF = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MOBILE = re.compile(r"^(09|\+639)\d{9}$")
MOVES = {"Pending": {"Confirmed", "Cancelled"}, "Confirmed": {"Cancelled", "Completed", "No-Show"}}

def db():
    if "db" not in g: g.db = D.connect()
    return g.db
@app.teardown_appcontext
def close(_): 
    if "db" in g: g.db.close()
def q(sql, *a): return db().execute(sql, a).fetchall()
def q1(sql, *a): return db().execute(sql, a).fetchone()
def x(sql, *a):
    c = db().execute(sql, a); db().commit(); return c
def audit(action, detail=""): x("INSERT INTO audit_log(user_id,action,detail) VALUES(?,?,?)", session.get("uid"), action, detail)
def mobile(m):
    m = (m or "").strip()
    if not MOBILE.match(m): return None
    return "0" + m[3:] if m.startswith("+63") else m

def need(*roles):
    def deco(f):
        @functools.wraps(f)
        def w(*a, **k):
            if "uid" not in session: return redirect("/")
            if roles and session["role"] not in roles: abort(403)
            return f(*a, **k)
        return w
    return deco
@app.before_request
def csrf():
    if request.method == "POST" and not secrets.compare_digest(request.form.get("csrf", ""), session.get("csrf", "x")): abort(400)

# ---------- auth ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if "uid" in session: return redirect("/" + session["role"])
    if request.method == "POST":
        u = q1("SELECT * FROM users WHERE username=?", request.form.get("username", "").strip())
        if u and u["active"] and check_password_hash(u["password_hash"], request.form.get("password", "")):
            session.clear(); session.permanent = True
            session.update(uid=u["id"], role=u["role"], name=u["full_name"], csrf=secrets.token_hex(16))
            audit("login"); return redirect("/" + u["role"])       # identify role -> portal
        flash("Invalid username or password.", "error")
    return render_template("login.html")
@app.post("/logout")
def logout():
    audit("logout"); session.clear(); return redirect("/")
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = {k: request.form.get(k, "").strip() for k in ("full_name", "student_no", "program", "username", "mobile")}
        pw, m = request.form.get("password", ""), mobile(request.form.get("mobile"))
        if not all(f.values()) or len(pw) < 8 or not m: flash("Complete every field: valid mobile (09XXXXXXXXX) and a password of 8+ characters.", "error")
        else:
            try:
                uid = x("INSERT INTO users(username,password_hash,role,full_name,mobile) VALUES(?,?,?,?,?)", f["username"], generate_password_hash(pw), "student", f["full_name"], m).lastrowid
                x("INSERT INTO students(user_id,student_no,program) VALUES(?,?,?)", uid, f["student_no"], f["program"])
                flash("Account created. Log in below."); return redirect("/")
            except sqlite3.IntegrityError:
                db().rollback(); x("DELETE FROM users WHERE id NOT IN (SELECT user_id FROM students UNION SELECT user_id FROM counselors) AND role='student'")
                flash("That username or student number is already registered.", "error")
    return render_template("register.html")
@app.route("/profile", methods=["GET", "POST"])
@need()
def profile():
    if request.method == "POST":
        m, n, pw = mobile(request.form.get("mobile")), request.form.get("full_name", "").strip(), request.form.get("password", "")
        if not m or not n or (pw and len(pw) < 8): flash("Enter a valid mobile (09XXXXXXXXX), name, and a password of 8+ characters if changing it.", "error")
        else:
            x("UPDATE users SET full_name=?,mobile=? WHERE id=?", n, m, session["uid"])
            if pw: x("UPDATE users SET password_hash=? WHERE id=?", generate_password_hash(pw), session["uid"])
            session["name"] = n; audit("profile_update"); flash("Profile saved.")
    return render_template("profile.html", u=q1("SELECT * FROM users WHERE id=?", session["uid"]))

# ---------- scheduling core ----------
def free_slots(cid, d):
    try: day = datetime.strptime(d, "%Y-%m-%d")
    except ValueError: return []
    if q1("SELECT 1 FROM time_off WHERE counselor_id=? AND date=?", cid, d): return []
    taken = {r["time"] for r in q("SELECT time FROM appointments WHERE counselor_id=? AND date=? AND status<>'Cancelled'", cid, d)}
    out = []
    for s in q("SELECT * FROM schedules WHERE counselor_id=? AND weekday=?", cid, day.weekday()):
        t, end = datetime.strptime(f"{d} {s['start_time']}", FMT), datetime.strptime(f"{d} {s['end_time']}", FMT)
        while t + timedelta(minutes=s["slot_min"]) <= end:
            if t > datetime.now() and t.strftime("%H:%M") not in taken: out.append(t.strftime("%H:%M"))
            t += timedelta(minutes=s["slot_min"])
    return sorted(set(out))
def set_status(aid, new):
    a = q1("SELECT status FROM appointments WHERE id=?", aid)
    if not a or new not in MOVES.get(a["status"], ()): return False
    x("UPDATE appointments SET status=? WHERE id=?", new, aid)
    x("INSERT INTO appt_history(appointment_id,old_status,new_status,by_user) VALUES(?,?,?,?)", aid, a["status"], new, session.get("uid"))
    audit("appointment_" + new, str(aid)); return True
def book(sid, cid, d, t, concern):
    if t not in free_slots(cid, d): return None
    try: aid = x("INSERT INTO appointments(student_id,counselor_id,date,time,concern) VALUES(?,?,?,?,?)", sid, cid, d, t, concern).lastrowid
    except sqlite3.IntegrityError: db().rollback(); return None   # DB unique index = last line of double-booking defence
    audit("book", str(aid)); sms.notify(db(), aid, "confirmation"); return aid

# ---------- student ----------
@app.route("/student")
@need("student")
def student():
    cs = q("SELECT c.user_id,u.full_name FROM counselors c JOIN users u ON u.id=c.user_id WHERE u.active=1")
    cid = request.args.get("counselor", type=int) or (cs[0]["user_id"] if cs else None)
    d = request.args.get("date")
    if not d and cid:     # open on the next day that actually has slots
        d = next((x_ for x_ in ((date.today() + timedelta(days=i)).isoformat() for i in range(1, 15)) if free_slots(cid, x_)), None)
    d = d or (date.today() + timedelta(days=1)).isoformat()
    appts = q("SELECT a.*,u.full_name cname FROM appointments a JOIN users u ON u.id=a.counselor_id WHERE student_id=? ORDER BY date DESC,time DESC", session["uid"])
    avail = {}
    for c_ in cs:
        rows = q("SELECT weekday,start_time,end_time FROM schedules WHERE counselor_id=? ORDER BY weekday,start_time", c_["user_id"])
        days = sorted({r["weekday"] for r in rows})
        avail[c_["user_id"]] = {"days": ", ".join(WD[w] for w in days) or "no schedule yet", "set": set(days),
                                "hours": ", ".join(sorted({f'{r["start_time"]}–{r["end_time"]}' for r in rows}))}
    slots = free_slots(cid, d) if cid else None
    why, nexts = None, []
    if cid and not slots:
        name = next(c_["full_name"] for c_ in cs if c_["user_id"] == cid)
        try: wd = datetime.strptime(d, "%Y-%m-%d").weekday()
        except ValueError: wd = None
        if wd is None: why = "Enter a valid date."
        elif wd not in avail[cid]["set"]: why = f"{name} is not available on {WDF[wd]}s. Available days: {avail[cid]['days']}."
        else: why = f"No available slots on {d}: fully booked, blocked, or already past."
        nexts = [x_ for x_ in ((date.today() + timedelta(days=i)).isoformat() for i in range(0, 30)) if free_slots(cid, x_)][:5]
        if not nexts and avail[cid]["set"]: why += " There are no available dates in the next 30 days."
    return render_template("student.html", counselors=cs, cid=cid, d=d, today=date.today().isoformat(), appts=appts, slots=slots,
                           resched=request.args.get("resched"), avail=avail, why=why, nexts=nexts)
@app.post("/student/book")
@need("student")
def s_book():
    f = request.form
    if book(session["uid"], f.get("counselor", type=int), f.get("date", ""), f.get("time", ""), f.get("concern", "").strip()[:300] or "General"): flash("Appointment confirmed. A confirmation SMS was sent.")
    else: flash("That slot is no longer available. Pick another.", "error")
    return redirect("/student")
@app.post("/student/reschedule/<int:aid>")
@need("student")
def s_resched(aid):
    a = q1("SELECT * FROM appointments WHERE id=? AND student_id=? AND status IN('Pending','Confirmed')", aid, session["uid"])
    d, t = request.form.get("date", ""), request.form.get("time", "")
    if not a: abort(404)
    if t in free_slots(a["counselor_id"], d):
        try:
            x("UPDATE appointments SET date=?,time=? WHERE id=?", d, t, aid); audit("reschedule", str(aid)); sms.notify(db(), aid, "confirmation"); flash("Appointment rescheduled. New confirmation sent.")
        except sqlite3.IntegrityError: db().rollback(); flash("Slot taken.", "error")
    else: flash("That slot is not available.", "error")
    return redirect("/student")
def _cancel(aid, who_sql, *args):
    if q1(f"SELECT 1 FROM appointments WHERE id=? AND {who_sql}", aid, *args) and set_status(aid, "Cancelled"):
        sms.notify(db(), aid, "cancellation"); return True
    return False
@app.post("/student/cancel/<int:aid>")
@need("student")
def s_cancel(aid):
    flash("Appointment cancelled." if _cancel(aid, "student_id=?", session["uid"]) else "Cannot cancel this appointment.", "info"); return redirect("/student")

# ---------- counselor ----------
@app.route("/counselor")
@need("counselor")
def counselor():
    rows = q("SELECT a.*,u.full_name sname FROM appointments a JOIN users u ON u.id=a.student_id WHERE counselor_id=? ORDER BY date DESC,time DESC", session["uid"])
    appts = [dict(r, started=datetime.strptime(f'{r["date"]} {r["time"]}', FMT) <= datetime.now()) for r in rows]
    return render_template("counselor.html", appts=appts, sched=q("SELECT * FROM schedules WHERE counselor_id=? ORDER BY weekday,start_time", session["uid"]),
                           off=q("SELECT date FROM time_off WHERE counselor_id=? ORDER BY date", session["uid"]))
@app.post("/counselor/schedule")
@need("counselor")
def add_sched():
    f = request.form
    try: x("INSERT INTO schedules(counselor_id,weekday,start_time,end_time,slot_min) VALUES(?,?,?,?,?)", session["uid"], f.get("weekday", type=int), f["start_time"], f["end_time"], f.get("slot_min", 30, type=int)); flash("Hours added.")
    except (sqlite3.IntegrityError, KeyError): db().rollback(); flash("Invalid hours: start must be before end; slots are 15–120 minutes.", "error")
    return redirect("/counselor")
@app.post("/counselor/schedule/<int:sid>/delete")
@need("counselor")
def del_sched(sid): x("DELETE FROM schedules WHERE id=? AND counselor_id=?", sid, session["uid"]); return redirect("/counselor")
@app.post("/counselor/timeoff")
@need("counselor")
def timeoff(): x("INSERT OR IGNORE INTO time_off VALUES(?,?)", session["uid"], request.form.get("date", "")); return redirect("/counselor")
@app.post("/counselor/cancel/<int:aid>")
@need("counselor")
def c_cancel(aid):
    flash("Appointment cancelled; student notified." if _cancel(aid, "counselor_id=?", session["uid"]) else "Cannot cancel.", "info"); return redirect("/counselor")
@app.post("/counselor/mark/<int:aid>")
@need("counselor")
def mark(aid):
    new, notes = request.form.get("status"), request.form.get("notes", "").strip()
    a = q1("SELECT * FROM appointments WHERE id=? AND counselor_id=?", aid, session["uid"])
    if not a or new not in ("Completed", "No-Show"): abort(404)
    if datetime.strptime(f'{a["date"]} {a["time"]}', FMT) > datetime.now(): flash("The session has not started yet.", "error")
    elif set_status(aid, new):
        if notes: x("INSERT OR IGNORE INTO case_records(appointment_id,student_id,counselor_id,notes) VALUES(?,?,?,?)", aid, a["student_id"], session["uid"], notes)
        flash(f"Marked {new}.")
    return redirect("/counselor")
def my_students(term=""):
    t = f"%{term}%"
    return q("""SELECT DISTINCT u.id,u.full_name,s.student_no,s.program FROM users u JOIN students s ON s.user_id=u.id JOIN appointments a ON a.student_id=u.id
                WHERE a.counselor_id=? AND (u.full_name LIKE ? OR s.student_no LIKE ?) ORDER BY u.full_name""", session["uid"], t, t)
@app.route("/counselor/records")
@need("counselor")
def records(): return render_template("records.html", rows=my_students(request.args.get("q", "")), q=request.args.get("q", ""))
@app.route("/counselor/student/<int:sid>")
@need("counselor")
def student_case(sid):
    if not q1("SELECT 1 FROM appointments WHERE student_id=? AND counselor_id=?", sid, session["uid"]): abort(403)  # only students you serve
    audit("view_case", str(sid))
    s = q1("SELECT u.full_name,st.student_no,st.program FROM users u JOIN students st ON st.user_id=u.id WHERE u.id=?", sid)
    hist = q("""SELECT a.*,c.full_name cname,r.notes FROM appointments a JOIN users c ON c.id=a.counselor_id LEFT JOIN case_records r ON r.appointment_id=a.id
                WHERE a.student_id=? ORDER BY a.date DESC,a.time DESC""", sid)
    return render_template("student_case.html", s=s, hist=hist)

# ---------- admin ----------
@app.route("/admin")
@need("admin")
def admin():
    n = lambda sql: q1(sql)[0]
    stats = {"Students": n("SELECT COUNT(*) FROM users WHERE role='student'"), "Counselors": n("SELECT COUNT(*) FROM users WHERE role='counselor'"),
             "Appointments": n("SELECT COUNT(*) FROM appointments"), "Upcoming": n("SELECT COUNT(*) FROM appointments WHERE status='Confirmed'"), "SMS sent": n("SELECT COUNT(*) FROM sms_log WHERE status='sent'")}
    return render_template("admin.html", stats=stats, users=q("SELECT * FROM users ORDER BY role,full_name"))
@app.post("/admin/counselor")
@need("admin")
def add_counselor():
    f, m = request.form, mobile(request.form.get("mobile"))
    if not m or len(f.get("password", "")) < 8 or not f.get("username") or not f.get("full_name"): flash("Enter a name, username, valid mobile, and 8+ character password.", "error")
    else:
        try:
            uid = x("INSERT INTO users(username,password_hash,role,full_name,mobile) VALUES(?,?,?,?,?)", f["username"].strip(), generate_password_hash(f["password"]), "counselor", f["full_name"].strip(), m).lastrowid
            x("INSERT INTO counselors(user_id) VALUES(?)", uid); audit("create_counselor", str(uid)); flash("Counselor created.")
        except sqlite3.IntegrityError: db().rollback(); flash("Username already exists.", "error")
    return redirect("/admin")
@app.post("/admin/user/<int:uid>/toggle")
@need("admin")
def toggle(uid):
    if uid != session["uid"]: x("UPDATE users SET active=1-active WHERE id=?", uid); audit("toggle_user", str(uid))
    return redirect("/admin")
@app.post("/admin/user/<int:uid>/role")
@need("admin")
def role(uid):
    r = request.form.get("role")
    if uid != session["uid"] and r in ("student", "counselor", "admin"):
        x("UPDATE users SET role=? WHERE id=?", r, uid)
        if r == "student": x("INSERT OR IGNORE INTO students(user_id) VALUES(?)", uid)
        if r == "counselor": x("INSERT OR IGNORE INTO counselors(user_id) VALUES(?)", uid)
        audit("role_change", f"{uid}->{r}")
    return redirect("/admin")
@app.route("/admin/reports")
@need("admin")
def reports():
    st = request.args.get("status", "")
    weekly = [dict(r, rate=round(100 * r["ns"] / max(r["done"] + r["ns"], 1))) for r in q("""SELECT strftime('%Y-W%W',date) wk,COUNT(*) total,SUM(status='Completed') done,SUM(status='No-Show') ns,SUM(status='Cancelled') cx
        FROM appointments GROUP BY wk ORDER BY wk DESC""")]
    appts = q("""SELECT a.*,s.full_name sname,c.full_name cname FROM appointments a JOIN users s ON s.id=a.student_id JOIN users c ON c.id=a.counselor_id
        WHERE (?='' OR a.status=?) ORDER BY date DESC,time DESC LIMIT 200""", st, st)       # no session notes exposed to admin
    return render_template("reports.html", weekly=weekly, appts=appts, st=st, logs=q("SELECT * FROM sms_log ORDER BY id DESC LIMIT 50"))

@app.errorhandler(403)
def e403(_): return "Forbidden: you do not have access to this page.", 403
def seed_demo(count=2):
    import random
    FF = ["Maria", "Angelica", "Carmela", "Katrina", "Liza"]; FM = ["Jose", "Mark", "Paolo", "Joel", "Miguel"]
    L = ["Reyes", "Dela Cruz", "Mendoza", "Bautista", "Villanueva", "Ramos", "Aquino", "Castillo", "Navarro", "Flores"]
    FIXED = [("Mr. Ramon Santos", (0, 2, 4)), ("Ms. Bianca Garcia", (1, 3, 5))]      # MWF  /  TTHS(Tue, Thu, Sat)
    pw = os.environ.get("DEMO_PASSWORD") or secrets.token_urlsafe(8); c = D.connect(); made = []
    for i in range(1, max(count, 2) + 1):
        if i <= 2: n, days = FIXED[i - 1]
        else:
            g = random.choice(["Ms.", "Mr."]); n, days = f"{g} {random.choice(FF if g == 'Ms.' else FM)} {random.choice(L)}", (0, 1, 2, 3, 4)
        u = f"counselor{i}"
        c.execute("INSERT OR IGNORE INTO users(username,password_hash,role,full_name) VALUES(?,?,?,?)", (u, generate_password_hash(pw), "counselor", n))
        c.execute("UPDATE users SET full_name=? WHERE username=? AND role='counselor'", (n, u))
        uid = c.execute("SELECT id FROM users WHERE username=?", (u,)).fetchone()[0]
        c.execute("INSERT OR IGNORE INTO counselors(user_id) VALUES(?)", (uid,))
        c.execute("DELETE FROM schedules WHERE counselor_id=?", (uid,))
        for wd in days:
            for st, en in ((("09:00", "12:00"),) if wd == 5 else (("09:00", "12:00"), ("13:00", "16:00"))):
                c.execute("INSERT INTO schedules(counselor_id,weekday,start_time,end_time,slot_min) VALUES(?,?,?,?,30)", (uid, wd, st, en))
        made.append(f"  {u}: {n}  ({', '.join(WD[w] for w in days)})")
    c.commit(); c.close()
    return "Demo counselors:\n" + "\n".join(made) + f"\nPassword: {pw if not os.environ.get('DEMO_PASSWORD') else '(from DEMO_PASSWORD)'}"
_c = D.init()
if os.environ.get("AUTO_DEMO", "1") == "1" and _c.execute("SELECT COUNT(*) FROM counselors").fetchone()[0] == 0:
    print("No counselors found, creating demo counselors (set AUTO_DEMO=0 to disable):\n" + seed_demo(), flush=True)
_c.close()
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "seed-admin":      # python app.py seed-admin
        pw = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(10)
        c = D.connect(); u = os.environ.get("ADMIN_USER", "gco_admin")
        c.execute("INSERT OR IGNORE INTO users(username,password_hash,role,full_name) VALUES(?,?,?,?)", (u, generate_password_hash(pw), "admin", "GCO Administrator")); c.commit()
        print(f"Admin '{u}' ready. Password: {pw if not os.environ.get('ADMIN_PASSWORD') else '(from ADMIN_PASSWORD)'}")
    elif len(sys.argv) > 1 and sys.argv[1] == "seed-demo": print(seed_demo(int(sys.argv[2]) if len(sys.argv) > 2 else 2))
    else: app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)))
