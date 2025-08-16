# apply_db.py  (place at repo root)
from __future__ import annotations
import os
import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

# -------------------- Config & helpers --------------------
DB_PATH = os.getenv("APPLY_DB_PATH", "data/apply.sqlite3")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

VALID_STATUSES = {
    "QUEUED", "IN_PROGRESS", "DRAFTED", "SUBMITTED", "DONE", "FAILED", "CANCELLED"
}

REQUIRED_APP_COLUMNS: Dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "url": "TEXT",
    "company": "TEXT",
    "title": "TEXT",
    "portal": "TEXT",
    "job_json": "TEXT NOT NULL",
    "created_at": "TEXT NOT NULL",
    "updated_at": "TEXT NOT NULL",
}

REQUIRED_TASK_COLUMNS: Dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "application_id": "INTEGER NOT NULL",
    "status": "TEXT NOT NULL",
    "attempts": "INTEGER NOT NULL DEFAULT 0",
    "error": "TEXT",
    "artifacts_json": "TEXT",  # JSON blob with screenshot_url, snapshot_url, confirmation, etc.
    "created_at": "TEXT NOT NULL",
    "updated_at": "TEXT NOT NULL",
}

def _conn() -> sqlite3.Connection:
    # autocommit mode; usable across threads in our simple worker
    return sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)

def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"

def _table_exists(c: sqlite3.Connection, name: str) -> bool:
    return bool(c.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone())

def _columns(c: sqlite3.Connection, table: str) -> List[str]:
    return [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]

def _ensure_table_with_columns(c: sqlite3.Connection, table: str, required: Dict[str, str]) -> None:
    if not _table_exists(c, table):
        cols = ", ".join(f"{k} {v}" for k, v in required.items())
        c.execute(f"CREATE TABLE {table} ({cols});")
        return
    # migrate: add any missing columns
    existing = set(_columns(c, table))
    for col, decl in required.items():
        if col not in existing:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl};")

def _ensure_indexes(c: sqlite3.Connection) -> None:
    # Create light indexes used by worker polling & status queries
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
    except Exception:
        pass
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_app ON tasks(application_id);")
    except Exception:
        pass
    try:
        c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_updated ON tasks(updated_at);")
    except Exception:
        pass

# -------------------- Public API --------------------
def init_apply() -> None:
    """Initialize/migrate DB schema."""
    with _conn() as c:
        _ensure_table_with_columns(c, "applications", REQUIRED_APP_COLUMNS)
        _ensure_table_with_columns(c, "tasks", REQUIRED_TASK_COLUMNS)
        _ensure_indexes(c)

def enqueue_application(job: Dict[str, Any]) -> int:
    """Create an application + initial QUEUED task. Returns new task_id."""
    url = (job.get("url") or "").strip()
    company = (job.get("company") or "").strip()
    title = (job.get("title") or "").strip()
    portal = (job.get("portal") or job.get("source") or "").strip().lower()
    payload = json.dumps(job or {})
    now = _now()
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO applications(url, company, title, portal, job_json, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (url, company, title, portal, payload, now, now)
        )
        app_id = int(cur.lastrowid)
        c.execute(
            "INSERT INTO tasks(application_id, status, attempts, created_at, updated_at) "
            "VALUES (?,?,?,?,?)",
            (app_id, "QUEUED", 0, now, now)
        )
        task_id = c.execute(
            "SELECT id FROM tasks WHERE application_id=? ORDER BY id DESC LIMIT 1",
            (app_id,)
        ).fetchone()[0]
        return int(task_id)

