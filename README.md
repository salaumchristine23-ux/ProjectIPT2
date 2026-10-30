# GCAS – Guidance and Counseling Appointment System (ICCT Cainta)
Flask + SQLite. Semaphore SMS via plain HTTPS (no extra SDK). Flowchart mapping: login → role → portal → DB → Semaphore → scheduler → attendance → logout.

## Run
    pip install -r requirements.txt
    cp .env.example .env          # set SECRET_KEY and SEMAPHORE_API_KEY (from semaphore.co)
    python app.py seed-admin      # creates admin; prints a generated password unless ADMIN_PASSWORD is set
    python app.py                 # web app  http://127.0.0.1:5000
    python scheduler.py           # SECOND terminal/service: reminder worker (runs without anyone using the site)
    python tests/test_gcas.py     # automated tests
Admin creates counselor accounts; counselors add weekly hours; students self-register.

## Deploy
    gunicorn -w 2 -b 0.0.0.0:8000 app:app      # behind nginx/HTTPS; set COOKIE_SECURE=1 and a fixed SECRET_KEY
Run `python scheduler.py` as a systemd service (or a second process on the host) with the same .env. Back up gcas.db.

## Behaviour notes
- Booking is auto-Confirmed. Statuses: Pending, Confirmed, Cancelled, Completed, No-Show (Confirmed→Completed/No-Show only after start time).
- Double-booking blocked in code and by DB unique indexes. SMS dedupe via unique `sms_log.dedupe_key`; failures retried up to 3 times by the scheduler; sends are throttled (SMS_MIN_INTERVAL) for Semaphore rate/credit limits.
- Counselors see case records only of students they have appointments with; admins see statistics and SMS logs, never session notes.

## Test status
Automated tests cover: registration, login/invalid login, role redirects, RBAC + CSRF, booking, double-booking, reschedule, cancel, duplicate-SMS prevention, reminder timing, retry after 429, attendance, case-record access control, admin reports/account creation.
**Not verified:** live Semaphore delivery (tests mock the HTTP layer; no network or API key in the build sandbox).
Confirm with your key: book a test appointment and check Admin → Reports → SMS log shows `sent`.
