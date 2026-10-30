import os, re, sys, tempfile, unittest
from datetime import datetime, timedelta
os.environ.update(DATABASE=tempfile.mktemp(suffix=".db"), SMS_MIN_INTERVAL="0", SECRET_KEY="t")
os.environ.pop("SEMAPHORE_API_KEY", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import app as A, sms, scheduler, db as D
from werkzeug.security import generate_password_hash as H
SENT = []
sms._post = lambda n, m: (SENT.append((n, m)) or (200, "[{}]"))   # mocked HTTP layer (live API not reachable here)

def client():
    c = A.app.test_client(); return c
def tok(c, path="/"): return re.search(r'name=csrf value="(.+?)"', c.get(path).get_data(True)).group(1)
def post(c, path, page="/", **f): return c.post(path, data=dict(f, csrf=tok(c, page)))
def login(c, u, p): return post(c, "/", username=u, password=p)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = D.connect()
        for u, r in (("admin1", "admin"), ("couns1", "counselor"), ("couns2", "counselor")):
            i = d.execute("INSERT INTO users(username,password_hash,role,full_name) VALUES(?,?,?,?)", (u, H("password1"), r, u)).lastrowid
            if r == "counselor": d.execute("INSERT INTO counselors(user_id) VALUES(?)", (i,))
        d.commit(); cls.d = d
        c = client()
        for n in (1, 2):
            post(c, "/register", "/register", full_name=f"Stu {n}", student_no=f"S{n}", program="BSIT", mobile=f"0917000000{n}", username=f"stu{n}", password="password1")
    def test_01_register_login_redirect(self):
        self.assertEqual(self.d.execute("SELECT COUNT(*) FROM students").fetchone()[0], 2)
        for u, path in (("stu1", "/student"), ("couns1", "/counselor"), ("admin1", "/admin")):
            c = client(); self.assertTrue(login(c, u, "password1").headers["Location"].endswith(path))
        c = client(); self.assertIn("Invalid", login(c, "stu1", "wrong").get_data(True)); self.assertEqual(c.get("/student").status_code, 302)
    def test_02_rbac(self):
        c = client(); login(c, "stu1", "password1")
        for p in ("/admin", "/counselor", "/admin/reports", "/counselor/records"): self.assertEqual(c.get(p).status_code, 403, p)
        self.assertEqual(c.post("/student/book", data={}).status_code, 400)  # CSRF
    def test_03_full_flow(self):
        cc = client(); login(cc, "couns1", "password1"); day = datetime.now() + timedelta(days=2)
        post(cc, "/counselor/schedule", "/counselor", weekday=day.weekday(), start_time="09:00", end_time="11:00", slot_min=30)
        cid = self.d.execute("SELECT id FROM users WHERE username='couns1'").fetchone()[0]; ds = day.strftime("%Y-%m-%d")
        s1, s2 = client(), client(); login(s1, "stu1", "password1"); login(s2, "stu2", "password1")
        SENT.clear(); post(s1, "/student/book", "/student", counselor=cid, date=ds, time="09:00", concern="exam stress")
        self.assertEqual(len(SENT), 1)                                            # confirmation SMS
        post(s2, "/student/book", "/student", counselor=cid, date=ds, time="09:00", concern="x")  # double-book attempt
        self.assertEqual(self.d.execute("SELECT COUNT(*) FROM appointments WHERE time='09:00' AND date=?", (ds,)).fetchone()[0], 1)
        aid = self.d.execute("SELECT id FROM appointments").fetchone()[0]
        post(s1, f"/student/reschedule/{aid}", "/student", date=ds, time="09:30")
        self.assertEqual(self.d.execute("SELECT time FROM appointments WHERE id=?", (aid,)).fetchone()[0], "09:30")
        post(s2, f"/student/book", "/student", counselor=cid, date=ds, time="09:00", concern="y")   # freed slot now bookable
        self.assertEqual(self.d.execute("SELECT COUNT(*) FROM appointments").fetchone()[0], 2)
        n = len(SENT); post(s1, f"/student/cancel/{aid}", "/student"); post(s1, f"/student/cancel/{aid}", "/student")
        self.assertEqual(len(SENT), n + 1)                                        # one cancellation SMS, no duplicate
        self.assertEqual(self.d.execute("SELECT status FROM appointments WHERE id=?", (aid,)).fetchone()[0], "Cancelled")
    def test_04_reminders_attendance_records(self):
        d = self.d; cid = d.execute("SELECT id FROM users WHERE username='couns1'").fetchone()[0]; sid = d.execute("SELECT id FROM users WHERE username='stu1'").fetchone()[0]
        soon = datetime.now() + timedelta(hours=3); past = datetime.now() - timedelta(hours=2)
        a1 = d.execute("INSERT INTO appointments(student_id,counselor_id,date,time,concern) VALUES(?,?,?,?,'c')", (sid, cid, soon.strftime("%Y-%m-%d"), soon.strftime("%H:%M"))).lastrowid
        a2 = d.execute("INSERT INTO appointments(student_id,counselor_id,date,time,concern) VALUES(?,?,?,?,'c')", (sid, cid, past.strftime("%Y-%m-%d"), past.strftime("%H:%M"))).lastrowid; d.commit()
        SENT.clear(); self.assertEqual(scheduler.run_once(d), 1); self.assertEqual(scheduler.run_once(d), 0)   # reminder once only
        sms._post = lambda n, m: (429, "slow down"); d.execute("DELETE FROM sms_log WHERE kind='reminder'"); d.commit()
        scheduler.run_once(d); self.assertEqual(d.execute("SELECT status FROM sms_log WHERE kind='reminder'").fetchone()[0], "failed")
        sms._post = lambda n, m: (SENT.append(1) or (200, "ok")); scheduler.run_once(d)
        self.assertEqual(d.execute("SELECT status FROM sms_log WHERE kind='reminder'").fetchone()[0], "sent")   # retried
        cc, other = client(), client(); login(cc, "couns1", "password1"); login(other, "couns2", "password1")
        post(cc, f"/counselor/mark/{a2}", "/counselor", status="Completed", notes="Discussed study plan")
        self.assertEqual(d.execute("SELECT status FROM appointments WHERE id=?", (a2,)).fetchone()[0], "Completed")
        post(cc, f"/counselor/mark/{a1}", "/counselor", status="No-Show")        # not started -> rejected
        self.assertEqual(d.execute("SELECT status FROM appointments WHERE id=?", (a1,)).fetchone()[0], "Confirmed")
        self.assertIn("Discussed study plan", cc.get(f"/counselor/student/{sid}").get_data(True))
        self.assertEqual(other.get(f"/counselor/student/{sid}").status_code, 403)   # unrelated counselor blocked
        ad = client(); login(ad, "admin1", "password1"); r = ad.get("/admin/reports").get_data(True)
        self.assertIn("Completed", r); self.assertNotIn("Discussed study plan", r)  # admin sees stats, not notes
        post(ad, "/admin/counselor", "/admin", full_name="New C", username="newc", mobile="09171234567", password="password1")
        self.assertIsNotNone(d.execute("SELECT 1 FROM counselors c JOIN users u ON u.id=c.user_id WHERE username='newc'").fetchone())
if __name__ == "__main__": unittest.main(verbosity=2)