def list_applications() -> List[Dict[str, Any]]:
    """Return latest status row per application, including last artifacts."""
    with _conn() as c:
        rows = c.execute("""
            SELECT
                a.id, a.url, a.company, a.title, a.portal, a.job_json, a.created_at, a.updated_at,
                COALESCE((
                    SELECT status FROM tasks
                    WHERE application_id=a.id
                    ORDER BY id DESC LIMIT 1
                ), 'QUEUED') AS latest_status,
                COALESCE((
                    SELECT attempts FROM tasks
                    WHERE application_id=a.id
                    ORDER BY id DESC LIMIT 1
                ), 0) AS attempts,
                (
                    SELECT error FROM tasks
                    WHERE application_id=a.id
                    ORDER BY id DESC LIMIT 1
                ) AS error,
                COALESCE((
                    SELECT artifacts_json FROM tasks
                    WHERE application_id=a.id
                    ORDER BY id DESC LIMIT 1
                ), '{}') AS artifacts_json
            FROM applications a
            ORDER BY a.id DESC
        """).fetchall()

    out: List[Dict[str, Any]] = []
    for (app_id, url, company, title, portal, job_json, created_at, updated_at,
         status, attempts, error, artifacts_json) in rows:
        try:
            job = json.loads(job_json or "{}")
        except Exception:
            job = {}
        try:
            artifacts = json.loads(artifacts_json or "{}")
        except Exception:
            artifacts = {}
        out.append({
            "id": app_id,
            "url": url,
            "company": company,
            "title": title,
            "portal": portal,
            "job": job,
            "status": status or "QUEUED",
            "attempts": attempts or 0,
            "error": error,
            "artifacts": artifacts or None,
            "created_at": created_at,
            "updated_at": updated_at,
        })
    return out

def get_application(app_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        row = c.execute(
            "SELECT id, url, company, title, portal, job_json, created_at, updated_at "
            "FROM applications WHERE id=?",
            (app_id,)
        ).fetchone()
    if not row:
        return None
    (id_, url, company, title, portal, job_json, created_at, updated_at) = row
    try:
        job = json.loads(job_json or "{}")
    except Exception:
        job = {}
    return {
        "id": id_,
        "url": url,
        "company": company,
        "title": title,
        "portal": portal,
        "job": job,
        "created_at": created_at,
        "updated_at": updated_at,
    }

def update_task_status(task_id: int, status: str, *, error: Optional[str] = None) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    now = _now()
    with _conn() as c:
        if error is None:
            c.execute(
                "UPDATE tasks SET status=?, updated_at=? WHERE id=?",
                (status, now, task_id)
            )
        else:
            c.execute(
                "UPDATE tasks SET status=?, error=?, updated_at=? WHERE id=?",
                (status, error, now, task_id)
            )

def set_artifacts(task_id: int, data: Dict[str, Any]) -> None:
    """Merge new artifacts into artifacts_json for a task."""
    with _conn() as c:
        prev = c.execute("SELECT artifacts_json FROM tasks WHERE id=?", (task_id,)).fetchone()
        cur = {}
        if prev and prev[0]:
            try:
                cur = json.loads(prev[0])
            except Exception:
                cur = {}
        cur.update(data or {})
        c.execute(
            "UPDATE tasks SET artifacts_json=?, updated_at=? WHERE id=?",
            (json.dumps(cur), _now(), task_id)
        )

def increment_attempts(task_id: int) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE tasks SET attempts=attempts+1, updated_at=? WHERE id=?",
            (_now(), task_id)
        )

def get_next_task() -> Optional[Dict[str, Any]]:
    """Atomically fetch the next QUEUED task and mark it IN_PROGRESS."""
    with _conn() as c:
        row = c.execute(
            "SELECT id, application_id FROM tasks WHERE status='QUEUED' ORDER BY id ASC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        task_id, app_id = int(row[0]), int(row[1])
        c.execute(
            "UPDATE tasks SET status='IN_PROGRESS', updated_at=? WHERE id=?",
            (_now(), task_id)
        )
        a = c.execute(
            "SELECT url, company, title, portal, job_json FROM applications WHERE id=?",
            (app_id,)
        ).fetchone()
    if not a:
        return None
    url, company, title, portal, job_json = a
    try:
        job = json.loads(job_json or "{}")
    except Exception:
        job = {}
    return {
        "task_id": task_id,
        "application_id": app_id,
        "status": "IN_PROGRESS",
        "url": url,
        "company": company,
        "title": title,
        "portal": portal,
        "job": job,
    }

# -------------------- Legacy shims (backward compat) --------------------
def transition(task_id: int, new_status: str, error: Optional[str] = None) -> None:
    """Compatibility: old worker imports `transition`."""
    update_task_status(task_id, new_status, error=error)

def dequeue_next():
    """Compatibility: old worker name."""
    return get_next_task()

def update_application_status(task_id: int, status: str, *, error: Optional[str] = None) -> None:
    """Compatibility: old worker name."""
    update_task_status(task_id, status, error=error)
