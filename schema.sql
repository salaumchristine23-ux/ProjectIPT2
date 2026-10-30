CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN('student','counselor','admin')), full_name TEXT NOT NULL,
 mobile TEXT CHECK(mobile IS NULL OR mobile GLOB '09[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'),
 active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS students(user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, student_no TEXT UNIQUE, program TEXT);
CREATE TABLE IF NOT EXISTS counselors(user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, specialization TEXT);
CREATE TABLE IF NOT EXISTS schedules(id INTEGER PRIMARY KEY, counselor_id INTEGER NOT NULL REFERENCES counselors(user_id) ON DELETE CASCADE,
 weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6), start_time TEXT NOT NULL, end_time TEXT NOT NULL,
 slot_min INTEGER NOT NULL DEFAULT 30 CHECK(slot_min BETWEEN 15 AND 120), CHECK(start_time<end_time));
CREATE TABLE IF NOT EXISTS time_off(counselor_id INTEGER NOT NULL REFERENCES counselors(user_id) ON DELETE CASCADE, date TEXT NOT NULL, PRIMARY KEY(counselor_id,date));
CREATE TABLE IF NOT EXISTS appointments(id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL REFERENCES students(user_id),
 counselor_id INTEGER NOT NULL REFERENCES counselors(user_id), date TEXT NOT NULL, time TEXT NOT NULL, concern TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'Confirmed' CHECK(status IN('Pending','Confirmed','Cancelled','Completed','No-Show')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE UNIQUE INDEX IF NOT EXISTS uq_counselor_slot ON appointments(counselor_id,date,time) WHERE status<>'Cancelled';
CREATE UNIQUE INDEX IF NOT EXISTS uq_student_slot ON appointments(student_id,date,time) WHERE status<>'Cancelled';
CREATE TABLE IF NOT EXISTS appt_history(id INTEGER PRIMARY KEY, appointment_id INTEGER NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
 old_status TEXT, new_status TEXT NOT NULL, by_user INTEGER, at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS case_records(id INTEGER PRIMARY KEY, appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(id),
 student_id INTEGER NOT NULL REFERENCES students(user_id), counselor_id INTEGER NOT NULL REFERENCES counselors(user_id),
 notes TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS sms_log(id INTEGER PRIMARY KEY, appointment_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
 kind TEXT NOT NULL CHECK(kind IN('confirmation','reminder','cancellation')), mobile TEXT NOT NULL, message TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'queued' CHECK(status IN('queued','sent','failed')), attempts INTEGER NOT NULL DEFAULT 0,
 response TEXT, dedupe_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT NOT NULL, detail TEXT, at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
