import os, sqlite3
def _env():
    f = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(f):
        for l in open(f):
            if "=" in l and not l.startswith("#"):
                k, v = l.strip().split("=", 1); os.environ.setdefault(k, v)
_env()
def connect():
    path = os.environ.get("DATABASE", "gcas.db")
    if not os.path.isabs(path): path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)  # same file no matter where you run from
    c = sqlite3.connect(path, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c
def init():
    c = connect()
    c.executescript(open(os.path.join(os.path.dirname(__file__), "schema.sql")).read())
    c.commit()
    return c
