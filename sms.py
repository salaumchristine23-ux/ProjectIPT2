"""Semaphore SMS client: real HTTP calls, logging, dedupe, retry bookkeeping, throttling."""
import os, time, json, urllib.request, urllib.parse, urllib.error
URL = "https://api.semaphore.co/api/v4/messages"
MAX_ATTEMPTS = 3
_last = [0.0]

def _post(number, message):
    key = os.environ.get("SEMAPHORE_API_KEY")
    if not key:
        return 0, "SEMAPHORE_API_KEY not configured"
    fields = {"apikey": key, "number": number, "message": message}
    if os.environ.get("SEMAPHORE_SENDER"):
        fields["sendername"] = os.environ["SEMAPHORE_SENDER"]
    req = urllib.request.Request(URL, urllib.parse.urlencode(fields).encode())
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode()[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]
    except Exception as e:  # network down, DNS, timeout
        return 0, f"network error: {e}"

def send(db, appt_id, kind, mobile, message, key):
    row = db.execute("SELECT id,status,attempts FROM sms_log WHERE dedupe_key=?", (key,)).fetchone()
    if row and row["status"] == "sent":
        return "duplicate"
    if row and row["attempts"] >= MAX_ATTEMPTS:
        return "gave_up"
    if row:
        lid = row["id"]
    else:
        lid = db.execute("INSERT INTO sms_log(appointment_id,kind,mobile,message,dedupe_key) VALUES(?,?,?,?,?)",
                         (appt_id, kind, mobile, message, key)).lastrowid
    wait = float(os.environ.get("SMS_MIN_INTERVAL", "0.6")) - (time.time() - _last[0])  # Semaphore rate limit
    if wait > 0:
        time.sleep(wait)
    code, body = _post(mobile, message)
    _last[0] = time.time()
    status = "sent" if code == 200 else "failed"
    if code == 429:
        body = "rate_limited: " + body
    db.execute("UPDATE sms_log SET status=?,attempts=attempts+1,response=? WHERE id=?", (status, f"{code} {body}", lid))
    db.commit()
    return status

def notify(db, appt_id, kind):
    a = db.execute("""SELECT a.*,u.mobile,u.full_name sname,c.full_name cname FROM appointments a
        JOIN users u ON u.id=a.student_id JOIN users c ON c.id=a.counselor_id WHERE a.id=?""", (appt_id,)).fetchone()
    if not a or not a["mobile"]:
        return "no_number"
    if kind == "reminder" and a["status"] != "Confirmed":
        return "skipped"
    when = f'{a["date"]} {a["time"]}'
    msg = {"confirmation": f"ICCT Cainta GCO: Your counseling appointment with {a['cname']} on {when} is confirmed.",
           "reminder": f"ICCT Cainta GCO reminder: counseling appointment with {a['cname']} on {when}. Please arrive on time.",
           "cancellation": f"ICCT Cainta GCO: Your counseling appointment on {when} has been cancelled. Book a new slot in GCAS."}[kind]
    return send(db, appt_id, kind, a["mobile"], msg, f"{appt_id}:{kind}:{when}")
