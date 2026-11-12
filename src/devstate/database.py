import json, sqlite3
from pathlib import Path
from threading import Lock
from datetime import datetime, timezone

_lock = Lock()

class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, title TEXT NOT NULL,
                message TEXT NOT NULL, priority INTEGER NOT NULL, tags TEXT NOT NULL, created_at TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL, payload TEXT NOT NULL,
                created_at TEXT NOT NULL)""")

    def _connect(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def add_event(self, e: dict) -> int:
        with _lock, self._connect() as c:
            cur = c.execute("INSERT INTO events(source,title,message,priority,tags,created_at) VALUES(?,?,?,?,?,?)",
                (e["source"], e["title"], e.get("message",""), int(e["priority"]),
                 json.dumps(e.get("tags",[])), datetime.now(timezone.utc).isoformat()))
            return cur.lastrowid

    def recent_events(self, limit=50):
        with self._connect() as c: rows = c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
        return [dict(r) | {"tags": json.loads(r["tags"])} for r in rows]

    def add_snapshot(self, project: str, payload: dict):
        with _lock, self._connect() as c:
            cur = c.execute("INSERT INTO snapshots(project,payload,created_at) VALUES(?,?,?)",
                (project,json.dumps(payload,default=str),datetime.now(timezone.utc).isoformat()))
            return cur.lastrowid

    def recent_snapshots(self, limit=100):
        with self._connect() as c: rows=c.execute("SELECT * FROM snapshots ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
        return [dict(r) | {"payload":json.loads(r["payload"])} for r in rows]
