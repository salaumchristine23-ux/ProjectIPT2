"""Independent reminder worker:  python scheduler.py   (runs forever, no browser needed)."""
import os, time
from datetime import datetime, timedelta
import db as D, sms

def run_once(conn, now=None):
    now = now or datetime.now()
    hours = float(os.environ.get("REMINDER_HOURS", "24"))
    sent = 0
    for a in conn.execute("SELECT id,date,time FROM appointments WHERE status='Confirmed'").fetchall():
        start = datetime.strptime(f'{a["date"]} {a["time"]}', "%Y-%m-%d %H:%M")
        if now < start <= now + timedelta(hours=hours):          # Reminder due?
            if sms.notify(conn, a["id"], "reminder") == "sent":   # dedupe via sms_log.dedupe_key
                sent += 1
    for r in conn.execute("SELECT appointment_id,kind FROM sms_log WHERE status='failed' AND attempts<?", (sms.MAX_ATTEMPTS,)).fetchall():
        sms.notify(conn, r["appointment_id"], r["kind"])          # retry failed sends
    return sent

if __name__ == "__main__":
    D.init()
    interval = int(os.environ.get("SCHEDULER_INTERVAL_SEC", "60"))
    while True:
        try:
            c = D.connect(); n = run_once(c); c.close()
            if n: print(f"{datetime.now():%F %T} sent {n} reminder(s)", flush=True)
        except Exception as e:
            print("scheduler error:", e, flush=True)
        time.sleep(interval)     # "Scheduler waits (loops) checks again"
