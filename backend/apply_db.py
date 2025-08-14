# apply_db.py  (place at repo root)
import os, json, sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List

DB_PATH = os.getenv("APPLY_DB_PATH", "data/apply.sqlite3")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

REQUIRED_TASK_COLUMNS = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "application_id": "INTEGER NOT NULL",
    "status": "TEXT NOT NULL",
    "attempts": "INTEGER NOT NULL DEFAULT 0",
    "error": "TEXT",
    "artifacts_json": "TEXT",    # <-- store screenshot/paths/etc.
    "created_at": "TEXT NOT NULL",
    "updated_at": "TEXT NOT NULL",
}
REQUIRED_APP_COLUMNS = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "url": "TEXT","company":"TEXT","title":"TEXT","portal":"TEXT",
    "job_json":"TEXT NOT NULL","created_at":"TEXT NOT NULL","updated_at":"TEXT NOT NULL",
}

VALID = {"QUEUED","IN_PROGRESS","DRAFTED","SUBMITTED","DONE","FAILED","CANCELLED"}

def _conn(): return sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
def _now():  return datetime.utcnow().isoformat()+"Z"
def _table_exists(c, name): return bool(c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())
def _cols(c, t): return [r[1] for r in c.execute(f"PRAGMA table_info({t})").fetchall()]

def _ensure_table(c, name, cols: Dict[str,str]):
    if not _table_exists(c, name):
        c.execute(f"CREATE TABLE {name} ({', '.join([f'{k} {v}' for k,v in cols.items()])});")
    else:
        existing = set(_cols(c, name))
        for k,v in cols.items():
            if k not in existing:
                c.execute(f"ALTER TABLE {name} ADD COLUMN {k} {v};")

def init_apply():
    with _conn() as c:
        _ensure_table(c, "applications", REQUIRED_APP_COLUMNS)
        _ensure_table(c, "tasks", REQUIRED_TASK_COLUMNS)
        if "status" in _cols(c, "tasks"):
            c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")

def enqueue_application(job: Dict[str,Any]) -> int:
    url=(job.get("url") or "").strip()
    company=(job.get("company") or "").strip()
    title=(job.get("title") or "").strip()
    portal=(job.get("portal") or job.get("source") or "").strip().lower()
    payload=json.dumps(job); now=_now()
    with _conn() as c:
        app_id=c.execute(
            "INSERT INTO applications(url,company,title,portal,job_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (url,company,title,portal,payload,now,now)
        ).lastrowid
        c.execute("INSERT INTO tasks(application_id,status,attempts,created_at,updated_at) VALUES (?,?,?,?,?)",
                  (app_id,"QUEUED",0,now,now))
        return int(c.execute("SELECT id FROM tasks WHERE application_id=? ORDER BY id DESC LIMIT 1",(app_id,)).fetchone()[0])

def list_applications() -> List[Dict[str,Any]]:
    with _conn() as c:
        rows=c.execute("""
        SELECT a.id,a.url,a.company,a.title,a.portal,a.job_json,a.created_at,a.updated_at,
               (SELECT status FROM tasks WHERE application_id=a.id ORDER BY id DESC LIMIT 1) as status,
               (SELECT attempts FROM tasks WHERE application_id=a.id ORDER BY id DESC LIMIT 1) as attempts,
               (SELECT error FROM tasks WHERE application_id=a.id ORDER BY id DESC LIMIT 1) as error,
               (SELECT artifacts_json FROM tasks WHERE application_id=a.id ORDER BY id DESC LIMIT 1) as artifacts_json
        FROM applications a ORDER BY a.id DESC
        """).fetchall()
    out=[]
    for id_,url,company,title,portal,job_json,ca,ua,status,attempts,error,artifacts_json in rows:
        out.append({
            "id":id_,"url":url,"company":company,"title":title,"portal":portal,
            "job":json.loads(job_json),"status":status or "QUEUED",
            "attempts":attempts or 0,"error":error,
            "artifacts": json.loads(artifacts_json) if artifacts_json else None,
            "created_at":ca,"updated_at":ua,
        })
    return out

def get_application(app_id:int)->Optional[Dict[str,Any]]:
    with _conn() as c:
        row=c.execute("SELECT id,url,company,title,portal,job_json,created_at,updated_at FROM applications WHERE id=?",(app_id,)).fetchone()
    if not row: return None
    id_,url,company,title,portal,job_json,ca,ua=row
    return {"id":id_,"url":url,"company":company,"title":title,"portal":portal,"job":json.loads(job_json),"created_at":ca,"updated_at":ua}

def update_task_status(task_id:int,status:str,*,error:str|None=None):
    if status not in VALID: raise ValueError("bad status")
    with _conn() as c:
        if error is None:
            c.execute("UPDATE tasks SET status=?,updated_at=? WHERE id=?", (status,_now(),task_id))
        else:
            c.execute("UPDATE tasks SET status=?,error=?,updated_at=? WHERE id=?", (status,error,_now(),task_id))

def set_artifacts(task_id:int, data:Dict[str,Any]):
    with _conn() as c:
        prev=c.execute("SELECT artifacts_json FROM tasks WHERE id=?",(task_id,)).fetchone()
        cur = json.loads(prev[0]) if (prev and prev[0]) else {}
        cur.update(data or {})
        c.execute("UPDATE tasks SET artifacts_json=?,updated_at=? WHERE id=?", (json.dumps(cur),_now(),task_id))

def increment_attempts(task_id:int):
    with _conn() as c:
        c.execute("UPDATE tasks SET attempts=attempts+1,updated_at=? WHERE id=?", (_now(),task_id))

def get_next_task()->Optional[Dict[str,Any]]:
    with _conn() as c:
        row=c.execute("SELECT id,application_id FROM tasks WHERE status='QUEUED' ORDER BY id ASC LIMIT 1").fetchone()
        if not row: return None
        task_id,app_id = int(row[0]), int(row[1])
        c.execute("UPDATE tasks SET status='IN_PROGRESS',updated_at=? WHERE id=?", (_now(),task_id))
        a=c.execute("SELECT url,company,title,portal,job_json FROM applications WHERE id=?",(app_id,)).fetchone()
    if not a: return None
    url,company,title,portal,job_json=a
    return {"task_id":task_id,"application_id":app_id,"status":"IN_PROGRESS","url":url,"company":company,"title":title,"portal":portal,"job":json.loads(job_json)}

# Legacy shims
def transition(task_id:int,new_status:str,error:str|None=None): update_task_status(task_id,new_status,error=error)
def dequeue_next(): return get_next_task()
def update_application_status(task_id:int,status:str,*,error:str|None=None): update_task_status(task_id,status,error=error)
